"""S5 2.7 全域数据采集全局规则（运营侧）— 渠道分级 L1/L2/L3 + 通用规则 + 额度。"""
import streamlit as st
import pandas as pd
from utils.admin_sidebar import render

render()

st.markdown('<div class="page-header"><h1>采集全局规则</h1>'
            '<p class="page-desc">渠道法律风险分级、通用去重/脱敏/限频、按套餐分配采集额度。'
            '高风险渠道默认关闭。</p></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["🚦 渠道分级", "🧹 通用规则", "📦 额度分配"])

with tab1:
    st.caption("L1 合规官方API（默认开放）· L2 第三方合规数据源 · L3 高风险（默认关闭）")
    default_channels = [
        {"渠道": "微博", "分级": "L1", "默认": "开放", "说明": "官方API"},
        {"渠道": "正规新闻", "分级": "L1", "默认": "开放", "说明": "授权"},
        {"渠道": "授权电商", "分级": "L1", "默认": "开放", "说明": "官方API"},
        {"渠道": "第三方数据服务", "分级": "L2", "默认": "开放", "说明": "合规整合"},
        {"渠道": "抖音", "分级": "L3", "默认": "关闭", "说明": "高风险，标注模拟数据"},
        {"渠道": "小红书", "分级": "L3", "默认": "关闭", "说明": "高风险，标注模拟数据"},
        {"渠道": "大众点评", "分级": "L3", "默认": "关闭", "说明": "高风险，标注模拟数据"},
        {"渠道": "淘宝", "分级": "L3", "默认": "关闭", "说明": "高风险，标注模拟数据"},
    ]
    st.dataframe(pd.DataFrame(default_channels), use_container_width=True, hide_index=True)
    st.warning("⚠️ L3 高风险渠道在商业化版本默认禁用；授权/测试场景开启时，页面强制标注"
               "「模拟数据」与「待验证」标签。")

with tab2:
    st.caption("以下规则全局统一生效：")
    rules = {
        "数据自动去重": True, "广告/水军过滤": True, "个人信息隐私脱敏": True,
        "采集频率限制": True,
    }
    for k, v in rules.items():
        st.checkbox(k, value=v, key=f"rule_{k}")
    st.number_input("单渠道采集间隔（秒）", 1, 3600, 5)
    if st.button("保存通用规则", type="primary"):
        st.success("通用采集规则已保存")

with tab3:
    st.caption("按订阅套餐分配可用渠道数、单日条数、并发任务，支持临时扩容。")
    quota = pd.DataFrame([
        {"套餐": "基础执行版", "可用渠道": 3, "单日条数": 500, "并发任务": 1},
        {"套餐": "标准管控版", "可用渠道": 6, "单日条数": 5000, "并发任务": 3},
        {"套餐": "企业集团版", "可用渠道": 10, "单日条数": 50000, "并发任务": 10},
    ])
    st.dataframe(quota, use_container_width=True, hide_index=True)
