"""登录会话管理 + 全局门控 + 侧边栏账号组件。

用法（在 main.py / app.py 中）：
    from auth.login import ensure_db, login_gate
    ensure_db()
    login_gate()          # 未登录则渲染登录页并 st.stop()
    pg = st.navigation([...]); pg.run()
"""
from __future__ import annotations
import streamlit as st

from auth.users import authenticate
from db.models import ROLE_ADMIN, ROLE_PLATFORM, ROLE_LABELS
import db.audit as audit

_SESSION_KEY = "auth"
_DB_READY = "_db_initialized"


def ensure_db():
    """首次运行初始化数据库（幂等，缓存避免重复建表）。"""
    if st.session_state.get(_DB_READY):
        return
    from db.init import init_db
    init_db()
    st.session_state[_DB_READY] = True


# ── 当前用户上下文 ───────────────────────────────────────────────────────────
def current_user() -> dict | None:
    return st.session_state.get(_SESSION_KEY)


def current_tenant_id():
    u = current_user()
    return u["tenant_id"] if u else None


def current_user_id():
    u = current_user()
    return u["id"] if u else None


def current_role():
    u = current_user()
    return u["role"] if u else None


def is_admin() -> bool:
    return current_role() == ROLE_ADMIN


def logout():
    u = current_user()
    if u:
        audit.log("登出", username=u["username"], tenant_id=u["tenant_id"], user_id=u["id"])
    st.session_state.pop(_SESSION_KEY, None)


# ── 登录页 ───────────────────────────────────────────────────────────────────
def _render_login_form():
    st.markdown(
        """
<div style="max-width:420px;margin:8vh auto 0;text-align:center">
  <div style="font-size:40px">🧠</div>
  <h1 style="font-family:'Noto Serif SC',serif;margin:6px 0 2px">PinSight AI</h1>
  <p style="color:#9C8E82;margin:0 0 18px">品觉 · 品牌智能工作台 · 登录</p>
</div>
""",
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        with st.form("login_form"):
            username = st.text_input("用户名", placeholder="admin")
            password = st.text_input("密码", type="password", placeholder="••••••")
            submitted = st.form_submit_button("登 录", type="primary", use_container_width=True)
        if submitted:
            user = authenticate(username, password)
            if user and user.get("role") == ROLE_PLATFORM:
                # 物理隔离：平台运营账号不得登录品牌端，只能走运营后台入口
                st.error("该账号为平台运营账号，请使用运营管理后台入口登录（与品牌端隔离）。")
            elif user:
                st.session_state[_SESSION_KEY] = user
                audit.log("登录", username=user["username"],
                          tenant_id=user["tenant_id"], user_id=user["id"])
                st.rerun()
            else:
                st.error("用户名或密码错误，或账号已被冻结")
        st.caption("默认管理员：admin / admin123（首次登录后请尽快修改密码）")


def login_gate():
    """未登录 → 渲染登录页并停止；已登录 → 放行。"""
    if current_user() is None:
        st.set_page_config(page_title="登录 — PinSight AI", page_icon="🔐", layout="centered")
        _render_login_form()
        st.stop()


# ── 侧边栏账号组件（在 render_sidebar 内调用）────────────────────────────────
def render_account_widget():
    u = current_user()
    if not u:
        return
    role_label = ROLE_LABELS.get(u["role"], u["role"])
    st.markdown(
        f'<div class="sidebar-section-label" style="margin-top:8px">账号</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="padding:2px 16px 6px;font-size:12px;color:var(--text-secondary,#5C4F42)">'
        f'👤 <b>{u["name"]}</b>（{role_label}）<br>'
        f'<span style="color:#9C8E82">{u["tenant_name"]}</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("退出登录", use_container_width=True, key="_logout_btn"):
        logout()
        st.rerun()
