# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/20 09:23
# @Author  : cuils
# @Description:
"""
import asyncio
import logging
from src.task import Task, ToolExecutor
from src.api import OpenAICompatibleClient, ModelConfig
from src.context import ContextManager
from src.prompts.components import TEST_SYSTEM_PROMPT
from src.cli.frontend import ConsoleApp


class Controller:
    """任务控制器，前后端结合"""
    def __init__(self, config: ModelConfig, logger: logging.Logger): # 这里暂时只传入模型参数
        self.llm_client = OpenAICompatibleClient(config)
        self.ctx = ContextManager()
        self.tool_executor = ToolExecutor()
        self.app = ConsoleApp()
        self.logger = logger

    async def run(self):
        task = Task(
            llm_client=self.llm_client,
            ctx=self.ctx,
            tool_executor=self.tool_executor,
            logger=self.logger,
        )
        self.ctx.chat_messages.append(
            {"role": "system", "content": TEST_SYSTEM_PROMPT}
        )

        self.app.set_context_manager(self.ctx)
        self.app.set_task(task)
        task.set_console_app(self.app)
        await self.app.run_async()



if __name__ == '__main__':
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
    logger = get_logger("66666")
    model_config = ModelConfig(**model_config)
    controller = Controller(model_config, logger)
    asyncio.run(controller.run())









