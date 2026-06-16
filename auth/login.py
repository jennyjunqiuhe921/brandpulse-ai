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
    u = st.session_state.get(_SESSION_KEY)
    # 残缺/空登录态（空字典、缺 id 的字典）一律归一化为未登录，避免半残状态
    return u if (isinstance(u, dict) and u.get("id")) else None


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
        audit.log("登出", username=u.get("username", ""), tenant_id=u.get("tenant_id"), user_id=u.get("id"))
    st.session_state.pop(_SESSION_KEY, None)
    # 「粘性登出」：持续拒绝 cookie 自动恢复，直到用户**真正重新登录**才解除。
    # （旧的一次性标记在云端 sc.clear 不可靠时，会被残留 cookie 在下一轮 rerun 悄悄登回，
    #  造成"点了退出又被弹回登录态"的幽灵复活——粘性标记根治此问题。）
    st.session_state["_brand_logged_out"] = True


def do_hard_logout():
    """决定性登出（服务端）：清会话 + 粘性登出标记 + best-effort 清 cookie + rerun。

    rerun 后由 enforce_login()（每个页面顶部调用）把空登录态弹回登录页。
    不用 JS 跳转——它被 Streamlit 组件 iframe 沙箱的 allow-top-navigation 限制挡死。
    """
    for _k in ("auth", "platform_auth"):
        st.session_state.pop(_k, None)
    st.session_state["_brand_logged_out"] = True
    st.session_state["_platform_logged_out"] = True
    try:
        from auth import session_cookie as sc
        sc.clear("brand"); sc.clear("platform")
    except Exception:
        pass
    st.rerun()


# ── 登录页 ───────────────────────────────────────────────────────────────────
def _render_login_form():
    st.markdown(
        """
<style>
/* 登录页隐藏 Streamlit 默认 pages/ 自动导航与侧边栏（居中布局无需侧栏，避免泄露内部页面名）*/
[data-testid="stSidebarNav"], [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] { display: none !important; }
</style>
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
                # 真正登录成功 → 解除粘性登出，恢复 cookie 持久化能力
                st.session_state.pop("_brand_logged_out", None)
                st.session_state[_SESSION_KEY] = user
                audit.log("登录", username=user["username"],
                          tenant_id=user["tenant_id"], user_id=user["id"])
                st.rerun()
            else:
                st.error("用户名或密码错误，或账号已被冻结")
        st.caption("默认管理员：admin / admin123（首次登录后请尽快修改密码）")


def login_gate():
    """未登录 → 先尝试 cookie 恢复；仍未登录则渲染登录页并停止；已登录 → 放行。

    注意：此处只做 cookie **读取**（原生 st.context.cookies，不渲染组件），
    cookie 的**写入**在侧边栏（set_page_config 之后）由 session_cookie.ensure 完成。
    """
    # 粘性登出标记：只要为 True，就**持续**拒绝 cookie 自动恢复（不 pop），直到登录成功才清除。
    logged_out = st.session_state.get("_brand_logged_out", False)
    # 用 not 判断：同时兜住 None 和异常的空字典 {}（避免"能浏览但无退出按钮"的怪态）
    if not current_user() and not logged_out:
        try:
            from auth import session_cookie as sc
            from auth.users import get_user_by_id
            uid = sc.read_uid("brand")
            if uid:
                u = get_user_by_id(uid)
                if u and u.get("role") != ROLE_PLATFORM:
                    st.session_state[_SESSION_KEY] = u
        except Exception:
            pass
    if not current_user():
        st.set_page_config(page_title="登录 — PinSight AI", page_icon="🔐", layout="centered")
        if logged_out:
            # 主动登出：在登录页（set_page_config 之后）尽力清除 cookie；即便 clear 不生效，
            # 粘性标记也已挡住自动恢复，不会再被弹回登录态。
            try:
                from auth import session_cookie as sc
                sc.clear("brand")
            except Exception:
                pass
        _render_login_form()
        st.stop()


def enforce_login() -> None:
    """页面级登录强制（每个品牌页在 render_sidebar 顶部调用）。

    背景：观测到 app.py 的 login_gate 在某些多页路由下未能拦住空登录态（页面照常渲染，
    状态栏「操作人 —」、侧栏无账号区、退出按钮形同虚设）。此处在**每个页面**重做强制：
    先尝试 cookie 恢复（粘性登出时跳过），仍未登录则直接渲染登录页并 st.stop()。
    与 login_gate 的区别：不调用 set_page_config（页面已调用），避免重复设置报错。
    已登录时立即返回，几乎零开销。
    """
    if current_user():
        return
    logged_out = st.session_state.get("_brand_logged_out", False)
    if not logged_out:
        try:
            from auth import session_cookie as sc
            from auth.users import get_user_by_id
            uid = sc.read_uid("brand")
            if uid:
                u = get_user_by_id(uid)
                if u and u.get("role") != ROLE_PLATFORM:
                    st.session_state[_SESSION_KEY] = u
        except Exception:
            pass
    if not current_user():
        if logged_out:
            try:
                from auth import session_cookie as sc
                sc.clear("brand")
            except Exception:
                pass
        _render_login_form()
        st.stop()


# ── 侧边栏账号组件（在 render_sidebar 内调用）────────────────────────────────
def render_account_widget():
    u = current_user()
    if not u:
        return
    # 全部用 .get() 取字段：即便登录态字段残缺也绝不抛异常，保证「退出登录」按钮永远渲染。
    role_label = ROLE_LABELS.get(u.get("role", ""), u.get("role", "") or "用户")
    st.markdown(
        f'<div class="sidebar-section-label" style="margin-top:8px">账号</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="padding:2px 16px 6px;font-size:12px;color:var(--text-secondary,#5C4F42)">'
        f'👤 <b>{u.get("name") or u.get("username") or "当前用户"}</b>（{role_label}）<br>'
        f'<span style="color:#9C8E82">{u.get("tenant_name","")}</span></div>',
        unsafe_allow_html=True,
    )
    if st.button("退出登录", use_container_width=True, key="_logout_btn"):
        do_hard_logout()
