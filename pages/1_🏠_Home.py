"""BrandPulse AI — Intelligence Dashboard (Home)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
from utils.sidebar import render as render_sidebar
from core.rag_engine import collection_count
from config.settings import BRAND_DISPLAY_NAMES, BRAND_FOCUS

st.set_page_config(
    page_title="BrandPulse AI — Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

brand = render_sidebar()

# ── 数据定义 ────────────────────────────────────────────────────────
AI_SCORES  = {"heytea": 92,  "nayuki": 84,  "chapanda": 79}
AI_DELTAS  = {"heytea": 3.2, "nayuki": 1.8, "chapanda": 5.1}
GEO_SCORES = {"heytea": 7.3, "nayuki": 8.0, "chapanda": 6.2}
COMP_SCORES = {"heytea": 8.1, "nayuki": 8.3, "chapanda": 7.8}

BRAND_TASKS = {
    "heytea": [
        "🔴 GEO：「低糖选择」类问题可见度偏低 → 建议补充官网营养/成分信息页",
        "🟡 价格信息在 AI 中可能过时 → 建议官网更新明确价格区间说明",
        "🟡 联名活动结束后旧内容残留 → 建议及时下架或存档历史联名页面",
    ],
    "nayuki": [
        "🟡 菜单产品描述可能与实际不符 → 建议定期同步官网产品页",
        "🟡 门店空间数据缺乏具体数字 → 补充平均面积、座位数等可验证信息",
        "🟢 港股上市背书已被 AI 准确识别 → 持续在品牌资料中强化此信息",
    ],
    "chapanda": [
        "🔴 招牌产品 AI 识别度偏低 → 补充杨枝甘露、芋泥波波等产品详情页",
        "🔴 下沉市场覆盖数据未充分曝光 → 发布各省门店分布数据媒体稿",
        "🟡 熊猫 IP 来源故事在 AI 中描述模糊 → 官网品牌故事页增加 IP 起源说明",
    ],
}

competitors = {k: v for k, v in BRAND_DISPLAY_NAMES.items() if k != brand}
comp_keys = list(competitors.keys())

# ── Header ──────────────────────────────────────────────────────────
st.markdown(f"## 📊 {BRAND_DISPLAY_NAMES[brand]} · AI 品牌情报中控台")
st.caption("AI Brand Intelligence Dashboard · 所有分析基于公开信息，模拟数据仅供演示")
st.divider()

# ── Row 1: 本品牌大指标 + 竞品基准 ─────────────────────────────────
col_main, col_divider, col_comp = st.columns([3, 0.1, 4])

with col_main:
    st.markdown("#### 🎯 本品牌实时指标")
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric(
            label="AI 热度指数",
            value=AI_SCORES[brand],
            delta=f"+{AI_DELTAS[brand]}% vs 上月",
            help="基于媒体曝光、社媒提及、AI搜索可见度的综合模拟指数",
        )
    with m2:
        st.metric(
            label="GEO 综合评分",
            value=f"{GEO_SCORES[brand]} / 10",
            help="Generative Engine Optimization — AI搜索引擎可见度评分",
        )
    with m3:
        st.metric(
            label="综合能力评分",
            value=COMP_SCORES[brand],
            help="品牌综合竞争力模拟评估",
        )

with col_comp:
    st.markdown("#### 📊 竞品基准对比")
    cc1, cc2 = st.columns(2)
    for i, (bk, bname) in enumerate(competitors.items()):
        with (cc1 if i == 0 else cc2):
            gap_heat = AI_SCORES[brand] - AI_SCORES[bk]
            gap_geo  = round(GEO_SCORES[brand] - GEO_SCORES[bk], 1)
            st.metric(
                label=bname,
                value=f"热度 {AI_SCORES[bk]}　GEO {GEO_SCORES[bk]}",
                delta=f"热度差 {'+' if gap_heat>=0 else ''}{gap_heat}　GEO差 {'+' if gap_geo>=0 else ''}{gap_geo}",
                delta_color="normal",
                help="正值=本品牌领先，负值=竞品领先（模拟数据）",
            )

st.divider()

# ── Row 2: 图表 + 待优化任务 ─────────────────────────────────────────
col_left, col_right = st.columns([3, 2])

with col_left:
    st.markdown("#### 🌐 GEO 可见度评分对比（模拟数据）")
    geo_data = pd.DataFrame({
        "GEO综合评分":   [GEO_SCORES["heytea"], GEO_SCORES["nayuki"], GEO_SCORES["chapanda"]],
        "AI描述准确性":  [7.0, 8.0, 6.0],
        "内容丰富度":    [6.0, 7.0, 5.0],
        "竞品差异化":    [7.0, 9.0, 7.0],
    }, index=["喜茶", "奈雪", "茶百道"])
    st.bar_chart(geo_data, height=240)
    st.caption("数据来源：GEO分析模块模拟评分，非真实市场数据")

    st.markdown("#### 📈 AI 搜索热度趋势（模拟月度数据）")
    trend_data = pd.DataFrame({
        "喜茶":  [82, 85, 87, 88, 90, 92],
        "奈雪":  [76, 78, 80, 81, 83, 84],
        "茶百道": [68, 70, 73, 75, 77, 79],
    }, index=["2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"])
    st.line_chart(trend_data, height=200)
    st.caption("⚠️ 以上均为演示用模拟趋势数据")

with col_right:
    st.markdown(f"#### 🚨 {BRAND_DISPLAY_NAMES[brand]} 待优化任务")
    for task in BRAND_TASKS[brand]:
        level = task[0]
        if level == "🔴":
            st.error(task[2:])
        elif level == "🟡":
            st.warning(task[2:])
        else:
            st.success(task[2:])

st.divider()

# ── Row 3: 竞品对标 + 知识库状态 ─────────────────────────────────────
col_rank, col_kb = st.columns([3, 2])

with col_rank:
    st.markdown("#### 🏅 竞品对标：综合能力评估（模拟）")
    rows = []
    for bk, bname in BRAND_DISPLAY_NAMES.items():
        is_self = "⭐ 本品牌" if bk == brand else "竞品"
        rows.append({
            "品牌": bname,
            "角色": is_self,
            "综合评分": COMP_SCORES[bk],
            "GEO评分": GEO_SCORES[bk],
            "AI热度": AI_SCORES[bk],
            "增长潜力": {"heytea": "📈 高", "nayuki": "📈 稳健", "chapanda": "🚀 快速"}[bk],
        })
    ranking_df = pd.DataFrame(rows)
    st.dataframe(ranking_df, use_container_width=True, hide_index=True)
    st.caption("⚠️ 以上为模拟评估数据，当前品牌行已标注「本品牌」")

with col_kb:
    st.markdown("#### 🗄️ 知识库状态")
    for bk, bname in BRAND_DISPLAY_NAMES.items():
        count = collection_count(bk)
        status = "✅ 就绪" if count > 0 else "⚠️ 未初始化"
        st.metric(bname, f"{count} 文档块", delta=status)

st.divider()

# ── Row 4: 快速进入 ──────────────────────────────────────────────────
st.markdown("### 🚀 快速进入分析模块")
st.markdown(f"**当前品牌：{BRAND_DISPLAY_NAMES[brand]}** · 战略切入点：{BRAND_FOCUS[brand]}")
st.markdown("")

a1, a2, a3, a4, a5, a6, a7 = st.columns(7)
with a1:
    st.markdown("**🔍 品牌分析**\n\n任务卡1\n必选模块")
with a2:
    st.markdown("**🌐 GEO分析**\n\nAI搜索\n可见度")
with a3:
    st.markdown("**✍️ 内容工厂**\n\n多平台\n内容矩阵")
with a4:
    st.markdown("**📊 市场定位**\n\nSTP / SWOT\n差异化策略")
with a5:
    st.markdown("**📡 数据采集**\n\n舆情采集\n行业动态")
with a6:
    st.markdown("**📰 舆情分析**\n\nAI情感分析\n风险预警")
with a7:
    st.markdown("**🛡️ 合规审查**\n\nRefChecker\n广告法合规")

st.divider()
st.caption(
    "⚠️ **免责声明**：本作品仅用于比赛演示。所有企业分析基于公开信息和 AI 工具辅助生成，"
    "不代表对企业经营、产品质量或市场表现的事实认定。所有输出须经品牌授权人员复核后方可商业使用。"
)
