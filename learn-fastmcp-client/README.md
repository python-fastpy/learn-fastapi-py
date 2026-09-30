# The FastMCP Client — Consolidated

The **Clients** section of [gofastmcp.com](https://gofastmcp.com/clients/client) — 14 documentation pages — condensed into 14 runnable files.

Every lesson calls the SAME server (`target_server.py`, the "greeting service" from [`learn-fastmcp-server`](../learn-fastmcp-server/)), so what changes between files is the CLIENT feature, not a new server to learn. Read `learn-fastmcp-server` first if you want to know how `target_server.py` itself works — this folder is entirely about the code that *calls* a server.

## Setup

```bash
cd learn-fastmcp-client
uv sync
uv run python 01_client_basics.py
```

Needs `fastmcp[tasks]>=4.0.0`. Verified against **fastmcp 4.0.10** — every lesson below was run for real while writing it.

## The shared server

| File | Role |
|---|---|
| [target_server.py](target_server.py) | The server every lesson connects to: `greet`/`farewell` tools, a resource + template, a prompt, plus one tool per client feature (`greet_slowly` for progress/logging, `greet_with_approval` for elicitation, `greet_creatively` for sampling, `list_client_roots` for roots, `greet_in_background` for tasks, `add_translate_tool` for notifications). |
| [utility_server.py](utility_server.py) | A second, unrelated server with one tool (`shout`) — used only by lesson 02 to demonstrate a client connected to *two* servers at once. |

## Lessons

| # | File | Covers |
|---|------|--------|
| 01 | [01_client_basics.py](01_client_basics.py) | Creating a `Client`, the `async with` connection lifecycle, `server_info` / `instructions` / `protocol_version` / `server_capabilities` |
| 02 | [02_transports.py](02_transports.py) | In-memory, stdio (`PythonStdioTransport`), HTTP (`StreamableHttpTransport`), multi-server config dicts, transport inference and its security caveat |
| 03 | [03_tools.py](03_tools.py) | `list_tools`, `call_tool` vs `call_tool_mcp`, `.data`/`.content`/`.structured_content`/`.is_error`, timeouts, `raise_on_error`, `meta` |
| 04 | [04_resources.py](04_resources.py) | `list_resources`, `list_resource_templates`, `read_resource`, template URIs, text vs binary content |
| 05 | [05_prompts.py](05_prompts.py) | `list_prompts`, `get_prompt`, arguments, `.messages` |
| 06 | [06_sampling.py](06_sampling.py) | `sampling_handler` — lending the server your LLM |
| 07 | [07_elicitation.py](07_elicitation.py) | `elicitation_handler` — answering a server's mid-call question |
| 08 | [08_tasks.py](08_tasks.py) | Background tasks: transparent `call_tool` vs explicit `call_tool_task`, `ToolTask.status/result/cancel` |
| 09 | [09_progress.py](09_progress.py) | `progress_handler`, client-level vs per-call |
| 10 | [10_logging.py](10_logging.py) | `log_handler`, `LogMessage`, the default forward-to-`logging` behavior |
| 11 | [11_roots.py](11_roots.py) | Static list vs callback `roots`, working across both protocol eras |
| 12 | [12_notifications.py](12_notifications.py) | `message_handler` (plain function) vs `MessageHandler` (subclass with hooks) |
| 13 | [13_fastmcp_remote.py](13_fastmcp_remote.py) | The `fastmcp-remote` CLI — bridging a remote HTTP/SSE server to a stdio-only host |
| 14 | [14_client_only_package.py](14_client_only_package.py) | `fastmcp-slim` — the client without the server framework |

Lessons 13 and 14 are reference lessons (a CLI tool and a packaging choice, not a Python API), so they print an explanation instead of running a demo.

## How to test your client code

Since every lesson here is a *client*, "testing it" means confirming it talks to the server the way you expect. Four ways, cheapest first:

### 1. Just run the file

```bash
uv run python 03_tools.py
```

Every lesson's `main()` prints what it did and what came back — read the output against the file's own docstring.

### 2. Cross-check by hand in the MCP Inspector

The most useful check here: open `target_server.py` — the one real server every lesson calls — in the Inspector, and do the same thing by hand that a lesson's code does automatically. Always run FastMCP's CLI through `uv run` in this project (`target_server.py` needs `fastmcp[tasks]`, which is only visible inside this project's own environment):

```bash
uv run fastmcp dev inspector target_server.py
```

For example, to sanity-check **lesson 07** (elicitation): call `greet_with_approval` from the Inspector's UI yourself, answer its question in the form it shows you, and confirm you get the same `"Hello, Ada!"` that `07_elicitation.py`'s handler produces automatically. This is the fastest way to tell "my client code is wrong" apart from "I misunderstood what the server does" — the Inspector shows you the server's side with no client code in the way at all.

No-UI version of the same idea, straight from the terminal:

```bash
uv run fastmcp list target_server.py --resources --prompts
uv run fastmcp call target_server.py greet name=Ada
```

### 3. Point a lesson at the real Inspector-visible server over HTTP

Some lessons (02, 08) spawn `target_server.py` themselves as a subprocess. You can instead start it yourself and leave it running, so the *same* server instance is visible to both the Inspector and a lesson script at once:

```bash
uv run python target_server.py --http 8791      # terminal 1, keeps running
uv run fastmcp dev inspector target_server.py   # terminal 2, or:
```

then edit a lesson to connect to `http://127.0.0.1:8791/mcp` instead of the in-memory `target_server.mcp`, and compare.

### 4. Write your own assertion-based test

Once you're confident a pattern works, pin it down with a real test instead of eyeballing printed output:

```python
from fastmcp import Client
from target_server import mcp

async def test_greet_with_approval_when_declined():
    async def elicitation_handler(message, response_type, params, context):
        return ElicitResult(action="decline")

    async with Client(mcp, elicitation_handler=elicitation_handler) as client:
        result = await client.call_tool("greet_with_approval", {"name": "Ada"})
        assert result.data == "Greeting was not approved."
```

## Where this sits

| Folder | Scope |
|---|---|
| [`learn-fastmcp-server/`](../learn-fastmcp-server/) | Building an MCP server: all `/servers/` pages |
| **`learn-fastmcp-client/`** (this one) | Calling an MCP server: all 14 `/clients/` pages |
| [`learn-mcp/`](../learn-mcp/) | Production patterns built on top of both: workflows, orchestration, LangGraph, agents |
