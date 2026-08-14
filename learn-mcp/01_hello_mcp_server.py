"""Lesson 01 -- MCP Server: Decorator vs Imperative Registration
================================================================

WHY THIS MATTERS:
  Every skill in the Reuters AI Assistant (story-drafting, urgent-drafting,
  text-archive) is an MCP server. Before you can build any of them, you
  need to know how to create a server and register tools on it. This lesson
  teaches both ways to do that.

WHAT YOU'LL LEARN:
  1. Create an MCP server with FastMCP (like FastAPI, but for tools)
  2. Register tools using @mcp.tool decorator (quick and easy)
  3. Register tools using mcp.tool()(fn) imperative style (production pattern)
  4. Test tools with an in-process client (no HTTP needed)

Concepts:
  - FastMCP: the server framework for building MCP-compliant tools
  - Two registration styles:
      1. @mcp.tool          -- decorator (simple, good for small servers)
      2. mcp.tool()(fn)     -- imperative (production pattern, decoupled)
  - Annotated[type, Field(description="...")]: parameter metadata
  - meta dict: display_name, response_mode, hidden
  - Client(server): in-process client -- no HTTP needed for testing

Flow:
  +--------+     +------------------+     +------------------+
  | Client | --> | MCP Server       | --> | Tool Functions   |
  +--------+     | "learn-mcp"      |     |                  |
                 +------------------+     | greet()          |
                 | Tools:           |     | farewell()       |
                 |  - greet         |     +------------------+
                 |  - farewell      |
                 +------------------+

  Your production code uses IMPERATIVE registration exclusively:
    mcp.tool(name="generate_spot_story", meta={...})(generate_spot_story)
  This keeps tool logic separate from server wiring.

PREREQUISITES: None -- this is the starting point.

Run:  uv run python 01_hello_mcp_server.py
"""

import asyncio
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client


mcp = FastMCP(name="learn-mcp")


# =============================================================================
# STYLE 1: DECORATOR REGISTRATION
# =============================================================================
# Simple and clean -- good for small servers or learning.
# The decorator extracts the function signature and docstring
# to build the MCP tool schema automatically.

@mcp.tool
async def greet(
    name: Annotated[str, Field(description="The person's name to greet")],
) -> dict:
    """Generate a personalized greeting."""
    return {
        "greeting": f"Hello, {name}! Welcome to MCP.",
        "server": "learn-mcp",
    }


# =============================================================================
# STYLE 2: IMPERATIVE REGISTRATION
# =============================================================================
# This is what your production codebase uses (story-drafting/src/main.py).
# Advantages:
#   - Tool function is a plain async def -- no framework coupling
#   - Registration with name/meta happens separately (usually in main.py)
#   - Easier to test the function independently
#   - meta dict controls UI behavior (display_name, response_mode, hidden)

async def farewell(
    name: Annotated[str, Field(description="The person's name to say goodbye to")],
) -> dict:
    """Generate a personalized farewell message."""
    return {
        "farewell": f"Goodbye, {name}! See you next time.",
        "server": "learn-mcp",
    }


mcp.tool(
    name="farewell",
    meta={
        "display_name": "Say Farewell",
        "response_mode": "direct",
    },
)(farewell)


# =============================================================================
# CLIENT -- test both styles in-process
# =============================================================================

async def main():
    async with Client(mcp) as client:

        # Discover all registered tools
        tools = await client.list_tools()
        print("=== Registered Tools ===")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
            if tool.inputSchema.get("properties"):
                for param, schema in tool.inputSchema["properties"].items():
                    print(f"      param '{param}': {schema.get('description', 'no description')}")
        print()

        # Call the decorator-registered tool
        print("=== greet (decorator style) ===")
        r1 = await client.call_tool("greet", {"name": "Shubham"})
        print(f"  {r1}")

        # Call the imperative-registered tool
        print("\n=== farewell (imperative style) ===")
        r2 = await client.call_tool("farewell", {"name": "Shubham"})
        print(f"  {r2}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    #
    # DECORATOR (@mcp.tool):
    #   - One-liner registration, function IS the tool
    #   - Good for small servers, learning, quick prototypes
    #
    # IMPERATIVE (mcp.tool(name, meta)(fn)):
    #   - Function stays framework-free (plain async def)
    #   - Registration + meta lives in one place (main.py)
    #   - Easier to unit-test the function directly
    #   - Production pattern used in story-drafting, urgent-drafting
    #
    # The meta dict controls UI behavior:
    #   display_name  -> what the user sees in the skill list
    #   response_mode -> "direct" (tool runs to completion)
    #   hidden        -> True for internal tools (validate_ric, search_rics)
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Move greet() to imperative style and farewell() to decorator style
    # 2. Add meta={"hidden": True} to farewell and verify it still works
    #    when called by name (hidden just affects UI display)
    # 3. Try calling a tool that doesn't exist and observe the error
