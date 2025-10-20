# -*- coding: utf-8 -*-
"""
# @Time    : 2025/9/28 10:23
# @Author  : cuils
# @Description:
"""
GENERAL_WITHOUT_USE_TOOL = """在你的回复中，没有使用工具，请重试。
如果你完成了用户的任务，使用 `complete` 工具，将你的结果使用该工具提供给用户，注意该结果内容应该是详细的，再次总结是不允许的；否则，如果你没有完成这个任务，请继续处理。
[该消息为自动消息，请勿直接回复]
"""

GENERAL_WITH_USE_TOOL = """
`{tool_name}` Result:

<{tool_name}>
{tool_result}
</{tool_name}>
"""

NO_TOOL_USED = """
在你的回复中，没有使用工具，请重试。

# 工具使用指令
使用XML格式表示工具使用，格式如下：
<tool_name>
<parameter1_name>value1</parameter1_name>
<parameter2_name>value2</parameter2_name>
...
</tool_name>

使用示例：
<attempt_completion>
<result>
I have completed the task...
</result>
</attempt_completion>

必须遵循以上格式，保证正确解析和执行。

# 下一步
如果你完成了用户的任务，使用 `attempt_completion` 工具；否则，如果你没有完成这个任务，请继续处理。
[该消息为自动消息，请勿直接回复]
"""
