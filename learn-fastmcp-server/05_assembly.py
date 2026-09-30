"""Lesson 05 -- Assembly: middleware, lifespan, providers, transforms, auth
===========================================================================

A quick OVERVIEW of five ways a FastMCP server is *assembled* rather than
written by hand. Lessons 10-14 go deep on each one.

    middleware=[...]   intercepts every message (logging, timing, limits)
    providers=[...]    WHERE components come from (a DB, an API, another
                        server) -- besides your own @mcp.tool decorators
    transforms=[...]   how components are PRESENTED (rename, hide, reshape)
    lifespan=...        startup/shutdown code that wraps all of the above
    auth=...            gates HTTP transports before any request runs

Order of the pipeline for one request: middleware -> transforms -> the
component itself (local or from a provider).

Run:  uv run python 05_assembly.py
"""

import asyncio
import time
from contextlib import asynccontextmanager

from fastmcp import Client, FastMCP
from fastmcp.server.middleware import Middleware, MiddlewareContext
from fastmcp.server.providers import FastMCPProvider
from fastmcp.server.transforms import Namespace


# ------------------------------------------------------------- MIDDLEWARE
# Middleware wraps every request/response. Typical jobs: logging, timing,
# rate limiting. Hook names mirror the protocol methods (on_call_tool,
# on_list_tools, ...) -- lesson 18 covers all of them.
class TimingMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        start = time.perf_counter()
        result = await call_next(context)          # let the tool run
        ms = (time.perf_counter() - start) * 1000
        print(f"  [middleware] {context.message.name} took {ms:.1f}ms")
        return result

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        tools = await call_next(context)
        print(f"  [middleware] listed {len(tools)} tools")
        return tools


# --------------------------------------------------------------- LIFESPAN
# Code before `yield` runs once at startup; code after runs at shutdown.
# Open connection pools here, not at import time (lesson 19 goes deeper).
@asynccontextmanager
async def lifespan(server: FastMCP):
    print("  [lifespan] startup: loading greeting templates")
    yield {"templates": {"en": "Hello, {name}!"}}   # available via the context
    print("  [lifespan] shutdown: releasing greeting templates")


# --------------------------------------------------------------- PROVIDERS
# A provider supplies components dynamically -- queried at request time,
# so it can pull from a database, an API, or another MCP server (lesson 13).
upstream = FastMCP("Upstream")


@upstream.tool
def greet_in(language: str, name: str) -> str:
    """Greets someone in a given language."""
    hello = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}.get(language, "Hello")
    return f"{hello}, {name}!"


# -------------------------------------------------------------- TRANSFORMS
# A transform changes how components are *presented*, without touching
# their code. Namespace prefixes every name, so two upstreams that both
# export "greet" can be combined without colliding. More in lessons 10-12.
mcp = FastMCP(
    "GreetingService",
    middleware=[TimingMiddleware()],
    providers=[FastMCPProvider(upstream)],
    transforms=[Namespace(prefix="intl")],
    lifespan=lifespan,
    # auth=...        # an AuthProvider; secures HTTP transports only (see below)
    experimental_capabilities={"draftFeature": {"enabled": True}},
)


@mcp.tool
def greet(name: str) -> str:
    """Greets someone in English -- defined right here, next to the provider's tool."""
    return f"Hello, {name}!"


async def main():
    async with Client(mcp) as client:
        # Namespace is server-WIDE: the provider's greet_in and the local
        # greet both come back prefixed.
        tools = sorted(t.name for t in await client.list_tools())
        print("tools (local + provider, both namespaced):", tools)

        r = await client.call_tool("intl_greet_in", {"language": "fr", "name": "Ada"})
        print("intl_greet_in('fr', 'Ada') ->", r.data)

        # experimental_capabilities advertises draft/interop features to the
        # client without touching the derived tools/resources capabilities.
        print("experimental capabilities:", client.server_capabilities.experimental)

    print(
        "\nauth (HTTP transports only -- STDIO is already a trust boundary):\n"
        "  mcp = FastMCP('Secure', auth=JWTVerifier(jwks_uri=..., issuer=...))\n"
        "  mcp.run(transport='http')\n"
        "Unlike tag filtering (lesson 04), auth IS a real security boundary.\n"
    )


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Add a second middleware that prints before TimingMiddleware. Which runs
#    outermost -- first or last in the list?
# 2. Remove the Namespace transform. What are the tool names now?
# 3. Read the lifespan dict from inside greet() via the request context.
# 4. Point FastMCPProvider at a *remote* server instead of an in-process one.
