"""G1 · GEO 关键词蒸馏引擎。

输入 产品/服务 + 地域 + 卖点，蒸馏长尾词，并对每个词：
- 标「通用词 / 成交词」
- 判定意图类型（价格敏感/B2B选品/决策参考/通用）
- 打成交意图分（高/中/低）
- 分配推荐平台

纯规则实现（确定性、零额外依赖、零 token 成本）。接真实 AI 后可在此基础上扩展挖词。
"""
from __future__ import annotations
from db.models import GEO_INTENT_PLATFORMS

# 意图信号词 → 意图类型
_PRICE = ["多少钱", "价格", "报价", "便宜", "性价比", "优惠", "促销"]
_B2B = ["厂家", "批发", "定制", "供应商", "代理", "加盟", "招商", "OEM"]
_DECISION = ["哪家好", "推荐", "避雷", "怎么选", "排行", "测评", "对比", "靠谱", "口碑"]

# 各意图的后缀模板
_SUFFIX = {
    "价格敏感型": ["多少钱", "价格", "贵不贵", "性价比"],
    "B2B选品型": ["厂家", "批发", "定制", "供应商"],
    "决策参考型": ["哪家好", "推荐", "怎么选", "避雷", "测评"],
    "通用型": ["", "怎么样", "介绍"],
}
_SCORE = {"价格敏感型": "高", "B2B选品型": "高", "决策参考型": "中", "通用型": "低"}


def _classify(kw: str) -> str:
    if any(w in kw for w in _PRICE):
        return "价格敏感型"
    if any(w in kw for w in _B2B):
        return "B2B选品型"
    if any(w in kw for w in _DECISION):
        return "决策参考型"
    return "通用型"


def distill(product: str, region: str = "", service: str = "",
            highlights: str = "", max_n: int = 40) -> list[dict]:
    """返回蒸馏后的关键词列表（去重）。"""
    product = (product or "").strip()
    if not product:
        return []
    region = (region or "").strip()
    services = [s.strip() for s in (service or "").replace("，", ",").split(",") if s.strip()]

    seeds = set()
    # 基础词：地域+产品、产品+服务
    bases = [product]
    if region:
        bases.append(f"{region}{product}")
    for s in services:
        bases.append(f"{product}{s}")
        if region:
            bases.append(f"{region}{product}{s}")

    # 基础 × 各意图后缀
    for b in bases:
        for intent, suffixes in _SUFFIX.items():
            for suf in suffixes:
                kw = (b + suf).strip()
                if kw:
                    seeds.add(kw)

    rows = []
    seen = set()
    for kw in seeds:
        if kw in seen:
            continue
        seen.add(kw)
        intent = _classify(kw)
        # 成交词：含地域/价格/厂家/决策信号；纯品类=通用词
        is_deal = (intent != "通用型") or (region and region in kw)
        platform = "、".join(GEO_INTENT_PLATFORMS.get(intent, ["综合"]))
        rows.append({
            "keyword": kw,
            "kw_type": "成交词" if is_deal else "通用词",
            "intent_type": intent,
            "intent_score": _SCORE[intent] if is_deal else "低",
            "platform": platform,
        })

    # 排序：成交词优先、高意图优先、词更短优先（更精准）
    order = {"高": 0, "中": 1, "低": 2}
    rows.sort(key=lambda r: (r["kw_type"] != "成交词", order[r["intent_score"]], len(r["keyword"])))
    return rows[:max_n]


def high_intent(rows: list[dict]) -> list[str]:
    """提取高意图成交词（供一键带入收录监测/内容创作）。"""
    return [r["keyword"] for r in rows if r["kw_type"] == "成交词" and r["intent_score"] in ("高", "中")]
