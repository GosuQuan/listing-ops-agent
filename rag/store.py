"""Chroma local vector store helpers."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

from .chunking import Chunk

DEFAULT_COLLECTION = "listing_ops_rag"
DEFAULT_PERSIST = Path(__file__).resolve().parent / ".chroma"


def get_client(persist_dir: Path | str | None = None) -> chromadb.PersistentClient:
    path = Path(persist_dir) if persist_dir else DEFAULT_PERSIST
    path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(path),
        settings=Settings(anonymized_telemetry=False),
    )


def reset_collection(
    client: chromadb.PersistentClient,
    name: str = DEFAULT_COLLECTION,
) -> chromadb.Collection:
    try:
        client.delete_collection(name)
    except Exception:
        pass
    # Default embedding function (ONNX MiniLM) — works offline after first download.
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def get_collection(
    client: chromadb.PersistentClient,
    name: str = DEFAULT_COLLECTION,
) -> chromadb.Collection:
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(collection: chromadb.Collection, chunks: list[Chunk]) -> int:
    if not chunks:
        return 0
    collection.upsert(
        ids=[c.id for c in chunks],
        documents=[c.text for c in chunks],
        metadatas=[
            {
                "source": c.source,
                "index": c.index,
                "token_estimate": c.token_estimate,
            }
            for c in chunks
        ],
    )
    return len(chunks)


def query_similar(
    collection: chromadb.Collection,
    question: str,
    top_k: int = 4,
) -> list[dict[str, Any]]:
    n = max(1, min(top_k, max(1, collection.count())))
    raw = collection.query(
        query_texts=[question],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
    docs = (raw.get("documents") or [[]])[0]
    metas = (raw.get("metadatas") or [[]])[0]
    dists = (raw.get("distances") or [[]])[0]
    ids = (raw.get("ids") or [[]])[0]
    out: list[dict[str, Any]] = []
    for i, doc in enumerate(docs):
        dist = dists[i] if i < len(dists) else None
        # Chroma cosine distance: lower is better. Convert to similarity-ish score.
        score = (1.0 - float(dist)) if dist is not None else 0.0
        out.append(
            {
                "id": ids[i] if i < len(ids) else f"hit-{i}",
                "text": doc,
                "metadata": metas[i] if i < len(metas) else {},
                "distance": dist,
                "score": score,
            }
        )
    return out
