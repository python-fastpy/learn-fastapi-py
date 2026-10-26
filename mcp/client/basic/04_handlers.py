"""Handlers -- hearing from the server WHILE it works
===========================================================

The server side of these is ../server/04_context.py (ctx.info, ctx.report_progress).
On the client you pass a handler function; the client calls it as messages arrive.

    server                                client handler
    ctx.report_progress(...)  ─────────►  progress_handler(progress, total, message)
    ctx.info / warning(...)   ─────────►  log_handler(LogMessage)
    "tool list changed"       ─────────►  message_handler(message)   (notifications)

PROGRESS   set on the Client (every call) or per call_tool(..., progress_handler=)
           -- per-call wins. `total` may be None (unknown length: just count up).
LOGGING    LogMessage has .level ("debug".."emergency"), .logger, .data ({"msg", "extra"}).
           No log_handler? FastMCP forwards to Python's `logging` instead (never lost).
NOTIFICATIONS  fire-and-forget announcements that need no answer. Two styles:
           a plain function (branch on message.method), or a MessageHandler subclass
           with one method per kind: on_tool_list_changed, on_resource_list_changed,
           on_prompt_list_changed, on_resource_updated, on_progress,
           on_logging_message, on_cancelled (+ catch-alls on_message, on_notification).

Level: BASIC
Run:  uv run python basic/04_handlers.py
"""

import asyncio

from fastmcp import Client
from fastmcp.client.logging import LogMessage
from fastmcp.client.messages import MessageHandler
from greet_server import mcp


# ---------------------------------------------------- 1. progress + logging
async def progress_handler(progress: float, total: float | None, message: str | None):
    pct = f"{progress / total * 100:5.1f}%" if total else f"{progress:g}"
    print(f"  progress {pct}  {message or ''}")


async def log_handler(m: LogMessage):
    msg = m.data.get("msg") if isinstance(m.data, dict) else m.data
    print(f"  log [{m.level}] {msg}")


async def demo_progress_and_logging():
    async with Client(mcp, progress_handler=progress_handler, log_handler=log_handler) as client:
        r = await client.call_tool("greet_slowly", {"names": ["Ada", "Bob"]})
        print("greet_slowly ->", r.data)

        async def just_this_call(progress, total, message):     # overrides for ONE call
            print(f"  (per-call) {progress:g}/{total:g}")

        await client.call_tool("greet_slowly", {"names": ["Cleo"]}, progress_handler=just_this_call)


# ------------------------------------------------------- 2. notifications
async def demo_function_handler():
    async def message_handler(message):
        if getattr(message, "method", None) == "notifications/tools/list_changed":
            print("  [function] tool list changed")

    async with Client(mcp, message_handler=message_handler) as client:
        await client.call_tool("add_translate_tool", {})
        await asyncio.sleep(0.05)      # give the notification a moment to arrive


class ToolCache(MessageHandler):
    """Caches the tool list; clears it when the server says it changed."""

    def __init__(self):
        self.tools: list[str] | None = None

    async def on_tool_list_changed(self, notification):
        print("  [subclass] clearing cached tool list")
        self.tools = None


async def demo_subclass_handler():
    cache = ToolCache()
    async with Client(mcp, message_handler=cache) as client:
        cache.tools = [t.name for t in await client.list_tools()]
        await client.call_tool("add_translate_tool", {})
        await asyncio.sleep(0.05)
        print("cache cleared? ->", cache.tools is None)


async def main():
    print("PROGRESS + LOGGING")
    await demo_progress_and_logging()
    print("\nNOTIFICATIONS")
    await demo_function_handler()
    await demo_subclass_handler()


if __name__ == "__main__":
    asyncio.run(main())
