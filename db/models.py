"""ORM 模型 — 多租户 + 角色 + 各业务实体。

隔离策略：每张业务表带 tenant_id（企业隔离）+ owner_id（个人数据归属）。
品牌/任务沿用原字符串主键，最大化兼容现有代码。
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String, Integer, Text, Boolean, DateTime, JSON, ForeignKey, func,
)
from sqlalchemy.orm import Mapped, mapped_column

from db.engine import Base


# ── 租户（企业）──────────────────────────────────────────────────────────────
class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    industry: Mapped[str] = mapped_column(String(60), default="")
    plan: Mapped[str] = mapped_column(String(30), default="基础执行版")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── 用户 ─────────────────────────────────────────────────────────────────────
ROLE_ADMIN = "enterprise_admin"     # 企业领导/管理层
ROLE_STAFF = "market_staff"         # 市场执行
ROLE_PLATFORM = "platform_admin"    # 平台运营（预留）
ROLES = [ROLE_PLATFORM, ROLE_ADMIN, ROLE_STAFF]
ROLE_LABELS = {
    ROLE_PLATFORM: "平台管理员",
    ROLE_ADMIN: "企业领导",
    ROLE_STAFF: "市场人员",
}


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(60), default="")
    role: Mapped[str] = mapped_column(String(30), default=ROLE_STAFF)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/frozen
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# ── 品牌（字符串主键，兼容现有 collection_name / 显示名逻辑）──────────────────
class Brand(Base):
    __tablename__ = "brands"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    industry: Mapped[str] = mapped_column(String(60), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    focus: Mapped[str] = mapped_column(Text, default="")
    collection_name: Mapped[str] = mapped_column(String(80), default="")
    color: Mapped[str] = mapped_column(String(16), default="#1A1A1A")
    tone: Mapped[str] = mapped_column(String(40), default="")
    brand_words: Mapped[list] = mapped_column(JSON, default=list)
    forbidden_words: Mapped[list] = mapped_column(JSON, default=list)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── 通用任务基字段（用 mixin 风格手写到每表）────────────────────────────────
class ContentTask(Base):
    __tablename__ = "content_tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    platforms: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="草稿")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    output: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(20), default="")
    updated_at: Mapped[str] = mapped_column(String(20), default="")


class GeoTask(Base):
    __tablename__ = "geo_tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    period: Mapped[str] = mapped_column(String(20), default="单次")
    region: Mapped[str] = mapped_column(String(40), default="全国")
    status: Mapped[str] = mapped_column(String(20), default="已完成")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(20), default="")


class SentimentTask(Base):
    __tablename__ = "sentiment_tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    risk_level: Mapped[int] = mapped_column(Integer, default=1)
    risk_label: Mapped[str] = mapped_column(String(20), default="")
    source: Mapped[str] = mapped_column(String(60), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(String(20), default="")


class CollectTask(Base):
    __tablename__ = "collect_tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(40), default="")
    schedule: Mapped[str] = mapped_column(String(20), default="单次执行")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="已完成")
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(20), default="")


# ── 审计日志（只增不改，为商用合规铺路）──────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(60), default="")
    action: Mapped[str] = mapped_column(String(60), default="")
    target: Mapped[str] = mapped_column(String(200), default="")
    ts: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
