from core.rag_engine import retrieve
from core.llm_client import chat, build_rag_context
from prompts.content_generation_prompt import build_system, PLATFORM_GUIDES
from config.settings import BRAND_DISPLAY_NAMES, BRAND_FOCUS

TONE_MAP = {
    "酷/有态度": "极简、有态度、拒绝平庸，不煽情，用词简洁克制",
    "温柔/精致": "温暖细腻，有生活仪式感，语气亲切优雅",
    "亲民/接地气": "轻松幽默，贴近生活，emoji 友好，互动感强",
}


def run(
    brand_key: str,
    product_name: str,
    platforms: list,
    tone_key: str,
    goal: str,
    selling_points: str = "",
    versions_per_platform: int = 3,
    word_limit: str = "",
    region: str = "",
    run_refcheck: bool = False,
) -> dict:
    chunks = retrieve(brand_key, f"{product_name} 产品特点 卖点 品牌调性", n_results=5)
    context = build_rag_context(chunks)

    brand_name = BRAND_DISPLAY_NAMES[brand_key]
    brand_focus = BRAND_FOCUS[brand_key]
    tone = TONE_MAP.get(tone_key, tone_key)

    # F1/F2 · 读取品牌词库、禁用词库与品牌调性
    from config.brand_manager import get_brand
    _b = get_brand(brand_key) or {}
    brand_words = _b.get("brand_words", [])
    forbidden_words = _b.get("forbidden_words", [])
    brand_tone_enum = _b.get("tone", "")
    if brand_tone_enum:
        tone = f"{brand_tone_enum}；{tone}"

    platform_instructions = "\n".join(
        f"**{p}**：{PLATFORM_GUIDES.get(p, '')}" for p in platforms
    )

    system = build_system(
        brand_name,
        tone,
        brand_focus,
        versions_per_platform=versions_per_platform,
        word_limit=word_limit,
        region=region,
        brand_words=brand_words,
        forbidden_words=forbidden_words,
    )

    n_ver = max(2, min(int(versions_per_platform or 3), 5))
    sp_block = f"核心卖点：{selling_points}\n" if selling_points else ""

    user_msg = f"""产品：{product_name}
{sp_block}推广目标：{goal}
目标平台及要求：
{platform_instructions}

【品牌知识库内容】
{context}

请为以上每个平台生成完整内容，每个平台 {n_ver} 个差异化版本，用 --- 分隔不同平台。"""

    output = chat(system, user_msg, max_tokens=4000)
    return {
        "output": output,
        "chunks": chunks,
        "platforms": platforms,
        "_meta": {
            "product_name": product_name,
            "selling_points": selling_points,
            "goal": goal,
            "tone_key": tone_key,
            "platforms": platforms,
            "versions_per_platform": versions_per_platform,
            "word_limit": word_limit,
            "region": region,
        },
    }
