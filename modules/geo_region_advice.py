"""G5-5 · AI 分省优化建议（对照区域 GEO PRD 的 3 板块 prompt，规则版）。

三板块：① 风险预警省份排序 ② 优先级布局(攻坚/维护/观察) ③ 分平台落地执行动作。
纯规则（确定性、零 token）；接真实 AI 后可换 PRD 原 prompt。
"""
from __future__ import annotations


def advise(stats: dict, industry: str = "茶饮") -> dict:
    """输入 geo_region.stats 结果，输出三板块建议。"""
    own = stats.get("own", {})
    gap = stats.get("gap", {})
    avg = stats.get("national_avg", 0)
    comps = stats.get("competitors", [])
    c0 = comps[0] if comps else "竞品"

    # 板块一：风险预警省份（竞品差距大 + 指数偏低）
    risk = sorted(gap.items(), key=lambda x: x[1])  # 差距最负的最危险
    risk_rows = [(p, g, own.get(p, 0)) for p, g in risk if g < 0][:5]

    # 板块二：优先级布局
    attack, maintain, observe = [], [], []
    for p, idx in own.items():
        g = gap.get(p, 0)
        if idx >= avg and g >= 0:
            maintain.append(p)
        elif g < 0 and idx >= avg * 0.7:
            attack.append(p)       # 落后竞品但有基础 → 攻坚
        else:
            observe.append(p)

    # 板块三：分平台落地动作（基于行业）
    content_focus = ("门店套餐、外卖福利" if industry == "餐饮"
                     else "新品、线下门店位置、团购优惠")

    return {
        "risk": risk_rows, "c0": c0,
        "attack": attack[:4], "maintain": maintain[:4], "observe": observe[:4],
        "content_focus": content_focus, "avg": avg,
        "text": _render_text(risk_rows, attack, maintain, observe, c0, content_focus, avg, industry),
    }


def _render_text(risk_rows, attack, maintain, observe, c0, focus, avg, industry):
    lines = ["【板块一·风险预警省份排序】"]
    if risk_rows:
        for i, (p, g, idx) in enumerate(risk_rows, 1):
            lines.append(f"{i}. {p}：落后{c0} {abs(g)} 分，本省指数 {idx}，建议优先补充本地化问答素材。")
    else:
        lines.append("暂无明显落后省份，整体竞争态势良好。")
    lines.append("")
    lines.append("【板块二·优先级布局省份规划】")
    lines.append(f"1. 优先攻坚（落后但有基础，加大投入）：{('、'.join(attack[:4]) or '暂无')}")
    lines.append(f"2. 稳步维护（已领先，定期维护素材）：{('、'.join(maintain[:4]) or '暂无')}")
    lines.append(f"3. 暂时观察（差距大或竞争低，短期不投）：{('、'.join(observe[:4]) or '暂无')}")
    lines.append("")
    lines.append("【板块三·分平台落地执行动作（未来7天）】")
    _attack2 = "、".join(attack[:2]) or "重点省份"
    lines.append(f"1. 内容方向：围绕「{focus}」补充本地化问答素材；")
    lines.append(f"2. 优先在攻坚省份（{_attack2}）补内容；")
    lines.append(f"3. 抢占{c0}薄弱平台：优先在其曝光低的平台铺设己方优质问答；")
    lines.append("4. 7天清单：每日产出2-3条本地化问答，覆盖攻坚省份核心提问词，发布后回收录监测验证。")
    return "\n".join(lines)
