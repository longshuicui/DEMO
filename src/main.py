# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/17 14:21
# @Author  : cuils
# @Description:
"""
import asyncio
import json
from src.task import Task, ToolExecutor
from src.api import OpenAICompatibleClient, ModelConfig
from src.context import ContextManager
from src.prompts.components import TEST_SYSTEM_PROMPT
from src.utils.lc_logger import get_logger


model_config = {
    "model": "qwen3-8b-guff",
    "provider": {
        "name": "openai_compatible",
        "base_url": "http://127.0.0.1:1234/v1",
        "api_key": "EMPTY",
    },
    "max_tokens": 10240
}

model_config = ModelConfig(**model_config)
llm_client = OpenAICompatibleClient(model_config)
ctx = ContextManager()
tool_executor = ToolExecutor()
logger = get_logger(__name__)

task = Task(
    llm_client=llm_client,
    ctx=ctx,
    tool_executor=tool_executor,
    logger=logger,
)

ctx.chat_messages.append(
    {"role": "system", "content": TEST_SYSTEM_PROMPT}
)

RED = "\033[31m"
GREEN = "\033[92m"
END_COLOR = "\033[0m"


async def main():

    while True:
        user_input = input(f">>>User:{RED}")
        ctx.chat_messages.append(
            {"role": "user", "content": user_input}
        )

        await task.start()
        if task.task_state.did_finish_current_task:
            print(f">>>Assistant:", ctx.chat_messages[-1]["content"])


if __name__ == '__main__':
    asyncio.run(main())