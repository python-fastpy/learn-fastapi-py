"""Lesson 12 -- Notifications: hearing about changes you didn't ask for
==========================================================================

Progress, logging, sampling and elicitation each have their own handler
because the server is asking YOU something. Notifications are different:
they're fire-and-forget announcements -- "my tool list just changed" --
that need no answer. Catch them with a `message_handler`.

TWO STYLES

    async def message_handler(message):        # one function, branch yourself
        if message.method == "notifications/tools/list_changed":
            ...
    Client(mcp, message_handler=message_handler)

    class MyHandler(MessageHandler):            # one method per notification
        async def on_tool_list_changed(self, notification):
            ...
    Client(mcp, message_handler=MyHandler())

Other hooks on `MessageHandler`: `on_resource_list_changed`,
`on_prompt_list_changed`, `on_resource_updated`, `on_progress`,
`on_logging_message`, `on_cancelled`, plus the catch-alls `on_message` and
`on_notification`.

Run:  uv run python 12_notifications.py
"""

import asyncio

from fastmcp import Client
from fastmcp.client.messages import MessageHandler
from target_server import mcp


# ------------------------------------------------------- 1. plain function
async def demo_function_handler():
    async def message_handler(message):
        if getattr(message, "method", None) == "notifications/tools/list_changed":
            print("  [function handler] tool list changed")

    async with Client(mcp, message_handler=message_handler) as client:
        await client.call_tool("add_translate_tool", {})
        await asyncio.sleep(0.05)   # give the notification a moment to arrive


# --------------------------------------------------------- 2. subclass
class ToolCacheInvalidator(MessageHandler):
    """Keeps its own cache, cleared whenever the tool list changes."""

    def __init__(self):
        self.cached_tools: list[str] | None = None

    async def on_tool_list_changed(self, notification) -> None:
        print("  [subclass handler] clearing cached tool list")
        self.cached_tools = None


async def demo_subclass_handler():
    handler = ToolCacheInvalidator()
    async with Client(mcp, message_handler=handler) as client:
        handler.cached_tools = sorted(t.name for t in await client.list_tools())
        print("cached before:", len(handler.cached_tools), "tools")

        await client.call_tool("add_translate_tool", {})
        await asyncio.sleep(0.05)
        print("cache cleared? ->", handler.cached_tools is None)


async def main():
    await demo_function_handler()
    await demo_subclass_handler()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Add on_resource_list_changed to ToolCacheInvalidator and trigger it by
#    adding a resource at runtime, the same way add_translate_tool does.
# 2. Try to ANSWER a sampling or elicitation request from inside
#    message_handler -- it's the wrong place; use sampling_handler /
#    elicitation_handler instead, since this handler is notifications-only.
# 3. Log every message.method that arrives during a normal call_tool(),
#    to see the full notification traffic for one call.
