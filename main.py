"""BrandPulse AI — Streamlit entry point (st.navigation API)."""
import streamlit as st

pg = st.navigation(
    {
        "主要的": [
            st.Page("pages/1_🏠_Home.py",               title="家",       icon="🏠", default=True),
            st.Page("pages/2_🔍_Brand_Analysis.py",     title="品牌分析",  icon="🔍"),
            st.Page("pages/3_🌐_GEO_Analysis.py",       title="地理分析",  icon="🌐"),
            st.Page("pages/4_✍️_Content_Studio.py",     title="内容工作室", icon="✍️"),
            st.Page("pages/5_📊_Market_Positioning.py", title="市场定位",  icon="📊"),
            st.Page("pages/6_📡_数据采集.py",            title="数据采集",  icon="📡"),
            st.Page("pages/7_📰_Sentiment_Analysis.py", title="情感分析",  icon="📰"),
            st.Page("pages/8_🛡️_Compliance_Guard.py",  title="合规卫士",  icon="🛡️"),
            st.Page("pages/9_🔍_竞品分析.py",            title="竞品分析",  icon="🔍"),
        ]
    }
)
pg.run()
