"""Context -- talking back to the CLIENT, and reaching the rest of the SERVER
==================================================================================

Context is the handle a tool/resource/prompt uses while it runs:

    your tool/resource/prompt
         │
         ├─► the CLIENT   ctx.info/warning(msg)       logging
         │                ctx.report_progress(...)    progress bar
         │
         └─► the SERVER   ctx.read_resource(uri)       read another component
                          ctx.get_state/set_state(k)   per-request state
                          ctx.request_id, .client_id   who's calling

THREE WAYS TO GET IT
    ctx: Context = CurrentContext()   preferred; hidden from the client schema
    ctx: Context                      older style; the parameter NAME doesn't matter
    get_context()                     call from a plain helper with no ctx param

PROGRESS + LOGGING are fire-and-forget NOTIFICATIONS -- and SILENT if nobody listens:
    report_progress()  no-op (no error) if the client didn't ask for progress
                       total=None -> "unknown length", just count up
                       multi-stage: give each stage a slice of 0-100
    ctx.debug/info/warning/error/log(level=...)  -> the CLIENT
                       logger_name="vip", extra={...} for structured fields
                       (extra keys can't be LogRecord names: name, msg, message...)
                       dropped below FastMCP(client_log_level=...)  (08_configuration)
    get_logger(__name__)  -> YOUR server logs; never leaves the process
  Never rely on either for something the tool NEEDS -- return it instead.
  (The logging capability is deprecated in the 2026-07-28 spec; calls still work.)

Note: sampling and ctx.elicit() (asking the client something mid-call) are
NOT reliable here -- the modern protocol removed that channel.
intermediate/05_server_requests.py covers the replacement pattern.

Level: BASIC
Run:  uv run python basic/04_context.py              (from mcp/server)
Test in Inspector:  uv run fastmcp dev inspector basic/04_context.py
"""

import asyncio
import json

from fastmcp import Client, FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.server.dependencies import get_context, get_http_headers
from fastmcp.server.middleware import Middleware
from fastmcp.utilities.logging import get_logger

mcp = FastMCP("GreetingService")


@mcp.resource("data://greeting-config")
def greeting_config() -> dict:
    return {"template": "Hello, {name}!"}


@mcp.prompt
def ask_greeting(name: str) -> str:
    """Ask for a greeting."""
    return f"Write a greeting for {name}."


# ------------------------------------------------- 1. the preferred access
@mcp.tool
async def greet_from_config(name: str, ctx: Context = CurrentContext()) -> dict:
    """Read a resource, log, and report progress -- all via ctx."""
    await ctx.info(f"Greeting {name} using data://greeting-config")
    result = await ctx.read_resource("data://greeting-config")
    config = json.loads(result.contents[0].content)
    await ctx.report_progress(progress=50, total=100)
    greeting = config["template"].format(name=name)
    await ctx.report_progress(progress=100, total=100)
    return {"greeting": greeting}


# ------------------------- 1b. unknown-length progress + structured logs
log = get_logger(__name__)          # server-side only -- the client never sees this


@mcp.tool
async def scan_for_names(ctx: Context = CurrentContext()) -> int:
    """No known total: omit `total` and just count upward."""
    for found in (2, 4, 6):
        await ctx.report_progress(progress=found, message=f"found {found} names")
    await ctx.info("scan done", logger_name="scanner", extra={"found": 6, "source": "demo"})
    log.info("this line stays in the server's own logs")
    return 6


# ------------------------------------------- 2. legacy type-hint injection
@mcp.tool
async def whoami(anything: Context) -> dict:
    """The parameter NAME doesn't matter -- only the Context type hint does."""
    return {
        "request_id": anything.request_id,
        "client_id": anything.client_id,
        "transport": anything.transport,
        "server": anything.fastmcp.name,
    }


# ------------------------------------------- 3. get_context() in a helper
async def _audit(action: str) -> str:
    """A plain function, no ctx parameter -- it reaches OUT for the context."""
    ctx = get_context()               # RuntimeError if called outside a request
    await ctx.warning(f"audit: {action}")
    return ctx.request_id


@mcp.tool
async def greet_audited(name: str) -> str:
    """The tool never touches Context directly; its helper does."""
    await _audit(f"greeted {name}")
    return f"Hello, {name}!"


# --------------------------------------------------------- 4. request state
# State carries values across the middleware -> handler pipeline WITHIN one
# request only. Use set_state(k, v, serializable=False) for live objects
# (connections, clients). For anything spanning multiple requests, use session state
# (intermediate/07_lifespan_and_state.py). Middleware itself: 06_middleware_and_di.py.
@mcp.tool
async def greet_caller(ctx: Context = CurrentContext()) -> str:
    """Greets whoever the middleware said is calling."""
    caller = await ctx.get_state("caller")
    return f"Hello, {caller}!"


class CallerMiddleware(Middleware):
    """Minimal middleware that stamps state onto every tool call."""

    async def on_call_tool(self, context, call_next):
        await context.fastmcp_context.set_state("caller", "Ada")
        return await call_next(context)


mcp.add_middleware(CallerMiddleware())


# --------------------------------------------- 5. discovery from inside a tool
@mcp.tool
async def introspect(ctx: Context = CurrentContext()) -> dict:
    """A tool can list and render the server's OWN resources and prompts."""
    rendered = await ctx.get_prompt("ask_greeting", {"name": "Ada"})
    return {
        "resources": [str(r.uri) for r in await ctx.list_resources()],
        "prompts": [p.name for p in await ctx.list_prompts()],
        "rendered": rendered.messages[0].content.text,
    }


# -------------------------------------------------------- 6. HTTP fallback
@mcp.tool
async def greet_user_agent() -> str:
    """get_http_headers() works under HTTP transport, even with no MCP session."""
    headers = get_http_headers()
    return f"Hello, {headers.get('user-agent', 'unknown client')}!"


# --------------------------------------------------------- 7. the elicitation wall
@mcp.tool
async def greet_in_chosen_language(ctx: Context = CurrentContext()) -> str:
    """ctx.elicit() pushes a question down the connection and waits -- the
    modern protocol removed that channel, so this fails regardless of
    whether the client registered a handler for it."""
    result = await ctx.elicit("Which language?", response_type=["en", "fr"])
    return f"user {result.action}ed" if result.action != "accept" else f"Hello in {result.data}!"


async def main():
    logs, progress = [], []

    async def log_handler(m):
        logs.append(m.level if m.logger is None else f"{m.level}:{m.logger} {m.data.get('extra')}")

    async def progress_handler(progress_val, total, message):
        progress.append(f"{progress_val:g}/{total:g}" if total else f"{progress_val:g}/?")

    async def elicitation_handler(message, response_type, params, ctx):
        return "fr"   # a handler IS registered -- it still won't be reached

    async with Client(
        mcp, log_handler=log_handler, progress_handler=progress_handler,
        elicitation_handler=elicitation_handler,
    ) as client:
        r = await client.call_tool("greet_from_config", {"name": "Ada"})
        print("greet_from_config ->", r.data, "| logs:", logs, "| progress:", progress)
        logs.clear(); progress.clear()
        await client.call_tool("scan_for_names")
        print("scan_for_names    -> progress:", progress, "| logs:", logs)

        print("whoami        ->", (await client.call_tool("whoami")).data)
        print("greet_audited ->", (await client.call_tool("greet_audited", {"name": "Ada"})).data)
        print("greet_caller  ->", (await client.call_tool("greet_caller")).data, "(name set by middleware)")
        print("introspect    ->", (await client.call_tool("introspect")).data)
        print("user agent    ->", (await client.call_tool("greet_user_agent")).data)

        try:
            await client.call_tool("greet_in_chosen_language")
        except Exception as e:
            print(f"\nelicitation blocked by protocol era -> {type(e).__name__}")


if __name__ == "__main__":
    asyncio.run(main())
