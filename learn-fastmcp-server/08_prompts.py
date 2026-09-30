"""Lesson 08 -- Prompts in depth
===============================

A prompt is a reusable, parameterized message template. The server writes
the wording; the client supplies the arguments. Unlike a tool, a prompt
returns MESSAGES for the LLM to read, not a result for your code to use.
Every prompt here asks for a greeting.

    def ask_greeting(name) -> str    one user message
    def convo() -> list[Message]    a multi-turn conversation
    def rich() -> PromptResult      messages + description + metadata

Gotcha: the wire protocol only sends STRING arguments. A list[str] parameter
arrives as the JSON string '["Ada", "Bob"]', and FastMCP parses it back into
a real list for you. Keep argument types simple (list[str], dict[str,str],
float, bool) -- deep Pydantic models don't round-trip reliably this way.

Restriction: *args / **kwargs functions can't be prompts.

Run:  uv run python 08_prompts.py
"""

import asyncio

from fastmcp import Client, Context, FastMCP
from fastmcp.prompts import Message, PromptResult

mcp = FastMCP("GreetingService")


# -------------------------------------------------------- 1. a plain string
# A bare string becomes a single message with role "user".
@mcp.prompt
def ask_greeting(name: str) -> str:
    """Asks the LLM to write a greeting for someone."""
    return f"Write a warm, one-line greeting for someone called {name}."


# --------------------------------------------------- 2. a conversation
# Message(content, role="user"|"assistant"). Bare strings in the list are
# promoted to user messages.
@mcp.prompt
def greeting_conversation(name: str, language: str) -> list[Message]:
    """Sets up a two-turn exchange about greeting someone."""
    return [
        Message(f"Greet {name} in {language}, then explain the greeting."),
        Message("Happy to help -- here is the greeting.", role="assistant"),
    ]


# ------------------------------------------------- 3. decorator arguments
@mcp.prompt(
    name="greeting_style_request",
    description="Asks for a greeting in a particular style.",
    tags={"greeting", "style"},
    meta={"version": "1.1", "author": "greeting-team"},
)
def styled_greeting(name: str, style: str = "friendly") -> str:
    """Ignored, because description= was supplied."""
    return f"Write a {style} greeting for {name}."


# ------------------------------------------- 4. describing the arguments
# Google / NumPy / Sphinx docstring styles are all parsed. Returns/Raises/
# Example sections are dropped from the description.
@mcp.prompt
def greeting_for_occasion(name: str, occasion: str = "birthday") -> str:
    """Generate a greeting for a particular occasion.

    Args:
        name: Who the greeting is for.
        occasion: The occasion being celebrated (birthday, promotion, ...).
    """
    return f"Write a {occasion} greeting for {name}."


# ------------------------------------------------------- 5. typed arguments
@mcp.prompt
def greet_group(names: list[str], preferences: dict[str, str], warmth: float) -> str:
    """Greet several people at once."""
    return (
        f"Greet these {len(names)} people: {', '.join(names)}. "
        f"Preferences: {preferences}. Warmth level: {warmth}."
    )


# ----------------------------------------- 6. required vs optional + Context
@mcp.prompt
async def greeting_report_request(name: str, ctx: Context) -> str:
    """Prompts get Context too. ctx is injected, not a client argument."""
    return f"Summarise every greeting sent to {name}. Request ID: {ctx.request_id}"


# --------------------------------------------------------- 7. PromptResult
# Full control: messages + a render-time description + render-time meta.
# NOTE: a plain return inherits the definition's description; PromptResult
# uses only what you pass.
@mcp.prompt
def review_greeting(text: str) -> PromptResult:
    """Returns a greeting-review prompt with metadata."""
    return PromptResult(
        messages=[
            Message(f"Please review this greeting:\n\n{text}"),
            Message("I'll check the tone and phrasing.", role="assistant"),
        ],
        description="Greeting review prompt",
        meta={"review_type": "tone", "priority": "high"},
    )


async def main():
    async with Client(mcp) as client:
        print("prompts:")
        for p in await client.list_prompts():
            args = [f"{a.name}{'' if a.required else '?'}" for a in (p.arguments or [])]
            print(f"  {p.name:<25} ({', '.join(args)})")

        # docstring Args: became per-argument descriptions
        target = next(p for p in await client.list_prompts() if p.name == "greeting_for_occasion")
        print("\ngreeting_for_occasion arg descriptions:")
        for a in target.arguments:
            print(f"  {a.name:<9} required={str(a.required):<5} {a.description}")

        # the typed-argument schema the client is told to satisfy
        typed = next(p for p in await client.list_prompts() if p.name == "greet_group")
        print("\ngreet_group advertises:")
        for a in typed.arguments:
            print(f"  {a.name:<12} {a.description}")

        print("\nrenders")
        r = await client.get_prompt("ask_greeting", {"name": "Ada"})
        print("  string  ->", [(m.role, m.content.text) for m in r.messages])

        r = await client.get_prompt(
            "greeting_conversation", {"name": "Ada", "language": "French"}
        )
        print("  convo   ->")
        for m in r.messages:
            print(f"            [{m.role}] {m.content.text}")

        # arguments as JSON STRINGS -- what a real MCP client sends
        r = await client.get_prompt(
            "greet_group",
            {"names": '["Ada", "Bob"]', "preferences": '{"Ada": "formal"}', "warmth": "0.8"},
        )
        print("  typed (JSON strings) ->", r.messages[0].content.text)

        # the same prompt with real Python values also works in-process
        r = await client.get_prompt(
            "greet_group",
            {"names": ["Cleo"], "preferences": {"Cleo": "casual"}, "warmth": 1.0},
        )
        print("  typed (native)       ->", r.messages[0].content.text)

        r = await client.get_prompt("review_greeting", {"text": "Hello, Ada!"})
        print("\n  PromptResult description:", r.description)
        print("  PromptResult meta       :", r.meta)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Remove the default from `occasion` -- watch `required` flip to true.
# 2. Return Message({"greeting": "Hello"}) and see the dict serialized to JSON.
# 3. Add a prompt with a Pydantic model argument and try to call it with a JSON
#    string. This is the case the docs warn about.
