"""Lifespan & state -- data that outlives one function call
=================================================================

    REQUEST STATE   one request    ctx.set_state / get_state       (04, 06)
    SESSION STATE   across calls   SessionId / UserSession          "shopping cart"
    LIFESPAN        whole server   setup -> yield -> teardown       templates, DB pools

    start ──► lifespan setup ──► [request] [request] [request] ──► lifespan teardown
                                  each reads ctx.lifespan_context

LIFESPAN   @lifespan generator; combine with `|`; use try/finally so teardown runs.
           Old @asynccontextmanager style: wrap in ContextManagerLifespan(...) to use `|`.
           Under FastAPI: combine_lifespans(app_lifespan, mcp.http_app().lifespan)

SESSIONS   the protocol is stateless, so state lives in a server-side STORE:
           SessionId    id is a tool argument; needs add_provider(SessionProvider())
                        (adds create_session / end_session tools)
           UserSession  one bucket per AUTHENTICATED user -- errors without auth
           without auth a session id is just a bearer token -> single-tenant only

STORES     MemoryStore (dev, lost on restart) | FileTreeStore (one server) |
           RedisStore (many servers, supports expiry)

Level: INTERMEDIATE
Run:  uv run python intermediate/07_lifespan_and_state.py      (from mcp/server)
"""

import asyncio

from fastmcp import Client, Context, FastMCP
from fastmcp.server.dependencies import get_session
from fastmcp.server.lifespan import lifespan
from fastmcp.server.sessions import SessionId, SessionProvider
from key_value.aio.stores.memory import MemoryStore


# ================================================================ lifespan
@lifespan
async def load_templates(server):
    print("  [startup] loading templates")
    try:
        yield {"templates": {"en": "Hello, {name}!", "fr": "Bonjour, {name}!"}}
    finally:
        print("  [shutdown] releasing templates")


@lifespan
async def load_config(server):
    yield {"default_language": "fr"}


mcp = FastMCP("GreetingService", lifespan=load_templates | load_config,   # `|` merges both dicts
              session_state_store=MemoryStore())                         # RedisStore in prod
mcp.add_provider(SessionProvider())


@mcp.tool
def greet(name: str, ctx: Context) -> str:
    """Uses templates loaded ONCE at startup."""
    lc = ctx.lifespan_context
    return lc["templates"][lc["default_language"]].format(name=name)


# =========================================================== session state
@mcp.tool
async def add_to_list(name: str, session_id: SessionId) -> int:
    session = await get_session(session_id)
    names = await session.get("names", default=[])      # also: .set(k, v), .clear()
    await session.set("names", names + [name])
    return len(names) + 1


@mcp.tool
async def read_list(session_id: SessionId) -> list[str]:
    return await (await get_session(session_id)).get("names", default=[])


async def main():
    async with Client(mcp) as c:
        print("greet       ->", (await c.call_tool("greet", {"name": "Ada"})).data)

        sid = (await c.call_tool("create_session", {})).data
        await c.call_tool("add_to_list", {"name": "Ada", "session_id": sid})
        await c.call_tool("add_to_list", {"name": "Bob", "session_id": sid})    # a separate request
        print("session     ->", (await c.call_tool("read_list", {"session_id": sid})).data)
        r = await c.call_tool("read_list", {"session_id": "made-up"}, raise_on_error=False)
        print("made-up id  -> is_error =", r.is_error)


if __name__ == "__main__":
    asyncio.run(main())
