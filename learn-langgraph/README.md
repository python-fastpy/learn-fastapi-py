# Learn LangGraph — Step by Step

15 runnable lessons building from zero to production patterns. Wired to the same TR LLM Orchestrator used by the Reuters AI Assistant skills.

Each lesson is one file with a flow diagram in its docstring, a numbered concept list, and exercises at the bottom. Every one has been run; the greeting example carries through all 15 so only the concept changes between them.

## Setup

```bash
cd learn-langgraph

# Install dependencies
uv sync

# Copy env template and fill in orchestrator credentials
cp .env.example .env
# (or run the fetch-secrets skill to populate from AWS Secrets Manager)

# Run any lesson
uv run python 01_state_basics.py
```

Lessons 01–04 and 11–12 need no credentials. 05–10 and 14 need `.env`.
Lesson 15 needs none, and serves on :8012; lesson 14 can serve on :8011.

## Lessons

### Phase 1: Core Concepts (no LLM needed)

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 01 | `01_state_basics.py` | The three parts: state that flows, nodes that change it, edges that pick what runs next | `StateGraph`, `TypedDict` state, partial returns that MERGE, `compile()` | every StateGraph in the orchestrator |
| 02 | `02_edges_and_flow.py` | Chain nodes into a pipeline, and watch the state grow one key per node | `add_edge(A, B)`; why partial returns make nodes reorderable | analyze → route → execute → synthesize |
| 03 | `03_conditional_edges.py` | Branch at runtime: 3 styles in, review-or-send out — two routing stages | `add_conditional_edges` with an explicit path map AND an implicit one; `Literal` route targets | `route_after_analysis()`, fast_path_matcher.py |
| 04 | `04_state_reducers.py` | Why the same three nodes lose data without a reducer — shown side by side, 3 entries vs 1 | `Annotated[list, operator.add]`; per-key choice; the `add_messages` preview | `OrchestratorState.errors` |

### Phase 2: LLM Integration (requires .env)

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 05 | `05_chat_models.py` | The first graph with a model in it, and why a long chat costs more per turn | `MessagesState`, System/Human/AI messages, the model sees the WHOLE history | the chatbot node, chat.py |
| 06 | `06_tool_calling.py` | Tools turn the graph into a loop: ask → run → decide again | `@tool` (the docstring is prompt), `bind_tools`, `ToolNode`, the cycle edge | the orchestrator's tool loop |
| 07 | `07_agent_loop.py` | The same loop prebuilt in one call — and when to go back to building it yourself | `create_react_agent`; ReAct; why you cannot insert a node into a graph you did not build | create_agent_orchestrator.py |
| 08 | `08_checkpointers.py` | One line turns a forgetful graph into a stateful one | `compile(checkpointer=...)`, `thread_id` as the session key, same-vs-different thread | dynamodb_checkpointer.py |

### Phase 3: Production Patterns (requires .env, except 11–12)

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 09 | `09_human_in_the_loop.py` | Pause mid-node for a human, then resume — and the re-entry that catches people out | `interrupt()`, `Command(resume=)`; the node RE-RUNS from its first line, so it counts its own entries (4 for 2 pauses) | the skills interrupt system |
| 10 | `10_streaming.py` | Three ways to watch one run: progress, snapshots, tokens | `stream_mode="updates" / "values" / "messages"` | chat.py, progress_websocket.py |
| 11 | `11_subgraphs.py` | A graph as a node — and the border leak that silently doubles a list | compiled graph in `add_node`; a subgraph that DECLARES a key it doesn't own gets it appended twice | skill composition |
| 12 | `12_error_handling.py` | Two kinds of failure, two different fixes | `RetryPolicy` for transient; catch + conditional edge for permanent; retry re-runs the whole node | MCP retry, orchestrator fallbacks |
| 13 | `13_orchestrator.py` | The capstone: analyze → route → execute → synthesize, with only `analyze` deciding | execution strategies incl. `none`; registry lookup; errors accumulate instead of raising | langgraph_mcp_orchestrator.py (end to end) |

### Phase 4: Over the Wire

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 14 | `14_mcp_plus_langgraph.py` | Where production tools actually live: separate MCP services, discovered at runtime | `list_tools()` → `StructuredTool`; pass the MCP `input_schema` or the model calls with no args; late-binding in the wrapper | langgraph_mcp_orchestrator.py, mcp_server_registry.py |
| 15 | `15_streaming_sse.py` | Getting lesson 10's chunks out to a browser | `astream_events()`, `StreamingResponse`, the `data: …\n\n` format, `X-Accel-Buffering` | chat.py's SSE endpoint |

## How it connects to your work

| Lesson | Maps to in the codebase |
|--------|------------------------|
| 05-07 | `reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py` |
| 08 | `reuters-assistant_backend/src/services/dynamodb_checkpointer.py` |
| 09 | Skills interrupt system (`sphinx_leon-assistant-skills/*/src/interrupts/`) |
| 10 | Backend SSE streaming (`reuters-assistant_backend/src/routers/v1/chat.py`) |
| 11 | Skill composition via MCP (each skill = subgraph) |
| 12 | Backend retry/fallback logic |
| 13 | `reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py` (end-to-end) |
| 14 | `mcp_server_registry.py` + `mcp_protocol.py` — tools as separate services |
| 15 | `reuters-assistant_backend/src/routers/v1/chat.py` — the SSE endpoint itself |

## Agent vs MCP, Agent-Creates-Agent, Handoff

See [`../learn-mcp/16_agent_vs_mcp_and_handoff.py`](../learn-mcp/16_agent_vs_mcp_and_handoff.py) — draws the line between "agent" (the decision loop, e.g. lesson 07's `create_react_agent`) and "MCP" (the protocol layer, no judgment of its own), then shows a supervisor creating specialist agents on demand and two ways to hand a job to one: delegation (call and wait) vs. control handoff (step aside), which is what LangGraph's `Command(goto=..., update=...)` in lesson 13 actually does under the hood.

## Flow-to-Learning Map

See [flow_to_learning_map.txt](../../reuters-ai_assistant/reuters-assistant_backend/flow_to_learning_map.txt) — maps every step of the production orchestrator flow to specific learning files across all directories (LangGraph, MCP, CopilotKit, FastAPI, AWS). Shows exactly which lessons cover each part of the request lifecycle.

## LLM Helper

`llm_helper.py` mirrors the skills repo's `shared/llm/orchestrator.py` setup:
- Same Azure AD client-credentials auth
- Same TR Orchestrator endpoint + deployment paths
- Same custom headers (`x-tr-chat-profile-name`, etc.)
- Returns a LangChain `AzureChatOpenAI` for direct use in LangGraph

Available models: `gpt-4o` (default), `gpt-4-1`, `o4-mini`
