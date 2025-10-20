# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/30 16:06
# @Author  : cuils
# @Description: VSCode 扩展消息定义
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class MessageType(Enum):
    ASK = "ask"
    SAY = "say"

class CancelReason(Enum):
    streaming_failed = "streaming_failed"
    user_cancelled = "user_cancelled"
    retries_exhausted = "retries_exhausted"


class LinkCoderMessage(BaseModel):
    timestamp: int
    type: MessageType
    text: Optional[str]
    ...


class LinkCodeApiReqInfo(BaseModel):
    """API请求信息"""
    request: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.
    cancel_reason: Optional[CancelReason] = None
    streaming_failed_message: Optional[str] = None









