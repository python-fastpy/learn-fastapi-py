# Learn MCP (Model Context Protocol)

A 13-lesson progressive series for building MCP servers, clients, workflows, and orchestration — using the same patterns as the Reuters AI Assistant production codebase.

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
| 01 | `01_hello_mcp_server.py` | Register tools two ways: decorator vs imperative | `@mcp.tool` and `mcp.tool()(fn)` | story-drafting/main.py |
| 02 | `02_input_validation.py` | Reject bad input vs clamp edge values | `ToolError` vs silent clamping | archive_search.py |
| 03 | `03_logging.py` | Debug tools without print statements | `get_logger()` and log levels | story-drafting/main.py |
| 04 | `04_resources_and_prompts.py` | Expose data and templates, not just actions | Resources + Prompts (the other 2 MCP primitives) | workflows/routes.py |

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

### Helper

| File | Purpose |
|------|---------|
| `llm_helper.py` | Reusable LLM client — wraps TR Orchestrator auth. Used by lessons 07, 08, 12. |
| `.env.example` | Credentials template for LLM lessons |

## Running

```bash
# Any lesson (no .env needed for 01-06, 09-11, 13):
uv run python 01_hello_mcp_server.py

# LLM lessons (need .env):
uv run python 07_llm_tool_server.py
```

## Glossary

| Term | What It Means |
|------|---------------|
| **MCP** | Model Context Protocol — a standard for LLM agents to discover and call tools on external servers |
| **FastMCP** | Python framework for building MCP-compliant servers (like FastAPI for MCP) |
| **Tool** | A function the LLM agent can call — e.g., `draft_story`, `search_archive` |
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
+--------------------+     +-------------+
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
