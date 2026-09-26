"""Lesson 01 -- MCP Server: one greet tool, two ways to register it
===================================================================

                     async def greet(name)
                             │
           ┌─────────────────┴──────────────────┐
           ▼                                    ▼
   @mcp.tool  (decorator)             mcp.tool(name="say_hello", meta={...})(greet)
   -> tool "greet"                    (imperative -- the production pattern)
                                      -> tool "say_hello"

Run:  uv run python 01_hello_mcp_server.py            (demo)
      uv run python 01_hello_mcp_server.py --serve    (real stdio server; lesson 02 explains stdio)
      uv run python 01_hello_mcp_server.py --http 8765  (real HTTP server at http://127.0.0.1:8765/mcp)

Maps to: story-drafting/src/main.py (imperative registration + meta)
"""

import asyncio
import sys
from fastmcp import FastMCP, Client
from fastmcp.exceptions import ToolError

mcp = FastMCP(name="learn-mcp")


# STYLE 1: decorator -- the function IS the tool.
# The docstring becomes the tool description the LLM reads.
@mcp.tool
async def greet(name: str) -> dict:
    """Greet someone by name."""
    if not name.strip():
        raise ToolError("name cannot be empty")   # the LLM sees this and can retry
    return {"greeting": f"Hello, {name}!"}


# STYLE 2: imperative -- register the same function separately, with a name
# and meta. meta is for the UI, not the LLM (display_name, response_mode, hidden).
mcp.tool(name="say_hello", meta={"display_name": "Say Hello"})(greet)


async def main():
    async with Client(mcp) as client:                 # in-process client, no subprocess
        print("Tools:", [t.name for t in await client.list_tools()])

        for tool_name in ("greet", "say_hello"):
            r = await client.call_tool(tool_name, {"name": "Shubham"})
            print(f"{tool_name:<10} -> {r.data}")

        r = await client.call_tool("greet", {"name": " "}, raise_on_error=False)
        print(f"empty name -> isError={r.is_error}, {r.content[0].text}")


if __name__ == "__main__":
    if "--serve" in sys.argv:
        mcp.run(show_banner=False)                    # stdio server (see lesson 02)
    elif "--http" in sys.argv:                        # HTTP server: --http 8765
        port = int(sys.argv[sys.argv.index("--http") + 1])
        mcp.run(transport="http", host="127.0.0.1", port=port, show_banner=False)
    else:
        asyncio.run(main())

# Exercises:
# 1. Remove @mcp.tool so greet is registered only imperatively.
# 2. Add meta={"hidden": True} to say_hello -- does it still work by name?
# 3. Call a tool that doesn't exist. What error do you get?
