"""Client basics -- connecting, and what you learn from the handshake
==========================================================================

A Client is how your code talks to ANY MCP server. Client(...) guesses the
transport from what you hand it:

    Client(mcp)                    a server OBJECT   -> in-memory (tests; no network)
    Client("greet_server.py")      a .py path        -> stdio     (01_stdio_client.py)
    Client("http://host/mcp")      a URL             -> HTTP      (02_http_client.py)
    Client({"mcpServers": {...}})  a config dict     -> several servers at once (01)

SECURITY: that guessing trusts its input -- a "user-supplied path" gets RUN as
a subprocess. If the path/URL comes from outside, build the transport yourself
(PythonStdioTransport / StreamableHttpTransport) so you control what happens.
(SSETransport also exists, for old servers only -- prefer HTTP.)

A client works only INSIDE `async with`. Connecting does a handshake, which fills in:

    client.server_info          server name + version
    client.instructions         what the server says it's for
    client.protocol_version     the negotiated MCP protocol version
    client.server_capabilities  which features it supports

Level: BASIC
Run:  uv run python basic/00_client_basics.py      (from mcp/client)
"""

import asyncio

from fastmcp import Client
from greet_server import mcp


async def main():
    async with Client(mcp) as client:          # in-memory: the server object itself
        print("server name  :", client.server_info.name)
        print("instructions :", client.instructions)
        print("protocol     :", client.protocol_version)
        print("has tools?   :", client.server_capabilities.tools is not None)
        print("connected    :", client.is_connected())
        print("greet('Ada') ->", (await client.call_tool("greet", {"name": "Ada"})).data)

    print("after block  : connected =", client.is_connected())   # closed on exit


if __name__ == "__main__":
    asyncio.run(main())
