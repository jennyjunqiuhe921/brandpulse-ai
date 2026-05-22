"""BrandPulse AI — 数据采集模块（舆情 + 行业动态）"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.sidebar import render as render_sidebar
from config.settings import BRAND_DISPLAY_NAMES
from core.data_collector import (
    collect_brand_sentiment,
    collect_industry_trends,
    flatten_comments_for_sentiment,
)

st.set_page_config(page_title="数据采集 — BrandPulse AI", page_icon="📡", layout="wide")
brand = render_sidebar()

st.markdown("## 📡 数据采集中心")
st.caption("采集品牌舆情与行业动态，结果可直接送往舆情分析或合规审查模块")

st.markdown(
    """
<div style="background:#f8f9fa;border-radius:10px;padding:14px 20px;margin-bottom:8px;font-size:14px">
<b>📊 数据工作流</b> &nbsp;&nbsp;
<span style="background:#e3f2fd;border-radius:4px;padding:3px 8px">📡 数据采集</span>
&nbsp;→&nbsp;
<span style="background:#e8f5e9;border-radius:4px;padding:3px 8px">📰 舆情分析</span>
&nbsp;/&nbsp;
<span style="background:#fff3e0;border-radius:4px;padding:3px 8px">🛡️ 合规审查</span>
&nbsp;&nbsp;·&nbsp;&nbsp;采集结果可一键流转至下游模块，无需手动复制
</div>
""",
    unsafe_allow_html=True,
)
st.divider()

tab_brand, tab_industry = st.tabs(["🎯 品牌舆情采集", "📊 行业动态采集"])

# ══════════════════════════════════════════════════════════════════
# TAB 1 — 品牌舆情采集
# ══════════════════════════════════════════════════════════════════
with tab_brand:
    st.markdown(f"#### 当前品牌：{BRAND_DISPLAY_NAMES[brand]}")

    col_params, col_btn = st.columns([4, 1])
    with col_params:
        c1, c2, c3 = st.columns(3)
        with c1:
            platform = st.selectbox("采集平台", ["全渠道", "小红书", "微博", "抖音"])
        with c2:
            days = st.selectbox("时间范围", ["近7天", "近30天", "近90天"])
        with c3:
            keyword = st.text_input("关键词", value=BRAND_DISPLAY_NAMES[brand].split()[0])

    with col_btn:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run = st.button("🔍 开始采集", use_container_width=True, type="primary")

    if run or st.session_state.get("brand_sentiment_data"):
        if run:
            with st.spinner("正在采集数据…（演示模式）"):
                import time; time.sleep(1.2)
            results = collect_brand_sentiment(brand, platform)
            st.session_state["brand_sentiment_data"] = results
            st.session_state["brand_sentiment_brand"] = brand
        else:
            results = st.session_state.get("brand_sentiment_data", [])

        if st.session_state.get("brand_sentiment_brand") != brand:
            results = collect_brand_sentiment(brand, platform)
            st.session_state["brand_sentiment_data"] = results
            st.session_state["brand_sentiment_brand"] = brand

        st.success(f"✅ 采集完成 · 共 {len(results)} 个话题 · {sum(len(t['comments']) for t in results)} 条评论")

        for topic in results:
            sentiment_color = {"正向": "🟢", "中性": "⚪", "负向": "🔴"}.get(topic["overall_sentiment"], "⚪")
            with st.expander(
                f"{sentiment_color} **{topic['title']}**　｜　{topic['source']} · {topic['time']} · {topic['heat']}",
                expanded=False,
            ):
                st.markdown(f"**整体情感：** {sentiment_color} {topic['overall_sentiment']}　｜　**评论数：** {len(topic['comments'])}")
                st.markdown("---")
                for c in topic["comments"]:
                    badge = {"正向": "🟢", "中性": "⚪", "负向": "🔴"}.get(c.get("sentiment", "中性"), "⚪")
                    col_a, col_b = st.columns([8, 1])
                    with col_a:
                        st.markdown(
                            f"{badge} **@{c['user']}** · {c['time']}\n\n{c['content']}"
                        )
                    with col_b:
                        st.caption(f"👍 {c['likes']}")
                    st.markdown("")

        st.divider()
        send_col1, send_col2, _ = st.columns([2, 2, 4])
        with send_col1:
            if st.button("📤 送往舆情分析模块", type="primary", use_container_width=True):
                flat = flatten_comments_for_sentiment(results)
                st.session_state["collected_sentiment_text"] = flat
                st.session_state["collected_sentiment_source"] = "采集数据"
                st.success("✅ 已送往「舆情分析」模块，切换页面即可分析")
        with send_col2:
            if st.button("📤 送往合规审查模块", use_container_width=True):
                sample_content = "\n".join(
                    c["content"]
                    for t in results
                    for c in t["comments"]
                    if c.get("sentiment") == "正向"
                )[:800]
                st.session_state["content_for_compliance"] = sample_content
                st.success("✅ 已送往「合规审查」模块，切换页面即可审查")
    else:
        st.info("配置采集参数后点击「开始采集」，获取品牌最新舆情数据（演示模式）")

# ══════════════════════════════════════════════════════════════════
# TAB 2 — 行业动态采集
# ══════════════════════════════════════════════════════════════════
with tab_industry:
    st.markdown("#### 新式茶饮行业动态 & 热门话题")

    col_cat, col_run = st.columns([4, 1])
    with col_cat:
        category = st.selectbox(
            "话题分类",
            ["全部", "行业报告", "竞品动向", "营销趋势", "消费洞察", "品类趋势"],
        )
    with col_run:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run_ind = st.button("🔍 开始采集", key="run_industry", use_container_width=True, type="primary")

    if run_ind or st.session_state.get("industry_trend_data"):
        if run_ind:
            with st.spinner("正在采集行业动态…（演示模式）"):
                import time; time.sleep(1.0)
            trends = collect_industry_trends(category)
            st.session_state["industry_trend_data"] = trends
        else:
            trends = st.session_state.get("industry_trend_data", [])

        st.success(f"✅ 采集完成 · 共 {len(trends)} 条行业动态")

        for trend in trends:
            cat_badge = {
                "行业报告": "📊", "竞品动向": "🔍", "营销趋势": "📣",
                "消费洞察": "💡", "品类趋势": "📈",
            }.get(trend["category"], "📌")
            with st.expander(
                f"{cat_badge} **{trend['title']}**　｜　{trend['source']} · {trend['time']}",
                expanded=False,
            ):
                st.info(trend["summary"])
                st.markdown(f"**业内讨论（{len(trend['comments'])} 条）**")
                for c in trend["comments"]:
                    st.markdown(f"💬 **@{c['user']}** · {c['time']} · 👍{c['likes']}")
                    st.markdown(f"> {c['content']}")

        st.divider()
        ind_send1, ind_send2, _ = st.columns([2, 2, 4])
        with ind_send1:
            if st.button("📤 送往舆情分析", key="ind_to_sent", type="primary", use_container_width=True):
                flat = "\n".join(
                    f"【{t['title']}】\n{t['summary']}\n" + "\n".join(f"  评论：{c['content']}" for c in t["comments"])
                    for t in trends
                )
                st.session_state["collected_sentiment_text"] = flat
                st.session_state["collected_sentiment_source"] = "行业动态"
                st.success("✅ 已送往「舆情分析」模块")
        with ind_send2:
            if st.button("📤 送往合规审查", key="ind_to_comp", use_container_width=True):
                sample = "\n".join(t["summary"] for t in trends[:3])
                st.session_state["content_for_compliance"] = sample
                st.success("✅ 已送往「合规审查」模块")
    else:
        st.info("选择话题分类后点击「开始采集」，获取行业最新动态（演示模式）")
