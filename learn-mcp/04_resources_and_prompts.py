"""Lesson 04 -- Beyond Tools: Resources & Prompts
==================================================

WHY THIS MATTERS:
  Most people think MCP = tools. But MCP actually has THREE primitives:
    - Tools:     DO something (write, search, generate)
    - Resources: READ something (config, templates, data)
    - Prompts:   TEMPLATE for LLM messages (reusable instructions)

  Tools are actions. Resources are data. Prompts are message templates.
  Together they let an agent discover everything it can do, read, and say.
  In production, workflows are exposed as resources via REST endpoints.

WHAT YOU'LL LEARN:
  1. Expose static data as resources (like a config endpoint)
  2. Expose dynamic data with URI templates (like a parameterized GET)
  3. Create reusable prompt templates
  4. Discover all three primitives from the client side
  5. (Part 2) A production-style newsroom server with all three primitives:
     ticker/article tools, a workflow resource, story + summary prompts

Concepts:
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
       +-- read_resource("language://fr") -> get dynamic data
       +-- list_prompts() -> discover prompt templates
       +-- get_prompt("welcome", {name: "Alice"}) -> get rendered prompt

  Maps to:
    shared/workflows/routes.py (workflows are effectively resources via REST)
    mcp_protocol.py (list_resources, read_resource client calls)
    Tools     -> every @mcp.tool in the skills (generate_spot_story, search_rics, ...)
    Resources -> workflow definitions loaded via GET /workflows
    Prompts   -> Jinja2 templates in story-drafting/src/prompts/

PREREQUISITES: Lesson 01 (server + tool basics)

Run:  uv run python 04_resources_and_prompts.py

EXPECTED OUTPUT:
  === Resources ===

  Available resources:
    - config://settings: get_settings

  config://settings -> ["...default_style: casual, max_name_length: 50..."]

  language://fr -> ["...hello: Bonjour...goodbye: Au revoir..."]
  language://de -> ["...hello: Hallo...goodbye: Auf Wiedersehen..."]

  === Resource Templates ===

  Available templates:
    - language://{code}: get_language_phrases

  === Prompts ===

  Available prompts:
    - welcome: Generate a prompt for composing a welcome message.
    - farewell_speech: Generate a prompt for composing a farewell speech.

  welcome(Alice, warm):
    Compose a warm welcome message for Alice. ...

  farewell_speech(Bob, retirement):
    Write a heartfelt farewell speech for Bob. ...

  === Tools (for comparison) ===

  Tools: ['greet']
  greet('Alice') -> CallToolResult(content=[TextContent(... Hello, Alice! ...)], ...)

  ============================================================
  PART 2: Newsroom server -- all three primitives
  ============================================================

  === Tools ===
    search_articles: Search news articles by keyword. Returns matching headlines.
    validate_ticker: Validate a stock ticker/RIC and return basic info.

  --- Calling validate_ticker('AAPL.O') ---
    {"name":"Apple Inc","exchange":"NASDAQ","valid":true}

  === Resources ===
    config://model-settings: get_model_settings
    workflow://spot-story: get_spot_story_workflow

  --- Reading workflow://spot-story ---
    name: spot-story-drafting ...

  === Prompts ===
    spot_story_prompt: Generate a prompt for drafting a spot news story.
    summary_prompt: Generate a prompt for summarizing text.

  --- Getting spot_story_prompt ---
    [user]: You are a Reuters journalist. Draft a spot news story. ...
"""

import asyncio
import json
from fastmcp import FastMCP, Client


mcp = FastMCP(name="greeting-resources")


# -- Static Resource -----------------------------------------------------------
# A fixed piece of data exposed at a known URI.
# Think of it like a config file or reference data.

@mcp.resource("config://settings")
def get_settings() -> str:
    """Greeting service settings and configuration."""
    return json.dumps({
        "default_style": "casual",
        "max_name_length": 50,
        "supported_languages": ["en", "fr", "de", "es"],
    })


# -- Dynamic Resource Template ------------------------------------------------
# URI contains a parameter {code} that gets filled at read time.
# Useful for serving language-specific greeting phrases.

@mcp.resource("language://{code}")
def get_language_phrases(code: str) -> str:
    """Get greeting and farewell phrases for a specific language."""
    languages = {
        "en": {"hello": "Hello", "goodbye": "Goodbye", "language": "English"},
        "fr": {"hello": "Bonjour", "goodbye": "Au revoir", "language": "French"},
        "de": {"hello": "Hallo", "goodbye": "Auf Wiedersehen", "language": "German"},
        "es": {"hello": "Hola", "goodbye": "Adios", "language": "Spanish"},
    }
    data = languages.get(code.lower(), {"error": f"Unknown language: {code}"})
    return json.dumps(data)


# -- Prompt Template -----------------------------------------------------------
# Reusable prompt templates that LLM clients can discover and use.
# The client calls get_prompt() with arguments to get a rendered prompt.

@mcp.prompt()
def welcome(name: str, style: str = "casual") -> str:
    """Generate a prompt for composing a welcome message."""
    styles = {
        "casual": "a friendly, casual",
        "formal": "a professional, formal",
        "warm": "a warm and heartfelt",
    }
    style_description = styles.get(style, styles["casual"])
    return (
        f"Compose {style_description} welcome message for {name}. "
        f"Make it personal and sincere. "
        f"Keep it to 2-3 sentences."
    )


@mcp.prompt()
def farewell_speech(name: str, occasion: str = "general") -> str:
    """Generate a prompt for composing a farewell speech."""
    return (
        f"Write a heartfelt farewell speech for {name}.\n"
        f"Occasion: {occasion}\n\n"
        f"Guidelines: Keep it under 100 words. Be sincere and positive. "
        f"Mention a memorable quality about the person."
    )


# -- A tool for comparison (tools DO things, resources EXPOSE data) ------------

@mcp.tool
async def greet(name: str) -> dict:
    """Greet someone by name (this is a tool, not a resource)."""
    return {"message": f"Hello, {name}!"}


# =============================================================================
# PART 2: A production-style server -- all three primitives, newsroom flavour
# =============================================================================
# The same three primitives, shaped like the real skills:
#   - Tools     -> every @mcp.tool in the skills (generate_spot_story, search_rics, ...)
#   - Resources -> workflow definitions (served via GET /workflows in production)
#   - Prompts   -> the Jinja2 templates in story-drafting/src/prompts/
#
# Rule of thumb for which primitive to use:
#   Tools     = ACTIONS the LLM decides to call. May have side effects.
#   Resources = DATA the client reads on demand, like a read-only GET endpoint.
#   Prompts   = reusable TEMPLATES, like stored procedures for LLM prompts:
#               the client fills in the variables before sending to the LLM.

newsroom = FastMCP("mcp-primitives")


@newsroom.tool()
def search_articles(query: str, max_results: int = 5) -> list[dict]:
    """Search news articles by keyword. Returns matching headlines."""
    return [
        {"id": f"art_{i}", "headline": f"{query} -- Development {i + 1}", "date": "2025-08-28"}
        for i in range(max_results)
    ]


@newsroom.tool()
def validate_ticker(ticker: str) -> dict:
    """Validate a stock ticker/RIC and return basic info."""
    known_tickers = {
        "AAPL.O": {"name": "Apple Inc", "exchange": "NASDAQ", "valid": True},
        "MSFT.O": {"name": "Microsoft Corp", "exchange": "NASDAQ", "valid": True},
        "GOOGL.O": {"name": "Alphabet Inc", "exchange": "NASDAQ", "valid": True},
    }
    return known_tickers.get(ticker, {"ticker": ticker, "valid": False, "error": "Unknown ticker"})


@newsroom.resource("config://model-settings")
def get_model_settings() -> str:
    """Current model configuration for story generation."""
    return json.dumps({
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 4096,
        "system_prompt_version": "v2.1",
    }, indent=2)


@newsroom.resource("workflow://spot-story")
def get_spot_story_workflow() -> str:
    """Workflow definition for spot story drafting."""
    return """
    name: spot-story-drafting
    description: Draft a spot news story from headlines and context
    steps:
      1. Validate the RIC (validate_ticker)
      2. Search for recent articles (search_articles)
      3. Generate draft (uses LLM -- not shown in this exercise)
      4. Present for review (human-in-the-loop interrupt)
    tools: [validate_ticker, search_articles]
    """


@newsroom.prompt()
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


@newsroom.prompt()
def summary_prompt(text: str, max_words: int = 50) -> str:
    """Generate a prompt for summarizing text."""
    return f"""Summarize the following text in {max_words} words or fewer.
Be concise and factual.

Text: {text}
"""


async def newsroom_demo():
    async with Client(newsroom) as client:
        print("\n" + "=" * 60)
        print("PART 2: Newsroom server -- all three primitives")
        print("=" * 60 + "\n")

        print("=== Tools ===")
        for t in await client.list_tools():
            print(f"  {t.name}: {t.description}")

        print("\n--- Calling validate_ticker('AAPL.O') ---")
        result = await client.call_tool("validate_ticker", {"ticker": "AAPL.O"})
        for c in result.content:            # fastmcp 3.x: a CallToolResult, not a list
            print(f"  {c.text}")

        print("\n=== Resources ===")
        for r in await client.list_resources():
            print(f"  {r.uri}: {r.name}")

        print("\n--- Reading workflow://spot-story ---")
        for c in await client.read_resource("workflow://spot-story"):
            print(f"  {c.text.strip()[:200]}...")

        print("\n=== Prompts ===")
        for p in await client.list_prompts():
            print(f"  {p.name}: {p.description}")

        print("\n--- Getting spot_story_prompt ---")
        prompt = await client.get_prompt(
            "spot_story_prompt",
            {"ticker": "AAPL.O", "headline": "Apple reports record Q3 revenue"},
        )
        for msg in prompt.messages:
            print(f"  [{msg.role}]: {msg.content.text[:150]}...")


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

        # Read dynamic resource (language code parameter in URI)
        french = await client.read_resource("language://fr")
        print(f"language://fr -> {french}")

        german = await client.read_resource("language://de")
        print(f"language://de -> {german}")
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
        p1 = await client.get_prompt("welcome", {"name": "Alice", "style": "warm"})
        print(f"welcome(Alice, warm):")
        print(f"  {p1.messages[0].content.text}")
        print()

        p2 = await client.get_prompt("farewell_speech", {
            "name": "Bob",
            "occasion": "retirement",
        })
        print(f"farewell_speech(Bob, retirement):")
        print(f"  {p2.messages[0].content.text}")
        print()

        # -- Tools (for comparison) --------------------------------------------
        print("=== Tools (for comparison) ===\n")

        tools = await client.list_tools()
        print(f"Tools: {[t.name for t in tools]}")
        r = await client.call_tool("greet", {"name": "Alice"})
        print(f"greet('Alice') -> {r}")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(newsroom_demo())

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
    # 1. Add a resource template "greeting://{name}" that returns a greeting
    # 2. Add a prompt "thank_you" that generates a thank-you message prompt
    # 3. Combine them: read a resource, then use a prompt with that data
    # 4. (Part 2) Add a resource that returns the list of supported RICs
    # 5. (Part 2) Add a prompt template for news bulletin generation
    # 6. (Part 2) Add a dynamic resource: @newsroom.resource("ticker://{symbol}/info")
