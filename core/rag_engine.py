"""ChromaDB RAG engine — brand-namespaced retrieval."""
import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from config.settings import CHROMA_DB_PATH, BRAND_COLLECTIONS, CHUNK_SIZE, CHUNK_OVERLAP

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
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_text(text)
    if not chunks:
        return 0

    collection = get_collection(brand_key)
    ids = [f"{source}_{i}" for i in range(len(chunks))]
    collection.upsert(
        documents=chunks,
        ids=ids,
        metadatas=[{"source": source, "brand": brand_key} for _ in chunks],
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
    counts: dict[str, int] = {}
    for m in result["metadatas"]:
        src = m.get("source", "(unknown)")
        counts[src] = counts.get(src, 0) + 1
    return [{"source": s, "chunks": c} for s, c in sorted(counts.items())]


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
