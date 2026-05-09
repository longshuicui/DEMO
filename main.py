# -*- coding: utf-8 -*-
"""
# @Time    : 2026/4/13 10:59
# @Author  : cuils
# @Description: 学习一下 claude code，从一个简单的demo开始
"""

import json
import openai
import asyncio
from typing import List
from src.llm import AsyncEmbeddingModel
from src.storage.vector_stores.es import AsyncElasticsearchDBClient
from src.retrieve import AsyncNaiveRetriever


# tools
# TODO: 支持的工具有哪些，如何定义工具的schema的
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "retrieve",
            "description": "用于知识库检索，输入多个queries，返回知识库中与该query相匹配的top-k个文档",
            "parameters": {
                "type": "object",
                "properties": {
                    "queries": {
                        "type": "array",
                        "description": "用户检索的query列表",
                    }
                },
                "required": ["queries"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "complete",
            "description": "用于完成任务的标志。当完成任务时，必须调用该工具，返回的你输出答案；其他情况，禁止使用该工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "result": {
                        "type": "string",
                        "description": "输出解答用户问题的详细答案，该输出仅包括结果内容，任何过程信息、与任务无关的内容将禁止出现在该结果里面。"
                    }
                },
                "required": ["result"]
            }
        }
    }
]

async def retrieve(queries: List[str]):
    """检索模块"""
    async_results = await retriever.parallel_retrieve(index="linkrag_kb_10_2bbd085c", queries=queries, top_k=10)
    documents = []
    for results in async_results:
        documents.extend(results)
    return documents

async def complete(result:str):
    """任务完成，必须调用该方法返回结果"""
    return result


# TODO: system prompt的组成部分有哪些？
SYSTEM_PROMPT = """
## Role
你是Finder，擅长知识搜索、信息推理、知识汇总，以及使用外部工具。

## Task
分析用户任务需求，思考需要获取哪知识回答用户问题；针对需要的知识，生成合理的query，用来检索知识库。获取到知识后，进行归纳整理，回答用户的需求。
当获取的知识不充分或不可用时，及时修改query，直到能完全回答用户的任务需求。
当用户需求不需要知识检索时，直接调用`complete`工具返回你的答案即可。

## Requirements
1. 生成query的数量必须不少于 5 个，且query不能存在语义相似，保证有效率的获取更全面、准确的信息。
2. 仔细分析、理解用户任务需求，对于复杂的任务需求，可以进行任务拆解。对于模糊的需求，可以进行联想。
3. 知识库中的文档，除代码外，均为日语，为了保证有效检索，生成的query必须为日语。
4. 每次回复，你必须调用外部工具。如果解决了用户的问题，必须调用`complete`工具。若没有完成用户任务，禁止调用`complete`工具。
5. 当需要重新生成query时，新的query不能和历史query相同或存在语义上的相似。
"""


embedding_client = AsyncEmbeddingModel(
    base_url="http://192.168.10.187:5002/v1",
    model="Qwen3-Embedding-0.6B"
)
vector_db_client = AsyncElasticsearchDBClient(
    url="http://192.168.10.187:9200",
    user="elastic",
    password="+ZWNahlRPSAwNj2g5Upr"
)

retriever = AsyncNaiveRetriever(
    embedding_client=embedding_client,
    vector_db_client=vector_db_client
)

llm = openai.AsyncClient(
    base_url="http://192.168.10.187:5007/v1",
    api_key="EMPTY"
)
model = "gemma-4-31B-it"
thinking = True

# 限制循环次数，避免任务无法停止
MAX_QUERY_LOOP = 5

# 仅单个query loop
async def query_loop(user_input:str):

    # TODO: system prompt组装
    # TODO: 上下文管理
    contexts = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input}
    ]

    loop = 0

    while loop < MAX_QUERY_LOOP:
        resp = await llm.chat.completions.create(
            messages=contexts,
            model=model,
            tool_choice="auto",
            tools=TOOLS
        )
        loop += 1
        content = resp.choices[0].message.content
        print("assistant:", content)
        # if thinking:
        #     content = content.split("</think>")[-1]
        assistant_message = {
            "role": "assistant",
            "content": content,
            "tool_calls": resp.choices[0].message.tool_calls
        }
        contexts.append(assistant_message)

        if not resp.choices[0].message.tool_calls:
            message = "[Error]：你没有调用任何工具。如果你确认已经完成了任务，请调用`complete`工具；如果没有，则按照任务要求继续执行。"
            contexts.append({"role": "user", "content": message})
            continue

        tool_call = resp.choices[0].message.tool_calls[0]
        function_name = tool_call.function.name
        function_arguments = tool_call.function.arguments
        print(function_name, function_arguments)

        if function_name == "retrieve":
            documents = await retrieve(**json.loads(function_arguments))
            documents = sorted(documents, key=lambda d: d["score"], reverse=True)[:10]
            references = []
            for i, doc in enumerate(documents):
                references.append(f"[{i + 1}]:\n{doc['content']}")
            references = "\n\n".join(references)
            message = f"工具：`{function_name}`, 参数：{function_arguments}, 返回结果：\n\n{references}"
            contexts.append({"role": "user", "content": message})

        elif function_name == "complete":
            return await complete(**json.loads(function_arguments))

        else:
            raise ValueError("Not found function, only `retrieve`, `complete`")

    return None


async def main():
    res = await query_loop("介绍一下电产")
    print(res)
    await embedding_client.close()
    await vector_db_client.close()
    await llm.close()



if __name__ == '__main__':
    res = asyncio.run(main())