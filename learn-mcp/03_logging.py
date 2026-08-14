"""Lesson 03 -- Logging in MCP Servers
======================================

WHY THIS MATTERS:
  MCP tools run on remote servers — you can't set breakpoints or add print
  statements. Logging is your only window into what's happening. FastMCP has
  its own logger (for framework events) and you'll want a separate Python
  logger (for your tool logic). This lesson shows both.

WHAT YOU'LL LEARN:
  1. FastMCP's built-in logger (framework-level: tool dispatch, transport)
  2. Python's logging.getLogger for your own tool code
  3. How production uses JSON formatting for Datadog

Concepts:
  - FastMCP built-in logging: log_level, get_logger
  - Python logging inside tools
  - Production pattern: JSON formatter for Datadog (story-drafting/src/main.py)

FastMCP settings:
  log_level      -> "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
  log_enabled    -> True/False to toggle all FastMCP logging
  client_log_level -> minimum level sent to MCP clients

PREREQUISITES: Lesson 01 (server + tool basics)

Run:  uv run python 03_logging.py

EXPECTED OUTPUT:
  === MCP Logging Demo ===

  <timestamp> __main__ INFO greet called with name=Shubham
  (+ FastMCP DEBUG lines: tool dispatch, schema loading)

  Result: [TextContent(... "Hello, Shubham!" ...)]

  --- Log level set to WARNING (fewer logs) ---

  (no INFO/DEBUG logs -- only WARNING+ would appear)

  Result: [TextContent(... "Hello, Shubham!" ...)]
"""

import asyncio
import logging
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client
from fastmcp.utilities.logging import get_logger

# FastMCP's own logger -- lives under "fastmcp." namespace
mcp_logger = get_logger("learn-mcp")

# Standard Python logger -- what your tool code uses
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

# FastMCP log_level controls framework-level logs (tool dispatch, transport, etc.)
mcp = FastMCP(name="learn-mcp-logging", log_level="DEBUG")


@mcp.tool
async def greet(
    name: Annotated[str, Field(description="The person's name to greet")],
) -> dict:
    """Greet with logging at each step."""
    logger.info("greet called with name=%s", name)

    if not name.strip():
        logger.warning("Empty name received")
        return {"error": "name cannot be empty"}

    result = {"greeting": f"Hello, {name}!", "server": "learn-mcp-logging"}
    logger.debug("greet result: %s", result)
    return result


async def main():
    print("=== MCP Logging Demo ===\n")

    async with Client(mcp) as client:
        # You'll see FastMCP DEBUG logs (tool dispatch, schema loading)
        # plus our INFO logs from inside the tool
        r1 = await client.call_tool("greet", {"name": "Shubham"})
        print(f"\nResult: {r1}\n")

        # Change log level at runtime
        mcp_logger.setLevel(logging.WARNING)
        logger.setLevel(logging.WARNING)
        print("--- Log level set to WARNING (fewer logs) ---\n")

        r2 = await client.call_tool("greet", {"name": "Shubham"})
        print(f"\nResult: {r2}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    #
    # Two loggers in an MCP server:
    #
    # 1. FastMCP logger (get_logger / log_level setting)
    #    - Framework logs: tool dispatch, transport, schema
    #    - Controlled via FastMCP(log_level="DEBUG")
    #
    # 2. Python logger (logging.getLogger(__name__))
    #    - Your tool logic: inputs, decisions, results
    #    - Standard logging.basicConfig() or custom formatter
    #
    # Production (story-drafting/src/main.py) uses a JsonFormatter
    # that outputs one JSON line per log entry for Datadog parsing.
