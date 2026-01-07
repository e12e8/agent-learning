"""Agent 执行模块：包含 Planner 拆解、工具并发调用、反思补救与结构化决策日志。"""

import asyncio
import time
import uuid
from agent_learning.planner import plan_task
from agent_learning.tool_registry import TOOLS
from agent_learning.state import FileState


def need_more_info(result: dict) -> bool:
    """
    判断 Tool 返回的信息是否足够
    """
    return result.get("confidence", 0) < 0.6


def choose_candidate_tools(step: str) -> list[str]:
    """
    为并发执行准备候选工具列表
    """
    if "技术" in step:
        return ["tech", "general"]
    elif "工程" in step or "项目" in step:
        return ["project", "tech"]
    else:
        return ["general"]


# 全局超时配置（秒）
TOOL_TIMEOUT = 3


async def run_agent(task: str, initial_state: dict | None = None, persistent_state: FileState | None = None) -> str:
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    print(f"\nAgent 接收到任务：{task} (trace={trace_id})")

    # Planner 拆解任务
    steps = plan_task(task)

    # state 用于本次任务内的短期记忆，避免重复调用相同工具
    # 内存 state 用于当前 run；persistent_state 为可选的跨 run 文件存储
    state: dict = initial_state.copy() if initial_state else {}

    decision_log: list[dict] = []
    final_result = ""

    for step in steps:
        step_start = time.time()
        print(f"执行步骤：{step}")
        await asyncio.sleep(0)  # 协作式调度点

        candidate_tools = choose_candidate_tools(step)
        decision_log.append({
            "time": time.time(),
            "trace_id": trace_id,
            "step": step,
            "candidate_tools": candidate_tools,
        })

        tasks = []
        # 存放预先命中的缓存结果（无需调用工具）
        cached_results = []

        for tool_type in candidate_tools:
            tool_func = TOOLS.get(tool_type)
            key = f"{step}:{tool_type}"
            # 先查询持久化存储（如果提供）
            persisted = None
            if persistent_state:
                try:
                    persisted = persistent_state.get(key)
                except Exception:
                    persisted = None

            if persisted is not None:
                cached_results.append(persisted)
                decision_log.append({
                    "time": time.time(),
                    "trace_id": trace_id,
                    "step": step,
                    "tool": tool_type,
                    "action": "persistent_cache_hit",
                })
                continue

            if key in state:
                # 内存缓存命中
                cached_results.append(state[key])
                decision_log.append({
                    "time": time.time(),
                    "trace_id": trace_id,
                    "step": step,
                    "tool": tool_type,
                    "action": "cache_hit",
                })
                continue

            if tool_func:
                # 使用 wait_for 包装每个工具调用，避免单个工具阻塞
                tasks.append(asyncio.wait_for(tool_func(task), timeout=TOOL_TIMEOUT))

        if not tasks and not cached_results:
            # 既没有可调用的工具也没有缓存结果，跳过该步骤
            decision_log.append({
                "time": time.time(),
                "trace_id": trace_id,
                "step": step,
                "action": "no_tools",
                "message": "未找到可用工具，跳过"
            })
            continue

        # 只有缓存命中且没有需要调用的工具，直接选缓存中最佳结果并跳过后续并发调用逻辑
        if cached_results and not tasks:
            best_cached = None
            best_c = -1
            for cres in cached_results:
                c = cres.get("confidence", 0.5)
                if cres.get("status") == "ok" and c > best_c:
                    best_c = c
                    best_cached = cres

            if best_cached:
                final_result += best_cached.get("content", "") + "\n"
                decision_log.append({
                    "time": time.time(),
                    "trace_id": trace_id,
                    "step": step,
                    "action": "use_cache_best",
                    "best_confidence": best_c,
                })
                # 若置信度不足，也可以执行补救逻辑（与普通流程一致）
                if need_more_info(best_cached):
                    tech_tool = TOOLS.get("tech")
                    if tech_tool:
                        try:
                            tech_result = await asyncio.wait_for(tech_tool(task), timeout=TOOL_TIMEOUT)
                            if tech_result.get("status") == "ok":
                                final_result += tech_result.get("content", "") + "\n"
                                decision_log.append({
                                    "time": time.time(),
                                    "trace_id": trace_id,
                                    "step": step,
                                    "action": "supplement_done",
                                    "tool": "tech",
                                    "confidence": tech_result.get("confidence", 0.5),
                                })
                        except Exception as e:
                            decision_log.append({
                                "time": time.time(),
                                "trace_id": trace_id,
                                "step": step,
                                "action": "supplement_error",
                                "tool": "tech",
                                "message": str(e),
                            })
                # 完成该 step 的处理
                decision_log.append({
                    "time": time.time(),
                    "trace_id": trace_id,
                    "step": step,
                    "action": "step_complete",
                    "duration": time.time() - step_start,
                })
                continue

        # 并发执行候选工具并把缓存结果合并
        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        # 把缓存命中追加到结果列表（保持与 tasks 对应的顺序不重要）
        results = list(results) + cached_results

        # 评估结果并处理异常/超时
        best_result = None
        best_confidence = -1

        for idx, res in enumerate(results):
            tool_name = candidate_tools[idx]
            entry = {
                "time": time.time(),
                "trace_id": trace_id,
                "step": step,
                "tool": tool_name,
            }

            if isinstance(res, asyncio.TimeoutError) or isinstance(res, asyncio.CancelledError):
                entry.update({"status": "timeout", "confidence": 0.0, "message": "timeout"})
                decision_log.append(entry)
                continue

            if isinstance(res, Exception):
                entry.update({"status": "error", "confidence": 0.0, "message": str(res)})
                decision_log.append(entry)
                continue

            # 正常返回 dict
            entry.update({
                "status": res.get("status"),
                "confidence": res.get("confidence", 0.5),
            })
            decision_log.append(entry)

            confidence = res.get("confidence", 0.5)
            if confidence > best_confidence and res.get("status") == "ok":
                best_confidence = confidence
                best_result = res
                # 将有效结果写入内存 state，并在提供 persistent_state 时写入持久化
                try:
                    tool_type_for_state = res.get("type") or "unknown"
                    state_key = f"{step}:{tool_type_for_state}"
                    state[state_key] = res
                    if persistent_state:
                        try:
                            persistent_state.set(state_key, res)
                        except Exception:
                            pass
                except Exception:
                    pass

        decision_log.append({
            "time": time.time(),
            "trace_id": trace_id,
            "step": step,
            "action": "choose_best",
            "best_confidence": best_confidence,
        })

        if not best_result:
            decision_log.append({
                "time": time.time(),
                "trace_id": trace_id,
                "step": step,
                "action": "no_valid_result",
                "message": "工具执行失败或无有效结果，跳过"
            })
            continue

        final_result += best_result.get("content", "") + "\n"

        # 反思与补救
        if need_more_info(best_result):
            decision_log.append({
                "time": time.time(),
                "trace_id": trace_id,
                "step": step,
                "action": "supplement",
                "reason": "low_confidence",
                "best_confidence": best_confidence,
            })

            tech_tool = TOOLS.get("tech")
            if tech_tool:
                try:
                    tech_result = await asyncio.wait_for(tech_tool(task), timeout=TOOL_TIMEOUT)
                    if tech_result.get("status") == "ok":
                        final_result += tech_result.get("content", "") + "\n"
                        decision_log.append({
                            "time": time.time(),
                            "trace_id": trace_id,
                            "step": step,
                            "action": "supplement_done",
                            "tool": "tech",
                            "confidence": tech_result.get("confidence", 0.5),
                        })
                except Exception as e:
                    decision_log.append({
                        "time": time.time(),
                        "trace_id": trace_id,
                        "step": step,
                        "action": "supplement_error",
                        "tool": "tech",
                        "message": str(e),
                    })

        step_end = time.time()
        decision_log.append({
            "time": time.time(),
            "trace_id": trace_id,
            "step": step,
            "action": "step_complete",
            "duration": step_end - step_start,
        })

    # 将结构化决策日志写入 JSON 文件，便于审计与展示
    try:
        import json
        from pathlib import Path

        logs_dir = Path(__file__).resolve().parent / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        decision_path = logs_dir / f"decision_{trace_id}.json"
        with decision_path.open("w", encoding="utf-8") as f:
            json.dump(decision_log, f, ensure_ascii=False, indent=2)

        # 计算简单指标
        steps_completed = sum(1 for e in decision_log if e.get("action") == "step_complete")
        supplement_count = sum(1 for e in decision_log if e.get("action") in ("supplement", "supplement_done"))
        timeout_count = sum(1 for e in decision_log if e.get("status") == "timeout")
        error_count = sum(1 for e in decision_log if e.get("status") == "error")

        metrics = {
            "trace_id": trace_id,
            "steps_completed": steps_completed,
            "supplement_count": supplement_count,
            "timeout_count": timeout_count,
            "error_count": error_count,
            "supplement_rate": (supplement_count / steps_completed) if steps_completed else 0.0,
            "timeout_rate": (timeout_count / max(1, len(decision_log))) ,
        }

        metrics_path = logs_dir / f"metrics_{trace_id}.json"
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
    except Exception:
        decision_path = None
        metrics_path = None

    total_time = time.time() - start_time
    # 返回中包含 trace_id 及日志文件路径，便于面试演示
    return (
        f"任务完成：{task}\n\n"
        f"【trace_id】 {trace_id}\n"
        f"【总耗时】 {total_time:.2f}s\n"
        f"【决策日志】 {decision_path}\n"
        f"【指标文件】 {metrics_path}\n\n"
        f"【最终结果】\n{final_result}"
    )
