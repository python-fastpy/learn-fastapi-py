"""Lesson 10 -- Logging: receiving a server's log messages
=============================================================

A tool can log while it runs (`ctx.info(...)` etc., on the server side --
see learn-fastmcp-server lesson 16). On the client, catch those messages
with a `log_handler`:

    async def log_handler(message: LogMessage):
        ...

    Client(mcp, log_handler=log_handler)

A `LogMessage` has three fields:

    message.level    "debug" | "info" | "notice" | "warning" | "error" |
                      "critical" | "alert" | "emergency"
    message.logger   an optional name for where it came from
    message.data     usually a dict with "msg" and "extra"

If you pass no log_handler at all, FastMCP quietly forwards these into
Python's own `logging` module instead (with `notice` mapped to INFO, and
`alert`/`emergency` mapped to CRITICAL) -- so logs are never silently lost,
just harder to see unless you configure `logging`.

Run:  uv run python 10_logging.py
"""

import asyncio

from fastmcp import Client
from fastmcp.client.logging import LogMessage
from target_server import mcp


async def log_handler(message: LogMessage) -> None:
    msg = message.data.get("msg") if isinstance(message.data, dict) else message.data
    print(f"  [{message.level}] {msg}")


async def main():
    async with Client(mcp, log_handler=log_handler) as client:
        result = await client.call_tool("greet_slowly", {"names": ["Ada"]})
        print("\ngreet_slowly ->", result.data)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Remove log_handler entirely and call the same tool -- configure Python's
#    `logging.basicConfig(level=logging.INFO)` first and watch the message
#    appear there instead.
# 2. Add `extra={"user": "ada"}` to a server-side log call and print it from
#    message.data["extra"] here.
# 3. Log something at "debug" from the server and set
#    FastMCP(client_log_level="warning") there -- confirm it never arrives.
