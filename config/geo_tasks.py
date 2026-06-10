"""C4 · GEO 监测任务历史记录。

支持单次 / 每日 / 每周监测周期，保留历史任务记录（含时间戳、状态、参数）。
单文件 JSON 持久化（data/geo_tasks.json）。
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path

_STORE = Path(__file__).parent.parent / "data" / "geo_tasks.json"
_STORE.parent.mkdir(exist_ok=True)

PERIODS = ["单次", "每日", "每周"]


def _load() -> list:
    if not _STORE.exists():
        return []
    try:
        return json.loads(_STORE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(tasks: list) -> None:
    _STORE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def add_record(brand_key: str, period: str, region: str, meta: dict,
               summary: str = "", status: str = "已完成") -> str:
    """记录一次 GEO 监测。返回任务 id。"""
    tasks = _load()
    tid = "geo_" + uuid.uuid4().hex[:8]
    tasks.append({
        "id": tid,
        "brand": brand_key,
        "period": period,
        "region": region,
        "status": status,
        "meta": meta or {},
        "summary": summary or "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save(tasks)
    return tid


def list_records(brand_key: str | None = None, period: str | None = None) -> list:
    """按品牌/周期筛选历史记录，创建时间倒序。"""
    out = []
    for t in _load():
        if brand_key and t.get("brand") != brand_key:
            continue
        if period and period != "全部" and t.get("period") != period:
            continue
        out.append(t)
    return sorted(out, key=lambda x: x.get("created_at", ""), reverse=True)


def get_record(tid: str) -> dict | None:
    for t in _load():
        if t.get("id") == tid:
            return t
    return None


def delete_record(tid: str) -> bool:
    tasks = _load()
    new = [t for t in tasks if t.get("id") != tid]
    if len(new) != len(tasks):
        _save(new)
        return True
    return False
