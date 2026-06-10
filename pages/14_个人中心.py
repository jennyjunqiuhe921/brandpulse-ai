"""S2-6 个人中心 & 帮助 — 修改资料、密码、消息通知、帮助。"""
import streamlit as st
from utils.sidebar import render
from auth.login import current_user, current_user_id
from auth import users as U
from db.models import ROLE_LABELS

render()

st.markdown('<div class="page-header"><h1>个人中心</h1>'
            '<p class="page-desc">管理个人资料、登录密码、消息通知偏好，并查看帮助。</p>'
            '</div>', unsafe_allow_html=True)

u = current_user() or {}
uid = current_user_id()

tab1, tab2, tab3, tab4 = st.tabs(["👤 个人资料", "🔑 修改密码", "🔔 消息通知", "❓ 帮助"])

with tab1:
    st.text_input("账号", value=u.get("username", ""), disabled=True)
    st.text_input("角色", value=ROLE_LABELS.get(u.get("role", ""), u.get("role", "")), disabled=True)
    name = st.text_input("显示名称", value=u.get("name", ""))
    if st.button("保存资料", type="primary"):
        if U.update_profile(uid, name):
            st.session_state["auth"]["name"] = name
            st.success("资料已更新")
        else:
            st.error("更新失败")

with tab2:
    old = st.text_input("原密码", type="password")
    new = st.text_input("新密码（至少 6 位）", type="password")
    new2 = st.text_input("确认新密码", type="password")
    if st.button("更新密码", type="primary"):
        if new != new2:
            st.error("两次输入的新密码不一致")
        else:
            ok, msg = U.change_own_password(uid, old, new)
            (st.success if ok else st.error)(msg)

with tab3:
    st.caption("选择希望在「消息中心」接收的通知类型（演示：保存在本会话）。")
    prefs = st.session_state.setdefault("_msg_prefs", {
        "审批通知": True, "任务提醒": True, "风险告警": True,
        "竞品异动": True, "GEO指标异常": True, "报表推送": False, "系统公告": True})
    for k in list(prefs.keys()):
        prefs[k] = st.checkbox(k, value=prefs[k], key=f"pref_{k}")
    if st.button("保存通知设置", type="primary"):
        st.success("通知偏好已保存")

with tab4:
    st.markdown("""
**快速上手**
1. 在左侧「品牌管理」维护品牌资料与知识库
2. 「内容工坊 / GEO / 舆情」生成分析，正式内容提交审批
3. 「我的审批」跟踪进度，被驳回可修改重提
4. 「消息中心」集中查看审批、风险、超时提醒

**常见问题**
- *为什么显示 Demo 模式？* 未配置 API Key 时使用预置数据演示。
- *正式内容为何不能直接导出？* 需先通过人工复核/审批，确保合规。
- *数据安全？* 多租户物理隔离，审计日志不可篡改。
""")
    st.caption("如需更多帮助，请联系企业管理员或平台运营。")
