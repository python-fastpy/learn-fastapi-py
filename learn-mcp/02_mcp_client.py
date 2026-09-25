"""
Lesson 2: MCP Client
=====================
Goal: Connect to an MCP server programmatically and call tools -- then
see exactly which messages the SDK sends to do it.

What you'll learn:
  - fastmcp.Client for calling MCP servers over stdio
  - The JSON-RPC handshake (initialize -> response -> notifications/initialized)
  - list_tools() and call_tool()
  - Inspecting CallToolResult (.content, .data, .is_error)
  - PART 2: the same handshake done by hand, every message printed

Run:
  uv run python 02_mcp_client.py

  (No need to start the server separately -- the client launches
   01_hello_mcp_server.py --serve as a subprocess automatically)

How stdio transport works:
  +-------------------+   JSON-RPC, one message per line   +-------------------------+
  | 02_mcp_client.py  | ---- writes to server's stdin ---> | 01_hello_mcp_server.py  |
  | (client)          | <--- reads server's stdout ------- | --serve  (subprocess)   |
  +-------------------+                                    +-------------------------+
  Same JSON messages as HTTP (lesson 14 shows those as POST /mcp requests);
  only the pipe is different.

Production parallel:
  reuters-assistant_backend/src/services/mcp_protocol.py does exactly this
  with StreamableHttpTransport instead of stdio. Each tool call creates a
  one-shot client for tenant header isolation.

EXPECTED OUTPUT (abridged):
  ######## PART 1: The SDK way ########
  === Available Tools ===
    greet: Generate a personalized greeting.
      - name: string
    farewell: Generate a personalized farewell message.
      - name: string

  === Calling greet ===
    text   : {"greeting":"Hello, Shubham! Welcome to MCP.","server":"learn-mcp"}
    data   : {'greeting': 'Hello, Shubham! Welcome to MCP.', 'server': 'learn-mcp'}
  ...
  ######## PART 2: The same handshake, by hand ########
  --- 1. initialize ---
    --> {"jsonrpc": "2.0", "id": 1, "method": "initialize", ...}
    <-- {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-03-26",...}}
  --- 2. notifications/initialized ---
    --> {"jsonrpc": "2.0", "method": "notifications/initialized"}
        (no reply -- notifications never get one)
  ...
"""

import asyncio
import json
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

# Resolve the server next to this file, so it works from any directory.
SERVER = Path(__file__).parent / "01_hello_mcp_server.py"


# ============================================================================
# PART 1: The SDK way
# ============================================================================

async def sdk_demo():
    print("######## PART 1: The SDK way ########\n")

    # --- Step 1: Connect to the server ---
    # PythonStdioTransport starts the .py file as a subprocess and talks to it
    # over stdin/stdout. `--serve` makes lesson 01 run as a real MCP server
    # instead of its own demo. In production you'd use StreamableHttpTransport
    # with a URL (lesson 05).
    client = Client(PythonStdioTransport(SERVER, args=["--serve"]))

    async with client:
        # Entering `async with` starts the subprocess and performs the handshake:
        #   1. client -> server: initialize            (versions + capabilities)
        #   2. server -> client: initialize result     (the server's capabilities)
        #   3. client -> server: notifications/initialized  ("I'm ready")
        # Over stdio these are lines of JSON on stdin/stdout; over HTTP they are
        # POST /mcp requests. PART 2 below prints every one of them.

        # --- Step 2: Discover available tools ---
        tools = await client.list_tools()
        print("=== Available Tools ===")
        for tool in tools:
            print(f"  {tool.name}: {tool.description}")
            if tool.inputSchema:
                props = tool.inputSchema.get("properties", {})
                for param, schema in props.items():
                    print(f"    - {param}: {schema.get('type', '?')}")
        print()

        # --- Step 3: Call tools ---
        # call_tool() returns ONE CallToolResult object (fastmcp 3.x), not a list:
        #   .content  -> list of content blocks (TextContent, ...) -- what an LLM sees
        #   .data     -> the tool's return value, parsed back into Python
        #   .is_error -> True if the tool failed
        print("=== Calling greet ===")
        result = await client.call_tool("greet", {"name": "Shubham"})
        for content in result.content:
            print(f"  type   : {content.type}")
            print(f"  text   : {content.text}")
        print(f"  data   : {result.data}")
        print(f"  error? : {result.is_error}")
        print()

        print("=== Calling farewell ===")
        result = await client.call_tool("farewell", {"name": "Shubham"})
        print(f"  Result: {result.data}")
        print()
    # Leaving `async with` closes the connection and the server process exits.


# ============================================================================
# PART 2: The same handshake, by hand -- every message printed
# ============================================================================
# No SDK: start the server ourselves and write/read JSON lines directly.
# This is what Client + PythonStdioTransport did for you in part 1.

def short(text: str, limit: int = 170) -> str:
    return text if len(text) <= limit else text[:limit] + "..."


async def raw_handshake_demo():
    print("######## PART 2: The same handshake, by hand ########\n")
    proc = await asyncio.create_subprocess_exec(
        sys.executable, str(SERVER), "--serve",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,     # server logs go to stderr; hide them here
    )
    assert proc.stdin and proc.stdout

    async def send(message: dict):
        line = json.dumps(message)
        print(f"    --> {short(line)}")
        proc.stdin.write((line + "\n").encode())      # one JSON message per line
        await proc.stdin.drain()

    async def receive(expected_id: int) -> dict:
        while True:
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=15)
            message = json.loads(line)
            print(f"    <-- {short(line.decode().strip())}")
            if message.get("id") == expected_id:        # skip any server notifications
                return message

    try:
        print("  --- 1. initialize (client says: my version + what I support) ---")
        await send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "learn-mcp-raw-stdio", "version": "0.1.0"},
        }})
        init = await receive(1)
        result = init["result"]
        print(f"\n      server name     : {result['serverInfo']['name']}")
        print(f"      agreed version  : {result['protocolVersion']}")
        print(f"      server supports : {sorted(result['capabilities'])}\n")

        print("  --- 2. notifications/initialized (client says: I'm ready) ---")
        await send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        print("        (no reply -- notifications never get one; no 'id' field)\n")

        print("  --- 3. tools/list ---")
        await send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tools = (await receive(2))["result"]["tools"]
        print(f"\n      tools: {[t['name'] for t in tools]}\n")

        print("  --- 4. tools/call greet ---")
        await send({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                    "params": {"name": "greet", "arguments": {"name": "Shubham"}}})
        call = (await receive(3))["result"]
        print(f"\n      text: {call['content'][0]['text']}\n")
    finally:
        proc.stdin.close()          # EOF on stdin tells a stdio server to exit
        await proc.wait()

    print("  Every request has an 'id'; its response carries the SAME id -- that's")
    print("  how the client matches answers to questions. Notifications have no id")
    print("  and get no answer.")


async def main():
    await sdk_demo()
    await raw_handshake_demo()


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================
# EXERCISES:
#
# 1. Try calling a tool with wrong parameter types -- what error
#    do you get? How does MCP validate inputs?
# 2. Call a tool that doesn't exist -- what's the error?
# 3. Print the raw tool.inputSchema to see the JSON Schema
#    that FastMCP auto-generated from your type hints
# 4. In PART 2, send tools/list with id 99 instead of 2. Which id
#    comes back in the response?
# 5. In PART 2, change "protocolVersion" to "1999-01-01". What
#    version does the server answer with?
# ============================================================
