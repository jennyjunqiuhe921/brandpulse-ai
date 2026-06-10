"""S2-3 GEO 复测前后对比 + 量化效果评估引擎（对齐 PRD 4.5 / 6.13）。

指标：曝光率、信息准确率、品牌排名、竞品差距。
评级标准（PRD 6.13）：
  优秀：核心指标提升 ≥20%
  良好：提升 10%~19%
  一般：提升 0~9%
  无效：无提升或下滑（≤0）

演示模式下，历史任务若无结构化指标，按任务 id+时间确定性合成，保证可复现。
"""
from __future__ import annotations
import hashlib

# 指标定义：key -> (中文名, 是否越大越好, 单位)
METRICS = [
    ("exposure", "曝光率", True, "%"),
    ("accuracy", "信息准确率", True, "%"),
    ("rank", "品牌排名", False, "位"),       # 越小越好
    ("competitor_gap", "竞品差距", False, "%"),  # 越小越好
]


def _seed(s: str) -> float:
    h = int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)
    return (h % 1000) / 1000.0  # 0~1


def synth_metrics(task_id: str, created_at: str = "") -> dict:
    """为缺少结构化指标的任务确定性合成一组演示指标。"""
    r = _seed(task_id + created_at)
    return {
        "exposure": round(40 + r * 45, 1),        # 40~85 %
        "accuracy": round(60 + r * 35, 1),        # 60~95 %
        "rank": int(1 + r * 6),                   # 1~7 位
        "competitor_gap": round(5 + r * 30, 1),   # 5~35 %
    }


def get_metrics(record: dict) -> dict:
    """取记录的结构化指标，缺失则合成。"""
    meta = record.get("meta") or {}
    m = meta.get("metrics")
    if isinstance(m, dict) and m:
        return m
    return synth_metrics(record.get("id", ""), record.get("created_at", ""))


def _growth(base: float, cur: float, bigger_better: bool) -> dict:
    delta = cur - base
    pct = (delta / base * 100) if base else 0.0
    # 对"越小越好"的指标，下降才是提升，效果方向取反
    effective_pct = pct if bigger_better else -pct
    return {"base": base, "current": cur, "delta": round(delta, 1),
            "pct": round(pct, 1), "effective_pct": round(effective_pct, 1)}


def rate_effect(avg_effective_pct: float) -> str:
    if avg_effective_pct >= 20:
        return "优秀"
    if avg_effective_pct >= 10:
        return "良好"
    if avg_effective_pct > 0:
        return "一般"
    return "无效"


_LEVEL_DESC = {
    "优秀": "核心指标提升≥20%，优化目标完全达成，建议固化本轮策略并复制到同类关键词。",
    "良好": "核心指标提升10%~19%，基本达成目标，可针对薄弱指标做小幅迭代。",
    "一般": "核心指标提升0~9%，变化幅度较小，建议重新审视内容补强落地执行力度。",
    "无效": "核心指标无提升或出现下滑，本轮优化未产生正向作用，需排查落地环节并调整方案。",
}


def evaluate(base_rec: dict, cur_rec: dict) -> dict:
    """生成《GEO 优化前后对比 & 效果评估报告》数据。"""
    bm, cm = get_metrics(base_rec), get_metrics(cur_rec)
    rows = []
    effective_list = []
    for key, label, bigger, unit in METRICS:
        g = _growth(bm.get(key, 0), cm.get(key, 0), bigger)
        rows.append({"key": key, "label": label, "unit": unit, **g})
        effective_list.append(g["effective_pct"])
    avg = round(sum(effective_list) / len(effective_list), 1) if effective_list else 0.0
    level = rate_effect(avg)
    # 范围一致性检查（关键词/平台/地域）
    warnings = []
    if base_rec.get("region") and cur_rec.get("region") and \
            base_rec["region"] != cur_rec["region"]:
        warnings.append(f"监测地域不一致（基准 {base_rec['region']} vs 本轮 {cur_rec['region']}），"
                        "对比结果仅供参考。")
    if base_rec.get("period") != cur_rec.get("period"):
        warnings.append("监测周期不同，趋势对比仅供参考。")
    return {
        "rows": rows, "avg_effective_pct": avg, "effect_level": level,
        "evaluate_desc": _LEVEL_DESC[level],
        "optimize_suggest": _suggest(rows, level),
        "warnings": warnings,
    }


def _suggest(rows: list, level: str) -> str:
    weak = [r for r in rows if r["effective_pct"] < 5]
    if not weak:
        return "各项指标均有提升，建议保持节奏并扩大关键词覆盖。"
    names = "、".join(r["label"] for r in weak)
    return f"重点关注提升不足的指标：{names}。建议补强对应官网/FAQ/媒体内容并在下轮复测验证。"
