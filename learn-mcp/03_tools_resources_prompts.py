"""
Lesson 3: Tools, Resources, and Prompts — The Three MCP Primitives
===================================================================
Goal: Understand all three MCP primitives and when to use each.

  - TOOLS   = Functions the LLM can call (actions, computations)
  - RESOURCES = Data the LLM can read (like GET endpoints)
  - PROMPTS   = Reusable prompt templates (like stored procedures for LLMs)

Run:
  uv run python 03_tools_resources_prompts.py

Production parallel:
  - Tools: Every @mcp.tool in the skills (generate_spot_story, search_rics, etc.)
  - Resources: Workflow definitions loaded via GET /workflows
  - Prompts: Jinja2 templates in story-drafting/src/prompts/
"""

import asyncio
import json
from fastmcp import FastMCP, Client

mcp = FastMCP("mcp-primitives")

# ===== TOOLS =====
# Tools are ACTIONS. The LLM decides when to call them.
# They can have side effects (write to DB, call APIs, etc.)

@mcp.tool()
def search_articles(query: str, max_results: int = 5) -> list[dict]:
    """Search news articles by keyword. Returns matching headlines."""
    # Simulated search results
    fake_articles = [
        {"id": f"art_{i}", "headline": f"{query} — Development {i+1}", "date": "2025-08-28"}
        for i in range(max_results)
    ]
    return fake_articles


@mcp.tool()
def validate_ticker(ticker: str) -> dict:
    """Validate a stock ticker/RIC and return basic info."""
    known_tickers = {
        "AAPL.O": {"name": "Apple Inc", "exchange": "NASDAQ", "valid": True},
        "MSFT.O": {"name": "Microsoft Corp", "exchange": "NASDAQ", "valid": True},
        "GOOGL.O": {"name": "Alphabet Inc", "exchange": "NASDAQ", "valid": True},
    }
    return known_tickers.get(ticker, {"ticker": ticker, "valid": False, "error": "Unknown ticker"})


# ===== RESOURCES =====
# Resources are DATA. The LLM (or client) reads them on demand.
# Think of them as read-only endpoints. No side effects.

@mcp.resource("config://model-settings")
def get_model_settings() -> str:
    """Current model configuration for story generation."""
    settings = {
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 4096,
        "system_prompt_version": "v2.1",
    }
    return json.dumps(settings, indent=2)


@mcp.resource("workflow://spot-story")
def get_spot_story_workflow() -> str:
    """Workflow definition for spot story drafting."""
    return """
    name: spot-story-drafting
    description: Draft a spot news story from headlines and context
    steps:
      1. Validate the RIC (validate_ticker)
      2. Search for recent articles (search_articles)
      3. Generate draft (uses LLM — not shown in this exercise)
      4. Present for review (human-in-the-loop interrupt)
    tools: [validate_ticker, search_articles]
    """


# ===== PROMPTS =====
# Prompts are reusable templates. The client fetches them and
# fills in variables before sending to the LLM.

@mcp.prompt()
def spot_story_prompt(ticker: str, headline: str) -> str:
    """Generate a prompt for drafting a spot news story."""
    return f"""You are a Reuters journalist. Draft a spot news story.

Ticker: {ticker}
Headline: {headline}

Requirements:
- Lead with the most newsworthy fact
- Include the ticker in the first paragraph
- Keep it under 200 words
- Use Reuters style guide conventions
"""


@mcp.prompt()
def summary_prompt(text: str, max_words: int = 50) -> str:
    """Generate a prompt for summarizing text."""
    return f"""Summarize the following text in {max_words} words or fewer.
Be concise and factual.

Text: {text}
"""


# ===== CLIENT DEMO =====

async def demo():
    client = Client(mcp)  # in-process client (no subprocess)

    async with client:
        # List and call tools
        tools = await client.list_tools()
        print("=== TOOLS ===")
        for t in tools:
            print(f"  {t.name}: {t.description}")

        print("\n--- Calling validate_ticker ---")
        result = await client.call_tool("validate_ticker", {"ticker": "AAPL.O"})
        for c in result:
            print(f"  {c.text}")

        # List and read resources
        resources = await client.list_resources()
        print("\n=== RESOURCES ===")
        for r in resources:
            print(f"  {r.uri}: {r.name}")

        print("\n--- Reading workflow://spot-story ---")
        resource = await client.read_resource("workflow://spot-story")
        for c in resource:
            print(f"  {c.text[:200]}...")

        # List and get prompts
        prompts = await client.list_prompts()
        print("\n=== PROMPTS ===")
        for p in prompts:
            print(f"  {p.name}: {p.description}")

        print("\n--- Getting spot_story_prompt ---")
        prompt = await client.get_prompt(
            "spot_story_prompt",
            {"ticker": "AAPL.O", "headline": "Apple reports record Q3 revenue"},
        )
        for msg in prompt.messages:
            print(f"  [{msg.role}]: {msg.content.text[:150]}...")


if __name__ == "__main__":
    asyncio.run(demo())


# ============================================================
# EXERCISES:
#
# 1. Add a resource that returns a list of supported RICs
# 2. Add a prompt template for news bulletin generation
# 3. Try using a resource URI with a dynamic path:
#    @mcp.resource("ticker://{symbol}/info")
# ============================================================
