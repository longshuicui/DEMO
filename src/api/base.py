#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：DEMO_python 
@File    ：base.py
@Author  ：longshuicui
@Date    ：2025/10/1 22:05 
@Desc    ：模型相关信息，包含模型基础类实现
"""

from pydantic import BaseModel
from typing import Optional, List, Dict
from openai.types.chat import ChatCompletionMessageParam
from src.tools.base import BaseTool


# 模型基本信息与参数
class ModelProvider(BaseModel):
    """模型提供商参数
    对于OpenAI和Anthropic来讲，base_url是可选的
    对于Azure来讲，api_version是必选的
    对于自部署模型来讲，base_url是必选的
    """
    name: str = "openai"
    base_url: Optional[str] = None
    api_key: str = "EMPTY"
    api_version: Optional[str] = None


class ModelConfig(BaseModel):
    """模型参数"""
    model: str
    model_provider: ModelProvider
    temperature: float = 0.7
    top_p: float = 1.
    top_k: int = 20
    parallel_tool_calls: bool = False
    max_retries: int = 3
    max_tokens: Optional[int] = None
    support_tool_calling: bool = True
    candidate_count: Optional[int] = None  # Gemini指定参数
    stop_sequences: Optional[List[str]] = None
    max_completion_tokens: Optional[int] = None  # Azure OpenAI指定参数

    def get_max_tokens_param(self) -> int:
        """获取允许的最大token数量"""
        if self.max_completion_tokens is not None:
            return self.max_completion_tokens
        elif self.max_tokens is not None:
            return self.max_tokens
        else:
            return 4096

    def should_use_max_completion_tokens(self) -> bool:
        """是否要用max completion tokens 参数，取决于是否用Azure OpenAI 模型"""
        return self.max_completion_tokens is not None and self.model_provider.name == "azure" and (
                    "gpt-5" in self.model or "o3" in self.model or "o4-mini" in self.model)

    def resolve_config_values(self, *, model_provider):
        """"""
        # TODO: 这里呢先不用考虑重置参数


# TODO:输入和输出契约，因为OpenAI和Anthropic模型存在差异，存在一个输入输出的解析。这里暂时只以 OpenAI兼容格式为准


class BaseClient:
    """base class for llm client"""
    def __init__(self, model_config: ModelConfig):
        self.api_key = model_config.model_provider.api_key
        self.base_url= model_config.model_provider.base_url
        self.api_version = model_config.model_provider.api_version
        # TODO: 这里要不要一个轨迹记录
        self.recoder = dict() # 这里使用一个dict记录轨迹
        self.model_config = model_config

    def set_recoder(self, recoder: Dict):
        self.recoder = recoder

    def set_chat_history(self, messages: List[ChatCompletionMessageParam]):
        """对话历史"""
        pass

    def chat(
        self,
        messages: [ChatCompletionMessageParam],
        tools:List[BaseTool],
        reuse_history: bool):
        """LLM交互"""
        pass

    def support_tool_calling(self):
        return self.model_config.support_tool_calling

