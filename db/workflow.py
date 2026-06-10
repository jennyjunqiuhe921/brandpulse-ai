"""S1-6 通用工作流引擎 — 全局统一流程状态与流转规则。

所有审批/复核/任务模块共用同一套状态机，保证全模块逻辑一致。
"""
from __future__ import annotations

# 标准状态（PRD 1.7.2）
DRAFT = "草稿"
PENDING = "待处理"
PROCESSING = "处理中"
APPROVED = "已通过"
REJECTED = "已驳回"
ARCHIVED = "已归档"

STATUSES = [DRAFT, PENDING, PROCESSING, APPROVED, REJECTED, ARCHIVED]

# 允许的流转关系
TRANSITIONS = {
    DRAFT: [PENDING, ARCHIVED],
    PENDING: [PROCESSING, REJECTED, ARCHIVED],
    PROCESSING: [APPROVED, REJECTED, PENDING],
    APPROVED: [ARCHIVED],
    REJECTED: [DRAFT, PENDING, ARCHIVED],
    ARCHIVED: [],
}

# 状态对应的展示色（与全局标签组件统一）
STATUS_COLORS = {
    DRAFT: "#9AA0A6",
    PENDING: "#F9A825",
    PROCESSING: "#1E88E5",
    APPROVED: "#2E7D32",
    REJECTED: "#C62828",
    ARCHIVED: "#607D8B",
}


def can_transition(src: str, dst: str) -> bool:
    return dst in TRANSITIONS.get(src, [])


def next_states(src: str) -> list[str]:
    return TRANSITIONS.get(src, [])


def status_badge(status: str) -> str:
    """返回带颜色的 HTML 徽章。"""
    color = STATUS_COLORS.get(status, "#9AA0A6")
    return (f'<span style="background:{color};color:#fff;padding:2px 10px;'
            f'border-radius:10px;font-size:12px;white-space:nowrap;">{status}</span>')
