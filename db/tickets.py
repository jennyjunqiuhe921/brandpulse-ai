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


# 处置方式（D5-4 消影）
DISPOSAL_METHODS = ["公域官方回复", "用户私下补偿退款", "平台投诉撤诉", "置顶评论回复", "电话沟通和解"]


def _to_dict(t: SentimentTicket) -> dict:
    return {
        "id": t.id, "brand": t.brand, "source_id": t.source_id, "title": t.title,
        "level": t.level, "level_label": TICKET_LEVEL_LABEL.get(t.level, ""),
        "sla": t.sla, "segment_tags": t.segment_tags or [], "response": t.response,
        "status": t.status, "is_case": t.is_case,
        "disposal_method": getattr(t, "disposal_method", "") or "",
        "impact_removed": getattr(t, "impact_removed", False) or False,
        "elimination_note": getattr(t, "elimination_note", "") or "",
        "eliminated_at": getattr(t, "eliminated_at", "") or "",
        "reviewed": getattr(t, "reviewed", False) or False,
        "review_data": getattr(t, "review_data", {}) or {},
        "reviewed_at": getattr(t, "reviewed_at", "") or "",
        "created_at": t.created_at, "closed_at": t.closed_at,
    }


def needs_review(level: int) -> bool:
    """橙标(3)/红标(4)强制复盘。"""
    return int(level) >= 3


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
            if status == "已归档":
                t.closed_at = _now()
        return True


def _get(s, tid: str):
    return s.query(SentimentTicket).filter(
        SentimentTicket.id == tid, SentimentTicket.tenant_id == ctx.tenant_id()).first()


def eliminate(tid: str, method: str, note: str, impact_removed: bool = True) -> bool:
    """D5-4 消影：记录处置方式/备注/是否消除影响。完成后停止告警；
    橙红(≥3级)转『待复盘』，其余直接『已归档』。"""
    with get_session() as s:
        t = _get(s, tid)
        if not t:
            return False
        t.disposal_method = method
        t.elimination_note = note
        t.impact_removed = bool(impact_removed)
        t.eliminated_at = _now()
        if needs_review(t.level):
            t.status = "待复盘"
        else:
            t.status = "已归档"
            t.closed_at = _now()
        return True


def review(tid: str, data: dict, *, as_case: bool = True) -> bool:
    """D5-3 复盘归档：保存复盘表单，标记已复盘并归档，沉淀负面案例库。"""
    with get_session() as s:
        t = _get(s, tid)
        if not t:
            return False
        t.review_data = data or {}
        t.reviewed = True
        t.reviewed_at = _now()
        t.status = "已归档"
        t.closed_at = _now()
        if as_case:
            t.is_case = True
        return True
