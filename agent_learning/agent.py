# agent.py
from zhipuai import ZhipuAI
import json

"""简要：实现基于工具调用的 ReAct 风格 Agent 主逻辑。
依赖外部 LLM 客户端（由 main.py 通过 `set_client` 注入），
负责解析模型输出、调用工具并返回最终结论。"""

# 全局 client，由 `main.py` 通过 `set_client` 注入
client = None

def set_client(zhipu_client: ZhipuAI):
    """main.py 中调用此函数把 client 传进来"""
    global client
    client = zhipu_client


async def run_agent(task: str, tools=None, max_steps: int = 15) -> str:
    """
    简单的 ReAct Agent 实现
    支持工具调用、逐步思考、最终输出 Final Answer
    """
    if client is None:
        return "【错误】AI 客户端未初始化，请先在 main.py 中调用 set_client(client)"

    # 构建工具映射：工具名 → 函数
    available_tools = {}
    if tools:
        for tool in tools:
            available_tools[tool["name"]] = tool["function"]

    # 系统提示词（关键：规定 Agent 回复格式，便于解析）
    system_prompt = f"""
你是一个高效的智能助手，能通过思考和调用工具快速完成任务。
请严格按照以下格式回复（只能用这个格式，禁止多余文字或解释）：

Thought: 你当前的思考（用中文）
Action: 工具名称
Action Input: {{参数 JSON}}

当所有任务都完成或可以给出最终结论时，必须立即回复：
Final Answer: 最终结论（用自然、完整的中文句子）

当前任务：{task}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task}
    ]
    # 与 LLM 循环交互，直到产生 Final Answer 或达到最大步数
    for step in range(max_steps):
        # 调用大模型
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=messages,
            temperature=0.3,
            max_tokens=512,
        )
        content = response.choices[0].message.content.strip()

        # 把模型回复加入历史
        messages.append({"role": "assistant", "content": content})

        # ------------------- 调试打印：看清每一步 Agent 在想什么 -------------------
        print(f"\n[第 {step + 1} 步] Agent 回复：")
        print(content)
        # -------------------------------------------------------------------------

        # 解析是否调用工具
        if "Action:" in content and "Action Input:" in content:
            try:
                # 提取 Action 和 Action Input
                action_part = content.split("Action:")[1].split("Action Input:")[0].strip()
                input_part = content.split("Action Input:")[1].strip()

                action_name = action_part.strip()
                action_input = json.loads(input_part)

                if action_name not in available_tools:
                    observation = f"【错误】找不到工具：{action_name}"
                else:
                    func = available_tools[action_name]
                    observation = func(**action_input)
                    observation = str(observation)
            except Exception as e:
                observation = f"【工具调用出错】{str(e)}"

            # 把工具执行结果作为 Observation 发回给模型
            messages.append({"role": "system", "content": f"Observation: {observation}"})
            continue

        # 检查是否直接给出了 Final Answer
        if "Final Answer:" in content:
            final_answer = content.split("Final Answer:")[1].strip()
            return final_answer

        # 如果既没有 Action 也没有 Final Answer，继续循环（模型可能在继续思考）

    # 超过最大步数还没结束
    return "【警告】达到最大思考步数（{max_steps}），未得到 Final Answer。可以继续增加 max_steps 或进一步优化提示词。"