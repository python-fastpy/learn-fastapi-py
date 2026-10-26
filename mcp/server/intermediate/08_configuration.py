"""Configuration -- the FastMCP(...) knobs, plus client-UI extras
=======================================================================

BEHAVIOUR (constructor arguments)
    on_duplicate="replace"         same name twice: warn (default) | replace | error | ignore
    strict_input_validation=True   reject "3" for an int (default coerces it)
    mask_error_details=True        hide exception text from clients -- USE IN PRODUCTION
    client_log_level="warning"     drop ctx.debug/info before they reach the client
    list_page_size=50              page long lists with a cursor (worth it > ~100 items)
    cache_ttl=300, cache_scope=    a freshness HINT for clients; scope needs a ttl
    dereference_schemas, experimental_capabilities, session_state_store (07), tasks (11)

CLIENT-UI EXTRAS
    @mcp.completion   suggest values while the user types a prompt/template argument
                      (one handler per server; branch on ref + argument.name)
    icons=[Icon(src=..., theme="light"|"dark")]   server, tools, resources, prompts
    website_url=...

Level: INTERMEDIATE
Run:  uv run python intermediate/08_configuration.py      (from mcp/server)
"""

import asyncio

from fastmcp import Client, Context, FastMCP
from mcp.types import Icon, PromptReference

mcp = FastMCP(
    "GreetingService",
    on_duplicate="replace",
    strict_input_validation=True,
    mask_error_details=True,
    client_log_level="warning",
    list_page_size=2,
    website_url="https://greetings.example.com",
    icons=[Icon(src="https://example.com/icon.png", sizes=["48x48"])],
)


@mcp.tool(name="greet")
def greet_v1(name: str) -> str:
    return f"Hello, {name}!"


@mcp.tool(name="greet", icons=[Icon(src="https://example.com/light.png", theme="light"),
                               Icon(src="https://example.com/dark.png", theme="dark")])
def greet_v2(name: str) -> str:              # same name -> REPLACES greet_v1
    return f"Hi there, {name}!"


@mcp.tool
async def greet_many(name: str, times: int, ctx: Context) -> str:
    await ctx.info("dropped by client_log_level")
    await ctx.warning("delivered")
    if times > 100:
        raise ValueError("secret internal detail")       # masked for the client
    return " ".join([f"Hello, {name}!"] * times)


@mcp.tool
def farewell(name: str) -> str:
    return f"Bye, {name}!"


@mcp.prompt
def greet_in_style(style: str) -> str:
    return f"Write a {style} greeting."


@mcp.completion
async def complete(ref, argument, context):
    if isinstance(ref, PromptReference) and argument.name == "style":
        return [s for s in ["formal", "friendly", "funny"] if s.startswith(argument.value)]
    return None


async def main():
    logs = []

    async def log_handler(m):
        logs.append(m.level)

    async with Client(mcp, log_handler=log_handler) as c:
        print("on_duplicate=replace ->", (await c.call_tool("greet", {"name": "Ada"})).data)

        r = await c.call_tool("greet_many", {"name": "Ada", "times": "3"}, raise_on_error=False)
        print('strict, times="3"    -> is_error =', r.is_error)
        r = await c.call_tool("greet_many", {"name": "Ada", "times": 500}, raise_on_error=False)
        print("masked error         ->", r.content[0].text)
        print("client_log_level     -> received", logs)

        page = await c.list_tools_mcp()
        print("list_page_size=2     ->", len(page.tools), "tools, cursor:", page.next_cursor is not None)

        r = await c.complete(PromptReference(type="ref/prompt", name="greet_in_style"),
                             {"name": "style", "value": "f"})
        print('completion "f"       ->', r.values)

        greet = next(t for t in await c.list_tools() if t.name == "greet")
        print("icons                ->", c.server_info.website_url, [i.theme for i in greet.icons])

    try:
        FastMCP("Broken", cache_scope="public")           # caching: scope without ttl
    except ValueError as e:
        print("cache_scope, no ttl  ->", e)


if __name__ == "__main__":
    asyncio.run(main())
