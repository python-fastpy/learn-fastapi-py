"""Lesson 01 -- Creating a Client, and its connection lifecycle
================================================================

A Client is how your code talks to an MCP server -- any server, not just a
FastMCP one. `Client(...)` figures out HOW to connect from what you hand it:

    Client(mcp)                  a FastMCP server object -> in-memory, no network
    Client("https://.../mcp")    a URL string             -> HTTP
    Client(Path("server.py"))    a script path            -> stdio (subprocess)

(Lesson 02 covers all of these, plus multi-server configs, in depth.)

A client only works INSIDE an `async with` block. Connecting runs a
handshake with the server, after which a few properties are filled in:

    client.server_info          the server's name + version
    client.instructions         what the server told you it's for
    client.server_capabilities  which features it supports (tools, etc.)
    client.protocol_version     the MCP protocol version that was negotiated

Run:  uv run python 01_client_basics.py
"""

import asyncio

from fastmcp import Client
from target_server import mcp


async def main():
    async with Client(mcp) as client:
        # 1. identity, filled in by the connection handshake
        print("server name  :", client.server_info.name)
        print("instructions :", client.instructions)
        print("protocol     :", client.protocol_version)
        print("has tools?   :", client.server_capabilities.tools is not None)

        # 2. the client is connected until the `async with` block ends
        print("\nconnected    :", client.is_connected())

        # 3. a first real call, just to prove the connection works
        result = await client.call_tool("greet", {"name": "Ada"})
        print("greet('Ada') ->", result.data)

    # outside the block, the connection is closed
    print("\nstill connected? ->", client.is_connected())


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Try calling client.call_tool(...) OUTSIDE the `async with` block --
#    read the error.
# 2. Print client.server_capabilities in full -- what else does it list
#    besides tools?
# 3. Pass mode="legacy" to Client() and call `await client.ping()` --
#    it only works on this older, session-based handshake.
