"""S3-2 竞品情报仓库 — 主体管理、六维情报、对标报表、历史归档、异动预警。"""
import streamlit as st
import pandas as pd
import hashlib
from utils.sidebar import render
import config.competitors as CP
from config.brand_manager import INDUSTRY_OPTIONS
from db.models import COMPETITOR_DIMENSIONS

render()

from config.plan_features import require_feature
require_feature("competitor")

st.markdown('<div class="page-header"><h1>竞品情报仓库</h1>'
            '<p class="page-desc">常态化竞品监控：品牌/产品/舆情/GEO/内容/策略六维情报、'
            '综合对标、历史归档与异动预警。所有内容基于公开数据客观分析。</p></div>',
            unsafe_allow_html=True)

tab_list, tab_intel, tab_bench, tab_alert = st.tabs(
    ["🏷️ 竞品主体", "🔍 六维情报", "📊 综合对标", "🚨 异动预警"])

# ── 竞品主体管理 ─────────────────────────────────────────────────────────────
with tab_list:
    with st.expander("➕ 新增竞品", expanded=False):
        with st.form("cmp_new"):
            name = st.text_input("竞品品牌名称")
            c1, c2 = st.columns(2)
            industry = c1.selectbox("所属行业", INDUSTRY_OPTIONS)
            frequency = c2.selectbox("监控频率", CP.FREQUENCIES)
            categories = st.text_input("核心对标品类（逗号分隔）")
            channels = st.multiselect("监控渠道", CP.CHANNELS, default=["社交种草", "点评"])
            dimensions = st.multiselect("监控维度", COMPETITOR_DIMENSIONS, default=COMPETITOR_DIMENSIONS)
            alerts = st.multiselect("预警规则", CP.ALERT_RULES, default=["上新", "负面"])
            if st.form_submit_button("添加并开始监控", type="primary"):
                if name.strip():
                    CP.add(name, industry,
                           [x.strip() for x in categories.split(",") if x.strip()],
                           channels, frequency, dimensions, alerts)
                    st.success(f"已添加竞品「{name}」并生成首批情报")
                    st.rerun()
                else:
                    st.warning("请填写竞品名称")

    f = st.selectbox("状态", ["全部", "正常监控", "暂停", "已归档"], key="cmp_f")
    comps = CP.list_all(status=f)
    if not comps:
        st.info("暂无竞品。点击上方「新增竞品」开始常态化监控。")
    _sc = {"正常监控": "#2E7D32", "暂停": "#F9A825", "已归档": "#9C8E82"}
    for c in comps:
        with st.container(border=True):
            hc1, hc2 = st.columns([4, 2])
            with hc1:
                st.markdown(
                    f'**{c["name"]}**　<span style="background:{_sc.get(c["status"],"#999")};'
                    f'color:#fff;padding:1px 8px;border-radius:8px;font-size:11px">{c["status"]}</span>',
                    unsafe_allow_html=True)
                st.caption(f"{c['industry']} · {c['frequency']}监控 · 渠道 {','.join(c['channels']) or '—'} · "
                           f"维度 {len(c['dimensions'])} · 预警 {','.join(c['alert_rules']) or '—'}")
            with hc2:
                bc = st.columns(3)
                with bc[0]:
                    if c["status"] == "正常监控":
                        if st.button("暂停", key=f"ps_{c['id']}", use_container_width=True):
                            CP.set_status(c["id"], "暂停"); st.rerun()
                    else:
                        if st.button("恢复", key=f"rs_{c['id']}", use_container_width=True):
                            CP.set_status(c["id"], "正常监控"); st.rerun()
                with bc[1]:
                    if st.button("归档", key=f"ar_{c['id']}", use_container_width=True):
                        CP.set_status(c["id"], "已归档"); st.rerun()
                with bc[2]:
                    if st.button("删除", key=f"dl_{c['id']}", use_container_width=True):
                        CP.delete(c["id"]); st.rerun()

# ── 六维情报 ─────────────────────────────────────────────────────────────────
with tab_intel:
    comps = CP.list_all()
    if not comps:
        st.info("请先在「竞品主体」添加竞品。")
    else:
        sel = st.selectbox("选择竞品", [c["id"] for c in comps],
                           format_func=lambda i: next(c["name"] for c in comps if c["id"] == i))
        dtabs = st.tabs(COMPETITOR_DIMENSIONS)
        for dt, dim in zip(dtabs, COMPETITOR_DIMENSIONS):
            with dt:
                rows = CP.list_intel(sel, dimension=dim)
                if not rows:
                    st.caption("暂无该维度情报。")
                for r in rows:
                    flag = "🚨 " if r["is_alert"] else ""
                    st.markdown(f"{flag}{r['content']}")
                    st.caption(r["created_at"])

# ── 综合对标报表 ─────────────────────────────────────────────────────────────
with tab_bench:
    comps = CP.list_all()
    if len(comps) < 1:
        st.info("请先添加竞品。")
    else:
        def _m(cid, key):
            h = int(hashlib.md5((cid + key).encode()).hexdigest(), 16) % 100
            return h
        df = pd.DataFrame([{
            "竞品": c["name"],
            "品牌声量": _m(c["id"], "voice"),
            "口碑指数": _m(c["id"], "rep"),
            "GEO曝光%": _m(c["id"], "geo"),
            "上新活跃度": _m(c["id"], "new"),
        } for c in comps]).set_index("竞品")
        st.markdown("**多品牌横向对标**")
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df)
        st.caption("演示数据：基于公开信息客观研判，禁止编造或恶意抹黑。")

# ── 异动预警 ─────────────────────────────────────────────────────────────────
with tab_alert:
    comps = CP.list_all(status="正常监控")
    st.caption("演示：手动触发一条竞品异动预警（实际由系统按规则 7×24 自动监测）。")
    if not comps:
        st.info("暂无正常监控中的竞品。")
    for c in comps:
        cols = st.columns([2] + [1] * len(CP.ALERT_RULES))
        cols[0].markdown(f"**{c['name']}**")
        for i, rule in enumerate(CP.ALERT_RULES):
            with cols[i + 1]:
                if st.button(rule, key=f"al_{c['id']}_{rule}", use_container_width=True):
                    CP.trigger_alert(c["id"], c["name"], rule)
                    st.toast(f"已触发「{c['name']}·{rule}」异动预警")
                    st.rerun()
