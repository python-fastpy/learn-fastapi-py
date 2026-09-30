"""Lesson 02 -- Running the server: transports + custom HTTP routes
===================================================================

A transport is HOW the client and server talk to each other:

    mcp.run()                   -> STDIO (default): the client launches your
                                   script and talks over stdin/stdout
    mcp.run(transport="http")   -> HTTP: clients connect to a running server
    mcp.run(transport="sse")    -> SSE: an older web transport, deprecated

Under HTTP you can also add plain web routes (like /health) next to the MCP
endpoint -- see @mcp.custom_route below.

Important: the `if __name__ == "__main__"` guard is required, not decoration.
A STDIO client launches your file as a subprocess and imports it first, so
the module must be safely importable without immediately starting a server.

Run:  uv run python 02_running_and_routes.py         (in-process demo)
      uv run python 02_running_and_routes.py --stdio  (real stdio server)
      uv run python 02_running_and_routes.py --http   (real http server :8000)
"""

import asyncio
import sys

from fastmcp import Client, FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

mcp = FastMCP("GreetingService")


@mcp.tool
def greet(name: str) -> str:
    """Greets someone by name."""
    return f"Hello, {name}!"


# ----------------------------------------------------------- custom routes
# A plain web endpoint, good for health checks or small webhooks. For a real
# web app, mount the MCP server inside FastAPI/Starlette instead.
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


async def demo():
    """Show the server works before choosing a transport."""
    async with Client(mcp) as client:
        print("tools:", [t.name for t in await client.list_tools()])
        print("greet ->", (await client.call_tool("greet", {"name": "Shubham"})).data)

    print(
        "\ntransports:\n"
        "  mcp.run()                                      # stdio  (default)\n"
        '  mcp.run(transport="http", host="127.0.0.1", port=9000)\n'
        '  mcp.run(transport="sse")                       # deprecated\n'
        "\ncustom route: GET /health -> 'OK'  (HTTP transport only)\n"
        "\nthe FastMCP CLI is the other way to launch:  fastmcp run 02_running_and_routes.py\n"
    )


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        mcp.run()                       # blocks, speaks MCP over stdin/stdout
    elif "--http" in sys.argv:
        # MCP endpoint:  http://127.0.0.1:8000/mcp
        # health check:  http://127.0.0.1:8000/health
        mcp.run(transport="http", host="127.0.0.1", port=8000)
    else:
        asyncio.run(demo())

# Exercises:
# 1. Start --http, then `curl http://127.0.0.1:8000/health`.
# 2. Add a POST /webhook custom route that reads the JSON body.
# 3. Run with --stdio and notice nothing prints: stdout is the protocol channel,
#    so a stray print() would corrupt it. (Log to stderr instead.)
