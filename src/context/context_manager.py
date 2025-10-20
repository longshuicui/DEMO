# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/23 17:35
# @Author  : cuils
# @Description: 上下文管理

"""
import os
import json
import math
from enum import Enum
from pydantic import BaseModel
from aiopathlib import AsyncPath
from typing import List, Dict, Optional, Any
from openai.types.chat import ChatCompletionMessageParam

from src.shared import CONTEXT_HISTORY
from src.shared import LinkCoderMessage, LinkCodeApiReqInfo


class EditType(Enum):
    UNDEFINED = 0
    NO_FILE_READ = 1
    READ_FILE_TOOL = 2
    ALTER_FILE_TOOL = 3
    FILE_MENTION = 4


class ContextUpdate(BaseModel):
    """上下文更新内容"""
    timestamp: str
    update_type: str
    message_content: Optional[List[str]]=None
    message_metadata: Optional[List[List[str]]]=None


class ContextTrackRecoder:
    """上下文轨迹记录"""
    def __init__(self):
        pass

    async def read(self):
        pass

    async def update(self):
        pass

    async def save(self):
        pass

"""
任务执行过程中，消息历史应该是：
user input >> (llm resp > mid input > llm resp  > mid input > ... > llm resp > update messages) >> agent output >> user input >> ...

"""
class ContextManager:
    """上下文管理"""
    def __init__(self):
        self.chat_messages: List[ChatCompletionMessageParam] = []  # 该列表直接传给LLM生成
        self.context_track_recoder = ContextTrackRecoder()
        self.total_usage = 0

    def save_context_history(self):
        self.context_track_recoder.save()

    def update_chat_messages(self, message: ChatCompletionMessageParam):
        """TODO: 重要 更新对话历史信息
        1. chat_messages中仅存在 system、user和assistant三种角色:
            若存在system，则必是第一条message，其余message为 user -> assistant -> user -> assistant循环，
            若不存在则为user和assistant两种角色循环
        2. 如果对话历史超过阈值，在请求LLM之前需要对上下文进行压缩，但是 新的user内容不能被压缩，因此，对不同角色消息处理如下
            如果role=assistant，不需要考虑上下文，直接添加
            如果role=user, 需要判断上下文token数量，如果超过上下文窗口数量，则进行压缩（执行总结任务）。
        3. 压缩过后，需要删除对应的message，删除之前，需要确保上下文历史已经被保存
        """
        self.chat_messages.append(message)

class ContextManagerAlias:
    """上下文管理"""
    def __init__(self, ):
        self.chat_messages: List[ChatCompletionMessageParam] = [] # 该列表直接传给LLM生成
        self.context_track_recoder = ContextTrackRecoder()

    async def initialize_context_history(self, task_directory: str) -> None:
        self.context_history_updates = await self.get_saved_context_history(task_directory)

    @staticmethod
    async def get_saved_context_history(task_directory: str) -> Dict[str, Any]:
        """获取已保存的上下文历史"""
        saved_context_history = dict()
        try:
            saved_context_history = await AsyncPath(os.path.join(task_directory, CONTEXT_HISTORY)).read_text()
            saved_context_history = json.loads(saved_context_history)
        except Exception as e:
            # TODO: 增加日志
            pass

        return saved_context_history

    async def save_context_history(self, task_directory: str) -> None:
        """保存上下文历史到文件，
        注意：该文件保存在服务端，而非客户端，cline会保存在本地（客户端）
        """
        try:
            filepath = os.path.join(task_directory, CONTEXT_HISTORY)
            await AsyncPath(filepath).write_text(json.dumps(self.context_history_updates, ensure_ascii=False, indent=2))
        except Exception as e:
            # TODO: 增加日志
            pass

    def should_compact_context_window(self, link_code_messages:List[LinkCoderMessage], api, previous_api_req_index: int) -> bool:
        """基于当前窗口的token数量，判断是否要压缩上下文
        params:
        link_code_messages:List[LinkCoderMessage]
        api: LLM
        previous_api_req_index: 上一次api请求的索引
        """
        if previous_api_req_index >= 0:
            previous_request = link_code_messages[previous_api_req_index]
            if previous_request and previous_request.text:
                link_code_api_req_info = LinkCodeApiReqInfo(**json.loads(previous_request.text))
                total_tokens = link_code_api_req_info.input_tokens + link_code_api_req_info.output_tokens
                max_allowed_size = self.get_max_allowed_size(api)
                return total_tokens >= max_allowed_size

        return False

    @staticmethod
    def get_max_allowed_size(api) -> int:
        """获取当前窗口允许的最大token数量
        当前窗口token数量要小于模型支持的最大token数量，需要有一定的buffer空间，防止出现token数量溢出，导致API请求报错
        不同的上下文窗口的buffer大小不同，默认值为80%或-40000
        """
        context_window = api.get_model().context_window or 128000
        # TODO: 特殊模型case，比如deepseek
        if "deepseek" in api.get_model().id.lower():
            context_window = 128000

        if context_window == 64000:
            max_allowed_size = context_window - 27000
        elif context_window == 128000:
            max_allowed_size = context_window - 30000
        elif context_window == 200000:
            max_allowed_size = context_window - 40000
        else:
            max_allowed_size = max(context_window - 40000, context_window * 0.8)

        return max_allowed_size

    ## 以下几个是对话历史上下文的处理，获取删除范围以及删除部分历史后的信息
    def get_next_truncation_range(self, api_messages: List[ChatCompletionMessageParam], current_deleted_range:Optional[List[int]], keep:str) -> List[int]:
        """获取下一个API对话历史删除范围"""
        range_start_index = 2 # 保存 0和1 索引，0和1是user/assistant消息对，内容最完整的
        start_of_rest = current_deleted_range[1] + 1 if current_deleted_range else 2 # 如果对话历史中已经删除一部分了，那么下一次删除范围就不能包含这一块

        if keep == "none":
            messages_to_remove = max(len(api_messages)-start_of_rest, 0)
        elif keep == "last_two":
            messages_to_remove = max(len(api_messages)-start_of_rest-2, 0)
        elif keep == "half":
            messages_to_remove = math.floor((len(api_messages)-start_of_rest)/4)*2 # 保证是个偶数
        else:
            messages_to_remove = math.floor((len(api_messages)-start_of_rest)*3/4/2) * 2 # 保证是个偶数

        range_end_index = start_of_rest + messages_to_remove - 1
        if api_messages[range_end_index] and api_messages[range_end_index]["role"] != "assistant":
            range_end_index -= 1

        return [range_start_index, range_end_index]

    def get_and_alter_truncated_messages(self, api_messages: List[ChatCompletionMessageParam], deleted_range:Optional[List[int]]) -> List[ChatCompletionMessageParam]:
        """删除后的对话信息"""
        if len(api_messages) < 2:
            return api_messages

        start_from_index = deleted_range[1] + 1 if deleted_range else 2

        first_chunk = api_messages[:2]
        second_chunk = api_messages[start_from_index:]
        messages_to_update = first_chunk + second_chunk
        # TODO

        return None

    async def get_new_context_messages_and_metadata(
        self,
        api_conversation_history: List[ChatCompletionMessageParam],
        link_coder_messages: List[LinkCoderMessage],
        api,
        conversation_history_deleted_range: Optional[List[int]] = None,
        previous_api_req_index: Optional[int] = None,
        task_directory: str = None,
        use_auto_condenses: bool = False
    ):
        """获取新的上下文信息和metadata
        api_conversation_history: API对话历史，openai类型的message
        link_coder_messages: 区别于API对话信息，这里记录了更详细的信息，包括规划、动作、反馈
        api: LLm 这里的LLM在对话过程中可能会改变，所以该参数是一个实时更新的 TODO：怎么实时获取当前的LLM API
        conversation_history_deleted_range: 如果窗口的token数量超过规定的值，将删除部分对话历史，[start_index, end_index]
        previous_api_req_index: 上一个API请求的索引
        task_directory: 任务目录，
        use_auto_condenses: 是否自动压缩上下文
        """
        updated_conversation_history_deleted_range = False # 对话历史删除范围是否已经更新

        if not use_auto_condenses:
            # 如果之前的API请求的token数量接近于规定的上下文窗口大小，删除对话历史，释放空间方便新的请求
            if previous_api_req_index >= 0:
                previous_request = link_coder_messages[previous_api_req_index]
                if previous_request and previous_request.text:
                    timestamp = previous_request.timestamp
                    link_code_api_req_info = LinkCodeApiReqInfo(**json.loads(previous_request.text))
                    total_tokens = link_code_api_req_info.input_tokens + link_code_api_req_info.output_tokens
                    max_allowed_size = self.get_max_allowed_size(api)

                    if total_tokens >= max_allowed_size:
                        # 切换不同上下文大小的模型，删除一半对话历史是不够的，比如 Claude支持200k，而deepseek支持64k，
                        # 如果删除一般还剩100k，仍然超过最大允许的token数量，此时，需要删除 3/4
                        keep = "quarter" if total_tokens / 2 > max_allowed_size else "half"
                        pass


    def apply_context_optimizations(self, api_messages: List[ChatCompletionMessageParam], start_from_index: int, timestamp: int):
        pass

    def find_and_potentially_save_file_read_context_history_updates(
        self,
        api_messages: List[ChatCompletionMessageParam],
        start_from_index: int,
        timestamp: int
    ):
        pass

    def get_possible_duplicated_file_reads(self, api_messages: List[ChatCompletionMessageParam], start_from_index: int):
        """"""
        file_read_indices = dict()
        message_file_paths = dict()
        for i in range(start_from_index, len(api_messages)):
            curr_existing_file_reads = []
            if i in self.context_history_updates:
                inner_tuple = self.context_history_updates.get(i)
                if inner_tuple:
                    edit_type = inner_tuple[0]

                    if edit_type == EditType.FILE_MENTION:
                        # 文件提及
                        inner_map = inner_tuple[1]
                        block_index = 1 # TODO: 文件提及block假设在索引1的位置上，为什么这么假设？
                        block_updates = inner_map.get(block_index)
                        if block_updates and len(block_updates)>0:
                            pass










if __name__ == '__main__':
    pass


