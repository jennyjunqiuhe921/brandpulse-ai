"""S5 运营端登录（与品牌端物理隔离）。

- 独立会话键 platform_auth（即便同浏览器也不与品牌端串号）
- 仅允许 platform_admin 角色登录
- 无注册 / 无第三方登录入口（PRD 2.8）
"""
from __future__ import annotations
import streamlit as st

from auth.users import authenticate
from db.models import ROLE_PLATFORM
import db.audit as audit

_SESSION_KEY = "platform_auth"
_DB_READY = "_db_initialized"


def ensure_db():
    if st.session_state.get(_DB_READY):
        return
    from db.init import init_db
    init_db()
    st.session_state[_DB_READY] = True


def current_user() -> dict | None:
    return st.session_state.get(_SESSION_KEY)


def logout():
    u = current_user()
    if u:
        audit.log("运营端登出", username=u["username"], user_id=u["id"])
    st.session_state.pop(_SESSION_KEY, None)


def _render_login_form():
    st.markdown(
        """
<div style="max-width:560px;margin:8vh auto 0;text-align:center">
  <div style="font-size:40px">🛰️</div>
  <h1 style="font-family:'Noto Serif SC',serif;margin:6px 0 2px;font-size:24px;line-height:1.3;white-space:nowrap">智营AI · 运营管理后台</h1>
  <p style="color:#9C8E82;margin:0 0 18px">平台运营专用入口 · 与品牌方系统物理隔离</p>
</div>
""",
        unsafe_allow_html=True,
    )
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        with st.form("platform_login_form"):
            username = st.text_input("运营账号", placeholder="platform")
            password = st.text_input("密码", type="password", placeholder="••••••")
            submitted = st.form_submit_button("登 录", type="primary", use_container_width=True)
        if submitted:
            user = authenticate(username, password)
            if user and user.get("role") == ROLE_PLATFORM:
                st.session_state[_SESSION_KEY] = user
                audit.log("运营端登录", username=user["username"], user_id=user["id"])
                st.rerun()
            elif user:
                st.error("该账号无运营后台权限（仅限平台管理员）")
            else:
                st.error("账号或密码错误，或账号已被冻结")
        st.caption("本入口无注册功能，账号由系统统一分配。演示账号：platform / platform123")


def platform_login_gate():
    if current_user() is None:
        st.set_page_config(page_title="运营后台登录 — 智营AI", page_icon="🛰️", layout="centered")
        _render_login_form()
        st.stop()


def render_account_widget():
    u = current_user()
    if not u:
        return
    st.markdown('<div class="sidebar-section-label" style="margin-top:8px">运营账号</div>',
                unsafe_allow_html=True)
    st.markdown(
        f'<div style="padding:2px 16px 6px;font-size:12px;color:#5C4F42">'
        f'🛰️ <b>{u["name"]}</b>（平台管理员）</div>', unsafe_allow_html=True)
    if st.button("退出登录", use_container_width=True, key="_plat_logout"):
        logout()
        st.rerun()
