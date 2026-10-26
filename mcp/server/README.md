# MCP Server -- build one, from first server to advanced

Every example is a "GreetingService", so only the MCP concept changes between files.
To **call** a server instead, see [../client](../client).

```
mcp/server/
  basic/          00 - 04   first server, tools, resources, prompts, context
  intermediate/   05 - 08   asking the client, middleware & DI, lifespan & state, configuration
  advanced/       09 - 11   transforms & visibility, composition & providers, tasks & versioning
```

### Basic: what every MCP server is made of
| File | Covers |
|---|---|
| [00_first_server.py](basic/00_first_server.py) | Create a server; stdio vs HTTP; `/health` route; in-process testing; connecting Claude |
| [01_tools.py](basic/01_tools.py) | **Tools**: schema from signature, `Field`/`Literal`, `Depends`, structured output, `ToolResult`, `ToolError`, annotations, `add_tool`, `remove_tool` |
| [02_resources.py](basic/02_resources.py) | **Resources** and templates: `{p}` `{p*}` `{?q}` `{?q*}`, mime types, multiple contents, path-traversal guard, `TextResource` and friends |
| [03_prompts.py](basic/03_prompts.py) | **Prompts**: string, conversation, `PromptResult`, JSON-string arguments |
| [04_context.py](basic/04_context.py) | **Context**: logging, progress (known or unknown total), structured logs, `get_logger`, reading other components, request state, HTTP headers |

### Intermediate: what production servers need
| File | Covers | Replaces old lesson |
|---|---|---|
| [05_server_requests.py](intermediate/05_server_requests.py) | Elicitation and sampling with the **guard pattern**: `InputRequiredResult`, `request_state`, declines, on prompts and resources too | 15 |
| [06_middleware_and_di.py](intermediate/06_middleware_and_di.py) | Middleware hooks and order; deny, rewrite, enrich, filter, state; built-ins; `Depends`, `CallArgument`, `Current*` | 18 |
| [07_lifespan_and_state.py](intermediate/07_lifespan_and_state.py) | Lifespan (`\|` composition), `UserSession` / `SessionId`, storage backends | 19 |
| [08_configuration.py](intermediate/08_configuration.py) | `on_duplicate`, strict validation, `mask_error_details`, `client_log_level`, pagination, caching, completions, icons | 03, 04 (caching), 17 |

### Advanced: big, combined or evolving servers (FastMCP-only)
| File | Covers | Replaces old lesson |
|---|---|---|
| [09_transforms_and_visibility.py](advanced/09_transforms_and_visibility.py) | Namespace, `ToolTransform`, `Tool.from_tool`, custom transforms, tool search, as-tools, Code Mode; **visibility** (`enable`/`disable`, the intersection trap), fingerprints | 10, 11, 04 (tags), 12 |
| [10_composition_and_providers.py](advanced/10_composition_and_providers.py) | `mount()`, namespaces, conflicts, live links, proxies; Local, FileSystem, Skills and custom providers | 13, 14 |
| [11_tasks_versioning_extensions.py](advanced/11_tasks_versioning_extensions.py) | Background tasks (`task=True`, modes, `Progress`); versioning and `VersionFilter`; custom protocol extensions | 20 |

Tools, resources and prompts are defined by the MCP protocol and work in every SDK.
Everything in `advanced/` is FastMCP-specific.

## The big picture

```
          MCP CLIENT (Claude Desktop, Inspector, your app)
   ┌───────────────┬─────────────────────┬──────────────────┐
   │ tools/call    │ resources/read      │ prompts/get      │
   ▼               ▼                     ▼                  │
┌──────────────────────────────────────────────────────┐    │
│ FastMCP("GreetingService")                           │    │
│                                                      │    │
│  @mcp.tool        @mcp.resource("greet://{name}")    │    │
│  def greet(...)   def greeting_for(name)             │    │
│                                                      │    │
│  @mcp.prompt                                         │    │
│  def ask_greeting(name) -> str                       │    │
│                                                      │    │
│        all three can take  ctx: Context ─────────────┼────┘
│        (log, progress, read other components)       │ notifications
└──────────────────────────────────────────────────────┘ back to client
```

## How one request travels through an assembled server

```
                         FastMCP(..., lifespan=..., middleware=[...], transforms=[...],
                                       providers=[...], auth=...)

request ──► auth (HTTP only) ──► middleware A ──► middleware B ──► transforms ──► component
            08 / below            06: logging, timing, limits       09: rename,     01-03, from a
                                                                    hide, reshape   provider (10)
            ◄──────────────────────── response unwinds back the same way ◄─────────────────┘

lifespan (07) wraps ALL of it: setup once at startup, teardown once at shutdown.
```

## How a function becomes an MCP component

```
def greet(name: str) -> str:          ──► inputSchema   {"name": {"type": "string"}}
    """Greets someone by name."""     ──► description   "Greets someone by name."
    return f"Hello, {name}!"          ──► result        TextContent "Hello, Ada!"
```

What a tool returns decides what the client gets:

```
str              ──► text
dict / dataclass ──► text + structuredContent
int / list       ──► text + structuredContent {"result": ...}
ToolResult       ──► exactly what you built, no conversion
```

## Resource URI anatomy

```
greet://{language}/{name}            hello://{name}{?language,repeat}
└─┬──┘ └────────┬───────┘            └─┬──┘└──┬──┘└─────────┬───────┘
scheme   path params (REQUIRED)     scheme  path   query params (OPTIONAL,
                                                   function args need defaults)
{p}  = one segment        {p*} = many segments (crosses "/")
{?p*} = repeated query param -> list
```

## Context: one handle, two directions

```
your tool ──ctx──┬──► CLIENT  ctx.info()  ctx.report_progress()
                 │
                 └──► SERVER  ctx.read_resource()  ctx.get_prompt()
                              ctx.get_state()      ctx.request_id
```

## The guard pattern (05): the server asks, the client answers

```
call 1:  input_responses is None  ──► return InputRequiredResult("Who?")
call 2:  input_responses["name"]  ──► return the real result
         (the client re-calls for you; carry values between rounds in request_state)
```

## Transforms: a pipeline between your tools and the client (09)

```
your tools ──► Namespace("api") ──► ToolTransform ──► TagFilter ──► client
   greet         api_greet          greet (renamed)   admin hidden
                 ▲ added first: later transforms see ITS output, so order matters
```

| Problem | Transform | Client now sees |
|---|---|---|
| Two servers both have `greet` | `Namespace("en")` | `en_greet`, `data://en/...` |
| Bad name/description on a tool you don't own | `ToolTransform` | your name and description |
| Cryptic or internal args (`n`, `user_id`) | `Tool.from_tool` + `ArgTransform` | `name`, with `user_id` hidden |
| Some tools shouldn't show | `disable(tags=...)` / `Visibility` | the rest (also blocks calling them) |
| 500 tools burn tokens | `RegexSearchTransform` / `BM25SearchTransform` | `search_tools` + `call_tool` |
| Client only supports tools | `ResourcesAsTools` / `PromptsAsTools` | `read_resource`, `get_prompt` |
| Chaining calls wastes context | `CodeMode` | `search` → `get_schema` → `execute` |

## Auth (not covered in a lesson yet)

`FastMCP("Secure", auth=JWTVerifier(jwks_uri=..., issuer=...))` gates **HTTP** transports
before any request runs. stdio is already a trust boundary, since the client launched you.
Unlike tag filtering and visibility, auth **is** a real security boundary. `UserSession` (07)
and `CurrentAccessToken` / `TokenClaim` (06) depend on it.

## Run each chapter

Always run from `mcp/server`:

```powershell
cd learn-fastapi-py\mcp\server
uv sync
uv run python basic/01_tools.py        # each file has an in-process Client demo in main()
```

Needs `fastmcp[tasks]` (already in `pyproject.toml`). Every file was run against fastmcp 4.1.4.

## Run a real server (00)

| Transport | Command | Client connects with |
|---|---|---|
| stdio | `uv run fastmcp run basic/00_first_server.py` | the client launches this command itself |
| HTTP | `uv run fastmcp run basic/00_first_server.py --transport http --port 8000` | URL `http://127.0.0.1:8000/mcp` |

`python basic/00_first_server.py --stdio` / `--http` does the same through `mcp.run()`.
Under HTTP, `curl http://127.0.0.1:8000/health` returns `OK` (the custom route).
Under stdio nothing is printed to the terminal, because stdout carries the protocol.

## Connect a real client

**Claude Code** (one command):
```powershell
uv run fastmcp install claude-code basic/00_first_server.py
```
Then run `/mcp` inside Claude Code to see `GreetingService` connected.

**Claude Desktop**:
```powershell
uv run fastmcp install claude-desktop basic/00_first_server.py
```
Restart Claude Desktop afterwards.

**Any other client (VS Code, Cursor, ...)**: generate the JSON and paste it into
that client's MCP config (e.g. `.vscode/mcp.json`):
```powershell
uv run fastmcp install mcp-json basic/00_first_server.py
```
```json
{
  "GreetingService": {
    "command": "uv",
    "args": ["run", "--with", "fastmcp", "fastmcp", "run", "C:\\...\\basic\\00_first_server.py"]
  }
}
```

**HTTP server instead?** Start it with the HTTP command above and give the client
the URL `http://127.0.0.1:8000/mcp`.

**Check it works:** ask the AI *"greet Ada"*. It should call your `greet` tool and
reply `Hello, Ada!`.

## Test in MCP Inspector

The Inspector is a browser UI that acts as an MCP client, so you can click
through tools, resources and prompts without writing a client. It needs Node.js
(it runs through `npx`).

```powershell
uv run fastmcp dev inspector basic/01_tools.py
```

1. A browser tab opens (default `http://localhost:6274`). If it asks for a token,
   use the URL printed in the terminal, which includes it.
2. Transport is **STDIO** and the command is pre-filled. Click **Connect**.
3. Open the tab for the chapter:

| Chapter | Inspector tab | What to try |
|---|---|---|
| 00 first server | **Tools**, **Resources**, **Prompts** | One of each. Run `greet` with `name=Ada`. |
| 01 tools | **Tools** → List Tools | Run `greet_annotated` with `repeat=500` to see the Field constraint reject it. Check `greet_me` has no `user` input. |
| 02 resources | **Resources** → List Resources / **Resource Templates** | Fill `greet://{language}/{name}` with `fr` / `Ada`. Try `card://../secret` to see the guard block it. |
| 03 prompts | **Prompts** → List Prompts | Render `greeting_conversation` to see the user and assistant messages. |
| 04 context | **Tools** → `greet_from_config` | Watch the log and progress messages arrive in the **Server Notifications** pane. |
| 05 server requests | **Tools** → `greet_interactively` | The Inspector shows each question as a form. Answer them yourself. |
| 09 transforms | **Tools** → List Tools | Shows the Part 1 server: `greet` is renamed from `api_greet`, `api_delete_greeting` is hidden by TagFilter, and `greet_as_me` has only a `name` input. |

Files 06–08, 10 and 11 build several small servers inside `main()`, so run them with `python`.
The Inspector only sees a module-level `mcp`.

Notes:
- Inspector imports the `mcp` object and does not run `main()`, so
  `delete_greeting` stays listed in 01 (the demo removes it only in `main()`).
- The server auto-reloads when you save the file. Click **Reconnect** if the UI goes stale.
- Use `--ui-port` / `--server-port` if the default ports are already in use.
