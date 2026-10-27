"""
Minimal runnable demo: Cross-border Listing Ops Agent (LangGraph + human approval).
No LLM API key required — diagnosis/draft use deterministic "tools" so you can see the graph flow.

Run:
  python demo.py
When prompted, type: approve   or   reject
"""
from __future__ import annotations

import json
import time
from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


class ListingState(TypedDict, total=False):
    product: dict[str, Any]
    diagnosis: list[str]
    draft_en: str
    draft_de: str
    approved: bool
    export_path: str
    metrics: dict[str, Any]


SAMPLE_PRODUCT = {
    "sku": "PET-WIPE-001",
    "title_zh": "竹纤维宠物湿巾 high quality 竹纤维",
    "bullets_zh": ["清洁爪子", "无酒精", "温和不刺激"],
    "category": "pet_wipes",
    "target_markets": ["US", "DE"],
}


def tool_diagnose_listing(product: dict[str, Any]) -> list[str]:
    """Deterministic diagnosis tool (stands in for an LLM tool call in the MVP)."""
    issues: list[str] = []
    title = product.get("title_zh", "")
    if "high quality" in title.lower():
        issues.append("标题含空词 'high quality'，建议删除")
    if title.count("竹纤维") >= 2:
        issues.append("标题重复词 '竹纤维'")
    if "无酒精" not in " ".join(product.get("bullets_zh", [])):
        issues.append("五点描述缺少核心卖点：无酒精")
    else:
        # still flag if only in bullets but not title keywords buyers search
        pass
    lower = title.lower()
    if "wipe" not in lower and "湿巾" in title:
        issues.append("英文检索词缺失：建议加入 'wet wipes' / pet paw wipes")
    if not issues:
        issues.append("未发现明显硬伤（规则集很小，仅作 demo）")
    return issues


def tool_draft_multilang(product: dict[str, Any], diagnosis: list[str]) -> tuple[str, str]:
    """Deterministic draft tool — replace with LLM later."""
    name = "Bamboo Fiber Pet Wet Wipes"
    bullets = [
        "Gentle paw & body cleaning for dogs and cats",
        "Alcohol-free formula, mild on skin",
        "Bamboo fiber, soft and low-lint",
    ]
    en = (
        f"Title: {name} — Alcohol-Free Paw Cleaning\n"
        f"Bullets:\n- " + "\n- ".join(bullets) + "\n"
        f"Notes from diagnosis: {'; '.join(diagnosis)}"
    )
    de = (
        "Titel: Bambusfaser Haustier-Feuchttücher — Alkoholfrei\n"
        "Bullet Points:\n"
        "- Sanfte Reinigung für Pfoten und Körper\n"
        "- Alkoholfrei, hautfreundlich\n"
        "- Weiche Bambusfaser\n"
        f"Hinweise: {'; '.join(diagnosis)}"
    )
    return en, de


def node_diagnose(state: ListingState) -> dict[str, Any]:
    t0 = time.perf_counter()
    issues = tool_diagnose_listing(state["product"])
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    metrics = dict(state.get("metrics") or {})
    metrics["diagnose_ms"] = elapsed_ms
    return {"diagnosis": issues, "metrics": metrics}


def node_draft(state: ListingState) -> dict[str, Any]:
    t0 = time.perf_counter()
    en, de = tool_draft_multilang(state["product"], state.get("diagnosis") or [])
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    metrics = dict(state.get("metrics") or {})
    metrics["draft_ms"] = elapsed_ms
    return {"draft_en": en, "draft_de": de, "metrics": metrics}


def node_human_approve(state: ListingState) -> dict[str, Any]:
    """Human-in-the-loop: graph pauses here until Command(resume=...)."""
    decision = interrupt(
        {
            "action": "approve_listing_draft",
            "sku": state["product"].get("sku"),
            "diagnosis": state.get("diagnosis"),
            "draft_en_preview": (state.get("draft_en") or "")[:400],
            "hint": "resume with 'approve' or 'reject'",
        }
    )
    ok = str(decision).strip().lower() in {"approve", "approved", "yes", "y"}
    return {"approved": ok}


def node_export(state: ListingState) -> dict[str, Any]:
    if not state.get("approved"):
        metrics = dict(state.get("metrics") or {})
        metrics["exported"] = False
        return {"export_path": "", "metrics": metrics}

    payload = {
        "sku": state["product"].get("sku"),
        "diagnosis": state.get("diagnosis"),
        "draft_en": state.get("draft_en"),
        "draft_de": state.get("draft_de"),
        "approved": True,
    }
    path = "outputs/listing_export_demo.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    metrics = dict(state.get("metrics") or {})
    metrics["exported"] = True
    metrics["total_agent_ms"] = int(metrics.get("diagnose_ms", 0)) + int(
        metrics.get("draft_ms", 0)
    )
    return {"export_path": path, "metrics": metrics}


def route_after_approval(state: ListingState) -> str:
    return "export" if state.get("approved") else "end_rejected"


def build_graph():
    g = StateGraph(ListingState)
    g.add_node("diagnose", node_diagnose)
    g.add_node("draft", node_draft)
    g.add_node("human_approve", node_human_approve)
    g.add_node("export", node_export)

    g.add_edge(START, "diagnose")
    g.add_edge("diagnose", "draft")
    g.add_edge("draft", "human_approve")
    g.add_conditional_edges(
        "human_approve",
        route_after_approval,
        {"export": "export", "end_rejected": END},
    )
    g.add_edge("export", END)

    return g.compile(checkpointer=MemorySaver())


def main() -> None:
    graph = build_graph()
    config = {"configurable": {"thread_id": "listing-demo-1"}}

    print("=== Listing Ops Agent demo ===")
    print("Product:", SAMPLE_PRODUCT["sku"], SAMPLE_PRODUCT["title_zh"])
    print("Running until human approval...\n")

    result = graph.invoke({"product": SAMPLE_PRODUCT, "metrics": {}}, config)

    # First invoke stops at interrupt
    interrupts = result.get("__interrupt__")
    if interrupts:
        payload = interrupts[0].value
        print("--- PENDING APPROVAL ---")
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        decision = input("\nType approve or reject, then Enter: ").strip() or "reject"
        result = graph.invoke(Command(resume=decision), config)

    print("\n=== DONE ===")
    print("approved:", result.get("approved"))
    print("export_path:", result.get("export_path") or "(none)")
    print("metrics:", result.get("metrics"))
    if result.get("draft_en"):
        print("\nDraft EN preview:\n", result["draft_en"][:500])


if __name__ == "__main__":
    main()
