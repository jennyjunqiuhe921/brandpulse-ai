import streamlit as st
from config.settings import BRAND_DISPLAY_NAMES, BRAND_FOCUS
from core.rag_engine import collection_count


def render() -> str:
    with st.sidebar:
        st.title("📊 BrandPulse AI")
        st.markdown("---")
        brand_options = list(BRAND_DISPLAY_NAMES.keys())
        current = st.session_state.get("brand", "heytea")
        idx = brand_options.index(current) if current in brand_options else 0
        selected = st.radio(
            "选择分析品牌",
            brand_options,
            index=idx,
            format_func=lambda k: BRAND_DISPLAY_NAMES[k],
        )
        st.session_state["brand"] = selected
        st.markdown("---")
        st.caption(f"**战略切入点**\n\n{BRAND_FOCUS[selected]}")
        kb_count = collection_count(selected)
        st.metric("知识库文档块", kb_count, help="✅ 就绪" if kb_count > 0 else "⚠️ 请运行 ingest_data.py")
        st.markdown("---")
        st.caption("⚠️ 本工作台仅用于比赛演示，所有输出需人工复核后方可商业使用。")
    return selected
