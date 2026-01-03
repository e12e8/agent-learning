# main.py
import asyncio
from agent import run_agent, set_client
from tools import get_current_weather, send_email
from zhipuai import ZhipuAI

# 你的 API Key（你已经填好了）
api_key = "127d3f4f9b254843a85904808c3bc36b.gzRgQ3fYA4yTCvlQ"
client = ZhipuAI(api_key=api_key)

# 重点：把 client 传给 agent.py
set_client(client)

# 定义工具（你已经写好了）
TOOLS = [
    {
        "name": "get_current_weather",
        "description": "查询指定城市的当前天气",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
        "function": get_current_weather
    },
    {
        "name": "send_email",
        "description": "发送一封邮件",
        "parameters": {"type": "object", "properties": {
            "to": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"}
        }, "required": ["to", "subject", "body"]},
        "function": send_email
    }
]

async def main():
    task = """
    请严格按以下步骤完成任务：
    1. 使用 get_current_weather 工具查询苏州的当前天气（假设代表明天）
    2. 根据天气情况判断是否需要带伞（如果有雨、小雨、阵雨等就建议带伞，否则不需要）
    3. 使用 send_email 工具把最终建议发送给 zhangsan@example.com，主题为“明日苏州天气提醒”，内容要包含天气情况和带伞建议
    4. 最后给出完整的最终总结
    """

    print("Agent 正在思考和执行任务，请稍等...")
    result = await run_agent(task, tools=TOOLS)
    
    print("\n=== Agent 最终结果 ===")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())