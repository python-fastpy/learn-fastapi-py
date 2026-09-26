"""Lesson 08 -- Client Patterns: discover, timeout, retry, errors, one-shot
==========================================================================

Skills run on remote containers that can be slow, crash, or be briefly
unavailable. The backend must not crash, hang forever, or flood a
recovering server. Five patterns, all calling one greet tool:

  1. DISCOVER   list_tools / list_resources / list_prompts   what can this server do?
  2. TIMEOUT    asyncio.wait_for(call, timeout=1.0)          don't wait forever
  3. RETRY      try -> wait 0.2s -> try -> wait 0.4s -> ...  exponential backoff
  4. ERRORS     call_tool() raises; call_tool_mcp() returns  unknown tool, bad args
                the raw result with isError=True
  5. ONE-SHOT   new client per call: connect -> call -> close

  ┌──────────────── CLIENT (backend) ────────────────┐         ┌──── MCP SERVER ────┐
  │ 1. discover ─────── list_tools ───────────────────┼───────► │                    │
  │ 2. timeout  ─────── greet(delay=5) ── gives up 1s ┼───────► │ greet(name,        │
  │ 3. retry    ─────── greet(flaky) ✗ wait ✓         ┼───────► │       delay=0,     │
  │ 4. errors   ─────── nope() / greet() no name      ┼───────► │       flaky=False) │
  │ 5. one-shot ─┬── client #1 ── greet ──────────────┼───────► │                    │
  │              ├── client #2 ── greet ──────────────┼───────► │                    │
  │              └── client #3 ── greet ──────────────┼───────► │                    │
  └───────────────────────────────────────────────────┘         └────────────────────┘

Run:  uv run python 08_client_patterns.py

Maps to: mcp_protocol.py (one-shot client), mcp_client_manager.py (retry,
         circuit breaker), mcp_server_registry.py (discovery via list_tools)
"""

import asyncio
from fastmcp import FastMCP, Client
from fastmcp.exceptions import ToolError

mcp = FastMCP("resilient-greetings")
CALLS: dict[str, int] = {}                     # how many times each name was greeted


@mcp.tool
async def greet(name: str, delay: float = 0, flaky: bool = False) -> str:
    """Greet someone. delay = seconds to wait (slow server); flaky = fail the first try."""
    await asyncio.sleep(delay)                                     # simulate a slow server
    CALLS[name] = CALLS.get(name, 0) + 1
    if flaky and CALLS[name] == 1:                                 # simulate a hiccup
        raise ToolError(f"server busy (call #{CALLS[name]})")
    return f"Hello, {name}!"


async def call_with_retry(client, args, retries=3, delay=0.2):
    """3. RETRY -- wait longer after each failure: 0.2s, 0.4s, 0.8s, then give up."""
    for attempt in range(1, retries + 2):
        try:
            return (await client.call_tool("greet", args)).data, attempt
        except ToolError as e:
            if attempt > retries:
                raise
            print(f"   attempt {attempt} failed ({e}) -> retry in {delay}s")
            await asyncio.sleep(delay)
            delay *= 2


async def main():
    async with Client(mcp) as client:
        # 1. DISCOVER
        print("1. tools     :", [t.name for t in await client.list_tools()])        # ['greet']
        print("   resources :", await client.list_resources(), "| prompts:", await client.list_prompts())

        # 2. TIMEOUT
        r = await asyncio.wait_for(client.call_tool("greet", {"name": "Ana", "delay": 0.1}), timeout=1.0)
        print("2. fast      :", r.data)                                            # Hello, Ana!
        try:
            await asyncio.wait_for(client.call_tool("greet", {"name": "Ana", "delay": 5}), timeout=1.0)
        except asyncio.TimeoutError:
            print("   slow      : gave up after 1s (TimeoutError)")

        # 3. RETRY
        result, attempt = await call_with_retry(client, {"name": "Bob", "flaky": True})
        print(f"3. retry     : {result} (succeeded on attempt {attempt})")

        # 4. ERRORS -- call_tool raises; call_tool_mcp returns the raw MCP result
        for label, tool, args in [("unknown tool", "nope", {}), ("missing name", "greet", {})]:
            try:
                await client.call_tool(tool, args)
            except Exception as e:
                print(f"4. {label:<12}: call_tool raised {type(e).__name__}")
        raw = await client.call_tool_mcp("nope", {})
        print(f"   call_tool_mcp -> isError={raw.isError} (no exception)")

    # 5. ONE-SHOT -- a fresh client per call (what mcp_protocol.py does)
    for i in (1, 2, 3):
        async with Client(mcp) as client:
            print(f"5. one-shot #{i}:", (await client.call_tool("greet", {"name": f"User-{i}"})).data)


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Circuit breaker: after 3 failures in a row, stop calling for 30 seconds.
# 2. Greet 5 names at once with asyncio.gather() -- how long does it take with delay=1?
# 3. Use call_with_retry against lesson 07's HTTP server.
