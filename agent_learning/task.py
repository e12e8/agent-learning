# task.py

from dataclasses import dataclass
from typing import List

@dataclass
class Task:
    task_id: str
    description: str
    result: str | None = None
