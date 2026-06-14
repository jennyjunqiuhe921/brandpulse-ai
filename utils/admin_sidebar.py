"""S5 运营后台侧边栏（独立于品牌端，无品牌选择器）。"""
import streamlit as st
from utils.sidebar import GLOBAL_CSS

_NAV = [
    ("🏢", "租户管理", "1_租户管理.py"),
    ("🤖", "大模型配置", "2_大模型配置.py"),
    ("🧩", "Prompt中心", "3_Prompt中心.py"),
    ("📚", "公共资源库", "4_公共资源库.py"),
    ("📡", "采集全局规则", "5_采集规则.py"),
    ("⚙️", "系统全局配置", "6_系统配置.py"),
]


def render() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(
            """
<div class="sidebar-logo">
  <div class="logo-icon">运</div>
  <div class="logo-name">智营AI · 运营后台</div>
  <div class="logo-sub">平台运营 · 多租户管理</div>
</div>
""", unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section-label">运营管理</div>', unsafe_allow_html=True)
        for icon, label, page in _NAV:
            st.page_link(f"admin_pages/{page}", label=f"{icon} {label}")
        try:
            from auth.platform_login import render_account_widget
            render_account_widget()
        except Exception:
            pass

        # 持久化登录 cookie：登录态在但 cookie 缺失 → 补写（刷新/重连后可恢复）
        try:
            from auth import session_cookie as sc
            from auth.platform_login import current_user as _pcu
            _u = _pcu()
            if _u:
                sc.ensure("platform", _u["id"])
        except Exception:
            pass
        st.markdown(
            '<div style="padding:0 16px 24px;font-size:10px;color:#9C8E82;line-height:1.6">'
            "运营后台与品牌方系统物理隔离，仅供平台运营人员使用。</div>",
            unsafe_allow_html=True)
