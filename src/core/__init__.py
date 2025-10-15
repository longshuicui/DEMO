#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：DEMO 
@File    ：__init__.py
@Author  ：longshuicui
@Date    ：2025/9/14 11:17 
@Desc    ：
"""
from pydantic import BaseModel
from typing import List, Optional, Dict



class TaskState(BaseModel):
    abort:bool=False


class ApiConversationHistory(BaseModel):
    conversations:List["Block"]=[]


class Block(BaseModel):
    role:str="user"
    content:str=""



block = Block().model_json_schema()
print(block)