# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/30 16:12
# @Author  : cuils
# @Description:
"""
import json
import openai
from typing import List, AsyncIterator
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionChunk
from tenacity import retry, stop_after_attempt, wait_exponential

from src.api.base_client import BaseClient
from src.api.basic import ModelProvider, ModelConfig, RequestAttempt


class OpenAICompatibleClient(BaseClient):
    """自部署模型，OpenAI兼容"""
    def __init__(self, model_config: ModelConfig):
        super().__init__(model_config)
        self.client = openai.Client(base_url=model_config.provider.base_url, api_key=model_config.provider.api_key) # 非异步仅供测试用，后续删除
        self.async_client = openai.AsyncClient(base_url=model_config.provider.base_url, api_key=model_config.provider.api_key)

    @retry(
        stop=stop_after_attempt(RequestAttempt().max_attempts),
        wait=wait_exponential(min=RequestAttempt().min_wait_time, max=RequestAttempt().max_wait_time)
    )
    def chat_with_stream(self, messages: List[ChatCompletionMessageParam], tool_schemas=None, **kwargs) -> ChatCompletionChunk:
        """流式输出，非异步"""
        stream = self.client.chat.completions.create(
            messages=messages,
            model=self.model_config.model,
            stream=True,
            stream_options={"include_usage": True},
            tool_choice="auto" if tool_schemas else "none",
            tools=tool_schemas,
            temperature=self.model_config.temperature,
            top_p=self.model_config.top_p,
            **kwargs
        )

        for chunk in stream:
            yield chunk

    @retry(
        stop=stop_after_attempt(RequestAttempt().max_attempts),
        wait=wait_exponential(min=RequestAttempt().min_wait_time, max=RequestAttempt().max_wait_time)
    )
    async def achat_with_stream(self, messages: List[ChatCompletionMessageParam], tool_schemas=None, **kwargs):
        """异步流式输出"""
        stream = await self.async_client.chat.completions.create(
            messages=messages,
            model=self.model_config.model,
            stream=True,
            stream_options={"include_usage": True},
            tool_choice="auto" if tool_schemas else "none",
            tools=tool_schemas,
            temperature=self.model_config.temperature,
            top_p=self.model_config.top_p,
            max_tokens=self.model_config.max_tokens,
            **kwargs
        )
        return stream



def main():
    model_config = ModelConfig(
        model="qwen3-8b-guff",
        provider=ModelProvider(
            name="openai_compatible",
            base_url="http://localhost:1234/v1",
            api_key="EMPTY"
        )
    )
    oc_client = OpenAICompatibleClient(model_config=model_config)

    for chunk in oc_client.chat_with_stream(messages=[{"role": "user", "content": "请介绍下自己"}]):
        print(chunk)




if __name__ == '__main__':
    # import asyncio
    # asyncio.run(main())
    main()

