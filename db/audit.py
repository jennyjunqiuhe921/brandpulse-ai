"""审计日志写入（只增不改）。"""
from __future__ import annotations
from db.engine import get_session
from db.models import AuditLog


def log(action: str, target: str = "", *, tenant_id=None, user_id=None, username: str = "") -> None:
    try:
        with get_session() as s:
            s.add(AuditLog(
                tenant_id=tenant_id, user_id=user_id, username=username,
                action=action, target=target[:200],
            ))
    except Exception:
        pass  # 审计失败不阻断业务
