# agent.py
import asyncio
from task import Task
from llm import call_llm

async def run_agent(name: str, task: Task):
    print(f"[{name}] 开始处理任务：{task.description}")

    await asyncio.sleep(1)  # 模拟规划
    plan = f"{name} 的执行计划"

    response = await call_llm(plan)
    task.result = response

    print(f"[{name}] 任务完成")
