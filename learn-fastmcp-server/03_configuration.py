"""Lesson 03 -- Configuration: the behavior knobs
================================================

Each setting below is a FastMCP(...) constructor argument. None of them add
features -- they change how the server *behaves* when something is
ambiguous, wrong, too big, or needs to stick around. Same greet() tool
throughout; only the server settings change.

    on_duplicate             what to do when two components share one name
    strict_input_validation  reject mismatched types, or coerce them ("3" -> 3)
    mask_error_details       hide exception text from the client (production)
    list_page_size           page large lists instead of returning them at once
    client_log_level         the minimum log level the client will receive

Two more exist but aren't demoed here: `dereference_schemas` (flattens $ref
in JSON schemas) and `tasks` / `session_state_store` (covered in lessons 19-20).

Run:  uv run python 03_configuration.py
"""

import asyncio

from fastmcp import Client, Context, FastMCP


# -------------------------------------------------- on_duplicate: "replace"
# Default is "warn": register anyway, just log a warning. "replace" makes
# the second registration silently win -- handy when a plugin overrides a
# base tool. Other options: "error" (raise) and "ignore" (keep the first).
dup = FastMCP("DuplicateDemo", on_duplicate="replace")


@dup.tool(name="greet")
def greet_v1(name: str) -> str:
    """Version 1."""
    return f"Hello, {name}!"


@dup.tool(name="greet")
def greet_v2(name: str) -> str:
    """Version 2 -- replaces v1."""
    return f"Hi there, {name}!"


# ------------------------------------------ strict_input_validation + errors
# strict=False (default): the string "3" is coerced to the int 3.
# strict=True:             the input must already match the schema exactly.
# mask_error_details=True: the client gets a generic message instead of the
#                           real exception text -- use this in production.
lenient = FastMCP("Lenient", strict_input_validation=False)
strict = FastMCP("Strict", strict_input_validation=True, mask_error_details=True)


def greet_many(name: str, times: int) -> str:
    """Greets someone `times` times."""
    if times > 100:
        raise ValueError(f"secret internal detail: {times} exceeds the cap of 100")
    return " ".join([f"Hello, {name}!"] * times)


lenient.tool(greet_many)
strict.tool(greet_many)


# --------------------------------------------------------- list_page_size
# A positive int caps how many items one list call returns; the client pages
# through with a cursor. None (default) returns everything at once.
# Lesson 17 pages through a 120-tool server by hand.
paged = FastMCP("Paged", list_page_size=2)

for lang in ("en", "fr", "de", "es", "it"):
    paged.tool(name=f"greet_{lang}")(lambda: "ok")


# --------------------------------------------------------- client_log_level
# The minimum level a tool's ctx.debug/info/warning/error message needs to
# reach the client. With the floor at "warning", debug and info are dropped.
logged = FastMCP("Logged", client_log_level="warning")


@logged.tool
async def greet_noisily(name: str, ctx: Context) -> str:
    """Greets, and emits one log per level -- only warning and above arrive."""
    await ctx.debug("debug: dropped by the floor")
    await ctx.info("info: dropped by the floor")
    await ctx.warning("warning: delivered")
    return f"Hello, {name}!"


async def main():
    # ---- on_duplicate
    async with Client(dup) as c:
        r = await c.call_tool("greet", {"name": "Ada"})
        print("on_duplicate='replace' -> greet returns", r.data)

    # ---- coercion vs strict
    async with Client(lenient) as c:
        r = await c.call_tool("greet_many", {"name": "Ada", "times": "3"})   # a string
        print('lenient  times="3"   ->', r.data)

    async with Client(strict) as c:
        r = await c.call_tool("greet_many", {"name": "Ada", "times": "3"}, raise_on_error=False)
        print('strict   times="3"   -> isError =', r.is_error)

        # mask_error_details hides the exception text from the client only --
        # the server still logs the full traceback above.
        r = await c.call_tool("greet_many", {"name": "Ada", "times": 500}, raise_on_error=False)
        print("masked   times=500   ->", r.content[0].text)

    # ---- paging
    async with Client(paged) as c:
        page = await c.list_tools_mcp()                # one raw page
        print(f"\nlist_page_size=2 -> {len(page.tools)} tools, cursor = {page.next_cursor}")
        print("all tools (client pages for you):", sorted(t.name for t in await c.list_tools()))

    # ---- client_log_level floor
    received: list[str] = []

    async def log_handler(message):                    # must be async: it is awaited
        received.append(message.level)

    async with Client(logged, log_handler=log_handler) as c:
        await c.call_tool("greet_noisily", {"name": "Ada"})
    print("client_log_level='warning' -> levels received:", received)

    # ---- the rest, stated rather than demoed
    print(
        "\nalso available:\n"
        "  dereference_schemas=True  # default: flattens $ref in JSON schemas\n"
        "  tasks=True                # background jobs the client can poll (lesson 20)\n"
        "  session_state_store=...   # persist per-session data (lesson 19)\n"
    )


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Change on_duplicate to "error" -- where does it blow up, import or call?
# 2. Set mask_error_details=False on `strict` and re-read the times=500 output.
# 3. Set client_log_level="debug" and count the messages `received` again.
