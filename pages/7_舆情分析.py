import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from utils.sidebar import render as render_sidebar
import modules.sentiment_analysis as sentiment_mod
import modules.sentiment_risk as risk_mod
import config.sentiment_tasks as sentiment_tasks
from utils.result_banner import maybe_show_banner
from utils.prd_components import render_four_blocks, render_source_meta, render_disclaimer, review_gate
from prompts.sentiment_prompt import get_sample_comments
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="AI舆情分析 — PinSight AI", page_icon="📰", layout="wide", initial_sidebar_state="expanded")
brand = render_sidebar()

CHANNELS = ["全渠道", "小红书/微博", "大众点评", "美团", "抖音", "新闻媒体"]

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">舆情中心</h1>
  <p class="page-desc">监测研判 + 处置应对一体：五级风险 · 口碑健康分 · 分级工单 · 复盘归档 · GEO联动</p>
</div>
""",
    unsafe_allow_html=True,
)


# ══════════════════════════════════════════════════════════════════════════════
# 舆情分析（监测）
# ══════════════════════════════════════════════════════════════════════════════
def _render_analysis(brand):
    st.info("输入用户评论样本（可从「数据采集」一键导入或手动粘贴）→ 输出整体情感分布 · "
            "五级风险预警 · 行业风险标签 · 标准化回应话术。分析基于样本，不代表全网舆情全貌。")
    collected = st.session_state.get("collected_sentiment_text", "")
    collected_source = st.session_state.get("collected_sentiment_source", "")
    if collected:
        st.success(f"📡 检测到来自「数据采集」模块的数据（{collected_source}）· 可直接使用")
    source_options = ["使用内置演示样本", "手动粘贴内容"]
    if collected:
        source_options.insert(0, f"使用采集数据（{collected_source}）")
    sc1, sc2 = st.columns([2, 1])
    with sc1:
        data_source = st.radio("数据来源", source_options, horizontal=True, key="sent_source")
    with sc2:
        channel = st.selectbox("数据渠道", CHANNELS, key="sent_channel",
                               help="覆盖小红书/微博、大众点评、美团等 O2O 点评平台")
    if collected and data_source.startswith("使用采集数据"):
        comments_input = collected
        source_label = collected_source or channel
        st.text_area("采集数据预览", value=comments_input, height=200, disabled=True)
    elif data_source == "使用内置演示样本":
        if st.session_state.get("_sent_sample_brand") != brand:
            st.session_state["comments_display"] = get_sample_comments(brand)
            st.session_state["_sent_sample_brand"] = brand
        st.text_area("样本数据预览（可编辑）", height=200, key="comments_display")
        comments_input = st.session_state.get("comments_display", "")
        source_label = f"内置样本·{channel}"
    else:
        comments_input = st.text_area(
            "粘贴用户评论/舆情样本（每条一行）",
            placeholder="粘贴来自小红书、微博、大众点评、美团、新闻摘要等平台的公开内容样本...",
            height=200, key="sent_paste")
        source_label = channel

    if st.button("🚀 运行舆情分析", type="primary"):
        if not comments_input.strip():
            st.warning("请输入评论样本或使用内置演示数据")
        else:
            with st.spinner("正在进行 AI 舆情分析...（约 20-35 秒）"):
                try:
                    result = sentiment_mod.run(brand, comments=comments_input)
                    result["_query_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    result["_brand"] = brand
                    result["_source"] = source_label
                    st.session_state["sentiment_result"] = result
                    st.session_state.pop("reviewed_sentiment", None)
                    rk = risk_mod.classify(comments_input)
                    sentiment_tasks.add_record(
                        brand, rk["level"], rk["label"], source_label,
                        summary=(comments_input.strip().splitlines() or [""])[0][:40],
                        tags=list(rk["tags"].keys()))
                except Exception as e:
                    st.error(f"分析失败：{e}")

    if st.session_state.get("sentiment_result", {}).get("_brand") != brand:
        st.session_state.pop("sentiment_result", None)
        st.session_state.pop("reviewed_sentiment", None)

    if "sentiment_result" in st.session_state:
        res = st.session_state["sentiment_result"]
        st.markdown("---")
        maybe_show_banner(res)
        rk = risk_mod.classify(res.get("comments_used", ""))
        lvl_render = {5: st.error, 4: st.error, 3: st.warning, 2: st.info, 1: st.success}
        lvl_render[rk["level"]](f"{rk['icon']} 风险预警等级：**{rk['level']} 级 · {rk['label']}** — {rk['desc']}")
        if rk["tags"]:
            st.markdown("**行业专属风险标签：** " + "　".join(f"`⚠️ {t}`" for t in rk["tags"]))
        with st.expander("💬 标准化回应话术库（按场景）", expanded=rk["level"] >= 4):
            for scen, icon, scripts in risk_mod.templates_for(rk["scenarios"]):
                st.markdown(f"**{icon} {scen}**")
                for s in scripts:
                    st.markdown(f"> {s}")
                st.divider()
            st.caption("⚠️ 以上话术为模板参考，正式对外发布前须由品牌方危机公关/法务复核。")
        st.markdown("---")
        render_four_blocks(res["output"])
        with st.expander("📋 分析所用样本内容", expanded=False):
            st.text(res.get("comments_used", "（暂无样本内容）"))
        render_source_meta(res["chunks"], query_time=res.get("_query_time"))
        review_gate("sentiment")
        render_disclaimer()


def _render_reputation(brand):
    import pandas as pd
    from modules.reputation_score import compute as _rep_compute
    st.caption("五维口碑健康模型（情感结构/负面占比/高危红标/传播热度/风险权重）→ 0-100 分 + "
               "一句汇报评语。已剔除待验证舆情；完成消影/复盘的事件降权。")
    _rep = _rep_compute(sentiment_tasks.list_records(brand_key=brand))
    if _rep["score"] is None:
        st.info(_rep["comment"])
        return
    sc = _rep["score"]
    color = "#2E7D32" if sc >= 85 else ("#1E88E5" if sc >= 70 else ("#F9A825" if sc >= 55 else "#C62828"))
    c = st.columns([1, 2])
    with c[0]:
        st.markdown(
            f'<div style="text-align:center;border:1px solid #DDD4C4;border-radius:12px;'
            f'padding:18px;background:#FDFAF5"><div style="font-size:13px;color:#9C8E82">'
            f'月度口碑健康分</div><div style="font-size:52px;font-weight:800;color:{color}">{sc}'
            f'</div><div style="font-size:12px;color:#9C8E82">/100</div></div>', unsafe_allow_html=True)
    with c[1]:
        st.metric("有效样本", _rep["total"])
        st.metric("负面舆情", _rep["negative"])
        st.metric("高危红标", _rep["high_risk"])
    st.info("📋 月度评语：" + _rep["comment"])
    st.markdown("**五维拆解**")
    st.bar_chart(pd.DataFrame({"得分": _rep["dims"]}))
    st.caption("可直接复制评语用于管理层汇报 PPT。数据基于本主体舆情记录计算。")


def _render_pr(brand):
    from modules.pr_scripts import generate as _pr_gen, SCENARIOS as _PR_SCENES
    st.caption("针对负面舆情生成两套话术：对外公域回复口径（正式礼貌合规）+ 内部市场处置口径"
               "（定性/底线/补偿/策略/禁止话术）。话术仅供人工参考，系统不自动对外发布。")
    sc = st.selectbox("场景模板", _PR_SCENES)
    detail = st.text_area("事件简述（选填）", placeholder="如：顾客反映饮品中有异物，已在大众点评发图")
    if st.button("💬 生成双口径话术", type="primary"):
        st.session_state["_pr_res"] = _pr_gen(sc, brand, detail)
    res = st.session_state.get("_pr_res")
    if res:
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown("##### 📢 对外公开回复口径")
            st.markdown(f'<div style="background:#EEF4FB;border:1px solid #C9DDF0;border-radius:8px;'
                        f'padding:12px;white-space:pre-wrap;font-size:13px">{res["external"]}</div>',
                        unsafe_allow_html=True)
        with cc2:
            st.markdown("##### 🛠 内部市场处置口径")
            st.markdown(f'<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-radius:8px;'
                        f'padding:12px;white-space:pre-wrap;font-size:13px">{res["internal"]}</div>',
                        unsafe_allow_html=True)
        if sc == "食品安全":
            st.warning("⚠️ 食品安全类：对外引导私域沟通，切勿公开争辩或作绝对化承诺；须经主管复核后使用。")


def _render_geo_bridge(brand):
    from modules import sentiment_geo_bridge as BR
    import pandas as _pd
    st.caption("把舆情里的**高频负面话题**推送到 GEO：针对这些话题，补充真实、准确的官方问答内容，"
               "改善 AI 搜索回答。⚠️ 仅补充真实信息，严禁刷好评/伪造/灌水。")
    topics = BR.hot_negatives(brand)
    if not topics:
        st.info("当前主体暂无高频负面话题（需有 3 级及以上舆情/工单）。先在「舆情分析」「工单处置」积累数据。")
        return
    sugs = BR.geo_suggestions(brand, topics)
    st.markdown("#### 高频负面话题 → GEO 前置优化建议")
    st.dataframe(_pd.DataFrame([{
        "负面话题": s["topic"], "声量": s["count"], "AI 风险点": s["concern"],
        "GEO 优化方向": s["geo_action"]} for s in sugs]), use_container_width=True, hide_index=True)
    st.markdown("**建议补充的 GEO 关键词**")
    kws = BR.all_keywords(sugs)
    st.code("\n".join(kws))
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("📡 带入 GEO 收录监测", use_container_width=True):
            st.session_state["gi_kw"] = "\n".join(kws)
            st.success(f"已带入 {len(kws)} 个词 → 去「GEO → 监测诊断 → 收录监测」运行检测")
    with cc2:
        st.page_link("pages/3_GEO.py", label="🌐 前往 GEO 布局优化内容", icon="🌐")
    st.caption("闭环：舆情发现负面话题 → GEO 前置补充真实内容 → 改善 AI 回答 → 收录监测验证。")


def _render_history(brand):
    st.caption("舆情分析历史记录（含时间戳、摘要、风险等级、来源渠道）。仅显示当前主体。")
    hc1, hc2 = st.columns(2)
    with hc1:
        f_level = st.selectbox("按风险等级筛选", ["全部", "≥3级", "≥4级", "仅5级危机"], key="sent_hist_level")
    with hc2:
        f_sort = st.selectbox("排序", ["时间（新→旧）", "时间（旧→新）", "风险（高→低）"], key="sent_hist_sort")
    min_level = {"全部": None, "≥3级": 3, "≥4级": 4, "仅5级危机": 5}[f_level]
    sort_key = {"时间（新→旧）": "time_desc", "时间（旧→新）": "time_asc", "风险（高→低）": "risk_desc"}[f_sort]
    records = sentiment_tasks.list_records(brand_key=brand, min_level=min_level, sort=sort_key)
    if not records:
        st.info("暂无舆情记录。在「舆情分析」运行一次分析后即会生成历史记录。")
        return
    _icon = {1: "🟢", 2: "🔵", 3: "🟡", 4: "🟠", 5: "🔴"}
    for r in records:
        with st.container(border=True):
            rc1, rc2 = st.columns([5, 1])
            with rc1:
                tags = "　".join(f"`{t}`" for t in r.get("tags", []))
                st.markdown(f"**{_icon.get(r['risk_level'],'•')} {r['risk_level']}级 · {r['risk_label']}** "
                            f"· 来源：{r.get('source','—')}")
                st.caption(f"⏱ {r.get('created_at','')}　|　摘要：{r.get('summary','')}　{tags}")
            with rc2:
                if st.button("删除", key=f"sent_del_{r['id']}", use_container_width=True):
                    sentiment_tasks.delete_record(r["id"]); st.rerun()


def _set_mode(m):
    st.session_state["_sent_mode"] = m


# ══════════════════════════════════════════════════════════════════════════════
# 场景模式调度（监测分析 / 处置应对）
# ══════════════════════════════════════════════════════════════════════════════
MODES = ["🔍 监测分析", "🛡️ 处置应对"]
mode = st.radio("场景", MODES, horizontal=True, key="_sent_mode", label_visibility="collapsed")
st.caption("🔍 监测分析 = 发现问题（舆情分析·口碑健康分·历史）　|　🛡️ 处置应对 = 解决问题（工单处置·公关话术·GEO联动）")
st.divider()

if mode == "🔍 监测分析":
    t1, t2, t3 = st.tabs(["📰 舆情分析", "📊 口碑健康分", "📜 历史记录"])
    with t1:
        _render_analysis(brand)
    with t2:
        _render_reputation(brand)
    with t3:
        _render_history(brand)
else:
    t1, t2, t3 = st.tabs(["🎫 工单处置", "💬 公关话术", "🔗 GEO联动"])
    with t1:
        from utils.ticket_view import render as render_tickets
        render_tickets(brand)
    with t2:
        _render_pr(brand)
    with t3:
        _render_geo_bridge(brand)
