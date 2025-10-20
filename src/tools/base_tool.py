# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/16 17:10
# @Author  : cuils
# @Description:
"""
from typing import Optional, List, Dict
from src.tools.basic import ToolParameter


class BaseTool:
    """基础工具类"""
    @property
    def name(self) -> str:
        return self.hermes_definition()["function"]["name"]

    @property
    def description(self) -> str:
        return self.hermes_definition()["function"]["description"]

    @property
    def parameters(self) -> List[ToolParameter]:
        """解析hermes格式"""
        hermes_params = self.hermes_definition()["function"]["parameters"]["properties"]
        required = self.hermes_definition()["function"]["parameters"]["required"]
        tool_parameters: List[ToolParameter] = []
        for name in hermes_params:
            tool_param = ToolParameter(
                name=name,
                type=hermes_params[name]["type"],
                description=hermes_params[name]["description"],
                required=True if name in required else False
            )
            tool_parameters.append(tool_param)
        return tool_parameters

    def execute(self, arguments):
        """执行工具"""
        raise NotImplementedError

    @property
    def hermes_definition(self):
        """openai hermes 风格定义"""
        raise NotImplementedError

    @property
    def xml_definition(self):
        """xml风格定义"""
        format = """
## {tool_name}
Description: {description}
Parameters:\n{parameters}
Usage:\n{usage}
"""
        text_lines = []
        xml_lines = [f"<{self.name}>"]
        for param in self.parameters:
            line = f"<{param.name}>{param.description}</{param.name}>"
            xml_lines.append(line)
            _line = f"    - {param.name}: [{'required' if param.required else 'optional'}] {param.description}"
            text_lines.append(_line)
        xml_lines.append(f"</{self.name}>")
        usage = "\n".join(xml_lines)
        parameters = "\n".join(text_lines)
        return format.format(tool_name=self.name, description=self.description, parameters=parameters, usage=usage)