import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.sentiment_analysis as sentiment_mod
from utils.result_banner import maybe_show_banner
from utils.prd_components import render_four_blocks, render_source_meta, render_disclaimer, review_gate
from prompts.sentiment_prompt import get_sample_comments
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="AI舆情分析 — PinSight AI", page_icon="📰", layout="wide")
brand = render_sidebar()

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">舆情分析</h1>
  <p class="page-desc">基于公开评论样本识别正负向情感、核心关注点、风险等级与官方回应建议</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-left:3px solid #C4522A;border-radius:6px;padding:12px 16px;margin:0 0 18px;font-size:13px;color:#5C4F42;line-height:1.7">
  <strong style="color:#1A1A1A">输入</strong>：用户评论样本（可从「数据采集」模块一键导入，或手动粘贴）<br>
  <strong style="color:#1A1A1A">输出</strong>：整体情感分布 · 正/负向核心主题 · 风险等级 · 官方回应建议<br>
  分析基于所提供样本，不代表全网舆情全貌，商业决策前需结合更大规模数据。
</div>
""",
    unsafe_allow_html=True,
)


brand_name = BRAND_DISPLAY_NAMES[brand]

# 样本文本框用「品牌后缀 key」，每个品牌独立 widget 实例，
# 切换品牌即换 widget_id → 强制 remount，彻底规避 pop+value= 的 stale DOM

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
    # 静态 key + 品牌切换时「预先写入」session_state（而非 pop+value=），
    # 既保留同品牌内的用户编辑，又在换品牌时刷新样本，且不产生孤儿 widget。
    if st.session_state.get("_sent_sample_brand") != brand:
        st.session_state["comments_display"] = get_sample_comments(brand)
        st.session_state["_sent_sample_brand"] = brand
    st.text_area("样本数据预览（可编辑）", height=200, key="comments_display")
    comments_input = st.session_state.get("comments_display", "")
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
                from datetime import datetime
                result = sentiment_mod.run(brand, comments=comments_input)
                result["_query_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                result["_brand"] = brand
                st.session_state["sentiment_result"] = result
                st.session_state.pop("reviewed_sentiment", None)
            except Exception as e:
                st.error(f"分析失败：{e}")

# 品牌切换后自动清除旧结果
if st.session_state.get("sentiment_result", {}).get("_brand") != brand:
    st.session_state.pop("sentiment_result", None)
    st.session_state.pop("reviewed_sentiment", None)

if "sentiment_result" in st.session_state:
    res = st.session_state["sentiment_result"]
    st.markdown("---")
    maybe_show_banner(res)

    # A1 · 四大区块渲染
    render_four_blocks(res["output"])

    with st.expander("📋 分析所用样本内容", expanded=False):
        st.text(res.get("comments_used", "（暂无样本内容）"))

    # A2 · 信息溯源
    render_source_meta(res["chunks"], query_time=res.get("_query_time"))

    # A4 · 人工复核门控
    review_gate("sentiment")

    # A3 · 标准免责声明
    render_disclaimer()
