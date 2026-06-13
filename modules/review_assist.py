"""D5-3 · 复盘根因智能分析（对照 PRD Prompt6）。

结合舆情内容、处置记录、风险等级，自动归类根因并给整改建议，一键回填复盘表单。
纯规则（确定性、零 token）；接真实 AI 后可换 Prompt6。
"""
from __future__ import annotations

ROOT_CAUSES = ["品控食品安全", "门店服务", "出餐效率", "售后退款", "用户误会", "营销问题"]
SCOPES = ["单店", "区域", "全网"]

_KW = {
    "品控食品安全": ["异物", "卫生", "食安", "变质", "过期", "头发", "拉肚子", "食物中毒"],
    "出餐效率": ["慢", "排队", "等", "出餐", "久"],
    "售后退款": ["退款", "退钱", "团购", "不退", "客服"],
    "门店服务": ["态度", "服务", "店员", "冷漠", "吵"],
    "营销问题": ["虚假", "夸大", "广告", "活动", "套路"],
}

_ACTIONS = {
    "品控食品安全": "立即自查原料与出品流程、留存证据、必要时停售排查；对涉事门店做食安专项培训。",
    "门店服务": "复盘当班服务记录，开展服务话术与情绪管理培训，建立顾客投诉首问负责制。",
    "出餐效率": "优化高峰排班与出餐动线，设置出餐时限看板，必要时增配人手。",
    "售后退款": "梳理退款 SOP 与时限，授权一线小额快速退款，减少升级与拖延。",
    "用户误会": "完善门店与线上信息透明度（价格/规则/份量），主动澄清，避免歧义。",
    "营销问题": "审查宣传话术合规性，规避绝对化用语与夸大承诺，活动规则前置公示。",
}


def suggest(content: str, level: int = 2, response: str = "") -> dict:
    """返回 {root_cause, scope, timeliness, conclusion, actions}。"""
    text = (content or "") + (response or "")
    root = "用户误会"
    for rc, kws in _KW.items():
        if any(k in text for k in kws):
            root = rc
            break
    # 影响范围：高危默认区域，食安默认更大
    scope = "全网" if (level >= 4 and root == "品控食品安全") else ("区域" if level >= 4 else "单店")
    timeliness = "及时" if response else "待评估"
    conclusion = f"经研判，本次舆情根因归类为「{root}」，风险等级 {level} 级，影响范围预估「{scope}」。"
    return {"root_cause": root, "scope": scope, "timeliness": timeliness,
            "conclusion": conclusion, "actions": _ACTIONS.get(root, "")}
