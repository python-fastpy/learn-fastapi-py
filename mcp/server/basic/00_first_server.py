"""Your first MCP server -- create it, run it, connect a real client
=========================================================================

A FastMCP server has ONE identity and THREE kinds of things inside it:

    @mcp.tool       DO something     (the LLM calls it)        -> 01_tools.py
    @mcp.resource   READ something   (data at a URI)           -> 02_resources.py
    @mcp.prompt     REUSE a template (the user picks it)       -> 03_prompts.py

A TRANSPORT is how the client and server talk:

    STDIO (default)                          HTTP
    ┌──────────┐ launches  ┌──────────┐      ┌──────────┐   POST /mcp   ┌──────────┐
    │  client  │──────────►│  server  │      │  client  │──────────────►│  server  │
    │ (Claude) │◄─stdin/──►│ (this    │      │          │◄──────────────│ (already │
    └──────────┘  stdout   │  file)   │      └──────────┘   responses   │ running) │
                           └──────────┘                                 └──────────┘
    local, one client, zero setup            remote/shared, many clients, needs a URL

    (transport="sse" also exists -- an older web transport, deprecated; use http.)

Level: BASIC          (run every command from mcp/server)
Run:  uv run python basic/00_first_server.py           in-process demo (no transport)
      uv run python basic/00_first_server.py --stdio   real stdio server (prints nothing!)
      uv run python basic/00_first_server.py --http    real HTTP server on :8000
Test in Inspector:  uv run fastmcp dev inspector basic/00_first_server.py
Connect to a client: see "Connect a real client" in README.md
"""

import asyncio
import sys

from fastmcp import Client, FastMCP
from starlette.requests import Request
from starlette.responses import PlainTextResponse

# ----------------------------------------------------------- 1. the server
# `name` is the only required field. `instructions` is what the client shows
# the LLM to explain what this server is for -- worth writing well.
mcp = FastMCP(
    name="GreetingService",
    instructions="Greets people by name. Call greet() for hello.",
)


# ---------------------------------------------- 2. one of each component
@mcp.tool
def greet(name: str) -> str:
    """Greets someone by name."""          # the docstring is what the LLM reads
    return f"Hello, {name}!"


@mcp.resource("data://greeting")
def greeting_config() -> dict:
    """The greeting template."""
    return {"template": "Hello, {name}!"}


@mcp.prompt
def ask_greeting(name: str) -> str:
    """Asks the LLM to write a greeting."""
    return f"Write a warm, one-line greeting for {name}."


# ----------------------------------------- 3. a plain web route (HTTP only)
# Handy for health checks next to the MCP endpoint. Ignored under stdio.
@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


# --------------------------------------------------- 4. in-process testing
async def demo():
    # Client(mcp) talks to the server in memory -- no transport, no network.
    # Every other chapter uses this style to test itself.
    async with Client(mcp) as client:
        print("server      :", client.server_info.name)
        print("instructions:", client.instructions)
        print("tools       :", [t.name for t in await client.list_tools()])
        print("resources   :", [str(r.uri) for r in await client.list_resources()])
        print("prompts     :", [p.name for p in await client.list_prompts()])

        print("\ngreet('Ada')         ->", (await client.call_tool("greet", {"name": "Ada"})).data)
        print("read data://greeting ->", (await client.read_resource("data://greeting"))[0].text)
        p = await client.get_prompt("ask_greeting", {"name": "Ada"})
        print("ask_greeting('Ada')  ->", p.messages[0].content.text)


# ------------------------------------------------------ 5. picking a transport
# The __main__ guard is REQUIRED: tools like `fastmcp run` and the Inspector
# import this file to find `mcp`, so importing must not start a server.
if __name__ == "__main__":
    if "--stdio" in sys.argv:
        # stdout IS the protocol channel -- a stray print() here would corrupt it.
        mcp.run()
    elif "--http" in sys.argv:
        # MCP endpoint: http://127.0.0.1:8000/mcp    health: http://127.0.0.1:8000/health
        mcp.run(transport="http", host="127.0.0.1", port=8000)
    else:
        asyncio.run(demo())
