"""智营AI · 运营管理后台入口（与品牌端 app.py 物理隔离的独立部署）。

本地启动：streamlit run admin_app.py --server.port 8502
云端：作为独立 Streamlit Cloud App，共享同一 Postgres 数据库。
"""
import streamlit as st
from auth.platform_login import ensure_db, platform_login_gate

ensure_db()
platform_login_gate()

_pages = [
    st.Page("admin_pages/1_租户管理.py",   title="租户管理",     icon="🏢", default=True),
    st.Page("admin_pages/2_大模型配置.py", title="大模型配置",   icon="🤖"),
    st.Page("admin_pages/3_Prompt中心.py", title="Prompt中心",   icon="🧩"),
    st.Page("admin_pages/4_公共资源库.py", title="公共资源库",   icon="📚"),
    st.Page("admin_pages/5_采集规则.py",   title="采集全局规则", icon="📡"),
    st.Page("admin_pages/6_系统配置.py",   title="系统全局配置", icon="⚙️"),
]
pg = st.navigation(_pages, position="hidden")
pg.run()
