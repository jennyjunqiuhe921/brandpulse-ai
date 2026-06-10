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

# D4 · 数据渠道（含 O2O 平台大众点评/美团）
CHANNELS = ["全渠道", "小红书/微博", "大众点评", "美团", "抖音", "新闻媒体"]

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">舆情分析</h1>
  <p class="page-desc">五级风险预警 · 行业专属风险标签 · 标准化回应话术库，识别情感、关注点与危机信号</p>
</div>
""",
    unsafe_allow_html=True,
)

brand_name = BRAND_DISPLAY_NAMES[brand]

tab_analyze, tab_history = st.tabs(["📰 舆情分析", "📜 历史记录"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — 舆情分析
# ══════════════════════════════════════════════════════════════════════════════
with tab_analyze:
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
        # 静态 key + 品牌切换预写 session_state（规避 stale DOM）
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
            height=200, key="sent_paste",
        )
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
                    # D1 · 规则化五级风险
                    rk = risk_mod.classify(comments_input)
                    # D3 · 记录历史
                    sentiment_tasks.add_record(
                        brand, rk["level"], rk["label"], source_label,
                        summary=(comments_input.strip().splitlines() or [""])[0][:40],
                        tags=list(rk["tags"].keys()),
                    )
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

        # ── D1 · 五级风险预警徽章 + 行业专属标签 ──────────────────────────────
        rk = risk_mod.classify(res.get("comments_used", ""))
        lvl_render = {5: st.error, 4: st.error, 3: st.warning, 2: st.info, 1: st.success}
        lvl_render[rk["level"]](
            f"{rk['icon']} 风险预警等级：**{rk['level']} 级 · {rk['label']}** — {rk['desc']}"
        )
        if rk["tags"]:
            st.markdown("**行业专属风险标签：** " + "　".join(f"`⚠️ {t}`" for t in rk["tags"]))

        # ── D2 · 标准化回应话术库 ────────────────────────────────────────────
        with st.expander("💬 标准化回应话术库（按场景）", expanded=rk["level"] >= 4):
            for scen, icon, scripts in risk_mod.templates_for(rk["scenarios"]):
                st.markdown(f"**{icon} {scen}**")
                for s in scripts:
                    st.markdown(f"> {s}")
                st.divider()
            st.caption("⚠️ 以上话术为模板参考，正式对外发布前须由品牌方危机公关/法务复核。")

        st.markdown("---")
        # A1 · 四大区块渲染
        render_four_blocks(res["output"])

        with st.expander("📋 分析所用样本内容", expanded=False):
            st.text(res.get("comments_used", "（暂无样本内容）"))

        # A2 · 信息溯源
        render_source_meta(res["chunks"], query_time=res.get("_query_time"))
        # A4 · 人工复核门控
        review_gate("sentiment")
        # A3 · 免责声明
        render_disclaimer()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — 历史记录（D3）
# ══════════════════════════════════════════════════════════════════════════════
with tab_history:
    st.caption("舆情分析历史记录（含时间戳、摘要、风险等级、来源渠道）。仅显示当前品牌。")
    hc1, hc2 = st.columns(2)
    with hc1:
        f_level = st.selectbox("按风险等级筛选", ["全部", "≥3级", "≥4级", "仅5级危机"], key="sent_hist_level")
    with hc2:
        f_sort = st.selectbox("排序", ["时间（新→旧）", "时间（旧→新）", "风险（高→低）"], key="sent_hist_sort")

    min_level = {"全部": None, "≥3级": 3, "≥4级": 4, "仅5级危机": 5}[f_level]
    sort_key = {"时间（新→旧）": "time_desc", "时间（旧→新）": "time_asc", "风险（高→低）": "risk_desc"}[f_sort]
    records = sentiment_tasks.list_records(brand_key=brand, min_level=min_level, sort=sort_key)

    if not records:
        st.info("暂无舆情记录。在「舆情分析」标签页运行一次分析后即会生成历史记录。")
    else:
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
                        sentiment_tasks.delete_record(r["id"])
                        st.rerun()
