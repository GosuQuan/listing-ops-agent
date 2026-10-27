"""
Standalone local RAG demo for Listing Ops knowledge (guidelines / banned terms).

Pipeline:
  load docs → chunk (500–1000 tokens, overlap) → embed + Chroma persist
  → similarity top-k → optional overlap re-rank → LLM or retrieval stub answer

Run from repo root:
  python -m rag.demo
  python -m rag.demo "宠物湿巾标题有哪些常见问题？"
  python -m rag.demo --rebuild --rerank --top-k 5 "禁限词有哪些？"

Env (optional LLM answer):
  OPENAI_API_KEY / LLM_API_KEY
  OPENAI_BASE_URL / LLM_BASE_URL
  OPENAI_MODEL / LLM_MODEL   (default gpt-4o-mini)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow `python rag/demo.py` as well as `python -m rag.demo`
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from rag.answer import answer_question
from rag.chunking import chunk_document, estimate_tokens
from rag.load import load_documents
from rag.rerank import rerank_by_overlap
from rag.store import (
    DEFAULT_COLLECTION,
    DEFAULT_PERSIST,
    get_client,
    get_collection,
    query_similar,
    reset_collection,
    upsert_chunks,
)

DEFAULT_QUESTION = "跨境 Listing 标题里重复关键词和空洞形容词一般怎么处理？禁限词要注意什么？"


def build_index(*, rebuild: bool = False, data_dir: Path | None = None) -> tuple[int, int]:
    client = get_client(DEFAULT_PERSIST)
    if rebuild or _needs_index(client):
        collection = reset_collection(client, DEFAULT_COLLECTION)
        docs = load_documents(data_dir)
        all_chunks = []
        for source, text in docs:
            all_chunks.extend(
                chunk_document(
                    text,
                    source=source,
                    min_tokens=500,
                    max_tokens=1000,
                    overlap_tokens=100,
                )
            )
        # Short sample docs may produce sub-500 chunks; still index them.
        if not all_chunks:
            raise RuntimeError("No chunks produced from sample docs")
        n = upsert_chunks(collection, all_chunks)
        return len(docs), n

    collection = get_collection(client, DEFAULT_COLLECTION)
    return -1, collection.count()


def _needs_index(client) -> bool:
    try:
        col = get_collection(client, DEFAULT_COLLECTION)
        return col.count() == 0
    except Exception:
        return True


def run_query(
    question: str,
    *,
    top_k: int = 4,
    rerank: bool = False,
    rebuild: bool = False,
) -> None:
    n_docs, n_chunks = build_index(rebuild=rebuild)
    if n_docs >= 0:
        print(f"[index] indexed {n_docs} docs → {n_chunks} chunks → {DEFAULT_PERSIST}")
    else:
        print(f"[index] using existing collection ({n_chunks} chunks) at {DEFAULT_PERSIST}")

    client = get_client(DEFAULT_PERSIST)
    collection = get_collection(client, DEFAULT_COLLECTION)
    fetch_k = max(top_k, top_k * 2 if rerank else top_k)
    hits = query_similar(collection, question, top_k=fetch_k)
    if rerank:
        hits = rerank_by_overlap(question, hits, top_k=top_k)
    else:
        hits = hits[:top_k]

    print("\n=== Retrieved chunks ===")
    for i, h in enumerate(hits, 1):
        meta = h.get("metadata") or {}
        preview = (h.get("text") or "").replace("\n", " ")
        if len(preview) > 180:
            preview = preview[:180] + "…"
        print(
            f"{i}. id={h.get('id')} source={meta.get('source')} "
            f"score={h.get('score', 0):.3f} tokens≈{meta.get('token_estimate')}"
        )
        print(f"   {preview}")

    mode, answer = answer_question(question, hits)
    print(f"\n=== Answer ({mode}) ===")
    print(answer)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Listing Ops local RAG demo")
    parser.add_argument(
        "question",
        nargs="?",
        default=DEFAULT_QUESTION,
        help="Question to ask over sample docs",
    )
    parser.add_argument("--top-k", type=int, default=4, help="Similarity top-k (default 4)")
    parser.add_argument(
        "--rerank",
        action="store_true",
        help="Optional lexical-overlap re-rank after vector retrieval",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Drop and rebuild the local Chroma collection",
    )
    parser.add_argument(
        "--show-chunk-stats",
        action="store_true",
        help="Print chunk token estimates for sample docs and exit",
    )
    args = parser.parse_args(argv)

    if args.show_chunk_stats:
        for source, text in load_documents():
            chunks = chunk_document(text, source=source)
            sizes = [c.token_estimate for c in chunks]
            print(f"{source}: doc_tokens≈{estimate_tokens(text)} chunks={len(chunks)} sizes={sizes}")
        return 0

    run_query(
        args.question,
        top_k=args.top_k,
        rerank=args.rerank,
        rebuild=args.rebuild,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
