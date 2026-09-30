# The FastMCP Server — Consolidated

The **Servers** section of [gofastmcp.com](https://gofastmcp.com/servers/server) — 28 documentation pages — condensed into 17 runnable files.

Every file runs standalone and prints its output, so you see each concept rather than read about it. No `.env`, no API keys, no LLM.

## One example, seventeen lessons

Every lesson greets someone. The domain never changes, so what you notice between files is the **feature**, not a new set of nouns:

| The cast | Appears as |
|---|---|
| `greet(name)` | the tool — decorated, renamed, hidden, namespaced, searched, filtered, fingerprinted, paginated, iconified |
| `farewell(name)` | the second tool, whenever one isn't enough |
| `greet_debug` / `greet_as_admin` / `greet_premium` | the tools that get filtered out |
| `Greeting` dataclass | structured output (06) |
| `data://greeting-config` | the static resource |
| `greet://{name}` , `greet://{language}/{name}` | the resource templates |
| `ask_greeting(name)` | the prompt |
| tags `public` `internal` `admin` `deprecated` | what visibility and tag filtering act on |

So when lesson 10 renames `verbose_greeting_generator` to `greet`, or lesson 14 mounts an English and a French server that both export `greet`, you already know the function — the only new thing on the page is the mechanism.

## Setup

```bash
cd learn-fastmcp-server
uv sync
uv run python 01_create_and_components.py
```

Needs `fastmcp>=4.0.0`. Verified against **fastmcp 4.0.10** on 2026-09-30 — all 17 lessons exit 0.

## How to test your server

Five ways to check a server works, from fastest to most realistic. All of
them work on any lesson file, because every lesson names its server `mcp`.

### 1. Just run the file (no setup)

Every lesson already IS a test: its `main()` connects an in-process client,
calls every tool/resource/prompt, and prints the result.

```bash
uv run python 01_create_and_components.py
```

If it exits without a traceback and the printed output looks right, the
server works.

### 2. Ask it questions from the command line

No code needed. `fastmcp list` shows what a server exposes; `fastmcp call`
runs one tool and prints the result. Run these through `uv run` so the
command sees this project's own environment (lesson 20 needs
`fastmcp[tasks]`, which only exists inside it):

```bash
uv run fastmcp list 01_create_and_components.py --resources --prompts
uv run fastmcp call 01_create_and_components.py greet name=Ada
```

(On this fastmcp version, `list` prints some noisy but harmless warnings to
stderr first -- add `2>$null` in PowerShell or `2>/dev/null` in bash to
hide them. `call` is clean.)

### 3. Click through it in a browser

`fastmcp dev inspector` starts your server and opens the official MCP
Inspector UI, where you can browse every tool/resource/prompt and call
them by hand with a form:

```bash
uv run fastmcp dev inspector 01_create_and_components.py
```

Best for exploring a server you don't know yet, or for the interactive
lessons (15-17) where you want to see the prompts/completions as a client
would.

### 4. Connect a real client (Claude Desktop / Claude Code)

The real end-to-end test: point an actual MCP client at your server and
talk to it. Add an entry like this to the client's MCP config (lesson 02's
file is the one built to actually serve over stdio, via its `--stdio` flag):

```json
{
  "mcpServers": {
    "greeting-service": {
      "command": "uv",
      "args": ["run", "python", "02_running_and_routes.py", "--stdio"]
    }
  }
}
```

Most lesson files (01, 03-20) only run their own demo in `__main__` and
don't take a `--stdio` flag -- for those, call `mcp.run()` yourself from a
one-line script, or use options 2/3/5 above instead.

### 5. Write your own quick script

Copy the pattern every lesson already uses -- it's the basis for a real
pytest test too:

```python
from fastmcp import Client
from my_server import mcp

async def test_greet():
    async with Client(mcp) as client:
        result = await client.call_tool("greet", {"name": "Ada"})
        assert result.data == "Hello, Ada!"
```

No server process, no network -- the in-process `Client` talks straight to
your `FastMCP` object, so this is the fastest way to assert real behavior
in CI.

## Lessons

### Part 1 — The server object (`/servers/server`)

| # | File | Covers |
|---|------|--------|
| 01 | [01_create_and_components.py](01_create_and_components.py) | `name`, `instructions`, `version`, `website_url`, `icons`; the three component types; decorator vs `tools=[...]` |
| 02 | [02_running_and_routes.py](02_running_and_routes.py) | `mcp.run()` STDIO / HTTP / SSE; the `__main__` guard; `@mcp.custom_route` |
| 03 | [03_configuration.py](03_configuration.py) | `on_duplicate`, `strict_input_validation`, `mask_error_details`, `list_page_size`, `client_log_level`, `dereference_schemas`, `tasks`, `session_state_store` |
| 04 | [04_caching_and_tags.py](04_caching_and_tags.py) | `cache_ttl` / `cache_scope`; tag filtering with `enable(only=True)` / `disable()` |
| 05 | [05_assembly.py](05_assembly.py) | Overview of `middleware`, `providers`, `transforms`, `lifespan`, `auth`, `experimental_capabilities` |

### Part 2 — Components

| # | File | Covers |
|---|------|--------|
| 06 | [06_tools.py](06_tools.py) | Decorator args, type hints, `Annotated` + `Field`, docstring `Args:`, `Depends()` to hide params, structured output, `ToolResult`, `ToolError`, `ToolAnnotations`, `timeout`, `add_tool` / `remove_tool` |
| 07 | [07_resources.py](07_resources.py) | URIs, return types, `ResourceResult` / `ResourceContent`, templates, wildcards `{p*}`, query params `{?a,b}`, explode `{?t*}`, path-traversal screening, `ResourceSecurity`, resource classes |
| 08 | [08_prompts.py](08_prompts.py) | `str` / `list[Message]` / `PromptResult`, roles, typed args as JSON strings, required vs optional, docstring arg descriptions |
| 09 | [09_context.py](09_context.py) | `CurrentContext()` vs type-hint vs `get_context()`, logging, progress, `read_resource`, `list_prompts` / `get_prompt`, request state, request metadata, HTTP headers, why `ctx.sample` is gone |

### Part 3 — Transforms

| # | File | Covers |
|---|------|--------|
| 10 | [10_transforms_basics.py](10_transforms_basics.py) | The `Transform` interface (both patterns), `Namespace`, `ToolTransform` vs `Tool.from_tool`, `ArgTransform` (rename / hide / `default_factory`), `transform_fn` + `forward()`, provider vs server scope, ordering |
| 11 | [11_transforms_advanced.py](11_transforms_advanced.py) | `RegexSearchTransform`, `BM25SearchTransform`, Code Mode end-to-end with a custom `SandboxProvider`, `ResourcesAsTools`, `PromptsAsTools` |
| 12 | [12_visibility.py](12_visibility.py) | Full `enable`/`disable` API, component keys, the intersection trap, allowlist mode, provider vs server precedence, session scope, the `Visibility` transform, tool fingerprinting + CI drift detection |

### Part 4 — Providers and composition

| # | File | Covers |
|---|------|--------|
| 13 | [13_providers.py](13_providers.py) | `LocalProvider` standalone, `FileSystemProvider` (with real files on disk), a custom `Provider` with `lifespan`, `create_proxy`, `SkillsDirectoryProvider` |
| 14 | [14_composition.py](14_composition.py) | `mount()` as a live link, `namespace=`, URI prefixing, conflict resolution, tag filtering through a mount, custom routes, mounting external servers |

### Part 5 — Talking to the client

| # | File | Covers |
|---|------|--------|
| 15 | [15_elicitation_and_sampling.py](15_elicitation_and_sampling.py) | Why `ctx.elicit()` and `ctx.sample()` broke; the `InputRequiredResult` guard pattern on tools *and* prompts *and* resources; `ctx.input_responses`, sealed `ctx.request_state`, `input_required_max_rounds`; borrowing the caller's model vs calling an LLM yourself |
| 16 | [16_progress_and_logging.py](16_progress_and_logging.py) | `report_progress` (percentage / absolute / indeterminate / multi-stage), the four log levels, `logger_name`, `extra`, `ctx.log()`, the server-side mirror logger, and how both go silently no-op |
| 17 | [17_completions_pagination_icons.py](17_completions_pagination_icons.py) | `@mcp.completion` for prompt args and template params, dependent completions via `context.arguments`, `Completion(total, has_more)`; `list_page_size` + manual cursor paging; `Icon` on servers and all four component types, themes, data URIs |

## Page → lesson map

All 28 pages:

| Docs page | Lesson |
|---|---|
| `/servers/server` | 01–05 |
| `/servers/tools` | 06 |
| `/servers/resources` | 07 |
| `/servers/prompts` | 08 |
| `/servers/context` | 09 |
| `/servers/transforms/transforms` | 10 |
| `/servers/transforms/namespace` | 10 |
| `/servers/transforms/tool-transformation` | 10 |
| `/servers/transforms/tool-search` | 11 |
| `/servers/transforms/code-mode` | 11 |
| `/servers/transforms/resources-as-tools` | 11 |
| `/servers/transforms/prompts-as-tools` | 11 |
| `/servers/visibility` | 12 |
| `/servers/tool-fingerprinting` | 12 |
| `/servers/providers/overview` | 13 |
| `/servers/providers/local` | 13 |
| `/servers/providers/filesystem` | 13 |
| `/servers/providers/custom` | 13 |
| `/servers/providers/proxy` | 13 |
| `/servers/providers/skills` | 13 |
| `/servers/composition` | 14 |
| `/servers/elicitation` | 15 |
| `/servers/sampling` | 15 |
| `/servers/progress` | 16 |
| `/servers/logging` | 16 |
| `/servers/completions` | 17 |
| `/servers/pagination` | 17 |
| `/servers/icons` | 17 |

## The whole thing in one diagram

```
                        FastMCP("MyServer", ...)
                                  │
   ┌──────────────┬───────────────┼───────────────┬──────────────┐
IDENTITY       BEHAVIOR        ASSEMBLY        STORAGE        RUNNING
name           on_duplicate    middleware      session_       run()
instructions   strict_input_   transforms       state_store    stdio
version         validation     providers                       http
website_url    mask_error_     lifespan                        sse
icons           details        auth                           custom_route
  (01)         cache_ttl        (05, 10-14)     (03)           (02)
               list_page_size
               client_log_level
                 (03, 04)
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
   WHERE COMPONENTS COME FROM (providers, 13)
   ┌─────────────┬──────────────┬─────────────┬──────────────┐
   │LocalProvider│FastMCPProvider│ProxyProvider│FileSystem /  │
   │ @mcp.tool   │ mcp.mount(14) │create_proxy │Skills/custom │
   └─────────────┴──────────────┴─────────────┴──────────────┘
                                  │
   WHAT THEY ARE (06, 07, 08)         + icons (17)
   ┌──────────────┬───────────────────┬──────────────────┐
   │  @mcp.tool   │  @mcp.resource    │   @mcp.prompt    │
   │  DO a thing  │  READ some data   │  REUSE a message │
   └──────────────┴───────────────────┴──────────────────┘
        │  ← Context (09): log, progress, read, state, who
        ▼
   HOW THEY ARE PRESENTED (transforms, 10-12)
   Namespace · ToolTransform · Visibility · Search · CodeMode
   ResourcesAsTools · PromptsAsTools · your own Transform
                                  │
                                  ▼
                               client
                                  │
   WHAT CROSSES BACK (15, 16, 17)
   ┌─────────────────────────────┬────────────────────────────────┐
   │ NOTIFICATIONS -- no answer  │ REQUESTS -- need an answer     │
   │ fire-and-forget, still fine │ era-gated, use the guard       │
   │   progress   (16)           │   elicitation  (15)            │
   │   logging    (16)           │   sampling     (15)            │
   │                             │   -> InputRequiredResult       │
   ├─────────────────────────────┴────────────────────────────────┤
   │ CLIENT-DRIVEN: completions · pagination cursors      (17)    │
   └──────────────────────────────────────────────────────────────┘
```

## Things worth remembering

| Concept | The point |
|---|---|
| **Tool vs resource vs prompt** | A tool *does*. A resource is passive data addressed by URI. A prompt returns *messages*, not a result for your code. |
| **`structuredContent` wrapping** | Objects always get structured output. A primitive with a return hint is wrapped as `{"result": N}` — which is what you must unwrap inside Code Mode. |
| **`Depends()` hides parameters** | User IDs and credentials should not be in the schema at all. `ArgTransform(hide=True, default=...)` does the same for a tool you don't own. |
| **Transform vs middleware** | Middleware sits on the message path (log, time, limit). A transform changes how components are *presented* (rename, hide, reshape). |
| **Transform getters run backwards** | `list_tools` rewrites outbound; `get_tool` must map the client's name *back* to the original before calling `call_next`. |
| **Provider vs decorator** | Decorators resolve once at import. Providers are asked on every request, so their component list can change at runtime. |
| **Filtering is not security** | `disable()` is a default, not a guarantee — a later `enable()` can undo it. And multiple filters in one call **intersect**: a rule that matches nothing fails silently. If something must be unreachable, don't register it, or use `auth`. |
| **Search hides, it does not block** | Tool Search removes tools from the *listing*. They stay directly callable. Discovery ≠ access. |
| **`mount()` is a live link** | Not a copy. A tool added to the child after mounting is immediately reachable — and every parent listing pays every child's latency. |
| **Caching is a hint** | `cache_ttl` does nothing unless the client opts in on the modern protocol. |
| **Notifications survived, requests didn't** | Logging and progress are fire-and-forget on the open stream, so they still work. Elicitation and sampling needed an answer back, so the modern protocol replaced them with the guard pattern: return the ask, get re-called with the answer. |
| **Every guard round re-runs the tool** | It keeps nothing in memory between rounds — which is exactly why a different worker can answer round 3. Carry values in `ctx.request_state`, which FastMCP seals and verifies for you. |
| **Progress and logs can vanish silently** | No `progressToken` means `report_progress()` is a no-op; logs under `client_log_level` are dropped. Neither errors. Never put anything you need in either. |

## Version notes (fastmcp 4.0.10)

Things that differ from what the docs describe — each verified by running it:

- **Modern protocol era by default.** `client.initialize_result` is `None` and `client.initialize()` raises. Read `client.server_info`, `client.instructions`, `client.server_capabilities`, `client.protocol_version` instead (01, 05).
- **`ctx.elicit()` fails on the modern protocol** — it is a server-initiated request and the 2026-07-28 era removed that channel (SEP-2322); a client `elicitation_handler` does not help. Not a bug: the replacement is the `InputRequiredResult` guard pattern, which lesson 15 runs end to end on tools, prompts and resources.
- **`ctx.sample()` and `ctx.sample_step()` were removed in FastMCP 4** — `AttributeError` on every era, and `FastMCP(sampling_handler=...)` raises `TypeError`. Either call an LLM from the server directly or put a `CreateMessageRequest` through the same guard pattern (15). Stay on 3.x if you need the old behaviour.
- **The logging *capability* is deprecated** as of 2026-07-28 (SEP-2577), so `ctx.info()` et al. emit a deprecation warning even though they still deliver. Notifications survived the era change because they are fire-and-forget; requests did not (16).
- **Session-scoped visibility is a no-op.** `ctx.enable_components()` / `disable_components()` have no observable effect — tested in-memory and over HTTP, with and without a `session_state_store`, for both enable and disable. Global `mcp.enable()` / `mcp.disable()` work correctly (12).
- **Transform getters take a keyword-only `version`.** `async def get_tool(self, name, call_next, *, version=None)`, and you must pass it through to `call_next`. The docs' v3-era signature raises `TypeError` (10).
- **No `import_server()`.** `mount()` is the composition API (14).
- **A bare exception inside a `transform_fn`** surfaces as a protocol-level "Internal server error", not a readable tool error. Raise `ToolError` (10).
- **Code Mode's `execute` needs `pydantic-monty`** (`fastmcp[code-mode]`). Discovery works without it; lesson 11 supplies a tiny custom `SandboxProvider` so the whole flow runs — clearly marked as *not* a sandbox.
- **Renamed protocol fields.** `inputSchema` → `input_schema`, `uriTemplate` → `uri_template`, `nextCursor` → `next_cursor`. The old names still work but warn.
- **`extra` keys collide with `LogRecord`.** `ctx.info(msg, extra={"name": x})` raises *"Attempt to overwrite 'name' in LogRecord"* — `extra` lands on a Python log record, so avoid its reserved attributes (`name`, `message`, `msg`, `levelname`, `args`, `module`, …) and prefix your keys (16).

## Where this sits

| Folder | Scope |
|---|---|
| **`learn-fastmcp-server/`** (this one) | The server side of FastMCP: all 21 `/servers/` pages |
| [`learn-mcp/`](../learn-mcp/) | The 16-lesson series: clients, transports, HITL interrupts, workflows, multi-server routing, LangGraph orchestration, raw JSON-RPC |

Read this folder to learn the server object cold; read `learn-mcp` for the orchestration built on top of it.
