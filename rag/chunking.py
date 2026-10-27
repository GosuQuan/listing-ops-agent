"""Semantic-ish chunking with token-budget windows and overlap."""
from __future__ import annotations

import re
from dataclasses import dataclass


def estimate_tokens(text: str) -> int:
    """Approximate tokens: prefer tiktoken if installed, else ~4 chars/token."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        return max(1, (len(text) + 3) // 4)


@dataclass
class Chunk:
    id: str
    text: str
    source: str
    index: int
    token_estimate: int


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text.strip())
    return [p.strip() for p in parts if p.strip()]


def chunk_document(
    text: str,
    source: str,
    *,
    min_tokens: int = 500,
    max_tokens: int = 1000,
    overlap_tokens: int = 100,
) -> list[Chunk]:
    """
    Pack paragraphs into chunks targeting [min_tokens, max_tokens].
    Adjacent chunks overlap by roughly `overlap_tokens` (default 100).
    Oversized paragraphs are hard-split by sentence / character budget.
    """
    if min_tokens > max_tokens:
        raise ValueError("min_tokens must be <= max_tokens")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be in [0, max_tokens)")

    paragraphs = _split_paragraphs(text)
    units: list[str] = []
    for para in paragraphs:
        if estimate_tokens(para) <= max_tokens:
            units.append(para)
            continue
        # Split long paragraph by sentences, then by hard window if needed.
        sentences = re.split(r"(?<=[。！？.!?])\s*", para)
        buf = ""
        for sent in sentences:
            if not sent:
                continue
            candidate = f"{buf} {sent}".strip() if buf else sent
            if estimate_tokens(candidate) <= max_tokens:
                buf = candidate
            else:
                if buf:
                    units.append(buf)
                if estimate_tokens(sent) <= max_tokens:
                    buf = sent
                else:
                    # Hard char window ~ max_tokens * 4
                    step = max_tokens * 4
                    for i in range(0, len(sent), step):
                        units.append(sent[i : i + step])
                    buf = ""
        if buf:
            units.append(buf)

    chunks: list[Chunk] = []
    i = 0
    chunk_idx = 0
    while i < len(units):
        buf_parts: list[str] = []
        buf_tokens = 0
        j = i
        while j < len(units):
            t = estimate_tokens(units[j])
            if buf_parts and buf_tokens + t > max_tokens:
                break
            buf_parts.append(units[j])
            buf_tokens += t
            j += 1
            if buf_tokens >= min_tokens:
                # Prefer stopping once we reached the min window unless next unit still fits.
                if j >= len(units) or buf_tokens + estimate_tokens(units[j]) > max_tokens:
                    break

        if not buf_parts:
            # Single oversized unit fallback
            buf_parts = [units[i]]
            j = i + 1
            buf_tokens = estimate_tokens(buf_parts[0])

        text_chunk = "\n\n".join(buf_parts)
        chunks.append(
            Chunk(
                id=f"{source}::chunk-{chunk_idx}",
                text=text_chunk,
                source=source,
                index=chunk_idx,
                token_estimate=estimate_tokens(text_chunk),
            )
        )
        chunk_idx += 1

        if j >= len(units):
            break

        # Walk back to create overlap ~ overlap_tokens from the end of this chunk.
        overlap_parts: list[str] = []
        ot = 0
        for part in reversed(buf_parts):
            pt = estimate_tokens(part)
            if overlap_parts and ot + pt > overlap_tokens:
                break
            overlap_parts.insert(0, part)
            ot += pt
            if ot >= overlap_tokens:
                break
        # Next start = first unit after the non-overlap prefix.
        next_i = j - len(overlap_parts)
        if next_i <= i:
            next_i = i + 1  # guarantee progress
        i = next_i

    return chunks
