# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/16 11:01
# @Author  : cuils
# @Description:
"""
from enum import Enum
from pydantic import BaseModel
from typing import Optional, List


class ProviderEnum(Enum):
    ANTHROPIC = "anthropic"
    AZURE = "azure"
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"


class ModelProvider(BaseModel):
    """模型提供商
    OpenAI和Anthropic模型，不需要 base_url
    Azure模型，需要api_version
    自部署模型，需要base_url
    """
    name: ProviderEnum
    base_url: Optional[str] = None
    api_key: str = "EMPTY"
    api_version: Optional[str] = None


class ModelConfig(BaseModel):
    """模型参数"""
    model: str
    provider: ModelProvider
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 20
    support_tool_calls: bool = True
    max_tokens: int = 4096
    max_completion_tokens: Optional[int] = None
    input_price: float = 0.
    output_price: float = 0.


class RequestAttempt(BaseModel):
    """请求重试"""
    max_attempts: int = 3 # 最多重试次数
    min_wait_time: float = 0. # 最少等待时间 0s
    max_wait_time: float = 10. # 最长等待时间 10s


class PriceTier(BaseModel):
    """不同价格等级"""
    context_window: int
    input_price: float = 0.
    output_price: float = 0.
    cache_write_price: float = 0.
    cache_read_price: float = 0.


class ThinkingPriceTier(BaseModel):
    """达到token限制数量后的价格"""
    token_limit: int
    price: float = 0.


class ThinkConfig(BaseModel):
    """思考模式token参数"""
    max_budget: Optional[int] = None # 最大token开销数量
    output_price: Optional[float] = None # 当budget>0时的价格/百万token
    output_price_tiers: Optional[List[ThinkingPriceTier]] = None