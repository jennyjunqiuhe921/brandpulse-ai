"""G1 · 个人工作台 — 待处理任务 / 最近记录 / 快捷入口。"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import config.content_tasks as content_tasks
import config.geo_tasks as geo_tasks
import config.sentiment_tasks as sentiment_tasks
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="工作台 — PinSight AI", page_icon="🏠", layout="wide")
brand = render_sidebar()

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">工作台</h1>
  <p class="page-desc">待处理任务 · 最近记录 · 快捷入口，一站掌握品牌运营全貌</p>
</div>
""",
    unsafe_allow_html=True,
)

brand_name = BRAND_DISPLAY_NAMES.get(brand, brand)
st.text_input("当前品牌", value=brand_name, disabled=True)

# ── 待处理任务 ────────────────────────────────────────────────────────────────
all_tasks = content_tasks.list_tasks(brand_key=brand)
pending_review = [t for t in all_tasks if t["status"] == "待审批"]
drafts = [t for t in all_tasks if t["status"] == "草稿"]
approved = [t for t in all_tasks if t["status"] == "已通过"]
archived = [t for t in all_tasks if t["status"] == "已归档"]
sent_records = sentiment_tasks.list_records(brand_key=brand)
high_risk = [r for r in sent_records if r.get("risk_level", 1) >= 4]
geo_records = geo_tasks.list_records(brand_key=brand)

st.subheader("📋 待处理任务")
m1, m2, m3, m4 = st.columns(4)
m1.metric("待审批文案", f"{len(pending_review)} 条")
m2.metric("草稿文案", f"{len(drafts)} 条")
m3.metric("高风险舆情", f"{len(high_risk)} 条")
m4.metric("已归档资产", f"{len(archived)} 条")

if pending_review:
    st.warning(f"⚠️ 有 {len(pending_review)} 条文案待审批，请尽快处理")
    for t in pending_review[:5]:
        st.markdown(f"- 📝 **{t['title']}** · {' / '.join(t.get('platforms', []))} · 创建于 {t.get('created_at','')}")
if high_risk:
    st.error(f"🔴 有 {len(high_risk)} 条 ≥4 级高风险舆情，建议优先处置")

# ── 最近生成记录 ──────────────────────────────────────────────────────────────
st.subheader("🕒 最近生成记录（最近 5 条）")
if not all_tasks:
    st.info("暂无文案记录。前往「内容工坊」生成内容并保存为任务后，这里会显示最近记录。")
else:
    _badge = {"草稿": "📝", "待审批": "⏳", "已通过": "✅", "已归档": "📦"}
    for t in all_tasks[:5]:
        with st.container(border=True):
            st.markdown(f"**{_badge.get(t['status'],'•')} {t['title']}** · `{t['status']}`")
            st.caption(f"平台：{' / '.join(t.get('platforms', [])) or '—'}　|　{t.get('created_at','')}")

# ── 快捷入口 ──────────────────────────────────────────────────────────────────
st.subheader("⚡ 快捷入口")
q1, q2, q3, q4 = st.columns(4)
with q1:
    st.page_link("pages/4_内容工坊.py", label="✍️ 生成内容", use_container_width=True)
    st.page_link("pages/3_GEO.py", label="🌐 GEO 分析", use_container_width=True)
with q2:
    st.page_link("pages/7_舆情分析.py", label="📰 舆情分析", use_container_width=True)
    st.page_link("pages/6_数据采集.py", label="📡 数据采集", use_container_width=True)
with q3:
    st.page_link("pages/8_合规卫士.py", label="🛡️ 合规卫士", use_container_width=True)
    st.page_link("pages/9_合规自查.py", label="✅ 合规自查", use_container_width=True)
with q4:
    st.page_link("pages/2_资产库.py", label="📦 资产库", use_container_width=True)
    st.page_link("pages/0_品牌管理.py", label="🏢 品牌管理", use_container_width=True)

st.divider()
st.caption("📊 数据概览："
           f"GEO 监测 {len(geo_records)} 次 · 舆情分析 {len(sent_records)} 次 · "
           f"文案任务 {len(all_tasks)} 条（已通过 {len(approved)} · 已归档 {len(archived)}）")
