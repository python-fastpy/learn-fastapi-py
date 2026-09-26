"""Lesson 02 -- MCP Client: connect to a server and call its tools
=================================================================

Lesson 01 built a server. A CLIENT does four things (plus two "under the hood"):

  1. CONNECT     async with Client(...)      start/reach the server + handshake
  2. DISCOVER    await client.list_tools()   "what can you do?"
  3. CALL        await client.call_tool()    "please run greet"
  4. ERRORS      raise_on_error=False        inspect a failure instead of crashing
  5. MESSAGES    the JSON-RPC lines the SDK sends for you (done by hand)
  6. TRANSPORTS  the same call over in-memory, stdio and HTTP

  02_mcp_client.py (client)                   01_hello_mcp_server.py --serve
  ─────────────────────────                   ──────────────────────────────
  Client(PythonStdioTransport(...))
    just a plan: "which program to start"    (nothing is running yet)
         │
  async with client:  ──── starts ─────────►  process starts, waits on stdin
         │
         │  HANDSHAKE (the SDK does this for you)
         │  1. initialize ──── stdin ──────►  "I speak 2025-03-26, I'm a client"
         │  2.            ◄─── stdout ──────  "Me too. I support tools, prompts..."
         │  3. notifications/initialized ──►  "I'm ready"  (no reply)
         │
  list_tools()        ──── tools/list ─────►
                      ◄─── greet, say_hello + their JSON schemas
         │
  call_tool("greet")  ──── tools/call ─────►  runs greet(name="Shubham")
                      ◄─── CallToolResult  {"greeting": "Hello, Shubham!"}
         │
  (end of async with) ──── closes stdin ───►  process exits

  Every arrow is ONE line of JSON-RPC text. Case 5 prints each of them.

Run:  uv run python 02_mcp_client.py      (no need to start the server yourself)

Maps to: reuters-assistant_backend/src/services/mcp_protocol.py -- the same
         client calls, over HTTP (case 6).
"""

import asyncio
import importlib.util
import json
import socket
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

# The server file next to this one (works from any folder -- see lesson notes)
SERVER = Path(__file__).parent / "01_hello_mcp_server.py"


async def cases_1_to_4():
    # 1. CONNECT -- PythonStdioTransport starts the server file as a program and
    #    talks to it over stdin/stdout. `async with` does the 3-step handshake.
    async with Client(PythonStdioTransport(SERVER, args=["--serve"])) as client:
        print("1. connected (server started, handshake done)")

        # 2. DISCOVER
        tools = await client.list_tools()
        print("2. tools :", [t.name for t in tools])               # ['greet', 'say_hello']

        # 3. CALL -- the result has three useful fields
        r = await client.call_tool("greet", {"name": "Shubham"})
        print("3. data  :", r.data)                                # {'greeting': 'Hello, Shubham!'}
        print("   text  :", r.content[0].text)                     # {"greeting":"Hello, Shubham!"}
        print("   error?:", r.is_error)                            # False

        # 4. ERRORS -- without raise_on_error=False this would raise ToolError
        r = await client.call_tool("greet", {"name": " "}, raise_on_error=False)
        print("4. error :", r.is_error, "-", r.content[0].text)    # True - name cannot be empty
    # leaving the block stops the server


async def case_5_messages_by_hand():
    # 5. MESSAGES -- no SDK: start the server and write/read JSON lines ourselves.
    #    Each line is one JSON-RPC message. A request has an "id"; its reply has
    #    the SAME id. A notification has no id and gets no reply.
    print("\n5. messages the SDK sends:")
    server = await asyncio.create_subprocess_exec(
        sys.executable, str(SERVER), "--serve",
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    async def send(message):                                        # client -> server
        line = json.dumps(message)
        print("   -->", line[:100])
        server.stdin.write((line + "\n").encode())
        await server.stdin.drain()

    async def receive():                                            # server -> client
        print("   <--", (await server.stdout.readline()).decode()[:100], "...")

    await send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "by-hand", "version": "1"}}})
    await receive()                                                 # handshake 1 + 2
    await send({"jsonrpc": "2.0", "method": "notifications/initialized"})   # 3, no reply
    await send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "greet", "arguments": {"name": "Shubham"}}})
    await receive()

    server.stdin.close()                                            # EOF stops the server
    await server.wait()


async def case_6_transports():
    # 6. TRANSPORTS -- the messages never change; the transport is only the road.
    #
    #                     the SAME JSON-RPC messages
    #              (initialize, tools/list, tools/call ...)
    #                               │
    #      ┌────────────────────────┼─────────────────────────────┐
    #      ▼                        ▼                             ▼
    #  1. IN-MEMORY             2. STDIO                      3. HTTP  (Streamable HTTP)
    #  Client(mcp)              Client(PythonStdioTransport   Client("http://host:port/mcp")
    #                                  ("server.py"))
    #
    #  ┌──────────────────┐    ┌────────┐ stdin  ┌────────┐   ┌────────┐ POST /mcp ┌────────┐
    #  │ client ⇄ server  │    │ client │ ─────► │ server │   │ client │ ────────► │ server │
    #  │  same program    │    │        │ ◄───── │program │   │        │ ◄──────── │ (runs  │
    #  └──────────────────┘    └────────┘ stdout └────────┘   └────────┘ response  │ on its │
    #                                                                              │  own)  │
    #  plain function calls    client STARTS the server,      server is ALREADY    └────────┘
    #  no process, no network  one client per server,          running; many clients,
    #                          server stops with the client    across the network
    #
    #  use for: tests          use for: local tools --        use for: production and
    #                          Claude Code, IDEs, .mcp.json   shared/remote servers,
    #                          "command" entries              .mcp.json "url" entries
    #
    #   What you pass to Client(...)             Transport picked
    #   a FastMCP server object (mcp)            FastMCPTransport          in-memory
    #   "server.py" / "server.js"                Python/NodeStdioTransport stdio
    #   StdioTransport("cmd", args=[...])        StdioTransport            stdio, any program
    #     (also UvxStdioTransport, NpxStdioTransport)
    #   "http://host:port/mcp"                   StreamableHttpTransport   HTTP (current)
    #   "http://host:port/sse"                   SSETransport              HTTP (older servers)
    #   {"mcpServers": {...}}  (like .mcp.json)  MCPConfigTransport        several servers
    print("\n6. the same greet call over all 3 transports:")

    # in-memory: import lesson 01's server object
    spec = importlib.util.spec_from_file_location("hello_server", SERVER)
    hello = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hello)
    async with Client(hello.mcp) as client:
        print("   in-memory ->", (await client.call_tool("greet", {"name": "Shubham"})).data)

    # stdio: the client starts the server itself
    async with Client(PythonStdioTransport(SERVER, args=["--serve"])) as client:
        print("   stdio     ->", (await client.call_tool("greet", {"name": "Shubham"})).data)

    # http: the server must be running FIRST; the client only connects to a URL
    with socket.socket() as s:                                      # pick a free port
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = await asyncio.create_subprocess_exec(
        sys.executable, str(SERVER), "--http", str(port),
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        for _ in range(50):                                         # wait until listening
            try:
                socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
                break
            except OSError:
                await asyncio.sleep(0.2)
        async with Client(f"http://127.0.0.1:{port}/mcp") as client:
            print("   http      ->", (await client.call_tool("greet", {"name": "Shubham"})).data)
    finally:
        server.terminate()                                          # WE stop it, not the client
        await server.wait()

    print("   Same tool, same answer -- only the road changed.")


async def main():
    await cases_1_to_4()
    await case_5_messages_by_hand()
    await case_6_transports()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Call a tool that doesn't exist -- what's the error?
# 2. Print tools[0].inputSchema to see the JSON Schema built from type hints.
# 3. In case 5, change "id": 2 to "id": 99. Which id comes back?
# 4. Start the HTTP server yourself (uv run python 01_hello_mcp_server.py --http 8765)
#    and connect two clients to http://127.0.0.1:8765/mcp at the same time.
