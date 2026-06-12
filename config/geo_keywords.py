"""G1 · GEO 关键词蒸馏批次 — 数据库存储（按租户隔离）。"""
from __future__ import annotations
import uuid
from datetime import datetime

from db.engine import get_session
from db.models import GeoKeyword
from db import context as ctx


def save_batch(brand: str, rows: list[dict]) -> str:
    """保存一批蒸馏关键词，返回 batch_id。"""
    if not rows:
        return ""
    bid = "kwb_" + uuid.uuid4().hex[:8]
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    with get_session() as s:
        for r in rows:
            s.add(GeoKeyword(
                tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(), brand=brand,
                batch_id=bid, keyword=r["keyword"], kw_type=r["kw_type"],
                intent_type=r["intent_type"], intent_score=r["intent_score"],
                platform=r["platform"], created_at=now))
    return bid


def list_batches(brand: str) -> list[dict]:
    with get_session() as s:
        rows = s.query(GeoKeyword).filter(
            GeoKeyword.tenant_id == ctx.tenant_id(), GeoKeyword.brand == brand).all()
    batches: dict[str, dict] = {}
    for r in rows:
        b = batches.setdefault(r.batch_id, {"batch_id": r.batch_id, "created_at": r.created_at, "count": 0})
        b["count"] += 1
    return sorted(batches.values(), key=lambda x: x["created_at"], reverse=True)


def list_keywords(brand: str, batch_id: str | None = None) -> list[dict]:
    with get_session() as s:
        q = s.query(GeoKeyword).filter(
            GeoKeyword.tenant_id == ctx.tenant_id(), GeoKeyword.brand == brand)
        if batch_id:
            q = q.filter(GeoKeyword.batch_id == batch_id)
        rows = q.all()
        return [{"keyword": r.keyword, "kw_type": r.kw_type, "intent_type": r.intent_type,
                 "intent_score": r.intent_score, "platform": r.platform} for r in rows]


def delete_batch(brand: str, batch_id: str) -> int:
    with get_session() as s:
        rows = s.query(GeoKeyword).filter(
            GeoKeyword.tenant_id == ctx.tenant_id(), GeoKeyword.brand == brand,
            GeoKeyword.batch_id == batch_id).all()
        for r in rows:
            s.delete(r)
        return len(rows)
