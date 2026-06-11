"""ChromaDB RAG engine — brand-namespaced retrieval."""
import chromadb
from chromadb.utils import embedding_functions
from config.settings import CHROMA_DB_PATH, BRAND_COLLECTIONS, CHUNK_SIZE, CHUNK_OVERLAP


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """轻量文本切分（替代 langchain RecursiveCharacterTextSplitter，零额外依赖）。

    优先按段落/句子边界切分，超长则按字符滑窗，块间保留 overlap 重叠。
    """
    if not text:
        return []
    seps = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " "]
    chunks, buf = [], ""
    # 先按最强分隔符切成片段，再贪心合并到接近 chunk_size
    import re
    pieces = re.split(r"(\n\n|\n|(?<=[。！？.!?]))", text)
    for p in pieces:
        if not p:
            continue
        if len(buf) + len(p) <= chunk_size:
            buf += p
        else:
            if buf:
                chunks.append(buf)
            # 处理超长单片
            if len(p) > chunk_size:
                i = 0
                while i < len(p):
                    chunks.append(p[i:i + chunk_size])
                    i += max(1, chunk_size - overlap)
                buf = ""
            else:
                buf = p
    if buf:
        chunks.append(buf)
    # 加入块间重叠
    if overlap > 0 and len(chunks) > 1:
        out = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            out.append(prev_tail + chunks[i])
        chunks = out
    return [c.strip() for c in chunks if c.strip()]

_client = None


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _client


def get_collection(brand_key: str):
    ef = embedding_functions.DefaultEmbeddingFunction()
    return get_client().get_or_create_collection(
        name=BRAND_COLLECTIONS[brand_key],
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def ingest_text(brand_key: str, text: str, source: str) -> int:
    """Split text and upsert into the brand's collection. Returns chunk count."""
    chunks = _split_text(text, CHUNK_SIZE, CHUNK_OVERLAP)
    if not chunks:
        return 0

    collection = get_collection(brand_key)
    ids = [f"{source}_{i}" for i in range(len(chunks))]
    # F3 · 记录文件元数据：字节大小 + 上传时间
    import datetime as _dt
    size_bytes = len(text.encode("utf-8"))
    added_at = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    collection.upsert(
        documents=chunks,
        ids=ids,
        metadatas=[{"source": source, "brand": brand_key,
                    "size": size_bytes, "added_at": added_at} for _ in chunks],
    )
    return len(chunks)


def retrieve(brand_key: str, query: str, n_results: int = 5) -> list[dict]:
    """Return top-n relevant chunks with metadata."""
    collection = get_collection(brand_key)
    results = collection.query(query_texts=[query], n_results=n_results)
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    return [{"text": d, "source": m.get("source", "")} for d, m in zip(docs, metas)]


def collection_count(brand_key: str) -> int:
    return get_collection(brand_key).count()


def get_sources(brand_key: str) -> list[dict]:
    """Return unique sources in the collection with their chunk counts.
    Returns [{"source": str, "chunks": int}, ...] sorted by source name."""
    coll = get_collection(brand_key)
    if coll.count() == 0:
        return []
    result = coll.get(include=["metadatas"])
    agg: dict[str, dict] = {}
    for m in result["metadatas"]:
        src = m.get("source", "(unknown)")
        if src not in agg:
            agg[src] = {"source": src, "chunks": 0, "size": m.get("size", 0),
                        "added_at": m.get("added_at", "")}
        agg[src]["chunks"] += 1
        # size/added_at 同源一致，取已有值即可
        if not agg[src]["size"]:
            agg[src]["size"] = m.get("size", 0)
        if not agg[src]["added_at"]:
            agg[src]["added_at"] = m.get("added_at", "")
    return [agg[s] for s in sorted(agg.keys())]


def delete_source(brand_key: str, source: str) -> int:
    """Delete all chunks from a specific source. Returns number of chunks removed."""
    coll = get_collection(brand_key)
    result = coll.get(include=["metadatas"])
    ids_to_delete = [
        id_ for id_, meta in zip(result["ids"], result["metadatas"])
        if meta.get("source") == source
    ]
    if ids_to_delete:
        coll.delete(ids=ids_to_delete)
    return len(ids_to_delete)


def clear_collection(brand_key: str) -> int:
    """Delete ALL chunks from a brand's collection. Returns count removed."""
    coll = get_collection(brand_key)
    count = coll.count()
    if count > 0:
        result = coll.get(include=[])
        coll.delete(ids=result["ids"])
    return count
