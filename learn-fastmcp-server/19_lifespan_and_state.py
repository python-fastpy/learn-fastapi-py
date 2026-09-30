"""Lesson 19 -- Lifespan, storage backends, session state
=========================================================

Three layers of "state that isn't just this one function call", from
shortest-lived to longest-lived.

    LIFESPAN         once per SERVER    shared setup, e.g. loaded templates
    REQUEST STATE    once per REQUEST   middleware writes it, the handler
                                         reads it (lessons 09 / 18)
    SESSION STATE    ACROSS requests    the "shopping cart" problem: data
                                         that must survive between calls

WHY SESSION STATE NEEDS SPECIAL HANDLING: the modern MCP protocol is
stateless -- every request gets a fresh connection, so nothing can be
stored "on the connection" anymore. FastMCP instead gives you a handle
(UserSession for an authenticated user, or SessionId for an explicit id)
backed by a server-side store.

ISOLATION: storage keys are the USER first, then the session id. Two users
sending the same session id never see each other's data. But WITHOUT auth,
a session id is just a bearer token -- treat it as single-tenant.

STORAGE BACKENDS: MemoryStore (default, lost on restart) for dev, or
FileTreeStore / RedisStore to persist across restarts and processes.

Run:  uv run python 19_lifespan_and_state.py
"""

import asyncio
from contextlib import asynccontextmanager

from fastmcp import Client, Context, FastMCP
from fastmcp.server.lifespan import ContextManagerLifespan, lifespan
from key_value.aio.stores.memory import MemoryStore


# ================================================================ 1. lifespan
@lifespan
async def templates_lifespan(server):
    """Runs ONCE when the server starts, however many clients connect."""
    print("  [lifespan] loading greeting templates")
    templates = {"en": "Hello, {name}!", "fr": "Bonjour, {name}!"}
    try:
        yield {"templates": templates}
    finally:
        # try/finally so teardown still runs if the server is cancelled
        print("  [lifespan] releasing greeting templates")


@lifespan
async def config_lifespan(server):
    """A second, independent lifespan."""
    print("  [lifespan] reading config")
    try:
        yield {"config": {"default_language": "en", "version": "1.0"}}
    finally:
        print("  [lifespan] discarding config")


# Compose with | -- enter left to right, exit right to left, contexts merged.
mcp = FastMCP("GreetingService", lifespan=templates_lifespan | config_lifespan)


@mcp.tool
def greet(name: str, language: str | None = None, ctx: Context = None) -> str:
    """Greets someone using a template loaded at startup."""
    templates = ctx.lifespan_context["templates"]
    default = ctx.lifespan_context["config"]["default_language"]
    return templates[language or default].format(name=name)


@mcp.tool
def list_languages(ctx: Context) -> list[str]:
    """Which languages the startup templates cover."""
    return sorted(ctx.lifespan_context["templates"])


async def demo_lifespan():
    async with Client(mcp) as c:
        print("greet('Ada')          ->", (await c.call_tool("greet", {"name": "Ada"})).data)
        print("greet('Ada', 'fr')    ->",
              (await c.call_tool("greet", {"name": "Ada", "language": "fr"})).data)
        print("list_languages        ->", (await c.call_tool("list_languages")).data)

    # A legacy @asynccontextmanager lifespan still works if passed directly,
    # but it CANNOT be piped with | until you wrap it.
    @asynccontextmanager
    async def legacy(server):
        yield {"legacy": True}

    legacy_only = FastMCP("Legacy", lifespan=legacy)

    @legacy_only.tool
    def whats_loaded(ctx: Context) -> dict:
        """Reads the legacy lifespan's context."""
        return dict(ctx.lifespan_context)

    async with Client(legacy_only) as c:
        print("\nlegacy @asynccontextmanager ->", (await c.call_tool("whats_loaded")).data)

    combined = ContextManagerLifespan(legacy) | config_lifespan
    print("wrapped for composition     ->", type(combined).__name__)

    # Mounting under FastAPI needs the OTHER helper, from a different module:
    #   from fastmcp.utilities.lifespan import combine_lifespans
    #   mcp_app = mcp.http_app()
    #   app = FastAPI(lifespan=combine_lifespans(app_lifespan, mcp_app.lifespan))
    #   app.mount("/mcp", mcp_app)


# ========================================================= 2. session state
async def demo_sessions():
    """UserSession needs auth. SessionId works without it -- as a bearer handle."""
    from fastmcp.server.dependencies import get_session
    from fastmcp.server.sessions import SessionId, SessionProvider, UserSession

    store = MemoryStore()          # swap for RedisStore in production
    shop = FastMCP("GreetingShop", session_state_store=store)

    # SessionProvider mints the ids. Register it whenever a tool takes a
    # session_id -- without it no id can be created, every id is rejected,
    # and sessions never resolve.
    shop.add_provider(SessionProvider())

    @shop.tool
    async def remember_name(name: str, session: UserSession) -> str:
        """One bucket per authenticated user. `session` is NOT in the schema."""
        names = await session.get("names", default=[])
        names.append(name)
        await session.set("names", names)
        return f"Remembered {len(names)} names."

    @shop.tool
    async def add_to_greeting_list(name: str, session_id: SessionId) -> str:
        """Many buckets. session_id IS in the schema -- the agent passes it."""
        session = await get_session(session_id)
        names = await session.get("names", default=[])
        names.append(name)
        await session.set("names", names)
        return f"{len(names)} names on this list."

    @shop.tool
    async def read_greeting_list(session_id: SessionId) -> list[str]:
        """Same id, later request -> same data. That is the whole point."""
        session = await get_session(session_id)
        return await session.get("names", default=[])

    async with Client(shop) as c:
        tools = {t.name: t for t in await c.list_tools()}
        print("\nUserSession is injected, not an argument:")
        print("  remember_name schema      :",
              list(tools["remember_name"].input_schema["properties"]))
        print("  add_to_greeting_list schema:",
              list(tools["add_to_greeting_list"].input_schema["properties"]))
        desc = tools["add_to_greeting_list"].input_schema["properties"]["session_id"].get("description")
        print("  ^ FastMCP describes session_id for the agent:")
        print("   ", (desc or "")[:100], "...")

        # UserSession without authentication: fails loudly rather than guessing
        r = await c.call_tool("remember_name", {"name": "Ada"}, raise_on_error=False)
        print("\n  UserSession with no auth  -> isError =", r.is_error)
        if r.is_error:
            print("    ", r.content[0].text[:95])

        # SessionId: create an id, then carry it across SEPARATE calls
        tool_names = sorted(tools)
        print("\n  session tools available   :", tool_names)
        r = await c.call_tool("create_session", {}, raise_on_error=False)
        if r.is_error:
            print("  create_session ->", r.content[0].text[:90])
            return
        sid = r.data if isinstance(r.data, str) else r.structured_content
        print("  create_session            ->", sid)

        sid_value = sid if isinstance(sid, str) else next(iter(sid.values()))
        print("  add 'Ada'                 ->",
              (await c.call_tool("add_to_greeting_list",
                                 {"name": "Ada", "session_id": sid_value})).data)
        print("  add 'Bob' (new request)   ->",
              (await c.call_tool("add_to_greeting_list",
                                 {"name": "Bob", "session_id": sid_value})).data)
        print("  read back                 ->",
              (await c.call_tool("read_greeting_list", {"session_id": sid_value})).data)

        # An id that was never minted -- or belongs to someone else -- raises
        r = await c.call_tool("read_greeting_list",
                              {"session_id": "not-a-real-id"}, raise_on_error=False)
        print("  a made-up id              -> isError =", r.is_error,
              "(a typo or stolen id fails loudly)")

    print(
        "\n  Session API: await session.get(k, default=None) / .set(k, v) / .clear()\n"
        "  Values are JSON-serialised. FastMCP sets no expiry of its own -- wrap\n"
        "  the store (e.g. TTLClampWrapper) if sessions should expire automatically.\n"
    )


# ====================================================== 3. storage backends
def describe_backends() -> None:
    print(
        "\n--- storage backends ---\n"
        "  MemoryStore()     default; fast; lost on restart; single process only\n"
        "  FileTreeStore(..) persists to disk; no extra services needed\n"
        "  RedisStore(...)   multi-instance, supports expiry\n"
        "\n  Used by: session_state_store (above), response caching (lesson 18),\n"
        "  and OAuth token storage. Rule of thumb: Memory for dev, File for one\n"
        "  durable server, Redis (or similar) once you have several servers.\n"
    )


async def main():
    await demo_lifespan()
    await demo_sessions()
    describe_backends()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Swap the composition order (config_lifespan | templates_lifespan) and
#    watch the startup/shutdown prints reverse.
# 2. Give both lifespans a "config" key. The later one wins -- merged dicts,
#    later values overwrite earlier.
# 3. Drop the try/finally from templates_lifespan, then interrupt the server
#    mid-run. Teardown no longer prints.
# 4. Try to pipe the bare @asynccontextmanager with | and read the error.
#    Then wrap it in ContextManagerLifespan.
# 5. Remove shop.add_provider(SessionProvider()) -- no id can be minted, so
#    every session_id is rejected.
# 6. Point session_state_store at a FileTreeStore, restart the script, and
#    confirm the list survives. (MemoryStore does not.)
