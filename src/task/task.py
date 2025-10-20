# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/16 13:39
# @Author  : cuils
# @Description:
"""
import asyncio
import logging
from typing import List
from openai.types.chat import ChatCompletionMessageParam

from src.api.base_client import BaseClient
from src.context.context_manager import ContextManager
from src.task.task_state import TaskState
from src.task.tool_executor import ToolExecutor
from src.tools.basic import ToolCall
from src.utils.parse_assistant_message import parse_assistant_message
from src.prompts.responses import GENERAL_WITHOUT_USE_TOOL, GENERAL_WITH_USE_TOOL
from src.cli.frontend import ConsoleApp


class Task:
    """任务"""
    def __init__(
        self,
        llm_client: BaseClient,
        ctx: ContextManager,
        tool_executor: ToolExecutor,
        logger: logging.Logger
    ):
        self.llm_client = llm_client
        self.ctx = ctx
        self.task_state = TaskState()
        self.tool_executor = tool_executor
        self.logger = logger
        self.app: ConsoleApp = None

    def set_console_app(self, app):
        self.app = app

    async def start(self):
        self.task_state.did_finish_current_task = False
        await self._loop()

    async def _loop(self):
        while not self.task_state.did_finish_current_task:
            await self.create_response(self.ctx.chat_messages, tool_schemas=self.tool_executor.tools)

    async def create_response(self, messages: List[ChatCompletionMessageParam], tool_schemas=None):
        """获取LLM结果，这里要对LLM的回复进行解析，存在两种解析方式"""
        self.logger.info(f"{messages[-1]['role']}: {messages[-1]["content"]}")
        
        # 开始流式输出
        if self.app and hasattr(self.app, "start_streaming_response"):
            self.logger.info("开始流式输出")
            # await self.app.call_from_thread(self.app.start_streaming_response)
            self.app.start_streaming_response()
        
        stream = await self.llm_client.achat_with_stream(messages, tool_schemas=tool_schemas)

        self.task_state.api_request_count += 1

        full_content = ""
        full_reasoning_content = ""
        full_tool_calls = []
        async for chunk in stream:
            curr_content = chunk.choices[0].delta.content
            tool_calls = chunk.choices[0].delta.tool_calls
            usage = chunk.usage
            # 解析工具
            if tool_calls:
                tool_call = tool_calls[0] # 在流式的情况下，每个chunk只会存在一个tool_call
                if tool_call.index == len(full_tool_calls):
                    full_tool_calls.append(ToolCall(id=tool_call.id, name="", arguments=""))
                if tool_call.function:
                    if tool_call.function.name:
                        full_tool_calls[-1].name = tool_call.function.name
                    if tool_call.function.arguments:
                        full_tool_calls[-1].arguments += tool_call.function.arguments

            # 思考内容
            if hasattr(chunk.choices[0].delta, "reasoning_content"):
                full_reasoning_content += chunk.choices[0].delta.reasoning_content
                # 流式显示思考过程
                if self.app and hasattr(self.app, 'append_streaming_content'):
                    # 在异步上下文中调用UI更新
                    # await self.app.call_from_thread(self.app.append_streaming_content, chunk.choices[0].delta.reasoning_content)
                    self.app.append_streaming_content(chunk.choices[0].delta.reasoning_content)

            # 回复内容
            if curr_content:
                full_content += curr_content
                # 流式显示内容
                if self.app and hasattr(self.app, 'append_streaming_content'):
                    # 在异步上下文中调用UI更新
                    # await self.app.call_from_thread(self.app.append_streaming_content, curr_content)
                    self.app.append_streaming_content(chunk.choices[0].delta.content)

            if usage:
                # 记录token使用量，最后一个chunk才是usage，在vllm或lmstudio部署的模型中，流式输出是没有usage的
                pass

        # 完成流式输出
        if self.app and hasattr(self.app, 'finish_streaming_response'):
            # await self.app.call_from_thread(self.app.finish_streaming_response)
            self.app.finish_streaming_response()
        
        self.logger.info(f"assistant: {full_reasoning_content}\n{full_content}")
        # 当前轮次assistant消息
        assistant_message = {
            "role": "assistant",
            "content": [{"type": "text", "text": full_reasoning_content}, {"type": "text", "text": full_content}]
        }
        if self.llm_client.support_tool_calls():
            if full_tool_calls:
                assistant_message["tool_calls"] = []
                for tool_call in full_tool_calls:
                    assistant_message["tool_calls"].append(
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {"name": tool_call.name, "arguments": tool_call.arguments}
                        }
                    )
        self.ctx.chat_messages.append(assistant_message)

        # 当前轮次执行工具
        # 因为自部署模型如vllm或lmstudio，可能不太支持hermes风格工具调用，建议手动处理；而OpenAI，自动处理即可
        if not self.llm_client.support_tool_calls():
            # TODO: 手动解析工具调用参数 xml格式
            full_tool_calls = parse_assistant_message(full_content)

        if not full_tool_calls:
            self.logger.error(f"没有调用工具")
            self.ctx.chat_messages.append(
                {"role": "user", "content": GENERAL_WITHOUT_USE_TOOL}
            )
            self.task_state.consecutive_mistake_count += 1
            return

        # print(full_tool_calls)
        self.logger.info(full_tool_calls)

        # TODO: 工具执行 下一次的交互之前，必须等待工具执行结束获取结果，直接在这里实现
        tool_results = await self.tool_executor.sequential_tool_call(full_tool_calls)

        for tool_call in full_tool_calls:
            if tool_call.name == "complete":
                self.logger.info("************************任务结束************************")
                self.task_state.did_finish_current_task = True
                print(tool_call.arguments)
                return

        next_messages = {
            "role": "user",
            "content": "\n".join(
                [GENERAL_WITH_USE_TOOL.format(tool_name=tool_result.name, tool_result=tool_result.result) for
                 tool_result in tool_results])
        }
        self.ctx.chat_messages.append(next_messages)

    def restore(self):
        pass

    def stop(self):
        self.task_state.did_finish_current_task = True

    def clear(self):
        self.ctx.save_context_history()
        self.ctx.chat_messages = []
