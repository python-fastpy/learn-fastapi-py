# Learn Agents — from Scratch, Then for Real

An agent is: **a model that decides** + **tools it can call** + **a loop**
that keeps going until the model says it's done. Every lesson here builds
some piece of that, with nothing hidden behind a framework — until lesson
08, which proves the whole thing works with a real model instead of a
hand-written mock.

## The loop

```
   user message
        │
        ▼
   ┌─────────────────────── THE AGENT LOOP ───────────────────────┐
   │  while True:                                                 │
   │      decision = decide(messages, tools)   <- the ONE line a  │
   │                                               real model call │
   │                                               replaces        │
   │      if decision is FINAL ANSWER:                             │
   │          return it, stop looping                              │
   │      if decision is a TOOL CALL:                               │
   │          result = tools[decision.name](**decision.arguments) │
   │          messages.append(a message holding `result`)          │
   │          # loop again -- informed by the new result            │
   └────────────────────────────────────────────────────────────────┘
```

Lessons 01–07 use a deterministic mock in place of `decide()` — same
loop shape, but free, instant, and reproducible, so every "Expected
output" block in this folder is real captured output, not a guess.
Lesson 08 swaps that mock for a real model and proves nothing else about
the loop had to change.

## Setup

```bash
cd learn-agents
uv sync
```

**Lesson 08 needs real credentials** (same TR Orchestrator as `learn-mcp`
— Azure OpenAI, not a public Anthropic/OpenAI key; a direct `anthropic`
SDK call was tested from this environment and rejected with `403
unapproved_developer_tool`, so this is the path that actually works here):

```bash
# copy .env.example to .env and fill in the values (same credentials as
# ../learn-mcp/.env, fetched via AWS Secrets Manager), then:
uv run python llm_client.py        # connection test only
uv run python 08_real_llm_agent_loop.py
```

Lessons 01–07 need no `.env` at all.

## Lessons

| # | File | Covers |
|---|------|--------|
| 01 | [01_agent_loop_from_scratch.py](01_agent_loop_from_scratch.py) | The agent loop itself: decide → act → observe → repeat, with a mock `decide()` standing in for a real model call |
| 02 | [02_tools_and_function_calling.py](02_tools_and_function_calling.py) | A tool is a SCHEMA (name/description/parameters) to the model, not a function — building that schema from a real function's signature + docstring, and validating arguments before calling anything |
| 03 | [03_subagents_as_tools.py](03_subagents_as_tools.py) | **Subagents**: a complete agent (own loop, own tools) exposed to a parent as ONE callable — "agent-as-tool" |
| 04 | [04_delegation_vs_handoff.py](04_delegation_vs_handoff.py) | Delegation (nested call stack, growing with each `await`) vs. control handoff (a flat runner loop, `Handoff(next_agent)`) — the stack difference made observable with `inspect.stack()`, not just asserted |
| 05 | [05_memory.py](05_memory.py) | Short-term memory (one run's `messages` list, thrown away after) vs. long-term memory (survives across separate runs) — proven across two genuinely separate calls |
| 06 | [06_planning_strategies.py](06_planning_strategies.py) | ReAct (decide one step at a time, adapt as you go) vs. Plan-and-Execute (fix the step sequence up front) — a concrete case where ReAct skips a step Plan-and-Execute can't |
| 07 | [07_context_window_management.py](07_context_window_management.py) | A long-running agent's history outgrows the budget — truncation (cheap, facts are GONE) vs. summarization (facts survive compressed) |
| 08 | [08_real_llm_agent_loop.py](08_real_llm_agent_loop.py) | Lesson 01's exact scenario, for real — raw HTTP tool-calling (`llm_client.py`), a genuine model deciding to call `greet` then `translate` then answer |

## How to check it's working

- **Lesson 01**: three loop iterations for one request -- two tool calls, then a final answer -- all from one `while True:` loop with no recursion.
- **Lesson 02**: the invalid call must be rejected by `validate_arguments` BEFORE `translate()` ever runs -- the error message says so explicitly.
- **Lesson 03**: the indented `[translator subagent]` lines are a separate internal loop; the `[supervisor]` lines treat calling it exactly like calling the plain `greet` function.
- **Lesson 04**: `agent_b`'s printed depth must equal `agent_a`'s exactly (both `1`) — proof the runner called it fresh, not nested inside `agent_a`. Contrast with part 1, where `specialist_b`'s depth is `2`, one more than `specialist_a`'s `1`.
- **Lesson 05**: run 2 and run 3 each start with a fresh, empty `messages = []` — the only reason run 2 can greet Ada in French is `LONG_TERM_MEMORY`, defined outside `run()`.
- **Lesson 06**: for Bob, ReAct's output never mentions a translate call; Plan-and-Execute's does (step 3 still runs, pointlessly) — same final text, different number of tool calls.
- **Lesson 07**: `fake_token_count` must drop after both truncation and summarization, and summarization's message list must be exactly one longer than truncation's (the summary note).
- **Lesson 08**: re-run it a few times — the model's exact phrasing will differ, but it should always call `greet` before `translate`, and always finish with a plain-text final answer containing "Bonjour, Ada" somewhere.

## Beyond this folder: the rest of "AI engineer"

Agents are one topic among many. Here's where the other big ones already
live in this workspace, and what's still a genuine gap:

**Already covered elsewhere**
- Building tools themselves (MCP) → [`learn-fastmcp-server`](../learn-fastmcp-server/), [`learn-fastmcp-client`](../learn-fastmcp-client/)
- Multi-agent orchestration, workflows, human-in-the-loop, LangGraph → [`learn-mcp`](../learn-mcp/) (lessons 06, 10, 12, 13, 16)
- Observability/tracing for LLM calls (the `gen_ai.*` conventions) → [`learn-opentelemetry`](../learn-opentelemetry/) (lesson 07), and could be wired directly onto this folder's lesson 01/08 loops
- Cost control via a fast-path before falling back to a model → `learn-mcp/12_workflow_orchestration.py`

**Real gaps — not covered anywhere in this workspace yet**
- **Guardrails** — input/output validation, scoping what an agent may touch, beyond the tool-gating `learn-mcp/10` already shows
- **Evaluation** — systematically measuring whether an agent did a good job, not just whether it ran
- **RAG / embeddings / vector databases** — grounding an agent in your own documents
- **Fine-tuning** — training vs. prompting a model for a specific task
- **Prompt engineering as its own discipline** — beyond "write a reasonable system prompt"
- **Deployment/serving** — running an agent as a production service (latency, concurrency, cost at scale)

Agents, subagents, and the surrounding loop mechanics are the part you
explicitly asked for, and they're the part this folder covers deeply. Say
the word if you want any of the gaps above as their own project next —
guardrails and evaluation are the most natural follow-ons to this folder
specifically, since they slot directly onto the loop lessons 01-08 already
built.
