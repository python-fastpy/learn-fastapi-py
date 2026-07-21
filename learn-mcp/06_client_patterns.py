"""Lesson 06 -- Discovery, Invocation & Retry
==============================================
Concepts:
  - Full discovery: list_tools(), list_resources(), list_prompts()
  - call_tool() vs call_tool_mcp() -- dict result vs raw MCP CallToolResult
  - Timeout handling with asyncio.wait_for
  - Retry with exponential backoff
  - One-shot client pattern (connect -> call -> disconnect per request)
  - Error handling for tool calls

Flow:
  +----------+     +------------------+
  | Client   | --> | MCP Server       |
  +----------+     +------------------+
  | Patterns:|     | Tools:           |
  |  discover|     |  slow_tool       |
  |  retry   |     |  flaky_tool      |
  |  timeout |     |  echo            |
  |  one-shot|     +------------------+
  +----------+

  Maps to:
    mcp_protocol.py  -> one-shot client pattern
    mcp_client_manager.py -> retry logic, circuit breaker concepts
    mcp_server_registry.py -> capability discovery (list_tools)

No LLM needed -- demonstrates client-side resilience patterns.

Run:  uv run python 06_client_patterns.py
"""

import asyncio
import random
import time as time_mod
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client


mcp = FastMCP(name="resilience-demo")

_call_count = 0


@mcp.tool
async def echo(
    message: Annotated[str, Field(description="Message to echo back")],
) -> dict:
    """Echo a message back (always succeeds)."""
    return {"echo": message}


@mcp.tool
async def slow_tool(
    seconds: Annotated[float, Field(default=2.0, description="Seconds to sleep")] = 2.0,
) -> dict:
    """Simulate a slow operation."""
    await asyncio.sleep(seconds)
    return {"status": "done", "slept_for": seconds}


@mcp.tool
async def flaky_tool(
    message: Annotated[str, Field(description="Message to process")],
) -> dict:
    """Fails 50% of the time to demonstrate retry logic."""
    global _call_count
    _call_count += 1
    if _call_count % 2 == 1:  # odd calls fail
        raise Exception(f"Random failure on call #{_call_count}")
    return {"processed": message, "attempt": _call_count}


# ============================================================================
# Client patterns
# ============================================================================

async def demo_discovery(client: Client):
    """Full capability discovery -- what can this server do?"""
    print("=== 1. Discovery ===\n")

    tools = await client.list_tools()
    print(f"  Tools ({len(tools)}):")
    for t in tools:
        params = list(t.inputSchema.get("properties", {}).keys())
        print(f"    - {t.name}({', '.join(params)}): {t.description}")

    resources = await client.list_resources()
    print(f"\n  Resources ({len(resources)}):")
    for r in resources:
        print(f"    - {r.uri}")

    prompts = await client.list_prompts()
    print(f"\n  Prompts ({len(prompts)}):")
    for p in prompts:
        print(f"    - {p.name}")
    print()


async def demo_timeout(client: Client):
    """Timeout handling -- don't wait forever for slow tools."""
    print("=== 2. Timeout Handling ===\n")

    # This will succeed (short timeout target)
    try:
        result = await asyncio.wait_for(
            client.call_tool("slow_tool", {"seconds": 0.1}),
            timeout=2.0,
        )
        print(f"  slow_tool(0.1s): {result}")
    except asyncio.TimeoutError:
        print("  slow_tool(0.1s): TIMED OUT")

    # This will time out
    try:
        result = await asyncio.wait_for(
            client.call_tool("slow_tool", {"seconds": 5.0}),
            timeout=1.0,
        )
        print(f"  slow_tool(5.0s): {result}")
    except asyncio.TimeoutError:
        print("  slow_tool(5.0s): TIMED OUT (expected)")
    print()


async def call_with_retry(
    client: Client,
    tool_name: str,
    args: dict,
    max_retries: int = 3,
    base_delay: float = 0.5,
) -> dict | None:
    """Retry a tool call with exponential backoff.

    This mirrors the retry logic in mcp_client_manager.py:
    retry on failure, exponential backoff, give up after max_retries.
    """
    for attempt in range(max_retries + 1):
        try:
            result = await client.call_tool(tool_name, args)
            return {"result": result, "attempt": attempt + 1}
        except Exception as e:
            if attempt == max_retries:
                return {"error": str(e), "attempts": attempt + 1}
            delay = base_delay * (2 ** attempt)
            print(f"    Attempt {attempt + 1} failed: {e}")
            print(f"    Retrying in {delay}s...")
            await asyncio.sleep(delay)
    return None


async def demo_retry(client: Client):
    """Retry with exponential backoff."""
    print("=== 3. Retry with Backoff ===\n")

    global _call_count
    _call_count = 0  # reset for demo

    result = await call_with_retry(
        client, "flaky_tool", {"message": "hello"}, max_retries=3, base_delay=0.2
    )
    print(f"  Final result: {result}")
    print()


async def demo_one_shot():
    """One-shot client: connect -> call -> disconnect.

    This is the pattern from mcp_protocol.py:
      async with Client(transport) as client:
          result = await client.call_tool(...)
    Each request gets a fresh connection. Simple but no connection reuse.
    """
    print("=== 4. One-Shot Client Pattern ===\n")

    # Each call creates a fresh client connection
    for i in range(3):
        async with Client(mcp) as client:
            result = await client.call_tool("echo", {"message": f"request #{i+1}"})
            print(f"  One-shot #{i+1}: {result}")

    print()
    print("  (Each call was a separate client session)")
    print()


async def demo_error_handling(client: Client):
    """Handle various error scenarios gracefully."""
    print("=== 5. Error Handling ===\n")

    # Call a tool that doesn't exist
    try:
        await client.call_tool("nonexistent_tool", {})
    except Exception as e:
        print(f"  Unknown tool: {type(e).__name__}: {str(e)[:80]}")

    # Call with missing required parameter
    try:
        await client.call_tool("echo", {})
    except Exception as e:
        print(f"  Missing param: {type(e).__name__}: {str(e)[:80]}")

    print()


async def main():
    async with Client(mcp) as client:
        await demo_discovery(client)
        await demo_timeout(client)
        await demo_retry(client)
        await demo_error_handling(client)

    # One-shot demo uses its own client instances
    await demo_one_shot()


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Production MCP clients need resilience:
    #
    # 1. Discovery -- list_tools() before calling (capability check)
    # 2. Timeout -- asyncio.wait_for() prevents hanging on slow tools
    # 3. Retry -- exponential backoff for transient failures
    # 4. One-shot -- fresh connection per request (simple, reliable)
    # 5. Error handling -- graceful degradation on unknown tools
    #
    # Your production code uses all of these:
    #   mcp_protocol.py -> one-shot Client pattern
    #   mcp_client_manager.py -> retry with backoff, circuit breaker
    #   mcp_server_registry.py -> discovery via list_tools()
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Implement a simple circuit breaker: if 3 consecutive failures,
    #    stop trying for 30 seconds
    # 2. Add parallel tool calls with asyncio.gather()
    # 3. Implement call_with_retry over HTTP transport (lesson 05 server)
