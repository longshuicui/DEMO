# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/16 09:23
# @Author  : cuils
# @Description:
TUI实现
"""
import asyncio
from rich import panel, text, syntax, markdown
from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.suggester import SuggestFromList
from textual.widgets import Input, Static, Header, Footer, RichLog


class StreamingRichLog(RichLog):
    """支持流式输出的 RichLog 组件"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_streaming_content = ""
        self.is_streaming = False
        self.streaming_panel = None
        self.panels: list[panel.Panel] = [] # 存储所有的画布，当要流式更新时，只需要更新最后一个画布即可

    def update(self, current_panel: panel.Panel):
        self.panels.append(current_panel)
        if not self.is_streaming:
            self.write(current_panel, animate=True)
        else:
            self.refresh()

    def start_streaming(self, title="Assistant", style="green"):
        """开始流式输出"""
        self.is_streaming = True
        self.current_streaming_content = ""
        # 创建一个初始的空面板
        self.streaming_panel = panel.Panel(
            text.Text("", style="dim"),
            title=f"[{style}]{title}[/{style}]",
            border_style=style,
            padding=(1, 2)
        )
        self.update(self.streaming_panel)
    
    def append_streaming_content(self, content: str):
        """追加流式内容"""
        if not self.is_streaming:
            return
        self.current_streaming_content += content
        # 更新面板内容
        if self.current_streaming_content.strip().startswith("```"):
            # 代码块处理
            try:
                # 尝试解析代码块
                lines = self.current_streaming_content.split('\n')
                code_content = ""
                language = "text"
                
                if len(lines) > 1 and lines[0].strip().startswith("```"):
                    language = lines[0].strip()[3:] or "text"
                    code_content = '\n'.join(lines[1:])
                    if code_content.endswith("```"):
                        code_content = code_content[:-3]
                
                rendered_content = syntax.Syntax(
                    code_content,
                    lexer=language,
                    theme="monokai",
                    line_numbers=False
                )
            except:
                rendered_content = text.Text(self.current_streaming_content)
        else:
            # 普通文本或 Markdown
            try:
                rendered_content = markdown.Markdown(self.current_streaming_content)
            except:
                rendered_content = text.Text(self.current_streaming_content)

        self.streaming_panel.renderable = rendered_content
    
    def finish_streaming(self):
        """完成流式输出"""
        if self.is_streaming:
            self.is_streaming = False
            self.current_streaming_content = ""
            self.streaming_panel = None


class ConsoleApp(App):
    """终端TUI"""
    CSS_PATH = "frontend.css"
    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self):
        super().__init__()
        self.ctx = None
        self.task_loop = None
        self.task_input = None
        self.task_log = StreamingRichLog(id="task_richlog", wrap=True, markup=True)

    def set_context_manager(self, ctx):
        """上下文管理"""
        self.ctx = ctx

    def set_task(self, task_loop):
        self.task_loop = task_loop

    def compose(self) -> ComposeResult:
        """UI组件layout"""
        # 页眉
        yield Header(show_clock=True)
        # 结果展示区
        with Container(id="exec_container"):
            yield self.task_log
        # 输入框
        with Container(id="input_container"):
            yield Input(
                placeholder="输入你的任务",
                id="task_input",
                compact=False,
                suggester=SuggestFromList(suggestions=["help", "exit", "status", "clear"], case_sensitive=True)
            ) # 不要线条
        # 页脚
        yield Footer()

    def on_mount(self) -> None:
        """挂载到屏幕上"""
        self.title = "手搓5nm航空材料"
        self.sub_title = "遥遥领先"
        self.task_input = self.query_one("#task_input", Input)
        self.task_input.focus() # 聚焦到输入框

    @on(Input.Submitted, "#task_input")
    async def on_input_submit(self, event: Input.Submitted):
        """处理输入提交事件"""
        # 用户输入
        utterance = event.value.strip()
        if not utterance:
            return

        # 检查任务状态，如果任务正在运行，输入该如何处理？暂时只做提示，后续将新消息加入消息队列
        if self.task_loop and not self.task_loop.task_state.did_finish_current_task:
            # 如果任务正在运行，显示提示信息，暂不处理
            self.task_log.update(
                panel.Panel("任务正在执行中，请等待当前任务完成...", title="System", style="yellow")
            )
            return

        # 处理特殊命令
        if utterance.lower() in ["help", "exit", "status", "clear"]:
            await self._handle_special_commands(utterance)
            event.input.value = ""
            return

        # 显示用户输入
        self.task_log.update(
            panel.Panel(utterance, title="User", style="red")
        )

        # 清空输入框
        event.input.value = ""

        # 启动任务
        if self.task_loop and self.ctx:
            # 添加用户消息到上下文
            self.ctx.chat_messages.append(
                {"role": "user", "content": utterance}
            )
            # 启动任务
            _ = asyncio.create_task(self.task_loop.start())
            # self.task_loop.start()

    async def _handle_special_commands(self, command: str):
        """处理特殊命令"""
        command = command.lower()
        
        if command == "help":
            help_text = """
可用命令：
- help: 显示帮助信息
- exit: 退出程序
- status: 显示当前任务状态
- clear: 清空聊天记录
            """
            self.task_log.update(
                panel.Panel(help_text.strip(), title="Help", style="green")
            )
        elif command == "exit":
            self.task_loop.stop()
            self.ctx.save_context_history()
            self.exit()
        elif command == "status":
            if self.task_loop:
                status_text = f"任务状态: {'运行中' if not self.task_loop.task_state.did_finish_current_task else '已完成'}"
                self.task_log.update(
                    panel.Panel(status_text, title="Status", style="blue")
                )
            else:
                self.task_log.update(
                    panel.Panel("任务未初始化", title="Status", style="red")
                )
        elif command == "clear":
            self.task_log.clear()
            if self.ctx:
                self.ctx.chat_messages = self.ctx.chat_messages[:1]
            self.task_log.update(
                panel.Panel("聊天记录已清空", title="System", style="yellow")
            )
    
    def start_streaming_response(self):
        """开始流式响应显示"""
        self.task_log.start_streaming()

    def append_streaming_content(self, content: str):
        """追加流式内容"""
        self.task_log.append_streaming_content(content)
    
    def finish_streaming_response(self):
        """完成流式响应显示"""
        self.task_log.finish_streaming()



if __name__ == '__main__':
    asyncio.run(ConsoleApp().run_async())
