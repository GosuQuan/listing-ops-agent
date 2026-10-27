# Cross-border Listing Ops Agent

> **一句话业务概括（面试可直接说）**  
> 我做的是跨境小团队 Listing Ops Agent：自动诊断标题卖点问题并生成多语草稿，必须人工一点通过才导出，把磨 Listing 从按「人天」变成按「分钟级草稿 + 短审批」。

Python + [LangGraph](https://github.com/langchain-ai/langgraph) 最小可运行演示：`diagnose → draft → human_approve (interrupt) → export`。

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python demo.py
# when prompted: approve   or   reject
```

No LLM API key required for the MVP (deterministic diagnosis/draft tools). After `approve`, see `outputs/listing_export_demo.json`.

## Architecture

```
START → diagnose (tool) → draft (tool) → human_approve (interrupt)
              ↓ approve                    ↓ reject
           export → END                   END
```

Checkpointing via `MemorySaver` + `thread_id`. Swap to SQLite/Postgres for durable HITL.

## Repo layout

| Path | Purpose |
|------|---------|
| `demo.py` | Runnable entry: graph + tools + human approval |
| `requirements.txt` | `langgraph` |
| `src/listing_ops/` | Package root (promote demo here later) |
| `src/listing_ops/graph/` | State & nodes |
| `src/listing_ops/tools/` | Diagnosis / draft tools |
| `src/listing_ops/prompts/` | Multilingual prompt templates |
| `data/samples/` | Sample product JSON |
| `data/eval/` | Labeled eval set (to fill) |
| `tests/` | Rule / path unit tests |
| `docs/architecture.md` | Architecture notes |
| `scripts/` | Batch eval / export scripts |
| `outputs/` | Approved exports |

## Technical challenges

1. **HITL state persistence** — `interrupt` / `Command(resume=…)`, `thread_id`, side effects after interrupt.
2. **Diagnosis stability** — rule/prompt consistency; pin empty words / duplicate terms with eval.
3. **Tool failure retry & fallback** — LLM timeout → rule draft; never silent hallucinated copy.
4. **Multilingual consistency** — EN/DE claim alignment; terminology constraints.
5. **Permission boundary** — export files only; no direct marketplace write; audit log.

## Metrics (measurable; no fake customer ROI)

| Metric | How | Demo baseline |
|--------|-----|----------------|
| `diagnose_ms` / `draft_ms` | `perf_counter` in nodes | Rule tools ~0–few ms on smoke run |
| Approval latency | interrupt → resume wall time | Depends on human |
| Approval rate | approve / total | Needs ≥20 real trials |
| Rule hit rate | vs `data/eval` labels | Sample `PET-WIPE-001` flags empty word / dup / missing EN search term |
| Time saved vs manual | `(manual − (agent+review)) / manual` | **Target** (not claimed customer data): manual often 4–8h/SKU → draft 5–15min + review 15–30min |

## Why LangGraph (vs alternatives)

| Approach | Pros | Cons | Fit for Listing Ops |
|----------|------|------|---------------------|
| **LangGraph** | Native HITL, checkpoint, conditional edges | Learning curve | **Chosen** — must pause for approval |
| Pure functions / scripts | Simple | DIY resume/branch/audit | Weak portfolio signal |
| CrewAI | Fast multi-role prototype | Weaker control/observability for hard gates | OK for spikes, not main |
| AutoGen / AG2 | Conversational multi-agent | Listing flow is a pipeline, not free chat | Secondary |

## Learning path (priority)

1. Python + TypedDict nodes  
2. LangGraph State / edges / `interrupt`  
3. Tool schema & structured errors  
4. Durable checkpointer  
5. Eval golden set  
6. Optional RAG (glossary / banned terms)  
7. Optional browser-use / MCP concepts  

## Critical build steps

Requirements → State fields → Wrap tools → Approval interrupt → Export + audit → Eval set → Swap in LLM + durable store.

## What’s next

- [ ] ≥20 labeled eval cases + CI script  
- [ ] Sqlite/Postgres checkpointer  
- [ ] LLM tool-calling draft with rule fallback  
- [ ] Lightweight RAG for brand terms / banned words  
- [ ] Structured JSONL traces  

## License

MIT
