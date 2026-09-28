"""Lesson 02, part A -- MCP Client over STDIO: the client starts the server
===========================================================================

Lesson 01 called its tools IN MEMORY: `Client(mcp)` is handed the server
object itself, so client and server live in one Python program and calls are
passed directly -- no process, no port, no JSON-RPC text on a wire (FastMCP
picks `FastMCPTransport` for that; it is what you use in tests).

Here the server is a SEPARATE PROGRAM, reached two ways. The server code and
the client calls are identical in both -- only the road changes.

  IN MEMORY (lesson 01)      PART A -- STDIO            PART B -- HTTP
  Client(mcp)                Client(PythonStdio...)     Client(StreamableHttp...)
  ┌──────────────────┐       ┌────────┐ stdin ┌──────┐  ┌────────┐ POST ┌──────┐
  │ client ⇄ server  │       │ client │ ────► │server│  │ client │ ───► │server│
  │  one program     │       │        │ ◄──── │ proc │  │        │ ◄─── │(own) │
  └──────────────────┘       └────────┘ stdout└──────┘  └────────┘      └──────┘
  direct calls               JSON-RPC lines             JSON-RPC over HTTP

  Four files in this folder, one job each -- no flags, nothing re-runs itself:

    greet_server.py    the server. Run it -> STDIO. Imported by the next file
    http_server.py     serves that same server over HTTP
    stdio_client.py    THIS FILE -- part A, the stdio client
    http_client.py     part B, the HTTP client

  PART A -- STDIO   the client STARTS the server and talks over stdin/stdout
                    (Claude Code, IDEs, .mcp.json "command" entries)
  1. SERVER    greet_server.py, mcp.run()               requests on stdin, replies on stdout
  2. CONNECT   Client(PythonStdioTransport(file))       START the server + handshake
  3. CALL      list_tools() / call_tool()               discover, then call
  4. ERRORS    call_tool(..., raise_on_error=False)     inspect a failure, don't crash

  ════════════════════════════════════════════════════════════════════════════
  PART A FLOW
  ════════════════════════════════════════════════════════════════════════════
  CLIENT (this file)                                 SERVER (greet_server.py)
  ──────────────────                                 ────────────────────────
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

  Every arrow is one line of JSON-RPC text. Exercise 3 lets you type them.

  ════════════════════════════════════════════════════════════════════════════
  STDIO vs HTTP
  ════════════════════════════════════════════════════════════════════════════
                    stdio (part A, here)             HTTP (part B, http_client.py)
  who starts it     the CLIENT starts the server     server runs on its own, FIRST
  how many clients  one -- it's the client's child   many, over the network
  lifetime          stops when the client leaves     keeps running
  per-request data  none (one client anyway)         HTTP headers (auth, tenant)
  use for           local tools, .mcp.json "command" production, .mcp.json "url"

  The JSON-RPC messages are identical on both.

Run:  uv run python 02_transports/stdio_client.py    (starts greet_server.py itself)
Then: uv run python 02_transports/http_client.py     (part B)

Maps to: mcp_protocol.py -- the same list_tools() / call_tool() calls
"""

import asyncio
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

SERVER_FILE = Path(__file__).with_name("greet_server.py")
LOG_FILE = Path(__file__).with_suffix(".server.log")    # the stdio server's stderr


async def main():
    # 2. CONNECT -- the transport is only a plan ("run greet_server.py").
    #    `async with` starts that process and does the handshake. The server's
    #    own logs go to stderr; log_file keeps them out of this output.
    transport = PythonStdioTransport(SERVER_FILE, log_file=LOG_FILE)

    async with Client(transport) as client:
        print("1. server       -> started by this client, as a child process")
        print("2. connected    -> handshake done")

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
    print("   disconnected -> server stopped (this client owned it)")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Call a tool that doesn't exist -- what does the client raise?
# 2. Print (await client.list_tools())[0].inputSchema -- the JSON Schema
#    built from greet's type hints. That's what an LLM reads.
# 3. Be the stdio client yourself. Run `uv run python 02_transports/greet_server.py`
#    and paste these lines one at a time (each is one JSON-RPC message):
#      {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"me","version":"1"}}}
#      {"jsonrpc":"2.0","method":"notifications/initialized"}
#      {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"greet","arguments":{"name":"Shubham"}}}
#    Requests with an "id" get a reply with the SAME id; the notification gets
#    none. Ctrl+C to stop. (Lesson 14 does the same over HTTP.)
# 4. Delete log_file= and run again -- the server's stderr now lands in your
#    terminal, mixed in with this output. That is what it is keeping out.
# 5. Swap the transport for Client(mcp) from lesson 01, importing mcp from
#    greet_server. Nothing else changes. Why is that the one you'd use in tests?
