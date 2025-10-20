# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/16 17:31
# @Author  : cuils
# @Description:
"""
import os
import re
import pathlib
import aiopathlib
from src.tools.base_tool import BaseTool


class ListFileTool(BaseTool):
    """给一个目录，列出当前目录所有的文件"""
    def hermes_definition(self):
        json_def = {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "Request to list files and directories within the specified directory. If recursive is true, it will list all files and directories recursively. If recursive is false or not provided, it will only list the top-level contents. Do not use this tool to confirm the existence of files you may have created, as the user will let you know if the files were created successfully or not.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "The path of the directory to list contents"
                        },
                        "recursive": {
                            "type": "string",
                            "description": "Whether to list files recursively. Use true for recursive listing, false or omit for top-level only.",
                            "enum": ["true", "false"]
                        }
                    },
                    "required": ["path"]
                }
            }
        }
        return json_def

    async def execute(self, arguments):
        try:
            return self.list_files(**arguments)
        except Exception as e:
            return str(e)

    @staticmethod
    def list_files(path, recursive=False):
        if recursive:
            files = []
            for _, _, sub_files in os.walk(path):
                files.extend(sub_files)
            return files
        return os.listdir(path)

    @staticmethod
    async def async_list_files(self, path, recursive=False):
        pass


if __name__ == '__main__':
    tool = ListFileTool()
    res = tool.execute({"path": "./"})
    print(res)