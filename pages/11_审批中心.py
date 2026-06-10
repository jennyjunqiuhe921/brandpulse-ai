"""S2-1 多级审批中心（企业领导/管理层）。"""
import streamlit as st
from utils.sidebar import render
from auth.login import is_admin
from db import approvals as A
from utils.approval_ui import render_detail

render()

st.markdown('<div class="page-header"><h1>审批中心</h1>'
            '<p class="page-desc">待我审批 / 我已审批 / 我发起的，支持多级分支、驳回评论、版本对比、催办与协作。</p>'
            '</div>', unsafe_allow_html=True)

if not is_admin():
    st.warning("审批中心面向企业领导/管理层。市场人员请使用「我的审批」查看自己发起的单据。")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📥 待我审批", "✅ 我已审批", "📤 我发起的"])


def _render_list(scope: str, *, can_decide: bool):
    reqs = A.list_requests(scope)
    if not reqs:
        st.info("暂无单据。")
        return
    for r in reqs:
        urge = " ⏰催办" if r["urged"] else ""
        with st.expander(f"{r['title']} · {r['biz_type']} · 风险{r['risk_level']}"
                         f" · {r['status']}{urge}", expanded=False):
            render_detail(r, can_decide=can_decide)


with tab1:
    _render_list("todo", can_decide=True)
with tab2:
    _render_list("done", can_decide=False)
with tab3:
    _render_list("mine", can_decide=False)
