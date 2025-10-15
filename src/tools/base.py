#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：DEMO_python 
@File    ：base.py
@Author  ：longshuicui
@Date    ：2025/9/28 21:03 
@Desc    ：
"""
import json
import asyncio
from pydantic import BaseModel, Field
from typing import List, Dict, override, Tuple, Generic  # noqa


class ToolError(BaseModel, Exception):
    """Base class for tool errors"""
    message: str | None = None


class ToolExecuteResult(BaseModel):
    """Intermediate result of a tool execution"""
    result: str | None = None
    error: str | None = None
    error_code: int = 0


class ToolResult(BaseModel):
    """Result of a tool execution"""
    call_id: str
    name: str  # Gemini 指定字段
    success: bool
    result: str | None = None
    error: str | None = None
    id: str | None = None  # OpenAI 指定字段


# 定义工具应该传入的参数数据类型（实参）
ToolCallArguments = dict[str, str | int | float | dict[str, object] | List[object] | None]


class ToolCall(BaseModel):
    """从模型响应中解析的工具调用内容"""
    id: str | None = None
    name: str
    call_id: str
    arguments: ToolCallArguments = Field(default_factory=dict)

    @override
    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False, indent=2)


class ToolParameter(BaseModel):
    """工具形参定义"""
    name: str
    type: str | List[str]
    description: str
    enum: List[str] | None = None
    items: dict[str, object] | None = None
    required: bool = True


class BaseTool:
    """工具-基础类"""

    def __init__(self, model_provider: str | None = None):
        self._model_provider = model_provider

    def get_model_provider(self) -> str|None:
        return self._model_provider

    def get_name(self) -> str:
        """工具名称"""
        raise NotImplementedError

    def get_description(self) -> str:
        """工具描述"""
        raise NotImplementedError

    def get_parameters(self) -> List[ToolParameter]:
        """工具参数"""
        raise NotImplementedError

    async def execute(self, arguments: ToolCallArguments) -> ToolExecuteResult:
        """基于给定的参数，执行工具"""
        raise NotImplementedError

    def json_definition(self) -> dict[str, object]:
        """获取工具的json格式定义，用于function call时传给大模型"""
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "parameters": self.get_parameters()
        }

    def xml_definition(self) -> str:
        """获取工具的xml格式定义，可直接在prompt中提供给大模型"""
        tool_opening_tag = f"<{self.get_name()}>"
        tool_closing_tag = f"</{self.get_name()}>"
        params = [f"<{p.name}>{p.description}</{p.name}>" for p in self.get_parameters()]

        return "\n".join([tool_opening_tag] + params + [tool_closing_tag])

    def get_input_schema(self):
        """TODO: 针对不同模型，对于工具参数的选择不同

        """
        pass

    async def close(self):
        """当任务完成时，确保工具资源关闭"""
        print("任务关闭")
        pass


class ToolExecutor:
    """管理工具执行，可以一次性执行多个工具"""
    def __init__(self, tools: List[BaseTool]):
        self.tools = tools
        self.tool_map: Dict[str, BaseTool]|None = None

    async def close_tools(self):
        """确保所有的工具资源都被释放"""
        tasks = [tool.close() for tool in self.tools if hasattr(tool, "close")]
        return await asyncio.gather(tasks)


    def get_tools(self) -> Dict[str, BaseTool]:
        if self.tool_map is None:
            self.tool_map = {tool.get_name(): tool for tool in self.tools}
        return self.tool_map

    async def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""

        if tool_call.name not in self.get_tools():
            return ToolResult(
                call_id=tool_call.call_id,
                name=tool_call.name,
                success=False,
                error=f"Tool '{tool_call.name}' not found, Available tools: {[tool.get_name() for tool in self.tools]}",
                id = tool_call.id,
            )

        tool = self.tool_map[tool_call.name]

        try:
            tool_exec_result: ToolExecuteResult = await tool.execute(tool_call.arguments)
            return ToolResult(
                name=tool_call.name,
                success=tool_exec_result.error_code == 0,
                result=tool_exec_result.result,
                error=tool_exec_result.error,
                call_id=tool_call.call_id,
                id=tool_call.id
            )
        except Exception as e:
            return ToolResult(
                name=tool_call.name,
                success=False,
                error=f"Error executing tool '{tool_call.name}': {repr(e)}",
                call_id=tool_call.call_id,
                id=tool_call.id
            )

    async def parallel_execute(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """并行执行多个工具"""
        return await asyncio.gather(*[self.execute_tool_call(tool_call) for tool_call in tool_calls])

    async def sequential_execute(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """串行执行多个工具"""
        return [await self.execute_tool_call(tool_call) for tool_call in tool_calls]





if __name__ == '__main__':
    calling = ToolCall(**{"id": "1111", "name": "test", "call_id": "xhdfadu", "arguments": {"args": ["a", "b"]}})

    tool = BaseTool(model_provider="custom")
    print(tool.get_name())