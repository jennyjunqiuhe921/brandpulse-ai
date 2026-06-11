"""S6-1 版本权限矩阵 — 按租户套餐控制功能开关（对齐 PRD 第五部分）。

三档套餐：基础执行版 / 标准管控版 / 企业集团版。
功能键经 has_feature() 判定；页面用 require_feature() 门控。
"""
from __future__ import annotations
import streamlit as st

PLANS = ["基础执行版", "标准管控版", "企业集团版"]

# 各功能键说明
FEATURE_LABELS = {
    "multi_approval": "多级审批",
    "full_audit": "完整审计台账",
    "multi_org": "多组织管控/监管级台账",
    "full_geo": "完整 GEO + 复测对比评估",
    "image_video": "生图 / 生视频",
    "sentiment_ticket": "舆情工单处置",
    "selection_full": "全维度选品",
    "competitor": "竞品情报仓库",
    "batch_tasks": "批量任务 / 危机舆情 / 高阶报表",
}

# 套餐 → 功能集合（递进包含）
_BASE = set()  # 基础版默认具备基础采集/文案/简易GEO/基础舆情/基础选品（不在此门控）
_STANDARD = {
    "multi_approval", "full_audit", "full_geo", "image_video",
    "sentiment_ticket", "selection_full", "competitor",
}
_GROUP = _STANDARD | {"multi_org", "batch_tasks"}

PLAN_FEATURES = {
    "基础执行版": _BASE,
    "标准管控版": _STANDARD,
    "企业集团版": _GROUP,
}


def current_plan() -> str:
    """当前登录租户的套餐（默认企业集团版兜底，便于演示）。"""
    try:
        from db import context as ctx
        from db.engine import get_session
        from db.models import Tenant
        with get_session() as s:
            t = s.query(Tenant).filter(Tenant.id == ctx.tenant_id()).first()
            return t.plan if t and t.plan in PLANS else "企业集团版"
    except Exception:
        return "企业集团版"


def has_feature(key: str, plan: str | None = None) -> bool:
    p = plan or current_plan()
    return key in PLAN_FEATURES.get(p, set())


def require_feature(key: str) -> None:
    """页面顶部门控：无权限则提示升级并停止渲染。"""
    if not has_feature(key):
        label = FEATURE_LABELS.get(key, key)
        st.warning(f"🔒 当前套餐「{current_plan()}」未包含「{label}」功能。"
                   f"请联系平台运营升级到更高版本以解锁。")
        st.stop()


def matrix_dataframe():
    """权限矩阵表（用于展示）。"""
    import pandas as pd
    rows = []
    for key, label in FEATURE_LABELS.items():
        rows.append({
            "功能": label,
            "基础执行版": "✅" if has_feature(key, "基础执行版") else "—",
            "标准管控版": "✅" if has_feature(key, "标准管控版") else "—",
            "企业集团版": "✅" if has_feature(key, "企业集团版") else "—",
        })
    return pd.DataFrame(rows)
