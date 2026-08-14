"""Lesson 02 -- Validation & Error Handling
============================================

WHY THIS MATTERS:
  When an LLM agent calls your tool, it might pass garbage — empty strings,
  negative numbers, invalid date formats. You need to decide: crash loudly
  (ToolError) or fix it silently (clamping). The LLM sees ToolError messages
  and can retry with corrected input. This lesson teaches both strategies.

WHAT YOU'LL LEARN:
  1. Raise ToolError for genuinely wrong inputs (LLM gets the error, can retry)
  2. Clamp edge values silently (e.g., limit=200 becomes limit=50)
  3. Inspect errors safely on the client side with raise_on_error=False

Concepts:
  - ToolError: graceful error responses (not exceptions that crash)
  - Input clamping: sanitize values instead of rejecting
  - isError flag on the client side
  - raise_on_error=False for safe error inspection

Flow:
  +--------+     +------------+     +----------+
  | Client | --> | MCP Server | --> | Tool     |
  +--------+     +------------+     +----------+
       |                                 |
       |  call_tool("greet", {name})     |
       |                                 |
       |       name empty?               |
       |       YES -> ToolError -------> isError=True
       |       NO  -> result ----------> isError=False
       +----------------------------------

  Maps to:
    text-archive/src/tools/archive_search.py (ToolError usage)
    story-drafting/src/tools/search_rics.py (input clamping pattern)

PREREQUISITES: Lesson 01 (server + tool basics)

Run:  uv run python 02_input_validation.py
"""

import asyncio
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client
from fastmcp.exceptions import ToolError


mcp = FastMCP(name="learn-mcp-validation")


# -- ToolError: reject genuinely wrong inputs ----------------------------------

@mcp.tool
async def greet(
    name: Annotated[str, Field(description="The person's name to greet")],
    style: Annotated[str, Field(description="Style: formal, casual, enthusiastic")] = "casual",
) -> dict:
    """Generate a personalized greeting with validation."""
    if not name.strip():
        raise ToolError("name cannot be empty")

    valid_styles = {"formal", "casual", "enthusiastic"}
    if style not in valid_styles:
        raise ToolError(
            f"Invalid style '{style}'. Must be one of: {', '.join(sorted(valid_styles))}"
        )

    greetings = {
        "formal": f"Good day, {name}. It is a pleasure to meet you.",
        "casual": f"Hey {name}! What's up?",
        "enthusiastic": f"HELLO {name.upper()}!!! SO GREAT TO SEE YOU!!!",
    }
    return {"greeting": greetings[style], "style": style}


# -- Input clamping: sanitize instead of rejecting -----------------------------
# Instead of rejecting bad inputs, clamp them to valid range.
# This is what search_rics.py does: limit = min(max(limit, 1), 20)

@mcp.tool
async def farewell(
    name: Annotated[str, Field(description="The person's name to say goodbye to")],
    wave_count: Annotated[int, Field(default=1, description="How many waves (1-5)")] = 1,
) -> dict:
    """Generate a farewell with clamped wave count."""
    if not name.strip():
        raise ToolError("name cannot be empty")

    # Clamp instead of rejecting -- better UX than erroring on edge values
    wave_count = min(max(wave_count, 1), 5)
    waves = " ".join(["👋"] * wave_count)

    return {
        "farewell": f"Goodbye, {name}! {waves}",
        "wave_count_used": wave_count,
    }


async def main():
    async with Client(mcp) as client:

        # -- Successful calls --------------------------------------------------
        print("=== Successful Calls ===\n")

        r1 = await client.call_tool("greet", {"name": "Shubham"})
        print(f"  greet('Shubham')           -> {r1}")

        r2 = await client.call_tool("greet", {"name": "Shubham", "style": "formal"})
        print(f"  greet('Shubham', formal)   -> {r2}")

        r3 = await client.call_tool("farewell", {"name": "Shubham", "wave_count": 3})
        print(f"  farewell('Shubham', 3)     -> {r3}")

        # -- Input clamping ----------------------------------------------------
        print("\n=== Input Clamping ===\n")

        r4 = await client.call_tool("farewell", {"name": "Shubham", "wave_count": 99})
        print(f"  farewell(wave_count=99)  -> clamped to {r4.data}")

        r5 = await client.call_tool("farewell", {"name": "Shubham", "wave_count": -5})
        print(f"  farewell(wave_count=-5)  -> clamped to {r5.data}")

        # -- Error cases (ToolError) -------------------------------------------
        print("\n=== Error Cases (ToolError) ===\n")

        # Empty name -> ToolError
        r6 = await client.call_tool("greet", {"name": "   "}, raise_on_error=False)
        print(f"  greet('')              -> isError={r6.is_error}, msg={r6.content[0].text}")

        # Invalid style -> ToolError
        r7 = await client.call_tool("greet", {
            "name": "Shubham", "style": "pirate"
        }, raise_on_error=False)
        print(f"  greet(style=pirate)    -> isError={r7.is_error}, msg={r7.content[0].text}")

        # Empty name on farewell -> ToolError
        r8 = await client.call_tool("farewell", {"name": ""}, raise_on_error=False)
        print(f"  farewell('')           -> isError={r8.is_error}, msg={r8.content[0].text}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Two strategies for invalid inputs:
    #
    # 1. ToolError -- for inputs that are genuinely wrong (empty name,
    #    invalid enum values). The client sees isError=True and can
    #    handle gracefully.
    #
    # 2. Clamping -- for inputs that are "close enough" (wave_count=99
    #    becomes 5). Better UX than rejecting outright.
    #
    # Your production code uses both:
    #   - ToolError in archive_search.py for missing queries
    #   - Clamping in search_rics.py for limit values
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a ToolError for name length > 50 characters
    # 2. Add clamping to the style param (default to "casual" if invalid)
    #    instead of raising ToolError -- when would you pick each approach?
