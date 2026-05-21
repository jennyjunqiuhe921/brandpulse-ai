"""RefChecker: compare AI output against retrieved knowledge-base chunks."""
from core.llm_client import chat

REFCHECK_SYSTEM = """你是一名品牌合规事实核查员。
你的任务：对比 AI 输出与知识库原文，将每一条结论标记为：
- ✅ 官方事实（有明确原文依据）
- ⚠️ AI 推断（合理推理，但无直接原文）
- ❌ 待复核（无依据或与原文矛盾）

同时检测以下合规风险：
- 绝对化用语（最、第一、唯一等）
- 贬低竞品
- 虚假夸大事实
输出格式：逐条标注 + 风险摘要。"""


def check(ai_output: str, kb_chunks: list[dict]) -> str:
    context = "\n\n".join(f"[原文{i+1}] {c['text']}" for i, c in enumerate(kb_chunks))
    user_msg = f"【知识库原文】\n{context}\n\n【AI 输出】\n{ai_output}"
    return chat(REFCHECK_SYSTEM, user_msg, max_tokens=1500)
