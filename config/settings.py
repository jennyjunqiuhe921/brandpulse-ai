import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "anthropic/claude-sonnet-4-5")
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# RAG chunking
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


# ── _LiveDict: dict-like proxy that reads live from brand_manager ─────────────
class _LiveDict:
    """
    Behaves exactly like a plain dict for all existing code:
        BRAND_DISPLAY_NAMES[key]          → brand name string
        BRAND_DISPLAY_NAMES.get(key, "")  → safe get
        BRAND_DISPLAY_NAMES.keys()        → all brand IDs
        BRAND_DISPLAY_NAMES.items()       → (id, value) pairs
        for k in BRAND_DISPLAY_NAMES      → iterate IDs
        "heytea" in BRAND_DISPLAY_NAMES   → membership test
    """

    def __init__(self, field: str):
        self._field = field

    def _all(self) -> dict:
        from config.brand_manager import load_all_brands
        return load_all_brands()

    def __getitem__(self, key: str):
        brands = self._all()
        if key not in brands:
            raise KeyError(key)
        return brands[key].get(self._field, "")

    def get(self, key: str, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def keys(self):
        return self._all().keys()

    def values(self):
        field = self._field
        return [b.get(field, "") for b in self._all().values()]

    def items(self):
        field = self._field
        return [(k, v.get(field, "")) for k, v in self._all().items()]

    def __contains__(self, key):
        return key in self._all()

    def __iter__(self):
        return iter(self._all())

    def __len__(self):
        return len(self._all())


# ── Public API — drop-in replacements for the old hardcoded dicts ─────────────
BRAND_DISPLAY_NAMES = _LiveDict("name")
BRAND_FOCUS         = _LiveDict("focus")
BRAND_COLLECTIONS   = _LiveDict("collection_name")

# BRAND_FOCUS alias used in some prompts
BRAND_FOCUS = BRAND_FOCUS  # noqa (kept for clarity)
