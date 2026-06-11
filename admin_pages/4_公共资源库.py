"""S5 2.3 公共资源库维护（运营侧）。"""
import streamlit as st
from utils.admin_sidebar import render

render()

st.markdown('<div class="page-header"><h1>公共资源库</h1>'
            '<p class="page-desc">平台统一维护、下发各租户的公共模板与规则库。租户仅可引用，不可修改。</p>'
            '</div>', unsafe_allow_html=True)

tabs = st.tabs(["📝 文案模板", "🛡️ 合规词库", "🌐 GEO提问库", "📰 舆情词库", "🛒 选品模板", "🔭 竞品配置"])

_DEFAULTS = {
    "文案模板": ["种草短文案模板", "直播口播模板", "节日促销模板", "新品上市模板"],
    "合规词库": ["最/第一/极致（绝对化）", "国家级/世界级", "零风险/100%", "包治/根治"],
    "GEO提问库": ["推荐几个高端{品类}品牌？", "{品牌}和{竞品}哪个更好？", "性价比高的{品类}有哪些？"],
    "舆情词库": ["难喝/踩雷（负面）", "排队久/服务差", "异物/食安（高危）", "涨价/缩水"],
    "选品模板": ["新式茶饮选品配置", "美妆护肤选品配置", "餐饮连锁选品配置"],
    "竞品配置": ["通用监控维度：品牌/产品/舆情/GEO/内容/策略", "默认采集频率：每日", "预警：上新/调价/负面"],
}
_keys = list(_DEFAULTS.keys())
store = st.session_state.setdefault("_public_lib", {k: list(v) for k, v in _DEFAULTS.items()})

for tab, key in zip(tabs, _keys):
    with tab:
        st.caption(f"{key}（共 {len(store[key])} 条）· 租户可一键引用，不可编辑公共内容。")
        for i, item in enumerate(store[key]):
            c1, c2 = st.columns([6, 1])
            c1.markdown(f"- {item}")
            with c2:
                if st.button("下架", key=f"rm_{key}_{i}", use_container_width=True):
                    store[key].pop(i); st.rerun()
        nw = st.text_input(f"新增{key}条目", key=f"add_{key}")
        if st.button("新增", key=f"addbtn_{key}") and nw.strip():
            store[key].append(nw.strip()); st.rerun()
