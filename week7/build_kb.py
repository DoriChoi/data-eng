"""Week 7 deliverable 2: idempotent MinIO -> Qdrant vector knowledge base.

Run in ~/data-eng/week7 with a configured local rag_env.py and minio_env.py.
No credentials are included.
"""
import os
import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, FieldCondition, Filter, FilterSelector,
    MatchValue, PointStruct, VectorParams,
)
from minio_env import mc, read_text
from rag_env import get_emb

BUCKET = os.getenv("BUCKET", "raw-docs")
COLLECTION = os.getenv("COLLECTION", "lecture_kb")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "300"))
CHUNK_OVERLAP = CHUNK_SIZE // 10
if CHUNK_SIZE <= 0 or CHUNK_OVERLAP >= CHUNK_SIZE:
    raise ValueError("CHUNK_SIZE must be positive and exceed overlap")

emb = get_emb()
client = QdrantClient(url=QDRANT_URL)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP
)

def ensure_collection(dim):
    if client.collection_exists(COLLECTION):
        cfg = client.get_collection(COLLECTION).config.params.vectors
        if cfg.size != dim:
            raise ValueError(f"Collection size {cfg.size} differs from embedding {dim}")
        if cfg.distance != Distance.COSINE:
            raise ValueError("Existing collection distance is not Cosine")
    else:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

def ingest_one(key):
    source = f"minio://{BUCKET}/{key}"
    text = read_text(BUCKET, key)
    chunks = splitter.split_text(text)
    vectors = emb.embed_documents(chunks) if chunks else []
    ids = [
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source}#{i}"))
        for i in range(len(chunks))
    ]
    points = [
        PointStruct(
            id=ids[i],
            vector=vectors[i],
            payload={"text": chunk, "source": source, "chunk_index": i},
        )
        for i, chunk in enumerate(chunks)
    ]
    client.delete(
        collection_name=COLLECTION,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=source))]
            )
        ),
        wait=True,
    )
    if points:
        client.upsert(collection_name=COLLECTION, points=points, wait=True)
    print(f"{source} -> {len(points)} chunks")
    return len(points)

def main():
    dim = len(emb.embed_query("dimension check"))
    ensure_collection(dim)
    objects = sorted(
        obj.object_name for obj in mc.list_objects(BUCKET, recursive=True)
        if obj.object_name.endswith(".txt")
    )
    if not objects:
        raise RuntimeError(f"No .txt files found in {BUCKET}; no data modified")
    total = sum(ingest_one(key) for key in objects)
    print(f"적재 {total} 조각 · 총 {client.count(COLLECTION, exact=True).count}")

if __name__ == "__main__":
    main()
