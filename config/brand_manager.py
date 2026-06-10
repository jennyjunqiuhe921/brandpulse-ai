"""Brand registry — manages brand metadata stored as JSON files in brands/."""
from __future__ import annotations
import json
import uuid
from datetime import datetime
from pathlib import Path

BRANDS_DIR = Path(__file__).parent.parent / "brands"
BRANDS_DIR.mkdir(exist_ok=True)

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


def _brand_path(brand_id: str) -> Path:
    return BRANDS_DIR / f"{brand_id}.json"


def load_all_brands() -> dict:
    """Return all brands as {id: data}, demo brands first then by name."""
    brands = {}
    for f in sorted(BRANDS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if "id" in data:
                brands[data["id"]] = data
        except Exception:
            pass
    # Demo brands first, then alphabetical by name
    return dict(
        sorted(brands.items(), key=lambda x: (not x[1].get("is_demo", False), x[1].get("name", "")))
    )


def get_brand(brand_id: str) -> dict | None:
    """Get a single brand by ID. Returns None if not found."""
    path = _brand_path(brand_id)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _safe_slug(name: str) -> str:
    """Generate an ASCII-only slug safe for ChromaDB collection names."""
    # Keep only ASCII letters and digits, replace everything else with _
    ascii_only = "".join(c if (c.isascii() and c.isalnum()) else "_" for c in name.lower())
    # Collapse consecutive underscores, strip leading/trailing
    parts = [p for p in ascii_only.split("_") if p]
    slug = "_".join(parts)[:20].strip("_")
    return slug or "brand"  # fallback if name is entirely non-ASCII


def create_brand(name: str, industry: str, description: str, focus: str, color: str = "#1A1A1A",
                 tone: str = "", brand_words: list | None = None,
                 forbidden_words: list | None = None) -> str:
    """Create a new brand. Returns the new brand ID."""
    slug = _safe_slug(name)
    brand_id = f"{slug}_{uuid.uuid4().hex[:6]}"
    data = {
        "id": brand_id,
        "name": name,
        "industry": industry,
        "description": description,
        "focus": focus,
        "collection_name": f"pinsight_{brand_id}",
        "color": color,
        "tone": tone,
        "brand_words": brand_words or [],
        "forbidden_words": forbidden_words or [],
        "is_demo": False,
        "created_at": datetime.now().isoformat(),
    }
    _brand_path(brand_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return brand_id


def update_brand(brand_id: str, **kwargs):
    """Update mutable fields (name, industry, description, focus, color)."""
    data = get_brand(brand_id)
    if data is None:
        raise ValueError(f"品牌不存在：{brand_id}")
    # Demo brands can be edited like any other brand
    allowed = {"name", "industry", "description", "focus", "color",
               "tone", "brand_words", "forbidden_words"}
    for k, v in kwargs.items():
        if k in allowed and v is not None:
            data[k] = v
    _brand_path(brand_id).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def delete_brand(brand_id: str):
    """Delete a brand and its ChromaDB collection."""
    data = get_brand(brand_id)
    if data is None:
        raise ValueError(f"品牌不存在：{brand_id}")
    # Demo brands can be deleted — will lose demo data
    # Remove ChromaDB collection
    try:
        from core.rag_engine import get_client
        get_client().delete_collection(data["collection_name"])
    except Exception:
        pass
    _brand_path(brand_id).unlink(missing_ok=True)


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
    # Fallback: generate on the fly so nothing breaks
    return f"pinsight_{brand_id}"
