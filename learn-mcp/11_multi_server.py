"""Lesson 11 -- Multi-Server Registry
======================================

WHY THIS MATTERS:
  Real MCP deployments don't stop at a single server. You might have one
  server for greetings, another for translations, and a third for
  formatting -- each running independently on a different port. When
  the orchestrator says "call translate," something needs to know that
  tool lives on the translation-server, not on the greeting-server.
  The ServerRegistry solves this: it discovers all tools from all servers
  at startup and builds a routing table (tool_name -> server).

WHAT YOU'LL LEARN:
  1. Register multiple MCP servers in a central registry
  2. Discover tools from all servers at startup
  3. Route tool calls to the correct server automatically
  4. Execute tools in parallel across different servers

Concepts:
  - Running multiple MCP servers simultaneously
  - ServerRegistry: track servers and their capabilities
  - Tool routing: which server handles which tool
  - Parallel tool calls across servers

Flow:
  +-------------------+
  | Server Registry   |
  +-------------------+
  | Servers:          |
  |  greeting-server  |-----> Client A --> [greet, farewell]
  |  translation-srv  |-----> Client B --> [translate, detect_language]
  |  format-server    |-----> Client C --> [format_card]
  +-------------------+
         |
         v
  +-------------------+
  | Orchestrator      |
  |  1. List all tools|
  |  2. Route to      |
  |     correct server|
  |  3. Parallel calls|
  +-------------------+

  Maps to:
    mcp_server_registry.py (server registration, capability cache)
    mcp_client_manager.py (connection pool, per-server clients)
    mcp_protocol.py (tool routing, parallel execution)

PREREQUISITES: Lesson 05 (HTTP transport), Lesson 06 (client patterns)

Run:  uv run python 11_multi_server.py

EXPECTED OUTPUT:
  === Server Registry ===

    Servers: ['greeting-server', 'translation-server', 'format-server']

  === Tool Routing Table ===

    detect_language        -> translation-server
    farewell               -> greeting-server
    format_card            -> format-server
    greet                  -> greeting-server
    translate              -> translation-server

  === Routed Tool Calls ===

    greet -> routed to 'greeting-server': ...
    translate -> routed to 'translation-server': ...
    format_card -> routed to 'format-server': ...

  === Unknown Tool ===

    nonexistent -> {'error': "No server found for tool 'nonexistent'"}

  === Parallel Calls Across Servers ===

    [greeting-server] greet: done
    [translation-server] translate: done
    [format-server] format_card: done

    All 3 calls completed in parallel.
"""

import asyncio
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client


# ============================================================================
# Server 1: Greeting Server
# ============================================================================

greeting_server = FastMCP(name="greeting-server")


@greeting_server.tool
async def greet(
    name: Annotated[str, Field(description="Name of the person to greet")],
) -> dict:
    """Greet someone with a friendly hello."""
    return {
        "source": "greeting-server",
        "message": f"Hello, {name}!",
    }


@greeting_server.tool
async def farewell(
    name: Annotated[str, Field(description="Name of the person to bid farewell")],
) -> dict:
    """Say goodbye to someone."""
    return {
        "source": "greeting-server",
        "message": f"Goodbye, {name}!",
    }


# ============================================================================
# Server 2: Translation Server
# ============================================================================

translation_server = FastMCP(name="translation-server")


@translation_server.tool
async def translate(
    text: Annotated[str, Field(description="Text to translate")],
    language: Annotated[str, Field(description="Target language")],
) -> dict:
    """Translate text into another language."""
    return {
        "source": "translation-server",
        "original": text,
        "translated": f"[{language}] {text}",
        "language": language,
    }


@translation_server.tool
async def detect_language(
    text: Annotated[str, Field(description="Text to detect language of")],
) -> dict:
    """Detect the language of a text."""
    return {
        "source": "translation-server",
        "text": text,
        "detected": "en",
        "confidence": 0.95,
    }


# ============================================================================
# Server 3: Format Server
# ============================================================================

format_server = FastMCP(name="format-server")


@format_server.tool
async def format_card(
    name: Annotated[str, Field(description="Name for the card")],
    message: Annotated[str, Field(description="Message content")],
) -> dict:
    """Format a greeting card."""
    return {
        "source": "format-server",
        "card": f"=== Card for {name} ===\n{message}\n=================",
        "name": name,
    }


# ============================================================================
# Server Registry (simplified mcp_server_registry.py)
# ============================================================================

class ServerEntry:
    """A registered MCP server with cached capabilities."""

    def __init__(self, name: str, server: FastMCP):
        self.name = name
        self.server = server
        self.tools: list[str] = []
        self._client: Client | None = None

    async def discover(self):
        """Discover tools from this server."""
        async with Client(self.server) as client:
            tool_list = await client.list_tools()
            self.tools = [t.name for t in tool_list]
        return self.tools

    async def call_tool(self, tool_name: str, args: dict) -> dict:
        """Call a tool on this server (one-shot pattern)."""
        async with Client(self.server) as client:
            result = await client.call_tool(tool_name, args)
            return {"server": self.name, "tool": tool_name, "result": result}


class ServerRegistry:
    """Registry of MCP servers with tool routing.

    Mirrors mcp_server_registry.py:
      - register servers
      - discover capabilities
      - route tool calls to the right server
    """

    def __init__(self):
        self._servers: dict[str, ServerEntry] = {}
        self._tool_to_server: dict[str, str] = {}

    def register(self, name: str, server: FastMCP):
        """Register a new MCP server."""
        self._servers[name] = ServerEntry(name, server)

    async def discover_all(self):
        """Discover tools from all registered servers."""
        for name, entry in self._servers.items():
            tools = await entry.discover()
            for tool in tools:
                self._tool_to_server[tool] = name

    def get_all_tools(self) -> dict[str, str]:
        """Get mapping of tool_name -> server_name."""
        return dict(self._tool_to_server)

    def get_server_for_tool(self, tool_name: str) -> ServerEntry | None:
        """Route a tool call to the correct server."""
        server_name = self._tool_to_server.get(tool_name)
        if server_name:
            return self._servers[server_name]
        return None

    async def call_tool(self, tool_name: str, args: dict) -> dict:
        """Route and execute a tool call."""
        entry = self.get_server_for_tool(tool_name)
        if not entry:
            return {"error": f"No server found for tool '{tool_name}'"}
        return await entry.call_tool(tool_name, args)

    async def call_tools_parallel(self, calls: list[tuple[str, dict]]) -> list[dict]:
        """Execute multiple tool calls in parallel across servers."""
        tasks = [self.call_tool(name, args) for name, args in calls]
        return await asyncio.gather(*tasks)


# ============================================================================
# Demo
# ============================================================================

async def main():
    # -- 1. Build the registry --
    registry = ServerRegistry()
    registry.register("greeting-server", greeting_server)
    registry.register("translation-server", translation_server)
    registry.register("format-server", format_server)

    # -- 2. Discover all capabilities --
    await registry.discover_all()

    print("=== Server Registry ===\n")
    print(f"  Servers: {list(registry._servers.keys())}")
    print()

    all_tools = registry.get_all_tools()
    print("=== Tool Routing Table ===\n")
    for tool, server in sorted(all_tools.items()):
        print(f"  {tool:25s} -> {server}")
    print()

    # -- 3. Route individual tool calls --
    print("=== Routed Tool Calls ===\n")

    r1 = await registry.call_tool("greet", {"name": "Alice"})
    print(f"  greet -> routed to '{r1['server']}': {r1['result']}")

    r2 = await registry.call_tool("translate", {"text": "Hello!", "language": "French"})
    print(f"  translate -> routed to '{r2['server']}': {r2['result']}")

    r3 = await registry.call_tool("format_card", {"name": "Bob", "message": "Best wishes!"})
    print(f"  format_card -> routed to '{r3['server']}': {r3['result']}")
    print()

    # -- 4. Unknown tool --
    print("=== Unknown Tool ===\n")
    r4 = await registry.call_tool("nonexistent", {})
    print(f"  nonexistent -> {r4}")
    print()

    # -- 5. Parallel calls across servers --
    print("=== Parallel Calls Across Servers ===\n")
    results = await registry.call_tools_parallel([
        ("greet", {"name": "Alice"}),
        ("translate", {"text": "Hello!", "language": "French"}),
        ("format_card", {"name": "Bob", "message": "Best wishes!"}),
    ])
    for r in results:
        print(f"  [{r['server']}] {r['tool']}: done")
    print()
    print(f"  All {len(results)} calls completed in parallel.")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # In production, multiple MCP servers run on different ports/URLs:
    #   greeting-server     -> :8001
    #   translation-server  -> :8002
    #   format-server       -> :8003
    #
    # The ServerRegistry:
    #   1. Tracks which servers are available
    #   2. Discovers tools from each server (list_tools)
    #   3. Routes tool calls to the correct server
    #   4. Enables parallel execution across servers
    #
    # This maps to:
    #   mcp_server_registry.py -> registration + capability cache
    #   mcp_client_manager.py  -> connection pool per server
    #   mcp_protocol.py        -> routing + parallel execution
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a "health_check" method that pings all servers
    # 2. Implement a simple circuit breaker per server
    # 3. Add server priority/fallback (if server A fails, try server B)
