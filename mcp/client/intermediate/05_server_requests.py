"""Server requests -- when the SERVER asks the CLIENT for something  (intermediate)
=========================================================================================

Usually the client asks and the server answers. Here it's reversed: mid-call,
the server needs something only the client has.

    SAMPLING     "run this through YOUR LLM"       sampling_handler(messages, params, ctx) -> str
    ELICITATION  "ask YOUR USER this question"     elicitation_handler(message, response_type, params, ctx)
    ROOTS        "which folders may I use?"        roots=[...]  or  roots=callback(ctx) -> list[str]

How it flows (you only write the handler; the client does the rest):

    client                                   server tool
    call_tool("greet_with_approval") ──────► no answer yet -> RETURNS the question
             ◄─────────────────────────────  InputRequiredResult("Approve?")
    elicitation_handler(...) -> approved=True
    call_tool again, with the answer ──────► ctx.input_responses has it -> finishes
             ◄─────────────────────────────  "Hello, Ada!"

SAMPLING     the server holds no API key -- you lend it your model. Return a plain
             string. FastMCP ships ready-made handlers for OpenAI, Anthropic, Gemini.
ELICITATION  return response_type(field=...) to accept, or
             ElicitResult(action="decline" | "cancel").
ROOTS        a fixed list, or a callback when the answer depends on state.

Level: INTERMEDIATE   (server side: ../server/intermediate/05_server_requests.py)
Run:  uv run python intermediate/05_server_requests.py
"""

import asyncio

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult
from mcp.types import TextContent
from greet_server import mcp


# --------------------------------------------------------------- 1. sampling
async def sampling_handler(messages, params, context) -> str:
    """Stands in for a real LLM call -- swap the body for your provider's SDK."""
    prompt = next((m.content.text for m in messages if isinstance(m.content, TextContent)), "")
    print(f"  [your LLM was asked] {prompt}")
    return "Wishing you the brightest of days, Ada!"


# ------------------------------------------------------------ 2. elicitation
async def approve(message, response_type, params, context):
    print(f"  [server asks] {message}")
    return response_type(approved=True)            # implicit "accept"


async def decline(message, response_type, params, context):
    return ElicitResult(action="decline")


# ------------------------------------------------------------------ 3. roots
async def roots_callback(context) -> list[str]:
    return ["file:///workspace/project", "file:///workspace/docs"]


async def main():
    print("SAMPLING")
    async with Client(mcp, sampling_handler=sampling_handler) as client:
        print("  greet_creatively ->", (await client.call_tool("greet_creatively", {"name": "Ada"})).data)

    print("\nELICITATION")
    async with Client(mcp, elicitation_handler=approve) as client:
        print("  accepted ->", (await client.call_tool("greet_with_approval", {"name": "Ada"})).data)
    async with Client(mcp, elicitation_handler=decline) as client:
        print("  declined ->", (await client.call_tool("greet_with_approval", {"name": "Ada"})).data)

    print("\nROOTS")
    async with Client(mcp, roots=["file:///workspace/project"]) as client:
        print("  fixed list ->", (await client.call_tool("list_client_roots", {})).data)
    async with Client(mcp, roots=roots_callback) as client:
        print("  callback   ->", (await client.call_tool("list_client_roots", {})).data)


if __name__ == "__main__":
    asyncio.run(main())
