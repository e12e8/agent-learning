# main.py - 程序入口文件
# 这里可以启动 Agent 或调用其他模块
from agent import run_agent
import asyncio
async def main():
    """主程序入口函数
    
    该函数负责启动多个Agent实例并并行运行它们。
    通过asyncio.gather()并发执行所有Agent任务，并等待所有任务完成。
    """
    print("主程序 开始运行")

    # 创建Agent任务列表
    agents=[
        run_agent("Agent-1"),
        run_agent("Agent-2"),
        run_agent("Agent-3")

    ]
    # 并发执行所有Agent任务，并等待所有任务完成
    await asyncio.gather(*agents)
if __name__ == "__main__":
        asyncio.run(main())