# -*- coding: utf-8 -*-
"""
# @Time    : 2025/10/15 13:19
# @Author  : cuils
# @Description:
"""
import difflib

a = "aaaaa\nbbbba\ncccccc"
b = "aaaaa\nbcbba\ncccacc"


differ = difflib.Differ()
cmp = differ.compare(a.splitlines(), b.splitlines())
print("\n".join(cmp))

cmp = difflib.ndiff(a.splitlines(), b.splitlines())
print("\n".join(cmp))




