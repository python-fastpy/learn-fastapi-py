"""Tools -- functions the LLM can call
========================================

FastMCP builds everything a client needs from your plain Python function:

    def greet(name: str) -> str:           signature   -> input schema
        '''Greets someone by name.'''      docstring   -> description
        return f"Hello, {name}!"           return type -> output schema

What you RETURN decides what the client gets back:
    str                -> plain text
    dict / dataclass   -> text + structured JSON
    a bare int/list    -> text + structured JSON, wrapped as {"result": ...}
    ToolResult         -> exactly what you put in it, no conversion

Restriction: *args / **kwargs functions can't be tools -- the schema needs a
fixed, complete list of parameters.

Level: BASIC
Run:  uv run python basic/01_tools.py
Test in Inspector:  uv run fastmcp dev inspector basic/01_tools.py
"""

import asyncio
from dataclasses import dataclass
from typing import Annotated, Literal

from fastmcp import Client, FastMCP
from fastmcp.dependencies import Depends
from fastmcp.exceptions import ToolError
from fastmcp.tools import Tool, ToolResult
from mcp.types import TextContent, ToolAnnotations
from pydantic import Field

mcp = FastMCP("GreetingService")


# ------------------------------------------------------------ 1. the basics
@mcp.tool
def greet(name: str) -> str:
    """Greets someone by name."""
    return f"Hello, {name}!"


# Decorator arguments override what FastMCP would otherwise infer.
@mcp.tool(
    name="greet_formally",                            # MCP name != function name
    description="Greets someone with their title.",   # overrides the docstring
    tags={"greeting", "formal"},                      # for filtering
    meta={"version": "1.2"},                          # static metadata for the client UI
    timeout=30.0,                                     # seconds; error if exceeded
)
def formal_greeting_impl(name: str, title: str = "Dr.") -> str:
    """Ignored, because description= was supplied above."""
    return f"Good day, {title} {name}."


# ------------------------------------------- 2. describing the arguments
# Two ways to tell the LLM what an argument means -- a docstring Args:
# section, or Annotated[type, Field(...)] when you also need a constraint.
@mcp.tool
def greet_with_options(name: str, repeat: int = 1) -> str:
    """Greets someone, optionally repeating.

    Args:
        name: Who to greet.
        repeat: How many times to repeat the greeting.
    """
    return " ".join([f"Hello, {name}!"] * repeat)


@mcp.tool
def greet_annotated(
    name: str,
    repeat: Annotated[int, Field(description="How many greetings", ge=1, le=100)] = 1,
    language: Literal["en", "fr", "de"] = "en",   # Literal -> an enum in the schema
) -> str:
    """Field adds a real constraint -- repeat > 100 is rejected before this runs."""
    hello = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}[language]
    return " ".join([f"{hello}, {name}!"] * repeat)


# ---------------------------------------- 3. hiding arguments with Depends
# Runtime values (user ids, credentials) should not be in the schema at all.
# Depends() injects them and removes them from what the client sees.
def get_current_user() -> str:
    return "Ada"


@mcp.tool
def greet_me(user: str = Depends(get_current_user)) -> str:
    """Greets the caller. The client never sees a `user` argument."""
    return f"Hello, {user}!"


# ------------------------------------------------- 4. structured output
@dataclass
class Greeting:
    text: str
    name: str


@mcp.tool
def greet_structured(name: str) -> Greeting:
    """Object-like returns always produce structuredContent."""
    return Greeting(text=f"Hello, {name}!", name=name)


@mcp.tool
def count_greetings(names: list[str]) -> int:
    """A non-object return gets wrapped: structuredContent = {"result": N}.
    (Drop the -> int return hint entirely and it's content-only, no schema.)"""
    return len(names)


# --------------------------------------------------- 5. full control
@mcp.tool
def greet_verbose(name: str) -> ToolResult:
    """ToolResult bypasses all automatic conversion."""
    return ToolResult(
        content=[TextContent(type="text", text=f"Hello, {name}!")],
        structured_content={"name": name, "greeting_count": 1},
        meta={"execution_time_ms": 145},   # per-CALL metadata (vs @mcp.tool(meta=))
    )


# ------------------------------------------------------ 6. error handling
@mcp.tool
def greet_strict(name: str) -> str:
    """Greets someone, refusing an empty name."""
    if not name.strip():
        raise ToolError("name cannot be empty")   # always reaches the client
    return f"Hello, {name}!"


# ------------------------------------------------------- 7. annotations
# Behavioural HINTS for the client UI -- cost no prompt tokens, enforce
# nothing server-side. A server can lie; never trust them from an
# untrusted server for a security decision. Five fields: title,
# readOnlyHint, destructiveHint, idempotentHint, openWorldHint.
#   readOnlyHint=True   -> client can skip its "allow this tool?" prompt
#   idempotentHint=True -> safe for a client to auto-retry after a timeout
#   openWorldHint=False -> "internal data only" (True = reaches the internet)
#   title               -> human-readable label for a tool-picker menu
@mcp.tool(annotations=ToolAnnotations(
    title="Greet Someone", readOnlyHint=True, idempotentHint=True, openWorldHint=False,
))
def greet_safely(name: str) -> str:
    """Greets someone. Safe to call repeatedly."""
    return f"Hello, {name}!"


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
def delete_greeting(name: str) -> dict:
    """Permanently removes a saved greeting -- clients should confirm first."""
    return {"deleted": name}


# ---------------------------------------- 8. programmatic registration
# No decorator at all -- useful when the function already exists elsewhere.
def farewell(name: str) -> str:
    """Says goodbye to someone by name."""
    return f"Goodbye, {name}!"


mcp.add_tool(Tool.from_function(farewell, name="say_goodbye"))


# Or call the decorator WITHOUT "@" -- one function under two tool names.
def greet_alt(name: str) -> str:
    """One function, reachable under two different tool names."""
    return f"Greetings, {name}."


mcp.tool(name="greet_formally_alt")(greet_alt)
mcp.tool(name="greet_casually_alt")(greet_alt)


async def main():
    async with Client(mcp) as client:
        tools = {t.name: t for t in await client.list_tools()}
        print("tools:", sorted(tools))

        # Field constraints land in the schema the LLM reads
        rep = tools["greet_annotated"].input_schema["properties"]["repeat"]
        print("\nrepeat constraints:", {k: v for k, v in rep.items() if k in ("minimum", "maximum")})

        # Depends() removed `user` from the schema
        print("greet_me schema args:", list(tools["greet_me"].input_schema["properties"]))
        print("greet_me ->", (await client.call_tool("greet_me")).data)

        # structured vs wrapped
        r = await client.call_tool("greet_structured", {"name": "Ada"})
        print("\nGreeting structured:", r.structured_content)
        r = await client.call_tool("count_greetings", {"names": ["a", "b", "c"]})
        print("int      structured:", r.structured_content, "  (wrapped in 'result')")

        r = await client.call_tool("greet_verbose", {"name": "Ada"})
        print("\nToolResult content   :", r.content[0].text)
        print("ToolResult structured:", r.structured_content)

        r = await client.call_tool("greet_strict", {"name": " "}, raise_on_error=False)
        print("\nToolError ->", r.content[0].text)

        print("annotations on greet_safely:", tools["greet_safely"].annotations)
        print("say_goodbye('Ada') ->", (await client.call_tool("say_goodbye", {"name": "Ada"})).data)

    # removing a tool at runtime (clients get a tools/list_changed notification)
    mcp.local_provider.remove_tool("delete_greeting")
    async with Client(mcp) as client:
        print("\nafter remove_tool:", "delete_greeting" in [t.name for t in await client.list_tools()])


if __name__ == "__main__":
    asyncio.run(main())
