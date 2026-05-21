import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# RAG chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# ChromaDB collection names — one per brand (namespace isolation)
BRAND_COLLECTIONS = {
    "heytea": "brandpulse_heytea",
    "nayuki": "brandpulse_nayuki",
    "chapanda": "brandpulse_chapanda",
}

BRAND_DISPLAY_NAMES = {
    "heytea": "喜茶 HEYTEA",
    "nayuki": "奈雪的茶 Nayuki",
    "chapanda": "茶百道 ChaPanda",
}

BRAND_FOCUS = {
    "heytea": "品牌创新、年轻化表达、跨界联名",
    "nayuki": "生活方式（茶+软欧包）、空间场景、女性客群",
    "chapanda": "加盟体系、下沉市场、熊猫IP、供应链优势",
}
