"""S2-4 舆情工单 + 负面案例库 — 数据库存储（按租户隔离）。"""
from __future__ import annotations
import uuid
from datetime import datetime

from db.engine import get_session
from db.models import SentimentTicket, TICKET_SLA, TICKET_LEVEL_LABEL
from db import context as ctx
from db import messages as msg_store
from db.models import MSG_RISK


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _to_dict(t: SentimentTicket) -> dict:
    return {
        "id": t.id, "brand": t.brand, "source_id": t.source_id, "title": t.title,
        "level": t.level, "level_label": TICKET_LEVEL_LABEL.get(t.level, ""),
        "sla": t.sla, "segment_tags": t.segment_tags or [], "response": t.response,
        "status": t.status, "is_case": t.is_case,
        "created_at": t.created_at, "closed_at": t.closed_at,
    }


def create(brand: str, title: str, level: int, *, source_id: str = "",
           segment_tags: list | None = None) -> str:
    tid = "tk_" + uuid.uuid4().hex[:8]
    sla = TICKET_SLA.get(level, "")
    with get_session() as s:
        s.add(SentimentTicket(
            id=tid, tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(),
            brand=brand, source_id=source_id, title=title, level=int(level), sla=sla,
            segment_tags=segment_tags or [], status="待处理", created_at=_now()))
    if level >= 3:
        msg_store.push(f"🔴 高危舆情工单：{title}", f"{TICKET_LEVEL_LABEL.get(level)} · 响应时效 {sla}",
                       category=MSG_RISK, level="danger", link="pages/15_舆情工单.py")
    return tid


def list_tickets(brand: str | None = None, status: str | None = None,
                 only_cases: bool = False) -> list:
    with get_session() as s:
        q = s.query(SentimentTicket).filter(SentimentTicket.tenant_id == ctx.tenant_id())
        if brand:
            q = q.filter(SentimentTicket.brand == brand)
        if status:
            q = q.filter(SentimentTicket.status == status)
        if only_cases:
            q = q.filter(SentimentTicket.is_case.is_(True))
        rows = [_to_dict(t) for t in q.all()]
    return sorted(rows, key=lambda x: (x["level"], x["created_at"]), reverse=True)


def update(tid: str, *, response: str | None = None, status: str | None = None,
           is_case: bool | None = None) -> bool:
    with get_session() as s:
        t = s.query(SentimentTicket).filter(
            SentimentTicket.id == tid, SentimentTicket.tenant_id == ctx.tenant_id()).first()
        if not t:
            return False
        if response is not None:
            t.response = response
        if is_case is not None:
            t.is_case = is_case
        if status is not None:
            t.status = status
            if status == "已办结":
                t.closed_at = _now()
        return True
