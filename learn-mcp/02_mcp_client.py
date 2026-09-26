"""Lesson 02 -- MCP Client: the same server over STDIO and over HTTP
====================================================================

Lesson 01 called its tools in-process: `Client(mcp)`, no real server. Here
the server is a SEPARATE PROGRAM, reached two ways. The server code and the
client calls are identical in both parts -- only the road changes.

  PART A -- STDIO   the client STARTS the server and talks over stdin/stdout
                    (Claude Code, IDEs, .mcp.json "command" entries)
  1. SERVER    mcp.run()                               requests on stdin, replies on stdout
  2. CONNECT   Client(PythonStdioTransport(file))      START the server + handshake
  3. CALL      list_tools() / call_tool()              discover, then call
  4. ERRORS    call_tool(..., raise_on_error=False)    inspect a failure, don't crash

  PART B -- HTTP    the server is ALREADY RUNNING; clients connect by URL
                    (production: every skill is its own container behind an ALB)
  5. SERVER    mcp.run(transport="http", ...)          serve POST /mcp
  6. HEALTH    @mcp.custom_route("/health")            plain GET for the load balancer
  7. CONNECT   Client(StreamableHttpTransport(url))    connect by URL, same calls as 3
  8. HEADERS   StreamableHttpTransport(url, headers=)  JWT + tenant id on every request;
                                                       the tool reads them server-side

  ════════════════════════════════════════════════════════════════════════════
  PART A -- STDIO FLOW
  ════════════════════════════════════════════════════════════════════════════
  CLIENT (this file)                                 SERVER (this file, --stdio-server)
  ──────────────────                                 ──────────────────────────────────
  2. async with Client(PythonStdioTransport(...)):
         │
         ├── starts ────────────────────────────►  1. mcp.run()  waits on stdin
         │
         │   HANDSHAKE  (the SDK does it for you)
         ├── initialize ──── stdin ─────────────►  "I speak 2025-03-26"
         │              ◄─── stdout ────────────   "me too; I have tools"
         ├── notifications/initialized ─────────►  (no reply)
         │
  3. list_tools()   ──── tools/list ────────────►
                    ◄──────────────────────────   ["greet"]
     call_tool("greet", {"name": "Shubham"}) ───►  greet()
                    ◄──────────────────────────   {"greeting": "Hello, Shubham!"}
         │
  4. call_tool("greet", {"name": " "}) ─────────►  raises ToolError
                    ◄──────────────────────────   is_error=True, "name cannot be empty"
         │
  (end of async with) ── closes stdin ──────────►  server exits

  Every arrow is one line of JSON-RPC text. Exercise 3 lets you type them yourself.

  ════════════════════════════════════════════════════════════════════════════
  PART B -- HTTP FLOW
  ════════════════════════════════════════════════════════════════════════════
  CLIENT (backend)                                   HTTP SERVER  127.0.0.1:8765
  ────────────────                                   ───────────────────────────
                                                     5. mcp.run(transport="http")
                                                        starts FIRST, listens on
                                                          POST /mcp    (MCP)
                                                          GET  /health (plain REST)
         │
  6. GET /health  ────────────────────────────────►  health()
                  ◄───────────────────────────────  200 {"status": "healthy"}
         │
  7. Client(StreamableHttpTransport(url/mcp))
     list_tools()  ──── POST /mcp  tools/list ─────►
                  ◄───────────────────────────────  ["greet"]
         │
  8. for each tenant -- a NEW client with its own headers:
     ┌─ tenant-a ──────────────────────────────────────────────────────────────┐
     │ call_tool("greet") ── POST /mcp  X-Tenant-ID: tenant-a ─►  greet() reads │
     │                    ◄── {"greeting": ..., "tenant": "tenant-a"}  header   │
     └─────────────────────────────────────────────────────────────────────────┘
     ┌─ tenant-b ──────────────────────────────────────────────────────────────┐
     │ call_tool("greet") ── POST /mcp  X-Tenant-ID: tenant-b ─►  greet() reads │
     │                    ◄── {"greeting": ..., "tenant": "tenant-b"}  header   │
     └─────────────────────────────────────────────────────────────────────────┘

  IN PRODUCTION
  ─────────────
  backend ──HTTPS──► ALB ──/story-drafting──► ECS container (MCP server, port 8004)
  (one-shot client      │   (health-checks
   per call, tenant     │    GET /health)
   headers)             └──/text-archive────► ECS container (MCP server)

  stateless_http=True is what lets the ALB send each request to ANY container:
  no request depends on a session kept in one container's memory.

  ════════════════════════════════════════════════════════════════════════════
  STDIO vs HTTP
  ════════════════════════════════════════════════════════════════════════════
                    stdio (part A)                   HTTP (part B)
  who starts it     the CLIENT starts the server     server runs on its own, FIRST
  how many clients  one -- it's the client's child   many, over the network
  lifetime          stops when the client leaves     keeps running
  per-request data  none (one client anyway)         HTTP headers (auth, tenant)
  use for           local tools, .mcp.json "command" production, .mcp.json "url"

  The JSON-RPC messages are identical on both.

Run:  uv run python 02_mcp_client.py                 (both parts; starts every server itself)
  or, one piece at a time:
      uv run python 02_mcp_client.py --stdio-server  (waits for JSON-RPC on stdin -- exercise 3)
      uv run python 02_mcp_client.py --http-server   (terminal 1: serves http://127.0.0.1:8765/mcp)
      uv run python 02_mcp_client.py --http-client   (terminal 2: part B against it)

Maps to: reuters-assistant_backend/src/services/mcp_protocol.py -- the same
         list_tools() / call_tool() calls over HTTP, one-shot client per call
         with per-request tenant headers (case 8);
         story-drafting/src/main.py run block (case 5 settings, /health).
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import httpx
from fastmcp import FastMCP, Client
from fastmcp.client.transports import PythonStdioTransport, StreamableHttpTransport
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from starlette.responses import JSONResponse

URL = "http://127.0.0.1:8765"
LOG_FILE = Path(__file__).with_suffix(".server.log")    # the stdio server's stderr

mcp = FastMCP("greetings")


# ============================================================================
# The server -- ONE definition, served over stdio (part A) or HTTP (part B)
# ============================================================================

@mcp.tool
def greet(name: str) -> dict:
    """Greet someone by name."""
    if not name.strip():
        raise ToolError("name cannot be empty")          # 4. the client sees this message
    result = {"greeting": f"Hello, {name}!"}
    tenant = get_http_headers().get("x-tenant-id")       # 8. empty over stdio -- no headers
    if tenant:
        result["tenant"] = tenant
    return result


# 6. HEALTH -- a normal REST endpoint next to /mcp (ALB/ECS health checks).
#    Only exists over HTTP; stdio has no URLs.
@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "healthy"})


# ============================================================================
# PART A -- STDIO: the client starts the server
# ============================================================================

def run_stdio_server():
    # 1. SERVER -- stdio is mcp.run()'s default. It prints nothing of its own:
    #    stdout is reserved for JSON-RPC replies.
    mcp.run(show_banner=False)


async def run_stdio_client():
    # 2. CONNECT -- the transport is only a plan ("run this file with --stdio-server").
    #    `async with` starts that process and does the handshake.
    #    The server's own logs go to stderr; log_file keeps them out of this output.
    transport = PythonStdioTransport(__file__, args=["--stdio-server"], log_file=LOG_FILE)
    async with Client(transport) as client:
        print("2. connected    -> server started, handshake done")

        # 3. CALL -- discover first, then call by name
        print("3. tools        ->", [t.name for t in await client.list_tools()])   # ['greet']
        r = await client.call_tool("greet", {"name": "Shubham"})
        print("   data         ->", r.data)              # {'greeting': 'Hello, Shubham!'}  your code uses this
        print("   text         ->", r.content[0].text)   # {"greeting":"Hello, Shubham!"}   an LLM sees this
        print("   is_error     ->", r.is_error)          # False

        # 4. ERRORS -- without raise_on_error=False this line would raise ToolError
        r = await client.call_tool("greet", {"name": " "}, raise_on_error=False)
        print("4. empty name   ->", f"is_error={r.is_error},", r.content[0].text)
    # leaving the block closes stdin, and the server exits
    print("   disconnected -> server stopped (the client owned it)")


# ============================================================================
# PART B -- HTTP: the server runs on its own; clients connect by URL
# ============================================================================

def run_http_server():
    # 5. SERVER -- the exact settings production uses
    mcp.run(
        transport="http", host="127.0.0.1", port=8765,
        json_response=True,       # reply with plain JSON (not a stream)
        stateless_http=True,      # no session between requests -> any container can answer
        show_banner=False,
    )


async def run_http_client():
    # 6. HEALTH -- plain HTTP, no MCP involved
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{URL}/health")
        print("6. GET /health  ->", r.status_code, r.json())          # 200 {'status': 'healthy'}

    # 7. CONNECT -- by URL. Everything inside the block is the same as part A.
    async with Client(StreamableHttpTransport(f"{URL}/mcp")) as client:
        print("7. tools        ->", [t.name for t in await client.list_tools()])   # ['greet']
        r = await client.call_tool("greet", {"name": "Shubham"})
        print("   data         ->", r.data)          # {'greeting': 'Hello, Shubham!'}

    # 8. HEADERS -- one NEW client per call, each with its own tenant headers
    #    (the production "one-shot client" pattern: tenants never share a client)
    for tenant in ("tenant-a", "tenant-b"):
        headers = {"Authorization": "Bearer fake-jwt", "X-Tenant-ID": tenant}
        async with Client(StreamableHttpTransport(f"{URL}/mcp", headers=headers)) as client:
            r = await client.call_tool("greet", {"name": "Shubham"})
            print(f"8. {tenant:<13}->", r.data)      # {... 'tenant': 'tenant-a'} / 'tenant-b'


def run_part_b():
    # Here WE start the server, because nothing else will -- with HTTP the
    # client never starts it. In production it's already running in ECS.
    server = subprocess.Popen([sys.executable, __file__, "--http-server"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):                                   # wait for /health
            try:
                httpx.get(f"{URL}/health", timeout=0.5)
                break
            except httpx.HTTPError:
                time.sleep(0.2)
        print("5. server       -> running on its own at", f"{URL}/mcp")
        asyncio.run(run_http_client())
    finally:
        server.terminate()                                    # WE stop it, not the client
        server.wait()
    print("   (the server kept running between clients until we stopped it)")


def banner(title: str) -> None:
    print("\n" + "=" * 64 + f"\n{title}\n" + "=" * 64)


if __name__ == "__main__":
    if "--stdio-server" in sys.argv:
        run_stdio_server()
    elif "--http-server" in sys.argv:
        run_http_server()
    elif "--http-client" in sys.argv:
        asyncio.run(run_http_client())
    else:
        banner("PART A -- STDIO: the client starts the server")
        print("1. server       -> started by the client below")
        asyncio.run(run_stdio_client())

        banner("PART B -- HTTP: the server is already running")
        run_part_b()

# Exercises:
# 1. Call a tool that doesn't exist -- what does the client raise?
# 2. Print (await client.list_tools())[0].inputSchema -- the JSON Schema
#    built from greet's type hints. That's what an LLM reads.
# 3. Be the stdio client yourself. Run `uv run python 02_mcp_client.py --stdio-server`
#    and paste these lines one at a time (each is one JSON-RPC message):
#      {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"me","version":"1"}}}
#      {"jsonrpc":"2.0","method":"notifications/initialized"}
#      {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"greet","arguments":{"name":"Shubham"}}}
#    Requests with an "id" get a reply with the SAME id; the notification gets
#    none. Ctrl+C to stop. (Lesson 14 does the same over HTTP.)
# 4. Start `--http-server` in one terminal and run `--http-client` in two
#    others at once. Could you do that with stdio? Why not?
# 5. Add a second custom route, GET /status, returning the tool count.
# 6. Swap either transport for Client(mcp) -- the in-process client from
#    lesson 01. Nothing else changes. Why is that the one you'd use in tests?
