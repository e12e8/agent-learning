# task.py

"""数据模型：简单的任务描述结构，用于在程序中传递任务信息。"""

from dataclasses import dataclass
from typing import List


@dataclass
class Task:
    """代表一个任务：包含 id、描述和可选结果字段。"""
    task_id: str
    description: str
    result: str | None = None
