import re
from pathlib import Path
import json
import asyncio

from agent_learning.agent import run_agent


def test_decision_log_and_metrics_written():
    out = asyncio.run(run_agent("测试日志与指标"))
    # 从返回字符串提取 trace_id
    m = re.search(r"【trace_id】\s+([0-9a-fA-F-]+)", out)
    assert m, "无法在输出中找到 trace_id"
    trace_id = m.group(1)

    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    decision_path = logs_dir / f"decision_{trace_id}.json"
    metrics_path = logs_dir / f"metrics_{trace_id}.json"

    assert decision_path.exists(), f"决策日志文件缺失: {decision_path}"
    assert metrics_path.exists(), f"指标文件缺失: {metrics_path}"

    dec = json.loads(decision_path.read_text(encoding="utf-8"))
    met = json.loads(metrics_path.read_text(encoding="utf-8"))

    assert isinstance(dec, list)
    assert "trace_id" in met and met["trace_id"] == trace_id
    assert "supplement_rate" in met and "timeout_rate" in met
