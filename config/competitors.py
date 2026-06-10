"""S3-2 竞品情报仓库 — 数据库存储（按租户隔离）。"""
from __future__ import annotations
import uuid
import hashlib
from datetime import datetime

from db.engine import get_session
from db.models import Competitor, CompetitorIntel, COMPETITOR_DIMENSIONS
from db import context as ctx
from db import messages as msg_store
from db.models import MSG_COMPETITOR

FREQUENCIES = ["实时", "每日", "每周"]
CHANNELS = ["社交种草", "点评", "综合社交", "新闻", "电商", "问答"]
ALERT_RULES = ["上新", "调价", "活动", "负面", "排名异动"]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _to_dict(c: Competitor) -> dict:
    return {
        "id": c.id, "name": c.name, "industry": c.industry,
        "categories": c.categories or [], "channels": c.channels or [],
        "frequency": c.frequency, "dimensions": c.dimensions or [],
        "tags": c.tags or [], "alert_rules": c.alert_rules or [],
        "status": c.status, "created_at": c.created_at, "updated_at": c.updated_at,
    }


# ── 竞品主体管理 ─────────────────────────────────────────────────────────────
def add(name: str, industry: str, categories: list, channels: list, frequency: str,
        dimensions: list, alert_rules: list, tags: list | None = None) -> str:
    cid = "cmp_" + uuid.uuid4().hex[:8]
    with get_session() as s:
        s.add(Competitor(
            id=cid, tenant_id=ctx.tenant_id(), owner_id=ctx.user_id(),
            name=name, industry=industry, categories=categories or [],
            channels=channels or [], frequency=frequency, dimensions=dimensions or [],
            alert_rules=alert_rules or [], tags=tags or [], status="正常监控",
            created_at=_now(), updated_at=_now()))
    # 首次添加即生成一批情报（演示）
    _generate_intel(cid, name, dimensions or COMPETITOR_DIMENSIONS)
    return cid


def list_all(status: str | None = None) -> list:
    with get_session() as s:
        q = s.query(Competitor).filter(Competitor.tenant_id == ctx.tenant_id())
        if status and status != "全部":
            q = q.filter(Competitor.status == status)
        rows = [_to_dict(c) for c in q.all()]
    return sorted(rows, key=lambda x: x["created_at"], reverse=True)


def get(cid: str) -> dict | None:
    with get_session() as s:
        c = s.query(Competitor).filter(
            Competitor.id == cid, Competitor.tenant_id == ctx.tenant_id()).first()
        return _to_dict(c) if c else None


def set_status(cid: str, status: str) -> bool:
    with get_session() as s:
        c = s.query(Competitor).filter(
            Competitor.id == cid, Competitor.tenant_id == ctx.tenant_id()).first()
        if not c:
            return False
        c.status = status
        c.updated_at = _now()
        return True


def delete(cid: str) -> bool:
    with get_session() as s:
        c = s.query(Competitor).filter(
            Competitor.id == cid, Competitor.tenant_id == ctx.tenant_id()).first()
        if not c:
            return False
        s.delete(c)
        s.query(CompetitorIntel).filter(CompetitorIntel.competitor_id == cid).delete()
        return True


# ── 情报生成与查询（演示：确定性合成）──────────────────────────────────────────
_INTEL_TEMPLATES = {
    "品牌情报": "{n} 近期强化高端化叙事，社媒声量环比上升，品牌心智集中在「{c}」。",
    "产品情报": "{n} 本周上新 2 款季节限定，主打鲜果赛道，定价 18-25 元区间。",
    "舆情情报": "{n} 整体口碑正向 65%，主要负面集中在排队时长与价格敏感。",
    "GEO情报": "{n} 在主流 AI 问答中曝光率约 60%，'性价比'关联词较强。",
    "内容文案": "{n} 小红书种草以「真实果肉」「颜值出片」为高频钩子，互动中等偏上。",
    "推广策略": "{n} 近期以联名+限定营销为主，渠道侧重外卖平台满减引流。",
}


def _generate_intel(cid: str, name: str, dimensions: list) -> None:
    cat = "鲜果茶" if "茶" in name else "核心品类"
    rows = []
    for dim in dimensions:
        tmpl = _INTEL_TEMPLATES.get(dim, "{n} 在 {d} 维度有常态化动态。")
        rows.append(CompetitorIntel(
            tenant_id=ctx.tenant_id(), competitor_id=cid, dimension=dim,
            content=tmpl.format(n=name, c=cat, d=dim), created_at=_now()))
    with get_session() as s:
        for r in rows:
            s.add(r)


def list_intel(cid: str, dimension: str | None = None) -> list:
    with get_session() as s:
        q = s.query(CompetitorIntel).filter(
            CompetitorIntel.tenant_id == ctx.tenant_id(),
            CompetitorIntel.competitor_id == cid)
        if dimension:
            q = q.filter(CompetitorIntel.dimension == dimension)
        rows = q.order_by(CompetitorIntel.id.desc()).all()
        return [{"dimension": r.dimension, "content": r.content,
                 "is_alert": r.is_alert, "created_at": r.created_at} for r in rows]


def trigger_alert(cid: str, name: str, rule: str) -> None:
    """演示：手动触发一条竞品异动预警，写情报 + 推消息。"""
    content = f"⚠️ 监测到「{name}」发生【{rule}】异动，请关注。"
    with get_session() as s:
        s.add(CompetitorIntel(
            tenant_id=ctx.tenant_id(), competitor_id=cid, dimension="品牌情报",
            content=content, is_alert=True, created_at=_now()))
    msg_store.push(f"竞品异动：{name} · {rule}", content,
                   category=MSG_COMPETITOR, level="warn", link="pages/17_竞品情报.py")
