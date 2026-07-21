# Learn LangGraph — Step by Step

13 runnable lessons building from zero to production patterns. Wired to the same TR LLM Orchestrator used by the Reuters AI Assistant skills.

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

## Lessons

### Phase 1: Core Concepts (no LLM needed)
| # | File | Topic |
|---|------|-------|
| 01 | `01_state_basics.py` | StateGraph, TypedDict, nodes, START/END |
| 02 | `02_edges_and_flow.py` | Sequential pipelines, state merging |
| 03 | `03_conditional_edges.py` | Branching with add_conditional_edges |
| 04 | `04_state_reducers.py` | Annotated reducers, accumulating state |

### Phase 2: LLM Integration (requires .env)
| # | File | Topic |
|---|------|-------|
| 05 | `05_chat_models.py` | MessagesState, ChatOpenAI, message types |
| 06 | `06_tool_calling.py` | @tool, bind_tools, ToolNode |
| 07 | `07_agent_loop.py` | create_react_agent, ReAct pattern |
| 08 | `08_checkpointers.py` | MemorySaver, thread_id, conversation memory |

### Phase 3: Production Patterns (requires .env)
| # | File | Topic |
|---|------|-------|
| 09 | `09_human_in_the_loop.py` | interrupt(), Command(resume=...) |
| 10 | `10_streaming.py` | stream modes: updates, values, messages |
| 11 | `11_subgraphs.py` | Composing graphs, parent/child state |
| 12 | `12_error_handling.py` | RetryPolicy, error routing, fallbacks |
| 13 | `13_orchestrator.py` | What is an orchestrator? Building a mini orchestrator |

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

## LLM Helper

`llm_helper.py` mirrors the skills repo's `shared/llm/orchestrator.py` setup:
- Same Azure AD client-credentials auth
- Same TR Orchestrator endpoint + deployment paths
- Same custom headers (`x-tr-chat-profile-name`, etc.)
- Returns a LangChain `AzureChatOpenAI` for direct use in LangGraph

Available models: `gpt-4o` (default), `gpt-4-1`, `o4-mini`
