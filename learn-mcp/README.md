# Learn MCP (Model Context Protocol)

A 16-lesson progressive series for building MCP servers, clients, workflows, and orchestration — using the same patterns as the Reuters AI Assistant production codebase.

## How to Use This Guide

**Start at Lesson 01 and go in order.** Each lesson builds on the one before it. The code is runnable — every lesson prints output so you can see what's happening.

**Read the docstring first.** Every file starts with a block explaining *what* you'll learn, *why* it matters, and an ASCII diagram showing the data flow.

**Run it, then read it.** Run each lesson, look at the output, *then* read the code. It's easier to understand code when you already know what it produces.

**Try the exercises.** Each lesson ends with 2-4 exercises. They're optional but they're the fastest way to solidify the concepts.

## Prerequisites

```bash
cd learn-mcp
uv sync          # install dependencies from pyproject.toml
```

For lessons 07, 08, 12 (LLM-powered): copy `.env.example` to `.env` and fill in TR Orchestrator credentials.

**You should already know:** Python async/await, basic FastAPI concepts, what an API is.
**You don't need to know:** MCP, LangGraph, or the Reuters codebase (that's what you're learning).

## Concept Map

```
                           ┌──────────────────┐
                           │  Full System (13) │
                           │  LangGraph + MCP  │
                           └────────┬─────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
           ┌────────▼─────────┐  ┌─▼────────────┐  │
           │ Wire Protocol(14)│  │ MCP-to-MCP   │  │
           │ Raw JSON-RPC HTTP│  │ Cross-Skill  │  │
           └────────┬─────────┘  │   (15)       │  │
                    │            └─┬────────────┘  │
                    │              │                │
                    ├──────────────┘                │
                    │                               │
                    ┌───────────────┐               │
                    │               │               │
           ┌───────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
           │ Orchestration │ │  Interrupts │ │ Multi-Server│
           │    (12)       │ │    (10)     │ │    (11)     │
           └───────┬──────┘ └──────┬──────┘ └──────┬──────┘
                   │               │               │
           ┌───────▼──────┐       │        ┌──────▼──────┐
           │  Workflows   │       │        │   Client    │
           │    (09)      ├───────┘        │  Patterns   │
           └───────┬──────┘                │    (06)     │
                   │                       └──────┬──────┘
           ┌───────▼──────┐                       │
           │  Meta/Fwd    │                ┌──────▼──────┐
           │  Blocks (08) │                │    HTTP     │
           └───────┬──────┘                │ Transport   │
                   │                       │    (05)     │
           ┌───────▼──────┐                └──────┬──────┘
           │  LLM Inside  │                       │
           │  Tools (07)  │                       │
           └───────┬──────┘                       │
                   │               ┌──────────────┘
                   │               │
           ┌───────▼───────────────▼──────┐
           │  Server Fundamentals (01-04) │
           │  Tools, Validation, Logging, │
           │  Resources & Prompts         │
           └──────────────────────────────┘
```

Lessons on the left side build the **skill (server)** side.
Lessons on the right side build the **orchestrator (client)** side.
Lesson 13 at the top combines both into the **full production architecture**.

## Lesson Index

### Phase 1: Server Fundamentals (No LLM needed)

*Build your first MCP server and learn the core primitives.*

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 01 | `01_hello_mcp_server.py` | Register tools two ways, then validate their input: reject bad input vs clamp edge values | `@mcp.tool` and `mcp.tool()(fn)`; `ToolError` vs silent clamping | story-drafting/main.py, archive_search.py, search_rics.py |
| 02 | `02_mcp_client.py` | Connect to a server as a client, and see the handshake messages | `Client` over stdio, `list_tools()` / `call_tool()`, JSON-RPC `initialize` | mcp_protocol.py |
| 03 | `03_logging.py` | Debug tools without print statements | `get_logger()` and log levels | story-drafting/main.py |
| 04 | `04_resources_and_prompts.py` | Expose data and templates, not just actions | Resources + Prompts (the other 2 MCP primitives) | workflows/routes.py |
| 04b | `04_structured_content.py` | One tool result, three parts: text for the LLM, JSON for your code, metadata for logs | `content` vs `structuredContent` vs `_meta`; `status: interrupted` + `continuation_token` | mcp_protocol.py `_call_tool_result_to_dict()` |

### Phase 2: Client & Transport (No LLM needed)

*Connect to MCP servers over HTTP and handle real-world failures.*

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 05 | `05_http_transport.py` | Run an MCP server as a real HTTP service | `mcp.run(transport="http")` + `StreamableHttpTransport` | story-drafting run block |
| 06 | `06_client_patterns.py` | Handle timeouts, retries, and server failures | Exponential backoff, one-shot clients | mcp_protocol.py |

### Phase 3: LLM + Advanced (Lessons 07-08 require `.env`)

*Make tools smart by calling LLMs, and learn how to send rich data to the UI.*

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 07 | `07_llm_tool_server.py` | Use an LLM *inside* a tool (LLM is implementation detail) | `llm_helper.get_llm()` inside `@mcp.tool` | generate_spot_story.py |
| 08 | `08_tool_result_meta.py` | Send data to the UI without the LLM agent seeing it | `_meta.forwarded_blocks` (agent-visible vs UI-visible) | shared/forwarded.py |
| 09 | `09_workflows.py` | Define multi-step processes as markdown files | YAML frontmatter, `mount_workflows()`, tool gating | shared/workflows/ |

### Phase 4: Production Patterns (No LLM for 10-11)

*Build the same patterns used in the production Reuters AI Assistant.*

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 10 | `10_interrupts.py` | Pause execution and ask the user for input | `SkillInterrupt`, `InterruptPayload`, `.block()` | shared/interrupts/ |
| 11 | `11_multi_server.py` | Route tool calls across multiple servers | `ServerRegistry`, tool routing table | mcp_server_registry.py |
| 12 | `12_workflow_orchestration.py` | Full loop: user intent to tool execution | Fast-path regex + LLM selection fallback | langgraph_mcp_orchestrator.py |

### Phase 5: Full Integration

*See how LangGraph and MCP combine to form the complete production backend.*

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 13 | `13_langgraph_mcp_integration.py` | LangGraph StateGraph orchestrating MCP servers | Nodes, conditional edges, `interrupt()`, `Command(resume=...)` | langgraph_mcp_orchestrator.py |
| 14 | `14_raw_jsonrpc_http.py` | Raw HTTP POST + JSON-RPC 2.0 wire protocol | `initialize` handshake, `tools/call` body, `_meta` injection, `structuredContent` | mcp_protocol.py (what StreamableHttpTransport does internally) |
| 15 | `15_mcp_to_mcp.py` | One MCP tool calling another MCP server's tool | One-shot `Client` inside `@mcp.tool`, cross-skill HTTP, non-fatal error handling | shared/mcp_client.py (planned), generate_spot_story.py |

### Phase 6: Agents and Multi-Agent Systems

*MCP has no judgment of its own — an agent is the decision loop on top of it. This phase draws that line explicitly, then shows what happens once one agent isn't enough.*

| # | File | What You Learn | Key Concept | Maps To |
|---|------|----------------|-------------|---------|
| 16 | `16_agent_vs_mcp_and_handoff.py` | Agent vs MCP boundary, agent-creates-agent, delegation vs control handoff | `Agent.run()` decision loop, agent-as-tool, `Handoff(next_agent=...)` | langgraph_mcp_orchestrator.py (`Command(goto=...)`), sphinx_leon-assistant-skills/* (each skill as agent-as-tool) |

### Helper

| File | Purpose |
|------|---------|
| `llm_helper.py` | Reusable LLM client — wraps TR Orchestrator auth. Used by lessons 07, 08, 12. |
| `.env.example` | Credentials template for LLM lessons |

## Running

```bash
# Any lesson (no .env needed for 01-06, 09-11, 13-16):
uv run python 01_hello_mcp_server.py

# LLM lessons (need .env):
uv run python 07_llm_tool_server.py
```

## Glossary

| Term | What It Means |
|------|---------------|
| **MCP** | Model Context Protocol — a standard for LLM agents to discover and call tools on external servers |
| **FastMCP** | Python framework for building MCP-compliant servers (like FastAPI for MCP) |
| **Tool** | A function the LLM agent can call — e.g., `greet`, `farewell`, `translate` |
| **Resource** | Read-only data the agent can fetch — e.g., a config file, a list of templates |
| **Prompt** | A reusable message template the agent can use — e.g., "summarize this article" |
| **Client** | Connects to an MCP server and calls its tools — `Client(server)` or `Client(transport=...)` |
| **Transport** | How client talks to server — in-process (`Client(mcp)`) or HTTP (`StreamableHttpTransport`) |
| **ToolError** | Exception you raise when a tool gets invalid input — LLM sees the error and can retry |
| **Forwarded blocks** | Data sent to the UI that the LLM agent never sees — for rich UI rendering |
| **`_meta`** | Metadata field on tool results — carries forwarded blocks and other out-of-band data |
| **Workflow** | A markdown file defining a multi-step process — name, description, which tools to use |
| **Tool gating** | Only showing the LLM the tools listed in the active workflow (not all tools) |
| **Interrupt** | Pausing execution to ask the user a question (approve draft? select RIC? choose buzz type?) |
| **SkillInterrupt** | Python class that builds the interrupt payload — type, message, actions, data |
| **ServerRegistry** | Tracks multiple MCP servers and routes tool calls to the right one |
| **Fast-path** | Regex shortcut that skips the LLM for well-known patterns — saves ~2 seconds |
| **LangGraph** | Framework for building stateful agent workflows as directed graphs (nodes + edges) |
| **StateGraph** | LangGraph's graph builder — you add nodes (functions) and edges (routing logic) |
| **Checkpointer** | Saves graph state so interrupted flows can resume later (MemorySaver, DynamoDB) |
| **`interrupt()`** | LangGraph function that pauses the graph and returns control to the caller |
| **`Command(resume=...)`** | LangGraph object that resumes a paused graph with the user's response |
| **JSON-RPC 2.0** | Wire protocol MCP uses — `{"jsonrpc":"2.0", "id":1, "method":"tools/call", "params":{...}}` |
| **`Mcp-Session-Id`** | HTTP header the server returns after `initialize` — client sends it back on all subsequent requests |
| **`structuredContent`** | Field in JSON-RPC response carrying interrupt status, continuation tokens — flattened to top-level by backend |
| **`_meta` injection** | Backend adds `_meta: {session_id, continuation_token, user_response}` to tool arguments for HITL resume |
| **MCP-to-MCP** | One MCP server's tool calling another MCP server over HTTP. Uses `Client` + `StreamableHttpTransport` (one-shot) inside the tool handler. Keeps skills decoupled — no shared imports |
| **Agent** | The decision loop on top of MCP — decides which tool to call and when to stop. MCP has no equivalent; it just answers calls |
| **Agent-as-tool** | A whole agent (loop + tools + memory) exposed as one callable — the caller only sees the final result, not the internal tool calls |
| **Agent-creates-agent** | A supervisor instantiating the specialist agent it needs *for this task*, at runtime, instead of wiring a fixed set of agents up front |
| **Delegation** | Handing off a job by calling it and waiting — caller keeps control, nested call stack (like a normal function call) |
| **Handoff (control)** | Handing off a job by transferring the active turn — caller steps aside, callee becomes the active agent. Mirrors LangGraph's `Command(goto=..., update=...)` |
| **Supervisor (agent)** | An agent whose only job is choosing or creating the right specialist for a task — not a domain tool user itself |

## Architecture (How It All Fits Together)

```
User Message
     |
     v
+--------------------+     +-----------------+
| Orchestrator (12)  | --> | MCP Servers     |
|                    |     | story-drafting  |
| 1. Discover wfs(9) |     | text-archive    |
| 2. Select wf (LLM) |     | urgent-drafting  |
| 3. Gate tools (9)  |     +-----------------+
| 4. Call tools (6)  |            |
| 5. Handle          |     +------+------+
|    interrupts (10) |     | Tools (1-3) |
| 6. Forward         |     | LLM (7)    |
|    results (8)     |     | Meta (8)   |
+--------------------+     | MCP-to-    |
                           |  MCP (15)  |
                           +-------------+
         |
         v
+--------------------+
| LangGraph (13)     |
| StateGraph nodes:  |
|  analyze -> tools  |
|  -> interrupt      |
|  -> synthesize     |
+--------------------+
```

## Production Codebase Reference

| This Series | Production Code |
|-------------|-----------------|
| FastMCP server setup | `sphinx_leon-assistant-skills/story-drafting/src/main.py` |
| Tool registration | `sphinx_leon-assistant-skills/*/src/main.py` |
| ToolError | `sphinx_leon-assistant-skills/text-archive/src/tools/` |
| Forwarded blocks | `sphinx_leon-assistant-skills/shared/src/shared/forwarded.py` |
| Workflow loader | `sphinx_leon-assistant-skills/shared/src/shared/workflows/loader.py` |
| Workflow routes | `sphinx_leon-assistant-skills/shared/src/shared/workflows/routes.py` |
| Interrupts | `sphinx_leon-assistant-skills/shared/src/shared/interrupts/models.py` |
| MCP client | `reuters-assistant_backend/src/services/mcp_protocol.py` |
| Server registry | `reuters-assistant_backend/src/services/mcp_server_registry.py` |
| Client manager | `reuters-assistant_backend/src/services/mcp_client_manager.py` |
| LangGraph orchestrator | `reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py` |
| Raw JSON-RPC wire protocol | `reuters-assistant_backend/src/services/mcp_protocol.py` (what StreamableHttpTransport does) |
| Cross-skill MCP calls | `sphinx_leon-assistant-skills/shared/src/shared/mcp_client.py` (planned) |

## Flow-to-Learning Map

See [flow_to_learning_map.txt](../../reuters-ai_assistant/reuters-assistant_backend/flow_to_learning_map.txt) — maps every step of the production orchestrator flow (HTTP POST → MCP discovery → tool wrapping → workflow loading → tool gating → MCP execution → interrupts → streaming) to specific learning files. Shows where each MCP lesson fits in the end-to-end request lifecycle alongside LangGraph, CopilotKit, FastAPI, and AWS lessons.

## Deep Dive: MCPClientManager → MCPProtocolManager

The backend's two core classes form an inheritance chain. This table maps each production pattern to the lesson that teaches it.

```
MCPClientManager (mcp_client_manager.py)      ← connection / resilience layer
       ▲
       │ inherits
       │
MCPProtocolManager (mcp_protocol.py)          ← MCP protocol / application layer
```

### MCPClientManager — Lessons 05, 06, 11

The base class handles connections, retries, and fault tolerance. No MCP protocol semantics.

| Production Pattern | Method | Lesson | Learning Equivalent |
|---|---|---|---|
| HTTP/STDIO transport creation | `_create_connection()` | 05 | `StreamableHttpTransport`, `mcp.run(transport="http")` |
| One-shot client (connect → call → disconnect) | `get_session()` | 06 | `async with Client(mcp) as client:` |
| Retry with exponential backoff | `call_tool_with_retry()` | 06 | `call_with_retry()` — `base_delay * (2 ** attempt)` |
| Circuit breaker (CLOSED/OPEN/HALF_OPEN) | `_circuit_breaker_*()` | 06 | Timeout handling, error state concepts |
| Connection pool per server | `_acquire_connection`, `_release_connection` | 11 | `ServerEntry` — per-server wrapper |
| Server registration | `register_server()` | 11 | `ServerRegistry.register()` |
| Health checks and stats | `get_server_health()`, `get_server_stats()` | 11 | `ServerEntry.discover()` |

### MCPProtocolManager — Lessons 06, 08, 10, 11, 12, 13

Extends the base with full MCP protocol: resources, prompts, streaming, tenant headers, interrupts.

| Production Pattern | Method | Lesson | Learning Equivalent |
|---|---|---|---|
| Capability discovery | `list_resources()`, `list_prompts()`, `list_tools_enhanced()` | 06 | `client.list_tools()`, `client.list_resources()`, `client.list_prompts()` |
| Tool call with tenant headers | `call_tool_enhanced()` | 06 | One-shot client pattern with per-request context |
| `_meta` / forwarded blocks | `call_tool_enhanced()` → `_meta` handling | 08 | `_meta.forwarded_blocks` — agent-visible vs UI-visible |
| Human-in-the-loop interrupts | `call_tool_enhanced()` → interrupt detection | 10 | `SkillInterrupt`, `InterruptPayload`, `.block()` |
| Tool routing across servers | used by orchestrator | 11 | `ServerRegistry.get_server_for_tool()`, `call_tools_parallel()` |
| Multi-server capability cache | `discover_server_capabilities()` | 11 | `ServerRegistry.discover_all()` |
| Fast-path regex bypass | used by orchestrator | 12 | `WorkflowOrchestrator.select_workflow_by_pattern()` |
| Full orchestration loop | used by LangGraph orchestrator | 12 | `WorkflowOrchestrator.handle_message()` |
| LangGraph StateGraph integration | `interrupt()` + `Command(resume=...)` | 13 | `call_mcp_tool()`, `discover_all_tools()`, StateGraph nodes |
| Raw JSON-RPC wire protocol | `StreamableHttpTransport` internals | 14 | Raw `POST /mcp` with `initialize`, `tools/list`, `tools/call` |
| `_meta` injection for HITL resume | `call_tool_enhanced()` → `_meta` in arguments | 14 | `arguments._meta = {session_id, continuation_token, user_response}` |
| `structuredContent` flattening | `_call_tool_result_to_dict()` | 14 | Parse `structuredContent` from JSON-RPC response |

### Reading Order for Backend Engineers

If you're working on `mcp_client_manager.py` or `mcp_protocol.py`, read the lessons in this order:

```
05 (transport)  → how servers and clients connect
06 (client)     → MCPClientManager core: retry, timeout, one-shot pattern
08 (_meta)      → MCPProtocolManager's forwarded-block handling
10 (interrupts) → MCPProtocolManager's human-in-the-loop support
11 (registry)   → MCPClientManager's registry + MCPProtocolManager's routing
12 (orchestration) → how the orchestrator drives MCPProtocolManager
13 (langgraph)  → full system: LangGraph StateGraph → MCPProtocolManager → skills
14 (wire proto)  → raw JSON-RPC over HTTP: what StreamableHttpTransport does
15 (mcp-to-mcp) → skill calling another skill over HTTP (cross-skill pattern)
```
