# agent.py
import asyncio
from planner import plan_task
from tool_registry import TOOLS

def choose_tool(step: str) -> str:
    if "技术" in step:
        return "tech"
    elif "工程" in step or "项目" in step:
        return "project"
    else:
        return "general"

async def run_agent(task: str) -> str:
    print(f"\nAgent 接收到任务：{task}")
    steps = plan_task(task)

    final_result = ""

    for step in steps:
        print(f"执行步骤：{step}")
        await asyncio.sleep(1)

        tool_type = choose_tool(step)
        tool_func = TOOLS[tool_type]

        tool_result = tool_func(task)

        # 🔥 核心：Agent 读取 Tool 的返回结果
        if tool_result["status"] != "ok":
            print("工具执行失败，终止任务")
            break

        final_result += tool_result["content"] + "\n"

        # 🔥 简单反思机制（第一版）
        if tool_result["type"] == "general":
            print("信息偏泛，尝试进一步查询技术信息")
            continue

    return f"任务完成：{task}\n{final_result}"
