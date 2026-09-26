# Learn AI Advanced — RAG, Evals, Observability, Guardrails

A 4-lesson series covering the AI-app skills that don't fit naturally
into `learn-langgraph` (agent orchestration) or `learn-mcp` (tool
protocol): retrieving your own unstructured data, testing answer
*quality* instead of just code paths, seeing what a request actually
cost and where it spent its time, and defending an agent against
untrusted content it reads.

## How to Use This Guide

**Start at Lesson 01 and go in order** — 02-04 don't depend on 01's
code, but the series is ordered by where each concern shows up in a
request's lifecycle: retrieve (01) → test the answer (02) → observe the
request (03) → defend it (04).

**Read the docstring first.** Every file starts with a block explaining
*what* you'll learn, *why* it matters, and an ASCII diagram of the flow.

**Run it, then read it.**

## Prerequisites

```bash
cd learn-ai-advanced
uv sync
```

**You should already know:** the agent/MCP shape from `learn-mcp` lesson
16 (agent-vs-MCP, agent-as-tool) — several examples here reuse that
vocabulary. You don't need `learn-langgraph` or a real LLM: all four
lessons run fully deterministic by default.

For a live LLM call in lessons 01, 02, and 04 (optional — each lesson
has a deterministic mock path that runs without it): copy `.env.example`
to `.env` and fill in TR Orchestrator credentials (or run the
`fetch-secrets` skill).

## Lesson Index

| # | File | What You Learn | Key Concept | Runs without .env? |
|---|------|----------------|-------------|---------------------|
| 01 | `01_rag_embeddings_and_retrieval.py` | Chunking, embeddings, cosine similarity, a minimal vector store, grounding | `chunk_text()`, `embed()`, `VectorStore.search()`, grounded prompt | Yes (hash-based mock embedding) |
| 02 | `02_evals_and_llm_judge.py` | Golden datasets, keyword/fact coverage, LLM-as-judge, regression diffing | `EvalCase`, `score_keyword_coverage()`, `llm_judge()`, `diff_reports()` | Yes (mock judge normalizes numbers) |
| 03 | `03_observability_and_tracing.py` | Spans, trace trees, latency waterfalls, token/cost tracking, critical path | `Tracer.span()`, `render_waterfall()`, `critical_path()` | Yes (fully deterministic) |
| 04 | `04_guardrails_and_prompt_injection.py` | Output validation + retry, PII redaction, direct vs. indirect prompt injection, data/instruction separation | `validate_with_retry()`, `redact_pii()`, `scan_for_injection()`, `wrap_as_inert_content()` | Yes (fully deterministic) |

## Running

```bash
# All 4 lessons run with zero setup:
uv run python 01_rag_embeddings_and_retrieval.py
uv run python 02_evals_and_llm_judge.py
uv run python 03_observability_and_tracing.py
uv run python 04_guardrails_and_prompt_injection.py

# With .env, lessons 01/02/04 additionally show a real LLM call for comparison.
```

## Glossary

| Term | What It Means | Lesson |
|------|---------------|--------|
| **Chunking** | Splitting a document into overlapping windows small enough to embed and retrieve precisely | 01 |
| **Embedding** | A fixed-length vector representing a text's meaning — similar meaning ends up close in vector space | 01 |
| **Cosine similarity** | The angle between two vectors — 1.0 = identical direction, 0.0 = unrelated | 01 |
| **Vector store** | A collection of (vector, text) pairs searchable by "k closest to this query vector" | 01 |
| **Grounding** | Instructing the LLM to answer only from retrieved text, not memorized knowledge | 01 |
| **Golden dataset** | A fixed, versioned set of (question, expected answer) test cases | 02 |
| **Keyword/fact coverage** | Cheap, deterministic scoring: does the answer contain the required facts, regardless of phrasing | 02 |
| **LLM-as-judge** | A second LLM call whose only job is grading another LLM's output against an expected answer | 02 |
| **Regression (eval)** | Same dataset, two system versions, a case that passed before now fails | 02 |
| **Span** | A named, timed unit of work with a start, end, optional parent, and attributes | 03 |
| **Trace** | A tree of spans sharing one root — one request end-to-end | 03 |
| **Waterfall** | A rendering of a trace tree where each span's bar is positioned by start time and sized by duration | 03 |
| **Critical path** | The longest chain of sequential spans — the one worth optimizing if the whole request feels slow | 03 |
| **Output validation** | Forcing LLM output through a schema and rejecting/retrying on violation | 04 |
| **PII redaction** | Stripping sensitive patterns (emails, phones, SSNs) before logging or displaying text | 04 |
| **Prompt injection** | Instructions smuggled inside data the LLM reads, trying to override its actual instructions | 04 |
| **Indirect injection** | The dangerous variant — the attacker poisons a document or tool response, never talks to the LLM directly | 04 |
| **Data/instruction separation** | Wrapping untrusted content so the model treats it as data to read, never instructions to follow | 04 |

## How This Connects to the Rest of the Repo

| This Series | Related Lesson |
|--------------|----------------|
| 01 RAG retrieval as an MCP tool | `learn-mcp` lesson 15 (MCP-to-MCP) — wrap `VectorStore.search()` as `@mcp.tool` |
| 02 Evals generalize a production pattern | Quote-fidelity checking (verify LLM draft against source) is a one-question eval at request time |
| 03 Tracing an agent's tool calls | `learn-mcp` lesson 16 (agent-vs-MCP, agent-as-tool) — the call shape this lesson traces |
| 03 vs. checkpointers | `learn-langgraph` lesson 08 saves *state* for resume; tracing records *what happened and when*, a different concern |
| 04 Guardrails on tool/document content | `learn-mcp` lesson 09's `_meta.forwarded_blocks` separates agent-visible from UI-visible content — guardrails apply the same instinct to trust, not visibility |
| 04 Indirect injection surface | Any lesson where an agent reads tool output it didn't generate (`learn-mcp` L06, L11, L15; `learn-langgraph` L07) |
