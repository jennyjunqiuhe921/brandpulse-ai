"""S3-1 选品综合评分引擎（对齐 PRD 4.7.5）。

综合评分(总分100)：市场热度30 + 口碑30 + 差异化20 + 合规20。
演示模式下，候选品类按确定性合成评分，保证可复现；非真实采集数据。
"""
from __future__ import annotations
import hashlib

# 各行业候选产品池（演示用）
_POOL = {
    "新式茶饮": ["油柑系列", "茉莉奶绿", "厚乳波波", "桂花酒酿", "杨梅冰萃",
                 "生椰拿铁", "黄皮气泡", "栀子绿妍", "芋泥啵啵", "青提乌龙"],
    "美妆护肤": ["早C晚A精华", "屏障修护霜", "氨基酸洁面", "视黄醇眼霜", "积雪草面膜"],
    "餐饮连锁": ["藤椒鸡套餐", "麻酱凉皮", "现烤欧包", "黑松露意面", "麻辣香锅"],
    "_default": ["新品A", "新品B", "新品C", "新品D", "新品E"],
}

_FORBIDDEN_HINT = ["零热量", "减脂", "养生", "药用", "抗癌", "最", "第一"]


def _seed(s: str) -> float:
    return (int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16) % 1000) / 1000.0


def _score_one(name: str, dims: list, competitors: list) -> dict:
    r = _seed(name)
    heat = round(12 + r * 18, 1)          # 市场热度 /30
    reputation = round(12 + _seed(name + "rep") * 18, 1)  # 口碑 /30
    diff = round(8 + _seed(name + "diff") * 12, 1)        # 差异化 /20
    compliance = round(14 + _seed(name + "cmp") * 6, 1)   # 合规 /20
    # 维度适配加分（命中维度标签略增热度）
    if dims:
        heat = min(30.0, heat + len(dims) * 0.3)
    # 竞品对标：若有对标竞品，差异化要求更高（略降）
    if competitors:
        diff = max(0.0, diff - 1.0)
    total = round(heat + reputation + diff + compliance, 1)
    # 合规风险提示
    risk = "低"
    if compliance < 16:
        risk = "中"
    return {
        "name": name, "total": total, "heat": heat, "reputation": reputation,
        "diff": diff, "compliance": compliance, "risk": risk,
        "match": "高" if total >= 75 else ("中" if total >= 60 else "低"),
    }


def analyze(categories: list, dimensions: list, competitors: list,
            industry: str = "") -> dict:
    pool = _POOL.get(industry, _POOL["_default"])
    # 候选 = 品类名 + 行业池，去重
    cands = []
    seen = set()
    for c in (categories or []) + pool:
        if c and c not in seen:
            seen.add(c)
            cands.append(c)
    scored = [_score_one(c, dimensions, competitors) for c in cands[:10]]
    scored.sort(key=lambda x: x["total"], reverse=True)
    top = scored[0] if scored else None
    # 合规专项：标注需注意的违规宣传词
    compliance_notes = (
        "选品文案需规避以下违规表述：" + "、".join(_FORBIDDEN_HINT)
        if industry == "新式茶饮" else
        "选品宣传须符合广告法，避免绝对化用语与未经证实的功效声明。")
    return {
        "recommendations": scored,
        "top_score": int(top["total"]) if top else 0,
        "top_name": top["name"] if top else "",
        "compliance_notes": compliance_notes,
    }
