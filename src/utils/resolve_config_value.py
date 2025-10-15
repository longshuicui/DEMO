#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：DEMO_python 
@File    ：resolve_config_value.py
@Author  ：longshuicui
@Date    ：2025/10/15 21:09 
@Desc    ：
"""
import os
import yaml


def resolve_config_value(*, cli_value, config_value, env_var):
    """修改参数值
    CLI > ENV > Config > Default
    """
    if cli_value is not None:
        return cli_value

    if env_var and os.getenv(env_var):
        return os.getenv(env_var)

    if config_value is not None:
        return config_value
    return None





