"""
PRD §1.5 全局合规组件
  A1 · render_four_blocks()   — AI四大内容区块分类展示
  A2 · render_source_meta()   — 信息溯源（来源 + 查询时间 + 链接）
  A3 · render_disclaimer()    — 全页面标准免责声明
  A4 · review_gate()          — 人工复核门控

注意：本模块全部使用原生 Streamlit 组件，不使用 unsafe_allow_html=True，
      避免在 st.tabs() 附近触发 React DOM removeChild 崩溃。
"""
from __future__ import annotations

import re
from datetime import datetime

import streamlit as st

# ── A3 标准免责文案（与 PRD §1.5.6 完全一致）────────────────────────────────
DISCLAIMER_TEXT = (
    "相关企业分析基于公开信息和AI工具辅助生成，不代表对企业经营、产品质量、"
    "市场表现或声誉状况的事实认定。所有输出均需在真实商业使用前由企业授权人员进行复核。"
)

# 区块名称正则（兼容全角括号）
_BLOCK_PATTERN = re.compile(
    r"【(公开事实|AI推断|人工判断|待验证事项)】",
    re.UNICODE,
)

# 每个区块对应的 Streamlit 原生样式函数 + 前缀标签
_BLOCK_RENDER = {
    "公开事实":   ("success", "📋 公开事实"),
    "AI推断":     ("info",    "🤖 AI 推断"),
    "人工判断":   ("warning", "👤 人工判断"),
    "待验证事项": ("error",   "⚠️ 待验证事项"),
}


# ── A1 · 四大区块渲染 ─────────────────────────────────────────────────────
def render_four_blocks(output_text: str) -> None:
    """
    解析 AI 输出文本，将【公开事实】【AI推断】【人工判断】【待验证事项】
    标记的内容以 Streamlit 原生色彩组件展示，未标记部分以普通 markdown 渲染。
    不使用 unsafe_allow_html，避免 React DOM 冲突。
    """
    if not output_text or not output_text.strip():
        return

    parts = _BLOCK_PATTERN.split(output_text)
    # split 以捕获组分割：[普通文, 区块名, 内容, 普通文, 区块名, 内容, ...]
    i = 0
    while i < len(parts):
        segment = parts[i]
        if segment.strip():
            st.markdown(segment)
        i += 1

        if i < len(parts):
            block_name = parts[i]
            i += 1
            block_content = parts[i].strip() if i < len(parts) else ""
            _render_block_card(block_name, block_content)
            i += 1


def _render_block_card(block_name: str, content: str) -> None:
    """用原生 Streamlit 组件渲染单个区块，无 HTML 注入。"""
    if not content:
        return
    style_fn_name, label = _BLOCK_RENDER.get(
        block_name, ("info", f"📌 {block_name}")
    )
    style_fn = getattr(st, style_fn_name)   # st.success / st.info / st.warning / st.error
    style_fn(f"**{label}**\n\n{content}")


# ── A2 · 信息溯源展示 ─────────────────────────────────────────────────────
def render_source_meta(
    chunks: list[dict],
    query_time: str | None = None,
    expanded: bool = False,
) -> None:
    """
    在可折叠面板中展示知识库引用，包含：
    来源名称 · 查询时间 · 原始文本摘要
    """
    if not chunks:
        return
    ts = query_time or datetime.now().strftime("%Y-%m-%d %H:%M")
    with st.expander("📚 信息溯源 · 知识库引用", expanded=expanded):
        st.caption(f"🕐 查询时间：{ts}")
        for i, c in enumerate(chunks, 1):
            src = c.get("source", "未知来源")
            txt = c.get("text", "")
            url = c.get("url", "")

            col_left, col_right = st.columns([3, 1])
            with col_left:
                st.markdown(f"**[{i}]** `{src}`")
            with col_right:
                if url:
                    st.markdown(f"[🔗 原始链接]({url})")

            st.text(txt[:300] + "…" if len(txt) > 300 else txt)
            if i < len(chunks):
                st.divider()


# ── A3 · 标准免责声明 ─────────────────────────────────────────────────────
def render_disclaimer() -> None:
    """在页面底部渲染 PRD §1.5.6 标准免责声明。应在每个页面末尾调用。"""
    st.divider()
    st.caption(f"⚖️ **免责声明**：{DISCLAIMER_TEXT}")


# ── A4 · 人工复核门控 ─────────────────────────────────────────────────────
def review_gate(page_key: str) -> bool:
    """
    在结果区域底部渲染人工复核勾选框。

    参数：
        page_key: 用于隔离不同页面 session_state 的唯一标识符
                  如 "geo" / "content" / "sentiment" / "compliance"

    返回：
        True  — 用户已勾选"已复核"，下游按钮可启用
        False — 未复核，下游按钮应禁用
    """
    state_key = f"reviewed_{page_key}"
    # 初始化 session state（避免 KeyError）
    if state_key not in st.session_state:
        st.session_state[state_key] = False

    st.divider()
    # 直接把 state_key 作为 key，让 Streamlit 管理值，不传 value= 参数
    # 避免 value= + key= 双重绑定引发的 React DOM 冲突
    st.checkbox(
        "✅ 我已人工复核以上 AI 输出内容，确认内容准确且符合品牌合规要求，可用于后续操作",
        key=state_key,
    )
    checked = st.session_state[state_key]

    if not checked:
        st.warning("⚠️ **导出 / 归档前请先完成人工复核**，勾选上方确认框后导出按钮将解锁。")
    return checked
