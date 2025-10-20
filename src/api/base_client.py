# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/30 16:08
# @Author  : cuils
# @Description:
"""
from typing import List
from openai.types.chat import ChatCompletionMessageParam
from src.api.basic import ModelConfig


class BaseClient:
    """LLM基础类"""
    def __init__(self, model_config: ModelConfig):
        self.model_config = model_config

    def chat(self, messages: List[ChatCompletionMessageParam], tools=None, **kwargs):
        """Openai client.chat.completion.create
        sync 非流式输出
        """
        raise NotImplemented

    def chat_with_stream(self, messages: List[ChatCompletionMessageParam], tools=None, **kwargs):
        """
        sync 流式输出
        """
        raise NotImplemented

    async def achat(self, messages: List[ChatCompletionMessageParam], tools=None):
        """
        async 非流式输出
        """
        raise NotImplemented

    async def achat_with_stream(self, messages: List[ChatCompletionMessageParam], tools=None, **kwargs):
        """
        async 流式输出
        """
        raise NotImplemented

    def support_tool_calls(self):
        return self.model_config.support_tool_calls






