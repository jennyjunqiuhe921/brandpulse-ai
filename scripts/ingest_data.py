"""
Batch ingest: reads all .md / .txt / .pdf files under data/{brand}/
and upserts them into the brand's ChromaDB collection.

Usage:
    python scripts/ingest_data.py              # ingest all brands
    python scripts/ingest_data.py heytea       # ingest one brand
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.rag_engine import ingest_text
from config.settings import BRAND_COLLECTIONS


def ingest_brand(brand_key: str):
    data_dir = Path("data") / brand_key
    if not data_dir.exists():
        print(f"[SKIP] {data_dir} not found")
        return

    total = 0
    for fp in data_dir.rglob("*"):
        if fp.suffix == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(fp))
            text = "\n".join(p.extract_text() or "" for p in reader.pages)
        elif fp.suffix in {".md", ".txt"}:
            text = fp.read_text(encoding="utf-8")
        else:
            continue

        count = ingest_text(brand_key, text, source=fp.name)
        print(f"  [{brand_key}] {fp.name} → {count} chunks")
        total += count

    print(f"  [{brand_key}] Total: {total} chunks ingested\n")


if __name__ == "__main__":
    brands = sys.argv[1:] if len(sys.argv) > 1 else list(BRAND_COLLECTIONS.keys())
    for brand in brands:
        ingest_brand(brand)
