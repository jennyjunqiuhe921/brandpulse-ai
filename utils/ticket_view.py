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

        open_tickets = [t for t in TK.list_tickets(brand=brand) if t["status"] != "已归档"]
        st.markdown(f"**进行中工单（{len(open_tickets)}）**　"
                    "<span style='font-size:12px;color:#9C8E82'>流转：待处理→处置中→待消影→待复盘→已归档</span>",
                    unsafe_allow_html=True)
        if not open_tickets:
            st.info("暂无进行中工单。")
        _lc = {4: "#C62828", 3: "#E64A19", 2: "#F9A825", 1: "#1E88E5", 0: "#607D8B"}
        _sc = {"待处理": "#9C8E82", "处置中": "#1E88E5", "待消影": "#B5860D", "待复盘": "#E64A19"}
        for t in open_tickets:
            color = _lc.get(t["level"], "#607D8B")
            sc = _sc.get(t["status"], "#607D8B")
            with st.container(border=True):
                st.markdown(
                    f'<span style="background:{color};color:#fff;padding:2px 10px;border-radius:10px;'
                    f'font-size:12px">{t["level_label"]} · 时效 {t["sla"]}</span>　'
                    f'<span style="background:{sc};color:#fff;padding:2px 10px;border-radius:10px;'
                    f'font-size:12px">{t["status"]}</span>　**{t["title"]}**', unsafe_allow_html=True)
                if t["segment_tags"]:
                    st.caption("🏷️ " + " · ".join(t["segment_tags"]))

                # 阶段一：处置（待处理/处置中）
                if t["status"] in ("待处理", "处置中"):
                    resp = st.text_area("处置话术 / 处理记录", value=t["response"],
                                        key=f"resp_{t['id']}", height=80)
                    bc1, bc2 = st.columns([1, 1])
                    with bc1:
                        if st.button("💾 保存话术", key=f"sv_{t['id']}"):
                            TK.update(t["id"], response=resp, status="处置中"); st.rerun()
                    with bc2:
                        if st.button("➡️ 处置完成，进入消影", key=f"toel_{t['id']}", type="primary"):
                            TK.update(t["id"], response=resp, status="待消影"); st.rerun()

                # 阶段二：消影（待消影）— D5-4
                elif t["status"] == "待消影":
                    st.markdown("**🩹 消除影响（消影）**")
                    m = st.selectbox("处置方式", TK.DISPOSAL_METHODS, key=f"dm_{t['id']}")
                    note = st.text_area("消影备注", key=f"eln_{t['id']}", height=68,
                                        placeholder="如：已在大众点评官方回复并引导私域，对方删除差评")
                    removed = st.checkbox("✅ 已消除影响（标记后停止该事件实时告警）", value=True, key=f"rm_{t['id']}")
                    if st.button("提交消影", key=f"elb_{t['id']}", type="primary"):
                        TK.eliminate(t["id"], m, note, removed)
                        st.toast("消影已记录，已停止该事件告警"); st.rerun()

                # 阶段三：复盘（待复盘）— D5-3，橙红强制
                elif t["status"] == "待复盘":
                    st.markdown("**🔁 事件复盘（橙红事件强制，复盘后归档）**")
                    from modules import review_assist as RA
                    src = next((r for r in records if r.get("id") == t["source_id"]), {})
                    if st.button("🤖 AI 生成根因建议并填充", key=f"ai_{t['id']}"):
                        st.session_state[f"rv_{t['id']}"] = RA.suggest(
                            src.get("summary", t["title"]), t["level"], t["response"])
                    sug = st.session_state.get(f"rv_{t['id']}", {})
                    rc = st.selectbox("事件根因分类", RA.ROOT_CAUSES,
                                      index=RA.ROOT_CAUSES.index(sug["root_cause"]) if sug.get("root_cause") in RA.ROOT_CAUSES else 0,
                                      key=f"rc_{t['id']}")
                    scope = st.selectbox("影响范围", RA.SCOPES,
                                         index=RA.SCOPES.index(sug["scope"]) if sug.get("scope") in RA.SCOPES else 0,
                                         key=f"scp_{t['id']}")
                    timeliness = st.text_input("处置及时性", value=sug.get("timeliness", ""), key=f"tl_{t['id']}")
                    conclusion = st.text_area("根因结论", value=sug.get("conclusion", ""), key=f"cc_{t['id']}", height=60)
                    actions = st.text_area("落地整改动作", value=sug.get("actions", ""), key=f"ac_{t['id']}", height=60)
                    if st.button("✅ 提交复盘并归档", key=f"rvb_{t['id']}", type="primary"):
                        if not (conclusion.strip() and actions.strip()):
                            st.warning("请填写根因结论与整改动作")
                        else:
                            TK.review(t["id"], {"root_cause": rc, "scope": scope, "timeliness": timeliness,
                                                "conclusion": conclusion, "actions": actions})
                            try:
                                from db.audit import log
                                log("舆情复盘归档", f"{t['title']} 根因={rc}")
                            except Exception:
                                pass
                            st.toast("复盘已提交，工单已归档并沉淀案例库"); st.rerun()

    with sub2:
        cases = TK.list_tickets(brand=brand, only_cases=True)
        st.caption("已复盘归档的橙红事件自动沉淀于此，支持检索复用、按月导出用于门店整改培训。")
        if not cases:
            st.info("暂无案例。橙红工单完成「消影 + 复盘归档」后自动沉淀于此。")
        for c in cases:
            rd = c.get("review_data") or {}
            with st.container(border=True):
                st.markdown(f"**{c['title']}** · {c['level_label']}　"
                            f"<span style='font-size:11px;color:#9C8E82'>归档 {c['closed_at']}</span>",
                            unsafe_allow_html=True)
                if c["segment_tags"]:
                    st.caption("🏷️ " + " · ".join(c["segment_tags"]))
                if c.get("disposal_method"):
                    st.markdown(f"**消影方式**：{c['disposal_method']}"
                                + (f" · {c['elimination_note']}" if c.get("elimination_note") else ""))
                if rd:
                    st.markdown(f"**复盘**：根因「{rd.get('root_cause','—')}」· 影响范围「{rd.get('scope','—')}」")
                    st.markdown(f"- 结论：{rd.get('conclusion','—')}")
                    st.markdown(f"- 整改：{rd.get('actions','—')}")
                else:
                    st.markdown(f"**处置话术**：{c['response'] or '（未填写）'}")
        if cases:
            import pandas as _pd
            from utils.watermark import stamp_text_export
            rows = []
            for c in cases:
                rd = c.get("review_data") or {}
                rows.append({"标题": c["title"], "等级": c["level_label"], "消影方式": c.get("disposal_method", ""),
                             "根因": rd.get("root_cause", ""), "影响范围": rd.get("scope", ""),
                             "整改动作": rd.get("actions", ""), "归档时间": c["closed_at"]})
            csv = _pd.DataFrame(rows).to_csv(index=False)
            st.download_button("📥 按月导出负面案例库（CSV，供门店整改培训）", csv,
                               file_name=f"负面案例库_{brand}.csv", use_container_width=True)

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
