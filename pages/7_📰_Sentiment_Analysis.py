import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.sentiment_analysis as sentiment_mod
from prompts.sentiment_prompt import SAMPLE_COMMENTS
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="AI舆情分析 — BrandPulse AI", page_icon="📰", layout="wide")
brand = render_sidebar()

st.title("📰 AI 舆情分析")
st.caption("基于公开评论样本，识别正负向情感、风险等级与官方回应建议")

brand_name = BRAND_DISPLAY_NAMES[brand]

st.info(
    "**输入**：用户评论、新闻摘要或社媒内容样本\n"
    "**输出**：情感分布、核心关注点、风险等级、官方回应建议\n\n"
    "⚠️ 分析结论基于所提供的样本，不代表全网舆情。商业决策前需更大规模数据采集。"
)

# ── 数据来源选择 ───────────────────────────────────────────────────
collected = st.session_state.get("collected_sentiment_text", "")
collected_source = st.session_state.get("collected_sentiment_source", "")

if collected:
    st.success(f"📡 检测到来自「数据采集」模块的数据（{collected_source}）· 可直接使用")

source_options = ["使用内置演示样本", "手动粘贴内容"]
if collected:
    source_options.insert(0, f"使用采集数据（{collected_source}）")

data_source = st.radio("数据来源", source_options, horizontal=True)

if collected and data_source.startswith("使用采集数据"):
    comments_input = collected
    st.text_area("采集数据预览", value=comments_input, height=200, disabled=True)
elif data_source == "使用内置演示样本":
    comments = SAMPLE_COMMENTS.get(brand, "")
    st.text_area("样本数据预览（可编辑）", value=comments, height=200, key="comments_display")
    comments_input = st.session_state.get("comments_display", comments)
else:
    comments_input = st.text_area(
        "粘贴用户评论/舆情样本（每条一行）",
        placeholder="粘贴来自小红书、微博、大众点评、新闻摘要等平台的公开内容样本...",
        height=200,
    )

if st.button("🚀 运行舆情分析", type="primary"):
    if not comments_input.strip():
        st.warning("请输入评论样本或使用内置演示数据")
    else:
        with st.spinner("正在进行 AI 舆情分析...（约 20-35 秒）"):
            try:
                result = sentiment_mod.run(brand, comments=comments_input)
                st.session_state["sentiment_result"] = result
            except Exception as e:
                st.error(f"分析失败：{e}")

if "sentiment_result" in st.session_state:
    res = st.session_state["sentiment_result"]
    st.markdown("---")
    st.markdown(res["output"])

    with st.expander("📋 分析所用样本内容", expanded=False):
        st.text(res["comments_used"])

    with st.expander("📚 知识库背景引用", expanded=False):
        for i, c in enumerate(res["chunks"], 1):
            st.markdown(f"**[{i}] 来源：`{c['source']}`**")
            st.text(c["text"][:200] + "..." if len(c["text"]) > 200 else c["text"])
