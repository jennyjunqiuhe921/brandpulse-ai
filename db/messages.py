"""S1-2 全局消息中心 — 数据库存储（按租户 + 用户隔离）。

消息可定向到具体用户（user_id）或全员（user_id=None）。
"""
from __future__ import annotations

from sqlalchemy import or_

from db.engine import get_session
from db.models import Message, MSG_SYSTEM
from db import context as ctx


def _to_dict(m: Message) -> dict:
    return {
        "id": m.id, "category": m.category, "title": m.title, "body": m.body,
        "level": m.level, "is_read": m.is_read, "link": m.link,
        "created_at": m.created_at.strftime("%Y-%m-%d %H:%M") if m.created_at else "",
    }


def push(title: str, body: str = "", *, category: str = MSG_SYSTEM,
         level: str = "info", link: str = "",
         tenant_id: int | None = None, user_id: int | None = None) -> int:
    """推送一条消息。user_id=None 表示全员可见。"""
    tid = tenant_id if tenant_id is not None else ctx.tenant_id()
    with get_session() as s:
        m = Message(tenant_id=tid, user_id=user_id, category=category,
                    title=title, body=body, level=level, link=link)
        s.add(m)
        s.flush()
        return m.id


def list_messages(category: str | None = None, only_unread: bool = False) -> list:
    """当前用户可见消息（定向给我 + 全员）。"""
    uid = ctx.user_id()
    with get_session() as s:
        q = s.query(Message).filter(Message.tenant_id == ctx.tenant_id())
        q = q.filter(or_(Message.user_id == uid, Message.user_id.is_(None)))
        if category:
            q = q.filter(Message.category == category)
        if only_unread:
            q = q.filter(Message.is_read.is_(False))
        rows = [_to_dict(m) for m in q.order_by(Message.created_at.desc()).all()]
    return rows


def unread_count() -> int:
    uid = ctx.user_id()
    with get_session() as s:
        return (s.query(Message)
                .filter(Message.tenant_id == ctx.tenant_id())
                .filter(or_(Message.user_id == uid, Message.user_id.is_(None)))
                .filter(Message.is_read.is_(False))
                .count())


def mark_read(msg_id: int) -> bool:
    with get_session() as s:
        m = s.query(Message).filter(
            Message.id == msg_id, Message.tenant_id == ctx.tenant_id()).first()
        if not m:
            return False
        m.is_read = True
        return True


def mark_all_read() -> int:
    uid = ctx.user_id()
    with get_session() as s:
        rows = (s.query(Message)
                .filter(Message.tenant_id == ctx.tenant_id())
                .filter(or_(Message.user_id == uid, Message.user_id.is_(None)))
                .filter(Message.is_read.is_(False)).all())
        for m in rows:
            m.is_read = True
        return len(rows)
