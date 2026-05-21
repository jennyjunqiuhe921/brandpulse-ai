from core.rag_engine import retrieve
from core.llm_client import chat, build_rag_context
from core.fact_checker import check as refcheck
from prompts.brand_analysis_prompt import SYSTEM
from config.settings import BRAND_DISPLAY_NAMES


def run(brand_key: str, run_refcheck: bool = False) -> dict:
    queries = [
        "品牌定位 品牌理念 品牌主张",
        "品牌调性 目标客群 品牌风格",
        "品牌优势 产品特色 品牌一致性",
        "品牌风险 挑战 竞争",
    ]
    all_chunks = []
    seen_texts = set()
    for q in queries:
        for chunk in retrieve(brand_key, q, n_results=3):
            if chunk["text"] not in seen_texts:
                seen_texts.add(chunk["text"])
                all_chunks.append(chunk)

    context = build_rag_context(all_chunks[:8])
    brand_name = BRAND_DISPLAY_NAMES[brand_key]

    user_msg = f"""品牌：{brand_name}

【知识库内容】
{context}

请基于以上知识库内容，输出完整的品牌分析报告。"""

    output = chat(SYSTEM, user_msg, max_tokens=2500)

    result = {"output": output, "chunks": all_chunks, "refcheck": None}
    if run_refcheck:
        result["refcheck"] = refcheck(output, all_chunks[:5])
    return result
