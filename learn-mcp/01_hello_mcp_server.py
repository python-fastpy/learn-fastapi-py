"""Lesson 01 -- MCP Server: Registering Tools + Validating Their Input
=====================================================================

WHY THIS MATTERS:
  Every skill in the Reuters AI Assistant (story-drafting, urgent-drafting,
  text-archive) is an MCP server. Before you can build any of them, you
  need to know two things:
    1. how to create a server and register tools on it (two styles)
    2. what to do when an LLM agent calls your tool with garbage input --
       empty strings, unknown options, out-of-range numbers

WHAT YOU'LL LEARN:
  1. Create an MCP server with FastMCP (like FastAPI, but for tools)
  2. Register a tool with the @mcp.tool DECORATOR (quick and easy)
  3. Register a tool IMPERATIVELY with mcp.tool(name, meta)(fn) (production pattern)
  4. Reject genuinely wrong input with ToolError (the LLM sees the message and can retry)
  5. Clamp edge values silently instead of rejecting (times=99 -> 5)
  6. Test everything with an in-process client, including errors (raise_on_error=False)

Concepts:
  - FastMCP: the server framework for building MCP-compliant tools
  - Annotated[type, Field(description="...")]: parameter descriptions the LLM reads
  - meta dict: display_name, response_mode, hidden (controls the UI, not the LLM)
  - ToolError: a graceful error RESULT (isError=True), not a crash
  - Clamping: fix "close enough" input instead of rejecting it
  - Client(server): in-process client -- no subprocess or HTTP needed for testing

Flow:
  +--------+     +--------------------+     +------------------------------+
  | Client | --> | MCP Server         | --> | greet(name)                  |  decorator
  +--------+     | "learn-mcp"        |     +------------------------------+
       ^         | Tools:             |     | greet_styled(name, style,    |  imperative
       |         |  - greet           |     |              times)          |
       |         |  - greet_styled    |     |   name empty?  -> ToolError  |
       |         +--------------------+     |   bad style?   -> ToolError  |
       |                                    |   times=99?    -> clamp to 5 |
       +------ result, or isError=True -----+------------------------------+

  Maps to:
    story-drafting/src/main.py          (imperative registration + meta)
    text-archive/src/tools/archive_search.py (ToolError usage)
    story-drafting/src/tools/search_rics.py  (clamping: limit = min(max(limit, 1), 20))

PREREQUISITES: None -- this is the starting point.

Run:  uv run python 01_hello_mcp_server.py            (in-process demo)
      uv run python 01_hello_mcp_server.py --serve    (real stdio server; lesson 02 connects to it)

EXPECTED OUTPUT:
  === Registered Tools ===
    - greet: Generate a personalized greeting.
        param 'name': The person's name to greet
    - greet_styled: Generate a greeting in a chosen style, with input validation.
        param 'name': The person's name to greet
        param 'style': formal, casual or enthusiastic
        param 'times': How many times to repeat the greeting (1-5)

  === 1. greet (decorator style) ===
    greet('Shubham')                   -> {'greeting': 'Hello, Shubham! Welcome to MCP.', ...}

  === 2. greet_styled (imperative style + validation) ===
    valid input:
      greet_styled('Shubham')          -> Hey Shubham! What's up?
      greet_styled('Shubham', formal)  -> Good day, Shubham. It is a pleasure to meet you.
    clamped (fixed silently):
      times=99  -> times_used=5
      times=-5  -> times_used=1
    rejected (ToolError):
      name='   '     -> isError=True, msg=name cannot be empty
      style='pirate' -> isError=True, msg=Invalid style 'pirate'. Must be one of: casual, enthusiastic, formal
"""

import asyncio
import sys
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client
from fastmcp.exceptions import ToolError


mcp = FastMCP(name="learn-mcp")


# =============================================================================
# STYLE 1: DECORATOR REGISTRATION
# =============================================================================
# Simple and clean -- good for small servers or learning.
# The decorator reads the function signature, type hints and docstring to
# build the MCP tool schema automatically. The docstring becomes the tool
# description and each Field(description=...) becomes a parameter description
# -- that's all the LLM knows about your tool.

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
# STYLE 2: IMPERATIVE REGISTRATION -- also our input-validation example
# =============================================================================
# This is what your production codebase uses (story-drafting/src/main.py).
# Advantages:
#   - Tool function is a plain async def -- no framework coupling
#   - Registration with name/meta happens separately (usually in main.py)
#   - Easier to test the function independently
#   - meta dict controls UI behavior (display_name, response_mode, hidden)
#
# An LLM agent may pass anything, so the function validates its input with
# the two standard strategies:
#   REJECT (ToolError) -- the input is genuinely wrong (empty name, unknown
#       style). The client gets isError=True plus your message; an LLM reads
#       the message and can retry with corrected input. Say how to fix it.
#   CLAMP -- the input is "close enough" (times=99). Fix it silently and
#       report what was used. Better UX than an error for edge values.

VALID_STYLES = {"formal", "casual", "enthusiastic"}


async def greet_styled(
    name: Annotated[str, Field(description="The person's name to greet")],
    style: Annotated[str, Field(description="formal, casual or enthusiastic")] = "casual",
    times: Annotated[int, Field(description="How many times to repeat the greeting (1-5)")] = 1,
) -> dict:
    """Generate a greeting in a chosen style, with input validation."""
    # REJECT: genuinely wrong input
    if not name.strip():
        raise ToolError("name cannot be empty")
    if style not in VALID_STYLES:
        raise ToolError(
            f"Invalid style '{style}'. Must be one of: {', '.join(sorted(VALID_STYLES))}"
        )

    # CLAMP: close-enough input -- same pattern as search_rics.py
    times = min(max(times, 1), 5)

    greetings = {
        "formal": f"Good day, {name}. It is a pleasure to meet you.",
        "casual": f"Hey {name}! What's up?",
        "enthusiastic": f"HELLO {name.upper()}!!! SO GREAT TO SEE YOU!!!",
    }
    return {"greeting": " ".join([greetings[style]] * times), "style": style, "times_used": times}


mcp.tool(
    name="greet_styled",
    meta={
        "display_name": "Styled Greeting",   # what the user sees in the skill list
        "response_mode": "direct",           # tool runs to completion (no interrupt)
    },
)(greet_styled)


# =============================================================================
# CLIENT -- test both tools in-process
# =============================================================================

async def main():
    async with Client(mcp) as client:

        # Discover all registered tools -- this is what an LLM client sees
        tools = await client.list_tools()
        print("=== Registered Tools ===")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
            for param, schema in tool.inputSchema.get("properties", {}).items():
                print(f"      param '{param}': {schema.get('description', 'no description')}")
        print()

        # -- 1. The decorator-registered tool ----------------------------------
        print("=== 1. greet (decorator style) ===")
        r = await client.call_tool("greet", {"name": "Shubham"})
        print(f"  greet('Shubham')                   -> {r.data}")
        print()

        # -- 2. The imperative tool, with validation ---------------------------
        print("=== 2. greet_styled (imperative style + validation) ===")

        print("  valid input:")
        r = await client.call_tool("greet_styled", {"name": "Shubham"})
        print(f"    greet_styled('Shubham')          -> {r.data['greeting']}")
        r = await client.call_tool("greet_styled", {"name": "Shubham", "style": "formal"})
        print(f"    greet_styled('Shubham', formal)  -> {r.data['greeting']}")

        print("  clamped (fixed silently):")
        for times in (99, -5):
            r = await client.call_tool("greet_styled", {"name": "Shubham", "times": times})
            print(f"    times={times:<3} -> times_used={r.data['times_used']}")

        # raise_on_error=False: inspect the error instead of raising in the client
        print("  rejected (ToolError):")
        r = await client.call_tool("greet_styled", {"name": "   "}, raise_on_error=False)
        print(f"    name='   '     -> isError={r.is_error}, msg={r.content[0].text}")
        r = await client.call_tool("greet_styled", {"name": "Shubham", "style": "pirate"},
                                   raise_on_error=False)
        print(f"    style='pirate' -> isError={r.is_error}, msg={r.content[0].text}")


if __name__ == "__main__":
    # Two ways to run this file:
    #   uv run python 01_hello_mcp_server.py           -> the in-process demo above
    #   uv run python 01_hello_mcp_server.py --serve   -> a real MCP server on stdio,
    #       waiting for a client to connect (lesson 02 launches it this way)
    if "--serve" in sys.argv:
        mcp.run(show_banner=False)          # stdio transport; stdout carries JSON-RPC only
    else:
        asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    #
    # REGISTRATION -- two styles, same result:
    #   @mcp.tool                     -> one-liner, the function IS the tool.
    #                                    Good for small servers and learning.
    #   mcp.tool(name, meta)(fn)      -> function stays framework-free; name +
    #                                    meta live in one place (main.py). The
    #                                    production pattern (story-drafting,
    #                                    urgent-drafting).
    #
    # The meta dict controls UI behavior (the LLM doesn't use it):
    #   display_name  -> what the user sees in the skill list
    #   response_mode -> "direct" (tool runs to completion)
    #   hidden        -> True for internal tools (validate_ric, search_rics)
    #
    # VALIDATION -- two strategies for bad input:
    #   ToolError -> genuinely wrong (empty name, invalid enum). The client sees
    #                isError=True and the message; an LLM can retry correctly.
    #                Used in archive_search.py for missing queries.
    #   Clamping  -> "close enough" (times=99 becomes 5). Better UX than an error.
    #                Used in search_rics.py for limit values.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Move greet() to imperative style and greet_styled() to decorator style
    # 2. Add meta={"hidden": True} to greet_styled and verify it still works
    #    when called by name (hidden just affects UI display)
    # 3. Try calling a tool that doesn't exist and observe the error
    # 4. Add a ToolError for name length > 50 characters
    # 5. Make an invalid style fall back to "casual" (clamp) instead of raising
    #    ToolError -- when would you pick each approach?
