from llm import call_llm

async def run_agent(name: str):
    print(f"{name} 开始思考了")
    response = await call_llm(f"你好，我是{name} ")
    print(f"{name}回复完成：{response}")