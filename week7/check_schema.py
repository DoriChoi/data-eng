"""Verify the vector-schema.yaml against the active embedding and Qdrant."""
import yaml
from qdrant_client import QdrantClient
from rag_env import get_emb

with open("vector-schema.yaml", encoding="utf-8") as f:
    spec = yaml.safe_load(f)

cfg = QdrantClient(url="http://localhost:6333").get_collection(
    spec["collection"]
).config.params.vectors
real_dim = len(get_emb().embed_query("dimension check"))
assert spec["embedding"]["dim"] == spec["vector"]["size"], "Schema dimension mismatch"
assert real_dim == spec["embedding"]["dim"], (
    f"Embedding dimension mismatch: actual={real_dim} schema={spec['embedding']['dim']}"
)
assert cfg.size == spec["vector"]["size"], (
    f"Qdrant dimension mismatch: actual={cfg.size} schema={spec['vector']['size']}"
)
assert cfg.distance.value.lower() == spec["vector"]["distance"].lower(), "Distance mismatch"
print("정의서와 실제 일치 —", cfg.size, cfg.distance)
