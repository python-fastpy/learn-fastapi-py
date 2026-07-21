"""Lesson 04 -- Beyond Tools: Resources & Prompts
==================================================
Concepts:
  - MCP has THREE primitives: Tools, Resources, Prompts
  - @mcp.resource("uri"): expose read-only data (like a GET endpoint)
  - @mcp.resource("template://{param}"): dynamic resource with URI params
  - @mcp.prompt(): reusable prompt templates for LLMs
  - Client discovery: list_resources(), read_resource(), list_prompts(), get_prompt()

Flow:
  +--------+     +------------------+
  | Client | --> | MCP Server       |
  +--------+     +------------------+
       |         | 3 Primitives:    |
       |         |  Tools     (DO)  |
       |         |  Resources (READ)|
       |         |  Prompts  (TMPL) |
       |         +------------------+
       |
       +-- list_resources() -> discover what data is available
       +-- read_resource("config://settings") -> get static data
       +-- read_resource("topic://markets") -> get dynamic data
       +-- list_prompts() -> discover prompt templates
       +-- get_prompt("summarize", {topic: "oil"}) -> get rendered prompt

  Maps to:
    shared/workflows/routes.py (workflows are effectively resources via REST)
    mcp_protocol.py (list_resources, read_resource client calls)

No LLM needed -- demonstrates the MCP primitive surface area.

Run:  uv run python 04_resources_and_prompts.py
"""

import asyncio
import json
from fastmcp import FastMCP, Client


mcp = FastMCP(name="news-resources")


# -- Static Resource -----------------------------------------------------------
# A fixed piece of data exposed at a known URI.
# Think of it like a config file or reference data.

@mcp.resource("config://settings")
def get_settings() -> str:
    """Application settings and configuration."""
    return json.dumps({
        "version": "2.1.0",
        "region": "eu-west-1",
        "max_results": 50,
        "supported_languages": ["en", "fr", "de", "es"],
    })


# -- Dynamic Resource Template ------------------------------------------------
# URI contains a parameter {topic} that gets filled at read time.
# Useful for serving topic-specific data.

@mcp.resource("topic://{topic}")
def get_topic_data(topic: str) -> str:
    """Get the latest data for a specific news topic."""
    topics = {
        "markets": {"index": "S&P 500", "value": 5930.85, "change": "+1.2%"},
        "energy": {"commodity": "Brent Crude", "price": 78.50, "change": "-0.5%"},
        "tech": {"sector": "AI/ML", "investment": "$200B", "trend": "accelerating"},
    }
    data = topics.get(topic.lower(), {"error": f"Unknown topic: {topic}"})
    return json.dumps(data)


# -- Prompt Template -----------------------------------------------------------
# Reusable prompt templates that LLM clients can discover and use.
# The client calls get_prompt() with arguments to get a rendered prompt.

@mcp.prompt()
def summarize(topic: str, style: str = "concise") -> str:
    """Generate a prompt for summarizing news about a topic."""
    styles = {
        "concise": "in 2-3 sentences",
        "detailed": "in a comprehensive paragraph with key data points",
        "bullet": "as 5 bullet points",
    }
    style_instruction = styles.get(style, styles["concise"])
    return (
        f"Summarize the latest news about {topic} {style_instruction}. "
        f"Include specific numbers and data points where available. "
        f"Write in Reuters news style."
    )


@mcp.prompt()
def draft_headline(event: str, impact: str = "neutral") -> str:
    """Generate a prompt for drafting a news headline."""
    return (
        f"Write a Reuters-style headline for the following event:\n"
        f"Event: {event}\n"
        f"Market impact: {impact}\n\n"
        f"Rules: Max 80 characters. Start with the key fact. No clickbait."
    )


# -- A tool for comparison (tools DO things, resources EXPOSE data) ------------

@mcp.tool
async def analyze_topic(topic: str) -> dict:
    """Analyze a news topic (this is a tool, not a resource)."""
    return {"topic": topic, "sentiment": "positive", "confidence": 0.85}


async def main():
    async with Client(mcp) as client:
        # -- Resources ---------------------------------------------------------
        print("=== Resources ===\n")

        resources = await client.list_resources()
        print("Available resources:")
        for r in resources:
            print(f"  - {r.uri}: {r.name}")
        print()

        # Read static resource
        settings = await client.read_resource("config://settings")
        print(f"config://settings -> {settings}")
        print()

        # Read dynamic resource (topic parameter in URI)
        markets = await client.read_resource("topic://markets")
        print(f"topic://markets -> {markets}")

        energy = await client.read_resource("topic://energy")
        print(f"topic://energy  -> {energy}")
        print()

        # -- Resource Templates ------------------------------------------------
        print("=== Resource Templates ===\n")

        templates = await client.list_resource_templates()
        print("Available templates:")
        for t in templates:
            print(f"  - {t.uriTemplate}: {t.name}")
        print()

        # -- Prompts -----------------------------------------------------------
        print("=== Prompts ===\n")

        prompts = await client.list_prompts()
        print("Available prompts:")
        for p in prompts:
            print(f"  - {p.name}: {p.description}")
        print()

        # Get rendered prompts
        p1 = await client.get_prompt("summarize", {"topic": "oil prices", "style": "bullet"})
        print(f"summarize(oil prices, bullet):")
        print(f"  {p1.messages[0].content.text}")
        print()

        p2 = await client.get_prompt("draft_headline", {
            "event": "Fed raises rates by 25bps",
            "impact": "negative",
        })
        print(f"draft_headline(Fed raises rates):")
        print(f"  {p2.messages[0].content.text}")
        print()

        # -- Tools (for comparison) --------------------------------------------
        print("=== Tools (for comparison) ===\n")

        tools = await client.list_tools()
        print(f"Tools: {[t.name for t in tools]}")
        r = await client.call_tool("analyze_topic", {"topic": "markets"})
        print(f"analyze_topic('markets') -> {r}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # MCP has three primitives:
    #
    #   Tools     -> DO something (call LLM, search DB, create draft)
    #   Resources -> EXPOSE data (config, reference data, status)
    #   Prompts   -> TEMPLATE for LLM prompts (reusable, parameterized)
    #
    # Your production codebase mostly uses Tools (MCP tools for skills)
    # but workflows are exposed via REST endpoints that work like resources
    # (GET /workflows returns read-only data about available workflows).
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a resource template "article://{id}" that returns article data
    # 2. Add a prompt "fact_check" that generates a fact-checking prompt
    # 3. Combine them: read a resource, then use a prompt with that data
