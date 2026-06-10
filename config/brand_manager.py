"""品牌档案 — 数据库存储（按租户隔离）。

接口签名保持与原 JSON 版一致，页面无需改动；内部改为 SQLAlchemy，
所有读写限定在当前登录用户所属租户内。
"""
from __future__ import annotations
import uuid

from db.engine import get_session
from db.models import Brand
from db import context as ctx

# Industries available for selection
INDUSTRY_OPTIONS = [
    "新式茶饮", "餐饮食品", "快消品", "美妆个护",
    "科技互联网", "电商零售", "教育培训", "医疗健康",
    "汽车出行", "金融服务", "文化娱乐", "其他",
]

# F2 · 品牌调性枚举（联动影响内容生成风格）
TONE_OPTIONS = [
    "高端精致", "活泼年轻", "国潮文化", "专业严谨",
    "温暖治愈", "酷潮态度", "亲民接地气", "简约极简",
]


def _to_dict(b: Brand) -> dict:
    return {
        "id": b.id,
        "name": b.name,
        "industry": b.industry or "",
        "description": b.description or "",
        "focus": b.focus or "",
        "collection_name": b.collection_name or f"pinsight_{b.id}",
        "color": b.color or "#1A1A1A",
        "tone": b.tone or "",
        "brand_words": b.brand_words or [],
        "forbidden_words": b.forbidden_words or [],
        "is_demo": bool(b.is_demo),
    }


def load_all_brands() -> dict:
    """当前租户的全部品牌 {id: data}，演示品牌在前、其余按名称。"""
    tid = ctx.tenant_id()
    with get_session() as s:
        rows = s.query(Brand).filter(Brand.tenant_id == tid).all()
        items = [_to_dict(b) for b in rows]
    items.sort(key=lambda x: (not x["is_demo"], x["name"]))
    return {d["id"]: d for d in items}


def get_brand(brand_id: str) -> dict | None:
    tid = ctx.tenant_id()
    with get_session() as s:
        b = s.query(Brand).filter(Brand.id == brand_id, Brand.tenant_id == tid).first()
        return _to_dict(b) if b else None


def _safe_slug(name: str) -> str:
    """ASCII-only slug，供 ChromaDB collection 名使用。"""
    ascii_only = "".join(c if (c.isascii() and c.isalnum()) else "_" for c in name.lower())
    parts = [p for p in ascii_only.split("_") if p]
    slug = "_".join(parts)[:20].strip("_")
    return slug or "brand"


def create_brand(name: str, industry: str, description: str, focus: str, color: str = "#1A1A1A",
                 tone: str = "", brand_words: list | None = None,
                 forbidden_words: list | None = None) -> str:
    slug = _safe_slug(name)
    brand_id = f"{slug}_{uuid.uuid4().hex[:6]}"
    with get_session() as s:
        s.add(Brand(
            id=brand_id,
            tenant_id=ctx.tenant_id(),
            owner_id=ctx.user_id(),
            name=name,
            industry=industry,
            description=description,
            focus=focus,
            collection_name=f"pinsight_{brand_id}",
            color=color,
            tone=tone,
            brand_words=brand_words or [],
            forbidden_words=forbidden_words or [],
            is_demo=False,
        ))
    return brand_id


def update_brand(brand_id: str, **kwargs):
    allowed = {"name", "industry", "description", "focus", "color",
               "tone", "brand_words", "forbidden_words"}
    tid = ctx.tenant_id()
    with get_session() as s:
        b = s.query(Brand).filter(Brand.id == brand_id, Brand.tenant_id == tid).first()
        if b is None:
            raise ValueError(f"品牌不存在：{brand_id}")
        for k, v in kwargs.items():
            if k in allowed and v is not None:
                setattr(b, k, v)


def delete_brand(brand_id: str):
    tid = ctx.tenant_id()
    with get_session() as s:
        b = s.query(Brand).filter(Brand.id == brand_id, Brand.tenant_id == tid).first()
        if b is None:
            raise ValueError(f"品牌不存在：{brand_id}")
        coll = b.collection_name
        s.delete(b)
    # 删除对应的 ChromaDB 知识库
    try:
        from core.rag_engine import get_client
        get_client().delete_collection(coll)
    except Exception:
        pass


# ── Convenience helpers ───────────────────────────────────────────────────────

def get_brand_name(brand_id: str) -> str:
    b = get_brand(brand_id)
    return b["name"] if b else brand_id


def get_brand_focus(brand_id: str) -> str:
    b = get_brand(brand_id)
    return b.get("focus", "") if b else ""


def get_collection_name(brand_id: str) -> str:
    b = get_brand(brand_id)
    if b:
        return b["collection_name"]
    return f"pinsight_{brand_id}"
