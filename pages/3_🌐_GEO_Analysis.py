import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.geo_analysis as geo_mod
from prompts.geo_analysis_prompt import GEO_QUESTIONS

st.set_page_config(page_title="GEO分析 — BrandPulse AI", page_icon="🌐", layout="wide")
brand = render_sidebar()

st.title("🌐 GEO / AI 搜索可见度分析")
st.caption("任务卡2：分析品牌在 AI 搜索场景中的可见度、准确性与内容补强建议")

st.info(
    "**GEO（Generative Engine Optimization）**：模拟用户向 AI 搜索提问，"
    "分析品牌被提及的频率、信息准确性与竞品差距，并给出合规内容补强建议。"
    "\n\n⚠️ 本分析坚持「真实、准确、可信」原则，严禁用于刷屏、灌水或虚假评价。"
)

st.subheader("测试问题设置")
default_questions = GEO_QUESTIONS.get(brand, GEO_QUESTIONS["heytea"])

with st.expander("✏️ 查看/编辑测试问题（可修改）", expanded=True):
    questions_text = st.text_area(
        "每行一个问题（至少8个）",
        value="\n".join(default_questions),
        height=200,
    )

questions = [q.strip() for q in questions_text.strip().split("\n") if q.strip()]
st.caption(f"当前共 {len(questions)} 个测试问题")

if len(questions) < 8:
    st.warning("建议至少设置 8 个测试问题以获得更全面的分析")

if st.button("🚀 运行 GEO 分析", type="primary"):
    with st.spinner("正在进行 GEO 可见度分析...（约 30-60 秒）"):
        try:
            result = geo_mod.run(brand, custom_questions=questions)
            st.session_state["geo_result"] = result
        except Exception as e:
            st.error(f"分析失败：{e}")

if "geo_result" in st.session_state:
    res = st.session_state["geo_result"]
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("测试问题数量", len(res["questions"]))
    with col2:
        st.metric("知识库引用块", len(res["chunks"]))
    with col3:
        st.metric("分析状态", "✅ 完成")

    st.markdown("---")
    st.markdown(res["output"])

    st.markdown("---")
    with st.expander("📚 知识库引用来源", expanded=False):
        for i, c in enumerate(res["chunks"], 1):
            st.markdown(f"**[{i}] 来源：`{c['source']}`**")
            st.text(c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"])

    st.info(
        "💡 **下一步**：将内容补强建议中的具体措施交由品牌方核实后，"
        "在官网/FAQ/媒体稿中补充对应内容，不得用于虚假宣传。"
    )
