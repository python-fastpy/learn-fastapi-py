"""Lesson 04 -- The 3 MCP Primitives: Tools, Resources, Prompts
===============================================================

An MCP server can offer three kinds of things (four cases):

  1. TOOL               greet(name)              DO something      -> "Hello, Shubham!"
  2. RESOURCE           greet://languages        READ fixed data   -> "en, fr, de"
  3. RESOURCE TEMPLATE  greet://hello/{lang}     READ by parameter -> greet://hello/fr = "Bonjour"
  4. PROMPT             welcome_message(name)    TEMPLATE for LLM  -> "Write a warm welcome for ..."

  Tool     = an ACTION the LLM decides to call      (like POST)
  Resource = DATA the app reads, no side effects    (like GET)
  Prompt   = reusable INSTRUCTIONS; the client fills in the blanks and
             sends the result to the LLM

      MCP CLIENT                                MCP SERVER "greetings"
  ┌──────────────────────┐                  ┌──────────────────────────────────┐
  │                      │  tools/call      │ 1. TOOL                          │
  │ call_tool("greet",   │ ───────────────► │    greet(name)                   │
  │   {"name":"Shubham"})│ ◄─────────────── │    -> "Hello, Shubham!"          │
  │                      │                  │                                  │
  │ read_resource(       │  resources/read  │ 2. RESOURCE                      │
  │  "greet://languages")│ ───────────────► │    greet://languages             │
  │                      │ ◄─────────────── │    -> "en, fr, de"               │
  │                      │                  │                                  │
  │ read_resource(       │  resources/read  │ 3. RESOURCE TEMPLATE             │
  │  "greet://hello/fr") │ ───────────────► │    greet://hello/{lang}          │
  │                      │ ◄─────────────── │    {lang}="fr" -> "Bonjour"      │
  │                      │                  │                                  │
  │ get_prompt(          │  prompts/get     │ 4. PROMPT                        │
  │  "welcome_message",  │ ───────────────► │    welcome_message(name)         │
  │  {"name":"Shubham"}) │ ◄─────────────── │    -> "Write a warm 2-sentence   │
  │         │            │                  │        welcome ... Shubham."     │
  └─────────┼────────────┘                  └──────────────────────────────────┘
            ▼
     send that text to the LLM (the server never talks to the LLM itself)

  Discovery first: list_tools / list_resources / list_resource_templates /
  list_prompts tell the client what exists -- nothing is hard-coded.

Run:  uv run python 04_resources_and_prompts.py

Maps to: tools -> every @mcp.tool in the skills; resources -> workflow
definitions (GET /workflows); prompts -> Jinja2 templates in story-drafting.
"""

import asyncio
from fastmcp import FastMCP, Client

mcp = FastMCP("greetings")


# 1. TOOL -- do something
@mcp.tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


# 2. RESOURCE -- fixed data at a fixed address
@mcp.resource("greet://languages")
def languages() -> str:
    """Languages this server can say hello in."""
    return "en, fr, de"


# 3. RESOURCE TEMPLATE -- {lang} in the address is filled in when read
@mcp.resource("greet://hello/{lang}")
def hello_in(lang: str) -> str:
    """'Hello' in one language."""
    return {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}.get(lang, "unknown language")


# 4. PROMPT -- a reusable instruction template for the LLM
@mcp.prompt
def welcome_message(name: str) -> str:
    """Ask the LLM to write a welcome message."""
    return f"Write a warm 2-sentence welcome message for {name}."


async def main():
    async with Client(mcp) as client:
        # 1. tool      -> call_tool
        r = await client.call_tool("greet", {"name": "Shubham"})
        print("1. tool     :", r.data)                      # Hello, Shubham!

        # 2. resource  -> read_resource
        r = await client.read_resource("greet://languages")
        print("2. resource :", r[0].text)                   # en, fr, de

        # 3. template  -> read_resource with the parameter in the address
        r = await client.read_resource("greet://hello/fr")
        print("3. template :", r[0].text)                   # Bonjour

        # 4. prompt    -> get_prompt (returns messages ready to send to an LLM)
        r = await client.get_prompt("welcome_message", {"name": "Shubham"})
        print("4. prompt   :", r.messages[0].content.text)  # Write a warm ... for Shubham.

        # Clients discover everything at runtime -- no hard-coding needed
        print("\nlist_tools             :", [t.name for t in await client.list_tools()])
        print("list_resources         :", [str(x.uri) for x in await client.list_resources()])
        print("list_resource_templates:", [x.uriTemplate for x in await client.list_resource_templates()])
        print("list_prompts           :", [p.name for p in await client.list_prompts()])


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Add a resource template "greet://goodbye/{lang}".
# 2. Add a prompt thank_you(name).
# 3. Read greet://hello/de, then pass the word into welcome_message.
# 4. Newsroom version: a "rics://supported" resource, a news_bulletin(headline)
#    prompt, and a "ticker://{symbol}/info" resource template.
