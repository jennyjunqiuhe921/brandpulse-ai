"""S6-2 冷启动向导（企业管理员首次登录）— 5 步引导 + 行业模板一键导入。"""
import streamlit as st
from utils.sidebar import render
from auth.login import is_admin, current_tenant_id

render()

st.markdown('<div class="page-header"><h1>冷启动向导</h1>'
            '<p class="page-desc">5 步完成企业初始化：导入行业模板、配置品牌、学习调性、选择审批流、生成示例任务。</p>'
            '</div>', unsafe_allow_html=True)

if not is_admin():
    st.warning("冷启动向导面向企业管理员。")
    st.stop()

# 行业模板市场（PRD 1.8.1）
INDUSTRY_PACKS = {
    "奶茶/新茶饮": {"词库": "禁止减脂/养生/药用/零热量等违规表述", "GEO": "C端+B端双维度提问库",
                    "舆情": "五级舆情规则", "选品": "新式茶饮选品配置"},
    "美妆护肤": {"词库": "功效禁用规则 + 广告法合规词", "GEO": "美妆高频提问库",
                 "舆情": "美妆敏感词", "选品": "美妆护肤选品配置"},
    "传统餐饮连锁": {"词库": "食安合规话术", "GEO": "本地化GEO词 + 点评采集",
                     "舆情": "食安舆情话术", "选品": "餐饮选品模板"},
}

STEPS = ["选择行业", "品牌信息", "学习调性", "审批流程", "示例任务"]
step = st.session_state.get("_wiz_step", 0)

# 进度条
st.progress((step) / (len(STEPS) - 1) if len(STEPS) > 1 else 0)
st.markdown("　".join(f"**{i+1}. {s}**" if i == step else f"{i+1}. {s}"
                      for i, s in enumerate(STEPS)))
st.divider()

if step == 0:
    st.markdown("### 第 1 步：选择所属行业，一键导入全套模板")
    ind = st.selectbox("行业", list(INDUSTRY_PACKS.keys()))
    pack = INDUSTRY_PACKS[ind]
    st.markdown("将自动加载：")
    for k, v in pack.items():
        st.markdown(f"- **{k}**：{v}")
    if st.button("导入并下一步", type="primary"):
        st.session_state["_wiz_industry"] = ind
        st.session_state["_wiz_step"] = 1
        st.rerun()

elif step == 1:
    st.markdown("### 第 2 步：填写品牌信息（自动生成品牌词库 / 选品基础词 / GEO 关键词）")
    st.text_input("品牌名称", key="_wiz_brand")
    st.text_area("核心产品线", key="_wiz_products", placeholder="如：鲜果茶、轻乳茶、气泡水")
    c1, c2 = st.columns(2)
    if c1.button("上一步"):
        st.session_state["_wiz_step"] = 0; st.rerun()
    if c2.button("下一步", type="primary"):
        st.session_state["_wiz_step"] = 2; st.rerun()

elif step == 2:
    st.markdown("### 第 3 步：上传品牌 VI / 优质历史文案，AI 学习品牌调性")
    st.file_uploader("上传文件（VI 手册 / 历史文案，可多选）", accept_multiple_files=True)
    st.caption("演示环境不实际训练，仅展示流程。正式版会让 AI 学习品牌调性。")
    c1, c2 = st.columns(2)
    if c1.button("上一步"):
        st.session_state["_wiz_step"] = 1; st.rerun()
    if c2.button("下一步", type="primary"):
        st.session_state["_wiz_step"] = 3; st.rerun()

elif step == 3:
    st.markdown("### 第 4 步：选择默认审批流程")
    st.radio("审批流程", ["简易（单级·市场主管）", "标准（两级·主管→负责人）",
                          "严格（多条件分支·高风险加法务）"], index=1, key="_wiz_flow")
    c1, c2 = st.columns(2)
    if c1.button("上一步"):
        st.session_state["_wiz_step"] = 2; st.rerun()
    if c2.button("下一步", type="primary"):
        st.session_state["_wiz_step"] = 4; st.rerun()

elif step == 4:
    st.markdown("### 第 5 步：生成示例任务，开始体验")
    st.success("即将创建示例任务：品牌分析 · 产品分析 · GEO 诊断 · 基础选品任务")
    st.markdown(f"- 行业模板：**{st.session_state.get('_wiz_industry','—')}**")
    st.markdown(f"- 品牌：**{st.session_state.get('_wiz_brand','—')}**")
    st.markdown(f"- 审批流：**{st.session_state.get('_wiz_flow','标准')}**")
    c1, c2 = st.columns(2)
    if c1.button("上一步"):
        st.session_state["_wiz_step"] = 3; st.rerun()
    if c2.button("完成并进入系统", type="primary"):
        st.session_state["_wiz_done"] = True
        st.session_state["_wiz_step"] = 0
        st.balloons()
        st.success("初始化完成！已在首页生成新手任务卡片，可前往各模块开始实操。")
        st.page_link("pages/1_工作台.py", label="🏠 进入工作台", icon="🏠")
