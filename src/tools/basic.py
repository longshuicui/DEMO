# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/16 14:15
# @Author  : cuils
# @Description:
"""
from pydantic import BaseModel
from typing import Optional, List, Dict



class ToolCall(BaseModel):
    """LLM回复中解析的工具调用参数."""
    name: str
    arguments: str = None  # 因为xml风格和openai hermes风格不一致，所以这里就直接是一个JSON格式，后面看是不是要改
    call_id: Optional[str] = None
    id: Optional[str] = None


class ToolResult(BaseModel):
    """工具执行结果"""
    id: Optional[str] = None
    name: str
    result: Optional[str] = None
    error: Optional[str] = None
    success: bool


class ToolParameter(BaseModel):
    """工具参数定义，因为涉及到openai hermes风格和xml风格，这里统一管理"""
    name: str
    type: str
    description: str
    enum: Optional[List[str]] = None
    items: Optional[Dict[str, object]] = None
    required: bool = True