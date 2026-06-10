"""GEO 复测与效果评估视图（嵌入 GEO 页的「复测评估」tab）。"""
import streamlit as st
import pandas as pd
from datetime import datetime
import config.geo_tasks as geo_tasks
from modules import geo_compare as GC
from utils.watermark import stamp_text_export

_LEVEL_COLOR = {"优秀": "#2E7D32", "良好": "#1E88E5", "一般": "#F9A825", "无效": "#C62828"}


def render(brand: str) -> None:
    st.caption("监测→优化→复测→验效→迭代全闭环：选择本轮与基准任务，自动计算指标提升、"
               "量化效果评级与趋势。")
    records = geo_tasks.list_records(brand_key=brand)
    if len(records) < 1:
        st.info("当前品牌暂无 GEO 监测记录。请先在「GEO 分析」运行至少一次监测。")
        return

    def _label(r):
        eff = (r.get("meta") or {}).get("effect_level")
        tag = f" · 已评估[{eff}]" if eff else ""
        return f"{r.get('created_at','')} · {r['period']}监测 · {r['region']}{tag}"

    c1, c2 = st.columns(2)
    with c1:
        cur_id = st.selectbox("本轮任务（当前）", [r["id"] for r in records],
                              format_func=lambda i: _label(next(r for r in records if r["id"] == i)),
                              key="gcv_cur")
    with c2:
        base_opts = [r["id"] for r in records if r["id"] != cur_id]
        if not base_opts:
            st.warning("暂无可作为对比基准的历史任务（至少需要 2 条监测记录）。")
            return
        base_id = st.selectbox("对比基准（历史）", base_opts,
                               format_func=lambda i: _label(next(r for r in records if r["id"] == i)),
                               key="gcv_base")

    cur_rec = next(r for r in records if r["id"] == cur_id)
    base_rec = next(r for r in records if r["id"] == base_id)
    report = GC.evaluate(base_rec, cur_rec)

    st.divider()
    b1, b2, b3 = st.columns(3)
    b1.metric("基准周期", base_rec.get("created_at", "—"))
    b2.metric("本轮周期", cur_rec.get("created_at", "—"))
    b3.metric("监测地域", cur_rec.get("region", "全国"))
    for w in report["warnings"]:
        st.warning("⚠️ " + w)

    st.markdown("#### 核心指标对比")
    tbl = []
    for row in report["rows"]:
        arrow = "🔺" if row["delta"] > 0 else ("🔻" if row["delta"] < 0 else "▪️")
        good = "✅" if row["effective_pct"] > 0 else ("⚠️" if row["effective_pct"] == 0 else "❌")
        tbl.append({"指标": row["label"], "基准值": f'{row["base"]}{row["unit"]}',
                    "当前值": f'{row["current"]}{row["unit"]}',
                    "提升绝对值": f'{arrow} {row["delta"]}{row["unit"]}',
                    "提升%": f'{row["pct"]}%', "效果": f'{good} {row["effective_pct"]}%'})
    st.dataframe(pd.DataFrame(tbl), use_container_width=True, hide_index=True)

    lc = _LEVEL_COLOR.get(report["effect_level"], "#9AA0A6")
    st.markdown("#### 综合效果评估")
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:14px;margin-bottom:8px">'
        f'<span style="background:{lc};color:#fff;padding:6px 18px;border-radius:20px;'
        f'font-size:18px;font-weight:700">{report["effect_level"]}</span>'
        f'<span style="font-size:14px;color:#5C4F42">核心指标平均提升：'
        f'<b>{report["avg_effective_pct"]}%</b></span></div>', unsafe_allow_html=True)
    st.info("📋 " + report["evaluate_desc"])
    st.markdown("**后续迭代优化建议**：" + report["optimize_suggest"])

    st.markdown("#### 长期趋势曲线")
    trend = sorted(records, key=lambda r: r.get("created_at", ""))
    df = pd.DataFrame([{"时间": r.get("created_at", "")[:16],
                        "曝光率": GC.get_metrics(r)["exposure"],
                        "信息准确率": GC.get_metrics(r)["accuracy"]} for r in trend]).set_index("时间")
    st.line_chart(df)

    st.markdown("#### 人工复盘批注")
    saved_note = (cur_rec.get("meta") or {}).get("note", "")
    note = st.text_area("落地总结 / 复盘记录（永久留痕，记入审计日志）", value=saved_note,
                        height=100, key="gcv_note")
    nc1, nc2 = st.columns([1, 1])
    with nc1:
        if st.button("💾 保存批注", type="primary", key="gcv_save"):
            geo_tasks.update_meta(cur_id, note=note, effect_level=report["effect_level"],
                                  base_id=base_id)
            try:
                from db.audit import log
                log("GEO复盘批注", f"task={cur_id}")
            except Exception:
                pass
            st.toast("批注已保存，效果评级已归档")
            st.rerun()
    with nc2:
        export = stamp_text_export(
            f"# GEO 优化前后对比 & 效果评估报告\n\n品牌：{brand}　基准：{base_rec.get('created_at')}"
            f"　本轮：{cur_rec.get('created_at')}\n\n效果评级：{report['effect_level']}"
            f"（{report['avg_effective_pct']}%）\n\n"
            + "\n".join(f"- {r['label']}：{r['base']}{r['unit']} → {r['current']}{r['unit']}"
                        f"（{r['pct']}%）" for r in report["rows"])
            + f"\n\n评估：{report['evaluate_desc']}\n建议：{report['optimize_suggest']}\n"
            + f"\n人工批注：{note or '（无）'}\n", title="GEO效果评估报告")
        st.download_button("📥 导出评估报告", export,
                           file_name=f"GEO效果评估_{brand}_{datetime.now():%Y%m%d}.md",
                           use_container_width=True, key="gcv_dl")

    st.divider()
    if st.button("🔁 基于本轮新建复测任务（自动以本轮为基准）", key="gcv_re"):
        meta = dict(cur_rec.get("meta") or {})
        meta["base_id"] = cur_id
        meta["metrics"] = GC.synth_metrics("re_" + cur_id, datetime.now().strftime("%Y-%m-%d %H:%M"))
        new_id = geo_tasks.add_record(brand, cur_rec["period"], cur_rec["region"], meta,
                                      summary=f"复测（基于 {cur_rec.get('created_at','')}）")
        st.success(f"已创建复测任务 {new_id}，并将本轮设为对比基准。")
        st.rerun()
