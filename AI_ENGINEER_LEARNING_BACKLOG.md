# AI Engineer Learning Backlog

Topics **not yet covered** in this repo, in the order to learn them.
Tick the boxes as you go. When a topic gets its own lesson folder, link
it here and move the row in the progress table to ✅.

What's already covered (fundamentals, sampling, context and prompt
engineering, basic RAG, evals, tracing, guardrails, agents, MCP,
LangGraph, deployment) is mapped in the roadmap:
[`learn-llm-fundamentals/README.md` §8](learn-llm-fundamentals/README.md#8-the-ai-engineer-roadmap).

---

## Progress

| # | Topic | Priority | Status | Lesson folder |
|---|---|---|---|---|
| 1 | Advanced RAG and retrieval evals | High | ⬜ Not started | — |
| 2 | Agent design patterns and agent evals | High | ⬜ Not started | — |
| 3 | LLMOps: the loop after launch | High | ⬜ Not started | — |
| 4 | Real-API lab (see the concepts on a real model) | High | ⬜ Not started | — |
| 5 | Multimodal (images, PDFs) | Medium | ⬜ Not started | — |
| 6 | Fine-tuning hands-on | Medium | ⬜ Not started | — |
| 7 | Local / open-weight models | Medium | ⬜ Not started | — |
| 8 | Transformer internals and the maths behind them | Medium | ⬜ Not started | — |
| 9 | Voice and realtime agents | Optional | ⬜ Not started | — |
| 10 | Computer-use and browser agents | Optional | ⬜ Not started | — |
| 11 | Red-teaming and jailbreak testing | Optional | ⬜ Not started | — |
| 12 | Responsible AI and compliance | Optional | ⬜ Not started | — |

Status key: ⬜ not started · 🟨 in progress · ✅ done

---

## High priority: learn these next

### 1. Advanced RAG and retrieval evals

**Why:** weak retrieval is the most common reason production RAG
fails. If the right chunk never reaches the context, no prompt can fix
the answer. Builds on `learn-ai-advanced/01` (which uses mock
embeddings and plain vector search).

- [ ] Real embedding models: dimensions, cost, choosing one, embedding drift when you switch models
- [ ] Chunking strategies: fixed vs recursive vs semantic; PDFs, tables, code; chunk size vs recall
- [ ] Metadata and filtering (date, source, permissions): only retrieve what this user may see
- [ ] Hybrid search: BM25 keyword + vector, combined with reciprocal rank fusion
- [ ] Rerankers (cross-encoders): retrieve 50, rerank, keep 5
- [ ] Query rewriting, multi-query and HyDE (hypothetical document embeddings)
- [ ] Agentic RAG: the agent decides when and what to search
- [ ] Vector databases in production: pgvector, OpenSearch, or a managed service; indexing (HNSW), updates, deletes
- [ ] **Retrieval evals:** recall@k, precision@k, MRR, measured separately from answer quality
- [ ] **Answer evals:** faithfulness (grounded in the retrieved text?), answer relevance, citation accuracy

**Done when:** you can take a docs Q&A system, measure recall@5, change
one thing (chunking, hybrid, reranker), and show the number moved.

---

### 2. Agent design patterns and agent evals

**Why:** the repo teaches the agent *loop* (`learn-mini-claude`,
`learn-langgraph`) but not the named patterns interviewers and teams
use, or how to test an agent beyond its final answer.

- [ ] ReAct (reason → act → observe loop), the pattern behind most agents
- [ ] Plan-and-execute: write a plan first, then execute the steps
- [ ] Reflection / self-critique: generate → critique → revise
- [ ] Router: classify the request, send it to a specialised prompt/agent
- [ ] Multi-agent: supervisor/worker, handoffs, debate (partly in `learn-mcp/16`)
- [ ] When NOT to use an agent: a fixed workflow is cheaper and more reliable
- [ ] Agent memory design: short-term (messages) vs long-term (stored facts), what to save, when to forget
- [ ] Stopping conditions, budgets, and loop detection
- [ ] **Trajectory evals:** did it call the right tools, in a sensible order, without wasted steps?
- [ ] **Task-success evals:** end-state checks (file exists, test passes, ticket updated)

**Done when:** you can build the same task as a workflow and as an
agent, then compare success rate, cost and steps on an eval set.

---

### 3. LLMOps: the loop after launch

**Why:** shipping is the start. Quality drifts as users, data and
models change. Builds on `learn-ai-advanced/02` (offline evals) and
`/03` (tracing).

- [ ] Prompt versioning / prompt registry: every answer traceable to a prompt version
- [ ] A/B testing prompts and models on live traffic
- [ ] User feedback capture (thumbs, edits, escalations) linked to the trace
- [ ] Online evals: LLM-as-judge on a sample of production traffic
- [ ] Dashboards: cost per request, latency p50/p95, error rate, eval score over time
- [ ] Drift detection: input topics changing, scores falling, a provider model update
- [ ] The data flywheel: production failures → new eval cases → fix → re-run
- [ ] Safe rollout: canary a new prompt/model, automatic rollback on metric drop
- [ ] CI for LLM apps: eval suite as a pipeline gate, with mocked LLMs for unit tests

**Done when:** a bad prompt change would be caught by CI *or* by a
dashboard alert before users complain.

---

### 4. Real-API lab

**Why:** every lesson in `learn-llm-fundamentals` uses a simulation so
it runs anywhere. Seeing the same effects on a real model makes them
stick. Uses `llm_helper.py` and the `.env` credentials.

- [ ] Same prompt at temperature 0 vs 0.7 vs 1.2, 5 runs each: compare the variation
- [ ] Is temperature 0 really deterministic? Run it 10 times and diff the outputs
- [ ] Real token counts from `usage` vs the ~4-chars-per-token estimate
- [ ] A real `max_tokens` cut-off on JSON output, with `finish_reason` = `length`
- [ ] Structured output with a real schema, validated with Pydantic
- [ ] Real tool call: define a tool, see the raw `tool_calls`, send a result back
- [ ] Prompt caching: send the same long prefix twice and compare cached-token counts
- [ ] Streaming: measure time-to-first-token vs total time
- [ ] Reasoning model (`o4-mini`) vs chat model (`gpt-4-1`) on the same task: cost, latency, quality

**Done when:** each lesson 01–06 concept has a matching real-model
experiment with its output recorded.

---

## Medium priority

### 5. Multimodal

- [ ] Image input: describing, extracting data from screenshots, charts and forms
- [ ] PDF/document input: native document support vs OCR + text
- [ ] Token cost of images; resizing to control it
- [ ] Vision in RAG: indexing diagrams and scanned pages
- [ ] Image generation APIs (awareness level)

### 6. Fine-tuning hands-on

- [ ] When it's worth it (lesson 06 §6 decision tree) and when RAG or prompting is better
- [ ] Building a training dataset: format, size, quality, train/validation split
- [ ] Provider fine-tuning APIs (hosted) vs open-model fine-tuning
- [ ] LoRA / QLoRA with Hugging Face `peft` on a small open model
- [ ] Distillation: fine-tune a small model on a big model's outputs
- [ ] Evaluate before vs after on the SAME eval set; watch for regressions on general tasks

### 7. Local / open-weight models

- [ ] Running models locally with Ollama; serving with vLLM
- [ ] Quantization (4-bit / 8-bit): memory vs quality trade-off
- [ ] OpenAI-compatible local endpoints, so the same client code works
- [ ] Comparing a local model to a hosted one on your eval set
- [ ] When local makes sense: privacy, offline, cost at high volume

### 8. Transformer internals and the maths behind them

- [ ] Vectors, dot product, cosine similarity (the maths of embeddings)
- [ ] Probability basics: softmax, log-probs, cross-entropy loss
- [ ] Embeddings and positional encoding
- [ ] Self-attention: queries, keys, values; why context length is expensive
- [ ] Transformer block: attention + feed-forward + residuals + layer norm
- [ ] KV cache: why output tokens are generated one at a time and how that's sped up
- [ ] Build a tiny GPT from scratch (Andrej Karpathy's *Let's build GPT* video)
- [ ] Visual intuition: 3Blue1Brown's neural-network and transformer videos

---

## Optional: depending on the role you're aiming for

### 9. Voice and realtime agents
- [ ] Speech-to-text → LLM → text-to-speech pipeline
- [ ] Realtime/speech-native model APIs
- [ ] Latency budgets for conversation (< ~1s to feel natural), interruption handling

### 10. Computer-use and browser agents
- [ ] Screenshot → action loops; browser automation (Playwright) as agent tools
- [ ] Sandboxing and permission design for agents that click and type

### 11. Red-teaming and jailbreak testing
- [ ] Building an adversarial test set (jailbreaks, injections, data exfiltration)
- [ ] Automated red-teaming with an attacker LLM
- [ ] Tracking attack success rate as a metric (beyond `learn-ai-advanced/04`)

### 12. Responsible AI and compliance
- [ ] Data governance: what data can go to which provider, retention, residency
- [ ] Bias and fairness testing basics
- [ ] Regulation awareness (e.g. the EU AI Act risk tiers)
- [ ] Model and dataset licensing (open-weight licences, commercial use)

---

## Portfolio projects

Build these to prove the skills (from the roadmap):

- [ ] **CLI chatbot:** history, token/cost counter, `/temperature` command
- [ ] **Docs Q&A (RAG):** citations, "I don't know" behaviour, 20-question eval set, recall@k measured
- [ ] **Tool-using agent:** 3 real internal APIs over MCP, permission gate, tracing, trajectory evals
- [ ] **Shipped product:** FastAPI backend, streaming UI, deployed on AWS, dashboards for cost, latency and eval score
