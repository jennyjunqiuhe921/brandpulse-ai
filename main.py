"""BrandPulse AI — Streamlit entry point."""
import streamlit as st
from config.settings import BRAND_DISPLAY_NAMES, BRAND_FOCUS
from core.rag_engine import collection_count

st.set_page_config(
    page_title="BrandPulse AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Brand selector (persisted in session state) ────────────────────────────────
st.sidebar.title("📊 BrandPulse AI")
st.sidebar.markdown("---")

brand_options = list(BRAND_DISPLAY_NAMES.keys())
selected = st.sidebar.radio(
    "选择分析品牌",
    brand_options,
    format_func=lambda k: BRAND_DISPLAY_NAMES[k],
)
st.session_state["brand"] = selected

st.sidebar.markdown("---")
st.sidebar.caption(f"**战略切入点**\n{BRAND_FOCUS[selected]}")

kb_count = collection_count(selected)
status = "✅ 已就绪" if kb_count > 0 else "⚠️ 知识库为空，请先运行 ingest_data.py"
st.sidebar.metric("知识库文档块", kb_count, help=status)
st.sidebar.markdown("---")
st.sidebar.caption("导航 → 左侧页面列表选择模块")

# ── Home page ──────────────────────────────────────────────────────────────────
st.title(f"🍵 BrandPulse AI — {BRAND_DISPLAY_NAMES[selected]}")
st.markdown(
    """
**AI 品牌与市场增长工作台** · 24h Hackathon MVP

| 模块 | 页面 |
|------|------|
| 品牌 & 产品分析 | 2_Brand_Analysis |
| GEO / AI 搜索可见度 | 3_GEO_Analysis |
| 内容生成工厂 | 4_Content_Studio |
| 市场定位 (STP/SWOT) | 5_Market_Positioning |
| AI 舆情分析 | 6_Sentiment_Analysis |
| 合规审查哨所 | 7_Compliance_Guard |
"""
)

st.info(
    "⚠️ 免责声明：本作品仅用于比赛演示。相关企业分析基于公开信息和 AI 工具辅助生成，"
    "不代表对企业经营、产品质量、市场表现或声誉状况的事实认定。"
    "所有输出均需在真实商业使用前由企业授权人员进行复核。",
    icon="⚠️",
)
