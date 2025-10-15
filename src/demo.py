#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：DEMO_python 
@File    ：demo.py
@Author  ：longshuicui
@Date    ：2025/9/28 22:32 
@Desc    ：

1. asyncio.create_task
显式地把协程包装成一个 Task 并立即调度，让它后台运行。
	•	特点：
	•	任务一旦创建就会加入事件循环，不需要等 await 就开始执行。
	•	可以在别的地方 await 它，也可以用 task.cancel() 取消。
	•	常见用途：
	•	启动一个“后台任务”，继续做别的事情，稍后再收结果。
	•	想要对单个 task 做操作（取消、检查状态等）。

2. asyncio.gather
	•	作用：并发运行一组协程，并在它们都完成后返回结果。
	•	特点：
	•	接收多个协程/任务，全部执行完才返回。
	•	适合“我要同时跑多个任务，并且一起收结果”。
	•	返回值是按传入顺序排列的结果列表。

```python
import asyncio

async def a():
    await asyncio.sleep(2)
    print("a done")

async def b():
    await asyncio.sleep(3)
    print("b done")

async def main():
    task1 = asyncio.create_task(a())
    task2 = asyncio.create_task(b())

    # 这里可以做别的事
    print("tasks started...")

    # 最后等待所有任务完成
    await asyncio.gather(task1, task2)

asyncio.run(main())
```
"""
import time
import asyncio


async def a():
    await asyncio.sleep(2)
    print("aaaaaa")

async def b():
    await asyncio.sleep(5)
    print("bbbbbb")


async def main1():
    await asyncio.gather(a(), b())

async def main2():
    task1 = asyncio.create_task(a()) #
    task2 = asyncio.create_task(b())

    await task1
    await task2


if __name__ == '__main__':
    start = time.time()
    asyncio.run(main2())
    print(time.time()-start)