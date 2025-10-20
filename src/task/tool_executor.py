# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/24 11:25
# @Author  : cuils
# @Description: 工具执行
"""
import json
import asyncio
from typing import List
from src.tools import ListFileTool, CompleteTool
from src.tools.basic import ToolCall, ToolResult

TOOL_FACTORY = {
    "list_files": ListFileTool(),
    "complete": CompleteTool()
}

class ToolExecutor:
    """工具执行器"""
    def __init__(self):
        # TODO: 权限控制、前端交互
        self.tools = [_t.hermes_definition() for _t in TOOL_FACTORY.values()]

    async def execute_tool_call(self, tool_call: ToolCall) -> ToolResult:
        tool_name = tool_call.name
        arguments = json.loads(tool_call.arguments)
        if tool_name not in TOOL_FACTORY:
            tool_result = ToolResult(
                id=tool_call.id,
                name=tool_name,
                error=f"Tool `{tool_name}` not found. Available tools: {list(TOOL_FACTORY.keys())}",
                success=False
            )
            return tool_result

        tool = TOOL_FACTORY[tool_name]

        exec_result = await tool.execute(arguments)

        if isinstance(exec_result, (list, dict)):
            exec_result = json.dumps(exec_result, ensure_ascii=False)

        tool_result = ToolResult(
            id=tool_call.id,
            name=tool_name,
            result=exec_result,
            success=True
        )
        return tool_result

    async def sequential_tool_call(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """顺序执行工具"""
        return await asyncio.gather(*[self.execute_tool_call(tool_call) for tool_call in tool_calls])






