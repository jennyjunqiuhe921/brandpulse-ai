"""G1 · 个人工作台 — 待处理任务 / 最近记录 / 快捷入口。"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import config.content_tasks as content_tasks
import config.geo_tasks as geo_tasks
import config.sentiment_tasks as sentiment_tasks
import config.collect_tasks as collect_tasks
from config.brand_manager import load_all_brands
from config.settings import BRAND_DISPLAY_NAMES
from db import context as ctx
from db import approvals as A
from utils.ui import kanban_board, priority_tag

st.set_page_config(page_title="工作台 — PinSight AI", page_icon="🏠", layout="wide", initial_sidebar_state="expanded")
brand = render_sidebar()

# ── 角色个性化欢迎（S2-5：区分执行岗/审批岗）────────────────────────────────────
_role = ctx.user_role()
_role_label = {"enterprise_admin": "管理层", "market_staff": "执行岗", "platform_admin": "平台"}.get(_role, "")
st.markdown(
    f"""
<div class="page-header">
  <h1 class="page-title">工作台</h1>
  <p class="page-desc">你好，{ctx.user_name()}（{_role_label}）— 全局待办 · 任务看板 · 快捷入口，一站掌握品牌运营全貌</p>
</div>
""",
    unsafe_allow_html=True,
)

brand_name = BRAND_DISPLAY_NAMES.get(brand, brand)
st.text_input("当前品牌", value=brand_name, disabled=True)

# ── 我的品牌（手机端无需展开侧边栏即可查看/切换）──────────────────────────────
st.subheader("🏷️ 我的品牌")
st.caption("点击卡片即可切换当前分析品牌（与侧边栏同步）")


def _switch_brand(bid: str):
    # 写入跨页持久化的真相源 brand_perm（侧边栏据此同步 radio）
    st.session_state["brand_perm"] = bid
    st.session_state["brand_widget"] = bid


_brands_all = load_all_brands()
if not _brands_all:
    st.info("还没有品牌，请到「品牌管理」新增。")
else:
    _bcols = st.columns(2)
    for _i, (_bid, _bdata) in enumerate(_brands_all.items()):
        _is_cur = _bid == brand
        _label = ("✅ " if _is_cur else "🏷️ ") + _bdata.get("name", _bid)
        with _bcols[_i % 2]:
            st.button(_label, key=f"wb_brand_{_bid}", on_click=_switch_brand,
                      args=(_bid,), disabled=_is_cur, use_container_width=True)

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
if high_risk:
    st.error(f"🔴 有 {len(high_risk)} 条 ≥4 级高风险舆情，建议优先处置")

# ── 角色个性化待办（审批岗 vs 执行岗）──────────────────────────────────────────
if _role == "enterprise_admin":
    _todo = A.list_requests("todo")
    if _todo:
        st.error(f"🗂️ 有 {len(_todo)} 项审批待你处理")
        st.page_link("pages/11_审批中心.py", label="前往审批中心", icon="🗂️")
else:
    _mine = [r for r in A.list_requests("mine") if r["status"] == "已驳回"]
    if _mine:
        st.warning(f"📝 有 {len(_mine)} 项审批被驳回，需修改重提")
        st.page_link("pages/12_我的审批.py", label="前往我的审批", icon="📝")

# ── 全局任务聚合（S2-5：列表 / 看板双视图 + 超时高亮）──────────────────────────
st.subheader("🗂️ 全局任务")
st.caption("聚合文案、采集等任务，统一展示优先级 · 标签 · 截止时间。超时任务自动高亮。")


def _agg_tasks():
    agg = []
    for t in all_tasks:
        agg.append({"id": t["id"], "title": "📝 " + (t.get("title") or "文案"),
                    "status": t["status"], "priority": t.get("priority", "普通"),
                    "task_tags": t.get("task_tags", []), "due_date": t.get("due_date", "")})
    for t in collect_tasks.list_tasks(brand_key=brand):
        agg.append({"id": t["id"], "title": "📡 采集·" + (t.get("platform") or ""),
                    "status": t["status"], "priority": t.get("priority", "普通"),
                    "task_tags": t.get("task_tags", []), "due_date": t.get("due_date", "")})
    return agg


_agg = _agg_tasks()
if not _agg:
    st.info("暂无任务。生成文案或创建采集任务后将在此聚合显示。")
else:
    view = st.radio("视图", ["📋 列表", "🗂️ 看板"], horizontal=True, key="wb_view")
    if view == "🗂️ 看板":
        kanban_board(_agg, columns=["草稿", "待审批", "已完成", "已通过", "已归档"])
    else:
        from utils.ui import _is_overdue
        for t in _agg[:20]:
            overdue = _is_overdue(t["due_date"]) if t["due_date"] else False
            due = (f"<span style='color:#C4391A'>⏰ {t['due_date']} 已超时</span>"
                   if overdue else (f"📅 {t['due_date']}" if t["due_date"] else ""))
            tags = " ".join(f"#{x}" for x in (t["task_tags"] or []))
            st.markdown(
                f"<div style='border:1px solid #DDD4C4;border-radius:8px;padding:8px 12px;"
                f"margin-bottom:6px;background:{'#FBE3E0' if overdue else '#FDFAF5'}'>"
                f"{priority_tag(t['priority'])}　{t['title']}　"
                f"<span style='color:#9C8E82;font-size:12px'>· {t['status']} · {tags} {due}</span>"
                f"</div>", unsafe_allow_html=True)

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
