"""S2-2 我的审批（市场执行层）— 查看我发起的单据、处理驳回重提、协作评论。"""
import streamlit as st
from utils.sidebar import render
from db import approvals as A
from utils.approval_ui import render_detail

render()

st.markdown('<div class="page-header"><h1>我的审批</h1>'
            '<p class="page-desc">查看我发起的审批单据，跟踪进度；被驳回时可修改后一键重提。</p>'
            '</div>', unsafe_allow_html=True)

# ── 发起新审批 ───────────────────────────────────────────────────────────────
with st.expander("➕ 发起新审批"):
    with st.form("new_approval"):
        title = st.text_input("标题", placeholder="如：多肉葡萄夏季推广文案（小红书）")
        c1, c2, c3 = st.columns(3)
        biz_type = c1.selectbox("类型", ["文案", "GEO方案", "舆情处置", "选品方案", "品牌方案"])
        risk = c2.selectbox("风险等级", ["低", "中", "高"])
        priority = c3.selectbox("优先级", ["普通", "紧急", "低"])
        content = st.text_area("送审内容", height=140)
        st.caption("审批链将根据风险/优先级自动路由：" +
                   " → ".join(A.route_preview(risk, priority)))
        if st.form_submit_button("提交审批", type="primary"):
            if title.strip() and content.strip():
                A.submit(biz_type, "", title, content, risk_level=risk, priority=priority)
                st.success("已提交审批")
                st.rerun()
            else:
                st.warning("请填写标题与送审内容")

reqs = A.list_requests("mine")

# 概览
c1, c2, c3, c4 = st.columns(4)
c1.metric("全部", len(reqs))
c2.metric("审批中", sum(1 for r in reqs if r["status"] == "审批中"))
c3.metric("已通过", sum(1 for r in reqs if r["status"] == "已通过"))
c4.metric("已驳回", sum(1 for r in reqs if r["status"] == "已驳回"))
st.divider()

if not reqs:
    st.info("你还没有发起任何审批。在内容工坊 / GEO / 舆情中生成正式内容后可提交审批。")
else:
    flt = st.radio("筛选", ["全部", "审批中", "已通过", "已驳回"], horizontal=True)
    for r in reqs:
        if flt != "全部" and r["status"] != flt:
            continue
        urge = ""
        with st.expander(f"{r['title']} · {r['status']} · v{r['version']} · {r['created_at']}"):
            render_detail(r, can_decide=False, can_resubmit=True)
            if r["status"] == "审批中":
                cc1, cc2, _ = st.columns([1, 1, 3])
                with cc1:
                    if st.button("⏰ 催办", key=f"urge_{r['id']}"):
                        A.urge(r["id"]); st.toast("已催办审批人"); st.rerun()
                with cc2:
                    if st.button("↩️ 撤回", key=f"wd_{r['id']}"):
                        A.withdraw(r["id"]); st.toast("已撤回"); st.rerun()
