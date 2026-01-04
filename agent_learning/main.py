# main.py
import asyncio
from agent import run_agent

async def main():
    """主函数，启动三个并发的Agent任务并处理结果。

    该函数创建三个异步任务，分别请求Agent解释'Agent'、'async'和'asyncio'的概念，
    使用asyncio.gather并发执行所有任务，并在所有任务完成后打印结果。
    """
    # 定义三个并发执行的Agent任务，每个任务处理不同的查询请求
    tasks = [
        run_agent("解释什么是 Agent"),
        run_agent("解释什么是 async"),
        run_agent("解释什么是 asyncio")
    ]

    # 并发执行所有任务并等待结果返回
    results = await asyncio.gather(*tasks)

    print("\n=== 所有任务完成 ===")
    for r in results:
        print(r)

if __name__ == "__main__":
    asyncio.run(main())
