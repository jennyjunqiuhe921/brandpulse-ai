from core.rag_engine import retrieve
from core.llm_client import chat, build_rag_context
from prompts.geo_analysis_prompt import build_geo_system, get_geo_questions
from config.settings import BRAND_DISPLAY_NAMES


def run(
    brand_key: str,
    custom_questions: list = None,
    brand_words: list = None,
    product_words: list = None,
    category_words: list = None,
    competitors: list = None,
    region: str = "全国",
    period: str = "单次",
) -> dict:
    questions = custom_questions or get_geo_questions(brand_key)

    # 关键词组与竞品一并纳入检索 query，提升相关 chunk 命中
    extra_terms = " ".join(
        (brand_words or []) + (product_words or []) + (category_words or []) + (competitors or [])
    )
    query = f"品牌定位 产品特色 品牌知名度 竞品 {extra_terms}".strip()
    chunks = retrieve(brand_key, query, n_results=6)
    context = build_rag_context(chunks)

    brand_name = BRAND_DISPLAY_NAMES[brand_key]

    system = build_geo_system(
        brand_name,
        questions,
        brand_words=brand_words,
        product_words=product_words,
        category_words=category_words,
        competitors=competitors,
        region=region,
    )

    comp_hint = f"竞品对标：{ '、'.join(competitors) }\n" if competitors else ""
    user_msg = f"""品牌：{brand_name}
监测地域：{region}　|　监测周期：{period}
{comp_hint}
【品牌知识库内容（用于判断信息准确性）】
{context}

请根据以上知识库内容和你对该品牌的了解，对 {len(questions)} 个 AI 搜索问题逐一进行 GEO 可见度分析，并按结构化曝光诊断（E-E-A-T）输出。"""

    output = chat(system, user_msg, max_tokens=3800)
    return {
        "output": output,
        "chunks": chunks,
        "questions": questions,
        "_meta": {
            "brand_words": brand_words or [],
            "product_words": product_words or [],
            "category_words": category_words or [],
            "competitors": competitors or [],
            "region": region,
            "period": period,
        },
    }
