"""Reusable follow-up chat component — renders below any analysis result."""
import streamlit as st
from core.llm_client import chat


def render(brand: str, context: str, key: str) -> None:
    """
    Render a follow-up chat box with message history.

    Args:
        brand:   Brand key (e.g. "heytea")
        context: The analysis result text to use as conversation context
        key:     Unique key per page/tab to avoid session_state conflicts
    """
    history_key = f"chat_history_{key}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []

    st.markdown("---")
    st.subheader("💬 追问 AI 顾问")
    st.caption("基于上方分析结果继续提问，例如：「有哪些具体风险？」「帮我改写成更激进的版本」")

    # Render message history
    for msg in st.session_state[history_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    user_input = st.chat_input("输入你的问题…", key=f"input_{key}")
    if user_input:
        # Show user message immediately
        st.session_state[history_key].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Build system prompt with analysis context + history
        history_text = ""
        for m in st.session_state[history_key][:-1]:  # exclude current message
            role_label = "用户" if m["role"] == "user" else "AI顾问"
            history_text += f"\n{role_label}：{m['content']}"

        system_prompt = f"""你是一位专业的品牌策略顾问，正在协助分析品牌「{brand}」。

以下是刚才完成的分析报告：
{context}

{f'以下是之前的对话记录：{history_text}' if history_text else ''}

请基于上述分析内容回答用户的追问。回答要简洁、有洞察力，如果用户要求改写或生成内容，直接输出内容。"""

        with st.chat_message("assistant"):
            with st.spinner("思考中..."):
                try:
                    reply = chat(system_prompt, user_input, max_tokens=1024)
                    st.markdown(reply)
                    st.session_state[history_key].append({"role": "assistant", "content": reply})
                except Exception as e:
                    err = f"请求失败：{e}"
                    st.error(err)
                    st.session_state[history_key].append({"role": "assistant", "content": err})

    # Clear button
    if st.session_state[history_key]:
        if st.button("🗑️ 清空对话", key=f"clear_{key}"):
            st.session_state[history_key] = []
            st.rerun()
