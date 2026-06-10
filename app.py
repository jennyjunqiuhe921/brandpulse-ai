"""PinSight AI — Streamlit entry point (st.navigation + 登录门控)."""
import streamlit as st
from auth.login import ensure_db, login_gate, current_role
from db.models import ROLE_ADMIN

# 初始化数据库 + 登录门控（未登录则渲染登录页并 st.stop）
ensure_db()
login_gate()

_pages = [
    st.Page("pages/1_工作台.py",    title="工作台",    icon="🏠", default=True),
    st.Page("pages/0_品牌管理.py",  title="品牌管理",  icon="🏢"),
    st.Page("pages/3_GEO.py",       title="GEO",       icon="🌐"),
    st.Page("pages/4_内容工坊.py",  title="内容工坊",  icon="✍️"),
    st.Page("pages/2_资产库.py",    title="资产库",    icon="📦"),
    st.Page("pages/6_数据采集.py",  title="数据采集",  icon="📡"),
    st.Page("pages/7_舆情分析.py",  title="舆情中心",  icon="📰"),
    st.Page("pages/16_智能选品.py", title="智能选品",  icon="🛒"),
    st.Page("pages/17_竞品情报.py", title="竞品情报",  icon="🔭"),
    st.Page("pages/8_合规卫士.py",  title="合规卫士",  icon="🛡️"),
    st.Page("pages/9_合规自查.py",  title="合规自查",  icon="✅"),
    st.Page("pages/12_我的审批.py", title="我的审批",  icon="📝"),
    st.Page("pages/10_消息中心.py", title="消息中心",  icon="🔔"),
    st.Page("pages/14_个人中心.py", title="个人中心",  icon="👤"),
]
# 仅企业领导可见的管理功能
if current_role() == ROLE_ADMIN:
    _pages.append(st.Page("pages/18_管理驾驶舱.py", title="管理驾驶舱", icon="📊"))
    _pages.append(st.Page("pages/11_审批中心.py", title="审批中心", icon="🗂️"))
    _pages.append(st.Page("pages/19_合规审计台账.py", title="审计台账", icon="📒"))
    _pages.append(st.Page("pages/5_账号管理.py", title="账号管理", icon="👥"))

pg = st.navigation(_pages, position="hidden")
pg.run()
