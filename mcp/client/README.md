# MCP Client -- the other end of the wire

To build a server, see [../server](../server). This folder covers the code that
**calls** one. Every lesson talks to the same [greet_server.py](greet_server.py),
so only the client feature changes between files.

```
mcp/client/
  greet_server.py          the one server every lesson calls
  basic/                   00 - 04   connect, transports, calling, handlers
  intermediate/            05        the server asks the client
  advanced/                06        background tasks
```

### Basic
| File | Covers |
|---|---|
| [00_client_basics.py](basic/00_client_basics.py) | `async with` lifecycle; `server_info`, `instructions`, `protocol_version`, capabilities; how `Client()` guesses a transport and why that's a security risk |
| [01_stdio_client.py](basic/01_stdio_client.py) | The client starts the server; handshake flow; `input_schema`; `.data` vs `.text`; `raise_on_error=False`; multi-server config (`mcpServers`) |
| [02_http_client.py](basic/02_http_client.py) | The server is already running; `/health`; connect by URL; per-tenant headers; production behind a load balancer |
| [03_calling.py](basic/03_calling.py) | Tools, resources and prompts: list, then call/read/get; the `_mcp` raw versions; result faces; timeout; `ToolError`; `meta` |
| [04_handlers.py](basic/04_handlers.py) | `progress_handler` (client-wide or per call), `log_handler`, notifications (`message_handler` function or `MessageHandler` subclass) |

### Intermediate
| File | Covers |
|---|---|
| [05_server_requests.py](intermediate/05_server_requests.py) | The server asks the client: **sampling** (your LLM), **elicitation** (your user), **roots** (your folders) |

### Advanced
| File | Covers |
|---|---|
| [06_tasks.py](advanced/06_tasks.py) | Background tasks: plain `call_tool` vs `call_tool_task`, plus `status` / `result` / `cancel` |

## Run

Always run from `mcp/client`, so `greet_server` can be imported:

```powershell
cd learn-fastapi-py\mcp\client
uv sync
uv run python basic/00_client_basics.py
```

Needs `fastmcp[tasks]` (already in `pyproject.toml`). Every lesson was run against fastmcp 4.1.4.

## Which way does the conversation go?

```
             CLIENT                                     SERVER
 00-03   call_tool / read_resource / get_prompt ──────►  answers
 04      progress / log / notification handlers ◄──────  ctx.report_progress, ctx.info, list_changed
 05      sampling / elicitation / roots handlers ◄──────  "I need something from you" -> client answers
 06      call_tool_task ─── poll status ─── result ────►  runs in the background
```

## stdio vs HTTP

| | stdio (01) | HTTP (02) |
|---|---|---|
| Who starts the server | the **client** starts it | it runs on its own, **first** |
| How many clients | one (it's the client's child process) | many, over the network |
| Lifetime | stops when the client leaves | keeps running |
| Per-request data | none | HTTP headers (auth, tenant) |
| Config entry | `.mcp.json` `"command"` | `.mcp.json` `"url"` |
| Use for | local tools, IDEs, Claude Desktop | shared or production servers |

To see the HTTP split, run the server yourself:
```powershell
uv run python greet_server.py --http   # terminal 1, keeps running
uv run python basic/02_http_client.py  # terminal 2 (and a 3rd at once -- stdio can't do that)
```

## Be the stdio client yourself

Run `uv run python greet_server.py`. It prints nothing and waits. Paste these one at a time:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"me","version":"1"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"greet","arguments":{"name":"Ada"}}}
```

A request with an `"id"` gets a reply with the **same** id. The notification has no id and gets no reply. Press Ctrl+C to stop.

## How to test your client code

1. **Run the lesson.** Each `main()` prints what it sent and what came back.
2. **Check the server by hand in the Inspector.** Do manually what the lesson does in code, so you can tell "my client is wrong" apart from "I misread the server":
   ```powershell
   uv run fastmcp dev inspector greet_server.py
   ```
   For example, call `greet_with_approval` in the Tools tab, answer the form, and compare with 05.
3. **No UI, straight from the terminal:**
   ```powershell
   uv run fastmcp list greet_server.py --resources --prompts
   uv run fastmcp call greet_server.py greet name=Ada
   ```
4. **Pin it down with a pytest test.** The in-memory `Client(mcp)` needs no subprocess or port:
   ```python
   from fastmcp import Client
   from fastmcp.client.elicitation import ElicitResult
   from greet_server import mcp

   async def test_declined_greeting():
       async def decline(message, response_type, params, ctx):
           return ElicitResult(action="decline")

       async with Client(mcp, elicitation_handler=decline) as client:
           r = await client.call_tool("greet_with_approval", {"name": "Ada"})
           assert r.data == "Greeting was not approved."
   ```

## Two tools worth knowing (no code needed)

**`fastmcp-remote`** bridges a remote HTTP server to an app that can only launch local stdio commands:
```
stdio-only app  ◄──►  fastmcp-remote  ◄──►  remote HTTP server
```
```json
{ "mcpServers": { "remote-api": { "command": "uvx", "args": ["fastmcp-remote", "https://example.com/mcp"] } } }
```
- Auth: OAuth by default (opens a browser once; tokens cached in `~/.fastmcp/remote`). Use `--header "Authorization: Bearer <token>"` for a bearer token, or `--auth none` for a dev server.
- TLS: `--verify ca.pem` trusts a self-signed certificate. `--verify false` skips verification (dev only).
- Try it: `uv run python greet_server.py --http`, then `uvx fastmcp-remote http://127.0.0.1:8765/mcp --auth none`.
- Use it only for bridging. To run your own local server file, use `fastmcp run`.

**`fastmcp-slim`** is the client without the server framework, for projects that only *connect* to MCP servers:
```powershell
pip install "fastmcp-slim[client]"          # + [openai] / [anthropic] / [gemini] for sampling handlers
```
- Same import: `from fastmcp import Client`. Your code doesn't change.
- Included: HTTP/SSE clients, stdio clients, a single-server config dict, and the optional LLM sampling handlers.
- Not included: `FastMCP(...)` servers, in-memory `Client(mcp)`, multi-server configs, proxies, server auth and middleware.
- Default to plain `fastmcp`, which includes everything in slim. Use slim when you're embedding an MCP client in your own tool.
