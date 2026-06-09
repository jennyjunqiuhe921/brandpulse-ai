"""Shared helper: render a small banner when showing demo-preview content."""
import streamlit as st


def demo_preview_notice():
    """Show a subtle notice when the result is a demo preview (not user-run)."""
    st.markdown(
        """
<div style="background:#FFFBEB;border:1px solid #FDE68A;border-radius:8px;
            padding:10px 16px;margin-bottom:12px;display:flex;align-items:center;gap:10px">
  <span style="font-size:16px">💡</span>
  <div>
    <span style="font-size:12px;font-weight:600;color:#92400E">示例预览</span>
    <span style="font-size:12px;color:#B45309;margin-left:6px">
      以下为内置演示内容，点击上方「运行」按钮可生成基于真实知识库的分析结果。
    </span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def maybe_show_banner(result: dict):
    """Call this before rendering any result. Shows banner if it's a demo preview."""
    if result.get("_is_demo_preview"):
        demo_preview_notice()
