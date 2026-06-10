"""B4 · 文案任务列表存储。

文案完整生命周期：草稿 → 待审批 → 已通过 → 已归档。
单文件 JSON 持久化（data/content_tasks.json），轻量、零依赖。
每条任务记录生成配置（_meta）以支持「复制配置」一键复用。
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path

_STORE = Path(__file__).parent.parent / "data" / "content_tasks.json"
_STORE.parent.mkdir(exist_ok=True)

# 状态机：顺序流转 + 可归档
STATUS_FLOW = ["草稿", "待审批", "已通过", "已归档"]
STATUS_NEXT = {
    "草稿": "待审批",
    "待审批": "已通过",
    "已通过": "已归档",
}


def _load() -> list:
    if not _STORE.exists():
        return []
    try:
        return json.loads(_STORE.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save(tasks: list) -> None:
    _STORE.write_text(
        json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def add_task(brand_key: str, title: str, platforms: list, meta: dict, output: str = "") -> str:
    """新增任务，初始状态「草稿」。返回任务 id。"""
    tasks = _load()
    tid = "ct_" + uuid.uuid4().hex[:8]
    tasks.append({
        "id": tid,
        "brand": brand_key,
        "title": title or "(未命名文案)",
        "platforms": platforms or [],
        "status": "草稿",
        "meta": meta or {},
        "output": output or "",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    _save(tasks)
    return tid


def list_tasks(brand_key: str | None = None, status: str | None = None,
               platform: str | None = None, include_archived: bool = True) -> list:
    """筛选任务列表（按状态/平台/品牌）。默认按创建时间倒序。"""
    tasks = _load()
    out = []
    for t in tasks:
        if brand_key and t.get("brand") != brand_key:
            continue
        if status and t.get("status") != status:
            continue
        if not include_archived and t.get("status") == "已归档":
            continue
        if platform and platform not in (t.get("platforms") or []):
            continue
        out.append(t)
    return sorted(out, key=lambda x: x.get("created_at", ""), reverse=True)


def get_task(tid: str) -> dict | None:
    for t in _load():
        if t.get("id") == tid:
            return t
    return None


def set_status(tid: str, status: str) -> bool:
    if status not in STATUS_FLOW:
        return False
    tasks = _load()
    for t in tasks:
        if t.get("id") == tid:
            t["status"] = status
            t["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            _save(tasks)
            return True
    return False


def advance(tid: str) -> str | None:
    """推进到下一状态，返回新状态；已是终态返回 None。"""
    t = get_task(tid)
    if not t:
        return None
    nxt = STATUS_NEXT.get(t.get("status"))
    if nxt and set_status(tid, nxt):
        return nxt
    return None


def delete_task(tid: str) -> bool:
    tasks = _load()
    new = [t for t in tasks if t.get("id") != tid]
    if len(new) != len(tasks):
        _save(new)
        return True
    return False
