"""G5 · GEO 区域竞争指数视图（嵌入 GEO 页「区域指数」tab）。"""
import streamlit as st
import pandas as pd
import config.geo_region as GR
from modules import geo_region_advice as RA


def render(brand: str) -> None:
    st.caption("监测品牌在各省份、5 大 AI 平台的提及率 → 可调权重加权为「区域竞争指数」，"
               "对比竞品、看分省排名与趋势，并给出 AI 分省优化建议。合规：纯监测分析，不刷量。")

    with st.expander("▶️ 运行区域监测", expanded=not GR.list_rounds(brand)):
        provinces = st.multiselect("监测省份", GR.PROVINCES, default=GR.PROVINCES[:8])
        competitors = st.text_input("竞品（逗号分隔，最多 2 个）", placeholder="如：奈雪的茶, 茶百道")
        st.caption(f"将检测 {len(provinces)} 省 × {len(GR.PLATFORMS)} 平台："
                   + " · ".join(GR.PLATFORMS))
        if st.button("🚀 开始区域监测", type="primary"):
            if not provinces:
                st.warning("请至少选择一个省份")
            else:
                comps = [c.strip() for c in competitors.replace("，", ",").split(",") if c.strip()]
                GR.run_check(brand, provinces, comps)
                try:
                    from db.audit import log
                    log("GEO区域监测", f"brand={brand} 省{len(provinces)} 竞品{len(comps)}")
                except Exception:
                    pass
                st.success("区域监测完成")
                st.rerun()

    rounds = GR.list_rounds(brand)
    if not rounds:
        st.info("暂无区域监测记录。展开上方运行一轮即可生成区域竞争指数看板。")
        return

    rid = st.selectbox("监测轮次", [r["round_id"] for r in rounds],
                       format_func=lambda i: next(f"{r['checked_at']}（{i}）" for r in rounds if r["round_id"] == i))

    # 权重调整（G5-1）
    with st.expander("⚖️ 调整平台权重（重新计算综合指数）"):
        weights = {}
        cols = st.columns(len(GR.PLATFORMS))
        for i, pf in enumerate(GR.PLATFORMS):
            weights[pf] = cols[i].number_input(pf, 0.0, 1.0, GR.DEFAULT_WEIGHTS[pf], 0.05, key=f"w_{pf}")
        st.caption("权重自动归一化，无需手动凑成 1。")

    stats = GR.stats(brand, rid, weights if any(weights.values()) else None)

    # 核心指标
    c = st.columns(3)
    c[0].metric("全国平均竞争指数", stats["national_avg"])
    c[1].metric("监测省份", len(stats["own"]))
    c[2].metric("对标竞品", "、".join(stats["competitors"]) or "—")

    # G5-2 分省竞争指数排名（条形榜，地图后置）
    st.markdown("#### 分省区域竞争指数（排名）")
    rank_df = pd.DataFrame({"竞争指数": dict(stats["ranking"])})
    st.bar_chart(rank_df)

    # G5-3 竞品分省对比
    if stats["competitors"]:
        st.markdown(f"#### 己方 vs {stats['competitors'][0]}（分省对比）")
        c0 = stats["competitors"][0]
        rows = []
        for prov, idx in stats["ranking"]:
            g = stats["gap"].get(prov, 0)
            rows.append({"省份": prov, "己方指数": idx, f"{c0}指数": stats["comp_idx"][c0].get(prov, 0),
                         "差距": g, "态势": "✅领先" if g >= 0 else "⚠️落后"})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # 趋势
    tr = GR.trend(brand, weights if any(weights.values()) else None)
    if len(tr) >= 2:
        st.markdown("#### 全国均值趋势")
        st.line_chart(pd.DataFrame(tr).set_index("时间"))

    # G5-5 AI 分省优化建议
    st.markdown("#### 🤖 AI 分省优化建议")
    industry = st.radio("行业", ["茶饮", "餐饮"], horizontal=True, key="rg_ind")
    if st.button("生成 AI 分省建议"):
        st.session_state["_rg_advice"] = RA.advise(stats, industry)
    adv = st.session_state.get("_rg_advice")
    if adv:
        st.markdown(f'<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-radius:8px;'
                    f'padding:12px;white-space:pre-wrap;font-size:13px">{adv["text"]}</div>',
                    unsafe_allow_html=True)
    st.caption("演示数据：区域提及率为模拟，己方随监测轮次走高。接真实 5 平台 API 后为实测。")
