"""Optional lightweight re-ranking (no heavy cross-encoder required)."""
from __future__ import annotations

import re
from typing import Any


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[\w\u4e00-\u9fff]+", text.lower()) if len(t) > 1}


def rerank_by_overlap(
    question: str,
    hits: list[dict[str, Any]],
    *,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """
    Re-score hits with lexical overlap against the query, blended with vector score.
    Lightweight stand-in for a cross-encoder; enable via --rerank.
    """
    q = _tokens(question)
    rescored: list[dict[str, Any]] = []
    for h in hits:
        doc_toks = _tokens(h.get("text") or "")
        overlap = len(q & doc_toks) / max(1, len(q))
        vec = float(h.get("score") or 0.0)
        blended = 0.55 * vec + 0.45 * overlap
        item = dict(h)
        item["rerank_overlap"] = overlap
        item["score"] = blended
        rescored.append(item)
    rescored.sort(key=lambda x: x["score"], reverse=True)
    if top_k is not None:
        return rescored[:top_k]
    return rescored
