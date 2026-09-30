"""Lesson 06 -- Tools in depth
=============================

A tool is a Python function the LLM can call. FastMCP reads the signature to
build the input schema, the docstring to build the description, runs the
function, and converts whatever you return into an MCP result:

    def greet(name: str) -> str:           signature   -> inputSchema
        '''Greets someone by name.'''      docstring   -> description
        return f"Hello, {name}!"           return type -> outputSchema

What you return decides what the client gets:
    str                     -> plain text
    dict / dataclass        -> text + structured JSON
    a bare int/list (typed) -> text + structured JSON wrapped as {"result": ...}
    ToolResult              -> exactly what you put in it, no conversion

Restriction: *args / **kwargs functions can't be tools -- the schema needs a
fixed, complete list of parameters.

Run:  uv run python 06_tools.py
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


# Decorator arguments override what FastMCP infers.
@mcp.tool(
    name="greet_formally",           # MCP name != function name
    description="Greets someone with their title.",   # overrides the docstring
    tags={"greeting", "formal"},     # for filtering (lesson 12)
    meta={"version": "1.2"},         # static metadata for the client UI
    timeout=30.0,                    # seconds; error -32000 if exceeded
)
def formal_greeting_impl(name: str, title: str | None = None) -> str:
    """Ignored, because description= was supplied."""
    return f"Good day, {title or 'Dr.'} {name}."


# ------------------------------------------- 2. describing the arguments
# Three ways to tell the LLM what an argument means. Explicit beats docstring.
@mcp.tool
def greet_with_options(
    name: str,
    shout: bool = False,
    repeat: int = 1,
) -> str:
    """Greets someone, optionally shouting or repeating.

    Args:
        name: Who to greet.
        shout: Whether to greet in capital letters.
        repeat: How many times to repeat the greeting.
    """
    text = " ".join([f"Hello, {name}!"] * repeat)
    return text.upper() if shout else text


@mcp.tool
def greet_annotated(
    # (b) a bare string in Annotated == Field(description=...)
    name: Annotated[str, "Who to greet"],
    # (c) Field, when you also want constraints
    repeat: Annotated[int, Field(description="How many greetings", ge=1, le=100)] = 1,
    language: Annotated[Literal["en", "fr", "de"], Field(description="Greeting language")] = "en",
) -> str:
    """Shows Annotated shorthand and Field constraints."""
    hello = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}[language]
    return " ".join([f"{hello}, {name}!"] * repeat)


# ---------------------------------------- 3. hiding arguments with Depends
# Runtime values (user ids, credentials, connections) should not be in the
# schema at all. Depends() injects them and removes them from the schema.
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
    language: str


@mcp.tool
def greet_structured(name: str) -> Greeting:
    """Object-like returns always produce structuredContent."""
    return Greeting(text=f"Hello, {name}!", name=name, language="en")


@mcp.tool
def count_greetings(names: list[str]) -> int:
    """A non-object return gets wrapped: structuredContent = {"result": N}."""
    return len(names)


@mcp.tool
def count_no_hint(names: list[str]):
    """No return annotation -> no output schema -> content only."""
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
        # ToolError always reaches the client, even with mask_error_details=True
        raise ToolError("name cannot be empty")
    return f"Hello, {name}!"


# ------------------------------------------------------- 7. annotations
# Behavioural hints for the CLIENT UI -- they cost no prompt tokens and
# enforce nothing. readOnlyHint is the one clients actually act on (skipping
# confirmation prompts for safe calls).
@mcp.tool(
    annotations=ToolAnnotations(
        title="Greet Someone",
        readOnlyHint=True,     # reads, changes nothing
        idempotentHint=True,   # repeat calls == one call
        openWorldHint=False,   # internal data only
    )
)
def greet_safely(name: str) -> str:
    """Greets someone. Safe to call repeatedly."""
    return f"Hello, {name}!"


@mcp.tool(annotations=ToolAnnotations(destructiveHint=True))
def delete_greeting(name: str) -> dict:
    """Permanently removes a saved greeting."""
    return {"deleted": name}


# ---------------------------------------- 8. programmatic registration
def farewell(name: str) -> str:
    """Says goodbye to someone by name."""
    return f"Goodbye, {name}!"


mcp.add_tool(Tool.from_function(farewell, name="say_goodbye"))


async def main():
    async with Client(mcp) as client:
        tools = {t.name: t for t in await client.list_tools()}
        print("tools:", sorted(tools))

        # docstring Args: became per-parameter descriptions
        props = tools["greet_with_options"].input_schema["properties"]
        print("\ngreet_with_options arg descriptions:")
        for arg, spec in props.items():
            print(f"  {arg:<8} {spec.get('description')}")

        # Field constraints land in the schema the LLM reads
        rep = tools["greet_annotated"].input_schema["properties"]["repeat"]
        print("\nrepeat constraints:", {k: v for k, v in rep.items() if k in ("minimum", "maximum")})

        # Depends() removed `user` from the schema
        print("greet_me schema args:", list(tools["greet_me"].input_schema["properties"]))
        print("greet_me ->", (await client.call_tool("greet_me")).data)

        # structured vs content-only
        r = await client.call_tool("greet_structured", {"name": "Ada"})
        print("\nGreeting structured:", r.structured_content)
        r = await client.call_tool("count_greetings", {"names": ["a", "b", "c"]})
        print("int      structured:", r.structured_content, "  (wrapped in 'result')")
        r = await client.call_tool("count_no_hint", {"names": ["a", "b", "c"]})
        print("no hint  structured:", r.structured_content, "  content:", r.content[0].text)

        r = await client.call_tool("greet_verbose", {"name": "Ada"})
        print("\nToolResult content   :", r.content[0].text)
        print("ToolResult structured:", r.structured_content)

        r = await client.call_tool("greet_strict", {"name": " "}, raise_on_error=False)
        print("\nToolError ->", r.content[0].text)

        print("annotations on greet_safely:", tools["greet_safely"].annotations)
        print("say_goodbye('Ada') ->", (await client.call_tool("say_goodbye", {"name": "Ada"})).data)

    # removing a tool at runtime (fires tools/list_changed inside a request)
    mcp.local_provider.remove_tool("delete_greeting")
    async with Client(mcp) as client:
        print("\nafter remove_tool:", "delete_greeting" in [t.name for t in await client.list_tools()])


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Give greet a Pydantic model parameter (e.g. Recipient(name, title)). Note
#    it must arrive as a JSON object, not a JSON string -- even in flexible mode.
# 2. Give `greet` a version="2" and register a second `greet`. Both survive:
#    identity is (type, name, version), so only an exact triple is a duplicate.
# 3. Try @mcp.tool(timeout=1.0, run_in_thread=False) on a sync function --
#    it is rejected at registration, because inline sync code can't be cancelled.
# 4. Return fastmcp.utilities.types.Image(path="x.png") and inspect the content
#    block type.
