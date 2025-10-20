# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/13 13:46
# @Author  : cuils
# @Description:
基于textual和rich实现自定义的用户交互TUI，当前仅支持多轮对话+流式输出
"""
import openai
import threading
import traceback
from datetime import datetime
from openai.types.chat import ChatCompletionMessageParam

from rich import panel, syntax, markdown
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer, Input, Button
from textual.containers import Container, ScrollableContainer, Horizontal


class LLMService:
    def __init__(self, base_url, api_key="EMPTY", model: str = None):
        self.client = openai.Client(api_key=api_key, base_url=base_url)
        self.model = model if model else self.client.models.list().data[0].id

    def chat(self, messages: list[ChatCompletionMessageParam], stream=False):
        retry = 0
        last_exception = None
        while retry < 3:
            try:
                resp = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    stream=stream
                )
                return resp
            except Exception as e:
                retry += 1
                last_exception = e

        print(last_exception)
        return None

    def chat_stream(self, messages: list[ChatCompletionMessageParam]):
        """流式聊天方法"""
        retry = 0
        last_exception = None
        while retry < 3:
            try:
                stream = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    stream=True
                )
                return stream
            except Exception as e:
                retry += 1
                last_exception = e

        print(last_exception)
        return None


def render_message(content, title, border_style):
    if content.strip().startswith("```"):
        # 代码块
        return panel.Panel(
            syntax.Syntax(content, lexer="python", theme="monokai"),
            title=title,
            border_style=border_style,
            padding=(1, 2)
        )
    else:
        return panel.Panel(
            markdown.Markdown(content),
            title=title,
            border_style=border_style,
            padding=(1, 2)
        )


class MessageWidget(Static):
    def __init__(self, text: str, is_user: bool, timestamp: str = None):
        super().__init__()
        self.is_user = is_user
        self.message = text
        self.timestamp = timestamp or datetime.now().strftime("%H:%M:%S")
        self.title = f"User [{self.timestamp}]" if is_user else f"LinkCoder [{self.timestamp}]"
        self.border_style = "blue" if is_user else "green"
        self.update(render_message(text, self.title, self.border_style))


class Display(ScrollableContainer):
    def __init__(self, ):
        super().__init__()
        self.messages: list[MessageWidget] = []
        self.current_streaming_message_widget: MessageWidget = None

    def add_message(self, content, is_user=True):
        """添加消息到显示区域"""
        message = MessageWidget(content, is_user)
        self.messages.append(message)
        self.mount(message)  # 将这个消息挂载到这个容器下面
        self.scroll_end(animate=True)
        return message

    def start_streaming_message(self, is_user=False):
        """开始流式消息显示"""
        self.current_streaming_message_widget = self.add_message("", is_user)

    def append_to_streaming_message(self, content: str):
        """追加内容到当前流式消息"""
        if self.current_streaming_message_widget:
            title = self.current_streaming_message_widget.title
            border_style = self.current_streaming_message_widget.border_style
            last_message_text = self.current_streaming_message_widget.message
            self.current_streaming_message_widget.message += content
            self.current_streaming_message_widget.update(
                render_message(last_message_text + content, title=title, border_style=border_style)
            )
            self.scroll_end(animate=False)  # 流式更新时不使用动画

    def finish_streaming_message(self):
        """完成流式消息显示"""
        self.current_streaming_message_widget = None

    def clear_messages(self):
        for message in self.messages:
            message.remove()
        self.messages = []


class MyApp(App):
    CSS_PATH = "custom.css"
    BINDINGS = [("ctrl+c", "quit", "退出")]
    conversation_history: list[ChatCompletionMessageParam] = []

    def __init__(self):
        super().__init__()
        self.input_message = Input(placeholder="input your task", id="input_message")
        self.messages_display = Display()
        self.llm_service = LLMService(base_url="http://localhost:1234/v1", api_key="EMPTY")

    def compose(self) -> ComposeResult:
        """
        header + 主体交互部分 + footer
        主体交互部分包含 输入 + 对话display 两个部分
        :return:
        """
        yield Header(show_clock=True)
        yield Container(
            # 构建一个水平容器，用于对话展示
            self.messages_display,
            # 构建一个水平容器，放输入框和按钮
            Horizontal(
                self.input_message,
                Button(label="submit", id="submit_button"),
                Button(label="clear", id="clear_button"),
                id="input_container"
            ),
            id="main_container"
        )
        yield Footer()

    def on_mount(self):
        self.title = "遥遥领先"
        self.sub_title = "不要问，赢麻了"
        self.input_message.focus()  # 聚焦输入框
        # 添加欢迎消息
        welcome_message = "欢迎使用LinkCoder！\n\n功能特性：\n- ✅ 多轮交互\n- ✅ 流式响应\n- ✅ \n\n请输入您的问题开始对话..."
        self.messages_display.add_message(welcome_message, is_user=False)

    @on(Input.Submitted, selector="#input_message")
    def input_submitted(self, event: Input.Submitted) -> None:
        """处理输入提交事件"""
        self.send_message()

    @on(Button.Pressed, selector="#clear_button")
    def clear_button(self) -> None:
        self.action_clear_chat()

    @on(Button.Pressed, selector="#submit_button")
    def submit_button(self, event: Button.Pressed) -> None:
        """处理按钮点击事件"""
        self.send_message()

    def send_message(self):
        """将输入的信息，发送到后端，这里暂时将这个信息存放到一个列表中"""
        input_widget = self.query_one(selector="#input_message", expect_type=Input)  # 广度搜索找到匹配的组件，搜索query为 定义的输入组件
        message = input_widget.value.strip()
        input_widget.value = ""  # 清空输入框
        if not message:
            return
        self.conversation_history.append({"role": "user", "content": message})
        # 显示用户消息
        self.messages_display.add_message(message, is_user=True)
        # 使用流式聊天（后台线程，避免阻塞UI）TODO：这里的阻塞想不到啊啊啊啊啊
        threading.Thread(target=self._chat_with_llm_streaming, daemon=True).start()

    def _chat_with_llm_streaming(self):
        """流式聊天方法（在后台线程中执行，避免阻塞UI）"""
        stream = self.llm_service.chat_stream(messages=self.conversation_history)
        if stream:
            # 开始流式消息显示（切回UI线程）
            self.call_from_thread(self.messages_display.start_streaming_message, False)
            full_response = ""
            try:
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        full_response += content
                        # 追加显示（切回UI线程）
                        self.call_from_thread(self.messages_display.append_to_streaming_message, content)
                # 完成流式显示
                self.call_from_thread(self.messages_display.finish_streaming_message)
                if full_response:
                    # 保存完整响应到历史（切回UI线程）
                    self.call_from_thread(self.conversation_history.append,{"role": "assistant", "content": full_response})
            except Exception as e:
                self.call_from_thread(self.messages_display.finish_streaming_message)
                error_msg = f"流式聊天出现异常: {str(e)}-{traceback.format_exc()}"
                self.call_from_thread(self.messages_display.add_message, error_msg, False)
        else:
            content = "LLM异常，无返回，现在将要退出"
            self.call_from_thread(self.messages_display.add_message, content, False)
            self.call_from_thread(self.action_quit)

    def _chat_with_llm(self):
        """非流式聊天方法（保留作为备用）"""
        resp = self.llm_service.chat(messages=self.conversation_history)
        if resp:
            content = resp.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": content})
            self.messages_display.add_message(content, is_user=False)
        else:
            content = "LLM异常，无返回，现在将要退出"
            self.messages_display.add_message(content, is_user=False)
            self.action_quit()

    def action_clear_chat(self):
        """清空对话历史"""
        self.messages_display.clear_messages()
        self.conversation_history = []

        welcome_message = "聊天记录已清空！您可以开始新的对话了。"
        self.messages_display.add_message(welcome_message, is_user=False)

    def action_new_chat(self):
        """开始新对话"""
        self.action_clear_chat()

    def action_quit(self):
        self.exit()


if __name__ == '__main__':
    app = MyApp()
    app.run()