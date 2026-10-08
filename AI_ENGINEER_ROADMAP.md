# AI Engineer Roadmap — What's Covered, What's Missing

One page, the whole repo. For *why* a stage matters and worked examples
with real numbers, see [`learn-llm-fundamentals/README.md` §8](learn-llm-fundamentals/README.md#8-the-ai-engineer-roadmap) —
this file is that table, kept at the root so it's the first thing you
find, cross-referenced against every folder as it stood after
`learn-agents` was added. For the *missing* half in full detail
(sub-checklists, priority order, "done when" criteria), see
[`AI_ENGINEER_LEARNING_BACKLOG.md`](AI_ENGINEER_LEARNING_BACKLOG.md).

## Covered

```
 STAGE 0  Foundations        Python, async, HTTP APIs, JSON, git, SQL, Docker
 STAGE 1  How LLMs work      tokens, sampling, context window, API anatomy, cost
 STAGE 2  Prompt + context   prompt engineering, structured output, context engineering
 STAGE 3  Knowledge (RAG)    embeddings, chunking, vector search, grounding
 STAGE 4  Tools + agents     tool calling, agent loop, subagents, MCP, orchestration, HITL
 STAGE 5  Quality            evals, LLM-as-judge, guardrails, injection defence
 STAGE 6  Production         observability, latency, caching, routing, retries, cost
 STAGE 7  Ship it            APIs, streaming UIs, deployment, CI/CD
```

| Stage | Skill | Folder | Status |
|---|---|---|---|
| 0 | Python, types, async, Pydantic | `python/` | ✅ |
| 0 | HTTP APIs with FastAPI | `fastapi/` | ✅ |
| 0 | Git | `github/` | ✅ |
| 1 | Tokens, sampling, API anatomy, cost | `learn-llm-fundamentals/01-03` | ✅ |
| 1 | Tool calling + tool-type catalogue | `learn-llm-fundamentals/07-08` | ✅ |
| 2 | Context engineering, prompt engineering | `learn-llm-fundamentals/04-05` | ✅ |
| 2 | Structured output + validation | `learn-llm-fundamentals/03`, `learn-ai-advanced/04` | ✅ |
| 3 | Embeddings, chunking, vector store, grounding | `learn-ai-advanced/01` | ✅ |
| 4 | Agent loop, built-in tools, sandbox, permissions | `learn-mini-claude/01-05` | ✅ |
| 4 | LLM vs. agent vs. subagent | `learn-mini-claude/06`, `learn-agents/01-03` | ✅ |
| 4 | Subagents (agent-as-tool), measured | `learn-mini-claude/11`, `learn-agents/03` | ✅ |
| 4 | **Delegation vs. control handoff, stack depth measured** | **`learn-agents/04`** | ✅ |
| 4 | **ReAct vs. Plan-and-Execute, named and contrasted** | **`learn-agents/06`** | ✅ |
| 4 | **Short/long-term memory, context window truncation vs. summarization** | **`learn-agents/05, 07`** | ✅ |
| 4 | Real LLM tool-calling loop, raw HTTP, no SDK | `learn-agents/08` | ✅ |
| 4 | Hooks, parallel tool calls, todo planning | `learn-mini-claude/07-10` | ✅ |
| 4 | MCP servers, clients, multi-server routing | `learn-fastmcp-server/`, `learn-fastmcp-client/`, `learn-mcp/01-16` | ✅ |
| 4 | Graph orchestration, checkpoints, HITL, subgraphs, streaming | `learn-langgraph/01-15` | ✅ |
| 4 | Agent-facing UIs, generative UI | `learn-copilotkit/` | ✅ |
| 5 | Evals, golden datasets, LLM-as-judge | `learn-ai-advanced/02` | ✅ |
| 5 | Guardrails, PII redaction, prompt injection | `learn-ai-advanced/04` | ✅ |
| 6 | Tracing, token/cost tracking, `gen_ai.*` OTEL conventions | `learn-ai-advanced/03`, `learn-opentelemetry/` | ✅ |
| 6 | Latency, routing, caching, batch, fine-tune decision | `learn-llm-fundamentals/06` | ✅ |
| 6 | Retries, error handling, streaming | `learn-langgraph/10,12`, `learn-mcp/06` | ✅ |
| 7 | Deploy to AWS, system design for scale | `project-book-store/`, `aws/`, `system-design/` | ✅ |

**Row in bold** = added by `learn-agents`, the newest folder. Everything
else predates it — `learn-agents` fills specific named gaps (agent design
*patterns*, call-stack mechanics of delegation vs. handoff) rather than
re-teaching stage 4 from zero; see `learn-agents/README.md`'s own
"Beyond this folder" section for exactly how it relates to
`learn-mini-claude`, which covers the same stage in more operational depth
(real file tools, a sandbox, hooks) but without naming ReAct/Plan-and-Execute
or measuring the delegation-vs-handoff stack difference.

## Missing

Tracked with sub-checklists and priority in
[`AI_ENGINEER_LEARNING_BACKLOG.md`](AI_ENGINEER_LEARNING_BACKLOG.md). Summary:

| Priority | Topic | Status |
|---|---|---|
| High | Advanced RAG and retrieval evals (hybrid search, rerankers, recall@k) | ⬜ Not started |
| High | Agent design patterns and agent evals | 🟨 In progress — `learn-agents` covers the patterns; trajectory/task-success evals, reflection, router, and "when not to use an agent" are still open |
| High | LLMOps: prompt versioning, A/B testing, drift detection, CI for LLM apps | ⬜ Not started |
| High | Real-API lab (see fundamentals-lesson effects on a real model) | ⬜ Not started |
| Medium | Multimodal (images, PDFs) | ⬜ Not started |
| Medium | Fine-tuning hands-on (LoRA, distillation) | ⬜ Not started |
| Medium | Local / open-weight models (Ollama, vLLM) | ⬜ Not started |
| Medium | Transformer internals and the maths behind them | ⬜ Not started |
| Optional | Voice/realtime agents, computer-use/browser agents, red-teaming, responsible AI | ⬜ Not started |

## How to use this file

1. Pick a ⬜/🟨 row above (or a sub-checklist item in the backlog).
2. Say which one — the next lesson folder gets built the same way every
   one so far was: verified by actually running it, not written from
   assumption.
