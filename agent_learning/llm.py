# llm.py
"""简要：模拟异步调用 LLM 的接口，用于本地调试与测试。"""
import asyncio


async def call_llm(prompt: str) -> str:
    """异步模拟：接收 `prompt` 并返回模拟回复（延迟 1 秒）。"""
    await asyncio.sleep(1)
    return f"【模拟 LLM 回复】针对：{prompt}"
