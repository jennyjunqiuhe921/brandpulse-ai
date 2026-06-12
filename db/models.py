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
    __tablename__ = "pin_tenants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    industry: Mapped[str] = mapped_column(String(60), default="")
    plan: Mapped[str] = mapped_column(String(30), default="基础执行版")
    ai_daily_quota: Mapped[int] = mapped_column(Integer, default=1000)  # AI 单日调用额度
    max_users: Mapped[int] = mapped_column(Integer, default=10)
    contact: Mapped[str] = mapped_column(String(60), default="")
    expire_at: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[str] = mapped_column(String(20), default="正常")  # 正常/冻结/已注销
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
    __tablename__ = "pin_users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("pin_tenants.id"), index=True)
    username: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    name: Mapped[str] = mapped_column(String(60), default="")
    role: Mapped[str] = mapped_column(String(30), default=ROLE_STAFF)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/frozen
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


# ── 品牌（字符串主键，兼容现有 collection_name / 显示名逻辑）──────────────────
class Brand(Base):
    __tablename__ = "pin_brands"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("pin_tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pin_users.id"), nullable=True)
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
# 任务通用字段常量（S1 任务通用规则）
PRIORITY_URGENT = "紧急"
PRIORITY_NORMAL = "普通"
PRIORITY_LOW = "低"
PRIORITIES = [PRIORITY_URGENT, PRIORITY_NORMAL, PRIORITY_LOW]


class ContentTask(Base):
    __tablename__ = "pin_content_tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("pin_tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pin_users.id"), nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    platforms: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(20), default="草稿")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    output: Mapped[str] = mapped_column(Text, default="")
    # S1 任务通用字段
    priority: Mapped[str] = mapped_column(String(10), default=PRIORITY_NORMAL)
    task_tags: Mapped[list] = mapped_column(JSON, default=list)
    due_date: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[str] = mapped_column(String(20), default="")
    updated_at: Mapped[str] = mapped_column(String(20), default="")


class GeoTask(Base):
    __tablename__ = "pin_geo_tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("pin_tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pin_users.id"), nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    period: Mapped[str] = mapped_column(String(20), default="单次")
    region: Mapped[str] = mapped_column(String(40), default="全国")
    status: Mapped[str] = mapped_column(String(20), default="已完成")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
    summary: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(10), default=PRIORITY_NORMAL)
    task_tags: Mapped[list] = mapped_column(JSON, default=list)
    due_date: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[str] = mapped_column(String(20), default="")


class SentimentTask(Base):
    __tablename__ = "pin_sentiment_tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("pin_tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pin_users.id"), nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    risk_level: Mapped[int] = mapped_column(Integer, default=1)
    risk_label: Mapped[str] = mapped_column(String(20), default="")
    source: Mapped[str] = mapped_column(String(60), default="")
    summary: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    priority: Mapped[str] = mapped_column(String(10), default=PRIORITY_NORMAL)
    task_tags: Mapped[list] = mapped_column(JSON, default=list)
    due_date: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[str] = mapped_column(String(20), default="")


class CollectTask(Base):
    __tablename__ = "pin_collect_tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("pin_tenants.id"), index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pin_users.id"), nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(40), default="")
    schedule: Mapped[str] = mapped_column(String(20), default="单次执行")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="已完成")
    result_count: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[str] = mapped_column(String(10), default=PRIORITY_NORMAL)
    task_tags: Mapped[list] = mapped_column(JSON, default=list)
    due_date: Mapped[str] = mapped_column(String(20), default="")
    created_at: Mapped[str] = mapped_column(String(20), default="")


# ── 审计日志（只增不改，为商用合规铺路）──────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "pin_audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(60), default="")
    action: Mapped[str] = mapped_column(String(60), default="")
    target: Mapped[str] = mapped_column(String(200), default="")
    ts: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── 运营侧：大模型配置中心（S5）─────────────────────────────────────────────
MODEL_TYPES = ["文本", "生图", "生视频"]


class ModelConfig(Base):
    __tablename__ = "pin_model_configs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    model_type: Mapped[str] = mapped_column(String(20), default="文本")
    api_base: Mapped[str] = mapped_column(String(200), default="")
    api_key_masked: Mapped[str] = mapped_column(String(80), default="")  # 仅存掩码，不存明文
    status: Mapped[str] = mapped_column(String(20), default="未启用")  # 未启用/测试中/正常/已停用
    note: Mapped[str] = mapped_column(String(200), default="")
    created_at: Mapped[str] = mapped_column(String(20), default="")


# ── 运营侧：Prompt 统一管理中心（S5）────────────────────────────────────────
PROMPT_CATEGORIES = ["文案生成", "GEO优化", "舆情分析", "通用校验", "选品分析", "竞品分析"]


class PromptTemplate(Base):
    __tablename__ = "pin_prompt_templates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(20), default="文案生成", index=True)
    model_name: Mapped[str] = mapped_column(String(80), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default="草稿")  # 草稿/已启用
    history: Mapped[list] = mapped_column(JSON, default=list)  # 历史版本快照
    created_by: Mapped[str] = mapped_column(String(60), default="")
    updated_at: Mapped[str] = mapped_column(String(20), default="")


# ── 全局消息中心（S1-2）──────────────────────────────────────────────────────
# 消息分类
MSG_APPROVAL = "审批通知"
MSG_TASK = "任务提醒"
MSG_RISK = "风险告警"
MSG_COMPETITOR = "竞品异动"
MSG_GEO = "GEO指标异常"
MSG_REPORT = "报表推送"
MSG_SYSTEM = "系统公告"
MSG_TYPES = [MSG_APPROVAL, MSG_TASK, MSG_RISK, MSG_COMPETITOR, MSG_GEO, MSG_REPORT, MSG_SYSTEM]


class Message(Base):
    __tablename__ = "pin_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # None=全员
    category: Mapped[str] = mapped_column(String(20), default=MSG_SYSTEM, index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    level: Mapped[str] = mapped_column(String(10), default="info")  # info/warn/danger
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    link: Mapped[str] = mapped_column(String(120), default="")  # 跳转页面
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


# ── GEO 关键词蒸馏（G1）──────────────────────────────────────────────────────
# 意图类型 → 推荐平台
GEO_INTENT_PLATFORMS = {
    "价格敏感型": ["抖音", "快手"],
    "B2B选品型": ["知乎", "网页SEO"],
    "决策参考型": ["小红书"],
    "通用型": ["综合"],
}


class GeoKeyword(Base):
    __tablename__ = "pin_geo_keywords"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    batch_id: Mapped[str] = mapped_column(String(40), index=True)
    keyword: Mapped[str] = mapped_column(String(200), default="")
    kw_type: Mapped[str] = mapped_column(String(10), default="通用词")   # 通用词/成交词
    intent_type: Mapped[str] = mapped_column(String(20), default="通用型")
    intent_score: Mapped[str] = mapped_column(String(4), default="中")   # 高/中/低
    platform: Mapped[str] = mapped_column(String(40), default="综合")
    created_at: Mapped[str] = mapped_column(String(20), default="")


# ── GEO 多平台收录监测（G4）──────────────────────────────────────────────────
# 国产主流 AI 搜索/问答平台
GEO_AI_PLATFORMS = ["DeepSeek", "豆包", "腾讯元宝", "通义千问", "文心一言", "纳米AI", "KIMI", "智谱清言"]


class GeoInclusion(Base):
    __tablename__ = "pin_geo_inclusion"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    brand: Mapped[str] = mapped_column(String(64), index=True)
    round_id: Mapped[str] = mapped_column(String(40), index=True)  # 同一轮检测分组
    keyword: Mapped[str] = mapped_column(String(200), default="")
    platform: Mapped[str] = mapped_column(String(30), default="")
    included: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)  # 1-10 命中名次，0=未收录
    checked_at: Mapped[str] = mapped_column(String(20), default="")


# ── 商品智能选品（S3-1）──────────────────────────────────────────────────────
class SelectionTask(Base):
    __tablename__ = "pin_selection_tasks"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    brand: Mapped[str] = mapped_column(String(64), default="")
    name: Mapped[str] = mapped_column(String(200), default="")
    industry: Mapped[str] = mapped_column(String(60), default="")
    categories: Mapped[list] = mapped_column(JSON, default=list)
    dimensions: Mapped[list] = mapped_column(JSON, default=list)   # 维度标签
    regions: Mapped[list] = mapped_column(JSON, default=list)
    goal: Mapped[str] = mapped_column(String(30), default="新品")  # 新品/迭代/区域款/竞品对标
    competitors: Mapped[list] = mapped_column(JSON, default=list)
    priority: Mapped[str] = mapped_column(String(10), default="普通")
    task_tags: Mapped[list] = mapped_column(JSON, default=list)
    due_date: Mapped[str] = mapped_column(String(20), default="")
    status: Mapped[str] = mapped_column(String(20), default="已完成")  # 草稿/采集中/分析中/已完成/已归档/分析异常
    score: Mapped[int] = mapped_column(Integer, default=0)         # 头名综合评分
    result: Mapped[dict] = mapped_column(JSON, default=dict)       # 推荐清单/评分/风险
    created_at: Mapped[str] = mapped_column(String(20), default="")


# ── 竞品情报仓库（S3-2）──────────────────────────────────────────────────────
COMPETITOR_DIMENSIONS = ["品牌情报", "产品情报", "舆情情报", "GEO情报", "内容文案", "推广策略"]


class Competitor(Base):
    __tablename__ = "pin_competitors"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(String(120), default="")
    industry: Mapped[str] = mapped_column(String(60), default="")
    categories: Mapped[list] = mapped_column(JSON, default=list)
    channels: Mapped[list] = mapped_column(JSON, default=list)
    frequency: Mapped[str] = mapped_column(String(20), default="每日")  # 实时/每日/每周
    dimensions: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    alert_rules: Mapped[list] = mapped_column(JSON, default=list)  # 上新/调价/活动/负面/排名异动
    status: Mapped[str] = mapped_column(String(20), default="正常监控")  # 正常监控/暂停/已归档
    created_at: Mapped[str] = mapped_column(String(20), default="")
    updated_at: Mapped[str] = mapped_column(String(20), default="")


class CompetitorIntel(Base):
    __tablename__ = "pin_competitor_intel"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(Integer, index=True)
    competitor_id: Mapped[str] = mapped_column(String(40), index=True)
    dimension: Mapped[str] = mapped_column(String(20), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    is_alert: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String(20), default="")


# ── 舆情工单（S2-4）──────────────────────────────────────────────────────────
# 处置分级 → 响应时效（PRD 4.6 / 6.2）
TICKET_SLA = {0: "无需响应", 1: "3 个工作日", 2: "24 小时", 3: "4 小时", 4: "1 小时"}
TICKET_LEVEL_LABEL = {0: "0级·日常", 1: "1级·轻度", 2: "2级·中度", 3: "3级·严重", 4: "4级·重大"}


class SentimentTicket(Base):
    __tablename__ = "pin_sentiment_tickets"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    brand: Mapped[str] = mapped_column(String(64), default="")
    source_id: Mapped[str] = mapped_column(String(40), default="")  # 关联舆情记录
    title: Mapped[str] = mapped_column(String(200), default="")
    level: Mapped[int] = mapped_column(Integer, default=2)          # 0-4
    sla: Mapped[str] = mapped_column(String(30), default="")
    segment_tags: Mapped[list] = mapped_column(JSON, default=list)  # 人群/地域/场景/情绪
    response: Mapped[str] = mapped_column(Text, default="")         # 处置话术/记录
    status: Mapped[str] = mapped_column(String(20), default="待处理")  # 待处理/处理中/已办结
    is_case: Mapped[bool] = mapped_column(Boolean, default=False)   # 归入负面案例库
    created_at: Mapped[str] = mapped_column(String(20), default="")
    closed_at: Mapped[str] = mapped_column(String(20), default="")


# ── 多级审批中心（S2-1）──────────────────────────────────────────────────────
# 审批单状态（复用工作流引擎语义）
APR_PENDING = "审批中"
APR_APPROVED = "已通过"
APR_REJECTED = "已驳回"
APR_WITHDRAWN = "已撤回"

# 步骤状态
STEP_WAIT = "待处理"
STEP_PASS = "已通过"
STEP_REJECT = "已驳回"


class ApprovalRequest(Base):
    __tablename__ = "pin_approval_requests"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(Integer, index=True)
    owner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # 发起人
    owner_name: Mapped[str] = mapped_column(String(60), default="")
    biz_type: Mapped[str] = mapped_column(String(30), default="")   # 文案/GEO方案/舆情处置/选品方案...
    biz_id: Mapped[str] = mapped_column(String(40), default="")     # 关联业务对象
    brand: Mapped[str] = mapped_column(String(64), default="")
    title: Mapped[str] = mapped_column(String(200), default="")
    content: Mapped[str] = mapped_column(Text, default="")          # 当前送审内容快照
    risk_level: Mapped[str] = mapped_column(String(10), default="低")  # 低/中/高
    priority: Mapped[str] = mapped_column(String(10), default="普通")
    status: Mapped[str] = mapped_column(String(20), default=APR_PENDING, index=True)
    current_step: Mapped[int] = mapped_column(Integer, default=1)   # 当前待办步骤号
    version: Mapped[int] = mapped_column(Integer, default=1)        # 修改重提递增
    history: Mapped[list] = mapped_column(JSON, default=list)       # 历史版本内容快照
    urged: Mapped[bool] = mapped_column(Boolean, default=False)     # 是否被催办
    created_at: Mapped[str] = mapped_column(String(20), default="")
    updated_at: Mapped[str] = mapped_column(String(20), default="")


class ApprovalStep(Base):
    __tablename__ = "pin_approval_steps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(40), index=True)
    step_no: Mapped[int] = mapped_column(Integer, default=1)
    approver_role: Mapped[str] = mapped_column(String(30), default="")   # 指派角色
    approver_label: Mapped[str] = mapped_column(String(60), default="")  # 展示名（如"市场主管"）
    status: Mapped[str] = mapped_column(String(20), default=STEP_WAIT)
    comment: Mapped[str] = mapped_column(Text, default="")
    quote: Mapped[str] = mapped_column(Text, default="")  # 驳回时高亮的原文段落
    decided_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    decided_at: Mapped[str] = mapped_column(String(20), default="")


class ApprovalComment(Base):
    __tablename__ = "pin_approval_comments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(40), index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    username: Mapped[str] = mapped_column(String(60), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(20), default="")


# ── AI 网关调用日志（S1-5）──────────────────────────────────────────────────
class AiCallLog(Base):
    __tablename__ = "pin_ai_call_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    module: Mapped[str] = mapped_column(String(40), default="")       # 文案/GEO/舆情/选品/竞品...
    prompt_category: Mapped[str] = mapped_column(String(40), default="")
    model: Mapped[str] = mapped_column(String(60), default="")
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    ts: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
