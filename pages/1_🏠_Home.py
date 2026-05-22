"""BrandPulse AI — Welcome & Navigation Hub"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
from utils.sidebar import render as render_sidebar

st.set_page_config(
    page_title="BrandPulse AI — AI 品牌与市场增长工作台",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

render_sidebar()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    """
<div style="text-align:center;padding:48px 0 32px 0">
  <div style="font-size:56px;margin-bottom:12px">📊</div>
  <h1 style="font-size:2.4rem;font-weight:800;margin:0">BrandPulse AI</h1>
  <p style="font-size:1.15rem;color:#555;margin:12px 0 4px 0">
    AI 品牌与市场增长工作台
  </p>
  <p style="font-size:0.95rem;color:#888;max-width:560px;margin:0 auto">
    基于 RAG 知识库 + Claude AI，覆盖品牌分析、GEO优化、内容生成、舆情监测、合规审查全流程
  </p>
</div>
""",
    unsafe_allow_html=True,
)

st.divider()

# ── Module Cards ──────────────────────────────────────────────────────────────
st.markdown("### 🚀 分析模块")
st.caption("从侧边栏选择品牌后，点击任意模块开始分析")
st.markdown("")

MODULES = [
    ("🔍", "品牌 & 产品分析",  "任务卡1（必选）", "品牌定位、调性、目标客群、产品功能拆解、核心卖点、价值主张"),
    ("🌐", "GEO / AI 搜索可见度", "增强模块 A",  "设计 AI 搜索测试问题，分析品牌在 AI 回答中的准确性与可见度"),
    ("✍️", "内容生成工厂",    "任务卡4",       "多平台内容矩阵：小红书、抖音脚本、海报标题、KOL Brief"),
    ("📊", "市场定位分析",    "任务卡1",       "STP 框架 + SWOT 分析 + 差异化定位建议"),
    ("📡", "数据采集中心",    "增强模块 B/C",  "采集品牌舆情与行业动态，结果可直接流转至舆情分析或合规审查"),
    ("📰", "AI 舆情分析",     "增强模块 B",    "识别正负向情感、核心关注点、风险等级、官方回应建议"),
    ("🛡️", "合规审查哨所",   "必做模块",      "检测绝对化用语、虚假宣传、竞品贬低、品牌调性偏差"),
    ("🔍", "竞品对标分析",    "增强模块 D",    "品牌定位差异、产品卖点对比、内容策略差距、GEO可见度对比"),
]

rows = [MODULES[:4], MODULES[4:]]
for row in rows:
    cols = st.columns(4)
    for col, (icon, title, tag, desc) in zip(cols, row):
        with col:
            st.markdown(
                f"""
<div style="border:1px solid #e0e0e0;border-radius:12px;padding:20px 18px;height:100%;min-height:150px">
  <div style="font-size:28px;margin-bottom:8px">{icon}</div>
  <div style="font-weight:700;font-size:1rem;margin-bottom:4px">{title}</div>
  <div style="display:inline-block;background:#f0f2f6;border-radius:4px;padding:1px 7px;font-size:0.75rem;color:#555;margin-bottom:8px">{tag}</div>
  <div style="font-size:0.85rem;color:#666;line-height:1.5">{desc}</div>
</div>
""",
                unsafe_allow_html=True,
            )
    st.markdown("")

st.divider()

# ── Tech Stack ────────────────────────────────────────────────────────────────
st.markdown("### 🛠️ 技术架构")
t1, t2, t3, t4 = st.columns(4)
with t1:
    st.markdown("**知识库**\n\nChromaDB · 每品牌独立向量库 · 公开信息构建")
with t2:
    st.markdown("**AI 引擎**\n\nClaude API · RAG 检索增强 · 品牌专属 Context")
with t3:
    st.markdown("**合规层**\n\nRefChecker 标注 · ✅事实 / ⚠️推断 / ❓待核查")
with t4:
    st.markdown("**数据流**\n\n采集 → 分析 → 生成 → 合规 全链路贯通")

st.divider()

st.caption(
    "⚠️ **免责声明**：本作品仅用于比赛演示。所有企业分析基于公开信息和 AI 工具辅助生成，"
    "不代表对企业经营、产品质量或市场表现的事实认定。所有输出须经品牌授权人员复核后方可商业使用。"
)
