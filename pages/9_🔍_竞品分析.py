"""BrandPulse AI — 竞品对标分析（D模块）"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
from config.settings import BRAND_DISPLAY_NAMES
import modules.competitor_analysis as comp_mod

st.set_page_config(page_title="竞品分析 — BrandPulse AI", page_icon="🔍", layout="wide")
brand = render_sidebar()

st.title("🔍 竞品对标分析")
st.caption("D模块：品牌定位差异 · 产品卖点对比 · 内容策略对比 · AI可见度差距")

st.info(
    "**输入**：主品牌（侧边栏选定） + 指定竞品\n"
    "**输出**：品牌定位对比表、产品卖点对比、内容策略差异、GEO可见度差距、策略建议\n\n"
    "⚠️ 分析基于公开信息，区分官方事实（✅）与AI推断（⚠️）。商业决策前需人工复核。"
)

competitors = {k: v for k, v in BRAND_DISPLAY_NAMES.items() if k != brand}
comp_keys = list(competitors.keys())

col_brand, col_vs, col_comp = st.columns([2, 0.3, 2])
with col_brand:
    st.markdown(f"**主品牌**")
    st.markdown(f"### {BRAND_DISPLAY_NAMES[brand]}")
with col_vs:
    st.markdown("<div style='text-align:center;padding-top:28px;font-size:20px;color:#888'>vs</div>", unsafe_allow_html=True)
with col_comp:
    st.markdown("**选择竞品**")
    competitor = st.selectbox(
        "竞品",
        comp_keys,
        format_func=lambda k: BRAND_DISPLAY_NAMES[k],
        label_visibility="collapsed",
    )

st.markdown("")

if st.button("🚀 运行竞品对标分析", type="primary"):
    with st.spinner(f"正在对标分析 {BRAND_DISPLAY_NAMES[brand]} vs {BRAND_DISPLAY_NAMES[competitor]}...（约 20-35 秒）"):
        try:
            result = comp_mod.run(brand, competitor)
            st.session_state["comp_result"] = result
            st.session_state["comp_pair"] = (brand, competitor)
        except Exception as e:
            st.error(f"分析失败：{e}")

if "comp_result" in st.session_state:
    pair = st.session_state.get("comp_pair", (None, None))
    if pair != (brand, competitor):
        st.info("检测到品牌或竞品已更换，请重新运行分析")
    else:
        res = st.session_state["comp_result"]

        if res.get("demo_mode"):
            st.caption("💡 演示模式 · 当前为预置分析样本 · 接入 API Key 后将动态生成")

        st.markdown("---")
        st.markdown(res["output"])

        if res.get("chunks"):
            with st.expander("📚 知识库引用来源", expanded=False):
                for i, c in enumerate(res["chunks"], 1):
                    st.markdown(f"**[{i}] 来源：`{c['source']}`**")
                    st.text(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])

        st.markdown("---")
        send_col, _ = st.columns([2, 5])
        with send_col:
            if st.button("📤 送往合规审查", use_container_width=True):
                st.session_state["content_for_compliance"] = res["output"]
                st.success("✅ 已送往「合规审查」模块")
