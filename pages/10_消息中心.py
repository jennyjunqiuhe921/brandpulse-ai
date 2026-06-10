"""S1-2 全局消息中心页面。"""
import streamlit as st
from utils.sidebar import render
from db import messages as msg_store
from db.models import MSG_TYPES

render()

st.markdown('<div class="page-header"><h1>消息中心</h1>'
            '<p class="page-desc">审批通知、任务提醒、风险告警、竞品异动、GEO异常、报表推送、系统公告统一汇聚于此。</p>'
            '</div>', unsafe_allow_html=True)

# ── 筛选 + 操作 ──────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([3, 2, 2])
with c1:
    cat = st.selectbox("分类筛选", ["全部"] + MSG_TYPES, key="msgpage_cat")
with c2:
    only_unread = st.checkbox("仅看未读", key="msgpage_unread")
with c3:
    st.markdown('<div style="height:26px"></div>', unsafe_allow_html=True)
    if st.button("全部标记已读", use_container_width=True):
        n = msg_store.mark_all_read()
        st.toast(f"已标记 {n} 条为已读")
        st.rerun()

rows = msg_store.list_messages(
    category=None if cat == "全部" else cat, only_unread=only_unread)

st.caption(f"共 {len(rows)} 条消息　·　未读 {msg_store.unread_count()} 条")
st.divider()

if not rows:
    st.info("暂无消息。系统在审批、风险、超时任务等事件发生时会自动推送提醒。")
else:
    _ICON = {"info": "🔵", "warn": "🟠", "danger": "🔴"}
    for m in rows:
        icon = _ICON.get(m["level"], "🔵")
        unread_mark = " 🆕" if not m["is_read"] else ""
        with st.container():
            cc1, cc2 = st.columns([8, 1])
            with cc1:
                st.markdown(
                    f"{icon} **{m['title']}**{unread_mark}　"
                    f"<span style='font-size:11px;color:#9C8E82'>"
                    f"〔{m['category']}〕 {m['created_at']}</span>",
                    unsafe_allow_html=True)
                if m["body"]:
                    st.caption(m["body"])
            with cc2:
                if not m["is_read"]:
                    if st.button("已读", key=f"read_{m['id']}"):
                        msg_store.mark_read(m["id"])
                        st.rerun()
        st.markdown('<hr style="margin:8px 0">', unsafe_allow_html=True)
