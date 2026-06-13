"""D5-1 · 月度口碑健康分（五维模型，对照 PRD Prompt5）。

五维：情感结构 / 负面舆情占比 / 高危红标事件数 / 传播热度 / 问题风险权重。
0-100 整数 + 一句汇报评语。剔除待验证舆情；已完成消影/复盘的事件扣分权重下调。

纯规则计算（确定性、零 token），基于品牌的舆情记录。接真实 AI 后可换 Prompt5。
"""
from __future__ import annotations


def _band_comment(score: int) -> str:
    if score >= 85:
        return "口碑健康，舆情结构良好，保持常规监测即可。"
    if score >= 70:
        return "口碑良好，存在少量负面，建议关注高频话题并及时回应。"
    if score >= 55:
        return "口碑一般，负面占比偏高，需主动处置重点舆情、加强公关响应。"
    return "口碑承压，高危/负面舆情较多，建议立即启动重点处置与复盘整改。"


def compute(records: list[dict]) -> dict:
    """records: sentiment_tasks.list_records 结果（含 risk_level）。
    返回 {score, comment, dims, total, valid, negative, high_risk}。"""
    # 剔除待验证（risk_level<=0 视为待验证；正常 1-5）
    valid = [r for r in records if int(r.get("risk_level", 1) or 1) >= 1]
    total = len(valid)
    if total == 0:
        return {"score": None, "comment": "暂无有效舆情样本，请先在「舆情分析」采集/生成数据。",
                "dims": {}, "total": 0, "valid": 0, "negative": 0, "high_risk": 0}

    negative = [r for r in valid if int(r.get("risk_level", 1)) >= 3]   # 3级及以上=负面/风险
    high = [r for r in valid if int(r.get("risk_level", 1)) >= 4]       # 4级红标=高危
    neg_ratio = len(negative) / total
    high_n = len(high)

    # 已完成消影/复盘的事件降权（meta.resolved 标记）
    resolved = sum(1 for r in negative if (r.get("tags") and "已消影" in r.get("tags", [])))
    resolved_relief = min(0.15, resolved * 0.03)  # 最多回血 15%

    # 综合分
    raw = 100 - neg_ratio * 45 - min(high_n, 12) * 3
    raw += raw * resolved_relief
    score = max(0, min(100, round(raw)))

    # 五维拆解（各 0-100，便于展示）
    dims = {
        "情感结构": round((1 - neg_ratio) * 100),
        "负面占比": round((1 - neg_ratio) * 100),
        "高危红标": round(max(0, 100 - high_n * 12)),
        "传播热度": round(max(40, 100 - total * 1.5)),   # 量越大热度风险略升（演示）
        "风险权重": round(max(0, 100 - high_n * 10 - len(negative) * 2)),
    }
    return {"score": score, "comment": _band_comment(score), "dims": dims,
            "total": total, "valid": total, "negative": len(negative), "high_risk": high_n}
