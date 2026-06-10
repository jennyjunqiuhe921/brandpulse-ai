"""初始化数据库：建表 + 种子（默认租户/管理员/演示品牌）。

幂等：可重复调用，已存在则跳过。应用启动时调用 init_db() 一次。
"""
from __future__ import annotations
import os
import json
from pathlib import Path

from sqlalchemy import inspect, text

from db.engine import engine, get_session, Base
from db import models  # noqa: F401  确保模型注册到 Base
from db.models import (
    Tenant, User, Brand, Message, ROLE_ADMIN, ROLE_STAFF,
    MSG_SYSTEM, MSG_TASK, MSG_RISK,
    ApprovalRequest, ApprovalStep, APR_PENDING, STEP_WAIT,
)
from auth.security import hash_password

# 轻量迁移：为已存在的表补加新列（SQLite/Postgres 均支持 ADD COLUMN）
_NEW_COLUMNS = {
    "tenants": [("ai_daily_quota", "INTEGER", "1000")],
    "content_tasks": [("priority", "VARCHAR(10)", "'普通'"), ("task_tags", "JSON", "'[]'"), ("due_date", "VARCHAR(20)", "''")],
    "geo_tasks": [("priority", "VARCHAR(10)", "'普通'"), ("task_tags", "JSON", "'[]'"), ("due_date", "VARCHAR(20)", "''")],
    "sentiment_tasks": [("priority", "VARCHAR(10)", "'普通'"), ("task_tags", "JSON", "'[]'"), ("due_date", "VARCHAR(20)", "''")],
    "collect_tasks": [("priority", "VARCHAR(10)", "'普通'"), ("task_tags", "JSON", "'[]'"), ("due_date", "VARCHAR(20)", "''")],
}


def _ensure_columns() -> None:
    """为现有表补加新增列，幂等。"""
    insp = inspect(engine)
    existing_tables = set(insp.get_table_names())
    with engine.begin() as conn:
        for table, cols in _NEW_COLUMNS.items():
            if table not in existing_tables:
                continue  # create_all 会建新表，无需迁移
            have = {c["name"] for c in insp.get_columns(table)}
            for name, coltype, default in cols:
                if name not in have:
                    conn.execute(text(
                        f"ALTER TABLE {table} ADD COLUMN {name} {coltype} DEFAULT {default}"))

_BRANDS_DIR = Path(__file__).parent.parent / "brands"

_DEFAULT_ADMIN_USER = os.getenv("DEFAULT_ADMIN_USER", "admin")
_DEFAULT_ADMIN_PASS = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")


def init_db() -> None:
    Base.metadata.create_all(engine)
    _ensure_columns()
    with get_session() as s:
        # 1. 默认租户
        tenant = s.query(Tenant).first()
        if tenant is None:
            tenant = Tenant(name="演示企业", industry="新式茶饮", plan="企业集团版")
            s.add(tenant)
            s.flush()  # 拿到 tenant.id

        # 2. 初始管理员 + 演示市场专员
        if s.query(User).count() == 0:
            s.add(User(
                tenant_id=tenant.id,
                username=_DEFAULT_ADMIN_USER,
                password_hash=hash_password(_DEFAULT_ADMIN_PASS),
                name="管理员",
                role=ROLE_ADMIN,
            ))
            s.add(User(
                tenant_id=tenant.id,
                username="staff1",
                password_hash=hash_password("staff123"),
                name="市场专员",
                role=ROLE_STAFF,
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

        # 4. 种子消息（仅当库内无消息时）
        if s.query(Message).count() == 0:
            s.add(Message(tenant_id=tenant.id, user_id=None, category=MSG_SYSTEM,
                          title="欢迎使用智营AI · 一体化营销工作台",
                          body="系统已就绪。审批、风险、超时任务等事件会自动推送至此。",
                          level="info"))
            s.add(Message(tenant_id=tenant.id, user_id=None, category=MSG_TASK,
                          title="您有 2 项内容任务待处理",
                          body="请在「内容工坊」查看草稿与待审批任务。", level="info"))
            s.add(Message(tenant_id=tenant.id, user_id=None, category=MSG_RISK,
                          title="舆情风险提醒（演示）",
                          body="检测到 1 条 3 级负面舆情，建议尽快在「舆情分析」处置。",
                          level="warn"))

        # 5. 种子审批单（演示：市场专员发起、风险中=两级审批链）
        if s.query(ApprovalRequest).count() == 0:
            staff = s.query(User).filter(User.username == "staff1").first()
            rid = "apr_demo0001"
            s.add(ApprovalRequest(
                id=rid, tenant_id=tenant.id,
                owner_id=staff.id if staff else None, owner_name="市场专员",
                biz_type="文案", biz_id="", brand="heytea",
                title="多肉葡萄夏季推广文案（小红书）",
                content="多肉葡萄上新🍇 整颗葡萄粒，真实果肉不将就。"
                        "今夏限定，灵感下午茶就选这一杯。",
                risk_level="中", priority="普通", status=APR_PENDING,
                current_step=1, version=1, history=[],
                created_at="2026-06-10 09:30", updated_at="2026-06-10 09:30",
            ))
            s.add(ApprovalStep(request_id=rid, step_no=1, approver_role=ROLE_ADMIN,
                               approver_label="市场主管", status=STEP_WAIT))
            s.add(ApprovalStep(request_id=rid, step_no=2, approver_role=ROLE_ADMIN,
                               approver_label="品牌负责人", status=STEP_WAIT))


if __name__ == "__main__":
    init_db()
    print("✅ 数据库已初始化")
