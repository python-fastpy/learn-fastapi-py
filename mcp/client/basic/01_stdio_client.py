"""STDIO client -- the client STARTS the server
=====================================================

Three ways a client reaches a server. Same calls in all three; only the road changes:

  IN MEMORY (tests)          STDIO (this file)            HTTP (02_http_client.py)
  Client(mcp)                Client(PythonStdio...)       Client(StreamableHttp...)
  ┌──────────────────┐       ┌────────┐ stdin ┌──────┐    ┌────────┐ POST ┌──────┐
  │ client ⇄ server  │       │ client │ ────► │server│    │ client │ ───► │server│
  │  one program     │       │        │ ◄──── │ proc │    │        │ ◄─── │(own) │
  └──────────────────┘       └────────┘ stdout└──────┘    └────────┘      └──────┘
  direct calls               JSON-RPC lines               JSON-RPC over HTTP

THE FLOW
  CLIENT (this file)                              SERVER (greet_server.py)
  async with Client(transport):
      ├── starts the process ──────────────────►  mcp.run()  waits on stdin
      │   HANDSHAKE (the SDK does it for you)
      ├── initialize ─────────── stdin ────────►  "I speak protocol X"
      │              ◄────────── stdout ───────   "me too; I have tools"
      ├── notifications/initialized ───────────►  (no reply -- it's a notification)
  list_tools()  ── tools/list ─────────────────►
                ◄──────────────────────────────   ["greet"]
  call_tool("greet", {"name": "Ada"}) ─────────►  greet()
                ◄──────────────────────────────   {"greeting": "Hello, Ada!"}
  (end of async with) ── closes stdin ─────────►  server exits

Every arrow is one line of JSON-RPC text -- the README shows how to type them yourself.

MULTI-SERVER: one client, many servers. Names get a prefix per server:
    Client({"mcpServers": {"a": {...}, "b": {...}}})   ->  a_greet, b_greet

Level: BASIC
Run:  uv run python basic/01_stdio_client.py      (starts greet_server.py itself)
"""

import asyncio
import logging
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

SERVER_FILE = Path(__file__).parent.parent / "greet_server.py"   # mcp/client/greet_server.py
LOG_FILE = Path(__file__).with_suffix(".server.log")   # the server's stderr goes here


async def demo_stdio():
    # EXPLICIT transport -- Client("greet_server.py") would guess the same,
    # but this way you control args/env/cwd. The transport is only a plan ("run greet_server.py"). `async with`
    # starts the process and does the handshake. log_file keeps the server's
    # stderr out of this output.
    transport = PythonStdioTransport(SERVER_FILE, log_file=LOG_FILE)

    async with Client(transport) as client:
        print("connected   -> server started as a child process, handshake done")

        # discover first, then call by name
        tools = await client.list_tools()
        print("tools       ->", [t.name for t in tools])
        print("input_schema->", tools[0].input_schema)    # what an LLM reads

        r = await client.call_tool("greet", {"name": "Ada"})
        print("data        ->", r.data)                  # what your code uses
        print("text        ->", r.content[0].text)       # what an LLM sees

        # errors: raise_on_error=False returns the failure instead of raising ToolError
        r = await client.call_tool("greet", {"name": " "}, raise_on_error=False)
        print("empty name  ->", f"is_error={r.is_error},", r.content[0].text)

    print("disconnected-> server stopped (this client owned it)")


async def demo_multi_server():
    """The same config shape as Claude Desktop / .mcp.json "mcpServers"."""
    logging.getLogger("fastmcp").setLevel(logging.WARNING)   # hide the multi-server info chatter
    server = {"command": sys.executable, "args": [str(SERVER_FILE)],
              "env": {"FASTMCP_LOG_LEVEL": "WARNING"}}       # quiet the servers' startup logs
    async with Client({"mcpServers": {"main": server, "backup": server}}) as client:
        names = sorted(t.name for t in await client.list_tools() if t.name.endswith("_greet"))
        print("\nmulti-server-> ", names)
        print("main_greet  ->", (await client.call_tool("main_greet", {"name": "Ada"})).data)


async def main():
    await demo_stdio()
    await demo_multi_server()


if __name__ == "__main__":
    asyncio.run(main())
