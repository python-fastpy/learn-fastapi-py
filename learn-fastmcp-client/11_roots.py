"""Lesson 11 -- Roots: telling the server which folders it may look at
=========================================================================

A root is a filesystem location -- a project directory, a workspace -- that
you make available to the server. The server reads them to scope its own
work; without any roots, a server either treats its own working directory
as the boundary, or has to ask the user directly.

Two ways to configure them on the client:

    Client(mcp, roots=["file:///path/to/project"])   a fixed list

    async def roots_callback(context) -> list[str]:
        return ["file:///path/to/project"]            # computed on demand
    Client(mcp, roots=roots_callback)

Either way, this works across both protocol eras automatically: older
servers pull roots with a live request mid-call; newer servers get them
back as part of a call's result and the client answers and retries for you.
You don't need to know which one a given server uses.

Run:  uv run python 11_roots.py
"""

import asyncio

from fastmcp import Client
from target_server import mcp


# --------------------------------------------------------------- 1. static
async def demo_static():
    async with Client(mcp, roots=["file:///workspace/project"]) as client:
        result = await client.call_tool("list_client_roots", {})
        print("static roots ->", result.data)


# ------------------------------------------------------------- 2. callback
async def roots_callback(context) -> list[str]:
    print(f"  [server asked for roots, request id {context.request_id}]")
    return ["file:///workspace/project", "file:///workspace/docs"]


async def demo_callback():
    async with Client(mcp, roots=roots_callback) as client:
        result = await client.call_tool("list_client_roots", {})
        print("callback roots ->", result.data)


async def main():
    await demo_static()
    await demo_callback()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Make the callback return a DIFFERENT list depending on the request id
#    or some external state -- that's why a callback exists instead of a
#    fixed list.
# 2. Pass no `roots` at all and call list_client_roots -- what comes back?
# 3. Read learn-fastmcp-server lesson 09's Context reference: the server
#    side of this call is just another InputRequiredResult round, same as
#    elicitation and sampling.
