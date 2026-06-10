"""B4 · 文案任务 — 数据库存储（按租户隔离）。接口签名与原 JSON 版一致。"""
from __future__ import annotations
import uuid
from datetime import datetime

from db.engine import get_session
from db.models import ContentTask
from db import context as ctx

STATUS_FLOW = ["草稿", "待审批", "已通过", "已归档"]
STATUS_NEXT = {"草稿": "待审批", "待审批": "已通过", "已通过": "已归档"}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _to_dict(t: ContentTask) -> dict:
    return {
        "id": t.id, "brand": t.brand, "title": t.title,
        "platforms": t.platforms or [], "status": t.status,
        "meta": t.meta or {}, "output": t.output or "",
        "created_at": t.created_at or "", "updated_at": t.updated_at or "",
    }


def add_task(brand_key: str, title: str, platforms: list, meta: dict, output: str = "") -> str:
    tid = "ct_" + uuid.uuid4().hex[:8]
    now = _now()
    with get_session() as s:
        s.add(ContentTask(
            id=tid, tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(),
            brand=brand_key, title=title or "(未命名文案)", platforms=platforms or [],
            status="草稿", meta=meta or {}, output=output or "",
            created_at=now, updated_at=now,
        ))
    return tid


def list_tasks(brand_key: str | None = None, status: str | None = None,
               platform: str | None = None, include_archived: bool = True) -> list:
    with get_session() as s:
        q = s.query(ContentTask).filter(ContentTask.tenant_id == ctx.tenant_id())
        if brand_key:
            q = q.filter(ContentTask.brand == brand_key)
        if status:
            q = q.filter(ContentTask.status == status)
        rows = [_to_dict(t) for t in q.all()]
    if not include_archived:
        rows = [r for r in rows if r["status"] != "已归档"]
    if platform:
        rows = [r for r in rows if platform in (r.get("platforms") or [])]
    return sorted(rows, key=lambda x: x.get("created_at", ""), reverse=True)


def get_task(tid: str) -> dict | None:
    with get_session() as s:
        t = s.query(ContentTask).filter(
            ContentTask.id == tid, ContentTask.tenant_id == ctx.tenant_id()).first()
        return _to_dict(t) if t else None


def set_status(tid: str, status: str) -> bool:
    if status not in STATUS_FLOW:
        return False
    with get_session() as s:
        t = s.query(ContentTask).filter(
            ContentTask.id == tid, ContentTask.tenant_id == ctx.tenant_id()).first()
        if not t:
            return False
        t.status = status
        t.updated_at = _now()
        return True


def advance(tid: str) -> str | None:
    t = get_task(tid)
    if not t:
        return None
    nxt = STATUS_NEXT.get(t["status"])
    if nxt and set_status(tid, nxt):
        return nxt
    return None


def delete_task(tid: str) -> bool:
    with get_session() as s:
        t = s.query(ContentTask).filter(
            ContentTask.id == tid, ContentTask.tenant_id == ctx.tenant_id()).first()
        if not t:
            return False
        s.delete(t)
        return True
