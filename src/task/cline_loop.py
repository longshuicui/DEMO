# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/24 11:28
# @Author  : cuils
# @Description:
"""
import time
from src.api import LLMService
from src.task import TaskState
from src.prompts import Context, get_system_prompt, NO_TOOL_USED, WITH_TOOL_USED
from src.utils import parse_assistant_message
from src.tools import REGISTRY_TOOLS

RED = "\033[31m"
GREEN = "\033[92m"
END_COLOR = "\033[0m"

# TODO: 前端需要将这个上下文context透传给后端
context = Context(
    operating_system="MacOS",
    shell="/bin/zsh",
    home_dir="/User/cuils", # noqa
    cwd="/Users/cuils/lscui/study/code-agents/link_coder", # noqa
)
system_prompt = get_system_prompt(context)

# TODO 全局控制：任务状态、循环状态，与LLM交互外部也可以更改任务状态，比如 did_reject_tool, 这个状态由用户决定，
task_state = TaskState()

llm_service = LLMService(base_url="http://localhost:1234/v1", api_key="EMPTY")

# TODO: demo阶段暂时使用一个列表存放历史对话
conversation_history = [
    # {"role": "system", "content": "你的名字是DEMO，一个AI助手。你必须使用中文回复，其他语言是严格禁止的，代码除外。"}
    {"role": "system", "content": system_prompt},
]

# TODO：流式返回和任务状态，包含内容流式传给前端、任务中断、重启等各种和前端交互的，
did_end_loop = False
cnt = 0
while not did_end_loop:
    time.sleep(5)
    cnt += 1
    if task_state.user_message_content:
        conversation_history.append({"role": "user", "content": task_state.user_message_content[-1]["content"]})
        task_state.user_message_content = []

    if len(conversation_history) < 2:
        user_input = input("User: ")
        conversation_history.append({"role": "user", "content": user_input})
    elif conversation_history[-1]["role"] != "user":
        user_input = input("\n\nUser: ")
        conversation_history.append({"role": "user", "content": user_input})
    else:
        print("\n\nUser: ", conversation_history[-1]["content"].lstrip())

    task_state.user_message_content_ready = True # 当前轮次用户已经输入

    resp =llm_service.chat(conversation_history)

    tokens = []
    assistant_message = ""
    reasoning_message = ""
    task_state.is_streaming = True
    did_receive_usage_chunk = False

    print("Assistant: ", end="", flush=True)

    for chunk in resp:
        if chunk["type"] == "reasoning":
            reasoning_message += chunk["reasoning"]
            if not task_state.abort:
                # TODO: 给前端发消息
                print("任务中断")
                exit()
        elif chunk["type"] == "usage":
            # 记录 token 数量，这里省略
            task_state.did_receive_usage_chunk = True
            pass
        else:
            # 文本类型 chunk.type = text
            if reasoning_message and len(assistant_message) == 0:
                # TODO: 推理部分结束，给前端发消息
                pass
            assistant_message += chunk["text"]
            print(chunk["text"], end="", flush=True)

            # 解析 assistant 消息
            # TODO: 因为是流式输出，每次循环都要解析一遍输出，不太fancy，是不是有优化的空间
            # prev_length = len(task_state.assistant_message_content)
            # assistant_message_content = parse_assistant_message(assistant_message)
            # task_state.assistant_message_content = assistant_message_content

            # if len(task_state.assistant_message_content) > prev_length:
            #     task_state.user_message_content_ready = False # 对于下一个轮次来讲，用户消息是没有准备好的，所以这里是False
            #
            # if task_state.present_assistant_message_locked:
            #     task_state.present_assistant_message_has_pending_updates = True
            #     continue

            # TODO: 这些任务状态有点绕，没咋懂
            # task_state.present_assistant_message_locked = True
            # task_state.present_assistant_message_has_pending_updates = False
            # if task_state.current_streaming_content_index >= len(task_state.assistant_message_content):
            #     if task_state.did_complete_reading_stream:
            #         task_state.user_message_content_ready = True
            #     task_state.present_assistant_message_locked = False
            #     continue
            # block = copy.deepcopy(task_state.assistant_message_content[-1]) # 这里选择最后一个block，因为最后一个block是最新的，之前的block之前已经处理过了
            # if block.type == "text":
            #     # TODO: 展示内容给用户，这里暂时在终端输出，应该发送到前端
            #     print(block["content"], end="", flush=True)
            #     pass
            # else:
            #     if not block.partial:
            #         if block.name == "attempt_completion":
            #             did_end_loop = True
            #             print(block["params"])
            #             continue
            #
            #         tool = REGISTRY_TOOLS[block.name]
            #         arguments = block.params
            #         for key in arguments:
            #             if arguments[key] == 'true':
            #                 arguments[key] = True
            #             elif arguments[key] == 'false':
            #                 arguments[key] = False
            #             else:
            #                 pass
            #         result = tool(**arguments)
            #         conversation_history.append({"role": "user", "content": WITH_TOOL_USED.format(tool_name=block.name, tool_result=result)})

            # TODO: 内容展示结束

        if task_state.abort:
            # TODO: 任务中断处理
            print("aborting stream...")
            exit()

        if task_state.did_reject_tool:
            assistant_message += "\n\n[用户拒绝使用该工具]" # Response interrupted by user feedback
            break

        if task_state.did_already_use_tool:
            assistant_message += "\n\n[每次仅能使用一个工具，且应放到消息末尾]" # Response interrupted by a tool use result. Only one tool may be used at a time and should be placed at the end of the message.
            break

    # 流式输出结束，更改对应状态
    task_state.is_streaming = False
    task_state.did_complete_reading_stream = True


    if len(assistant_message) > 0:
        conversation_history.append(
            {"role": "assistant", "content": [{"type": "text", "text": assistant_message}]}
        )

        print("\n", RED, "将工具添加到对话历史中", END_COLOR)
        assistant_message_content = parse_assistant_message(assistant_message)
        print(assistant_message_content)
        task_state.assistant_message_content = assistant_message_content

        tool_block = None
        for i in range(len(assistant_message_content)-1, -1):
            if assistant_message_content[i].type == "tool_use":
                tool_block = assistant_message_content[i]
                break

        # 是否使用工具
        did_tool_use = any([block.type == "tool_use" for block in task_state.assistant_message_content])
        if tool_block is None:
            task_state.user_message_content.append({"type": "text", "content": NO_TOOL_USED, "partial": False})
            task_state.consecutive_mistake_count += 1
            continue

        if tool_block.name == "attempt_completion":
            did_end_loop = True
            print(tool_block["params"])
            continue

        tool = REGISTRY_TOOLS[tool_block.name]
        arguments = tool_block.params
        for key in arguments:
            if arguments[key] == 'true':
                arguments[key] = True
            elif arguments[key] == 'false':
                arguments[key] = False
            else:
                pass
        result = tool(**arguments)
        conversation_history.append({"role": "user", "content": WITH_TOOL_USED.format(tool_name=tool_block.name, tool_result=result)})

    else:
        conversation_history.append({"role": "assistant", "content": [{"type": "text", "text": "响应失败：没有提供任何响应"}]})
    #     print("没有收到任何的回复，是否需要重试")
        did_end_loop = True



# for message in messages:
#     print(messages)