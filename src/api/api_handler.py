# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/23 16:48
# @Author  : cuils
# @Description:
"""
import time
import openai
from functools import wraps
from typing import List, Dict

from openai.types import CompletionUsage
from openai.types.chat import ChatCompletionStreamOptionsParam


def retry(max_retry_count=3, interval_time=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(max_retry_count):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    time.sleep(interval_time)
            return None
        return wrapper
    return decorator


class LLMService:
    def __init__(self, base_url, api_key, model=None):
        self.client = openai.Client(base_url=base_url, api_key=api_key)
        self.model = model
        if self.model is None:
            self.model = self.client.models.list().data[0].id

    @retry(max_retry_count=3)
    def chat(self, messages: List[Dict[str, str]], **kwargs):
        stream_chunks = self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            stream=True,
            stream_options=ChatCompletionStreamOptionsParam(include_usage=True),
            **kwargs
        )
        for chunk in stream_chunks:
            delta = chunk.choices[0].delta
            if delta.content:
                yield {"type": "text", "text": delta.content}
            if delta and "reasoning_content" in delta and delta.reasoning_content:
                yield {"type": "reasoning", "reasoning": delta.reasoning_content}
            if chunk.usage:
                yield {
                    "type": "usage",
                    **chunk.usage.model_dump()
                }