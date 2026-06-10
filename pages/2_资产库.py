"""G2 · 企业资产库 — 已审批归档内容的统一沉淀、检索与再编辑。"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import config.content_tasks as content_tasks
from prompts.content_generation_prompt import PLATFORM_GUIDES
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="资产库 — PinSight AI", page_icon="📦", layout="wide", initial_sidebar_state="expanded")
brand = render_sidebar()

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">企业资产库</h1>
  <p class="page-desc">已审批归档的内容统一沉淀于此，支持检索、筛选与一键再编辑</p>
</div>
""",
    unsafe_allow_html=True,
)

st.info("资产来源：在「内容工坊」将已通过的文案任务推进到「已归档」状态，即自动进入资产库。")

# ── 检索与筛选 ────────────────────────────────────────────────────────────────
fc1, fc2, fc3 = st.columns([2, 2, 2])
with fc1:
    kw = st.text_input("🔎 搜索（标题/正文关键词）", key="asset_search")
with fc2:
    plat = st.selectbox("按平台筛选", ["全部"] + list(PLATFORM_GUIDES.keys()), key="asset_plat")
with fc3:
    scope = st.radio("品牌范围", ["当前品牌", "全部品牌"], horizontal=True, key="asset_scope")

# 资产 = 已归档的文案任务
brand_filter = None if scope == "全部品牌" else brand
assets = content_tasks.list_tasks(
    brand_key=brand_filter, status="已归档",
    platform=None if plat == "全部" else plat,
)

# 关键词检索（标题 + 正文）
if kw and kw.strip():
    k = kw.strip().lower()
    assets = [a for a in assets if k in a.get("title", "").lower() or k in a.get("output", "").lower()]

st.caption(f"共 {len(assets)} 项资产")

if not assets:
    st.info("暂无归档资产。在「内容工坊」的文案任务列表中，将「已通过」任务点「→已归档」即可沉淀到此。")
else:
    for a in assets:
        with st.container(border=True):
            hc1, hc2 = st.columns([5, 1])
            with hc1:
                bname = BRAND_DISPLAY_NAMES.get(a.get("brand"), a.get("brand", ""))
                st.markdown(f"**📦 {a['title']}**　·　{bname}")
                st.caption(f"平台：{' / '.join(a.get('platforms', [])) or '—'}　|　归档时间：{a.get('updated_at', a.get('created_at',''))}")
            with hc2:
                if st.button("✏️ 再编辑", key=f"asset_edit_{a['id']}", use_container_width=True):
                    meta = a.get("meta", {})
                    # 构造内容工坊可识别的安全预填（仅含有效值）
                    prefill = {}
                    if meta.get("product_name"):
                        prefill["product_name"] = meta["product_name"]
                    if meta.get("selling_points"):
                        prefill["selling_points"] = meta["selling_points"]
                    if meta.get("goal"):
                        prefill["goal"] = meta["goal"]
                    if meta.get("tone_key"):
                        prefill["tone"] = meta["tone_key"]
                    prefill["word_limit"] = meta.get("word_limit") or "不限"
                    if meta.get("region"):
                        prefill["region"] = meta["region"]
                    if meta.get("platforms"):
                        prefill["platforms"] = meta["platforms"]
                    if meta.get("versions_per_platform"):
                        prefill["versions"] = meta["versions_per_platform"]
                    st.session_state["cw_prefill"] = prefill
                    st.switch_page("pages/4_内容工坊.py")
            with st.expander("查看资产内容", expanded=False):
                st.text_area("内容", value=a.get("output", ""), height=240,
                             key=f"asset_view_{a['id']}", disabled=True)
