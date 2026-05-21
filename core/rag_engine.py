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
