"""Lesson 02 -- MCP Client: connect to a server and call its tools
=================================================================

Lesson 01 built a server. This lesson is the other side: a CLIENT that
starts the server, asks what tools it has, and calls one.

  02_mcp_client.py (client)                 01_hello_mcp_server.py --serve
  ─────────────────────────                 ──────────────────────────────
  async with client:  ──── starts ──────►  server process starts
        │
        │  handshake (the SDK does it for you)
        │  1. initialize  ─────────────────►  "I'm a client, I speak MCP 2025-03-26"
        │  2.             ◄─────────────────  "Me too. I have tools, prompts, ..."
        │  3. initialized ─────────────────►  "Ready."  (no reply)
        │
  list_tools()        ──── tools/list ────►
                      ◄─── greet, greet_styled
  call_tool("greet")  ──── tools/call ────►  runs greet(name="Shubham")
                      ◄─── {"greeting": "Hello, Shubham! ..."}
        │
  (end of async with) ──── stops ───────►  server process exits

  Each arrow is one line of JSON text sent over the server's stdin/stdout.
  PART 2 prints those lines so you can see them.

Run:  uv run python 02_mcp_client.py      (no need to start the server yourself)

Maps to: reuters-assistant_backend/src/services/mcp_protocol.py -- same thing,
         over HTTP (StreamableHttpTransport, lesson 05) instead of stdio.
"""

import asyncio
import json
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

SERVER = Path(__file__).parent / "01_hello_mcp_server.py"


# ============================================================================
# PART 1: The normal way -- the SDK does everything
# ============================================================================

async def part1_sdk():
    print("=== PART 1: using the SDK ===\n")

    # Which program to start. `--serve` makes lesson 01 run as a real server.
    client = Client(PythonStdioTransport(SERVER, args=["--serve"]))

    async with client:                        # start server + handshake
        tools = await client.list_tools()     # "what can you do?"
        print("Tools:", [t.name for t in tools])

        result = await client.call_tool("greet", {"name": "Shubham"})
        print("greet ->", result.data)        # .data = the tool's return value
    # leaving the block stops the server


# ============================================================================
# PART 2: The same thing by hand -- see every message
# ============================================================================

async def part2_by_hand():
    print("\n=== PART 2: the messages the SDK sends ===\n")
    server = await asyncio.create_subprocess_exec(
        sys.executable, str(SERVER), "--serve",
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )

    async def send(message):                  # client -> server
        line = json.dumps(message)
        print("-->", line[:110])
        server.stdin.write((line + "\n").encode())
        await server.stdin.drain()

    async def receive():                      # server -> client
        line = (await server.stdout.readline()).decode().strip()
        print("<--", line[:110] + "...\n")

    await send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
        "protocolVersion": "2025-03-26", "capabilities": {},
        "clientInfo": {"name": "by-hand", "version": "1"}}})
    await receive()                                                   # 1 + 2
    await send({"jsonrpc": "2.0", "method": "notifications/initialized"})
    print("    (no reply -- notifications don't get one)\n")             # 3
    await send({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                "params": {"name": "greet", "arguments": {"name": "Shubham"}}})
    await receive()

    server.stdin.close()                      # closing stdin stops the server
    await server.wait()


async def main():
    await part1_sdk()
    await part2_by_hand()


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # A client does 3 things: connect (handshake), list_tools(), call_tool().
    # Under the hood each is a JSON-RPC message with an "id"; the reply has
    # the same id, which is how answers are matched to questions.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Call greet_styled with style="pirate". What does result.is_error say?
    #    (hint: call_tool(..., raise_on_error=False))
    # 2. Call a tool that doesn't exist -- what's the error?
    # 3. Print tools[0].inputSchema to see the JSON Schema built from type hints
    # 4. In PART 2, change "id": 2 to "id": 99. Which id comes back?
