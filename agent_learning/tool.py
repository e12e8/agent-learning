# tool.py 用作 AI agent 或智能系统中的外部知识接入点，
# 当系统需要获取特定领域的知识时，会调用相应的工具函数来获取信息。
import asyncio

async def search_tech_knowledge(query: str):
    await asyncio.sleep(2)  # 模拟慢 I/O
    return {
        "status": "ok",
        "type": "tech",
        "confidence": 0.8,
        "content": "技术相关内容（已修改）"
    }

async def search_general_knowledge(query: str):
    await asyncio.sleep(2)
    return {
        "status": "ok",
        "type": "general",
        "confidence": 0.4,
        "content": "一些通用说明"
}

async def search_project_knowledge(query: str):
    await asyncio.sleep(2)
    return {
        "status": "ok",
        "type": "project",
        "confidence": 0.7,
        "content": "项目实践经验"
    }
