"""VectorAI-style store for difficulty pattern embeddings (ChromaDB)."""
import os
from typing import Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from .config import VECTOR_DB_PATH, EMBEDDING_MODEL

# Pre-defined difficulty pattern clusters (Actian VectorAI conceptual equivalent)
DIFFICULTY_CLUSTERS = [
    "frustration spike - player shows clear signs of anger or intense frustration",
    "overwhelmed behavior - player appears lost, confused, or unable to keep up",
    "mastery flow state - player is in the zone, engaged and performing well",
    "perfect difficulty balance - challenge matches skill, optimal engagement",
    "unfair enemy pattern - player struggles with specific mechanics that feel cheap",
    "too easy under-stimulated - player bored, distracted, not challenged",
]

_clients: dict[str, chromadb.PersistentClient] = {}
_models: dict[str, SentenceTransformer] = {}


def _get_client(collection_name: str = "difficulty_patterns"):
    """Get or create ChromaDB client."""
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)
    key = VECTOR_DB_PATH
    if key not in _clients:
        _clients[key] = chromadb.PersistentClient(
            path=VECTOR_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
    return _clients[key]


def _get_embedding_model() -> SentenceTransformer:
    """Lazy-load embedding model."""
    if EMBEDDING_MODEL not in _models:
        _models[EMBEDDING_MODEL] = SentenceTransformer(EMBEDDING_MODEL)
    return _models[EMBEDDING_MODEL]


def ensure_collection() -> chromadb.Collection:
    """Ensure difficulty_patterns collection exists and is seeded."""
    client = _get_client()
    coll = client.get_or_create_collection(
        "difficulty_patterns", metadata={"description": "GameSense difficulty embeddings"}
    )
    # Re-seed if empty (e.g. a previous start failed to download the embedding model)
    if coll.count() == 0:
        try:
            _seed_collection(coll)
        except Exception:
            client.delete_collection("difficulty_patterns")
            raise
    return coll


def _seed_collection(coll: chromadb.Collection):
    """Seed collection with canonical difficulty cluster embeddings."""
    model = _get_embedding_model()
    embeddings = model.encode(DIFFICULTY_CLUSTERS).tolist()
    ids = [f"cluster_{i}" for i in range(len(DIFFICULTY_CLUSTERS))]
    coll.add(
        ids=ids,
        embeddings=embeddings,
        documents=DIFFICULTY_CLUSTERS,
        metadatas=[{"cluster": c} for c in DIFFICULTY_CLUSTERS],
    )


def add_embedding(
    text_or_description: str,
    doc_id: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> str:
    """Add a custom embedding to the store."""
    coll = ensure_collection()
    model = _get_embedding_model()
    emb = model.encode([text_or_description]).tolist()[0]
    uid = doc_id or f"custom_{hash(text_or_description) % 10**10}"
    coll.add(
        ids=[uid],
        embeddings=[emb],
        documents=[text_or_description],
        metadatas=[metadata or {}],
    )
    return uid


def query_similar(
    text: str,
    n_results: int = 3,
) -> list[tuple[str, float, str]]:
    """
    Query for similar difficulty patterns.
    Returns list of (cluster/doc, distance, document).
    Chroma uses L2; we convert to similarity-ish: 1 / (1 + distance).
    """
    coll = ensure_collection()
    model = _get_embedding_model()
    query_emb = model.encode([text]).tolist()
    res = coll.query(
        query_embeddings=query_emb,
        n_results=min(n_results, coll.count()),
        include=["documents", "distances", "metadatas"],
    )
    out: list[tuple[str, float, str]] = []
    docs = res["documents"][0] if res["documents"] else []
    dists = res["distances"][0] if res["distances"] else []
    metas = res["metadatas"][0] if res["metadatas"] else []
    for i, (doc, dist) in enumerate(zip(docs, dists)):
        cluster = metas[i].get("cluster", doc) if metas else doc
        sim = 1.0 / (1.0 + float(dist))
        out.append((cluster, sim, doc))
    return out


def get_cluster_name(doc: str) -> str:
    """Extract short cluster name from document."""
    for c in DIFFICULTY_CLUSTERS:
        if c.lower().startswith(doc[:30].lower()) or doc in c:
            return c.split(" - ")[0] if " - " in c else c[:40]
    return doc[:50] + "..." if len(doc) > 50 else doc
