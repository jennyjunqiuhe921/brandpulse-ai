import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.sidebar import render as render_sidebar
import modules.content_generator as content_mod
from utils.result_banner import maybe_show_banner
from utils.prd_components import render_four_blocks, render_disclaimer, review_gate
from prompts.content_generation_prompt import PLATFORM_GUIDES

st.set_page_config(page_title="内容生成工厂 — PinSight AI", page_icon="✍️", layout="wide")
brand = render_sidebar()

st.markdown(
    """
<div class="page-header">
  <h1 class="page-title">内容工坊</h1>
  <p class="page-desc">一键生成小红书、抖音、公众号等多平台内容矩阵，所有输出经人工复核后可直接使用</p>
</div>
""",
    unsafe_allow_html=True,
)


col1, col2 = st.columns(2)
with col1:
    product_name = st.text_input(
        "产品名称 *",
        value="",
        placeholder="输入要推广的产品或服务名称",
    )
    goal = st.text_input(
        "推广目标",
        value="",
        placeholder="例如：新品上市、节日限定、品牌活动",
    )

with col2:
    tone_key = st.selectbox(
        "品牌语气",
        options=["酷/有态度", "温柔/精致", "亲民/接地气"],
    )
    platforms = st.multiselect(
        "目标平台（可多选）",
        options=list(PLATFORM_GUIDES.keys()),
        default=["小红书种草文案", "抖音/短视频脚本", "海报标题组合"],
    )

if not platforms:
    st.warning("请至少选择一个目标平台")

if st.button("🚀 生成内容矩阵", type="primary", disabled=not platforms or not product_name):
    with st.spinner(f"正在为「{product_name}」生成 {len(platforms)} 个平台的内容...（约 20-40 秒）"):
        try:
            result = content_mod.run(brand, product_name, platforms, tone_key, goal)
            st.session_state["content_result"] = result
            st.session_state["content_for_compliance"] = result["output"]
            st.session_state.pop("reviewed_content", None)
        except Exception as e:
            st.error(f"生成失败：{e}")

if "content_result" in st.session_state:
    res = st.session_state["content_result"]
    st.markdown("---")
    maybe_show_banner(res)

    generated_platforms = res.get("platforms", platforms)
    raw_output = res["output"]

    # Split by ### headers (more reliable than ---)
    import re as _re
    header_pattern = _re.compile(r"(?=^###\s)", _re.MULTILINE)
    raw_sections = [s.strip() for s in header_pattern.split(raw_output) if s.strip()]

    # Fall back to --- split if no ### found
    if not raw_sections:
        raw_sections = [s.strip() for s in raw_output.split("---") if s.strip()]

    if len(raw_sections) >= 1 and len(generated_platforms) > 0:
        # Match sections to platforms (best-effort by position)
        tab_labels = [f"📄 {p}" for p in generated_platforms]
        with st.container():
            tabs = st.tabs(tab_labels)
            for i, tab in enumerate(tabs):
                with tab:
                    content = raw_sections[i] if i < len(raw_sections) else ""
                    st.markdown(content if content else "（该平台内容暂无，请重新生成）")
    else:
        st.markdown(raw_output)

    st.markdown("---")

    # ── 推广策略建议 ──────────────────────────────────────────────────────────
    st.subheader("📣 推广策略建议")
    CHANNEL_MAP = {
        "小红书种草文案": {"渠道": "小红书", "节奏": "发布频率 3-4次/周，以图文为主", "核心指标": "收藏量、搜索词曝光", "预算优先级": "★★★★☆"},
        "抖音/短视频脚本": {"渠道": "抖音/视频号", "节奏": "每周 1-2 条短视频", "核心指标": "完播率、点赞/转发", "预算优先级": "★★★★★"},
        "海报标题组合": {"渠道": "线下门店/朋友圈/公众号封面", "节奏": "配合新品节点或活动", "核心指标": "点击率、扫码转化", "预算优先级": "★★★☆☆"},
        "公众号推文": {"渠道": "微信公众号", "节奏": "每周 1-2 篇深度内容", "核心指标": "阅读量、分享数", "预算优先级": "★★★☆☆"},
        "KOL/KOC Brief": {"渠道": "全平台达人", "节奏": "新品上市提前 2 周启动", "核心指标": "曝光量、互动率、带货GMV", "预算优先级": "★★★★★"},
        "微博话题文案": {"渠道": "微博", "节奏": "话题节点 + 产品热搜", "核心指标": "话题阅读量、互动量", "预算优先级": "★★★☆☆"},
    }

    selected_channels = [p for p in (res.get("platforms") or platforms) if p in CHANNEL_MAP]
    if selected_channels:
        strat_cols = st.columns(min(len(selected_channels), 3))
        for i, ch in enumerate(selected_channels):
            info = CHANNEL_MAP[ch]
            with strat_cols[i % len(strat_cols)]:
                st.markdown(f"**{info['渠道']}**")
                st.markdown(f"- 节奏：{info['节奏']}")
                st.markdown(f"- 指标：{info['核心指标']}")
                st.markdown(f"- 预算优先级：{info['预算优先级']}")
    else:
        st.markdown("- 建议在新品上市前 2 周启动 KOL 种草，配合小红书图文同步覆盖")
        st.markdown("- 核心指标：小红书收藏量 · 抖音完播率 · 公众号阅读量")

    st.caption("⚠️ 以上推广建议为 AI 辅助生成，需结合品牌实际预算和资源由市场团队复核调整")

    # A1 · 展示四区块分类说明（追加在内容后面的分类章节）
    # 找到四区块分类说明部分单独渲染，无则静默跳过
    split_marker = "---\n\n### AI 输出内容分类"
    if split_marker in raw_output:
        _, classification_part = raw_output.split(split_marker, 1)
        render_four_blocks("---\n\n### AI 输出内容分类" + classification_part)

    # A4 · 人工复核门控
    reviewed = review_gate("content")

    st.markdown("---")
    col_a, col_b = st.columns([2, 2])
    with col_a:
        if reviewed:
            st.success("✅ 已完成人工复核")
        else:
            st.info("🔒 完成复核后可送往合规审查")
    with col_b:
        if st.button(
            "🛡️ 一键送往合规审查",
            type="primary",
            use_container_width=True,
            disabled=not reviewed,
        ):
            st.session_state["content_for_compliance"] = res["output"]
            st.session_state["auto_run_compliance"] = False
            st.switch_page("pages/8_合规卫士.py")

    with st.expander("📋 查看完整输出", expanded=False):
        st.text_area("完整文本（可复制）", value=res["output"], height=300)

    with st.expander("⚠️ 使用说明", expanded=False):
        st.markdown("""
- 所有生成内容须经品牌授权人员**人工复核**后方可发布
- 标注 `[创意内容]` 的部分为 AI 创意发挥，需核实是否符合品牌调性
- 标注 `[品牌信息]` 的部分来自知识库，需核实信息是否仍然准确
- 建议在「合规审查」模块对生成内容进行进一步合规扫描
""")

    # A3 · 标准免责声明
    render_disclaimer()
