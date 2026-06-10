"""账号管理（仅企业领导）— 新增/冻结员工账号、重置密码。"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
from auth.login import current_user, is_admin
from auth import users as user_svc
from db.models import ROLE_ADMIN, ROLE_STAFF, ROLE_LABELS
import db.audit as audit

st.set_page_config(page_title="账号管理 — PinSight AI", page_icon="👥", layout="wide",
                   initial_sidebar_state="expanded")
render_sidebar()

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">账号管理</h1>
  <p class="page-desc">新增、冻结企业员工账号，重置密码（仅企业领导可操作）</p>
</div>
""",
    unsafe_allow_html=True,
)

u = current_user()
if not is_admin():
    st.error("⛔ 仅企业领导可访问账号管理。")
    st.stop()

tenant_id = u["tenant_id"]

# ── 新增账号 ──────────────────────────────────────────────────────────────────
with st.expander("➕ 新增员工账号", expanded=False):
    with st.form("create_user_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            new_username = st.text_input("用户名 *", placeholder="如：zhangsan")
            new_name = st.text_input("姓名", placeholder="如：张三")
        with c2:
            new_password = st.text_input("初始密码 *", type="password")
            new_role = st.selectbox("角色", [ROLE_STAFF, ROLE_ADMIN],
                                    format_func=lambda r: ROLE_LABELS[r])
        submitted = st.form_submit_button("创建账号", type="primary", use_container_width=True)
    if submitted:
        ok, msg = user_svc.create_user(tenant_id, new_username, new_password, new_name, new_role)
        if ok:
            audit.log("新增账号", target=new_username, tenant_id=tenant_id,
                      user_id=u["id"], username=u["username"])
            st.success(f"✅ 账号「{new_username}」已创建")
            st.rerun()
        else:
            st.error(msg)

st.markdown("---")

# ── 账号列表 ──────────────────────────────────────────────────────────────────
st.subheader("👥 企业账号列表")
rows = user_svc.list_users(tenant_id)
if not rows:
    st.info("暂无账号。")
else:
    for r in rows:
        with st.container(border=True):
            cc1, cc2, cc3 = st.columns([3, 2, 2])
            with cc1:
                badge = "🟢" if r["status"] == "active" else "🔴"
                st.markdown(f"**{badge} {r['name'] or r['username']}** · `{r['username']}`")
                st.caption(f"{ROLE_LABELS.get(r['role'], r['role'])} ｜ 最近登录：{r['last_login']}")
            with cc2:
                is_self = r["id"] == u["id"]
                if r["status"] == "active":
                    if st.button("冻结", key=f"freeze_{r['id']}", use_container_width=True,
                                 disabled=is_self, help="不能冻结自己" if is_self else None):
                        user_svc.set_status(r["id"], "frozen")
                        audit.log("冻结账号", target=r["username"], tenant_id=tenant_id,
                                  user_id=u["id"], username=u["username"])
                        st.rerun()
                else:
                    if st.button("解冻", key=f"unfreeze_{r['id']}", use_container_width=True):
                        user_svc.set_status(r["id"], "active")
                        st.rerun()
            with cc3:
                with st.popover("重置密码", use_container_width=True):
                    np = st.text_input("新密码", type="password", key=f"np_{r['id']}")
                    if st.button("确认重置", key=f"rp_{r['id']}"):
                        if user_svc.reset_password(r["id"], np):
                            audit.log("重置密码", target=r["username"], tenant_id=tenant_id,
                                      user_id=u["id"], username=u["username"])
                            st.success("已重置")
                        else:
                            st.error("重置失败（密码不能为空）")
