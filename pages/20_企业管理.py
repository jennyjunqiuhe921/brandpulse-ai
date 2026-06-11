"""S4-3/S4-4/S4-6 企业管理（企业领导端）— 全员任务总览 / 组织架构 / 企业设置。"""
import streamlit as st
import pandas as pd
from utils.sidebar import render
from auth.login import is_admin, current_tenant_id
from db import audit
import config.content_tasks as content_tasks
import config.geo_tasks as geo_tasks
import config.sentiment_tasks as sentiment_tasks
import config.selection_tasks as selection_tasks
from auth import users as U
from db.models import ROLE_LABELS

render()

st.markdown('<div class="page-header"><h1>企业管理</h1>'
            '<p class="page-desc">全员任务总览（只读）· 组织架构与权限 · 企业系统设置。</p>'
            '</div>', unsafe_allow_html=True)

if not is_admin():
    st.warning("企业管理面向企业领导/管理层。")
    st.stop()

tab1, tab2, tab3, tab4 = st.tabs(["📂 全员任务总览", "🏢 组织架构", "⚙️ 企业设置", "📦 套餐权益"])

# ── S4-4 各模块管理视角：企业级任务列表（只读全员）──────────────────────────────
with tab1:
    st.caption("企业级只读视图：汇总全公司各模块任务，供管理层抽检与方案终审。")
    module = st.selectbox("模块", ["文案", "GEO", "舆情", "选品"])
    if module == "文案":
        rows = [{"标题": t["title"], "品牌": t["brand"], "状态": t["status"],
                 "优先级": t.get("priority", "普通"), "创建": t.get("created_at", "")}
                for t in content_tasks.list_tasks(brand_key=None)]
    elif module == "GEO":
        rows = [{"周期": t["period"], "品牌": t["brand"], "地域": t["region"],
                 "状态": t["status"], "创建": t.get("created_at", "")}
                for t in geo_tasks.list_records(brand_key=None)]
    elif module == "舆情":
        rows = [{"摘要": (t.get("summary") or "")[:30], "品牌": t["brand"],
                 "风险等级": t.get("risk_level", 1), "来源": t.get("source", ""),
                 "创建": t.get("created_at", "")}
                for t in sentiment_tasks.list_records(brand_key=None)]
    else:
        rows = [{"任务": t["name"], "品牌": t["brand"], "行业": t["industry"],
                 "评分": t["score"], "状态": t["status"], "创建": t.get("created_at", "")}
                for t in selection_tasks.list_tasks(brand=None)]
    st.metric(f"{module}任务总数", len(rows))
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info(f"暂无{module}任务。")

# ── S4-3 组织架构与账号权限 ──────────────────────────────────────────────────
with tab2:
    st.caption("部门/门店/子品牌架构（集团版）。账号增删改密请用「账号管理」。")
    tid = current_tenant_id()
    users = U.list_users(tid)
    # 演示：部门归属存于会话
    depts = st.session_state.setdefault("_dept_map", {})
    st.markdown("**成员与部门**")
    rows = []
    for u in users:
        d = depts.get(u["username"], "未分配")
        rows.append({"账号": u["username"], "姓名": u.get("name", ""),
                     "角色": ROLE_LABELS.get(u.get("role", ""), u.get("role", "")),
                     "部门": d, "状态": u.get("status", "")})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    with st.expander("➕ 维护部门归属"):
        unames = [u["username"] for u in users]
        who = st.selectbox("成员", unames)
        dept = st.text_input("部门 / 门店 / 子品牌", placeholder="如：华东大区 / 旗舰店")
        if st.button("保存归属") and dept.strip():
            depts[who] = dept.strip()
            audit.log("组织架构调整", f"{who}→{dept.strip()}")
            st.success("已更新")
            st.rerun()
    st.page_link("pages/5_账号管理.py", label="👥 前往账号管理（增删账号/改密/冻结）", icon="👥")

# ── S4-6 企业系统设置 ────────────────────────────────────────────────────────
with tab3:
    st.caption("企业信息、Logo、消息渠道与资产密级策略。")
    cfg = st.session_state.setdefault("_ent_cfg", {
        "name": "演示企业", "industry": "新式茶饮", "logo": "",
        "channels": ["站内消息"], "secrecy_default": "内部"})
    cfg["name"] = st.text_input("企业名称", value=cfg["name"])
    cfg["industry"] = st.text_input("所属行业", value=cfg["industry"])
    cfg["channels"] = st.multiselect("消息推送渠道", ["站内消息", "邮件", "短信", "企业微信"],
                                     default=cfg["channels"])
    st.markdown("**资产密级策略（S4-6）**")
    cfg["secrecy_default"] = st.selectbox(
        "新建资产默认密级", ["公开", "内部", "机密"],
        index=["公开", "内部", "机密"].index(cfg["secrecy_default"]))
    st.caption("密级说明：公开=可跨品牌复用；内部=本企业可见；机密=指定人员可见。")
    if st.button("💾 保存企业设置", type="primary"):
        audit.log("企业设置变更", f"名称={cfg['name']} 默认密级={cfg['secrecy_default']}")
        st.success("企业设置已保存")

# ── S6-1 套餐权益矩阵 ────────────────────────────────────────────────────────
with tab4:
    from config.plan_features import current_plan, matrix_dataframe
    plan = current_plan()
    st.markdown(f"#### 当前套餐：**{plan}**")
    st.caption("✅ = 该套餐包含；— = 需升级。升级请联系平台运营。")
    st.dataframe(matrix_dataframe(), use_container_width=True, hide_index=True)
    st.info("基础采集 / 文案 / 简易GEO / 基础舆情 / 基础选品 为各套餐共有，不在上表门控范围。")
