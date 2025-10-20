# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/23 15:33
# @Author  : cuils
# @Description:
"""
from pydantic import BaseModel
from typing import List, Dict, Union, Optional


class TextContent(BaseModel):
    """文本内容"""
    type: str = "text"
    content: str
    partial: bool  # 处理流式返回时，因为是边读边解析，该字段表示是否已经解析结束


class ToolUse(BaseModel):
    """工具使用"""
    type: str = "tool_use"
    name: str
    params: Optional[Dict[str, str]]  # TODO，工具的格式待定
    partial: bool


class TaskState(BaseModel):
    """任务状态"""
    # 任务状态：初始化、取消、终端、放弃
    did_finish_current_task: bool = True
    is_initialized: bool = False
    abort: bool = False
    did_finish_aborting_stream: bool = False
    abandoned: bool = False


    # streaming flags
    is_streaming: bool = False  # 是否流式响应
    is_awaiting_for_first_chunk: bool = False  # 是否等待第一个chunk
    did_complete_reading_stream: bool = False  # 是否完成流式内容读取

    # content processing
    current_streaming_content_index: int = 0  # 流式响应，当前内容块/工具块的索引
    user_message_content_ready: bool = False # 用户消息是否已经准备就绪
    # TODO: 以下的用户消息和助手消息都是单个对话轮次
    user_message_content: List[TextContent] = []
    assistant_message_content: List[Union[TextContent, ToolUse]] = []  # 助手消息，要么是文本内容，要么是工具使用信息

    # tool execute flags 工具执行标记
    did_reject_tool: bool = False
    did_already_use_tool: bool = False
    did_edit_file:bool = False

    # context and history
    conversation_history_delete_range: Optional[List[int]] = None

    # auto context summarization
    currently_summarizing: bool = False # 是否已经做过总结
    last_auto_compact_trigger_index: Optional[int] = None # 如果做过总结，记录最后一次触发总结的索引

    # Focus Chain / TodoList management
    api_request_count: int = 0
    api_requests_since_last_todo_update: int = 0 # 最近一次 Todolist 更新api请求次数
    current_focus_chain_checklist: Optional[str] = None
    todo_list_was_updated_by_user: bool = False

    # TODO: 以下状态参数，主要是Cline的实现，LinkCoder暂时不考虑
    # presentation locks (for front-end) 前端展示锁
    present_assistant_message_locked: bool = False
    present_assistant_message_has_pending_updates: bool = False

    # error tracking
    consecutive_mistake_count: int = 0
    did_auto_retry_failed_api_request: bool = False
    checkpoint_manager_error_message: Optional[str] = None

    # consecutive request tracking
    consecutive_auto_approved_requests_count: int = 0

    # plan mode specific state
    is_awaiting_plan_response: bool = False
    did_respond_to_plan_ask_by_switching_mode: bool = False

    # ask / response handling
    ask_response: bool = False # TODO
    ask_response_text: Optional[str] = None
    ask_response_images: Optional[List[str]] = None
    ask_response_files: Optional[List[str]] = None
    last_message_ts: Optional[int] = None # 这个ts不知道是什么意思


class StepState(BaseModel):
    """
    单轮交互状态，该类定义每一个step的信息，包含用用户输入、LLM回复、工具调用结果
    """

