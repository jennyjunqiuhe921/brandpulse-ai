"""用户 CRUD（供管理员账号管理使用）。"""
from __future__ import annotations
from datetime import datetime

from db.engine import get_session
from db.models import User, Tenant, ROLE_STAFF
from auth.security import hash_password, verify_password


def authenticate(username: str, password: str) -> dict | None:
    """校验账号密码。成功返回用户 dict，失败返回 None。"""
    with get_session() as s:
        u = s.query(User).filter(User.username == username.strip()).first()
        if not u or u.status != "active":
            return None
        if not verify_password(password, u.password_hash):
            return None
        u.last_login = datetime.now()
        return _to_dict(u, s)


def get_user_by_id(user_id: int) -> dict | None:
    """按 id 加载活跃用户（供 cookie 持久化恢复会话用）。不存在/冻结返回 None。"""
    with get_session() as s:
        u = s.query(User).filter(User.id == user_id).first()
        if not u or u.status != "active":
            return None
        return _to_dict(u, s)


def _to_dict(u: User, s) -> dict:
    t = s.query(Tenant).filter(Tenant.id == u.tenant_id).first()
    return {
        "id": u.id,
        "username": u.username,
        "name": u.name or u.username,
        "role": u.role,
        "tenant_id": u.tenant_id,
        "tenant_name": t.name if t else "",
    }


def list_users(tenant_id: int) -> list[dict]:
    with get_session() as s:
        rows = s.query(User).filter(User.tenant_id == tenant_id).order_by(User.id).all()
        return [{
            "id": u.id, "username": u.username, "name": u.name,
            "role": u.role, "status": u.status,
            "last_login": u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "—",
        } for u in rows]


def create_user(tenant_id: int, username: str, password: str, name: str, role: str) -> tuple[bool, str]:
    username = (username or "").strip()
    if not username or not password:
        return False, "用户名和密码不能为空"
    with get_session() as s:
        if s.query(User).filter(User.username == username).first():
            return False, f"用户名「{username}」已存在"
        s.add(User(
            tenant_id=tenant_id, username=username,
            password_hash=hash_password(password),
            name=name or username, role=role or ROLE_STAFF,
        ))
    return True, "已创建"


def set_status(user_id: int, status: str) -> bool:
    with get_session() as s:
        u = s.query(User).filter(User.id == user_id).first()
        if not u:
            return False
        u.status = status
        return True


def reset_password(user_id: int, new_password: str) -> bool:
    if not new_password:
        return False
    with get_session() as s:
        u = s.query(User).filter(User.id == user_id).first()
        if not u:
            return False
        u.password_hash = hash_password(new_password)
        return True


def update_profile(user_id: int, name: str) -> bool:
    with get_session() as s:
        u = s.query(User).filter(User.id == user_id).first()
        if not u:
            return False
        u.name = name
        return True


def change_own_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    from auth.security import verify_password
    if not new_password or len(new_password) < 6:
        return False, "新密码至少 6 位"
    with get_session() as s:
        u = s.query(User).filter(User.id == user_id).first()
        if not u:
            return False, "用户不存在"
        if not verify_password(old_password, u.password_hash):
            return False, "原密码不正确"
        u.password_hash = hash_password(new_password)
        return True, "密码已更新"
