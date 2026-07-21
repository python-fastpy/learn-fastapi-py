"""Lesson 03 -- Validation & Error Handling
============================================
Concepts:
  - Pydantic Field for input constraints (min, max, description)
  - ToolError: graceful error responses (not exceptions that crash)
  - Input clamping: sanitize values instead of rejecting
  - isError flag on the client side

Flow:
  +--------+     +------------+     +----------+
  | Client | --> | MCP Server | --> | Tool     |
  +--------+     +------------+     +----------+
       |                                 |
       |  call_tool("divide", {a, b})    |
       |                                 |
       |       b == 0?                   |
       |       YES -> ToolError -------> isError=True
       |       NO  -> result ----------> isError=False
       +----------------------------------

  Maps to:
    text-archive/src/tools/archive_search.py (ToolError usage)
    story-drafting/src/tools/search_rics.py (input clamping pattern)

No LLM needed -- demonstrates validation and error patterns.

Run:  uv run python 03_input_validation.py
"""

import asyncio
from typing import Annotated, Optional
from pydantic import Field
from fastmcp import FastMCP, Client
from fastmcp.exceptions import ToolError


mcp = FastMCP(name="calculator")


# -- Tool with ToolError for invalid inputs ------------------------------------

@mcp.tool
async def divide(
    a: Annotated[float, Field(description="Numerator")],
    b: Annotated[float, Field(description="Denominator (must not be zero)")],
) -> dict:
    """Divide two numbers. Raises ToolError on division by zero."""
    if b == 0:
        raise ToolError("Division by zero is not allowed")
    return {"result": a / b, "expression": f"{a} / {b}"}


# -- Tool with input clamping (production pattern) -----------------------------
# Instead of rejecting bad inputs, clamp them to valid range.
# This is what search_rics.py does: limit = min(max(limit, 1), 20)

@mcp.tool
async def search_data(
    query: Annotated[str, Field(description="Search query")],
    limit: Annotated[int, Field(default=10, description="Results to return (1-50)")] = 10,
    offset: Annotated[int, Field(default=0, description="Pagination offset")] = 0,
) -> dict:
    """Search with clamped pagination parameters."""
    # Clamp instead of rejecting
    limit = min(max(limit, 1), 50)
    offset = max(offset, 0)

    results = [
        {"id": offset + i + 1, "title": f"Result for '{query}' #{offset + i + 1}"}
        for i in range(limit)
    ]
    return {
        "query": query,
        "limit_used": limit,
        "offset_used": offset,
        "count": len(results),
        "results": results,
    }


# -- Tool with multiple validation rules --------------------------------------

@mcp.tool
async def create_alert(
    headline: Annotated[str, Field(description="Alert headline text")],
    priority: Annotated[str, Field(description="Priority: low, medium, high, urgent")] = "medium",
    category: Annotated[Optional[str], Field(default=None, description="Optional category")] = None,
) -> dict:
    """Create a news alert with validation."""
    if not headline.strip():
        raise ToolError("headline cannot be empty")

    valid_priorities = {"low", "medium", "high", "urgent"}
    if priority not in valid_priorities:
        raise ToolError(
            f"Invalid priority '{priority}'. Must be one of: {', '.join(sorted(valid_priorities))}"
        )

    if len(headline) > 200:
        raise ToolError(f"headline too long ({len(headline)} chars). Max is 200.")

    return {
        "status": "created",
        "headline": headline.strip(),
        "priority": priority,
        "category": category,
    }


async def main():
    async with Client(mcp) as client:
        # -- Successful calls --------------------------------------------------
        print("=== Successful Calls ===\n")

        r1 = await client.call_tool("divide", {"a": 10, "b": 3})
        print(f"  divide(10, 3) = {r1}")

        r2 = await client.call_tool("search_data", {"query": "oil", "limit": 3})
        print(f"  search_data('oil', limit=3) -> {r2.data}")

        r3 = await client.call_tool("create_alert", {
            "headline": "OPEC+ extends cuts",
            "priority": "high",
        })
        print(f"  create_alert -> {r3.data}")

        # -- Error cases -------------------------------------------------------
        print("\n=== Error Cases ===\n")

        # Division by zero -> ToolError
        # raise_on_error=False returns the error as a result instead of raising
        r4 = await client.call_tool("divide", {"a": 10, "b": 0}, raise_on_error=False)
        print(f"  divide(10, 0) -> isError={r4.is_error}, text={r4.content[0].text}")

        # Empty headline -> ToolError
        r5 = await client.call_tool("create_alert", {
            "headline": "   ",
            "priority": "high",
        }, raise_on_error=False)
        print(f"  create_alert('') -> isError={r5.is_error}, text={r5.content[0].text}")

        # Invalid priority -> ToolError
        r6 = await client.call_tool("create_alert", {
            "headline": "Test",
            "priority": "CRITICAL",
        }, raise_on_error=False)
        print(f"  create_alert(priority=CRITICAL) -> isError={r6.is_error}, text={r6.content[0].text}")

        # -- Clamping demo -----------------------------------------------------
        print("\n=== Input Clamping ===\n")

        r7 = await client.call_tool("search_data", {"query": "oil", "limit": 999})
        print(f"  search_data(limit=999) -> {r7.data}")

        r8 = await client.call_tool("search_data", {"query": "oil", "limit": -5})
        print(f"  search_data(limit=-5)  -> {r8.data}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Two strategies for invalid inputs:
    #
    # 1. ToolError -- for inputs that are genuinely wrong (division by
    #    zero, empty required fields, invalid enum values). The client
    #    sees isError=True and can handle gracefully.
    #
    # 2. Clamping -- for inputs that are "close enough" (limit=999
    #    becomes limit=50). Better UX than rejecting outright.
    #
    # Your production code uses both:
    #   - ToolError in archive_search.py for missing queries
    #   - Clamping in search_rics.py for limit values
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a `sqrt` tool that raises ToolError for negative inputs
    # 2. Add an `enum` constraint using json_schema_extra={"enum": [...]}
    #    on a Field to restrict parameter values at the schema level
