# MCP Glossary — Quick Reference

Cheat sheet for terms used across the 13 lessons. Open this side-by-side while reading the code.

## MCP Primitives (Lesson 04)

| Primitive | Analogy | Example |
|-----------|---------|---------|
| **Tool** | A function you can call | `draft_story(topic="oil")` — does something |
| **Resource** | A GET endpoint | `config://settings` — reads something |
| **Prompt** | A message template | `summarize(topic="oil")` — generates LLM messages |

## Server Side (Lessons 01-04, 07-10)

| Term | What It Is | First Seen |
|------|-----------|------------|
| `FastMCP` | Python framework for building MCP servers (like FastAPI for tools) | Lesson 01 |
| `@mcp.tool` | Decorator that registers a function as an MCP tool | Lesson 01 |
| `mcp.tool()(fn)` | Imperative registration — production pattern, keeps wiring separate from logic | Lesson 01 |
| `Annotated[str, Field(description="...")]` | How you describe a tool parameter so the LLM knows what to pass | Lesson 01 |
| `meta dict` | Tool metadata — `display_name`, `response_mode`, `hidden` | Lesson 01 |
| `ToolError` | Exception for invalid input — LLM sees the error message and can retry | Lesson 02 |
| **Clamping** | Silently fixing edge values instead of rejecting (e.g., `limit=200` → `limit=50`) | Lesson 02 |
| `get_logger()` | FastMCP's built-in logger (framework events) | Lesson 03 |
| `@mcp.resource("uri")` | Expose read-only data at a fixed URI | Lesson 04 |
| `@mcp.prompt()` | Define a reusable prompt template | Lesson 04 |

## Client Side (Lessons 05-06)

| Term | What It Is | First Seen |
|------|-----------|------------|
| `Client(server)` | In-process client — no network, used for testing | Lesson 01 |
| `Client(transport=StreamableHttpTransport(...))` | HTTP client — connects to a remote MCP server | Lesson 05 |
| `StreamableHttpTransport` | HTTP transport layer — POSTs to `/mcp` endpoint | Lesson 05 |
| `mcp.run(transport="http")` | Start the server as a real HTTP service | Lesson 05 |
| `stateless_http=True` | No session state between requests (each call is independent) | Lesson 05 |
| `call_tool(name, args)` | Call a tool, get back a Python dict | Lesson 01 |
| `call_tool_mcp(name, args)` | Call a tool, get back the raw MCP `CallToolResult` (preserves `_meta`) | Lesson 06 |
| **One-shot client** | Connect → call → disconnect per request (no persistent connection) | Lesson 06 |
| **Exponential backoff** | Wait 1s, 2s, 4s... between retries (don't flood a recovering server) | Lesson 06 |

## LLM Integration (Lessons 07-08)

| Term | What It Is | First Seen |
|------|-----------|------------|
| `get_llm()` | Helper that returns an `AzureChatOpenAI` instance connected to TR Orchestrator | Lesson 07 |
| `_meta` | Metadata field on tool results — carries forwarded blocks and other out-of-band data | Lesson 08 |
| `forwarded_blocks` | Content inside `_meta` that goes to the **UI** but is **invisible** to the LLM agent | Lesson 08 |
| `forwarded_tool_result()` | Helper that builds a tool result with both agent-visible text and UI-only blocks | Lesson 08 |

## Workflows (Lesson 09)

| Term | What It Is | First Seen |
|------|-----------|------------|
| **Workflow** | A markdown file that defines a multi-step process (name, description, tools, steps) | Lesson 09 |
| **YAML frontmatter** | The `---` block at the top of a workflow file — parsed into `name`, `description`, `tools` | Lesson 09 |
| `trigger_patterns` | Regex patterns that match user messages to workflows (fast-path routing) | Lesson 09 |
| **Tool gating** | Only showing the LLM the tools listed in the active workflow (hiding everything else) | Lesson 09 |
| `mount_workflows()` | Register REST endpoints (`GET /workflows`) so the orchestrator can discover them | Lesson 09 |

## Interrupts (Lesson 10)

| Term | What It Is | First Seen |
|------|-----------|------------|
| `SkillInterrupt` | Base class for all interrupt types — holds type, message, payload, actions | Lesson 10 |
| `InterruptPayload` | Typed data for the interrupt (draft text, RIC candidates, etc.) — `extra="forbid"` | Lesson 10 |
| `.block()` | Method that builds the forwarded block format from a SkillInterrupt | Lesson 10 |
| `event_type` | String that tells the frontend which UI component to render (e.g., `SPOT_STORY_REVIEW`) | Lesson 10 |
| **Actions** | Buttons the user can click — approve, refine, reject, select | Lesson 10 |

## Multi-Server (Lesson 11)

| Term | What It Is | First Seen |
|------|-----------|------------|
| `ServerEntry` | A registered MCP server with cached tool list | Lesson 11 |
| `ServerRegistry` | Central registry — maps tool names to servers, routes calls | Lesson 11 |
| **Tool routing table** | `dict[str, str]` mapping `tool_name → server_name` | Lesson 11 |
| `call_tools_parallel()` | Execute multiple tool calls across servers simultaneously via `asyncio.gather` | Lesson 11 |

## Orchestration (Lessons 12-13)

| Term | What It Is | First Seen |
|------|-----------|------------|
| **Fast-path** | Regex matching that skips the LLM for well-known patterns (~100ms vs ~2-3s) | Lesson 12 |
| **LLM selection** | Fallback: ask the LLM to pick a workflow when regex doesn't match | Lesson 12 |
| `StateGraph` | LangGraph's graph builder — add nodes (functions) and edges (routing) | Lesson 13 |
| **Node** | A function in the graph — `analyze`, `call_tools`, `human_review`, `synthesize` | Lesson 13 |
| **Conditional edge** | Routes to different nodes based on state (e.g., "needs approval?" → human_review) | Lesson 13 |
| `interrupt()` | LangGraph function — pauses the graph, checkpoints state, returns to caller | Lesson 13 |
| `Command(resume=...)` | LangGraph object — resumes a paused graph with the user's response | Lesson 13 |
| `MemorySaver` | In-memory checkpointer for LangGraph (production uses DynamoDB) | Lesson 13 |
| `OrchestratorState` | TypedDict that flows through every node — user_message, tool_results, response, etc. | Lesson 13 |

## Production Mapping

| This Guide | Production File |
|------------|----------------|
| `FastMCP(name="story-drafting")` | `sphinx_leon-assistant-skills/story-drafting/src/main.py` |
| `@mcp.tool` / `mcp.tool()(fn)` | `sphinx_leon-assistant-skills/*/src/main.py` |
| `ToolError` | `sphinx_leon-assistant-skills/text-archive/src/tools/` |
| `forwarded_tool_result()` | `sphinx_leon-assistant-skills/shared/src/shared/forwarded.py` |
| `WorkflowDef` + loader | `sphinx_leon-assistant-skills/shared/src/shared/workflows/loader.py` |
| `SkillInterrupt` | `sphinx_leon-assistant-skills/shared/src/shared/interrupts/models.py` |
| `Client` + one-shot | `reuters-assistant_backend/src/services/mcp_protocol.py` |
| `ServerRegistry` | `reuters-assistant_backend/src/services/mcp_server_registry.py` |
| `StateGraph` + nodes | `reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py` |
