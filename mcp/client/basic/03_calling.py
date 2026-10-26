"""Calling tools, resources and prompts -- from the client side
=====================================================================

Same pattern for all three: DISCOVER, then USE. Each has a convenient method
and a raw `_mcp` twin that returns the protocol object untouched.

    TOOLS       list_tools()               call_tool(name, args)       call_tool_mcp(...)
    RESOURCES   list_resources()           read_resource(uri)          read_resource_mcp(...)
                list_resource_templates()  (fill {params} into the URI yourself)
    PROMPTS     list_prompts()             get_prompt(name, args)      get_prompt_mcp(...)

A call_tool() result has a face for each reader:

    result.data                a real Python value  -> your code
    result.content             MCP content blocks   -> what an LLM sees
    result.structured_content  the raw JSON dict, before .data's conversion
    result.is_error            True on failure (only with raise_on_error=False)

read_resource() returns a LIST (one resource can have several representations):
    TextResourceContents -> .text     BlobResourceContents -> .blob (base64)

Level: BASIC
Run:  uv run python basic/03_calling.py
"""

import asyncio

from fastmcp import Client
from fastmcp.exceptions import ToolError
from greet_server import mcp


async def tools(client: Client):
    print("TOOLS")
    print("  list_tools    ->", sorted(t.name for t in await client.list_tools()))
    page = await client.list_tools_mcp()            # one raw page; page by hand with the cursor
    print("  list_tools_mcp-> next_cursor =", page.next_cursor)

    r = await client.call_tool("greet", {"name": "Ada"})
    print("  .data              :", r.data)
    print("  .content[0].text   :", r.content[0].text)
    print("  .structured_content:", r.structured_content)

    # attach metadata for your own tracing (the tool's arguments don't change)
    r = await client.call_tool("greet", {"name": "Ada"}, meta={"trace_id": "demo-123"})
    print("  with meta          :", r.data)

    try:                                            # timeout in seconds
        await client.call_tool("greet_slowly", {"names": ["A"] * 50}, timeout=0.01)
    except Exception as e:
        print("  timeout            ->", type(e).__name__)

    try:                                            # default: errors RAISE
        await client.call_tool("greet", {"name": " "})
    except ToolError as e:
        print("  ToolError          ->", e)

    r = await client.call_tool("greet", {"name": " "}, raise_on_error=False)   # or inspect them
    print("  raise_on_error=False -> is_error =", r.is_error)

    raw = await client.call_tool_mcp("greet", {"name": "Ada"})   # never raises, no .data
    print("  call_tool_mcp      ->", type(raw).__name__, "| is_error =", raw.is_error)


async def resources(client: Client):
    print("\nRESOURCES")
    print("  list_resources          ->", [str(r.uri) for r in await client.list_resources()])
    print("  list_resource_templates ->", [t.uri_template for t in await client.list_resource_templates()])

    content = await client.read_resource("data://greeting")
    print("  data://greeting ->", content[0].text, f"({content[0].mime_type})")
    content = await client.read_resource("greet://Ada")     # template: param goes in the URI
    print("  greet://Ada     ->", content[0].text)
    print("  read_resource_mcp ->", type(await client.read_resource_mcp("data://greeting")).__name__)


async def prompts(client: Client):
    print("\nPROMPTS")
    for p in await client.list_prompts():
        print(f"  {p.name}({', '.join(a.name for a in p.arguments or [])})")

    result = await client.get_prompt("ask_greeting", {"name": "Ada"})
    for m in result.messages:                       # ready-to-send messages, not a value
        print(f"  [{m.role}] {m.content.text}")
    print("  get_prompt_mcp ->", type(await client.get_prompt_mcp("ask_greeting", {"name": "Ada"})).__name__)


async def main():
    async with Client(mcp) as client:
        await tools(client)
        await resources(client)
        await prompts(client)


if __name__ == "__main__":
    asyncio.run(main())
