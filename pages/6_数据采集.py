"""PinSight AI — 数据采集模块（舆情 + 行业动态）"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.sidebar import render as render_sidebar
from utils.prd_components import render_disclaimer
from config.settings import BRAND_DISPLAY_NAMES
from config.brand_manager import get_brand
from core.data_collector import (
    collect_brand_sentiment,
    collect_industry_trends,
    flatten_comments_for_sentiment,
)
from modules.collect_helpers import channel_risk, group_by_keywords, DEFAULT_NEGATIVE_WORDS
import config.collect_tasks as collect_tasks
from prompts.geo_analysis_prompt import parse_keywords

st.set_page_config(page_title="数据采集 — PinSight AI", page_icon="📡", layout="wide", initial_sidebar_state="expanded")
brand = render_sidebar()

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">数据采集</h1>
  <p class="page-desc">采集品牌舆情与行业动态，结果可一键流转至舆情分析或合规审查模块</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("## 📡 数据采集中心")

st.markdown(
    """
<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-radius:6px;padding:12px 16px;margin-bottom:10px;font-size:13px;color:#5C4F42">
<b>📊 数据工作流</b> &nbsp;&nbsp;
<span style="background:rgba(43,108,176,0.08);border:1px solid rgba(43,108,176,0.2);border-radius:4px;padding:3px 8px;color:#2B6CB0">📡 数据采集</span>
&nbsp;→&nbsp;
<span style="background:rgba(61,122,90,0.09);border:1px solid rgba(61,122,90,0.2);border-radius:4px;padding:3px 8px;color:#3D7A5A">📰 舆情分析</span>
&nbsp;/&nbsp;
<span style="background:rgba(181,134,13,0.1);border:1px solid rgba(181,134,13,0.2);border-radius:4px;padding:3px 8px;color:#B5860D">🛡️ 合规审查</span>
&nbsp;&nbsp;·&nbsp;&nbsp;采集结果可一键流转至下游模块，无需手动复制
</div>
""",
    unsafe_allow_html=True,
)
st.divider()

# 品牌切换时清除两个 tab 的缓存数据
if st.session_state.get("_datacollect_last_brand") != brand:
    st.session_state.pop("brand_sentiment_data", None)
    st.session_state.pop("brand_sentiment_brand", None)
    st.session_state.pop("industry_trend_data", None)
    st.session_state.pop("industry_trend_brand", None)
    st.session_state["_datacollect_last_brand"] = brand

tab_brand, tab_industry, tab_history = st.tabs(["🎯 品牌舆情采集", "📊 行业动态采集", "📜 历史任务"])

# ══════════════════════════════════════════════════════════════════
# TAB 1 — 品牌舆情采集
# ══════════════════════════════════════════════════════════════════
with tab_brand:
    # 禁用 text_input 显示当前品牌，「不设 key」用 value=，每次运行重置为当前品牌
    # （与下方能正常更新的 keyword 框同机制；动态 markdown / 品牌后缀 key 都会 stale）
    st.text_input("当前品牌", value=BRAND_DISPLAY_NAMES[brand], disabled=True)

    # 关键词组默认值（仅初始化一次；品牌切换时刷新品牌词）
    st.session_state.setdefault("dc_brand_words", BRAND_DISPLAY_NAMES[brand].split()[0])
    st.session_state.setdefault("dc_product_words", "")
    st.session_state.setdefault("dc_negative_words", "、".join(DEFAULT_NEGATIVE_WORDS))
    if st.session_state.get("_dc_kw_brand") != brand:
        st.session_state["dc_brand_words"] = BRAND_DISPLAY_NAMES[brand].split()[0]
        st.session_state["_dc_kw_brand"] = brand
    # 复用历史配置预填（E4）—— 在 widget 实例化前覆盖
    if "dc_prefill" in st.session_state:
        _pf = st.session_state.pop("dc_prefill")
        for _k in ("dc_brand_words", "dc_product_words", "dc_negative_words"):
            short = _k[3:]
            if short in _pf:
                st.session_state[_k] = _pf[short]

    # ── E1 · 关键词分组采集 ────────────────────────────────────────────────────
    st.markdown("**① 关键词分组**（支持逗号 / 换行分隔）")
    kc1, kc2, kc3 = st.columns(3)
    with kc1:
        st.text_area("品牌词", key="dc_brand_words", height=80)
    with kc2:
        st.text_area("产品词", key="dc_product_words", height=80, placeholder="如：多肉葡萄, 芝士奶盖")
    with kc3:
        st.text_area("负面词", key="dc_negative_words", height=80)

    # ── E2/E3 · 平台 / 时间 / 调度频率 ─────────────────────────────────────────
    st.markdown("**② 采集设置**")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        platform = st.selectbox("采集平台", ["全渠道", "小红书", "微博", "抖音", "大众点评", "美团"])
    with c2:
        days = st.selectbox("时间范围", ["近7天", "近30天", "近90天"])
    with c3:
        schedule = st.selectbox("执行频率", collect_tasks.SCHEDULES,
                                help="单次：立即执行一次；每日/每周：登记为定期自动采集任务")
    with c4:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run = st.button("🔍 开始采集", use_container_width=True, type="primary")

    _brand_words = parse_keywords(st.session_state.get("dc_brand_words", ""))
    _product_words = parse_keywords(st.session_state.get("dc_product_words", ""))
    _negative_words = parse_keywords(st.session_state.get("dc_negative_words", "")) or DEFAULT_NEGATIVE_WORDS

    if run or st.session_state.get("brand_sentiment_data"):
        if run:
            with st.spinner("正在采集数据…（演示模式）"):
                import time; time.sleep(1.2)
            results = collect_brand_sentiment(brand, platform)
            st.session_state["brand_sentiment_data"] = results
            st.session_state["brand_sentiment_brand"] = brand
            # E3/E4 · 登记采集任务
            collect_tasks.add_task(
                brand, platform, schedule,
                config={
                    "brand_words": st.session_state.get("dc_brand_words", ""),
                    "product_words": st.session_state.get("dc_product_words", ""),
                    "negative_words": st.session_state.get("dc_negative_words", ""),
                    "days": days,
                },
                result_count=sum(len(t["comments"]) for t in results),
            )
            if schedule != "单次执行":
                st.toast(f"已登记「{schedule}」定期采集任务", icon="🔁")
        else:
            results = st.session_state.get("brand_sentiment_data", [])

        if st.session_state.get("brand_sentiment_brand") != brand:
            results = collect_brand_sentiment(brand, platform)
            st.session_state["brand_sentiment_data"] = results
            st.session_state["brand_sentiment_brand"] = brand

        st.success(f"✅ 采集完成 · 共 {len(results)} 个话题 · {sum(len(t['comments']) for t in results)} 条评论")

        # ── 结果视图切换：话题视图 / E1 关键词分组视图 ─────────────────────────
        view = st.radio("结果视图", ["按话题", "按关键词分组（品牌词/产品词/负面词）"],
                        horizontal=True, key="dc_view")

        if view == "按话题":
            for topic in results:
                sentiment_color = {"正向": "🟢", "中性": "⚪", "负向": "🔴"}.get(topic["overall_sentiment"], "⚪")
                # E2 · 渠道风险标注
                rlv, ricon, rdesc = channel_risk(topic.get("source", ""))
                with st.expander(
                    f"{sentiment_color} **{topic['title']}**　｜　{topic['source']} {ricon}{rlv}风险 · {topic['time']} · {topic['heat']}",
                    expanded=False,
                ):
                    st.caption(f"📡 渠道风险：{ricon} {rlv} — {rdesc}")
                    st.markdown(f"**整体情感：** {sentiment_color} {topic['overall_sentiment']}　｜　**评论数：** {len(topic['comments'])}")
                    st.markdown("---")
                    for c in topic["comments"]:
                        badge = {"正向": "🟢", "中性": "⚪", "负向": "🔴"}.get(c.get("sentiment", "中性"), "⚪")
                        col_a, col_b = st.columns([8, 1])
                        with col_a:
                            st.markdown(f"{badge} **@{c['user']}** · {c['time']} · {ricon}{topic['source']}\n\n{c['content']}")
                        with col_b:
                            st.caption(f"👍 {c['likes']}")
                        st.markdown("")
        else:
            # E1-2 · 按三组关键词分区展示
            grouped = group_by_keywords(results, _brand_words, _product_words, _negative_words)
            gcfg = [("品牌词", "🏷️", _brand_words), ("产品词", "🧋", _product_words), ("负面词", "⚠️", _negative_words)]
            for gname, gicon, gwords in gcfg:
                items = grouped.get(gname, [])
                st.markdown(f"### {gicon} {gname}（{len(items)} 条）　<span style='color:#999;font-size:12px'>关键词：{('、'.join(gwords)) or '—'}</span>", unsafe_allow_html=True)
                if not items:
                    st.caption("未命中相关评论")
                for it in items:
                    c = it["comment"]
                    rlv, ricon, _ = channel_risk(it["source"])
                    badge = {"正向": "🟢", "中性": "⚪", "负向": "🔴"}.get(c.get("sentiment", "中性"), "⚪")
                    st.markdown(f"{badge} **@{c['user']}** · {ricon}{it['source']}（{rlv}风险） · 👍{c['likes']}　〔{it['topic']}〕\n\n{c['content']}")
                st.divider()

        st.divider()
        send_col1, send_col2, _ = st.columns([2, 2, 4])
        with send_col1:
            if st.button("📤 送往舆情分析模块", type="primary", use_container_width=True):
                flat = flatten_comments_for_sentiment(results)
                st.session_state["collected_sentiment_text"] = flat
                st.session_state["collected_sentiment_source"] = "采集数据"
                st.switch_page("pages/7_舆情分析.py")
        with send_col2:
            if st.button("📤 送往合规审查模块", use_container_width=True):
                sample_content = "\n".join(
                    c["content"]
                    for t in results
                    for c in t["comments"]
                    if c.get("sentiment") == "正向"
                )[:800]
                st.session_state["content_for_compliance"] = sample_content
                st.switch_page("pages/8_合规卫士.py")
    else:
        st.info("配置采集参数后点击「开始采集」，获取品牌最新舆情数据（演示模式）")

# ══════════════════════════════════════════════════════════════════
# TAB 2 — 行业动态采集
# ══════════════════════════════════════════════════════════════════
with tab_industry:
    _b = get_brand(brand)
    _industry = _b.get("industry", "") if _b else ""
    _ind_label = f"{_industry}行业动态" if _industry else "行业动态"
    st.markdown(f"#### {_ind_label} & 热门话题")

    col_cat, col_run = st.columns([4, 1])
    with col_cat:
        category = st.selectbox(
            "话题分类",
            ["全部", "行业报告", "竞品动向", "营销趋势", "消费洞察", "品类趋势"],
        )
    with col_run:
        st.markdown("<div style='margin-top:28px'></div>", unsafe_allow_html=True)
        run_ind = st.button("🔍 开始采集", key="run_industry", use_container_width=True, type="primary")

    # Clear cached trends when brand changes
    if st.session_state.get("industry_trend_brand") != brand:
        st.session_state.pop("industry_trend_data", None)

    if run_ind or st.session_state.get("industry_trend_data"):
        if run_ind:
            with st.spinner("正在采集行业动态…（演示模式）"):
                import time; time.sleep(1.0)
            trends = collect_industry_trends(category, brand_key=brand)
            st.session_state["industry_trend_data"] = trends
            st.session_state["industry_trend_brand"] = brand
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
                st.switch_page("pages/7_舆情分析.py")
        with ind_send2:
            if st.button("📤 送往合规审查", key="ind_to_comp", use_container_width=True):
                sample = "\n".join(t["summary"] for t in trends[:3])
                st.session_state["content_for_compliance"] = sample
                st.switch_page("pages/8_合规卫士.py")
    else:
        st.info("选择话题分类后点击「开始采集」，获取行业最新动态（演示模式）")

# ══════════════════════════════════════════════════════════════════
# TAB 3 — 历史任务（E4）
# ══════════════════════════════════════════════════════════════════
with tab_history:
    st.caption("数据采集历史任务记录（含时间戳、平台、调度频率、执行状态）。仅显示当前品牌。")
    records = collect_tasks.list_tasks(brand_key=brand)
    if not records:
        st.info("暂无采集任务。在「品牌舆情采集」标签页运行一次采集后即会生成历史记录。")
    else:
        _sb = {"单次执行": "▶️", "每日": "🔁", "每周": "📅"}
        for r in records:
            with st.container(border=True):
                hc1, hc2 = st.columns([5, 1.4])
                with hc1:
                    st.markdown(f"**{_sb.get(r['schedule'],'•')} {r['schedule']}** · 平台：{r['platform']} · "
                                f"`{r['status']}` · {r.get('result_count',0)} 条")
                    cfg = r.get("config", {})
                    st.caption(f"⏱ {r.get('created_at','')}　|　品牌词：{cfg.get('brand_words','—')}　"
                               f"产品词：{cfg.get('product_words','—') or '—'}")
                with hc2:
                    bcols = st.columns(2)
                    with bcols[0]:
                        if st.button("复制配置", key=f"col_copy_{r['id']}", use_container_width=True):
                            st.session_state["dc_prefill"] = r.get("config", {})
                            st.success("已载入到「品牌舆情采集」表单")
                            st.rerun()
                    with bcols[1]:
                        if st.button("删除", key=f"col_del_{r['id']}", use_container_width=True):
                            collect_tasks.delete_task(r["id"])
                            st.rerun()

# A3 · 标准免责声明
render_disclaimer()
