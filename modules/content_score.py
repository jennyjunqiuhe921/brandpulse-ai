"""S2-2 内容热度评分（0-10）— 基于可观测特征的轻量启发式评估。

维度：长度适中度、表情符号、话题标签、行动号召、情绪词、平台适配。
仅作内容优化参考，非真实传播数据。
"""
from __future__ import annotations
import re

_CTA = ["点击", "关注", "评论", "扣1", "私信", "下单", "立即", "戳", "链接", "购买", "领取"]
_EMO = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]")
_EMOTION = ["绝了", "爱了", "心动", "惊艳", "上头", "宝藏", "好喝", "必", "yyds", "强烈推荐"]


def heat_score(text: str, platforms: list | None = None) -> dict:
    text = text or ""
    n = len(text)
    # 长度适中度（150-600 字最佳）
    if 150 <= n <= 600:
        len_s = 2.5
    elif n < 150:
        len_s = max(0.5, n / 150 * 2.5)
    else:
        len_s = max(1.0, 2.5 - (n - 600) / 600)
    emoji_s = min(2.0, len(_EMO.findall(text)) * 0.4)
    tag_s = min(2.0, text.count("#") * 0.5)
    cta_s = 1.5 if any(k in text for k in _CTA) else 0.0
    emo_s = min(1.5, sum(text.count(k) for k in _EMOTION) * 0.5)
    plat_s = min(0.5, len(platforms or []) * 0.25)
    total = round(min(10.0, len_s + emoji_s + tag_s + cta_s + emo_s + plat_s), 1)
    tips = []
    if emoji_s < 1:
        tips.append("可适当增加表情符号提升亲和力")
    if tag_s < 1:
        tips.append("建议补充 2-3 个话题标签 #")
    if cta_s == 0:
        tips.append("缺少行动号召（关注/评论/下单等）")
    if n > 600:
        tips.append("文案偏长，可精简以提升完读率")
    return {"score": total, "tips": tips}


def score_badge(score: float) -> str:
    color = "#2E7D32" if score >= 7 else ("#F9A825" if score >= 4 else "#C62828")
    return (f'<span style="background:{color};color:#fff;padding:2px 9px;border-radius:10px;'
            f'font-size:12px;font-weight:600">🔥 热度 {score}/10</span>')
