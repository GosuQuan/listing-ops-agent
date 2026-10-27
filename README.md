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
| `requirements.txt` | `langgraph` + RAG deps (`chromadb`, optional `openai`/`tiktoken`) |
| `rag/` | Local document Q&A (Chroma) mini-demo |
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


## Local RAG mini-demo (`rag/`)

Optional knowledge layer for glossary / banned terms / title guidelines. Independent of the LangGraph HITL flow.

**Pipeline:** load `.md`/`.txt` → chunk (~500–1000 tokens, ~100-token overlap) → embed + persist in local Chroma → similarity top-k → optional lexical re-rank → answer (LLM if API key, else retrieval stub).

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# first run downloads a small ONNX embedding model via Chroma (then works offline)
python -m rag.demo --rebuild
python -m rag.demo "宠物湿巾标题有哪些常见问题？禁限词要注意什么？"
python -m rag.demo --rerank --top-k 5 "哪些宣称不能写在宠物湿巾 Listing？"
```

| Item | Detail |
|------|--------|
| Sample docs | `rag/data/*.md` (title guidelines, banned claims, ops notes) |
| Vector DB | `rag/.chroma/` (gitignored; rebuild with `--rebuild`) |
| Embeddings | Chroma default ONNX MiniLM (no paid key) |
| Re-rank | `--rerank` = light lexical-overlap blend (no cross-encoder) |
| LLM answer | Set `OPENAI_API_KEY` (or `LLM_API_KEY`); optional `OPENAI_BASE_URL` / `OPENAI_MODEL` |
| No API key | Still demos index + retrieval + templated stub answer |

Chunking uses `tiktoken` when installed, otherwise ≈4 chars/token. Short docs may yield sub-500-token chunks; they are still indexed.

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
- [x] Lightweight RAG for brand terms / banned words (`rag/` demo)  
- [ ] Structured JSONL traces  

## License

MIT
