"""PinSight AI — Streamlit entry point (st.navigation)."""
import streamlit as st

# st.navigation replaces auto-discovered pages, giving us full control:
# - removes "应用程序" (app.py itself) from the sidebar
# - sets explicit Chinese page titles (prevents Chrome auto-translate)
# - controls display order

pg = st.navigation(
    [
        st.Page("pages/0_品牌管理.py",  title="品牌管理",  icon="🏢"),
        st.Page("pages/3_GEO.py",       title="GEO分析",   icon="🌐"),
        st.Page("pages/4_内容工坊.py",  title="内容工坊",  icon="✍️"),
        st.Page("pages/6_数据采集.py",  title="数据采集",  icon="📡"),
        st.Page("pages/7_舆情分析.py",  title="舆情分析",  icon="📰"),
        st.Page("pages/8_合规卫士.py",  title="合规卫士",  icon="🛡️"),
    ],
    position="hidden",   # hide Streamlit's built-in nav; we render nav in sidebar.py
)
pg.run()
