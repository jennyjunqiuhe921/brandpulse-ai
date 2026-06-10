"""C4 · GEO 监测历史 — 数据库存储（按租户隔离）。接口签名与原 JSON 版一致。"""
from __future__ import annotations
import uuid
from datetime import datetime

from db.engine import get_session
from db.models import GeoTask
from db import context as ctx

PERIODS = ["单次", "每日", "每周"]


def _to_dict(t: GeoTask) -> dict:
    return {
        "id": t.id, "brand": t.brand, "period": t.period, "region": t.region,
        "status": t.status, "meta": t.meta or {}, "summary": t.summary or "",
        "created_at": t.created_at or "",
    }


def add_record(brand_key: str, period: str, region: str, meta: dict,
               summary: str = "", status: str = "已完成") -> str:
    tid = "geo_" + uuid.uuid4().hex[:8]
    with get_session() as s:
        s.add(GeoTask(
            id=tid, tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(),
            brand=brand_key, period=period, region=region, status=status,
            meta=meta or {}, summary=summary or "",
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        ))
    return tid


def list_records(brand_key: str | None = None, period: str | None = None) -> list:
    with get_session() as s:
        q = s.query(GeoTask).filter(GeoTask.tenant_id == ctx.tenant_id())
        if brand_key:
            q = q.filter(GeoTask.brand == brand_key)
        if period and period != "全部":
            q = q.filter(GeoTask.period == period)
        rows = [_to_dict(t) for t in q.all()]
    return sorted(rows, key=lambda x: x.get("created_at", ""), reverse=True)


def get_record(tid: str) -> dict | None:
    with get_session() as s:
        t = s.query(GeoTask).filter(
            GeoTask.id == tid, GeoTask.tenant_id == ctx.tenant_id()).first()
        return _to_dict(t) if t else None


def delete_record(tid: str) -> bool:
    with get_session() as s:
        t = s.query(GeoTask).filter(
            GeoTask.id == tid, GeoTask.tenant_id == ctx.tenant_id()).first()
        if not t:
            return False
        s.delete(t)
        return True
