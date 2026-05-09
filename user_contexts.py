# -*- coding: utf-8 -*-
"""
# @Time    : 2026/4/28 16:12
# @Author  : cuils
# @Description:
用户上下文：
1. 收集CLAUDE.md / 相关 memory文件，作为用户提供的长期说明
2. 当前本地日期

极简模式或者显式关闭时，不会读取md文件

改用户上下文在整个会话期间复用，避免每次重新扫文件
"""
from typing import Dict
from datetime import datetime


MEMORY_INSTRUCTION_PROMPT = """Codebase and user instructions are shown below. Be sure to adhere to these instructions. IMPORTANT: These instructions OVERRIDE any default behavior and you MUST follow them exactly as written."""


def get_user_context() -> Dict[str, str]:
    """
    context.ts: 155行 getUserContext
    getUserContext -> getMemoryFiles -> getClaudeMds
    Returns:
    """
    memories = []
    # TODO: 读取各种用户写的文件，
    for file in []:
        pass

    _contexts = {
        "current_date": f"Today's date is {datetime.now().strftime('%Y-%m-%d')}",
    }
    if not memories:
        return _contexts

    _contexts["claud_md"] = f"""{MEMORY_INSTRUCTION_PROMPT}\n\n{"\n\n".join(memories)}"""

    return _contexts