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
  greet('Alice') -> [TextContent(... Hello, Alice! ...)]
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
