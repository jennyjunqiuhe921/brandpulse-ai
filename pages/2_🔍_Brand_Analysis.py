import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
from utils.followup_chat import render as render_chat
import modules.brand_analysis as brand_mod
import modules.product_analysis as product_mod

st.set_page_config(page_title="品牌 & 产品分析 — BrandPulse AI", page_icon="🔍", layout="wide")
brand = render_sidebar()

st.title("🔍 品牌 & 产品分析")
st.caption("任务卡1（必选）：品牌分析 + 产品分析")

tab1, tab2 = st.tabs(["🏷️ 品牌分析", "📦 产品分析"])

# ── Tab 1: Brand Analysis ──────────────────────────────────────────────────────
with tab1:
    st.subheader("品牌深度分析")
    st.info("输入：品牌官方公开资料（知识库）\n输出：定位、关键词、调性、目标客群、优势、一致性评估、风险提示")

    col1, col2 = st.columns([3, 1])
    with col2:
        run_refcheck = st.checkbox("开启 RefCheck（合规标注）", value=False, key="brand_rc")

    if st.button("🚀 运行品牌分析", type="primary", key="run_brand"):
        with st.spinner("正在分析品牌知识库...（约 15-30 秒）"):
            try:
                result = brand_mod.run(brand, run_refcheck=run_refcheck)
                st.session_state["brand_result"] = result
            except Exception as e:
                st.error(f"分析失败：{e}")

    if "brand_result" in st.session_state:
        res = st.session_state["brand_result"]
        st.markdown("---")
        st.markdown(res["output"])

        if res.get("chunks"):
            st.markdown("**📎 主要依据来源**（知识库）")
            for c in res["chunks"][:2]:
                st.caption(f"来源：`{c['source']}` · {c['text'][:80]}...")

        if res.get("refcheck"):
            st.markdown("---")
            st.subheader("🔎 RefCheck 合规标注")
            st.markdown(res["refcheck"])

        with st.expander("📚 完整知识库引用来源", expanded=False):
            for i, c in enumerate(res["chunks"], 1):
                st.markdown(f"**[{i}] 来源：`{c['source']}`**")
                st.text(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])

        render_chat(brand, res["output"], key=f"brand_{brand}")

# ── Tab 2: Product Analysis ────────────────────────────────────────────────────
with tab2:
    st.subheader("产品深度分析")
    st.info("输入：产品名称 + 知识库\n输出：功能拆解、痛点匹配、核心卖点、使用场景、价值主张")

    from config.settings import BRAND_DISPLAY_NAMES
    PRODUCT_SUGGESTIONS = {
        "heytea": ["多肉葡萄", "芝士莓莓", "波波冰", "满杯红柚", "纯茶系列"],
        "nayuki": ["霸气玉油柑", "霸气芝士草莓", "软欧包套餐", "鸭屎香宝藏茶"],
        "chapanda": ["杨枝甘露", "芋泥波波奶茶", "四季青茶", "黑提鲜果茶"],
    }

    col_a, col_b = st.columns([2, 1])
    with col_a:
        suggestions = PRODUCT_SUGGESTIONS.get(brand, [])
        product_name = st.text_input(
            "产品名称",
            value=suggestions[0] if suggestions else "",
            placeholder="输入要分析的产品名称",
        )
    with col_b:
        if suggestions:
            st.caption("快速选择：")
            for s in suggestions[:3]:
                if st.button(s, key=f"prod_{s}"):
                    st.session_state["selected_product"] = s
                    st.rerun()

    if "selected_product" in st.session_state:
        product_name = st.session_state["selected_product"]

    run_rc2 = st.checkbox("开启 RefCheck", value=False, key="prod_rc")

    if st.button("🚀 运行产品分析", type="primary", key="run_product") and product_name:
        with st.spinner(f"正在分析产品「{product_name}」..."):
            try:
                result = product_mod.run(brand, product_name, run_refcheck=run_rc2)
                st.session_state["product_result"] = result
            except Exception as e:
                st.error(f"分析失败：{e}")

    if "product_result" in st.session_state:
        res = st.session_state["product_result"]
        st.markdown("---")
        st.markdown(res["output"])

        if res.get("chunks"):
            st.markdown("**📎 主要依据来源**（知识库）")
            for c in res["chunks"][:2]:
                st.caption(f"来源：`{c['source']}` · {c['text'][:80]}...")

        if res.get("refcheck"):
            st.markdown("---")
            st.subheader("🔎 RefCheck 合规标注")
            st.markdown(res["refcheck"])

        with st.expander("📚 完整知识库引用来源", expanded=False):
            for i, c in enumerate(res["chunks"], 1):
                st.markdown(f"**[{i}] 来源：`{c['source']}`**")
                st.text(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])

        render_chat(brand, res["output"], key=f"product_{brand}")
