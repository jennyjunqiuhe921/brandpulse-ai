"""D3 · 舆情分析历史任务记录。

持久化每次舆情分析（时间戳、摘要、风险等级、来源渠道），
支持按风险等级筛选、按时间排序。单文件 JSON（data/sentiment_tasks.json）。
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path

_STORE = Path(__file__).parent.parent / "data" / "sentiment_tasks.json"
_STORE.parent.mkdir(exist_ok=True)


def _load() -> list:
    if not _STORE.exists():
        return []
    try:
        return json.loads(_STORE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(tasks: list) -> None:
    _STORE.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def add_record(brand_key: str, risk_level: int, risk_label: str, source: str,
               summary: str, tags: list | None = None) -> str:
    tasks = _load()
    tid = "sent_" + uuid.uuid4().hex[:8]
    tasks.append({
        "id": tid,
        "brand": brand_key,
        "risk_level": int(risk_level),
        "risk_label": risk_label,
        "source": source,
        "summary": summary,
        "tags": tags or [],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save(tasks)
    return tid


def list_records(brand_key: str | None = None, min_level: int | None = None,
                 sort: str = "time_desc") -> list:
    """筛选 + 排序。min_level：仅返回 >= 该等级的记录。
    sort: time_desc / time_asc / risk_desc。"""
    out = []
    for t in _load():
        if brand_key and t.get("brand") != brand_key:
            continue
        if min_level and t.get("risk_level", 1) < min_level:
            continue
        out.append(t)
    if sort == "risk_desc":
        out.sort(key=lambda x: (x.get("risk_level", 1), x.get("created_at", "")), reverse=True)
    elif sort == "time_asc":
        out.sort(key=lambda x: x.get("created_at", ""))
    else:  # time_desc
        out.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return out


def delete_record(tid: str) -> bool:
    tasks = _load()
    new = [t for t in tasks if t.get("id") != tid]
    if len(new) != len(tasks):
        _save(new)
        return True
    return False
