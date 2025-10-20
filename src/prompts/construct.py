# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/24 11:45
# @Author  : cuils
# @Description:
"""


# def get_system_info():
#     home_dir = os.environ.get("HOME", "")
#     if home_dir.startswith("/Users"):
#         _os = "MacOS"
#     elif home_dir.startswith("C:\\") or home_dir.startswith("D:\\"):
#         _os = "Windows"
#     else:
#         _os = "Linux"
#
#     return {
#         "os": _os,
#         "home_dir": home_dir,
#         "shell": os.environ.get("SHELL"),
#     }


from pydantic import BaseModel
from typing import Optional, List, Any
from src.prompts.components import (
    AGENT_ROLE,
    TOOL_USE,
    MCP,
    CAPABILITIES,
    BASIC_RULES,
    SYSTEM_INFO,
    OBJECTIVE,
    USER_CUSTOM_INSTRUCTIONS
)

class Context(BaseModel):
    operating_system: str
    shell: str
    home_dir: str
    cwd: str


def get_system_prompt(context: Context, user_custom_instructions: Optional[str]=None, mcp_server_list:Optional[List[Any]]=None) -> str:
    """system prompt 组装"""

    if user_custom_instructions:
        system_prompt_components = [
            AGENT_ROLE,
            TOOL_USE,
            MCP,
            CAPABILITIES,
            BASIC_RULES,
            SYSTEM_INFO,
            OBJECTIVE,
            USER_CUSTOM_INSTRUCTIONS
        ]
        system_prompt = "\n====\n".join(system_prompt_components)
        system_prompt = system_prompt.format(
            **context.model_dump(),
            user_custom_instructions=user_custom_instructions,
            mcp_servers_list=mcp_server_list if mcp_server_list else "[]"
        )
    else:
        system_prompt_components = [
            AGENT_ROLE,
            TOOL_USE,
            MCP,
            CAPABILITIES,
            BASIC_RULES,
            SYSTEM_INFO,
            OBJECTIVE
        ]

        system_prompt = "\n====\n".join(system_prompt_components)
        system_prompt = system_prompt.format(
            **context.model_dump(),
            mcp_servers_list=mcp_server_list if mcp_server_list else "[]"
        )

    return system_prompt



if __name__ == '__main__':
    import os
    context = Context(operating_system="MacOS", shell="/bin/zsh", home_dir="/User/cuils", cwd=os.getcwd())
    system_prompt = get_system_prompt(context)
    print(system_prompt)