"""G2 · GEO 批量创作视图（嵌入 GEO 页「批量创作」tab）。"""
import streamlit as st
import pandas as pd
from modules import geo_content_batch as GB
from modules.compliance_precheck import precheck
import config.geo_keywords as GK

_RISK_COLOR = {"高": "#C62828", "中": "#F9A825", "低": "#2E7D32"}


def render(brand: str) -> None:
    st.caption("选一批关键词，按平台模板批量生成内容草稿，自动做 SEO 埋词（标题加'地域+产品'、"
               "结尾插联系方式）。草稿落「内容工坊」，须经合规预检 + 人工复核 + 审批后方可使用。")

    # 关键词来源：优先用蒸馏带过来的，其次最近一批蒸馏词，否则手填
    prefill = st.session_state.get("gi_kw", "")
    if not prefill:
        batches = GK.list_batches(brand)
        if batches:
            rows = GK.list_keywords(brand, batches[0]["batch_id"])
            deal = [r["keyword"] for r in rows if r["kw_type"] == "成交词"][:8]
            prefill = "\n".join(deal)

    with st.expander("▶️ 批量生成草稿", expanded=True):
        kw_text = st.text_area("关键词组（每行一个，最多 30）", value=prefill, key="gb_kw", height=110,
                               placeholder="可从「关键词蒸馏」带入，或手动输入")
        c1, c2 = st.columns(2)
        product = c1.text_input("产品 / 服务", key="gb_product", placeholder="如：空调维修")
        region = c2.text_input("地域（SEO 前缀）", key="gb_region", placeholder="如：南京江宁")
        c3, c4 = st.columns(2)
        contact = c3.text_input("联系方式 / CTA", key="gb_contact", placeholder="如：400-xxx-xxxx")
        highlights = c4.text_input("卖点（逗号分隔）", key="gb_hl", placeholder="如：上门,厂家直销,3年质保")
        platforms = st.multiselect("生成平台", GB.PLATFORMS, default=GB.PLATFORMS)

        if st.button("🛠 批量生成草稿", type="primary"):
            kws = [k for k in kw_text.split("\n") if k.strip()]
            if not kws:
                st.warning("请至少输入一个关键词")
            elif not platforms:
                st.warning("请至少选择一个平台")
            else:
                drafts = GB.generate_batch(brand, kws, platforms, product, region, contact, highlights)
                st.session_state["_gb_drafts"] = drafts
                st.success(f"已生成 {len(drafts)} 条草稿（{len(kws)} 词 × {len(platforms)} 平台）")

    drafts = st.session_state.get("_gb_drafts")
    if not drafts:
        st.info("填写上方表单并「批量生成草稿」后，这里会显示草稿与合规预检结果。")
        return

    # ── 草稿清单 + 合规预检 ───────────────────────────────────────────────────
    st.markdown(f"#### 生成结果（{len(drafts)} 条）")
    checked = [{**d, "_pre": precheck(d["output"])} for d in drafts]
    high_n = sum(1 for d in checked if d["_pre"]["level"] == "高")
    c = st.columns(3)
    c[0].metric("草稿数", len(checked))
    c[1].metric("合规高风险", high_n)
    c[2].metric("可直接复核", len(checked) - high_n)
    if high_n:
        st.warning(f"⚠️ {high_n} 条命中绝对化用语等高风险，需修改后方可使用（已在表中标红）。")

    st.dataframe(pd.DataFrame([{
        "关键词": d["keyword"], "平台": d["platform"], "标题": d["title"],
        "合规": d["_pre"]["level"],
    } for d in checked]), use_container_width=True, hide_index=True)

    with st.expander("👀 预览草稿内容", expanded=False):
        for d in checked[:12]:
            lc = _RISK_COLOR.get(d["_pre"]["level"], "#9C8E82")
            st.markdown(f"**[{d['platform']}] {d['title']}**　"
                        f"<span style='color:{lc};font-size:12px'>合规{d['_pre']['level']}</span>",
                        unsafe_allow_html=True)
            st.markdown(f"<div style='background:#FDFAF5;border:1px solid #DDD4C4;border-radius:6px;"
                        f"padding:8px 12px;white-space:pre-wrap;font-size:13px'>{d['output']}</div>",
                        unsafe_allow_html=True)

    # ── 保存到内容工坊（走合规审批）──────────────────────────────────────────
    st.markdown("#### 保存与复核")
    st.caption("保存后草稿进入「内容工坊 → 文案任务列表」，在那里逐条人工复核、提交审批，"
               "通过后由你自行合规发布（系统不自动发布）。")
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("💾 保存全部草稿到内容工坊", type="primary"):
            n = GB.save_drafts(brand, drafts)
            try:
                from db.audit import log
                log("GEO批量创作", f"brand={brand} 草稿={n}")
            except Exception:
                pass
            st.session_state.pop("_gb_drafts", None)
            st.success(f"已保存 {n} 条草稿到内容工坊，请前往复核与提交审批")
            st.rerun()
    with cc2:
        st.page_link("pages/4_内容工坊.py", label="✍️ 去内容工坊复核 / 提交审批", icon="✍️")

    st.caption("⚠️ 内容须基于真实信息，严禁夸大宣传、刷量灌水；正式发布前必经人工复核。")
