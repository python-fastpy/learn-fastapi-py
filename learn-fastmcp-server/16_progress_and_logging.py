"""Lesson 16 -- Progress and logging: telling the client what's happening
=========================================================================

Both are NOTIFICATIONS: fire-and-forget messages that don't need a reply,
so -- unlike elicitation and sampling in lesson 15 -- they still work
everywhere. Here we greet a whole list of people, reporting progress as we go.

    PROGRESS                             LOGGING
    await ctx.report_progress(           await ctx.debug(msg)
        progress=3,   # done so far          ctx.info(msg)
        total=10,     # optional scope       ctx.warning(msg)
    )                                        ctx.error(msg)

Both are SILENT BY DEFAULT if nobody's listening: report_progress() does
nothing (no error) if the client never asked for progress updates, and
logs below the client_log_level floor (lesson 03) are simply dropped.
Never rely on either for something your tool actually needs to happen.

Note: ctx.* logging sends to the CLIENT. For your own server-side logs, use
fastmcp.utilities.logging.get_logger() instead -- that never leaves the process.

Run:  uv run python 16_progress_and_logging.py
"""

import asyncio
import logging

from fastmcp import Client, Context, FastMCP
from fastmcp.utilities.logging import get_logger

mcp = FastMCP("GreetingService")

# Your own server-side logger -- never leaves the process.
log = get_logger(__name__)


# ------------------------------------------------------- 1. progress in a loop
@mcp.tool
async def greet_everyone(names: list[str], ctx: Context) -> dict:
    """Greet a list of people, reporting progress after each one."""
    total = len(names)
    greetings = []

    for i, name in enumerate(names):
        await ctx.report_progress(progress=i, total=total, message=f"Greeting {name}")
        await asyncio.sleep(0.01)
        greetings.append(f"Hello, {name}!")

    # a final call at progress == total marks the job complete
    await ctx.report_progress(progress=total, total=total)
    return {"greeted": len(greetings), "greetings": greetings}


# ---------------------------------------------- 2. indeterminate + multi-stage
@mcp.tool
async def scan_for_names(ctx: Context) -> int:
    """No known endpoint -- omit `total` and just count upward."""
    found = 0
    for _ in range(3):
        found += 2
        await ctx.report_progress(progress=found, message=f"found {found} names")
    return found


@mcp.tool
async def build_greeting_cards(ctx: Context) -> str:
    """Four stages, each owning a slice of one 0-100 range."""
    stages = [("validating names", 0, 25), ("rendering cards", 25, 60),
              ("translating", 60, 80), ("packaging", 80, 100)]
    for name, start, end in stages:
        await ctx.report_progress(progress=start, total=100, message=name)
        await asyncio.sleep(0.01)
        await ctx.report_progress(progress=end, total=100, message=f"{name} done")
    return "cards ready"


# ------------------------------------------------------------- 3. log levels
@mcp.tool
async def greet_with_logs(names: list[str], ctx: Context) -> dict:
    """Greet a list of people, logging at every level."""
    await ctx.debug("Starting to greet the supplied names")
    await ctx.info(f"Greeting {len(names)} people")

    try:
        if not names:
            await ctx.warning("Empty name list provided")
            return {"error": "Empty name list"}

        greetings = [f"Hello, {n}!" for n in names]
        await ctx.info(f"Greeted {len(greetings)} people")
        return {"greeted": len(greetings)}

    except Exception as e:
        await ctx.error(f"Greeting failed: {str(e)}")
        raise


# ------------------------------------------- 4. structured logs + logger_name
@mcp.tool
async def greet_vip(name: str, tier: str, ctx: Context) -> str:
    """`extra` attaches structured fields to a log entry; `logger_name` labels
    where it came from. ctx.log() is the general form behind debug/info/etc.

    Gotcha: `extra` keys land on a Python LogRecord, so they can't reuse its
    reserved attribute names (`name`, `message`, `msg`, `levelname`, ...).
    extra={"name": name} raises an error -- use a different key, like below.
    """
    await ctx.info(
        f"Greeting VIP {name}",
        logger_name="vip",
        extra={"recipient": name, "tier": tier, "channel": "greeting"},
    )
    # the same call, spelled explicitly
    await ctx.log("greeting delivered", level="notice", logger_name="vip")

    log.info("this one stays on the server -- the client never sees it")
    return f"A very warm hello, {name}!"


async def main():
    received_logs: list[tuple] = []
    progress_events: list[str] = []

    async def log_handler(message):
        received_logs.append((message.level, message.logger, message.data))

    async def progress_handler(progress, total, message):
        progress_events.append(f"{progress:g}/{total if total is not None else '?'} {message or ''}")

    async with Client(mcp, log_handler=log_handler, progress_handler=progress_handler) as client:
        r = await client.call_tool("greet_everyone", {"names": ["Ada", "Bob", "Cleo"]})
        print("greet_everyone ->", r.data)
        print("  progress events:", progress_events)

        progress_events.clear()
        await client.call_tool("scan_for_names")
        print("\nindeterminate (no total):", progress_events)

        progress_events.clear()
        await client.call_tool("build_greeting_cards")
        print("multi-stage slices     :", progress_events)

        print("\nlogging")
        r = await client.call_tool("greet_with_logs", {"names": ["Ada", "Bob"]})
        print("  greet_with_logs ->", r.data)
        for level, logger, data in received_logs:
            print(f"    {level:<8} logger={logger} {data.get('msg')}")

        received_logs.clear()
        await client.call_tool("greet_vip", {"name": "Ada", "tier": "gold"})
        print("\n  structured:")
        for level, logger, data in received_logs:
            print(f"    {level:<8} logger={logger!r:<7} msg={data.get('msg')!r} extra={data.get('extra')}")

        # an empty list takes the warning branch
        received_logs.clear()
        r = await client.call_tool("greet_with_logs", {"names": []})
        print("\n  empty input ->", r.data, "| levels:", [lv for lv, _, _ in received_logs])

    # No handlers at all: both features go quiet, nothing raises.
    async with Client(mcp) as client:
        r = await client.call_tool("greet_everyone", {"names": ["Ada"]})
        print("\nno client handlers -> tool still fine:", r.data)

    # Mirror what was sent to the client into your own server logs.
    to_client = get_logger(name="fastmcp.server.context.to_client")
    to_client.setLevel(logging.DEBUG)
    print("\nserver-side mirror logger:", to_client.name, "at", logging.getLevelName(to_client.level))


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Build the server with FastMCP(client_log_level="warning") (lesson 03) and
#    re-run greet_with_logs -- debug and info never leave the server.
# 2. Drop progress_handler and confirm report_progress() is a silent no-op:
#    no progressToken, no delivery, no error.
# 3. Report progress backwards (10 then 5). Nothing stops you -- the protocol
#    does not police monotonicity, so your client UI might jump.
# 4. Note the deprecation warning this file prints: the logging CAPABILITY is
#    deprecated as of 2026-07-28 (SEP-2577), even though the calls still work.
#    Anything you actually need should be a return value, not a log line.
# 5. Change greet_vip's extra back to {"name": name} and read the error:
#    extra keys share a namespace with LogRecord's own attributes.
