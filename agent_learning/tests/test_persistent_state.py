import asyncio
from pathlib import Path
import tempfile

import pytest

from agent_learning.state import FileState
from agent_learning import tool as tool_module
from agent_learning.agent import run_agent


def test_persistent_state_prevents_second_call(tmp_path, monkeypatch):
    # 第一次运行，持久化 store 为空，应正常调用工具并写入持久化
    state_file = tmp_path / "persist_state.json"
    store = FileState(state_file)

    # 保证原始工具能被调用一次并写入
    result1 = asyncio.run(run_agent("持久化测试", persistent_state=store))
    assert state_file.exists()

    # 替换工具为会抛异常的实现，若持久化生效则不会被调用
    called = {"flag": False}

    async def bad_tool(q: str):
        called["flag"] = True
        raise RuntimeError("should not be called")

    monkeypatch.setattr(tool_module, "search_general_knowledge", bad_tool)

    # 再次运行，应读取持久化并避免调用 bad_tool（即 called 仍为 False）
    result2 = asyncio.run(run_agent("持久化测试", persistent_state=store))
    assert called["flag"] is False
    assert "任务完成" in result2
