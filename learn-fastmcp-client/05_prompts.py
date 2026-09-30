"""Lesson 05 -- Getting prompts from a client
==============================================

A prompt is a reusable message template. The server owns the wording; you
supply the arguments and get back ready-to-send MESSAGES, not a result for
your code to use.

    list_prompts()          what's available, and their arguments
    get_prompt(name, args)  render one -> GetPromptResult, with .messages

Arguments can be plain values -- FastMCP serializes anything more complex
(dataclasses, dicts, lists) for you.

Run:  uv run python 05_prompts.py
"""

import asyncio

from fastmcp import Client
from target_server import mcp


async def main():
    async with Client(mcp) as client:
        # 1. discover
        for p in await client.list_prompts():
            args = [a.name for a in (p.arguments or [])]
            print(f"{p.name}({', '.join(args)})")

        # 2. render it
        result = await client.get_prompt("ask_greeting", {"name": "Ada"})
        print("\nmessages:")
        for m in result.messages:
            text = m.content.text if hasattr(m.content, "text") else m.content
            print(f"  [{m.role}] {text}")

        # 3. the raw protocol result
        raw = await client.get_prompt_mcp("ask_greeting", {"name": "Ada"})
        print("\nget_prompt_mcp ->", type(raw).__name__)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Call get_prompt with a missing required argument and read the error.
# 2. Add a second prompt to target_server.py that returns list[Message]
#    (a short conversation) and print every message's role.
# 3. In a multi-server client (lesson 02), a prompt name gets prefixed too
#    -- try get_prompt("greet_ask_greeting", ...) against that config.
