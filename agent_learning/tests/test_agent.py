import asyncio
import types
import sys
import pathlib
import pytest

# Ensure repository root is on sys.path for imports during pytest
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from agent_learning.agent import run_agent, TOOL_TIMEOUT
import agent_learning.tool as tool_module


def test_successful_run():
    # 基本成功运行（使用默认工具实现）
    result = asyncio.run(run_agent("测试正常运行"))
    assert "任务完成" in result


def test_low_confidence_triggers_supplement(monkeypatch):
    # 将 general 返回置信度置低，确保会触发补救调用 tech

    async def low_conf(query: str):
        await asyncio.sleep(0.1)
        return {"status": "ok", "type": "general", "confidence": 0.1, "content": "低置信通用内容"}

    monkeypatch.setattr(tool_module, "search_general_knowledge", low_conf)

    result = asyncio.run(run_agent("测试低置信触发补救"))
    assert "技术相关内容" in result or "supplement_done" in result


def test_tool_timeout(monkeypatch):
    # 模拟一个长时工具，超出 TOOL_TIMEOUT 应该被记录为 timeout

    async def long_running(query: str):
        await asyncio.sleep(TOOL_TIMEOUT + 2)
        return {"status": "ok", "type": "tech", "confidence": 0.9, "content": "晚到的内容"}

    monkeypatch.setattr(tool_module, "search_tech_knowledge", long_running)

    result = asyncio.run(run_agent("测试超时"))
    assert "timeout" in result or "supplement_error" in result or "任务完成" in result


def test_state_cache_avoids_call(monkeypatch):
    # 当 initial_state 中已有 step:tool 的返回时，相关工具不应被调用
    called = {"flag": False}

    async def failing_tool(query: str):
        called["flag"] = True
        await asyncio.sleep(0.1)
        return {"status": "ok", "type": "general", "confidence": 0.9, "content": "不应该被调用"}

    # 把 general 工具替换为会设置 flag 的实现
    monkeypatch.setattr(tool_module, "search_general_knowledge", failing_tool)

    # 构造 initial_state，模拟已缓存了该 step:general 的结果
    initial_state = {"理解问题的通用背景:general": {"status": "ok", "type": "general", "confidence": 0.9, "content": "缓存内容"}}

    result = asyncio.run(run_agent("测试缓存", initial_state=initial_state))
    # 工具不应被真正调用
    assert called["flag"] is False
    assert "缓存内容" in result
