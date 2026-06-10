"""E4 · 数据采集历史任务记录与复用。

持久化每次采集任务的配置与状态（时间戳、平台、关键词组、调度频率），
支持一键复用配置。单文件 JSON（data/collect_tasks.json）。
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path

_STORE = Path(__file__).parent.parent / "data" / "collect_tasks.json"
_STORE.parent.mkdir(exist_ok=True)

SCHEDULES = ["单次执行", "每日", "每周"]


def _load() -> list:
    if not _STORE.exists():
        return []
    try:
        return json.loads(_STORE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(tasks: list) -> None:
    _STORE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def add_task(brand_key: str, platform: str, schedule: str, config: dict,
             status: str = "已完成", result_count: int = 0) -> str:
    tasks = _load()
    tid = "col_" + uuid.uuid4().hex[:8]
    tasks.append({
        "id": tid,
        "brand": brand_key,
        "platform": platform,
        "schedule": schedule,
        "config": config or {},
        "status": status,
        "result_count": result_count,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save(tasks)
    return tid


def list_tasks(brand_key: str | None = None) -> list:
    out = [t for t in _load() if not brand_key or t.get("brand") == brand_key]
    return sorted(out, key=lambda x: x.get("created_at", ""), reverse=True)


def get_task(tid: str) -> dict | None:
    for t in _load():
        if t.get("id") == tid:
            return t
    return None


def delete_task(tid: str) -> bool:
    tasks = _load()
    new = [t for t in tasks if t.get("id") != tid]
    if len(new) != len(tasks):
        _save(new)
        return True
    return False
