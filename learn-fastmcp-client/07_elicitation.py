"""Lesson 07 -- Elicitation: answering a server's question mid-call
======================================================================

Some tools need to ask the user something before they can finish -- approve
a draft, pick an option. You supply an `elicitation_handler`; the client
calls it automatically whenever the server asks, and the server sees the
answer on its next turn (this is the guard pattern from
learn-fastmcp-server lesson 15, from the CLIENT's side).

    async def elicitation_handler(message, response_type, params, context):
        ...
        return response_type(field=value)     # accept, with data
        # or: return ElicitResult(action="decline")   # or "cancel"

    Client(mcp, elicitation_handler=elicitation_handler)

- `message` is the question text.
- `response_type` is a ready-made class matching the server's requested
  shape -- construct it with the field(s) it asks for, and returning it is
  treated as an implicit "accept".
- Use `ElicitResult(action=...)` yourself for an explicit decline/cancel.

Run:  uv run python 07_elicitation.py
"""

import asyncio

from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult
from target_server import mcp


async def elicitation_handler(message, response_type, params, context):
    print(f"  [server asks]: {message}")
    if "Approve" in message:
        return response_type(approved=True)          # implicit accept
    return ElicitResult(action="decline")


async def main():
    async with Client(mcp, elicitation_handler=elicitation_handler) as client:
        result = await client.call_tool("greet_with_approval", {"name": "Ada"})
        print("\ngreet_with_approval ->", result.data)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Change the handler to return ElicitResult(action="decline") always,
#    and read what greet_with_approval returns instead.
# 2. Print `params.requested_schema` inside the handler -- that's the JSON
#    Schema response_type was generated from.
# 3. Add a second question to target_server.py's tool (ask for a language
#    too) and answer both in one round using two keys in input_requests.
