"""S4-1/S4-2 管理驾驶舱（企业领导端）— 7看板 + ROI + 自定义报表 + GEO全局对比。

仅企业领导可见；数据按租户聚合全员、全品牌。
"""
import streamlit as st
import pandas as pd
import hashlib
from utils.sidebar import render
from auth.login import is_admin
import config.content_tasks as content_tasks
import config.geo_tasks as geo_tasks
import config.sentiment_tasks as sentiment_tasks
import config.collect_tasks as collect_tasks
import config.selection_tasks as selection_tasks
import config.competitors as competitors
from config.brand_manager import load_all_brands
from db import approvals as A
from db import tickets as TK
from modules import geo_compare as GC
from modules.content_score import heat_score
from utils.ui import compare_mode_selector, apply_compare

render()

st.markdown('<div class="page-header"><h1>管理驾驶舱</h1>'
            '<p class="page-desc">全公司品牌运营全景：7 大看板 · ROI 价值 · 自定义报表 · '
            'GEO 全局对比，支持同比/环比对标与数据下钻。</p></div>', unsafe_allow_html=True)

if not is_admin():
    st.warning("管理驾驶舱面向企业领导/管理层。")
    st.stop()

st.info("📊 本页为**全公司聚合视图**，统计所有品牌的汇总数据，**不随左侧「分析品牌」切换**。"
        "如需查看单一品牌明细，请到对应执行模块（内容工坊 / GEO / 舆情中心 等）。")


def _syn(seed: str, lo: int, hi: int) -> int:
    return lo + int(hashlib.md5(seed.encode()).hexdigest(), 16) % (hi - lo + 1)


# ── 聚合全租户数据 ───────────────────────────────────────────────────────────
brands = load_all_brands()
contents = content_tasks.list_tasks(brand_key=None)
geos = geo_tasks.list_records(brand_key=None)
sents = sentiment_tasks.list_records(brand_key=None)
collects = collect_tasks.list_tasks(brand_key=None)
selections = selection_tasks.list_tasks(brand=None)
comps = competitors.list_all()
tickets = TK.list_tickets(brand=None)

# 顶部对比模式
cmp_mode = compare_mode_selector("dash_cmp")
st.caption("对比基准为演示合成的历史数据，仅用于展示同比/环比能力。")
st.divider()

boards = st.tabs([
    "🏷️ 品牌总览", "✍️ 内容运营", "📰 舆情口碑", "🌐 GEO搜索",
    "📡 渠道效果", "🛒 选品数据", "🔭 竞品情报", "💰 ROI价值", "📑 自定义报表"])

# ── 1 品牌总览 ───────────────────────────────────────────────────────────────
with boards[0]:
    health = round(sum(_syn(b, 70, 95) for b in brands) / max(1, len(brands)), 1)
    rep = round(sum(_syn(b + "r", 60, 90) for b in brands) / max(1, len(brands)), 1)
    c = st.columns(3)
    c[0].metric("在管品牌", len(brands))
    cc = apply_compare(health, cmp_mode, prev=health - 3.2, industry_avg=80.0)
    c[1].metric("品牌健康分", health, f"{cc['delta']:+.1f} vs {cc['label']}")
    c[2].metric("整体口碑", rep)
    with st.expander("📊 下钻：各品牌健康分"):
        st.dataframe(pd.DataFrame([{"品牌": v.get("name", k), "健康分": _syn(k, 70, 95),
                                    "口碑": _syn(k + "r", 60, 90)} for k, v in brands.items()]),
                     use_container_width=True, hide_index=True)

# ── 2 内容运营 ───────────────────────────────────────────────────────────────
with boards[1]:
    approved = [t for t in contents if t["status"] in ("已通过", "已归档")]
    avg_heat = round(sum(heat_score(t.get("output", ""), t.get("platforms"))["score"]
                         for t in contents) / max(1, len(contents)), 1)
    rate = round(len(approved) / max(1, len(contents)) * 100, 1)
    c = st.columns(3)
    c[0].metric("文案产量", len(contents))
    c[1].metric("合规通过率", f"{rate}%")
    c[2].metric("平均热度", f"{avg_heat}/10")
    with st.expander("📊 下钻：文案状态分布"):
        dist = {}
        for t in contents:
            dist[t["status"]] = dist.get(t["status"], 0) + 1
        if dist:
            st.bar_chart(pd.DataFrame({"数量": dist}))

# ── 3 舆情口碑 ───────────────────────────────────────────────────────────────
with boards[2]:
    high = [r for r in sents if r.get("risk_level", 1) >= 3]
    c = st.columns(3)
    c[0].metric("舆情总量", len(sents))
    c[1].metric("高风险(≥3级)", len(high))
    c[2].metric("处置工单", len(tickets))
    dist = {}
    for r in sents:
        dist[f"{r.get('risk_level',1)}级"] = dist.get(f"{r.get('risk_level',1)}级", 0) + 1
    if dist:
        st.bar_chart(pd.DataFrame({"舆情风险分布": dist}))

# ── 4 GEO搜索 ────────────────────────────────────────────────────────────────
with boards[3]:
    if geos:
        avg_exp = round(sum(GC.get_metrics(r)["exposure"] for r in geos) / len(geos), 1)
        avg_acc = round(sum(GC.get_metrics(r)["accuracy"] for r in geos) / len(geos), 1)
    else:
        avg_exp = avg_acc = 0
    c = st.columns(3)
    cc = apply_compare(avg_exp, cmp_mode, prev=avg_exp - 6, industry_avg=58.0)
    c[0].metric("平均曝光率", f"{avg_exp}%", f"{cc['delta']:+.1f} vs {cc['label']}")
    c[1].metric("平均信息准确率", f"{avg_acc}%")
    c[2].metric("GEO监测次数", len(geos))
    trend = sorted(geos, key=lambda r: r.get("created_at", ""))
    if trend:
        st.line_chart(pd.DataFrame([{"时间": r.get("created_at", "")[:10],
                                     "曝光率": GC.get_metrics(r)["exposure"]} for r in trend]).set_index("时间"))

# ── 5 渠道效果 ───────────────────────────────────────────────────────────────
with boards[4]:
    by_plat = {}
    for t in collects:
        by_plat[t.get("platform", "其他")] = by_plat.get(t.get("platform", "其他"), 0) + (t.get("result_count") or 1)
    c = st.columns(2)
    c[0].metric("采集任务", len(collects))
    c[1].metric("覆盖渠道", len(by_plat))
    if by_plat:
        st.bar_chart(pd.DataFrame({"采集量": by_plat}))

# ── 6 选品数据 ───────────────────────────────────────────────────────────────
with boards[5]:
    c = st.columns(2)
    c[0].metric("选品任务", len(selections))
    c[1].metric("最高综合分", max([s["score"] for s in selections], default=0))
    rows = []
    for s in selections:
        for r in (s["result"].get("recommendations", []) or [])[:3]:
            rows.append({"任务": s["name"], "推荐品类": r["name"], "评分": r["total"]})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.caption("暂无选品推荐数据。")

# ── 7 竞品情报 ───────────────────────────────────────────────────────────────
with boards[6]:
    monitoring = [c for c in comps if c["status"] == "正常监控"]
    c = st.columns(2)
    c[0].metric("监控竞品", len(comps))
    c[1].metric("监控中", len(monitoring))
    if comps:
        st.dataframe(pd.DataFrame([{"竞品": x["name"], "行业": x["industry"],
                                    "频率": x["frequency"], "状态": x["status"]} for x in comps]),
                     use_container_width=True, hide_index=True)

# ── 8 ROI价值看板 ────────────────────────────────────────────────────────────
with boards[7]:
    st.markdown("#### ROI 价值看板")
    content_eff = len(contents) * 1.5            # 内容效率（演示：每条折算工时价值）
    compliance_save = len([t for t in contents]) * 0.8  # 合规止损
    geo_value = round(sum(GC.get_metrics(r)["exposure"] for r in geos) / 10, 1) if geos else 0
    resp_eff = len([t for t in tickets if t["status"] == "已办结"])
    c = st.columns(4)
    c[0].metric("内容效率(折算人天)", f"{content_eff:.0f}")
    c[1].metric("合规止损(万元)", f"{compliance_save:.1f}")
    c[2].metric("GEO曝光价值", f"{geo_value}")
    c[3].metric("舆情响应办结", resp_eff)
    period = st.selectbox("汇报周期", ["本周", "本月", "本季"])
    st.caption(f"周期：{period}　·　ROI 指标为演示折算，正式版可对接真实成本与转化数据。")

# ── 9 自定义报表 ─────────────────────────────────────────────────────────────
with boards[8]:
    st.markdown("#### 自定义报表")
    METRICS_POOL = {
        "文案产量": len(contents), "合规通过率%": round(len([t for t in contents if t["status"] in ("已通过", "已归档")]) / max(1, len(contents)) * 100, 1),
        "舆情总量": len(sents), "高风险舆情": len([r for r in sents if r.get("risk_level", 1) >= 3]),
        "GEO监测次数": len(geos), "选品任务": len(selections), "监控竞品": len(comps),
        "待审批": len(A.list_requests("todo")), "处置工单": len(tickets),
    }
    picked = st.multiselect("选择报表指标", list(METRICS_POOL.keys()),
                            default=["文案产量", "舆情总量", "GEO监测次数"])
    sched = st.radio("定时推送", ["不推送", "每日", "每周", "每月"], horizontal=True)
    if picked:
        st.dataframe(pd.DataFrame([{"指标": k, "数值": METRICS_POOL[k]} for k in picked]),
                     use_container_width=True, hide_index=True)
    if st.button("💾 保存报表模板", type="primary"):
        st.session_state["_report_tpl"] = {"metrics": picked, "schedule": sched}
        if sched != "不推送":
            try:
                from db import messages as M
                from db.models import MSG_REPORT
                M.push(f"自定义报表已订阅（{sched}）", "报表将按周期推送至消息中心",
                       category=MSG_REPORT, level="info")
            except Exception:
                pass
        st.success(f"报表模板已保存，推送：{sched}")

st.divider()

# ── GEO 全局对比汇总（S4-2，管理层专属）──────────────────────────────────────
st.markdown("### 🌐 GEO 全局对比汇总（全公司）")
st.caption("全公司 GEO 复测效果评级分布，支持月度/季度整体复盘与团队考核。")
evaluated = [r for r in geos if (r.get("meta") or {}).get("effect_level")]
if len(geos) >= 2:
    # 自动两两对比同品牌最近两轮，统计评级分布
    by_brand = {}
    for r in geos:
        by_brand.setdefault(r["brand"], []).append(r)
    level_dist = {"优秀": 0, "良好": 0, "一般": 0, "无效": 0}
    rows = []
    for b, rs in by_brand.items():
        rs_sorted = sorted(rs, key=lambda x: x.get("created_at", ""))
        if len(rs_sorted) >= 2:
            rep = GC.evaluate(rs_sorted[-2], rs_sorted[-1])
            level_dist[rep["effect_level"]] += 1
            rows.append({"品牌": brands.get(b, {}).get("name", b),
                         "基准": rs_sorted[-2].get("created_at", "")[:10],
                         "本轮": rs_sorted[-1].get("created_at", "")[:10],
                         "平均提升%": rep["avg_effective_pct"], "效果评级": rep["effect_level"]})
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.bar_chart(pd.DataFrame({"评级分布": {k: v for k, v in level_dist.items() if v}}))
    else:
        st.info("暂无可对比的多轮 GEO 数据（需同品牌至少两轮监测）。")
else:
    st.info("暂无足够 GEO 数据生成全局对比（需至少两轮监测）。")
