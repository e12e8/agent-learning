# tool.py 用作 AI agent 或智能系统中的外部知识接入点，
# 当系统需要获取特定领域的知识时，会调用相应的工具函数来获取信息。

def search_general_knowledge(query: str) -> dict:
    print(f"[Tool] 查询通用知识：{query}")
    return {
        "status": "ok",
        "type": "general",
        "content": f"【通用知识】关于 {query} 的基础解释"
    }

def search_tech_knowledge(query: str) -> dict:
    print(f"[Tool] 查询技术知识：{query}")
    return {
        "status": "ok",
        "type": "tech",
        "content": f"【技术知识】关于 {query} 的技术原理说明"
    }

def search_project_knowledge(query: str) -> dict:
    print(f"[Tool] 查询工程知识：{query}")
    return {
        "status": "ok",
        "type": "project",
        "content": f"【工程知识】关于 {query} 的项目实践经验"
    }
