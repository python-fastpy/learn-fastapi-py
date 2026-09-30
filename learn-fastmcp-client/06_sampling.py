"""Lesson 06 -- Sampling: lending the server your LLM
=======================================================

A server can ask YOUR client to run a piece of text through an LLM, instead
of holding its own API key. You supply a `sampling_handler`; the server
sends messages, your handler runs them through a real model, and returns
the text. The server pays nothing and holds no credentials -- you do.

    async def sampling_handler(messages, params, context) -> str:
        ...           # call your LLM here, return its text

    Client(mcp, sampling_handler=sampling_handler)

`messages` is the conversation the server wants completed. `params` carries
generation settings (system_prompt, temperature, max_tokens, ...). Returning
a plain string is enough -- FastMCP wraps it into the protocol result for you.

FastMCP also ships ready-made handlers for OpenAI, Anthropic and Gemini --
pass one of those instead of writing your own.

Run:  uv run python 06_sampling.py
"""

import asyncio

from fastmcp import Client
from mcp.types import TextContent
from target_server import mcp


async def sampling_handler(messages, params, context) -> str:
    """Stands in for a real LLM call -- swap this body for your provider."""
    prompt = next(
        (m.content.text for m in messages if isinstance(m.content, TextContent)), ""
    )
    print(f"  [your LLM was asked]: {prompt}")
    return "Wishing you the brightest of days ahead!"


async def main():
    async with Client(mcp, sampling_handler=sampling_handler) as client:
        result = await client.call_tool("greet_creatively", {"name": "Ada"})
        print("\ngreet_creatively ->", result.data)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Swap the handler body for a real call to your LLM provider's SDK.
# 2. Raise an exception inside sampling_handler -- the client sends the
#    error back in place of a completion, and the tool has to handle it.
# 3. Pass sampling_capabilities=SamplingCapability() if your handler can
#    only return text, so the server knows not to send it tool-calling
#    requests it can't fulfil.
