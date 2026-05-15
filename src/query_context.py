# -*- coding: utf-8 -*-
"""
# @Time    : 2026/4/28 15:59
# @Author  : cuils
# @Description:
"""
from typing import Dict, Any
from system_prompts import get_system_prompt
from user_contexts import get_user_context


def fetch_system_prompt_parts(
    **kwargs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    获取系统提示词部分的三个上下文片段：
    1. 默认系统提示词 system_prompts.py: 86行 get_system_prompt
    2. 用户上下文 user_contexts.py: 19行 get_user_context
    3. 系统上下文 git相关和ant内部相关，此处忽略

    当用户自定义系统提示词（customSystemPrompt）设置时，默认系统提示词/系统上下文是被跳过的，
    后面就是将 默认系统提示词或自定义系统提示词 + 额外部分 + 补充系统提示词组装，在这上面注入 用户上下文和记忆机制

    """

