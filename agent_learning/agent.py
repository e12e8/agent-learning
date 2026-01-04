# agent.py
import asyncio
from planner import plan

async def run_agent(task: str) -> str:
    print(f"\nAgent 接收到任务：{task}")

    steps = plan(task)

    results = []

    for step in steps:
        print(f"执行步骤：{step}")
        await asyncio.sleep(1)  # 模拟每一步耗时
        results.append(f"{step} 完成")

    return f"任务完成：{task}\n" + "\n".join(results)
