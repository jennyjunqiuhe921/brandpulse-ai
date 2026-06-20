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
    u = st.session_state.get(_SESSION_KEY)
    # 残缺/空登录态（空字典、缺 id 的字典）一律归一化为未登录
    return u if (isinstance(u, dict) and u.get("id")) else None


def logout():
    u = current_user()
    if u:
        audit.log("运营端登出", username=u.get("username", ""), user_id=u.get("id"))
    st.session_state.pop(_SESSION_KEY, None)
    # 「粘性登出」：持续拒绝 cookie 自动恢复，直到真正重新登录才解除（防残留 cookie 幽灵复活）。
    st.session_state["_platform_logged_out"] = True


def _render_login_form():
    st.markdown(
        """
<style>
/* 登录页隐藏 Streamlit 默认 pages/ 自动导航与侧边栏（避免运营端登录页泄露品牌端内部页面名）*/
[data-testid="stSidebarNav"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
</style>
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
                st.session_state.pop("_platform_logged_out", None)
                st.session_state[_SESSION_KEY] = user
                audit.log("运营端登录", username=user["username"], user_id=user["id"])
                st.rerun()
            elif user:
                st.error("该账号无运营后台权限（仅限平台管理员）")
            else:
                st.error("账号或密码错误，或账号已被冻结")
        st.caption("本入口无注册功能，账号由系统统一分配。")


def platform_login_gate():
    # 先尝试用持久化 cookie 恢复（仅平台管理员；只读 cookie 不渲染组件）
    logged_out = st.session_state.get("_platform_logged_out", False)
    # 用 not 判断：同时兜住 None 和异常空字典 {}
    if not current_user() and not logged_out:
        try:
            from auth import session_cookie as sc
            from auth.users import get_user_by_id
            uid = sc.read_uid("platform")
            if uid:
                u = get_user_by_id(uid)
                if u and u.get("role") == ROLE_PLATFORM:
                    st.session_state[_SESSION_KEY] = u
        except Exception:
            pass
    if not current_user():
        st.set_page_config(page_title="运营后台登录 — 智营AI", page_icon="🛰️", layout="centered")
        if logged_out:
            try:
                from auth import session_cookie as sc
                sc.clear("platform")
            except Exception:
                pass
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
        f'🛰️ <b>{u.get("name") or u.get("username") or "运营管理员"}</b>（平台管理员）</div>',
        unsafe_allow_html=True)
    if st.button("退出登录", use_container_width=True, key="_plat_logout"):
        from auth.login import do_hard_logout
        do_hard_logout()
