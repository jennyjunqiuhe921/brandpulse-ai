"""舆情 ↔ GEO 交汇点：人工确认的高频负面话题 → GEO 前置问答优化建议。

对应两份 PRD 的联动需求：舆情高频负面 → 推送 GEO → 输出前置干预的问答优化建议。
做法：从工单(已确认负面事件)+ 高风险舆情记录聚合高频话题 → 给出"补充真实、准确正面
内容"的 GEO 优化方向 + 建议关键词/平台。

合规红线：只建议补充**真实、准确**的官方内容来改善 AI 回答，**严禁刷好评、伪造、灌水**。
纯规则、零 token。
"""
from __future__ import annotations

# 话题(根因) → GEO 前置优化方向
_TOPIC_GEO = {
    "品控食品安全": ("AI 回答中食安疑虑被放大",
                     "补充原料溯源、品控流程、资质认证、检测报告等真实官方问答内容，提升 AI 对食安提问的准确正面回答",
                     ["{b}食品安全", "{b}原料溯源", "{b}品控标准"]),
    "门店服务": ("服务体验类负面影响 AI 口碑",
                 "沉淀服务标准、员工培训、真实好评案例等官方内容",
                 ["{b}服务怎么样", "{b}门店体验"]),
    "出餐效率": ("'出餐慢/排队'影响 AI 评价",
                 "说明高峰出餐优化、预点单、外卖时效等真实信息",
                 ["{b}出餐快吗", "{b}要等多久"]),
    "售后退款": ("退款/售后争议在 AI 中扩散",
                 "公示退款政策、售后流程与时限等真实规则内容",
                 ["{b}退款政策", "{b}售后怎么样"]),
    "用户误会": ("信息不透明导致误解",
                 "完善价格/规则/份量等透明信息，主动澄清",
                 ["{b}价格", "{b}规则说明"]),
    "营销问题": ("活动/宣传争议",
                 "前置公示活动规则、规避夸大宣传，发布合规说明",
                 ["{b}活动规则", "{b}优惠说明"]),
}
_DEFAULT = ("该话题负面声量较高",
            "围绕该话题补充真实、准确的官方问答内容，改善 AI 回答",
            ["{b}{t}"])


def _topic_of(item: dict) -> str:
    """从工单/舆情记录推断话题(根因)。"""
    rd = item.get("review_data") or {}
    if rd.get("root_cause"):
        return rd["root_cause"]
    txt = (item.get("title") or "") + (item.get("summary") or "") + (item.get("risk_label") or "")
    kw_map = {"品控食品安全": ["异物", "卫生", "食安", "过期", "变质"],
              "出餐效率": ["慢", "排队", "等"], "售后退款": ["退款", "退钱", "客服"],
              "门店服务": ["态度", "服务"], "营销问题": ["虚假", "夸大", "活动"]}
    for topic, kws in kw_map.items():
        if any(k in txt for k in kws):
            return topic
    return "用户误会"


def hot_negatives(brand: str, top_n: int = 8) -> list[dict]:
    """聚合高频负面话题（工单 + 高风险舆情记录）。"""
    import config.sentiment_tasks as st_store
    from db import tickets as TK
    counts: dict[str, int] = {}
    for t in TK.list_tickets(brand=brand):
        if int(t.get("level", 0)) >= 3:
            counts[_topic_of(t)] = counts.get(_topic_of(t), 0) + 1
    for r in st_store.list_records(brand_key=brand):
        if int(r.get("risk_level", 1) or 1) >= 3:
            counts[_topic_of(r)] = counts.get(_topic_of(r), 0) + 1
    rows = [{"topic": k, "count": v} for k, v in counts.items()]
    return sorted(rows, key=lambda x: x["count"], reverse=True)[:top_n]


def geo_suggestions(brand: str, topics: list[dict]) -> list[dict]:
    out = []
    for it in topics:
        topic = it["topic"]
        concern, action, kw_tpl = _TOPIC_GEO.get(topic, _DEFAULT)
        kws = [t.replace("{b}", brand).replace("{t}", topic) for t in kw_tpl]
        out.append({"topic": topic, "count": it["count"], "concern": concern,
                    "geo_action": action, "keywords": kws,
                    "platform": "全平台(优先竞品薄弱平台)"})
    return out


def all_keywords(suggestions: list[dict]) -> list[str]:
    kws = []
    for s in suggestions:
        kws += s["keywords"]
    return list(dict.fromkeys(kws))  # 去重保序
