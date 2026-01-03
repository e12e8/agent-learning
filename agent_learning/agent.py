from llm import call_llm
def run_agent():
    print("agent is thinking...")
    respponse = call_llm("你好，请介绍你自己")
    print(respponse)