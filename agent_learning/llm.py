# llm.py
import asyncio

async def call_llm(prompt: str) -> str:
    await asyncio.sleep(1)
    return f"【模拟 LLM 回复】针对：{prompt}"
