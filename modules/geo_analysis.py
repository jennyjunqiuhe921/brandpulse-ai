from core.rag_engine import retrieve
from core.llm_client import chat, build_rag_context
from prompts.geo_analysis_prompt import SYSTEM_TEMPLATE, GEO_QUESTIONS
from config.settings import BRAND_DISPLAY_NAMES


def run(brand_key: str, custom_questions: list = None) -> dict:
    questions = custom_questions or GEO_QUESTIONS.get(brand_key, GEO_QUESTIONS["heytea"])

    chunks = retrieve(brand_key, "品牌定位 产品特色 品牌知名度 竞品", n_results=6)
    context = build_rag_context(chunks)

    brand_name = BRAND_DISPLAY_NAMES[brand_key]
    questions_list = "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions))

    system = SYSTEM_TEMPLATE.format(
        brand_name=brand_name,
        n_questions=len(questions),
        questions_list=questions_list,
    )

    user_msg = f"""品牌：{brand_name}

【品牌知识库内容（用于判断信息准确性）】
{context}

请根据以上知识库内容和你对该品牌的了解，对 {len(questions)} 个 AI 搜索问题逐一进行 GEO 可见度分析。"""

    output = chat(system, user_msg, max_tokens=3500)
    return {"output": output, "chunks": chunks, "questions": questions}
