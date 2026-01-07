# tool_registry.py
# 像是一个工具名单册，列出了AI agent可以调用的各种工具函数。 
# 我这里有search_general_knowledge, search_tech_knowledge, search_project_knowledge。。。工具

from agent_learning.tool import (
    search_general_knowledge,
    search_tech_knowledge,
    search_project_knowledge,
)

TOOLS = {
    "general": search_general_knowledge,
    "tech": search_tech_knowledge,
    "project": search_project_knowledge,
}
