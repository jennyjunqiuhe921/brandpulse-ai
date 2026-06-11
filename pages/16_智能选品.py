"""S3-1 商品智能选品 — 任务创建、综合评分、推荐清单、合规专项、配套物料、导出。"""
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sidebar import render
import config.selection_tasks as ST
from modules import selection_score as SC
from config.brand_manager import INDUSTRY_OPTIONS
from utils.watermark import stamp_text_export

brand = render()

from config.plan_features import require_feature
require_feature("selection_full")

st.markdown('<div class="page-header"><h1>商品智能选品</h1>'
            '<p class="page-desc">多维数据驱动的新品/迭代/区域款/竞品对标选品：综合评分 = '
            '市场热度30 + 口碑30 + 差异化20 + 合规20。</p></div>', unsafe_allow_html=True)

tab_new, tab_list = st.tabs(["🆕 新建选品任务", "📋 选品任务列表"])

with tab_new:
    with st.form("sel_new"):
        name = st.text_input("任务名称", placeholder="如：2026夏季新品选品")
        c1, c2 = st.columns(2)
        industry = c1.selectbox("所属行业", INDUSTRY_OPTIONS)
        goal = c2.selectbox("选品目标", ST.GOALS)
        categories = st.text_input("目标品类（逗号分隔）", placeholder="如：果茶, 奶茶, 气泡水")
        dimensions = st.multiselect("维度标签", ST.DIMENSIONS)
        c3, c4 = st.columns(2)
        regions = c3.multiselect("目标区域", ["全国", "华东", "华南", "华北", "西南", "下沉市场"])
        competitors = c4.text_input("对标竞品（逗号分隔，选填）", placeholder="如：奈雪, 茶百道")
        c5, c6, c7 = st.columns(3)
        priority = c5.selectbox("优先级", ["普通", "紧急", "低"])
        due = c6.text_input("截止时间", placeholder="2026-06-30")
        tags = c7.text_input("任务标签（逗号分隔）")
        submitted = st.form_submit_button("🚀 开始采集分析", type="primary")

    if submitted and name.strip():
        cats = [x.strip() for x in categories.split(",") if x.strip()]
        comps = [x.strip() for x in competitors.split(",") if x.strip()]
        with st.spinner("正在分析多维数据并评分…"):
            result = SC.analyze(cats, dimensions, comps, industry)
        tid = ST.add_task(brand, name, industry, cats, dimensions, regions, goal, comps,
                          result, priority=priority,
                          task_tags=[x.strip() for x in tags.split(",") if x.strip()],
                          due_date=due)
        st.success(f"分析完成！综合最高分 {result['top_score']}（{result['top_name']}）")
        st.session_state["_sel_last"] = tid

    # 展示最近分析结果
    last = st.session_state.get("_sel_last")
    if last:
        t = ST.get_task(last)
        if t:
            _render = t["result"]
            st.divider()
            st.markdown("### 推荐清单")
            df = pd.DataFrame([{
                "推荐品类": r["name"], "综合评分": r["total"], "适配": r["match"],
                "市场热度": r["heat"], "口碑": r["reputation"],
                "差异化": r["diff"], "合规": r["compliance"], "风险": r["risk"],
            } for r in _render["recommendations"]])
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.markdown("### 合规风险专项")
            st.warning("🛡️ " + _render["compliance_notes"])
            cc1, cc2 = st.columns(2)
            with cc1:
                st.page_link("pages/4_内容工坊.py", label="🎨 为头名生成配套营销物料", icon="🎨")
            with cc2:
                export = stamp_text_export(
                    f"# 选品分析报告 · {t['name']}\n\n行业：{t['industry']}　目标：{t['goal']}\n\n"
                    + "## 推荐清单\n"
                    + "\n".join(f"- {r['name']}：{r['total']}分（热度{r['heat']}/口碑{r['reputation']}"
                                f"/差异化{r['diff']}/合规{r['compliance']}）适配{r['match']} 风险{r['risk']}"
                                for r in _render["recommendations"])
                    + f"\n\n## 合规专项\n{_render['compliance_notes']}\n",
                    title="选品报告")
                st.download_button("📥 导出选品报告", export,
                                   file_name=f"选品报告_{t['name']}_{datetime.now():%Y%m%d}.md",
                                   use_container_width=True)

with tab_list:
    f = st.selectbox("状态筛选", ["全部", "已完成", "已归档"], key="sel_f")
    tasks = ST.list_tasks(brand=brand, status=f)
    if not tasks:
        st.info("暂无选品任务。在「新建选品任务」创建并分析后将在此显示。")
    _pic = {"紧急": "🔴", "普通": "🟡", "低": "⚪"}
    for t in tasks:
        with st.container(border=True):
            hc1, hc2 = st.columns([4, 1])
            with hc1:
                st.markdown(f"**{t['name']}** · `{t['status']}` · 综合评分 **{t['score']}**")
                st.caption(f"{_pic.get(t['priority'],'')} {t['priority']} · {t['industry']} · "
                           f"{t['goal']} · 品类 {','.join(t['categories']) or '—'} · {t['created_at']}")
            with hc2:
                if st.button("归档" if t["status"] != "已归档" else "取消归档",
                             key=f"arc_{t['id']}", use_container_width=True):
                    ST.set_status(t["id"], "已归档" if t["status"] != "已归档" else "已完成")
                    st.rerun()
                if st.button("删除", key=f"del_{t['id']}", use_container_width=True):
                    ST.delete_task(t["id"]); st.rerun()
            recs = t["result"].get("recommendations", [])
            if recs:
                with st.expander("查看推荐清单"):
                    st.dataframe(pd.DataFrame([{
                        "品类": r["name"], "评分": r["total"], "适配": r["match"], "风险": r["risk"],
                    } for r in recs]), use_container_width=True, hide_index=True)
