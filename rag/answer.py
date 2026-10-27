"""Answer generation: LLM if configured, else retrieval-only stub."""
from __future__ import annotations

import os
from typing import Any


SYSTEM_PROMPT = (
    "你是跨境电商 Listing Ops 助手。只根据提供的资料片段回答；"
    "资料不足时明确说不知道，不要编造客户 ROI 或虚假指标。"
)


def format_context(hits: list[dict[str, Any]]) -> str:
    blocks = []
    for i, h in enumerate(hits, 1):
        src = (h.get("metadata") or {}).get("source", "unknown")
        blocks.append(f"[{i}] source={src} score={h.get('score', 0):.3f}\n{h.get('text', '')}")
    return "\n\n".join(blocks)


def stub_answer(question: str, hits: list[dict[str, Any]]) -> str:
    if not hits:
        return (
            "（检索模式）未检索到相关片段，无法作答。"
            "可先重建索引：python -m rag.demo --rebuild"
        )
    lines = [
        "（检索模式 / 未配置 LLM）下面根据向量检索结果整理要点；"
        "设置 OPENAI_API_KEY（或 OPENAI_BASE_URL + 兼容密钥）后可生成完整回答。",
        "",
        f"问题：{question}",
        "",
        "相关片段摘要：",
    ]
    for i, h in enumerate(hits, 1):
        src = (h.get("metadata") or {}).get("source", "unknown")
        snippet = (h.get("text") or "").replace("\n", " ")
        if len(snippet) > 220:
            snippet = snippet[:220] + "…"
        lines.append(f"{i}. [{src}] {snippet}")
    lines.append("")
    lines.append("建议：结合品牌词表 / 禁限词规则复核后再改 Listing。")
    return "\n".join(lines)


def llm_answer(question: str, hits: list[dict[str, Any]]) -> str | None:
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    if not api_key:
        return None
    base_url = os.environ.get("OPENAI_BASE_URL") or os.environ.get("LLM_BASE_URL")
    model = os.environ.get("OPENAI_MODEL") or os.environ.get("LLM_MODEL") or "gpt-4o-mini"

    try:
        from openai import OpenAI
    except ImportError:
        return (
            "已检测到 API Key，但未安装 openai 包。"
            "请执行：pip install openai"
        )

    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    context = format_context(hits)
    user = (
        f"资料片段：\n{context}\n\n"
        f"用户问题：{question}\n\n"
        "请用简洁中文回答，并在关键处标注引用编号如 [1]。"
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as exc:
        # Region blocks / bad keys / network: fall back to retrieval stub.
        return None


def answer_question(question: str, hits: list[dict[str, Any]]) -> tuple[str, str]:
    """Returns (mode, answer_text). mode is 'llm' or 'retrieval_stub'."""
    llm = llm_answer(question, hits)
    if llm is not None and not llm.startswith("已检测到 API Key"):
        return "llm", llm
    if llm is not None:
        return "retrieval_stub", llm + "\n\n" + stub_answer(question, hits)
    return "retrieval_stub", stub_answer(question, hits)
