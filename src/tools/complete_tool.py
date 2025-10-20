# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/17 13:24
# @Author  : cuils
# @Description:
"""

from src.tools.base_tool import BaseTool


class CompleteTool(BaseTool):
    """给一个目录，列出当前目录所有的文件"""
    def hermes_definition(self):
        json_def = {
            "type": "function",
            "function": {
                "name": "complete",
                "description": "Once you've received the results of tool uses and can confirm that the task is complete, use this tool to present the result of your work to the user. The user may respond with feedback if they are not satisfied with the result, which you can use to make improvements and try again. IMPORTANT NOTE: This tool CANNOT be used until you've confirmed from the user that any previous tool uses were successful. Failure to do so will result in code corruption and system failure. Before using this tool, if you've confirmed from the user that any previous tool uses were successful. If not, then DO NOT use this tool.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "result": {
                            "type": "string",
                            "description": "The result of the tool use. This should be a clear, specific description of the result"
                        }
                    },
                    "required": ["result"]
                }
            }
        }
        return json_def

    async def execute(self, arguments):
        try:
            return arguments.get("result", None)
        except Exception as e:
            return str(e)