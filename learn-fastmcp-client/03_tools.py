"""Lesson 03 -- Calling tools from a client
============================================

Two ways to discover tools, and two ways to call one:

    list_tools()          the full catalog, paged for you automatically
    list_tools_mcp()       one raw page at a time, if you want to page by hand

    call_tool(name, args)      convenient: raises on error, gives you .data
    call_tool_mcp(name, args)  raw: never raises, gives you the protocol result

A `call_tool()` result has several faces, each for a different reader:

    result.data                the value, already converted to a real Python
                                object (a dict, a dataclass, a plain string...)
    result.content             the raw MCP content blocks (mostly text)
    result.structured_content  the plain JSON dict, before .data's conversion
    result.is_error            True if the tool failed (only when raise_on_error=False)

Run:  uv run python 03_tools.py
"""

import asyncio

from fastmcp import Client
from fastmcp.exceptions import ToolError
from target_server import mcp


async def main():
    async with Client(mcp) as client:
        # 1. discover
        tools = await client.list_tools()
        print("tools:", sorted(t.name for t in tools))

        # 2. the convenient way -- raises ToolError on failure
        result = await client.call_tool("greet", {"name": "Ada"})
        print("\ncall_tool ->")
        print("  .data              :", result.data)
        print("  .content[0].text   :", result.content[0].text)
        print("  .structured_content:", result.structured_content)

        # 3. a timeout -- aborts if the call takes too long
        try:
            await client.call_tool("greet_slowly", {"names": ["A"] * 50}, timeout=0.01)
        except Exception as e:
            print("\ntimeout ->", type(e).__name__)

        # 4. handling failure with a try/except
        try:
            await client.call_tool("nonexistent_tool", {})
        except ToolError as e:
            print("\nToolError ->", e)

        # 5. handling failure without exceptions
        raw = await client.call_tool("nonexistent_tool", {}, raise_on_error=False)
        print("raise_on_error=False -> is_error =", raw.is_error)

        # 6. the raw protocol result -- no .data, no automatic unwrapping
        raw = await client.call_tool_mcp("greet", {"name": "Ada"})
        print("\ncall_tool_mcp ->", raw.content[0].text, "| is_error =", raw.is_error)

        # 7. attach metadata to a call (for your own logging/tracing, not the tool)
        result = await client.call_tool(
            "greet", {"name": "Ada"}, meta={"trace_id": "demo-123"}
        )
        print("\nmeta attached, call still returns ->", result.data)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Call a tool with the wrong argument types (e.g. {"name": 123}) and see
#    whether it fails before or after reaching the server.
# 2. Use list_tools_mcp() directly and print its next_cursor.
# 3. Pass a per-call progress_handler to call_tool("greet_slowly", ...) --
#    lesson 09 covers what it receives.
