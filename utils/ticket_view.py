"""舆情工单与案例库视图（嵌入舆情中心的「工单处置」tab）。"""
import streamlit as st
import pandas as pd
import config.sentiment_tasks as sentiment_tasks
from db import tickets as TK
from db.models import TICKET_SLA, TICKET_LEVEL_LABEL

SEGMENTS = ["年轻女性", "学生党", "一线城市", "下沉市场", "到店场景",
            "外卖场景", "愤怒", "失望", "中性吐槽"]


def render(brand: str) -> None:
    from config.plan_features import require_feature
    require_feature("sentiment_ticket")
    sub1, sub2, sub3 = st.tabs(["🎫 工单处置", "📚 负面案例库", "📊 传播概览"])

    with sub1:
        records = sentiment_tasks.list_records(brand_key=brand)
        high = [r for r in records if r.get("risk_level", 1) >= 2]
        with st.expander("➕ 从高风险舆情新建工单", expanded=False):
            if not high:
                st.caption("当前品牌暂无 2 级及以上风险舆情。可手动建单：")
            opts = {f"[{r.get('risk_label','')}] {r.get('summary','')[:40]}": r for r in high}
            src_label = st.selectbox("关联舆情（可选）", ["— 手动建单 —"] + list(opts.keys()), key="tk_src")
            title = st.text_input("工单标题", key="tk_title",
                                  value=("" if src_label == "— 手动建单 —" else opts[src_label].get("summary", "")[:60]))
            c1, c2 = st.columns(2)
            level = c1.selectbox("处置分级", [4, 3, 2, 1, 0],
                                 format_func=lambda l: f"{TICKET_LEVEL_LABEL[l]} · 时效 {TICKET_SLA[l]}",
                                 key="tk_level")
            tags = c2.multiselect("细分标签（人群/地域/场景/情绪）", SEGMENTS, key="tk_tags")
            if st.button("建单", type="primary", key="tk_create"):
                if title.strip():
                    src = "" if src_label == "— 手动建单 —" else opts[src_label].get("id", "")
                    TK.create(brand, title, level, source_id=src, segment_tags=tags)
                    st.success("工单已创建")
                    st.rerun()
                else:
                    st.warning("请填写工单标题")

        open_tickets = [t for t in TK.list_tickets(brand=brand) if t["status"] != "已办结"]
        st.markdown(f"**待处理工单（{len(open_tickets)}）**")
        if not open_tickets:
            st.info("暂无待处理工单。")
        _lc = {4: "#C62828", 3: "#E64A19", 2: "#F9A825", 1: "#1E88E5", 0: "#607D8B"}
        for t in open_tickets:
            color = _lc.get(t["level"], "#607D8B")
            with st.container(border=True):
                st.markdown(
                    f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:10px;'
                    f'font-size:12px">{t["level_label"]} · 时效 {t["sla"]}</span>　**{t["title"]}**',
                    unsafe_allow_html=True)
                if t["segment_tags"]:
                    st.caption("🏷️ " + " · ".join(t["segment_tags"]))
                resp = st.text_area("处置话术 / 处理记录", value=t["response"],
                                    key=f"resp_{t['id']}", height=80)
                bc1, bc2, bc3 = st.columns([1, 1, 1])
                with bc1:
                    if st.button("保存", key=f"sv_{t['id']}"):
                        TK.update(t["id"], response=resp, status="处理中"); st.rerun()
                with bc2:
                    if st.button("✅ 办结", key=f"cl_{t['id']}"):
                        TK.update(t["id"], response=resp, status="已办结"); st.rerun()
                with bc3:
                    if st.button("📚 存为案例", key=f"cs_{t['id']}"):
                        TK.update(t["id"], response=resp, status="已办结", is_case=True)
                        st.toast("已沉淀至负面案例库"); st.rerun()

    with sub2:
        cases = TK.list_tickets(brand=brand, only_cases=True)
        if not cases:
            st.info("暂无案例。办结工单时点「存为案例」即可沉淀复用。")
        for c in cases:
            with st.container(border=True):
                st.markdown(f"**{c['title']}** · {c['level_label']}")
                if c["segment_tags"]:
                    st.caption("🏷️ " + " · ".join(c["segment_tags"]))
                st.markdown(f"**处置话术**：{c['response'] or '（未填写）'}")
                st.caption(f"办结于 {c['closed_at']}")

    with sub3:
        records = sentiment_tasks.list_records(brand_key=brand)
        if not records:
            st.info("暂无舆情数据。")
        else:
            st.markdown("**风险等级分布（传播概览）**")
            dist = {}
            for r in records:
                lv = r.get("risk_level", 1)
                dist[f"{lv}级"] = dist.get(f"{lv}级", 0) + 1
            st.bar_chart(pd.DataFrame({"数量": dist}))
            st.caption(f"共 {len(records)} 条舆情 · 工单 {len(TK.list_tickets(brand=brand))} 张 · "
                       f"案例 {len(TK.list_tickets(brand=brand, only_cases=True))} 条")
