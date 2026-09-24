"""Diagnostic: is each server in .mcp.json actually connected?

Run:  uv run python check_mcp.py

Checks every server listed in .mcp.json and reports what happened. For
URL (HTTP) servers it separates the two things that fail independently:

  1. REACHABLE  -- is anything listening at that URL at all?
  2. MCP OK     -- does the MCP handshake + tools/list succeed?

A server can be reachable but not speak MCP (wrong path, wrong service),
which is the confusing case this exists to disambiguate.

Exit code is 0 if every server connected, 1 otherwise -- so you can use
it in a script or CI step.
"""

import asyncio
import sys
import time

import httpx
from fastmcp import Client

from agent_core import build_transport, load_mcp_config


async def check_url_reachable(url: str) -> tuple[bool, str]:
    """Is anything listening? A 4xx/5xx still counts as reachable -- it
    means something answered, which is a different problem from nothing
    being there at all."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
        return True, f"HTTP {resp.status_code}"
    except httpx.ConnectError:
        return False, "connection refused / host not found"
    except httpx.TimeoutException:
        return False, "timed out"
    except Exception as e:
        # Some MCP endpoints reject GET but are still up.
        return True, f"responded ({type(e).__name__})"


async def check_server(name: str, cfg: dict) -> bool:
    kind = "http" if "url" in cfg else "stdio"
    target = cfg["url"] if kind == "http" else f"{cfg['command']} {' '.join(cfg.get('args', []))}"
    print(f"\n[{name}]  {kind}  ->  {target}")

    # For URL servers, check reachability first so a network problem
    # doesn't look like an MCP problem.
    if kind == "http":
        reachable, detail = await check_url_reachable(cfg["url"])
        print(f"  reachable : {'YES' if reachable else 'NO'}  ({detail})")
        if not reachable:
            print("  mcp       : SKIPPED -- nothing listening at that URL")
            print("  fix       : start the server, or check the host/port in .mcp.json")
            return False

    # The real test: can we complete an MCP handshake and list tools?
    started = time.monotonic()
    try:
        transport = build_transport(cfg)
        async with Client(transport=transport) as client:
            tools = await asyncio.wait_for(client.list_tools(), timeout=20.0)
        elapsed = (time.monotonic() - started) * 1000
        print(f"  mcp       : OK  ({len(tools)} tools, {elapsed:.0f}ms)")
        for t in tools:
            desc = (t.description or "").split("\n")[0][:56]
            print(f"     - {name}__{t.name}  {desc}")
        return True
    except asyncio.TimeoutError:
        print("  mcp       : FAILED -- handshake timed out after 20s")
        return False
    except Exception as e:
        print(f"  mcp       : FAILED -- {type(e).__name__}: {str(e)[:150]}")
        if kind == "http":
            print("  fix       : the host answered but MCP failed. Usually the wrong")
            print("              path -- most servers mount MCP at /mcp, not /")
        else:
            print("  fix       : check the command runs on its own:")
            print(f"              uv run {target}")
        return False


async def main() -> int:
    config = load_mcp_config()
    if not config:
        print("No servers in .mcp.json (or the file is missing).")
        return 1

    print(f"Checking {len(config)} server(s) from .mcp.json...")
    results = [await check_server(name, cfg) for name, cfg in config.items()]

    ok, total = sum(results), len(results)
    print(f"\n{'=' * 52}")
    print(f"{ok}/{total} server(s) connected")
    if ok < total:
        print("\nNote: the agent starts anyway and just skips failed servers.")
        print("Restart the CLI or web server after fixing .mcp.json --")
        print("the tool registry is built once at startup.")
    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
