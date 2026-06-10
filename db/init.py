"""初始化数据库：建表 + 种子（默认租户/管理员/演示品牌）。

幂等：可重复调用，已存在则跳过。应用启动时调用 init_db() 一次。
"""
from __future__ import annotations
import os
import json
from pathlib import Path

from db.engine import engine, get_session, Base
from db import models  # noqa: F401  确保模型注册到 Base
from db.models import Tenant, User, Brand, ROLE_ADMIN
from auth.security import hash_password

_BRANDS_DIR = Path(__file__).parent.parent / "brands"

_DEFAULT_ADMIN_USER = os.getenv("DEFAULT_ADMIN_USER", "admin")
_DEFAULT_ADMIN_PASS = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")


def init_db() -> None:
    Base.metadata.create_all(engine)
    with get_session() as s:
        # 1. 默认租户
        tenant = s.query(Tenant).first()
        if tenant is None:
            tenant = Tenant(name="演示企业", industry="新式茶饮", plan="企业集团版")
            s.add(tenant)
            s.flush()  # 拿到 tenant.id

        # 2. 初始管理员
        if s.query(User).count() == 0:
            s.add(User(
                tenant_id=tenant.id,
                username=_DEFAULT_ADMIN_USER,
                password_hash=hash_password(_DEFAULT_ADMIN_PASS),
                name="管理员",
                role=ROLE_ADMIN,
            ))

        # 3. 导入演示品牌（仅当库内无品牌时）
        if s.query(Brand).count() == 0 and _BRANDS_DIR.exists():
            for f in sorted(_BRANDS_DIR.glob("*.json")):
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if "id" not in d:
                    continue
                s.add(Brand(
                    id=d["id"],
                    tenant_id=tenant.id,
                    owner_id=None,
                    name=d.get("name", d["id"]),
                    industry=d.get("industry", ""),
                    description=d.get("description", ""),
                    focus=d.get("focus", ""),
                    collection_name=d.get("collection_name", f"pinsight_{d['id']}"),
                    color=d.get("color", "#1A1A1A"),
                    tone=d.get("tone", ""),
                    brand_words=d.get("brand_words", []),
                    forbidden_words=d.get("forbidden_words", []),
                    is_demo=bool(d.get("is_demo", False)),
                ))


if __name__ == "__main__":
    init_db()
    print("✅ 数据库已初始化")
