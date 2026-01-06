# agent.py
import asyncio
from planner import plan_task
from tool_registry import TOOLS


def need_more_info(result: dict) -> bool:
    """
    判断 Tool 返回的信息是否足够
    """
    return result.get("confidence", 0) < 0.6
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

    tasks = []  # 🔥 并发任务列表

    for step in steps:
        print(f"准备执行步骤：{step}")
        tool_type = choose_tool(step)
        tool_func = TOOLS[tool_type]

        # ⚠️ 注意：这里没有 await
        tasks.append(tool_func(task))

    # 🔥 统一并发执行
    results = await asyncio.gather(*tasks)

    final_result = ""

    for result in results:
        if result["status"] != "ok":
            print("工具执行失败，跳过")
        continue

    # 第一次工具返回
    final_result += result["content"] + "\n"

    # ===== 反馈闭环开始 =====
    if need_more_info(result):
        print("信息不充分，尝试使用技术工具补充")

        tech_tool = TOOLS["tech"]
        tech_result = await tech_tool(task)

        if tech_result["status"] == "ok":
            final_result += tech_result["content"] + "\n"
    # ===== 反馈闭环结束 =====


    return f"任务完成：{task}\n{final_result}"

    print(f"\nAgent 接收到任务：{task}")
    steps = plan_task(task)

    final_result = ""

    for step in steps:
        print(f"执行步骤：{step}")
        await asyncio.sleep(1)

        tool_type = choose_tool(step)
        tool_func = TOOLS[tool_type]

        # 调用相应的工具函数处理当前任务步骤
        tool_result = await tool_func(task)


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