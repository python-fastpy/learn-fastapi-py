# MCP Glossary — Quick Reference

Cheat sheet for terms used across the 13 lessons. Open this side-by-side while reading the code.

## MCP Primitives (Lesson 04)

| Primitive | Analogy | Example |
|-----------|---------|---------|
| **Tool** | A function you can call | `draft_story(topic="oil")` — does something |
| **Resource** | A GET endpoint | `config://settings` — reads something |
| **Prompt** | A message template | `summarize(topic="oil")` — generates LLM messages |

## Server Side (Lessons 01-04)

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

## Client Side (Lessons 07-08)

| Term | What It Is | First Seen |
|------|-----------|------------|
| `Client(server)` | In-process client — no network, used for testing | Lesson 01 |
| `Client(transport=StreamableHttpTransport(...))` | HTTP client — connects to a remote MCP server | Lesson 07 |
| `StreamableHttpTransport` | HTTP transport layer — POSTs to `/mcp` endpoint | Lesson 07 |
| `mcp.run(transport="http")` | Start the server as a real HTTP service | Lesson 07 |
| `stateless_http=True` | No session state between requests (each call is independent) | Lesson 07 |
| `call_tool(name, args)` | Call a tool, get back a Python dict | Lesson 01 |
| `call_tool_mcp(name, args)` | Call a tool, get back the raw MCP `CallToolResult` (preserves `_meta`) | Lesson 08 |
| **One-shot client** | Connect → call → disconnect per request (no persistent connection) | Lesson 08 |
| **Exponential backoff** | Wait 1s, 2s, 4s... between retries (don't flood a recovering server) | Lesson 08 |

## LLM Integration (Lessons 09-10)

| Term | What It Is | First Seen |
|------|-----------|------------|
| `get_llm()` | Helper that returns an `AzureChatOpenAI` instance connected to TR Orchestrator | Lesson 09 |
| `_meta` | Metadata field on tool results — carries forwarded blocks and other out-of-band data | Lesson 10 |
| `forwarded_blocks` | Content inside `_meta` that goes to the **UI** but is **invisible** to the LLM agent | Lesson 10 |
| `forwarded_tool_result()` | Helper that builds a tool result with both agent-visible text and UI-only blocks | Lesson 10 |

## Workflows (Lesson 11)

| Term | What It Is | First Seen |
|------|-----------|------------|
| **Workflow** | A markdown file that defines a multi-step process (name, description, tools, steps) | Lesson 11 |
| **YAML frontmatter** | The `---` block at the top of a workflow file — parsed into `name`, `description`, `tools` | Lesson 11 |
| `trigger_patterns` | Regex patterns that match user messages to workflows (fast-path routing) | Lesson 11 |
| **Tool gating** | Only showing the LLM the tools listed in the active workflow (hiding everything else) | Lesson 11 |
| `mount_workflows()` | Register REST endpoints (`GET /workflows`) so the orchestrator can discover them | Lesson 11 |

## Interrupts (Lesson 06)

| Term | What It Is | First Seen |
|------|-----------|------------|
| `SkillInterrupt` | Production base class for all interrupt types — holds type, message, payload, actions (the lesson's `interrupt()` helper does the same job) | Lesson 06 |
| `InterruptPayload` | Typed data for the interrupt (draft text, RIC candidates, etc.) — `extra="forbid"` | Lesson 06 |
| `.block()` | Production method that puts the interrupt's UI payload in `_meta.forwarded_blocks`, so the agent only sees a summary | Lesson 06 (mechanism: Lesson 10) |
| `event_type` | String that tells the frontend which UI component to render (e.g., `SPOT_STORY_REVIEW`) | Lesson 06 |
| **Actions** | Buttons the user can click — approve, refine, reject, select | Lesson 06 |
| `continuation_token` | Bookmark for the saved state; sent back on resume | Lesson 06 |

## Multi-Server (Lesson 12)

| Term | What It Is | First Seen |
|------|-----------|------------|
| `ServerEntry` | A registered MCP server with cached tool list | Lesson 12 |
| `ServerRegistry` | Central registry — maps tool names to servers, routes calls | Lesson 12 |
| **Tool routing table** | `dict[str, str]` mapping `tool_name → server_name` | Lesson 12 |
| `call_tools_parallel()` | Execute multiple tool calls across servers simultaneously via `asyncio.gather` | Lesson 12 |

## Orchestration (Lessons 13-14)

| Term | What It Is | First Seen |
|------|-----------|------------|
| **Fast-path** | Regex matching that skips the LLM for well-known patterns (~100ms vs ~2-3s) | Lesson 13 |
| **LLM selection** | Fallback: ask the LLM to pick a workflow when regex doesn't match | Lesson 13 |
| `StateGraph` | LangGraph's graph builder — add nodes (functions) and edges (routing) | Lesson 14 |
| **Node** | A function in the graph — `analyze`, `call_tools`, `human_review`, `synthesize` | Lesson 14 |
| **Conditional edge** | Routes to different nodes based on state (e.g., "needs approval?" → human_review) | Lesson 14 |
| `interrupt()` | LangGraph function — pauses the graph, checkpoints state, returns to caller | Lesson 14 |
| `Command(resume=...)` | LangGraph object — resumes a paused graph with the user's response | Lesson 14 |
| `MemorySaver` | In-memory checkpointer for LangGraph (production uses DynamoDB) | Lesson 14 |
| `OrchestratorState` | TypedDict that flows through every node — user_message, tool_results, response, etc. | Lesson 14 |

## Agents and Multi-Agent (Lesson 17)

| Term | What It Is | First Seen |
|------|-----------|------------|
| **Agent** | The decision loop on top of MCP: decides which tool to call and when the task is done. MCP tools have no equivalent — they only answer calls | Lesson 17 |
| **Agent vs MCP** | MCP = protocol/interface (tools, resources, prompts). Agent = judgment layer that decides what to call. MCP works with zero agents (lessons 01-08); an agent doesn't require MCP either | Lesson 17 |
| **Agent-as-tool** | Wrapping a whole agent as one callable — caller sees only the final result, not the agent's internal tool calls. Same shape as MCP-to-MCP (Lesson 16), one level up | Lesson 17 |
| **Agent-creates-agent** | A supervisor instantiating the specialist agent it needs *for this task* at runtime, instead of a fixed pipeline of pre-wired agents | Lesson 17 |
| **Delegation** | Handing off a job by calling it and waiting — caller keeps control, nested call stack | Lesson 17 |
| **Handoff (control)** | Handing off a job by transferring the active turn — caller steps aside, callee becomes active. Mirrors LangGraph's `Command(goto=..., update=...)` | Lesson 17 |
| `Handoff` (dataclass) | This lesson's stand-in for `Command`: `Handoff(next_agent, context)` — `None` next_agent means the run is done | Lesson 17 |
| **Supervisor (agent)** | An agent whose only job is choosing/creating the right specialist — not a domain-tool user itself | Lesson 17 |
| **Planner/executor** | One agent plans the steps, a different agent executes each step and reports back — delegation with a shared plan | Lesson 17 |
| **Hierarchical supervisors** | A supervisor of supervisors — each mid-level supervisor owns a domain and creates its own specialists | Lesson 17 |
| **Blackboard / shared state** | Agents don't call each other directly; they all read/write one shared state object (LangGraph's `OrchestratorState` is a small version of this) | Lesson 17 |

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
