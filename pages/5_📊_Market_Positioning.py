import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.market_positioning as mp_mod
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="市场定位 — BrandPulse AI", page_icon="📊", layout="wide")
brand = render_sidebar()

st.title("📊 市场定位分析")
st.caption("STP 框架 + SWOT 分析 + 差异化定位建议")

brand_name = BRAND_DISPLAY_NAMES[brand]

st.info(
    f"**当前品牌**：{brand_name}\n\n"
    "本模块基于知识库内容，输出完整的 STP（市场细分/目标市场/定位）和 "
    "SWOT（优势/劣势/机会/威胁）分析报告，并给出差异化策略建议。"
)

col1, col2 = st.columns([3, 1])
with col2:
    run_refcheck = st.checkbox("开启 RefCheck", value=False)

if st.button("🚀 运行市场定位分析", type="primary"):
    with st.spinner("正在生成市场定位分析...（约 20-35 秒）"):
        try:
            result = mp_mod.run(brand, run_refcheck=run_refcheck)
            st.session_state["mp_result"] = result
        except Exception as e:
            st.error(f"分析失败：{e}")

if "mp_result" in st.session_state:
    res = st.session_state["mp_result"]
    st.markdown("---")

    output = res["output"]

    # Try to split STP and SWOT into side-by-side columns
    if "## SWOT" in output:
        stp_part, swot_part = output.split("## SWOT", 1)
        col_stp, col_swot = st.columns(2)
        with col_stp:
            st.markdown(stp_part)
        with col_swot:
            st.markdown("## SWOT" + swot_part)
    else:
        st.markdown(output)

    if res.get("refcheck"):
        st.markdown("---")
        st.subheader("🔎 RefCheck 合规标注")
        st.markdown(res["refcheck"])

    with st.expander("📚 知识库引用来源", expanded=False):
        for i, c in enumerate(res["chunks"], 1):
            st.markdown(f"**[{i}] 来源：`{c['source']}`**")
            st.text(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])
