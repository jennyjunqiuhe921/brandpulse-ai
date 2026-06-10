"""E4 · 采集历史任务 — 数据库存储（按租户隔离）。接口签名与原 JSON 版一致。"""
from __future__ import annotations
import uuid
from datetime import datetime

from db.engine import get_session
from db.models import CollectTask
from db import context as ctx

SCHEDULES = ["单次执行", "每日", "每周"]


def _to_dict(t: CollectTask) -> dict:
    return {
        "id": t.id, "brand": t.brand, "platform": t.platform, "schedule": t.schedule,
        "config": t.config or {}, "status": t.status,
        "result_count": t.result_count,
        "priority": getattr(t, "priority", "普通") or "普通",
        "task_tags": getattr(t, "task_tags", []) or [],
        "due_date": getattr(t, "due_date", "") or "",
        "created_at": t.created_at or "",
    }


def add_task(brand_key: str, platform: str, schedule: str, config: dict,
             status: str = "已完成", result_count: int = 0,
             priority: str = "普通", task_tags: list | None = None, due_date: str = "") -> str:
    tid = "col_" + uuid.uuid4().hex[:8]
    with get_session() as s:
        s.add(CollectTask(
            id=tid, tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(),
            brand=brand_key, platform=platform, schedule=schedule,
            config=config or {}, status=status, result_count=result_count,
            priority=priority, task_tags=task_tags or [], due_date=due_date,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ))
    return tid


def list_tasks(brand_key: str | None = None) -> list:
    with get_session() as s:
        q = s.query(CollectTask).filter(CollectTask.tenant_id == ctx.tenant_id())
        if brand_key:
            q = q.filter(CollectTask.brand == brand_key)
        rows = [_to_dict(t) for t in q.all()]
    return sorted(rows, key=lambda x: x.get("created_at", ""), reverse=True)


def get_task(tid: str) -> dict | None:
    with get_session() as s:
        t = s.query(CollectTask).filter(
            CollectTask.id == tid, CollectTask.tenant_id == ctx.tenant_id()).first()
        return _to_dict(t) if t else None


def delete_task(tid: str) -> bool:
    with get_session() as s:
        t = s.query(CollectTask).filter(
            CollectTask.id == tid, CollectTask.tenant_id == ctx.tenant_id()).first()
        if not t:
            return False
        s.delete(t)
        return True
