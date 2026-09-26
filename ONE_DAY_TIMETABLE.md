# One-Day MCP + LangGraph Mastery Timetable

**Pre-requisite:** Copy `.env.example` to `.env` in both `learn-mcp/` and `learn-langgraph/` and fill in your TR LLM Orchestrator credentials (from AWS Secrets Manager secret `a207920-leon-skills`).

---

## Morning: MCP with FastMCP (9:00 - 13:00)

| Time | Lesson | File | What You Learn | Reuters Prod Equivalent |
|------|--------|------|----------------|------------------------|
| 9:00 - 9:40 | 1. Hello MCP Server | `learn-mcp/01_hello_mcp_server.py` | Create a minimal MCP server with `@mcp.tool()`, run it, test with `fastmcp dev` | Every skill's `main.py` (e.g. `story-drafting/src/main.py`) |
| 9:40 - 10:20 | 2. MCP Client | `learn-mcp/02_mcp_client.py` | Connect to your server programmatically using `fastmcp.Client`, call tools, inspect results | Backend's `mcp_protocol.py` — how the orchestrator calls skills |
| 10:20 - 11:00 | 3. Tools, Resources, Prompts | `learn-mcp/04_resources_and_prompts.py` | All three MCP primitives: `@mcp.tool`, `@mcp.resource`, `@mcp.prompt` | Skills expose tools; workflows loaded as resources |
| 11:00 - 11:40 | 4. Structured Content | `learn-mcp/05_structured_content.py` | Return `structuredContent` + `_meta` with timing data from tools | How skills return interrupt payloads + `skill_call_extras` |
| 11:40 - 12:20 | 5. Human-in-the-Loop | `learn-mcp/06_hitl_interrupt.py` | Implement interrupt/resume with continuation tokens and `_meta` injection | The full HITL cycle: skill interrupts -> backend checkpoints -> user responds -> resume |
| 12:20 - 13:00 | 6. HTTP Transport | `learn-mcp/07_http_transport.py` | Run MCP over Streamable HTTP (production transport), test with `httpx` | Production: ECS Fargate behind ALB, path-based routing |

**Lunch break: 13:00 - 13:30**

---

## Afternoon: LangGraph (13:30 - 17:30)

| Time | Lesson | File | What You Learn | Reuters Prod Equivalent |
|------|--------|------|----------------|------------------------|
| 13:30 - 14:10 | 7. State Basics | `learn-langgraph/01_state_basics.py` | `StateGraph`, typed state with `TypedDict`, nodes, edges, compile & invoke | Backend's `langgraph_mcp_orchestrator.py` — the state definition |
| 14:10 - 14:50 | 8. Conditional Routing | `learn-langgraph/02_conditional_routing.py` | `add_conditional_edges`, router functions, branching logic | Backend's execution strategies: none/single/sequential/parallel |
| 14:50 - 15:30 | 9. Tool-Calling Agent | `learn-langgraph/03_tool_calling_agent.py` | Bind tools to LLM, `ToolNode`, agent loop with tool calls | The core agent loop that decides which MCP tool to call |
| 15:30 - 16:10 | 10. Human-in-the-Loop | `learn-langgraph/04_human_in_the_loop.py` | `interrupt()`, `MemorySaver` checkpointer, resume from checkpoint | Backend's DynamoDB checkpointer + interrupt/resume cycle |
| 16:10 - 16:50 | 11. MCP + LangGraph | `learn-langgraph/05_mcp_plus_langgraph.py` | LangGraph agent that discovers and calls MCP tools dynamically | The exact production pattern: LangGraph orchestrator -> MCP skill servers |
| 16:50 - 17:30 | 12. Streaming SSE | `learn-langgraph/06_streaming_sse.py` | Stream graph execution events via FastAPI SSE endpoint | Backend's `/api/v1/chat` SSE streaming response |

---

## How to Run Each Lesson

```bash
# MCP lessons (from learn-mcp/)
cd learn-fastapi-py/learn-mcp
uv run python 01_hello_mcp_server.py    # starts MCP server
uv run python 02_mcp_client.py          # calls the server
# ... etc

# LangGraph lessons (from learn-langgraph/)
cd learn-fastapi-py/learn-langgraph
uv run python 01_state_basics.py
# ... etc
```

## Key Concepts Map: Learning -> Production

```
Your Exercise                    Reuters Production Code
-----------                      ----------------------
FastMCP server with @mcp.tool    sphinx_leon-assistant-skills/story-drafting/src/main.py
fastmcp.Client + call_tool       reuters-assistant_backend/src/services/mcp_protocol.py
structuredContent interrupt       Skill interrupt payloads (NEWS_BUZZ.REVIEW etc.)
StreamableHttpTransport           ECS Fargate + ALB path routing (/story-drafting)
StateGraph + TypedDict            langgraph_mcp_orchestrator.py state definition
conditional_edges                 Execution strategy routing (none/single/parallel)
ToolNode + agent loop             Core orchestrator agent loop
interrupt() + checkpointer        DynamoDB checkpointer + interrupt/resume
LangGraph + MCP client            The full orchestrator -> skill call chain
SSE streaming                     /api/v1/chat SSE endpoint
```
