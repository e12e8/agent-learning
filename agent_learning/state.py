"""
state.py

简单的本地文件持久化 state 存储，用于跨任务或跨 run 的短期记忆演示。
接口非常小：`get(key)`, `set(key, value)`, `save()`。
实现为每次写入都会刷新文件（便于演示和测试）。
"""
import json
from pathlib import Path
from typing import Any


class FileState:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except Exception:
                self._data = {}
        else:
            self._data = {}

    def get(self, key: str) -> Any:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        # 立即保存，保证跨进程可见（演示用途）
        self.save()

    def save(self) -> None:
        try:
            self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def all(self) -> dict:
        return dict(self._data)
