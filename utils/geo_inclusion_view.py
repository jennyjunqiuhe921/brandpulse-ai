"""G4 · GEO 多平台收录监测看板视图（嵌入 GEO 页「收录监测」tab）。"""
import streamlit as st
import pandas as pd
import config.geo_inclusion as GI

# 平台展示用图标
_PF_ICON = {"DeepSeek": "🐳", "豆包": "🫛", "腾讯元宝": "💎", "通义千问": "🧭",
            "文心一言": "📖", "纳米AI": "🔬", "KIMI": "🌙", "智谱清言": "🧠"}


def render(brand: str) -> None:
    st.caption("监测品牌在各大国产 AI 平台回答中的「收录情况」：是否被提及/收录、命中名次、"
               "关键词占位率。持续优化后收录率应逐轮提升。")

    # ── 运行一轮收录检测 ──────────────────────────────────────────────────────
    with st.expander("▶️ 运行收录检测", expanded=not GI.list_rounds(brand)):
        kw_text = st.text_area(
            "监测关键词组（每行一个，最多 20 个）", key="gi_kw",
            placeholder="如：高端新式茶饮推荐\n奶盖茶哪个品牌好\n喜茶有什么联名",
            height=120)
        st.caption(f"将对每个关键词检测 {len(GI.PLATFORMS)} 个 AI 平台："
                   + " · ".join(GI.PLATFORMS))
        if st.button("🚀 开始检测收录", type="primary"):
            kws = [k for k in kw_text.split("\n") if k.strip()]
            if not kws:
                st.warning("请至少输入一个监测关键词")
            else:
                rid = GI.run_check(brand, kws)
                st.success(f"检测完成（{len(kws)} 词 × {len(GI.PLATFORMS)} 平台）")
                try:
                    from db.audit import log
                    log("GEO收录检测", f"brand={brand} 词数={len(kws)}")
                except Exception:
                    pass
                st.rerun()

    rounds = GI.list_rounds(brand)
    if not rounds:
        st.info("当前品牌暂无收录检测记录。展开上方「运行收录检测」跑一轮即可生成看板。")
        return

    # 轮次选择
    rid = st.selectbox("检测轮次", [r["round_id"] for r in rounds],
                       format_func=lambda i: next(
                           f"{r['checked_at']}（{r['round_id']}）" for r in rounds if r["round_id"] == i))
    stats = GI.round_stats(brand, rid)

    # ── 指标说明：区分"收录(覆盖广度)"与"名次(排名靠前)"两个维度 ───────────────
    st.info("📖 **两个维度别混淆**：**收录** = 品牌是否出现在 AI 对该问题的回答里（覆盖广度）；"
            "**命中名次** = 出现时排第几（越小越靠前）。下方矩阵可看每个问题在每个平台的具体表现。")

    # ── 顶部核心指标 ──────────────────────────────────────────────────────────
    c = st.columns(4)
    c[0].metric("整体收录率", f"{stats['overall_rate']}%",
                help="所有「问题×平台」检测中，品牌出现的比例（覆盖广度）")
    c[1].metric("前3名占比", f"{stats.get('top3_rate', 0)}%",
                help="被收录且排进前3名的比例（衡量排名是否靠前，与收录率是两回事）")
    c[2].metric("平均命中名次", stats["avg_position"] or "—",
                help="品牌被收录时的平均排名，数值越小越靠前")
    c[3].metric("检测轮次", len(rounds))

    # ── 8 大平台收录卡片（仿真实界面）────────────────────────────────────────
    st.markdown("#### 各 AI 平台收录")
    pp = stats["per_platform"]
    cols = st.columns(4)
    for i, pf in enumerate(GI.PLATFORMS):
        d = pp[pf]
        rate = d["rate"]
        color = "#2E7D32" if rate >= 50 else ("#F9A825" if rate >= 20 else "#9C8E82")
        with cols[i % 4]:
            st.markdown(
                f'<div style="border:1px solid #DDD4C4;border-radius:10px;padding:10px 12px;'
                f'margin-bottom:8px;background:#FDFAF5">'
                f'<div style="font-size:13px;color:#1C1510">{_PF_ICON.get(pf,"🔹")} {pf}</div>'
                f'<div style="font-size:22px;font-weight:700;color:{color}">{d["included"]}'
                f'<span style="font-size:12px;color:#9C8E82">/{d["total"]} 收录</span></div>'
                f'<div style="font-size:11px;color:{color}">收录率 {rate}%</div></div>',
                unsafe_allow_html=True)

    # ── 各平台收录率柱状图 + 趋势曲线 ────────────────────────────────────────
    cc1, cc2 = st.columns(2)
    with cc1:
        st.markdown("**各平台收录率（%）**")
        df_pf = pd.DataFrame({"收录率": {pf: pp[pf]["rate"] for pf in GI.PLATFORMS}})
        st.bar_chart(df_pf)
    with cc2:
        st.markdown("**整体收录率趋势**")
        tr = GI.trend(brand)
        if len(tr) >= 1:
            st.line_chart(pd.DataFrame(tr).set_index("time"))
        else:
            st.caption("多跑几轮后显示趋势。")

    # ── 问题 × 平台 收录矩阵（逐格：是否收录 + 命中名次）──────────────────────
    st.markdown("#### 问题 × 平台 收录矩阵")
    st.caption("每格 = 该问题在该平台的表现：**✅ 第N** = 被收录且排第 N 名；**—** = 未收录。"
               "最后一列「收录平台数」= 该问题被几个平台收录。")
    mx = GI.round_matrix(brand, rid)

    def _cell(inc: bool, pos: int) -> str:
        return (f"✅ 第{pos}" if pos else "✅") if inc else "—"

    matrix_rows = []
    for kw in mx.get("keywords", []):
        row = {"问题": kw}
        hit = 0
        for pf in mx["platforms"]:
            inc, pos = mx["cells"][kw][pf]
            row[f'{_PF_ICON.get(pf, "")}{pf}'] = _cell(inc, pos)
            if inc:
                hit += 1
        row["收录平台数"] = f'{hit}/{len(mx["platforms"])}'
        matrix_rows.append(row)
    st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True, hide_index=True)

    st.caption("演示数据：收录情况为模拟生成，持续检测轮次越多收录率越高。接入真实 AI 平台 "
               "API 后替换为实测。所有内容优化须基于真实信息，严禁刷量灌水。")
