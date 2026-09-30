"""Lesson 01 -- Creating a server, and its three components
===========================================================

A FastMCP server has ONE identity (its name, etc.) and THREE kinds of things
you can put inside it:

    @mcp.tool       -- DO something   (like a function call)
    @mcp.resource   -- READ something (like a GET request, has a URI)
    @mcp.prompt     -- REUSE a message template

THE RUNNING EXAMPLE: every lesson in this folder greets someone. The domain
never changes, so what you notice between lessons is the FEATURE, not a new
set of nouns to learn.

Run:  uv run python 01_create_and_components.py
"""

import asyncio

from fastmcp import Client, FastMCP


# --------------------------------------------------------------- 1. SERVER
# `name` is the only required field. `instructions` matters most in
# practice: it's what the client shows the LLM to explain what this server
# is for.
mcp = FastMCP(
    name="GreetingService",
    instructions="Greets people by name. Call greet() for hello, farewell() for goodbye.",
)


# ----------------------------------------------------------------- 2. TOOLS
# A tool = an action. The docstring becomes the description the LLM reads.
@mcp.tool
def greet(name: str) -> str:
    """Greets someone by name."""
    return f"Hello, {name}!"


@mcp.tool
def farewell(name: str) -> str:
    """Says goodbye to someone by name."""
    return f"Goodbye, {name}!"


# ------------------------------------------------------------- 3. RESOURCES
# A resource = read-only data, addressed by a URI instead of a function call.
@mcp.resource("data://greeting")
def greeting_config() -> dict:
    """A fixed piece of data at a fixed URI."""
    return {"template": "Hello, {name}!", "language": "en"}


# A resource TEMPLATE has a parameter inside the URI itself.
# One function serves greet://alice, greet://bob, greet://anyone...
@mcp.resource("greet://{name}")
def greeting_for(name: str) -> dict:
    """Same idea, but the URI has a placeholder."""
    return {"name": name, "greeting": f"Hello, {name}!"}


# ------------------------------------------------------------- 4. PROMPTS
# A prompt = a reusable message template. The server writes the wording,
# the caller fills in the blanks.
@mcp.prompt
def ask_greeting(name: str) -> str:
    """Asks the LLM to write a greeting for someone."""
    return f"Write a warm, one-line greeting for someone called {name}."


async def main():
    # Client(mcp) talks to the server directly in-memory -- no network needed.
    # Lesson 02 covers real transports (HTTP, stdio, ...).
    async with Client(mcp) as client:
        # 1. See the server's identity
        print("server      :", client.server_info.name)
        print("instructions:", client.instructions)

        # 2. List each kind of component
        print("\ntools     :", [t.name for t in await client.list_tools()])
        print("resources :", [str(r.uri) for r in await client.list_resources()])
        print("templates :", [t.uri_template for t in await client.list_resource_templates()])
        print("prompts   :", [p.name for p in await client.list_prompts()])

        # 3. Use each kind of component
        greeting = await client.call_tool("greet", {"name": "Shubham"})
        print("\ncall greet('Shubham')   ->", greeting.data)

        bye = await client.call_tool("farewell", {"name": "Shubham"})
        print("call farewell('Shubham')->", bye.data)

        config = await client.read_resource("data://greeting")
        print("read data://greeting    ->", config[0].text)

        alice = await client.read_resource("greet://Alice")
        print("read greet://Alice      ->", alice[0].text)

        prompt = await client.get_prompt("ask_greeting", {"name": "Alice"})
        print("prompt ask_greeting     ->", prompt.messages[0].content.text)


if __name__ == "__main__":
    asyncio.run(main())


# Exercises:
# 1. Drop `instructions` from FastMCP() -- what does client.instructions become?
# 2. Add a second parameter to the template: greet://{name}/{language}.
#    Does it show up under resources or templates?
