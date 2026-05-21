import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.compliance_checker as compliance_mod
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="合规审查 — BrandPulse AI", page_icon="🛡️", layout="wide")
brand = render_sidebar()

st.title("🛡️ 合规审查哨所")
st.caption("自动检测绝对化用语、虚假宣传、竞品贬低、品牌调性偏差等风险")

st.info(
    "**输入**：任何 AI 生成的文案、分析结论或策略方案\n"
    "**输出**：逐条风险标注（🔴高/🟡中/🟢低）+ 修改建议\n\n"
    "⚠️ 本模块基于AI分析，结果供参考。正式发布前须由品牌授权人员进行人工最终复核。"
)

# Pre-populate from content studio if available
prefill = st.session_state.get("content_for_compliance", "")

if prefill:
    st.success("✅ 已从「内容生成工厂」导入内容，可直接运行审查")

content_input = st.text_area(
    "待审查内容",
    value=prefill,
    placeholder="粘贴需要合规审查的文案、分析报告、推广策略等内容...",
    height=250,
)

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("清除导入内容", type="secondary"):
        st.session_state["content_for_compliance"] = ""
        st.rerun()

EXAMPLE_RISKY = """喜茶是新式茶饮行业第一品牌，产品口味最好，喝了我们的茶你一定不会去喝其他家！我们的芝士是全国最顶级的食材，健康无添加，喝了包你变年轻。竞争对手的产品根本比不上我们。"""

if st.button("📋 加载示例（含风险内容）"):
    st.session_state["example_loaded"] = EXAMPLE_RISKY
    st.rerun()

if "example_loaded" in st.session_state:
    content_input = st.session_state["example_loaded"]

if st.button("🚀 运行合规审查", type="primary", disabled=not content_input.strip()):
    with st.spinner("正在进行合规审查...（约 15-25 秒）"):
        try:
            result = compliance_mod.run(content_input, brand)
            st.session_state["compliance_result"] = result
        except Exception as e:
            st.error(f"审查失败：{e}")

if "compliance_result" in st.session_state:
    res = st.session_state["compliance_result"]
    st.markdown("---")
    st.markdown(res["output"])

    with st.expander("📚 品牌事实核查依据（知识库）", expanded=False):
        for i, c in enumerate(res["chunks"], 1):
            st.markdown(f"**[{i}] 来源：`{c['source']}`**")
            st.text(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])

    st.markdown("---")
    st.caption(
        "**免责声明**：本审查由 AI 辅助完成，所有输出仅供参考，"
        "不构成法律意见。正式发布前请咨询品牌合规部门或法律顾问。"
    )
