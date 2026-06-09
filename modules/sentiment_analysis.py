from core.llm_client import chat
from core.rag_engine import retrieve
from core.llm_client import build_rag_context
from prompts.sentiment_prompt import SYSTEM, get_sample_comments
from config.settings import BRAND_DISPLAY_NAMES


def run(brand_key: str, comments: str = "") -> dict:
    if not comments.strip():
        comments = get_sample_comments(brand_key)

    chunks = retrieve(brand_key, "品牌特点 产品 服务", n_results=3)
    kb_context = build_rag_context(chunks)

    brand_name = BRAND_DISPLAY_NAMES[brand_key]

    user_msg = f"""品牌：{brand_name}

【品牌知识库背景（辅助分析）】
{kb_context}

【舆情样本内容】
{comments}

请对以上舆情样本进行全面的 AI 舆情分析，输出完整分析报告。"""

    output = chat(SYSTEM, user_msg, max_tokens=2500)
    return {"output": output, "chunks": chunks, "comments_used": comments}
