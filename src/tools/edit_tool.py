#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：DEMO_python 
@File    ：edit_tool.py
@Author  ：longshuicui
@Date    ：2025/9/29 22:31 
@Desc    ：
"""
from typing import List, Optional
from pathlib import Path
from src.tools.base import BaseTool, ToolParameter, ToolCallArguments, ToolExecuteResult, ToolError


TOOL_DESCRIPTION = """Custom editing tool for viewing, creating and editing files
* State is persistent across command calls and discussions with the user
* If `path` is a file, `view` displays the result of applying `cat -n`. If `path` is a directory, `view` lists non-hidden files and directories up to 2 levels deep
* The `create` command cannot be used if the specified `path` already exists as a file !!! If you know that the `path` already exists, please remove it first and then perform the `create` operation!
* If a `command` generates a long output, it will be truncated and marked with `<response clipped>`

Notes for using the `str_replace` command:
* The `old_str` parameter should match EXACTLY one or more consecutive lines from the original file. BE MINDFUL OF WHITESPACE!
* If the `old_str` parameter is not unique in the file, the replacement will not be performed. Make sure to include enough context in `old_str` to make it unique
* The `new_str` parameter should contain the edited lines that should replace the `old_str`
"""


EDIT_TOOL_SUB_COMMANDS = ["view", "create", "str_replace", "insert"]

# TODO: 文件读写是否需要异步，该处实现均为同步实现，是否会发生阻塞

class TextEditorTool(BaseTool):
    """文本编辑工具"""
    def __init__(self, model_provider:str|None=None, snippet_lines: int=4) -> None:
        super(TextEditorTool, self).__init__(model_provider)
        self.snippet_lines = snippet_lines

    def get_name(self) -> str:
        return "edit_tool"

    def get_description(self) -> str:
        return TOOL_DESCRIPTION

    def get_parameters(self) -> List[ToolParameter]:
        command = ToolParameter(
            name="command",
            type="string",
            description=f"The command to run. Allow options are: {', '.join(EDIT_TOOL_SUB_COMMANDS)}.",
            required=True,
            enum=EDIT_TOOL_SUB_COMMANDS
        )
        file_text = ToolParameter(
            name="file_text",
            type="string",
            description="Required parameter of `create` command, with the content of the file to be created."
        )
        insert_line = ToolParameter(
            name="insert_line",
            type="integer",
            description="Optional parameter of `insert` command. The `new_str` will be inserted AFTER the line `insert_line` of `path`."
        )
        new_str = ToolParameter(
            name="new_str",
            type="string",
            description="Optional parameter of `str_replace` command containing the new string (if not given, no string will be added). Required parameter of `insert` command containing the string to insert."
        )
        old_str = ToolParameter(
            name="old_str",
            type="string",
            description="Required parameter of `str_replace` command containing the string in `path` to repalce."
        )
        path = ToolParameter(
            name="path",
            type="string",
            description="Absolute path to file or directory, e.g. `/repo/file.py` or`/repo`.",
            required=True
        )
        view_range = ToolParameter(
            name="view_range",
            type="array",
            description="Optional parameter of `view` command when `path` points to a file. If none is given, the full file is shown. If provided, the file will be shown in the indicated line number range, e.g. [11, 12] will show lines 11 and 12. Indexing at 1 to start. Setting `[start_line, -1]` shows all lines from `start_line` to the end of the file.",
            items={"type": "integer"}
        )
        return [command, file_text, insert_line, new_str, old_str, path, view_range]

    async def execute(self, arguments: ToolCallArguments) -> ToolExecuteResult:
        pass

    def str_replace(self, path: Path, old_str:str, new_str: Optional[str]) -> ToolExecuteResult:
        """字符串替换"""
        file_content = self.read_file(path).expandtabs()
        old_str = old_str.expandtabs()
        new_str = new_str.expandtabs() if new_str is not None else ""

        # 判断一下 old str出现了多少次
        occur = file_content.count(old_str)
        if occur == 0:
            raise ToolError(message=f"No replacement was performed, old_str `{old_str}` did not appear verbatim in {path}.")
        elif occur > 1:
            file_content_lines = file_content.split("\n")
            lines = [idx+1 for idx, line in enumerate(file_content_lines) if old_str in line]
            raise ToolError(message=f"No replacement was performed. Multiple occurrences of old_str `{old_str}` in lines {lines}. Please ensure it is unique.")

        new_file_content = file_content.replace(old_str, new_str)
        self.write_file(path, new_file_content)

        # Create a snippet of the edited section
        replacement_line = file_content.split(old_str)[0].count("\n")
        start_line = max(0, replacement_line - self.snippet_lines)
        end_line = replacement_line + self.snippet_lines + new_str.count("\n")
        snippet = "\n".join(new_file_content.split("\n")[start_line: end_line + 1])

        # Prepare the success message
        success_msg = f"The file {path} has been edited. "
        success_msg += self._make_output(snippet, f"a snippet of {path}", start_line + 1)
        success_msg += "Review the changes and make sure they are as expected. Edit the file again if necessary."

        return ToolExecuteResult(result=success_msg)



    def read_file(self, path: Path):
        """读取文件"""
        try:
            return path.read_text()
        except Exception as e:
            raise ToolError(message=f"Ran into {e} while trying to read {path}.") from None

    def write_file(self, path: Path, file: str):
        """写入文件"""
        try:
            path.write_text(file)
        except Exception as e:
            raise ToolError(message=f"Ran into {e} while trying to write to {path}.") from None

    def _make_output(self, snippet, ):
        pass