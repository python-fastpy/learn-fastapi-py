"""Lesson 02 -- Tool Registration & Types
==========================================
Concepts:
  - Two registration styles: decorator (@mcp.tool) vs imperative mcp.tool()(fn)
  - meta dict: display_name, response_mode, hidden
  - Multiple tools on one server
  - async def tool functions with typed parameters
  - Return type patterns: dict for simple results

Flow:
  +--------+     +------------------+     +------------------+
  | Client | --> | MCP Server       | --> | Tool Functions   |
  +--------+     | "news-tools"     |     |                  |
                 +------------------+     | get_headline()   |
                 | Tools:           |     | search_articles()|
                 |  - get_headline  |     | validate_ticker()|
                 |  - search_articles|    +------------------+
                 |  - validate_ticker|
                 +------------------+

  Your production code uses IMPERATIVE registration exclusively:
    mcp.tool(name="generate_spot_story", meta={...})(generate_spot_story)
  This keeps tool logic separate from server wiring.

No LLM needed -- demonstrates registration patterns.

Run:  uv run python 02_tool_patterns.py
"""

import asyncio
from typing import Annotated, Optional
from pydantic import Field
from fastmcp import FastMCP, Client


mcp = FastMCP(name="news-tools")


# -- Style 1: Decorator registration ------------------------------------------
# Simple and clean -- good for small servers or learning.

@mcp.tool
async def get_headline(
    topic: Annotated[str, Field(description="News topic to get headline for")],
) -> dict:
    """Get the latest headline for a given news topic."""
    headlines = {
        "markets": "S&P 500 Hits Record High Amid Fed Optimism",
        "energy": "Oil Prices Surge After OPEC+ Extends Cuts",
        "tech": "AI Investment Reaches $200B Globally",
    }
    return {
        "headline": headlines.get(topic.lower(), f"No headline for: {topic}"),
        "topic": topic,
    }


# -- Style 2: Imperative registration -----------------------------------------
# This is what your production codebase uses (story-drafting/src/main.py).
# Advantages:
#   - Tool function has no framework coupling (plain async def)
#   - Registration with name/meta happens in one place (main.py)
#   - Easier to test the function independently

async def _search_articles(
    query: Annotated[str, Field(description="Search query for articles")],
    limit: Annotated[int, Field(default=5, description="Max results to return")] = 5,
) -> dict:
    """Search the news archive for articles matching a query."""
    limit = min(max(limit, 1), 20)  # clamp like search_rics.py does
    articles = [
        {"title": f"Article about {query} #{i+1}", "date": f"2024-12-{20-i}"}
        for i in range(limit)
    ]
    return {"query": query, "count": len(articles), "articles": articles}


# Imperative registration with meta -- mirrors production pattern
mcp.tool(
    name="search_articles",
    meta={
        "display_name": "Search News Archive",
        "response_mode": "direct",
    },
)(_search_articles)


# -- Hidden tools (internal, not shown as skills in UI) ------------------------

async def _validate_ticker(
    ticker: Annotated[str, Field(description="Stock ticker symbol to validate")],
) -> dict:
    """Validate if a stock ticker symbol exists."""
    valid = {"AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"}
    return {
        "ticker": ticker.upper(),
        "valid": ticker.upper() in valid,
    }


mcp.tool(
    name="validate_ticker",
    meta={
        "display_name": "Validate Ticker",
        "response_mode": "direct",
        "hidden": True,  # internal tool, not exposed as a skill
    },
)(_validate_ticker)


async def main():
    async with Client(mcp) as client:
        # Discover all tools (including hidden ones -- MCP lists them all)
        tools = await client.list_tools()
        print("=== Registered Tools ===")
        for tool in tools:
            meta = getattr(tool, "meta", {}) or {}
            hidden = meta.get("hidden", False) if isinstance(meta, dict) else False
            label = " [HIDDEN]" if hidden else ""
            print(f"  - {tool.name}{label}: {tool.description}")
        print()

        # Call each tool
        print("=== get_headline ===")
        r1 = await client.call_tool("get_headline", {"topic": "markets"})
        print(f"  {r1}")

        print("\n=== search_articles ===")
        r2 = await client.call_tool("search_articles", {"query": "OPEC", "limit": 3})
        print(f"  {r2}")

        print("\n=== validate_ticker (hidden tool) ===")
        r3 = await client.call_tool("validate_ticker", {"ticker": "AAPL"})
        print(f"  {r3}")

        r4 = await client.call_tool("validate_ticker", {"ticker": "FAKE"})
        print(f"  {r4}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Production uses IMPERATIVE registration to keep tool functions clean:
    #   mcp.tool(name="...", meta={...})(function)
    #
    # The meta dict controls UI behavior:
    #   display_name  -> what the user sees
    #   response_mode -> "direct" (tool runs to completion)
    #   hidden        -> True for internal tools (validate_ric, search_rics)
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a tool with meta={"hidden": True} and verify it still works
    #    when called by name (hidden just affects UI display)
    # 2. Try calling a tool that doesn't exist and observe the error
