# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/25 09:37
# @Author  : cuils
# @Description:
模型返回结果解析，文本块和工具使用
"""

from typing import List, Union


# 已经定义的工具和参数
TOOL_USE_OPEN_TAGS = ["<list_files>", "<read_file>", "<search_files>", "<write_to_file>", "<replace_in_file>", "<attempt_completion>"]
TOOL_PARAM_OPEN_TAGS = ["<path>", "<recursive>", "<regex>", "<file_pattern>", "<content>", "<diff>", "<result>"]


def parse_assistant_message(assistant_message: str):
    """
    流式内容解析，工具块和文本块
    ```text
    <list_files>
    <path> /Users/cuils/lscui/study/link_coder </path>
    <recursive>true</recursive>
    </list_files>
    ```
    """
    content_blocks = []

    curr_text_content_start = 0 # 文本块开始索引
    curr_text_content: TextContent = None
    curr_tool_use_start = 0 # 当前工具 opening tag 开始的索引
    curr_tool_use: ToolUse = None
    curr_param_value_start = 0 # 参数开始索引
    curr_param_name = None

    for i in range(len(assistant_message)): # 从左往右扫描，识别工具、参数、文本块
        curr_char_index = i
        # 解析工具参数，已经获取了当前的参数名称，就是说要解析参数的值是什么
        if curr_tool_use and curr_param_name:
            close_tag = f"</{curr_param_name}>"
            if curr_char_index >= len(close_tag)-1 and assistant_message.startswith(close_tag, curr_char_index-len(close_tag)+1):
                value = assistant_message[curr_param_value_start: curr_char_index-len(close_tag)+1].strip()
                if curr_tool_use.params:
                    curr_tool_use.params[curr_param_name] = value
                else:
                    curr_tool_use.params = {curr_param_name: value}
                curr_param_name = None
            else:
                # 移到下一个字符
                continue

        # 解析工具使用，已经获取了工具，现在需要获取参数名称
        if curr_tool_use and not curr_param_name:
            started_new_param = False
            for tag in TOOL_PARAM_OPEN_TAGS: # 遍历，找到声明了哪个参数
                if curr_char_index >= len(tag) - 1 and assistant_message.startswith(tag, curr_char_index-len(tag)+1):
                    curr_param_name = tag[1:-1]
                    curr_param_value_start = curr_char_index+1
                    started_new_param = True
                    break
            if started_new_param: # 找到param了，直接跳到下一个字符，这个时候就跳到参数解析上去了
                continue

            # 判断 工具使用 closing tag
            tool_closing_tag = f"</{curr_tool_use.name}>"
            if curr_char_index >= len(tool_closing_tag)-1 and assistant_message.startswith(tool_closing_tag, curr_char_index-len(tool_closing_tag)+1):
                # 处理工具参数
                tool_content_slice = assistant_message[curr_tool_use_start: curr_char_index-len(tool_closing_tag)+1].strip()

                # TODO: content参数需要特殊处理，为什么？
                if curr_tool_use.name == "write_to_file" and "<content>"in tool_content_slice:
                    # 防止嵌套tag出现，最左侧和最右侧的分别用 index/rindex 确定索引
                    content_start_index = tool_content_slice.index("<content>")
                    content_end_index = tool_content_slice.rindex("</content>")
                    if content_start_index != -1 and content_end_index != -1 and content_end_index > content_start_index:
                        content_value = tool_content_slice[content_start_index+len("<content>"): content_end_index].strip()
                        if curr_tool_use.params:
                            curr_tool_use.params["content"] = content_value
                        else:
                            curr_tool_use.params = {"content": content_value}

                curr_tool_use.partial = False
                content_blocks.append(curr_tool_use)
                curr_tool_use = None
                curr_text_content_start = curr_char_index+1
                continue

        # 解析文本块/查找工具块
        if not curr_tool_use:
            # 看文本块中有没有出现工具tag
            started_new_tool = False
            for tag in TOOL_USE_OPEN_TAGS:
                if curr_char_index >= len(tag) - 1 and assistant_message.startswith(tag, curr_char_index - len(tag) + 1):
                    # 识别到 <tool_name>
                    if curr_text_content:
                        curr_text_content.content = assistant_message[curr_text_content_start: curr_char_index - len(tag) + 1].strip()
                        curr_text_content.partial = False # 出现工具调用内容，表示内容文本描述结束了
                        if len(curr_text_content.content) > 0:
                            content_blocks.append(curr_text_content)
                        curr_text_content = None
                    else:
                        # 没有文本块就新建文本块
                        content = assistant_message[curr_text_content_start: curr_char_index - len(tag) + 1].strip()
                        if len(content) > 0:
                            content_blocks.append(TextContent(content=content, partial=False))

                    # 当前使用的工具，还没有发现 closing tag，所以partial为True
                    curr_tool_use = ToolUse(name=tag[1:-1], params=None, partial=True)
                    curr_tool_use_start = curr_char_index + 1 # <tool_name>START_INDEX  内容在opening tag 后面
                    started_new_tool = True
                    break # TODO: 找到工具就终止循环，因为每轮仅能使用一个工具

            if started_new_tool: # 获取到新工具，直接跳到下一个字符
                continue

            # 如果不是从<tool_name> 开始，那么一定是一个文本块 TODO: 是这个道理，但是在解析过程中，`<tool_name` 这种是不会作为一个工具的
            if not curr_text_content:
                curr_text_content_start = curr_char_index
                curr_text_content = TextContent(content="", partial=True) # 这里只是初始化了一个对象

    if curr_tool_use and curr_param_name:
        # 边界情况处理，正常情况，curr_tool_use 此时为None
        if curr_tool_use.params:
            curr_tool_use.params[curr_param_name] = assistant_message[curr_param_value_start:].strip()
        else:
            curr_tool_use.params = {curr_param_name: assistant_message[curr_param_value_start:].strip()}

    if curr_tool_use:
        content_blocks.append(curr_tool_use)
    elif curr_text_content:
        curr_text_content.content = assistant_message[curr_text_content_start:].strip()
        if len(curr_text_content.content) > 0:
            content_blocks.append(curr_text_content)

    return content_blocks







if __name__ == '__main__':
    msg = """
    <list_files>
    <path> /Users/cuils/lscui/study/link_coder </path>
    <recursive>true</recursive>
    </list_files>
    """
    blocks = parse_assistant_message(msg)

    for block in blocks:
        print(block)















