from core.rag_engine import retrieve
from core.llm_client import chat, build_rag_context
from core.fact_checker import check as refcheck
from prompts.product_analysis_prompt import SYSTEM
from config.settings import BRAND_DISPLAY_NAMES


def run(brand_key: str, product_name: str, run_refcheck: bool = False) -> dict:
    queries = [
        f"{product_name} 产品特点 原料 工艺",
        f"{product_name} 卖点 价格 用户",
        "产品价值主张 产品系列 竞品",
    ]
    all_chunks = []
    seen_texts = set()
    for q in queries:
        for chunk in retrieve(brand_key, q, n_results=3):
            if chunk["text"] not in seen_texts:
                seen_texts.add(chunk["text"])
                all_chunks.append(chunk)

    context = build_rag_context(all_chunks[:7])
    brand_name = BRAND_DISPLAY_NAMES[brand_key]

    user_msg = f"""品牌：{brand_name}
分析产品：{product_name}

【知识库内容】
{context}

请基于以上内容，对产品「{product_name}」进行专业分析。若知识库中无该产品详细信息，请基于品牌整体信息推断并明确标注 【AI推断】。"""

    output = chat(SYSTEM, user_msg, max_tokens=2000)

    result = {"output": output, "chunks": all_chunks, "refcheck": None}
    if run_refcheck:
        result["refcheck"] = refcheck(output, all_chunks[:5])
    return result
