# llm.py
import asyncio

async def call_llm(prompt: str) -> str:
    print("模型处理中...")
    await asyncio.sleep(2)   # 模拟模型慢响应
    return f"【模拟模型回复】{prompt}"