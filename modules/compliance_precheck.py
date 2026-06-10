"""B5 · 合规预检（轻量、即时、无需 LLM 调用）。

基于《广告法》绝对化用语与常见违禁表述做关键词扫描，
在内容生成完成后立即给出风险等级，高风险时禁止导出。
完整的逐条合规审查仍由「合规卫士」模块的 LLM 流程负责。
"""
from __future__ import annotations
import re

# ── 高风险：广告法明令禁止的绝对化用语 ──
_HIGH_RISK = [
    "最佳", "最好", "最优", "最强", "最大", "最高", "最低", "最便宜", "最新",
    "第一", "唯一", "独一无二", "顶级", "顶尖", "极致", "极品", "巅峰",
    "国家级", "世界级", "全球领先", "行业领先", "销量第一", "排名第一",
    "绝对", "百分百", "100%有效", "永久", "万能", "包治", "根治", "彻底解决",
    "史无前例", "空前绝后", "无与伦比", "首选品牌", "驰名商标",
]

# ── 中风险：功效/承诺类需核实表述 ──
_MED_RISK = [
    "治疗", "疗效", "药效", "抗癌", "防癌", "杀菌率", "100%",
    "立竿见影", "马上见效", "一次见效", "无副作用", "纯天然无添加",
    "升值", "稳赚", "保本", "零风险", "稳赚不赔",
    "瘦身", "减肥成功", "美白祛斑", "丰胸",
]


def _find(text: str, words: list) -> list:
    hits = []
    for w in words:
        if w in text:
            hits.append(w)
    return hits


def precheck(text: str) -> dict:
    """返回 {level, score, high, med, can_export, summary}

    level: '高' / '中' / '低'
    can_export: 高风险为 False，导出按钮应禁用
    """
    text = text or ""
    high = _find(text, _HIGH_RISK)
    med = _find(text, _MED_RISK)

    if high:
        level, can_export = "高", False
    elif med:
        level, can_export = "中", True
    else:
        level, can_export = "低", True

    if level == "高":
        summary = f"检测到 {len(high)} 处绝对化用语，存在《广告法》违规风险，需修改后方可导出。"
    elif level == "中":
        summary = f"检测到 {len(med)} 处功效/承诺类表述，建议核实真实性并补充依据。"
    else:
        summary = "未检测到明显违规用语，仍建议经人工复核后发布。"

    return {
        "level": level,
        "high": high,
        "med": med,
        "can_export": can_export,
        "summary": summary,
    }
