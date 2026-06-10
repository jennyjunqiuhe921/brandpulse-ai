"""G3 · 合规自查工具 — 批量粘贴多条文案，逐条检测并输出汇总报告。"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
from modules.compliance_precheck import precheck

st.set_page_config(page_title="合规自查 — PinSight AI", page_icon="✅", layout="wide")
brand = render_sidebar()

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">合规自查</h1>
  <p class="page-desc">批量粘贴多条文案，一键逐条检测广告法风险，输出汇总报告（轻量自查，正式审查请用「合规卫士」）</p>
</div>
""",
    unsafe_allow_html=True,
)

st.info("与「合规卫士」区别：本工具为**批量快速自查**，基于关键词扫描即时给出每条文案风险等级；"
        "「合规卫士」为单条深度 AI 合规审查。")

st.markdown("**粘贴待检测文案（每行一条）**")
text = st.text_area(
    "批量文案",
    height=220,
    placeholder="全场最便宜，错过再无！\n精选优质原料，用心做好茶\n效果立竿见影，包治百病\n......",
    label_visibility="collapsed",
    key="selfcheck_text",
)

if st.button("🔍 批量检测", type="primary"):
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        st.warning("请至少粘贴一条文案")
    else:
        st.session_state["selfcheck_results"] = [(ln, precheck(ln)) for ln in lines]

if "selfcheck_results" in st.session_state:
    results = st.session_state["selfcheck_results"]
    st.markdown("---")

    # ── 逐条结果 ──────────────────────────────────────────────────────────────
    st.subheader(f"📋 检测明细（共 {len(results)} 条）")
    _icon = {"高": "🔴", "中": "🟡", "低": "🟢"}
    for i, (line, pc) in enumerate(results, 1):
        with st.container(border=True):
            st.markdown(f"**{i}. {_icon[pc['level']]} {pc['level']}风险**　—　{line}")
            hits = []
            if pc["high"]:
                hits.append("绝对化用语：" + "、".join(pc["high"]))
            if pc["med"]:
                hits.append("功效/承诺类：" + "、".join(pc["med"]))
            if hits:
                st.caption("⚠️ " + "　|　".join(hits))
            else:
                st.caption("未检测到明显违规用语")

    # ── 汇总统计 ──────────────────────────────────────────────────────────────
    high = sum(1 for _, pc in results if pc["level"] == "高")
    med = sum(1 for _, pc in results if pc["level"] == "中")
    low = sum(1 for _, pc in results if pc["level"] == "低")

    st.markdown("---")
    st.subheader("📊 汇总统计")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("总条数", len(results))
    s2.metric("🔴 高风险", f"{high} 条")
    s3.metric("🟡 中风险", f"{med} 条")
    s4.metric("🟢 低风险", f"{low} 条")

    if high:
        st.error(f"🚫 共 {high} 条高风险文案含绝对化用语，须修改后方可使用")
    elif med:
        st.warning(f"⚠️ 共 {med} 条文案含功效/承诺类表述，建议核实依据")
    else:
        st.success("✅ 全部文案未检测到明显违规用语，仍建议人工复核后发布")

    st.caption("⚠️ 本自查基于关键词规则扫描，不能覆盖全部合规风险，正式发布前须经人工/法务复核。")
