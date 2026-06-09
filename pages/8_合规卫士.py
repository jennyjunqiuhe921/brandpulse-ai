import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.compliance_checker as compliance_mod
from utils.result_banner import maybe_show_banner
from utils.prd_components import render_four_blocks, render_source_meta, render_disclaimer, review_gate
from config.settings import BRAND_DISPLAY_NAMES

st.set_page_config(page_title="合规审查 — PinSight AI", page_icon="🛡️", layout="wide")
brand = render_sidebar()

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">合规卫士</h1>
  <p class="page-desc">自动检测绝对化用语、虚假宣传、竞品贬低等合规风险，输出逐条修改建议</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div style="background:#FDFAF5;border:1px solid #DDD4C4;border-left:3px solid #C4522A;border-radius:6px;padding:12px 16px;margin:0 0 18px;font-size:13px;color:#5C4F42;line-height:1.7">
  <strong style="color:#1A1A1A">输入</strong>：任何 AI 生成的文案、分析报告或推广策略<br>
  <strong style="color:#1A1A1A">输出</strong>：逐条风险标注（🔴 高 / 🟡 中 / 🟢 低）+ 修改建议<br>
  ⚠️ 结果供参考，正式发布前须由品牌授权人员进行人工最终复核。
</div>
""",
    unsafe_allow_html=True,
)



# Pre-populate from content studio if available
prefill = st.session_state.get("content_for_compliance", "")

if prefill:
    st.success("✅ 已从「内容生成工厂」导入内容，可直接运行审查")

content_input = st.text_area(
    "待审查内容",
    value=prefill,
    placeholder="粘贴需要合规审查的文案、分析报告、推广策略等内容...",
    height=250,
)

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("清除导入内容", type="secondary"):
        st.session_state["content_for_compliance"] = ""
        st.rerun()

EXAMPLE_RISKY = """我们是行业第一品牌，产品口味最好，用了我们的产品你一定不会去选其他家！我们的原料是全国最顶级的食材，健康无添加，用了包你效果翻倍。竞争对手的产品根本比不上我们。"""

with st.expander("📋 风险示例库（点击展开 · 一键加载并运行）", expanded=False):
    st.markdown("以下样本包含典型合规风险，可一键加载并直接运行审查，快速演示检测能力：")
    ex_col1, ex_col2 = st.columns(2)
    with ex_col1:
        st.markdown("**示例A：绝对化用语 + 虚假功效**")
        st.code(EXAMPLE_RISKY[:80] + "...", language=None)
        if st.button("加载示例A并运行", key="load_ex_a", type="primary", use_container_width=True):
            st.session_state["example_loaded"] = EXAMPLE_RISKY
            st.session_state["auto_run_compliance"] = True
            st.rerun()
    with ex_col2:
        EXAMPLE_B = """我们首创双品类经营模式，全球独一无二，任何竞品都无法复制。我们的核心产品是世界上最好的，没有之一。消费者使用我们产品后普遍反映其他品牌都失去吸引力。"""
        st.markdown("**示例B：竞品贬低 + 绝对化表述**")
        st.code(EXAMPLE_B[:80] + "...", language=None)
        if st.button("加载示例B并运行", key="load_ex_b", type="primary", use_container_width=True):
            st.session_state["example_loaded"] = EXAMPLE_B
            st.session_state["auto_run_compliance"] = True
            st.rerun()

if "example_loaded" in st.session_state:
    content_input = st.session_state["example_loaded"]

auto_run = st.session_state.pop("auto_run_compliance", False)

if st.button("🚀 运行合规审查", type="primary", disabled=not content_input.strip()) or (auto_run and content_input.strip()):
    with st.spinner("正在进行合规审查...（约 15-25 秒）"):
        try:
            from datetime import datetime
            result = compliance_mod.run(content_input, brand)
            result["_query_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state["compliance_result"] = result
            # pop 而非赋值 False，让 review_gate 初始化逻辑重新生效
            st.session_state.pop("reviewed_compliance", None)
        except Exception as e:
            st.error(f"审查失败：{e}")

if "compliance_result" in st.session_state:
    res = st.session_state["compliance_result"]
    st.markdown("---")
    maybe_show_banner(res)

    # A1 · 四大区块渲染
    render_four_blocks(res["output"])

    # A2 · 信息溯源
    render_source_meta(res["chunks"], query_time=res.get("_query_time"))

    # A4 · 人工复核门控（合规卫士：高风险时额外提示）
    reviewed = review_gate("compliance")
    if reviewed:
        st.success("✅ 已完成复核，内容可进行下一步处理")

    # A3 · 标准免责声明
    render_disclaimer()
