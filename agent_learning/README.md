# Agent 学习项目（演示版）

简介
---
这是一个用于学习和演示基于异步工具调用的简易 Agent 架构的小项目。项目实现了 Planner → Executor → Reflection 的闭环，并带有本地持久化（文件）和结构化决策日志，方便调试与面试演示。

项目目标
---
- 演示 Agent 的基本架构与决策闭环（拆解任务、并发调用工具、评估与补救）。
- 提供可观测性（`logs/decision_*.json`、`logs/metrics_*.json`）。
- 演示短期记忆（`state.py` 的文件持久化实现）。

关键文件说明
---
- `main.py`: 程序入口，构建并发的 `run_agent` 调用用于演示。
- `agent.py`: Agent 的核心实现（`run_agent`）：负责调用 `planner`、并发调用 `TOOLS`、评估结果、补救、记录 `decision_log` 和写入 `logs/`。
- `planner.py`: 把任务拆成若干 `steps`（演示用静态拆解）。
- `tool.py`: 模拟的异步工具实现（返回 `status`/`confidence`/`content`）。
- `tool_registry.py`: 将工具函数按类型注册为 `TOOLS` 字典。
- `state.py`: 简单的本地文件持久化实现 `FileState`，支持 `get`/`set`/`save`（用于跨 run 缓存）。
- `logs/`: 运行时生成的结构化决策日志与指标（`decision_<trace>.json`、`metrics_<trace>.json`）。
- `tests/`: 单元测试，展示各模块预期行为（建议先阅读测试以理解功能）。

如何运行（本地）
---
1. 安装依赖（已将 `pytest` 列入 `requirements.txt`）：

```bash
python -m pip install -r requirements.txt
```

2. 运行单元测试：

```bash
python -m pytest -q
```

3. 运行演示（生成决策日志）：

```bash
python -m agent_learning.main
```

运行后会在 `agent_learning/logs/` 看到 `decision_*.json` 与 `metrics_*.json` 文件。

如何在面试中讲解（1 页要点）
---
1. 项目目的与架构：说明这是一个“工具型 Agent”实现，分为 Planner（拆任务）、Executor（并发调用工具）、Reflection（评估 + 补救）。强调事件驱动与异步并发是关键实现点。
2. 关键数据流：展示 `run_agent` 中的 `steps -> candidate_tools -> asyncio.gather -> results -> decision_log -> final_result` 的流程图。
3. 反思层（亮点）：基于 `confidence` 判断是否补救（调用 `tech`），并记录 `decision_log`，如果置信度低，触发补救是工程上常见的鲁棒性策略。
4. 可观测性与工程化：项目写入 `logs/` 的决策与指标，便于审计与调优；实现了文件后端 `state` 做跨 run 缓存，演示了生产环境常用的缓存思路。
5. 面试演示建议：准备一条 trace（`decision_*.json`），逐条解释为什么选该工具、何时触发补救、如何衡量成功（supplement_rate/timeout_rate）。

下一步学习动作（建议）
---
- 本地跑一次 `main.py` 并打开一个 `decision_*.json`，我可以逐条帮你解读（我会带你一步步看）。
- 修改一个工具返回（非常小改动），再跑一次看输出差异，帮助理解数据流。

---
如果你准备好了，我现在就带你执行“运行一次并逐条解读 + 做一个小改动并观察变化”的流程。
