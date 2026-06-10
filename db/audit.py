"""审计日志写入与查询（只增不改，防篡改）。"""
from __future__ import annotations
from db.engine import get_session
from db.models import AuditLog
from db import context as ctx


def log(action: str, target: str = "", *, tenant_id=None, user_id=None, username: str = "") -> None:
    try:
        with get_session() as s:
            s.add(AuditLog(
                tenant_id=tenant_id if tenant_id is not None else ctx.tenant_id(),
                user_id=user_id if user_id is not None else ctx.user_id(),
                username=username or ctx.user_name(),
                action=action, target=target[:200],
            ))
    except Exception:
        pass  # 审计失败不阻断业务


def list_logs(action: str | None = None, limit: int = 500) -> list:
    try:
        with get_session() as s:
            q = s.query(AuditLog).filter(AuditLog.tenant_id == ctx.tenant_id())
            if action and action != "全部":
                q = q.filter(AuditLog.action == action)
            rows = q.order_by(AuditLog.ts.desc()).limit(limit).all()
            return [{
                "ts": r.ts.strftime("%Y-%m-%d %H:%M:%S") if r.ts else "",
                "username": r.username, "action": r.action, "target": r.target,
            } for r in rows]
    except Exception:
        return []


def distinct_actions() -> list:
    try:
        with get_session() as s:
            rows = s.query(AuditLog.action).filter(
                AuditLog.tenant_id == ctx.tenant_id()).distinct().all()
            return sorted({r[0] for r in rows if r[0]})
    except Exception:
        return []
