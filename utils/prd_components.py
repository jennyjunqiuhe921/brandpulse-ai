"""
PRD §1.5 全局合规组件
  A1 · render_four_blocks()   — AI四大内容区块分类展示
  A2 · render_source_meta()   — 信息溯源（来源 + 查询时间 + 链接）
  A3 · render_disclaimer()    — 全页面标准免责声明
  A4 · review_gate()          — 人工复核门控
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

# ── A1 四大区块样式配置 ────────────────────────────────────────────────────
_BLOCK_STYLES: dict[str, dict] = {
    "公开事实": {
        "icon": "📋",
        "label": "公开事实",
        "bg": "#F0FDF4",
        "border": "#4ADE80",
        "header_color": "#14532D",
        "text_color": "#1A3A1A",
    },
    "AI推断": {
        "icon": "🤖",
        "label": "AI 推断",
        "bg": "#EFF6FF",
        "border": "#60A5FA",
        "header_color": "#1E3A5F",
        "text_color": "#1E3A5F",
    },
    "人工判断": {
        "icon": "👤",
        "label": "人工判断",
        "bg": "#FFFBEB",
        "border": "#FCD34D",
        "header_color": "#78350F",
        "text_color": "#451A03",
    },
    "待验证事项": {
        "icon": "⚠️",
        "label": "待验证事项",
        "bg": "#FFF7ED",
        "border": "#F97316",
        "header_color": "#9A3412",
        "text_color": "#7C2D12",
    },
}

# 区块名称正则（兼容全角/半角括号）
_BLOCK_PATTERN = re.compile(
    r"【(公开事实|AI推断|人工判断|待验证事项)】",
    re.UNICODE,
)


# ── A1 · 四大区块渲染 ─────────────────────────────────────────────────────
def render_four_blocks(output_text: str) -> None:
    """
    解析 AI 输出文本，将【公开事实】【AI推断】【人工判断】【待验证事项】
    标记的内容以带色彩的卡片展示，未标记部分以普通 markdown 渲染。
    """
    parts = _BLOCK_PATTERN.split(output_text)

    # parts 交替出现：[普通文本, 区块名, 区块内容, 普通文本, 区块名, ...]
    # split 以捕获组分割时，偶数下标为普通文本，奇数下标为区块名，下一个为内容
    i = 0
    while i < len(parts):
        segment = parts[i]
        if segment.strip():
            st.markdown(segment)
        i += 1

        if i < len(parts):
            block_name = parts[i]        # 区块名称
            i += 1
            block_content = parts[i] if i < len(parts) else ""
            _render_block_card(block_name, block_content)
            i += 1


def _render_block_card(block_name: str, content: str) -> None:
    """渲染单个区块卡片。"""
    if not content.strip():
        return
    s = _BLOCK_STYLES.get(block_name, {
        "icon": "📌", "label": block_name,
        "bg": "#F9FAFB", "border": "#D1D5DB",
        "header_color": "#374151", "text_color": "#111827",
    })
    # 将内容中换行转为 <br> 以在 HTML 中正确显示
    html_content = content.strip().replace("\n", "<br>")
    st.markdown(
        f"""
<div style="background:{s['bg']};border:1px solid {s['border']};
            border-left:4px solid {s['border']};border-radius:8px;
            padding:14px 18px;margin:10px 0 6px;">
  <div style="font-size:11px;font-weight:700;color:{s['header_color']};
              letter-spacing:0.08em;margin-bottom:8px;text-transform:uppercase">
    {s['icon']}&nbsp;&nbsp;{s['label']}
  </div>
  <div style="font-size:14px;color:{s['text_color']};line-height:1.75">
    {html_content}
  </div>
</div>""",
        unsafe_allow_html=True,
    )


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
            url = c.get("url", "")          # 如有外部链接

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
    st.markdown(
        f"""
<div style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:6px;
            padding:10px 16px;margin-top:24px;font-size:12px;
            color:#6B7280;line-height:1.65">
  ⚖️&nbsp;<strong style="color:#374151">免责声明</strong>：{DISCLAIMER_TEXT}
</div>""",
        unsafe_allow_html=True,
    )


# ── A4 · 人工复核门控 ─────────────────────────────────────────────────────
def review_gate(page_key: str) -> bool:
    """
    在结果区域底部渲染人工复核勾选框。

    参数：
        page_key: 用于隔离不同页面 session_state 的唯一标识符
                  建议使用页面文件名，如 "geo" / "content" / "sentiment" / "compliance"

    返回：
        True  — 用户已勾选"已复核"，下游按钮（导出/归档）可启用
        False — 未复核，下游按钮应禁用
    """
    state_key = f"reviewed_{page_key}"
    reviewed = st.session_state.get(state_key, False)

    st.markdown("---")
    checked = st.checkbox(
        "✅ 我已人工复核以上 AI 输出内容，确认内容准确且符合品牌合规要求，可用于后续操作",
        value=reviewed,
        key=f"review_checkbox_{page_key}",
    )
    st.session_state[state_key] = checked

    if not checked:
        st.warning(
            "⚠️ **导出 / 归档前请先完成人工复核**  \n"
            "勾选上方确认框后，导出按钮将解锁。",
            icon="🔒",
        )
    return checked
