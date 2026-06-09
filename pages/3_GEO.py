import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.geo_analysis as geo_mod
from utils.result_banner import maybe_show_banner
from prompts.geo_analysis_prompt import get_geo_questions

st.set_page_config(page_title="GEO分析 — PinSight AI", page_icon="🌐", layout="wide")
brand = render_sidebar()

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">GEO 分析</h1>
  <p class="page-desc">模拟真实用户向 AI 搜索提问，评估品牌在 AI 回答中的可见度与内容补强方向</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-left:3px solid #C4522A;border-radius:6px;padding:12px 16px;margin:0 0 18px;font-size:13px;color:#5C4F42;line-height:1.7">
  <strong style="color:#1A1A1A">什么是 GEO？</strong> 模拟真实用户向 ChatGPT、Perplexity 等 AI 引擎提问，分析品牌是否被准确提及、与竞品的差距，并给出合规的内容补强建议。<br>
  ⚠️ 本分析坚持「真实、准确、可信」原则，<strong>严禁</strong>用于刷屏、灌水或虚假评价。
</div>
""",
    unsafe_allow_html=True,
)



st.subheader("测试问题设置")
default_questions = get_geo_questions(brand)

with st.expander("✏️ 查看/编辑测试问题（可修改）", expanded=True):
    questions_text = st.text_area(
        "每行一个问题（至少8个）",
        value="\n".join(default_questions),
        height=200,
    )

questions = [q.strip() for q in questions_text.strip().split("\n") if q.strip()]
st.caption(f"当前共 {len(questions)} 个测试问题")

if len(questions) < 4:
    st.warning("建议至少设置 4 个测试问题以获得更全面的分析")

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
    maybe_show_banner(res)

    col1, col2, col3 = st.columns(3)
    with col1:
        q_count = len(res.get("questions") or questions)
        st.metric("测试问题数量", q_count)
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
