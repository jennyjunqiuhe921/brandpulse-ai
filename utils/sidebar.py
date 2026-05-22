import streamlit as st
from config.settings import BRAND_DISPLAY_NAMES, BRAND_FOCUS
from core.rag_engine import collection_count
from core.llm_client import DEMO_MODE


def render() -> str:
    with st.sidebar:
        st.title("📊 BrandPulse AI")
        st.markdown("---")
        brand_options = list(BRAND_DISPLAY_NAMES.keys())
        if "brand" not in st.session_state:
            st.session_state["brand"] = "heytea"
        prev_brand = st.session_state.get("_active_brand", st.session_state["brand"])
        selected = st.radio(
            "选择分析品牌",
            brand_options,
            key="brand",
            format_func=lambda k: BRAND_DISPLAY_NAMES[k],
        )
        if prev_brand != selected:
            for k in list(st.session_state.keys()):
                if k.endswith("_result"):
                    del st.session_state[k]
        st.session_state["_active_brand"] = selected
        st.markdown("---")
        st.caption(f"**战略切入点**\n\n{BRAND_FOCUS[selected]}")
        kb_count = collection_count(selected)
        st.metric("知识库文档块", kb_count, help="✅ 就绪" if kb_count > 0 else "⚠️ 请运行 ingest_data.py")
        st.markdown("---")
        if DEMO_MODE:
            st.warning("💡 **演示模式** · 无 API Key\n\n当前返回预置样本，接入 Claude API Key 后将动态生成", icon=None)
        else:
            st.success("🟢 **API 已连接** · 动态生成模式")
        st.caption("⚠️ 本工作台仅用于比赛演示，所有输出需人工复核后方可商业使用。")
    return selected
