"""Lesson 04 -- The 3 MCP Primitives: Tools, Resources, Prompts
===============================================================

Most people think MCP = tools. An MCP server can actually offer THREE
kinds of things. One greeting server shows all three:

  ┌──────────────────── MCP server "greetings" ────────────────────┐
  │                                                                │
  │  TOOL       greet(name, language)       DO something           │
  │             the LLM decides to call it  -> "Bonjour, Shubham!" │
  │                                                                │
  │  RESOURCE   greet://languages           READ fixed data        │
  │             like GET /languages         -> ["en","fr","de",..] │
  │                                                                │
  │  RESOURCE   greet://phrases/{code}      READ data by parameter │
  │  TEMPLATE   like GET /phrases/fr        -> {"hello": "Bonjour"}│
  │                                                                │
  │  PROMPT     welcome_message(name)       TEMPLATE for the LLM   │
  │             like a stored procedure     -> "Write a warm       │
  │             for prompts                     welcome for ..."   │
  └────────────────────────────────────────────────────────────────┘

  Which one to use?
    Tool     -> an ACTION (may have side effects). The LLM chooses to call it.
    Resource -> DATA to read (no side effects). The app/client reads it.
    Prompt   -> reusable INSTRUCTIONS. The client fills in the blanks and
                sends the result to the LLM.

  Maps to production:
    Tools     -> every @mcp.tool in the skills (generate_spot_story, search_rics, ...)
    Resources -> workflow definitions (GET /workflows, shared/workflows/routes.py)
    Prompts   -> Jinja2 templates in story-drafting/src/prompts/

Run:  uv run python 04_resources_and_prompts.py
"""

import asyncio
import json
from fastmcp import FastMCP, Client

mcp = FastMCP("greetings")

PHRASES = {
    "en": {"hello": "Hello", "goodbye": "Goodbye"},
    "fr": {"hello": "Bonjour", "goodbye": "Au revoir"},
    "de": {"hello": "Hallo", "goodbye": "Auf Wiedersehen"},
    "es": {"hello": "Hola", "goodbye": "Adios"},
}


# -- 1. TOOL: do something ----------------------------------------------------

@mcp.tool
def greet(name: str, language: str = "en") -> str:
    """Greet someone by name in a given language (en, fr, de, es)."""
    return f"{PHRASES.get(language, PHRASES['en'])['hello']}, {name}!"


# -- 2. RESOURCE: read fixed data at a known URI -----------------------------

@mcp.resource("greet://languages")
def languages() -> str:
    """The language codes this server supports."""
    return json.dumps(sorted(PHRASES))


# -- 3. RESOURCE TEMPLATE: read data by parameter ({code} is filled in) -------

@mcp.resource("greet://phrases/{code}")
def phrases(code: str) -> str:
    """Hello and goodbye phrases for one language."""
    return json.dumps(PHRASES.get(code, {"error": f"unknown language: {code}"}))


# -- 4. PROMPT: a reusable template for the LLM -------------------------------

@mcp.prompt
def welcome_message(name: str, style: str = "warm") -> str:
    """A prompt asking the LLM to write a welcome message."""
    return f"Write a {style} 2-sentence welcome message for {name}. Be sincere."


# -- Client: discover and use all of them -------------------------------------

async def main():
    async with Client(mcp) as client:
        print("TOOLS:", [t.name for t in await client.list_tools()])
        result = await client.call_tool("greet", {"name": "Shubham", "language": "fr"})
        print("  call greet(Shubham, fr)          ->", result.data)

        print("\nRESOURCES:", [str(r.uri) for r in await client.list_resources()])
        data = await client.read_resource("greet://languages")
        print("  read greet://languages           ->", data[0].text)

        print("\nRESOURCE TEMPLATES:", [t.uriTemplate for t in await client.list_resource_templates()])
        data = await client.read_resource("greet://phrases/de")
        print("  read greet://phrases/de          ->", data[0].text)

        print("\nPROMPTS:", [p.name for p in await client.list_prompts()])
        prompt = await client.get_prompt("welcome_message", {"name": "Shubham"})
        print("  get welcome_message(Shubham)     ->", prompt.messages[0].content.text)


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    #   Tool     -> DO    (call_tool)       e.g. greet, generate_spot_story
    #   Resource -> READ  (read_resource)   e.g. config, workflow definitions
    #   Prompt   -> SAY   (get_prompt)      e.g. reusable instruction templates
    # All three are discovered at runtime with list_*() -- the client doesn't
    # need to know in advance what a server offers.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a resource template "greet://greeting/{name}" that returns a greeting
    # 2. Add a prompt "thank_you(name)" for a thank-you message
    # 3. Combine them: read greet://phrases/fr, then put the phrases into a prompt
    # 4. Newsroom version: a "rics://supported" resource listing valid RICs,
    #    a "news_bulletin(headline)" prompt, and a "ticker://{symbol}/info" template
