"""D3 · 舆情历史 — 数据库存储（按租户隔离）。接口签名与原 JSON 版一致。"""
from __future__ import annotations
import uuid
from datetime import datetime

from db.engine import get_session
from db.models import SentimentTask
from db import context as ctx


def _to_dict(t: SentimentTask) -> dict:
    return {
        "id": t.id, "brand": t.brand, "risk_level": t.risk_level,
        "risk_label": t.risk_label, "source": t.source, "summary": t.summary or "",
        "tags": t.tags or [], "created_at": t.created_at or "",
    }


def add_record(brand_key: str, risk_level: int, risk_label: str, source: str,
               summary: str, tags: list | None = None) -> str:
    tid = "sent_" + uuid.uuid4().hex[:8]
    with get_session() as s:
        s.add(SentimentTask(
            id=tid, tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(),
            brand=brand_key, risk_level=int(risk_level), risk_label=risk_label,
            source=source, summary=summary, tags=tags or [],
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ))
    return tid


def list_records(brand_key: str | None = None, min_level: int | None = None,
                 sort: str = "time_desc") -> list:
    with get_session() as s:
        q = s.query(SentimentTask).filter(SentimentTask.tenant_id == ctx.tenant_id())
        if brand_key:
            q = q.filter(SentimentTask.brand == brand_key)
        if min_level:
            q = q.filter(SentimentTask.risk_level >= min_level)
        rows = [_to_dict(t) for t in q.all()]
    if sort == "risk_desc":
        rows.sort(key=lambda x: (x.get("risk_level", 1), x.get("created_at", "")), reverse=True)
    elif sort == "time_asc":
        rows.sort(key=lambda x: x.get("created_at", ""))
    else:
        rows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return rows


def delete_record(tid: str) -> bool:
    with get_session() as s:
        t = s.query(SentimentTask).filter(
            SentimentTask.id == tid, SentimentTask.tenant_id == ctx.tenant_id()).first()
        if not t:
            return False
        s.delete(t)
        return True
