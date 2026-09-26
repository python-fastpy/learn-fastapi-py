"""Lesson 03 -- Logging in MCP Servers
======================================

An MCP server can log in two places (three cases):

  1. SERVER LOG   log.info("...")        -> the server's terminal (stderr) / Datadog
                                            for YOU, the developer
  2. CLIENT LOG   await ctx.info("...")  -> sent over MCP to the client, which
                                            receives it in its log_handler
  3. LOG LEVELS   debug < info < warning < error
                  log.setLevel("WARNING") hides server INFO lines

  ┌──────────── MCP SERVER ─────────────┐
  │ greet("Shubham") runs:              │
  │                                     │    stderr     ┌─────────────────────────┐
  │   1. log.info("greet called ...") ──┼─────────────► │ server terminal/Datadog │
  │      (filtered by log.setLevel) 3.  │               │ for YOU, the developer  │
  │                                     │               └─────────────────────────┘
  │   2. await ctx.info("Greeting ...") │
  │         │                           │
  └─────────┼───────────────────────────┘
            │ MCP notification  {"method": "notifications/message",
            │                    "params": {"level": "info", "data": {...}}}
            ▼  (travels with the other MCP messages -- stdio or HTTP)
  ┌──────────── MCP CLIENT ─────────────┐
  │ Client(mcp, log_handler=show_log)   │
  │   show_log(message) is called:      │
  │   "client got [info] Greeting ..."  │  -> the app shows it in its UI or logs
  └─────────────────────────────────────┘

  Never print() in a stdio server: stdout carries the MCP messages, so a stray
  print corrupts them. Logs go to stderr, a separate channel.

Run:  uv run python 03_logging.py

Maps to: story-drafting/src/main.py (server logs as JSON lines for Datadog)
"""

import asyncio
from fastmcp import FastMCP, Client, Context
from fastmcp.utilities.logging import get_logger

log = get_logger("greet")                 # fastmcp's server logger ("fastmcp.greet")
mcp = FastMCP("learn-mcp-logging")


@mcp.tool
async def greet(name: str, ctx: Context) -> str:
    """Greet someone by name."""
    # ctx is injected by FastMCP -- the LLM never sees it as an argument.
    log.info(f"greet called with name={name!r}")          # 1. server log
    await ctx.info(f"Greeting {name}")                     # 2. client log

    if not name.strip():                                   # 3. a higher level
        log.warning("empty name received")
        await ctx.warning("Empty name -- greeting a stranger")
        return "Hello, stranger!"
    return f"Hello, {name}!"


async def show_client_log(message):
    """The client's log_handler: called for every log the server sends."""
    # For `await ctx.info(f"Greeting {name}")`, message looks like:
    #
    #   LoggingMessageNotificationParams(
    #       level="info",                                     # ctx.info -> "info", ctx.warning -> "warning"
    #       logger=None,                                      # optional logger name
    #       data={"msg": "Greeting Shubham", "extra": None},  # your text is under "msg"
    #   )
    #
    # On the wire it arrived as an MCP notification (no "id", so no reply):
    #   {"jsonrpc": "2.0", "method": "notifications/message",
    #    "params": {"level": "info", "data": {"msg": "Greeting Shubham", "extra": null}}}
    print(f"   client got [{message.level}] {message.data['msg']}")


async def main():
    async with Client(mcp, log_handler=show_client_log) as client:
        # 1 + 2. One call produces BOTH logs:
        #   server terminal: INFO  greet called with name='Shubham'
        #                    DEBUG Sending INFO to client: Greeting Shubham   <- fastmcp's own trace
        #   client         : client got [info] Greeting Shubham
        r = await client.call_tool("greet", {"name": "Shubham"})
        print("1+2. result:", r.data)

        # 3. Raise the server log level: INFO lines disappear, WARNING stays.
        #    Client logs are unaffected -- they're a separate channel.
        log.setLevel("WARNING")
        r = await client.call_tool("greet", {"name": " "})
        print("3.   result:", r.data)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Add `await ctx.debug(...)` to greet. Does the client print it?
# 2. Add log.error(...) for a name longer than 50 characters.
# 3. Production logs one JSON object per line (for Datadog). Give `log` a
#    handler whose formatter outputs JSON and compare the output.
