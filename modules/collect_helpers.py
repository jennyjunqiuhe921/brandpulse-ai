"""E1+E2 · 数据采集辅助：渠道风险标注 + 关键词分组归类。"""
from __future__ import annotations

# ── E2 · 渠道风险等级 ────────────────────────────────────────────────────────
# UGC/匿名渠道内容易失真、易极端，标注为高风险，提示需谨慎采信
_CHANNEL_RISK = {
    "抖音": ("高", "🔴", "UGC短视频，内容情绪化/失真风险高"),
    "快手": ("高", "🔴", "UGC短视频，需谨慎采信"),
    "贴吧": ("高", "🔴", "匿名社区，真实性待核实"),
    "小红书": ("中", "🟡", "种草社区，含营销内容"),
    "微博": ("中", "🟡", "公开社交，含水军风险"),
    "B站": ("中", "🟡", "UGC社区，含主观测评"),
    "大众点评": ("中", "🟡", "O2O点评，含同行干扰"),
    "美团": ("中", "🟡", "O2O点评，含刷评风险"),
    "新闻媒体": ("低", "🟢", "媒体报道，相对权威"),
    "微信公众号": ("低", "🟢", "官方/机构内容"),
    "官方": ("低", "🟢", "品牌官方信息"),
}


def channel_risk(source: str) -> tuple[str, str, str]:
    """返回 (风险等级, 图标, 说明)。未知渠道默认中风险。"""
    for k, v in _CHANNEL_RISK.items():
        if k in (source or ""):
            return v
    return ("中", "🟡", "渠道未知，建议人工核实")


# ── E1 · 关键词分组归类 ──────────────────────────────────────────────────────
DEFAULT_NEGATIVE_WORDS = ["难喝", "难吃", "贵", "排队", "差", "失望", "投诉", "不新鲜", "退款", "异物"]


def _match(text: str, words: list) -> bool:
    return any(w and w in text for w in words)


def group_by_keywords(results: list, brand_words: list, product_words: list,
                      negative_words: list) -> dict:
    """把采集到的评论按「品牌词/产品词/负面词」三组归类。
    一条评论可同时命中多组。返回 {组名: [ {topic, comment, source} ]}。"""
    groups = {"品牌词": [], "产品词": [], "负面词": []}
    for topic in results or []:
        src = topic.get("source", "")
        for c in topic.get("comments", []):
            text = c.get("content", "")
            item = {"topic": topic.get("title", ""), "comment": c, "source": src}
            if brand_words and _match(text, brand_words):
                groups["品牌词"].append(item)
            if product_words and _match(text, product_words):
                groups["产品词"].append(item)
            if _match(text, negative_words):
                groups["负面词"].append(item)
    return groups
