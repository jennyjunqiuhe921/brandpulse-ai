"""S2-1 审批中心共享 UI 组件：单据卡片、详情(步骤/Diff/评论/决策)。"""
from __future__ import annotations
import streamlit as st
from db import approvals as A

_RISK_COLOR = {"低": "#3D7A5A", "中": "#B5860D", "高": "#C4391A"}
_STATUS_COLOR = {"审批中": "#2B6CB0", "已通过": "#3D7A5A", "已驳回": "#C4391A", "已撤回": "#9C8E82"}
_PRI_ICON = {"紧急": "🔴", "普通": "🟡", "低": "⚪"}


def status_chip(status: str) -> str:
    c = _STATUS_COLOR.get(status, "#9C8E82")
    return (f'<span style="background:{c};color:#fff;padding:2px 10px;border-radius:10px;'
            f'font-size:12px">{status}</span>')


def render_steps(req: dict) -> None:
    st.markdown("**审批链**")
    parts = []
    for s in req["steps"]:
        if s["status"] == "已通过":
            ic = "✅"
        elif s["status"] == "已驳回":
            ic = "❌"
        elif s["step_no"] == req["current_step"] and req["status"] == "审批中":
            ic = "⏳"
        else:
            ic = "⚪"
        parts.append(f"{ic} {s['step_no']}. {s['approver_label']}")
    st.markdown("　→　".join(parts))
    for s in req["steps"]:
        if s["comment"]:
            st.caption(f"〔{s['approver_label']}〕意见：{s['comment']}")
            if s["quote"]:
                st.markdown(f"> 针对原文：{s['quote']}")


def render_detail(req: dict, *, can_decide: bool = False, can_resubmit: bool = False) -> None:
    risk_c = _RISK_COLOR.get(req["risk_level"], "#9C8E82")
    st.markdown(
        f"### {req['title']}　{status_chip(req['status'])}", unsafe_allow_html=True)
    st.markdown(
        f"{_PRI_ICON.get(req['priority'],'🟡')} {req['priority']}　·　"
        f"<span style='color:{risk_c}'>风险：{req['risk_level']}</span>　·　"
        f"类型：{req['biz_type']}　·　品牌：{req['brand'] or '—'}　·　"
        f"发起人：{req['owner_name']}　·　版本 v{req['version']}　·　{req['created_at']}",
        unsafe_allow_html=True)

    render_steps(req)
    st.divider()

    st.markdown("**送审内容**")
    st.markdown(
        f'<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-radius:8px;'
        f'padding:12px 16px;white-space:pre-wrap;font-size:13px">{req["content"]}</div>',
        unsafe_allow_html=True)

    # 版本 Diff
    if req["history"]:
        with st.expander(f"📝 版本对比（共 {req['version']} 版）"):
            prev = req["history"][-1]
            st.caption(f"上一版 v{prev['version']} → 当前 v{req['version']}（绿=新增 红=删除）")
            st.markdown(
                f'<div style="background:#fff;border:1px solid #DDD4C4;border-radius:8px;'
                f'padding:12px;font-size:13px">{A.diff_versions(prev["content"], req["content"])}</div>',
                unsafe_allow_html=True)

    # 协作评论区
    with st.expander("💬 协作评论区"):
        for c in A.list_comments(req["id"]):
            st.markdown(f"**{c['username']}** · <span style='font-size:11px;color:#9C8E82'>"
                        f"{c['created_at']}</span>", unsafe_allow_html=True)
            st.markdown(c["body"])
        nc = st.text_input("写评论…", key=f"cmt_{req['id']}")
        if st.button("发表评论", key=f"cmtbtn_{req['id']}"):
            if A.add_comment(req["id"], nc):
                st.rerun()

    # 审批决策（管理层）
    if can_decide and req["status"] == "审批中":
        st.divider()
        st.markdown("**审批决策**")
        quote = st.text_input("（可选）驳回时高亮的原文段落", key=f"q_{req['id']}")
        comment = st.text_area("审批意见", key=f"c_{req['id']}",
                               placeholder="可选用意见模板：内容合规，同意 / 存在风险，请修改…")
        cc1, cc2, _ = st.columns([1, 1, 3])
        with cc1:
            if st.button("✅ 通过", key=f"pass_{req['id']}", type="primary"):
                if A.decide(req["id"], True, comment, quote):
                    st.toast("已通过")
                    st.rerun()
        with cc2:
            if st.button("❌ 驳回", key=f"rej_{req['id']}"):
                if A.decide(req["id"], False, comment or "请修改后重提", quote):
                    st.toast("已驳回")
                    st.rerun()

    # 修改重提（发起人）
    if can_resubmit and req["status"] == "已驳回":
        st.divider()
        st.markdown("**修改后重新提交**")
        new = st.text_area("修改内容", value=req["content"], key=f"re_{req['id']}", height=160)
        if st.button("🔁 修改重提", key=f"rebtn_{req['id']}", type="primary"):
            if A.resubmit(req["id"], new):
                st.toast("已重新提交审批")
                st.rerun()
