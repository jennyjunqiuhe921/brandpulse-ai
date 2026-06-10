"""S4-5 合规审查 & 审计台账（企业领导端）— 违规统计 + 防篡改审计日志 + 导出。"""
import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sidebar import render
from auth.login import is_admin
from db import audit
import config.content_tasks as content_tasks
import config.sentiment_tasks as sentiment_tasks
from db import tickets as TK
from utils.watermark import stamp_text_export

render()

st.markdown('<div class="page-header"><h1>合规审查 & 审计台账</h1>'
            '<p class="page-desc">全链路操作审计（只增不改、防篡改）+ 合规风险统计，支持按监管格式导出。</p>'
            '</div>', unsafe_allow_html=True)

if not is_admin():
    st.warning("合规审计台账面向企业领导/法务/内审。")
    st.stop()

tab1, tab2 = st.tabs(["📋 审计台账", "🛡️ 合规风险统计"])

with tab1:
    actions = ["全部"] + audit.distinct_actions()
    c1, c2 = st.columns([3, 1])
    act = c1.selectbox("操作类型筛选", actions)
    logs = audit.list_logs(action=act)
    c2.metric("记录数", len(logs))
    if not logs:
        st.info("暂无审计记录。系统会在审批、复盘、配置变更等关键操作时自动记录。")
    else:
        df = pd.DataFrame(logs).rename(
            columns={"ts": "时间", "username": "操作人", "action": "操作", "target": "对象"})
        st.dataframe(df, use_container_width=True, hide_index=True)
        export = stamp_text_export(
            "# 审计台账导出\n\n| 时间 | 操作人 | 操作 | 对象 |\n|---|---|---|---|\n"
            + "\n".join(f"| {l['ts']} | {l['username']} | {l['action']} | {l['target']} |"
                        for l in logs), title="审计台账")
        st.download_button("📥 按监管格式导出（含水印）", export,
                           file_name=f"审计台账_{datetime.now():%Y%m%d}.md")
    st.caption("🔒 审计日志只增不改，永久留存，符合监管追溯要求。")

with tab2:
    contents = content_tasks.list_tasks(brand_key=None)
    sents = sentiment_tasks.list_records(brand_key=None)
    tickets = TK.list_tickets(brand=None)
    high_risk_sent = [r for r in sents if r.get("risk_level", 1) >= 3]
    pending_content = [t for t in contents if t["status"] in ("草稿", "待审批")]

    c = st.columns(4)
    c[0].metric("内容总量", len(contents))
    c[1].metric("未过审内容", len(pending_content))
    c[2].metric("高风险舆情", len(high_risk_sent))
    c[3].metric("处置工单", len(tickets))

    st.markdown("#### 合规风险提示")
    if pending_content:
        st.warning(f"⚠️ 有 {len(pending_content)} 条内容未完成审批，禁止对外发布。")
    if high_risk_sent:
        st.error(f"🔴 有 {len(high_risk_sent)} 条 ≥3 级高风险舆情，请确认均已建单处置。")
    if not pending_content and not high_risk_sent:
        st.success("✅ 暂无突出合规风险项。")

    st.markdown("#### 企业私有合规词库")
    words = st.session_state.setdefault("_compliance_words",
                                        ["最", "第一", "国家级", "零风险", "永久"])
    st.write("当前禁用词：", "、".join(words))
    nw = st.text_input("新增禁用词")
    if st.button("加入词库") and nw.strip():
        words.append(nw.strip())
        audit.log("更新合规词库", f"新增禁用词:{nw.strip()}")
        st.rerun()
