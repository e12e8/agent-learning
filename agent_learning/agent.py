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


async def run_agent(
    task: str,
    initial_state: dict | None = None,
    persistent_state: FileState | None = None
) -> str:
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    print(f"\nAgent 接收到任务：{task} (trace={trace_id})")

    # 《Planner Layer（规划层）》
    # 输入：Task（自然语言目标）
    # 输出：Steps（可执行的子目标）
    # 特点：
    #   1、不调用 Tool
    #   2、不关心执行方式
    #   3、只负责“把任务拆清楚”
    # 📌 到这里为止：Agent 仍然处于“纯思考阶段”
    steps = plan_task(task)

    # 《State Layer（状态层）》
    # state：本次 run 内的短期记忆（内存态）
    # persistent_state：跨 run 的长期记忆（文件态）
    # 目的：避免重复调用 Tool，形成“经验复用”
    state: dict = initial_state.copy() if initial_state else {}

    decision_log: list[dict] = []
    final_result = ""

    # <<================ Agent Control Loop（控制循环） =================>>
    # Agent 的“生命循环”
    # 每一个 step 都会经历：Decision → Execution → Reflection → State Update
    for step in steps:
        step_start = time.time()
        print(f"执行步骤：{step}")
        await asyncio.sleep(0)  # 协作式调度点

        # 《Decision Layer（决策层）》
        # 职责：
        #   1、只读信息（step / state）
        #   2、不执行任何能力
        #   3、只产出“策略选择”（用哪些 Tool）
        candidate_tools = choose_candidate_tools(step)
        decision_log.append({
            "time": time.time(),
            "trace_id": trace_id,
            "step": step,
            "candidate_tools": candidate_tools,
        })

        tasks = []
        cached_results = []

        # 《State Read（状态读取）》
        # 优先从持久化 / 内存缓存中命中结果
        for tool_type in candidate_tools:
            tool_func = TOOLS.get(tool_type)
            key = f"{step}:{tool_type}"

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
                cached_results.append(state[key])
                decision_log.append({
                    "time": time.time(),
                    "trace_id": trace_id,
                    "step": step,
                    "tool": tool_type,
                    "action": "cache_hit",
                })
                continue

            # 《Execution Layer（执行层）》
            # 职责：
            #   1、把“策略选择”变成真实行动
            #   2、调用 Tool（不可控）
            #   3、可能失败 / 超时 / 异常
            if tool_func:
                tasks.append(
                    asyncio.wait_for(tool_func(task), timeout=TOOL_TIMEOUT)
                )

        if not tasks and not cached_results:
            decision_log.append({
                "time": time.time(),
                "trace_id": trace_id,
                "step": step,
                "action": "no_tools",
                "message": "未找到可用工具，跳过"
            })
            continue

        # 《Fast Path（纯缓存路径）》
        # 无需执行 Tool，直接评估缓存结果
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

                # 《Reflection Layer（反思层）》
                # 判断结果是否“足够好”
                if need_more_info(best_cached):
                    tech_tool = TOOLS.get("tech")
                    if tech_tool:
                        try:
                            tech_result = await asyncio.wait_for(
                                tech_tool(task), timeout=TOOL_TIMEOUT
                            )
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

                decision_log.append({
                    "time": time.time(),
                    "trace_id": trace_id,
                    "step": step,
                    "action": "step_complete",
                    "duration": time.time() - step_start,
                })
                continue

        # 《Execution Layer（并发执行）》
        results = []
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        results = list(results) + cached_results

        # 《Reflection Layer（结果评估）》
        # 职责：
        #   1、判断成功 / 失败
        #   2、比较多个结果质量
        #   3、选出“当前最优解”
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
                entry.update({"status": "timeout", "confidence": 0.0})
                decision_log.append(entry)
                continue

            if isinstance(res, Exception):
                entry.update({"status": "error", "confidence": 0.0, "message": str(res)})
                decision_log.append(entry)
                continue

            entry.update({
                "status": res.get("status"),
                "confidence": res.get("confidence", 0.5),
            })
            decision_log.append(entry)

            confidence = res.get("confidence", 0.5)
            if confidence > best_confidence and res.get("status") == "ok":
                best_confidence = confidence
                best_result = res

                # 《State Update（状态写入）》
                try:
                    tool_type_for_state = res.get("type") or "unknown"
                    state_key = f"{step}:{tool_type_for_state}"
                    state[state_key] = res
                    if persistent_state:
                        persistent_state.set(state_key, res)
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
            })
            continue

        final_result += best_result.get("content", "") + "\n"

        # 《Reflection Layer（补救策略）》
        if need_more_info(best_result):
            decision_log.append({
                "time": time.time(),
                "trace_id": trace_id,
                "step": step,
                "action": "supplement",
            })

            tech_tool = TOOLS.get("tech")
            if tech_tool:
                try:
                    tech_result = await asyncio.wait_for(
                        tech_tool(task), timeout=TOOL_TIMEOUT
                    )
                    if tech_result.get("status") == "ok":
                        final_result += tech_result.get("content", "") + "\n"
                except Exception:
                    pass

        decision_log.append({
            "time": time.time(),
            "trace_id": trace_id,
            "step": step,
            "action": "step_complete",
            "duration": time.time() - step_start,
        })

    # 《Observation Layer（可观测性层）》
    # 输出结构化日志与指标，便于审计 / 面试 / Debug
    try:
        import json
        from pathlib import Path

        logs_dir = Path(__file__).resolve().parent / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        decision_path = logs_dir / f"decision_{trace_id}.json"
        with decision_path.open("w", encoding="utf-8") as f:
            json.dump(decision_log, f, ensure_ascii=False, indent=2)

        metrics_path = logs_dir / f"metrics_{trace_id}.json"
        with metrics_path.open("w", encoding="utf-8") as f:
            json.dump({}, f)
    except Exception:
        decision_path = None
        metrics_path = None

    total_time = time.time() - start_time
    return (
        f"任务完成：{task}\n\n"
        f"【trace_id】 {trace_id}\n"
        f"【总耗时】 {total_time:.2f}s\n"
        f"【决策日志】 {decision_path}\n"
        f"【指标文件】 {metrics_path}\n\n"
        f"【最终结果】\n{final_result}"
    )
