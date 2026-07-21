# Learn MCP (Model Context Protocol)

A 12-lesson progressive series for building MCP servers, clients, workflows, and orchestration — using the same patterns as the Reuters AI Assistant production codebase.

## Prerequisites

```bash
cd learn-mcp
uv sync          # install dependencies from pyproject.toml
```

For lessons 07, 08, 12 (LLM-powered): copy `.env.example` to `.env` and fill in TR Orchestrator credentials.

## Lesson Index

### Phase 1: Server Fundamentals (No LLM)

| # | File | Title | Concepts | Maps To |
|---|------|-------|----------|---------|
| 01 | `01_hello_mcp_server.py` | Your First MCP Server | FastMCP, @mcp.tool, Annotated params, in-process Client | story-drafting/main.py |
| 02 | `02_tool_patterns.py` | Tool Registration & Types | Decorator vs imperative, meta dict, hidden tools | story-drafting/main.py |
| 03 | `03_input_validation.py` | Validation & Error Handling | ToolError, input clamping, Pydantic Field | archive_search.py, search_rics.py |
| 04 | `04_resources_and_prompts.py` | Beyond Tools: Resources & Prompts | 3 MCP primitives, @mcp.resource, @mcp.prompt | workflows/routes.py |

### Phase 2: Client & Transport (No LLM)

| # | File | Title | Concepts | Maps To |
|---|------|-------|----------|---------|
| 05 | `05_http_transport.py` | Real HTTP Server | mcp.run(transport="http"), StreamableHttpTransport, /health | story-drafting run block |
| 06 | `06_client_patterns.py` | Discovery, Invocation & Retry | Timeout, retry with backoff, one-shot client, error handling | mcp_protocol.py, mcp_client_manager.py |

### Phase 3: LLM + Advanced (Requires .env for 07-08)

| # | File | Title | Concepts | Maps To |
|---|------|-------|----------|---------|
| 07 | `07_llm_tool_server.py` | Tools That Call LLMs | LLM inside tools, get_llm(), async LLM calls | generate_spot_story.py |
| 08 | `08_tool_result_meta.py` | ToolResult & Forwarded Blocks | _meta, forwarded_blocks, call_tool_mcp() | shared/forwarded.py |
| 09 | `09_workflows.py` | Workflow System | Markdown workflows, YAML frontmatter, mount_workflows() | shared/workflows/ |

### Phase 4: Production Patterns (No LLM for 10-11)

| # | File | Title | Concepts | Maps To |
|---|------|-------|----------|---------|
| 10 | `10_interrupts.py` | Human-in-the-Loop Interrupts | SkillInterrupt, InterruptPayload, .block(), event types | shared/interrupts/ |
| 11 | `11_multi_server.py` | Multi-Server Registry | ServerRegistry, tool routing, parallel calls | mcp_server_registry.py |
| 12 | `12_workflow_orchestration.py` | Workflow-Driven Orchestration | Full loop: discover, select, gate, execute | langgraph_mcp_orchestrator.py |

## Running

```bash
# Any lesson (no .env needed for 01-06, 09-11):
uv run python 01_hello_mcp_server.py

# LLM lessons (need .env):
uv run python 07_llm_tool_server.py
```

## Architecture

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
| Orchestrator | `reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py` |
