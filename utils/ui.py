"""S1 标准页面范式公共组件：顶部导航栏、底部状态栏、看板、数据对比下钻。

被 sidebar.render() 调用，使每个页面自动获得统一顶部栏 + 状态栏。
"""
from __future__ import annotations
import streamlit as st
from datetime import datetime

APP_VERSION = "v1.2-saas"


# ── 顶部导航栏（S1-1）──────────────────────────────────────────────────────────
def render_top_bar(brand_label: str = "") -> None:
    from core.llm_client import DEMO_MODE
    try:
        from db import messages as msg_store
        unread = msg_store.unread_count()
    except Exception:
        unread = 0

    c1, c2, c3, c4 = st.columns([5, 3, 1.2, 1.2])
    with c1:
        st.markdown(
            f'<div style="font-family:var(--font-display,serif);font-size:15px;'
            f'font-weight:700;color:#1C1510;padding-top:6px">智营AI · 一体化营销工作台'
            f'<span style="font-size:12px;color:#9C8E82;font-weight:400">'
            f'　{brand_label}</span></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.text_input("全局搜索", key="_global_search", placeholder="🔍 全局搜索…",
                      label_visibility="collapsed")
    with c3:
        label = f"🔔 {unread}" if unread else "🔔"
        with st.popover(label, use_container_width=True):
            _render_message_popover()
    with c4:
        with st.popover("❓ 帮助", use_container_width=True):
            st.markdown("**帮助中心**")
            st.caption("· 每个模块顶部有操作引导\n\n· 正式内容需人工复核后导出\n\n· "
                       "Demo 模式使用预置数据")
            st.divider()
            # 永远可见的逃生口：决定性清除会话+cookie，不依赖登录态字段是否完整
            if st.button("🚪 退出登录", key="_topbar_logout", use_container_width=True):
                # 决定性登出：前端 JS 直删 cookie + 硬跳转，绕过 cookie 控件的不可靠时序
                from auth.login import do_hard_logout
                do_hard_logout()
    st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)


def _render_message_popover() -> None:
    from db import messages as msg_store
    st.markdown("**消息中心**")
    cats = ["全部", "审批通知", "任务提醒", "风险告警", "竞品异动", "GEO指标异常", "报表推送", "系统公告"]
    cat = st.selectbox("筛选", cats, key="_msg_cat", label_visibility="collapsed")
    rows = msg_store.list_messages(category=None if cat == "全部" else cat)
    if not rows:
        st.caption("暂无消息")
    else:
        for m in rows[:12]:
            icon = {"info": "🔵", "warn": "🟠", "danger": "🔴"}.get(m["level"], "🔵")
            read = "" if m["is_read"] else "**[未读]** "
            st.markdown(f"{icon} {read}{m['title']}  \n<span style='font-size:11px;"
                        f"color:#9C8E82'>{m['category']} · {m['created_at']}</span>",
                        unsafe_allow_html=True)
            if m["body"]:
                st.caption(m["body"])
        if st.button("全部标记已读", key="_msg_read_all", use_container_width=True):
            msg_store.mark_all_read()
            st.rerun()


# ── 底部状态栏（S1-1）──────────────────────────────────────────────────────────
def render_status_bar() -> None:
    from core.llm_client import DEMO_MODE
    try:
        from core.ai_gateway import usage_today, quota_limit
        used, limit = usage_today(), quota_limit()
    except Exception:
        used, limit = 0, 1000
    try:
        from db import context as ctx
        from db.engine import get_session
        from db.models import User
        u = None
        uid = ctx.user_id()
        if uid:
            with get_session() as s:
                row = s.query(User).filter(User.id == uid).first()
                u = (row.name or row.username) if row else None
        operator = u or "—"
    except Exception:
        operator = "—"
    source = "Demo 预置数据" if DEMO_MODE else "实时生成"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    st.markdown(
        f'<div style="position:fixed;left:220px;right:0;bottom:0;z-index:90;padding:5px 18px;'
        f'background:rgba(253,250,245,0.96);border-top:1px solid #DDD4C4;'
        f'backdrop-filter:blur(4px);'
        f'font-size:11px;color:#5C4F42;display:flex;gap:18px;flex-wrap:wrap">'
        f'<span>🤖 AI调用 {used}/{limit}</span>'
        f'<span>📊 数据来源：{source}</span>'
        f'<span>🛡️ 合规：已启用四区块/溯源</span>'
        f'<span>🏷️ 版本：{APP_VERSION}</span>'
        f'<span>👤 操作人：{operator}</span>'
        f'<span>🕐 {ts}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── 看板视图（S1-3）──────────────────────────────────────────────────────────
def kanban_board(tasks: list, status_field: str = "status",
                 title_field: str = "title", columns: list | None = None,
                 meta_fn=None) -> None:
    """通用看板：按状态分列展示任务卡片。

    tasks: dict 列表；columns: 状态列顺序（默认取 workflow 标准状态）。
    meta_fn(task)->str: 卡片副标题渲染函数。
    """
    from db.workflow import STATUSES, STATUS_COLORS
    cols_order = columns or STATUSES
    cols = st.columns(len(cols_order))
    for i, status in enumerate(cols_order):
        with cols[i]:
            color = STATUS_COLORS.get(status, "#9AA0A6")
            items = [t for t in tasks if t.get(status_field) == status]
            st.markdown(
                f'<div style="font-size:12px;font-weight:600;color:#fff;background:{color};'
                f'border-radius:6px;padding:4px 8px;text-align:center;margin-bottom:6px">'
                f'{status} · {len(items)}</div>', unsafe_allow_html=True)
            for t in items:
                meta = meta_fn(t) if meta_fn else _default_card_meta(t)
                st.markdown(
                    f'<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-radius:8px;'
                    f'padding:8px 10px;margin-bottom:6px;font-size:12px">'
                    f'<div style="font-weight:600;color:#1C1510">{t.get(title_field) or t.get("id","")}</div>'
                    f'<div style="font-size:11px;color:#9C8E82;margin-top:2px">{meta}</div>'
                    f'</div>', unsafe_allow_html=True)


def _default_card_meta(t: dict) -> str:
    parts = []
    pr = t.get("priority")
    if pr:
        pic = {"紧急": "🔴", "普通": "🟡", "低": "⚪"}.get(pr, "")
        parts.append(f"{pic}{pr}")
    if t.get("due_date"):
        overdue = _is_overdue(t["due_date"])
        parts.append(("⏰超时 " if overdue else "📅") + t["due_date"])
    tags = t.get("task_tags") or t.get("tags") or []
    if tags:
        parts.append("#" + " #".join(tags[:2]))
    return " · ".join(parts)


def _is_overdue(due: str) -> bool:
    try:
        d = datetime.strptime(due[:10], "%Y-%m-%d")
        return d.date() < datetime.now().date()
    except Exception:
        return False


def priority_tag(priority: str) -> str:
    pic = {"紧急": "🔴", "普通": "🟡", "低": "⚪"}.get(priority, "🟡")
    return f"{pic} {priority}"


# ── 数据对比与下钻（S1-4）────────────────────────────────────────────────────
def compare_mode_selector(key: str = "cmp_mode") -> str:
    """返回当前对比模式：同比 / 环比 / 行业均值。"""
    return st.radio("对比模式", ["环比", "同比", "行业均值对标"],
                    horizontal=True, key=key)


def apply_compare(current: float, mode: str, *, prev: float | None = None,
                  industry_avg: float | None = None) -> dict:
    """计算对比结果，返回 {base, delta, pct, label}。"""
    if mode == "行业均值对标" and industry_avg is not None:
        base = industry_avg
        label = "行业均值"
    else:
        base = prev if prev is not None else current
        label = "上期" if mode == "环比" else "去年同期"
    delta = current - base
    pct = (delta / base * 100) if base else 0.0
    return {"base": base, "delta": delta, "pct": pct, "label": label}
