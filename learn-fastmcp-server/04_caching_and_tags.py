"""Lesson 04 -- Response caching + tag-based filtering
=====================================================

Two ways to control what the client gets. Four greeting tools, tagged
differently, are the whole cast.

  CACHING -- "keep this answer fresh for N seconds" (a hint, not a
  guarantee: nothing is cached unless the client opts in).
     cache_ttl=300              how many seconds an answer stays fresh
     cache_scope="public"       shared across everyone, vs "private" (default)

  TAG FILTERING -- which components exist at all, for this server.
     @mcp.tool(tags={"public"})               label a component
     mcp.enable(tags={"public"}, only=True)   allowlist: ONLY these show
     mcp.disable(tags={"internal"})           hide these
     Later calls override earlier ones, so chain: enable(only=True).disable(...)

  IMPORTANT: filtering covers listing AND calling, but it is a DEFAULT, not
  a security boundary -- a later enable() can bring a component back. If
  something must never be reachable, don't register it, or use auth
  (lesson 05).

Run:  uv run python 04_caching_and_tags.py
"""

import asyncio

from fastmcp import Client, FastMCP


def build(*, configure=None) -> FastMCP:
    """One server, four tagged greeting tools; `configure` applies a filter."""
    mcp = FastMCP("GreetingService")

    @mcp.tool(tags={"public", "utility"})
    def greet(name: str) -> str:
        """Greets someone by name. Anyone may call this."""
        return f"Hello, {name}!"

    @mcp.tool(tags={"internal", "admin"})
    def greet_as_admin(name: str) -> str:
        """Greets with admin privileges."""
        return f"Greetings, Administrator {name}."

    @mcp.tool(tags={"internal"})
    def greet_debug(name: str) -> str:
        """Internal plumbing for greetings."""
        return f"[debug] greet({name!r})"

    @mcp.tool(tags={"admin", "deprecated"})
    def greet_old(name: str) -> str:
        """Superseded by greet_as_admin."""
        return f"Hi, {name}."

    if configure:
        configure(mcp)
    return mcp


async def names(mcp: FastMCP) -> list[str]:
    async with Client(mcp) as client:
        return sorted(t.name for t in await client.list_tools())


async def main():
    # -------------------------------------------------------- tag filtering
    print("no filter                      :", await names(build()))

    # allowlist: only components tagged "public" survive
    print(
        "enable(tags={public}, only=True):",
        await names(build(configure=lambda m: m.enable(tags={"public"}, only=True))),
    )

    # denylist: drop anything tagged internal or deprecated
    print(
        "disable({internal, deprecated}) :",
        await names(build(configure=lambda m: m.disable(tags={"internal", "deprecated"}))),
    )

    # combine -- order matters, the disable subtracts from the allowlist
    print(
        "enable({admin}).disable({dep.}) :",
        await names(
            build(configure=lambda m: m.enable(tags={"admin"}, only=True).disable(tags={"deprecated"}))
        ),
    )

    # filtering governs access too, not just listing
    filtered = build(configure=lambda m: m.disable(tags={"internal"}))
    async with Client(filtered) as client:
        r = await client.call_tool("greet_as_admin", {"name": "Ada"}, raise_on_error=False)
        print("\ncalling a hidden tool          : isError =", r.is_error)

    # ------------------------------------------------------------- caching
    print("\n--- response caching ---")
    cached = FastMCP("GreetingService", cache_ttl=300, cache_scope="public")

    @cached.tool
    def greet(name: str) -> str:
        """Greets someone by name."""
        return f"Hello, {name}!"

    async with Client(cached) as client:
        r = await client.call_tool("greet", {"name": "Ada"})
        print("cache_ttl=300, cache_scope='public' -> greet:", r.data)

    # a scope with no TTL does not enable caching, so it is rejected outright
    try:
        FastMCP("Broken", cache_scope="public")
    except ValueError as e:
        print("cache_scope without cache_ttl ->", e)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Swap the order in the combined example -- disable first, then enable(only=True).
#    Which tools survive, and why?
# 2. Add components={"tool"} to a disable() call so only tools are filtered,
#    leaving resources and prompts visible.
# 3. Use disable(names={"greet_as_admin"}) instead of tags. Then call enable()
#    afterwards -- confirm for yourself that the "default, not a guarantee"
#    warning in the docs is literal.
