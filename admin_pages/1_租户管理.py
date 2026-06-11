"""S5 2.2 租户管理（运营侧）。"""
import streamlit as st
import pandas as pd
from utils.admin_sidebar import render
from config import platform_store as PS

render()

st.markdown('<div class="page-header"><h1>租户管理</h1>'
            '<p class="page-desc">企业租户的开通/套餐/额度/冻结/注销与运营数据概览。</p>'
            '</div>', unsafe_allow_html=True)

PLANS = ["基础执行版", "标准管控版", "企业集团版"]

with st.expander("➕ 新增租户"):
    with st.form("new_tenant"):
        c1, c2 = st.columns(2)
        name = c1.text_input("租户名称")
        industry = c2.text_input("所属行业")
        c3, c4, c5 = st.columns(3)
        plan = c3.selectbox("订阅套餐", PLANS)
        max_users = c4.number_input("最大账号数", 1, 999, 10)
        ai_quota = c5.number_input("AI单日额度", 100, 100000, 1000, step=100)
        c6, c7 = st.columns(2)
        contact = c6.text_input("联系人")
        expire = c7.text_input("到期时间", placeholder="2027-06-30")
        if st.form_submit_button("开通租户", type="primary"):
            if name.strip():
                PS.create_tenant(name, industry, plan, max_users=int(max_users),
                                 ai_quota=int(ai_quota), contact=contact, expire_at=expire)
                st.success(f"已开通租户「{name}」")
                st.rerun()
            else:
                st.warning("请填写租户名称")

tenants = PS.list_tenants()
st.markdown(f"#### 全部租户（{len(tenants)}）")

_sc = {"正常": "#2E7D32", "冻结": "#F9A825", "已注销": "#9C8E82"}
for t in tenants:
    with st.container(border=True):
        c1, c2 = st.columns([4, 2])
        with c1:
            st.markdown(
                f'**{t["name"]}**　<span style="background:{_sc.get(t["status"],"#999")};'
                f'color:#fff;padding:1px 8px;border-radius:8px;font-size:11px">{t["status"]}</span>'
                f'　<span style="font-size:12px;color:#9C8E82">{t["plan"]}</span>',
                unsafe_allow_html=True)
            st.caption(f"{t['industry'] or '—'} · 账号 {t['user_count']}/{t['max_users']} · "
                       f"AI额度 {t['ai_daily_quota']}/日 · 已调用 {t['ai_calls']} · "
                       f"到期 {t['expire_at'] or '—'}")
        with c2:
            bc = st.columns(3)
            with bc[0]:
                if t["status"] == "正常":
                    if st.button("冻结", key=f"fz_{t['id']}", use_container_width=True):
                        PS.set_tenant_status(t["id"], "冻结"); st.rerun()
                else:
                    if st.button("启用", key=f"ac_{t['id']}", use_container_width=True):
                        PS.set_tenant_status(t["id"], "正常"); st.rerun()
            with bc[1]:
                with st.popover("套餐"):
                    np = st.selectbox("套餐", PLANS, index=PLANS.index(t["plan"]) if t["plan"] in PLANS else 0,
                                      key=f"pl_{t['id']}")
                    nq = st.number_input("AI额度", 100, 100000, t["ai_daily_quota"], step=100, key=f"q_{t['id']}")
                    if st.button("保存", key=f"sv_{t['id']}"):
                        PS.update_tenant(t["id"], plan=np, ai_daily_quota=int(nq)); st.rerun()
            with bc[2]:
                if st.button("注销", key=f"de_{t['id']}", use_container_width=True):
                    PS.set_tenant_status(t["id"], "已注销")
                    st.toast("已注销（数据归档保留 90 天）"); st.rerun()

st.divider()
st.markdown("#### 运营数据概览")
if tenants:
    st.dataframe(pd.DataFrame([{
        "租户": t["name"], "套餐": t["plan"], "状态": t["status"],
        "账号数": t["user_count"], "AI调用": t["ai_calls"],
    } for t in tenants]), use_container_width=True, hide_index=True)
