"""Lesson 09 -- MCP Context: talking back to the client mid-call
===============================================================

Context is the handle a tool/resource/prompt uses to reach MCP features
while it runs: logging, progress, reading other components, per-request
state, and who is calling. Every tool below still just greets someone.

THREE WAYS TO GET IT
    ctx: Context = CurrentContext()   preferred; hidden from the schema
    ctx: Context                      older style; the parameter name doesn't matter
    get_context()                     call from inside a helper with no ctx param

WHAT IT OFFERS
    logging    await ctx.debug/info/warning/error(msg)
    progress   await ctx.report_progress(progress=50, total=100)
    reading    await ctx.read_resource(uri), ctx.list_resources()
    state      await ctx.set_state(k, v) / get_state(k)
    who        ctx.request_id, ctx.client_id, ctx.transport

Note: sampling and ctx.elicit() (asking the client something mid-call) are
NOT reliable here -- the modern protocol removed that channel. Lesson 15
covers the replacement pattern.

Run:  uv run python 09_context.py
"""

import asyncio

from fastmcp import Client, FastMCP
from fastmcp.dependencies import CurrentContext
from fastmcp.server.context import Context
from fastmcp.server.dependencies import get_context, get_http_headers
from fastmcp.server.middleware import Middleware

mcp = FastMCP("GreetingService")


@mcp.resource("data://greeting-config")
def greeting_config() -> dict:
    return {"template": "Hello, {name}!", "language": "en"}


@mcp.prompt
def ask_greeting(name: str) -> str:
    """Ask for a greeting."""
    return f"Write a greeting for {name}."


# ------------------------------------------------- 1. the preferred access
@mcp.tool
async def greet_from_config(name: str, ctx: Context = CurrentContext()) -> dict:
    """Read the greeting template from a resource, logging and reporting progress."""
    await ctx.info(f"Greeting {name} using data://greeting-config")

    result = await ctx.read_resource("data://greeting-config")
    raw = result.contents[0].content if result.contents else "{}"
    await ctx.report_progress(progress=50, total=100)

    greeting = f"Hello, {name}!"
    await ctx.report_progress(progress=100, total=100)
    return {"greeting": greeting, "config_bytes": len(str(raw))}


# ------------------------------------------- 2. legacy type-hint injection
# The parameter NAME doesn't matter -- only the Context type hint does.
@mcp.tool
async def whoami(anything: Context) -> dict:
    """Request metadata. Guard request_context: it is None before a session."""
    return {
        "request_id": anything.request_id,
        "client_id": anything.client_id,
        "transport": anything.transport,
        "server": anything.fastmcp.name,
        "has_request_context": anything.request_context is not None,
    }


# ------------------------------------------- 3. get_context() in a helper
async def _audit(action: str) -> str:
    """A plain function, no ctx parameter -- it reaches out for the context."""
    ctx = get_context()               # RuntimeError if called outside a request
    await ctx.warning(f"audit: {action}")
    return ctx.request_id


@mcp.tool
async def greet_audited(name: str) -> str:
    """The tool never touches Context; its helper does."""
    await _audit(f"greeted {name}")
    return f"Hello, {name}!"


# --------------------------------------------------------- 4. request state
# State carries values across the middleware -> handler pipeline WITHIN one
# request. Use serializable=False for live objects (connections, clients);
# those live only for the current call. For anything spanning requests, use
# session state (FastMCP(session_state_store=...), lesson 03).
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
    """A tool can list and render the server's own resources and prompts."""
    resources = await ctx.list_resources()
    prompts = await ctx.list_prompts()
    rendered = await ctx.get_prompt("ask_greeting", {"name": "Ada"})
    return {
        "resources": [str(r.uri) for r in resources],
        "prompts": [p.name for p in prompts],
        "rendered": rendered.messages[0].content.text,
    }


# -------------------------------------------------------- 6. HTTP fallback
@mcp.tool
async def greet_user_agent() -> str:
    """get_http_headers() works under HTTP transport even with no MCP session."""
    headers = get_http_headers()
    return f"Hello, {headers.get('user-agent', 'unknown client')}!"


# --------------------------------------------------------- 7. elicitation
@mcp.tool
async def greet_in_chosen_language(ctx: Context = CurrentContext()) -> str:
    """Ask the user which language to greet in -- and hit the protocol wall.

    ctx.elicit() pushes a question down the open connection and waits. The
    modern protocol removed that channel, so this fails no matter what
    handler the client registered. Lesson 15 shows the replacement: return
    the question as your RESULT and let the client re-call you with the answer.
    """
    result = await ctx.elicit("Which language?", response_type=["en", "fr", "de"])
    if result.action != "accept":
        return f"user {result.action}ed"
    hello = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}[result.data]
    return f"{hello}, Ada!"


async def main():
    logs: list[str] = []
    progress: list[str] = []

    async def log_handler(m):
        logs.append(f"{m.level}: {m.data.get('msg') if isinstance(m.data, dict) else m.data}")

    async def progress_handler(progress_val, total, message):
        progress.append(f"{progress_val:g}/{total:g}")

    async def elicitation_handler(message, response_type, params, ctx):
        print(f"  [client] asked: {message} -> answering 'fr'")
        return "fr"

    async with Client(
        mcp,
        log_handler=log_handler,
        progress_handler=progress_handler,
        elicitation_handler=elicitation_handler,
    ) as client:
        r = await client.call_tool("greet_from_config", {"name": "Ada"})
        print("greet_from_config ->", r.data)
        print("  logs     :", logs)
        print("  progress :", progress)

        print("\nwhoami        ->", (await client.call_tool("whoami")).data)
        r = await client.call_tool("greet_audited", {"name": "Ada"})
        print("greet_audited ->", r.data, "(helper used get_context)")
        print("  logs now  :", logs[-1:])

        print("\ngreet_caller ->", (await client.call_tool("greet_caller")).data,
              "(name set by middleware)")
        print("introspect   ->", (await client.call_tool("introspect")).data)
        print("user agent   ->", (await client.call_tool("greet_user_agent")).data)

        # The client registered an elicitation_handler, yet this still fails:
        # on the modern protocol there is no channel for the server to ask.
        print("\nelicitation (server-initiated):")
        try:
            r = await client.call_tool("greet_in_chosen_language")
            print("  ->", r.data)
        except Exception as e:
            print(f"  blocked by protocol era -> {e}")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Call get_context() from a plain script (outside any request). Read the
#    RuntimeError -- that is the whole point of the function.
# 2. Store a non-serializable object with set_state(..., serializable=False).
# 3. Have a tool call ctx.send_notification(ToolListChangedNotification(...))
#    and watch it arrive in a client message_handler.
# 4. Run this file's server over HTTP (see lesson 02) and call
#    greet_user_agent with curl -- now the header is real.
