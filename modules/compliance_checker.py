from core.llm_client import chat
from core.rag_engine import retrieve
from core.llm_client import build_rag_context
from prompts.compliance_check_prompt import SYSTEM
from config.settings import BRAND_DISPLAY_NAMES


def run(content: str, brand_key: str) -> dict:
    brand_name = BRAND_DISPLAY_NAMES.get(brand_key, "")
    chunks = retrieve(brand_key, "品牌定位 官方事实 品牌调性", n_results=4)
    kb_context = build_rag_context(chunks)

    user_msg = f"""品牌：{brand_name}

【品牌知识库（用于核实事实）】
{kb_context}

【待审查内容】
{content}

请对以上内容进行全面合规审查，并与品牌知识库内容进行比对核实。"""

    output = chat(SYSTEM, user_msg, max_tokens=2000)
    return {"output": output, "chunks": chunks}
