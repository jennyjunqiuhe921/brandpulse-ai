"""G3 · GEO 导出发布包视图（嵌入 GEO 页「发布包」tab）。合规版分发：人工发布。"""
import streamlit as st
import pandas as pd
from datetime import datetime
import config.geo_publish as GP
import config.content_tasks as ct


def render(brand: str) -> None:
    st.markdown(
        '<div style="background:#FFF7E6;border:1px solid #FFE0A3;border-left:3px solid #B5860D;'
        'border-radius:6px;padding:10px 14px;margin-bottom:12px;font-size:13px;color:#7A5500">'
        '🛡️ <b>合规说明</b>：本模块只做「发布清单 + 导出发布包」，由你<b>自行登录各平台手动发布</b>。'
        '系统<b>不提供</b>账号授权、自动投喂、批量发布等任何自动分发功能。发布须真实合规。</div>',
        unsafe_allow_html=True)

    # ── 1. 从内容工坊加入发布计划 ────────────────────────────────────────────
    st.markdown("#### ① 加入发布计划")
    geo_tasks = [t for t in ct.list_tasks(brand_key=brand)
                 if "GEO获客" in (t.get("task_tags") or [])]
    approved = [t for t in geo_tasks if t["status"] == "已通过"]
    others = [t for t in geo_tasks if t["status"] in ("草稿", "待审批")]

    if not geo_tasks:
        st.info("暂无 GEO 内容。请先在「✍️ 批量创作」生成草稿并保存到内容工坊。")
    else:
        st.caption(f"GEO 内容：已通过 {len(approved)} 条 · 草稿/待审批 {len(others)} 条。"
                   "建议仅发布**已通过审批**的内容。")
        pool = approved if approved else geo_tasks
        labels = {f"[{t['status']}] [{(t.get('platforms') or ['—'])[0]}] {t['title']}": t for t in pool}
        picked = st.multiselect("选择内容加入发布清单", list(labels.keys()))
        c1, c2 = st.columns(2)
        plan_time = c1.text_input("计划发布时间", placeholder="如：2026-06-15 上午")
        if not approved:
            c2.warning("当前无已通过内容，加入的是草稿，请发布前务必完成审批。")
        if st.button("➕ 加入发布清单", type="primary"):
            if picked:
                n = GP.add_items(brand, [labels[k] for k in picked], plan_time)
                try:
                    from db.audit import log
                    log("GEO加入发布清单", f"brand={brand} 条数={n}")
                except Exception:
                    pass
                st.success(f"已加入 {n} 条到发布清单")
                st.rerun()
            else:
                st.warning("请先选择内容")

    # ── 2. 发布清单 ──────────────────────────────────────────────────────────
    st.markdown("#### ② 发布清单")
    items = GP.list_items(brand)
    if not items:
        st.info("发布清单为空。")
    else:
        pending = [i for i in items if i["status"] == "待发布"]
        done = [i for i in items if i["status"] == "已发布"]
        cc = st.columns(3)
        cc[0].metric("总条目", len(items))
        cc[1].metric("待发布", len(pending))
        cc[2].metric("已发布", len(done))
        st.dataframe(pd.DataFrame([{
            "平台": i["platform"], "标题": i["title"], "关键词": i["keyword"],
            "计划时间": i["plan_time"] or "—", "状态": i["status"],
            "发布于": i["published_at"] or "—",
        } for i in items]), use_container_width=True, hide_index=True)

        # 逐条：标记已发布 / 删除
        with st.expander("管理清单条目（标记已发布 / 删除）"):
            for i in items:
                col1, col2, col3 = st.columns([5, 1, 1])
                col1.markdown(f"[{i['platform']}] {i['title']} · `{i['status']}`")
                with col2:
                    if i["status"] == "待发布" and st.button("已发布", key=f"pub_{i['id']}"):
                        GP.set_published(i["id"]); st.rerun()
                with col3:
                    if st.button("删除", key=f"pdel_{i['id']}"):
                        GP.delete_item(i["id"]); st.rerun()

        # ── 3. 导出发布包 ────────────────────────────────────────────────────
        st.markdown("#### ③ 导出发布包（人工发布）")
        scope = st.radio("导出范围", ["仅待发布", "全部"], horizontal=True)
        export_items = pending if scope == "仅待发布" else items
        if export_items:
            pkg = GP.export_package(brand, export_items)
            st.download_button(
                f"📥 导出发布包（{len(export_items)} 条，含水印）", pkg,
                file_name=f"GEO发布包_{brand}_{datetime.now():%Y%m%d}.md",
                use_container_width=True)
            st.caption("导出后由你自行登录各平台手动发布；发布完成回此标记「已发布」。")
        else:
            st.caption("当前范围无可导出条目。")

        # ── 4. 回填收录联动 G4 ───────────────────────────────────────────────
        if done:
            st.markdown("#### ④ 发布后验收")
            st.caption("已发布内容可把其关键词带入「📡 收录监测」，过段时间检测是否被 AI 平台收录。")
            if st.button("📡 把已发布关键词带入收录监测"):
                kws = sorted({i["keyword"] for i in done if i["keyword"]})
                if kws:
                    st.session_state["gi_kw"] = "\n".join(kws)
                    st.success(f"已带入 {len(kws)} 个词 → 请切到「📡 收录监测」运行检测")
                else:
                    st.info("已发布条目暂无关联关键词。")
