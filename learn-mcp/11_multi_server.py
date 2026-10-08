"""Lesson 11 -- Multi-Server Registry: which server owns this tool?
===================================================================

Greetings live on one server, translation on another. When the orchestrator
decides to call "translate", something has to know that tool is not on the
greeting server. A REGISTRY answers that: it asks every server what it has
(tools/list) and builds one routing table, tool name -> server.

  ┌──────── REGISTRY ────────┐
  │ 1. register(name, server)│
  │ 2. discover_all():       │        tools/list      ┌── greeting-server ──┐
  │      ask each server ────┼──────────────────────► │  greet              │
  │                          │ ◄──────────────────────┤  farewell           │
  │                          │                        └─────────────────────┘
  │    routing table:        │        tools/list      ┌── translate-server ─┐
  │      greet     -> greet… ├──────────────────────► │  translate          │
  │      farewell  -> greet… │ ◄──────────────────────┤                     │
  │      translate -> trans… │                        └─────────────────────┘
  │                          │
  │ 3. call_tool("translate")│   look up the table, open a client to THAT
  │      ────────────────────┼─► server, call it, return the result
  │                          │
  │ 4. call_tools_parallel() │   asyncio.gather -- calls to different servers
  │      ────────────────────┼─► overlap instead of queueing
  └──────────────────────────┘

  An unknown tool fails in the registry, before any network call.
  In production each server is a separate process on its own URL; here they
  are two in-process FastMCP objects so the lesson runs with no ports.

Run:  uv run python 11_multi_server.py

Maps to: mcp_server_registry.py (registration + capability cache),
mcp_client_manager.py (per-server clients), mcp_protocol.py (routing)

NOTE ON A SECOND WAY TO DO THIS: FastMCP itself has a built-in answer to
"which server owns this tool" -- mount() and create_proxy() (see
learn-fastmcp-server lesson 14), which combine multiple servers into ONE
that a client talks to directly, with namespacing handled for you. The
hand-rolled ServerRegistry here is what this codebase's production
backend actually runs (it also does per-server health/capability caching
mount() doesn't), but if you're building a new server from scratch and
don't need that, mount() is less code for the same routing problem.
"""

import asyncio
from fastmcp import FastMCP, Client

from greeting_tools import greet, farewell, translate

# -- Two servers, each owning part of the greeting job ------------------------
# Same three functions as lessons 10 and 12 (greeting_tools.py), just split
# across two servers here instead of registered on one.

greeting_server = FastMCP(name="greeting-server")
greeting_server.tool(greet)
greeting_server.tool(farewell)

translate_server = FastMCP(name="translate-server")
translate_server.tool(translate)


# -- The registry (simplified mcp_server_registry.py) ------------------------

class ServerRegistry:
    """Servers by name, plus a tool -> server routing table."""

    def __init__(self):
        self.servers: dict[str, FastMCP] = {}
        self.routes: dict[str, str] = {}          # tool name -> server name

    def register(self, server: FastMCP) -> None:
        self.servers[server.name] = server

    async def discover_all(self) -> None:
        """Ask every server for its tools and build the routing table once."""
        for name, server in self.servers.items():
            async with Client(server) as client:
                for tool in await client.list_tools():
                    self.routes[tool.name] = name

    async def call_tool(self, tool: str, args: dict) -> dict:
        """Route one call to the server that owns the tool."""
        server_name = self.routes.get(tool)
        if not server_name:                        # fails here, before any I/O
            return {"error": f"no server owns tool '{tool}'"}
        async with Client(self.servers[server_name]) as client:
            r = await client.call_tool(tool, args)
            return {"server": server_name, "tool": tool, "result": r.data}

    async def call_tools_parallel(self, calls: list[tuple[str, dict]]) -> list[dict]:
        """Different servers, so the calls overlap instead of queueing."""
        return await asyncio.gather(*(self.call_tool(t, a) for t, a in calls))


async def main():
    # 1 + 2. register, then discover
    registry = ServerRegistry()
    registry.register(greeting_server)
    registry.register(translate_server)
    await registry.discover_all()

    print("servers:", list(registry.servers), "\n")
    print("routing table")
    for tool, server in sorted(registry.routes.items()):
        print(f"  {tool:<10} -> {server}")

    # 3. routed calls -- the caller never names a server
    print("\nrouted calls")
    r = await registry.call_tool("greet", {"name": "Shubham"})
    print(f"  greet     -> [{r['server']}] {r['result']['message']}")

    r = await registry.call_tool("translate", {"text": "Hello, Shubham!", "language": "fr"})
    print(f"  translate -> [{r['server']}] {r['result']['translated']}")

    print("  nonexistent ->", await registry.call_tool("nonexistent", {}))

    # 4. parallel across servers
    results = await registry.call_tools_parallel([
        ("greet", {"name": "Shubham"}),
        ("farewell", {"name": "Shubham"}),
        ("translate", {"text": "Hello!", "language": "de"}),
    ])
    print("\nparallel")
    for r in results:
        print(f"  [{r['server']:<16}] {r['tool']}")
    print(f"  {len(results)} calls, all in flight at once")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Register a third server with a `greet_formal` tool -- the table grows
#    with no change to call_tool.
# 2. Add greet to translate-server too. Which server wins the route, and why?
#    (hint: discover_all overwrites -- add a conflict warning)
# 3. Give call_tool a try/except that returns {"error": ...} so one dead
#    server cannot break call_tools_parallel.
