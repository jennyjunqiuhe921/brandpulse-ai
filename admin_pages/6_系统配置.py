"""S5 2.4 系统全局配置（运营侧）— RBAC 矩阵 / 审批模板 / 存储导出水印。"""
import streamlit as st
import pandas as pd
from utils.admin_sidebar import render
from db.models import ROLE_LABELS

render()

st.markdown('<div class="page-header"><h1>系统全局配置</h1>'
            '<p class="page-desc">RBAC 角色默认权限、审批流默认模板、数据存储/导出/水印全局规则。</p>'
            '</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["👥 角色权限矩阵", "🔀 审批流模板", "💾 存储与水印"])

with tab1:
    st.caption("三大 RBAC 角色默认权限矩阵（平台管理员可配置通用角色模板）。")
    matrix = pd.DataFrame([
        {"功能": "全平台配置/租户/模型/Prompt", "平台管理员": "✅", "企业领导": "❌", "市场人员": "❌"},
        {"功能": "管理驾驶舱/审计/账号", "平台管理员": "❌", "企业领导": "✅", "市场人员": "❌"},
        {"功能": "多级审批/审计台账", "平台管理员": "❌", "企业领导": "✅", "市场人员": "❌"},
        {"功能": "数据采集/文案/GEO/舆情/选品", "平台管理员": "❌", "企业领导": "只读", "市场人员": "✅"},
        {"功能": "竞品情报/合规自查", "平台管理员": "❌", "企业领导": "只读", "市场人员": "✅"},
    ])
    st.dataframe(matrix, use_container_width=True, hide_index=True)

with tab2:
    st.caption("预设审批模板，租户可基于模板自定义流程。")
    st.markdown("- **简易**：单级（市场主管）")
    st.markdown("- **标准**：两级（市场主管 → 品牌负责人）")
    st.markdown("- **严格**：多条件分支（按风险/渠道自动指派，高风险加法务节点）")
    st.selectbox("新租户默认审批模板", ["简易", "标准", "严格"], index=1)
    if st.button("保存默认审批模板", type="primary"):
        st.success("已保存")

with tab3:
    st.caption("全系统数据备份、日志保留、导出格式、水印规则。")
    c1, c2 = st.columns(2)
    c1.number_input("普通业务数据保留（年）", 1, 10, 3)
    c2.selectbox("默认导出格式", ["Markdown", "PDF", "Excel", "Word"])
    st.checkbox("导出文件强制水印（企业名/操作人/时间）", value=True)
    st.checkbox("审计/溯源/竞品/选品/GEO 数据永久不可删", value=True, disabled=True)
    st.number_input("单文件上传上限（MB）", 1, 100, 20)
    if st.button("保存存储配置", type="primary"):
        st.success("已保存")
