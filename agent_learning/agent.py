# agent.py
from zhipuai import ZhipuAI
import json

# ========= 全局客户端 =========
client = None


def set_client(zhipu_client: ZhipuAI):
    """
    设置全局的智谱AI客户端实例
    
    该函数将传入的ZhipuAI客户端实例赋值给全局变量client，
    以便在其他函数中可以使用该客户端进行AI相关的操作。
    
    参数:
        zhipu_client (ZhipuAI): ZhipuAI客户端实例，用于与智谱AI服务进行交互
    
    返回值:
        无返回值
    """
    global client
    client = zhipu_client


# ========= 严格解析 Agent JSON =========
def parse_agent_response(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"Agent 输出不是合法 JSON：{text}")

    required_keys = {"thought", "action", "action_input"}
    if not required_keys.issubset(data.keys()):
        raise ValueError(f"Agent 输出缺少字段：{data}")

    if not isinstance(data["action_input"], dict):
        raise ValueError("action_input 必须是 JSON 对象")

    return data


# ========= 全局状态 =========
state = {}


# ========= ReAct Agent 主循环 =========
async def run_agent(task: str, tools=None, max_steps: int = 10) -> str:
    if client is None:
        return "【错误】AI 客户端未初始化"

    # 工具映射
    available_tools = {}
    if tools:
        for tool in tools:
            available_tools[tool["name"]] = tool["function"]

    # 系统 Prompt
    system_prompt = f"""
你是一个严格受控的智能 Agent。

你必须【只输出合法 JSON】，不得输出任何解释或多余文本。

当前状态 state：
{state}

规则：
- 已成功获取天气信息后，允许 action=NONE
- 不允许重复调用工具
- 不允许编造结果
- action 只能是 {list(available_tools.keys())} 或 NONE

输出格式：
{{
  "thought": "...",
  "action": "工具名 或 NONE",
  "action_input": {{}}
}}

当前任务：
{task}
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    for step in range(max_steps):

        # ===== 程序级完成判断（最高优先级）=====
        if "get_current_weather" in state:
            return f"任务完成，天气结果：{state['get_current_weather']}"

        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=messages,
            temperature=0.3,
            max_tokens=512,
        )

        raw_output = response.choices[0].message.content.strip()

        print(f"\n[第 {step + 1} 步] Agent 原始输出：")
        print(raw_output)

        try:
            agent_output = parse_agent_response(raw_output)
        except Exception as e:
            messages.append({
                "role": "system",
                "content": f"JSON 解析失败，请重新输出。错误：{e}"
            })
            continue

        thought = agent_output["thought"]
        action = agent_output["action"]
        action_input = agent_output["action_input"]

        print(f"Thought: {thought}")
        print(f"Action: {action}")
        print(f"Action Input: {action_input}")

        # ===== LLM 请求结束 =====
        if action == "NONE":
            messages.append({
                "role": "system",
                "content": "如果任务已完成，将由程序统一结束。"
            })
            continue

        # ===== action 合法性检查 =====
        if action not in available_tools:
            messages.append({
                "role": "system",
                "content": f"非法 action：{action}"
            })
            continue

        # ===== 禁止重复调用 =====
        if action in state:
            messages.append({
                "role": "system",
                "content": f"工具 {action} 已执行过，禁止重复调用。"
            })
            continue

        # ===== 执行工具 =====
        try:
            result = available_tools[action](**action_input)
            observation = str(result)
            state[action] = observation
        except Exception as e:
            observation = f"工具执行失败：{e}"

        messages.append({
            "role": "system",
            "content": f"Observation: {observation}"
        })

    return f"【警告】达到最大步数 {max_steps}，任务未完成"
