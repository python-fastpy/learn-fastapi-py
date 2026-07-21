"""Lesson 11 -- Multi-Server Registry
======================================
Concepts:
  - Running multiple MCP servers simultaneously
  - ServerRegistry: track servers and their capabilities
  - Tool routing: which server handles which tool
  - Parallel tool calls across servers
  - Capability discovery across the fleet

Flow:
  +-------------------+
  | Server Registry   |
  +-------------------+
  | Servers:          |
  |  story-drafting   |-----> Client A --> [draft_story, search_rics]
  |  text-archive     |-----> Client B --> [search_archive]
  |  urgent-drafting   |-----> Client C --> [generate_urgent]
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

No LLM needed -- demonstrates multi-server coordination.

Run:  uv run python 11_multi_server.py
"""

import asyncio
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client


# ============================================================================
# Server 1: Story Drafting
# ============================================================================

story_server = FastMCP(name="story-drafting")


@story_server.tool
async def draft_story(
    topic: Annotated[str, Field(description="Topic for the story")],
) -> dict:
    """Draft a spot news story."""
    return {
        "source": "story-drafting",
        "draft": f"REUTERS - Story about {topic}...",
        "style": "spot",
    }


@story_server.tool
async def search_rics(
    query: Annotated[str, Field(description="RIC search query")],
) -> dict:
    """Search for Reuters Instrument Codes."""
    return {
        "source": "story-drafting",
        "results": [f"{query}.O", f"{query}.L"],
    }


# ============================================================================
# Server 2: Text Archive
# ============================================================================

archive_server = FastMCP(name="text-archive")


@archive_server.tool
async def search_archive(
    query: Annotated[str, Field(description="Search query for the archive")],
    limit: Annotated[int, Field(default=10, description="Max results")] = 10,
) -> dict:
    """Search the Reuters Text Archive."""
    return {
        "source": "text-archive",
        "query": query,
        "results": [
            {"title": f"Archive: {query} #{i+1}", "date": f"2024-12-{20-i}"}
            for i in range(min(limit, 5))
        ],
    }


# ============================================================================
# Server 3: Urgent Drafting
# ============================================================================

urgent_server = FastMCP(name="urgent-drafting")


@urgent_server.tool
async def generate_urgent(
    headline: Annotated[str, Field(description="Breaking news headline")],
    details: Annotated[str, Field(default="", description="Additional details")] = "",
) -> dict:
    """Generate an urgent/breaking news alert."""
    return {
        "source": "urgent-drafting",
        "urgent": f"URGENT: {headline}",
        "details": details or "No additional details.",
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
    registry.register("story-drafting", story_server)
    registry.register("text-archive", archive_server)
    registry.register("urgent-drafting", urgent_server)

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

    r1 = await registry.call_tool("draft_story", {"topic": "Fed rate decision"})
    print(f"  draft_story -> routed to '{r1['server']}': {r1['result']}")

    r2 = await registry.call_tool("search_archive", {"query": "OPEC", "limit": 3})
    print(f"  search_archive -> routed to '{r2['server']}': {r2['result']}")

    r3 = await registry.call_tool("generate_urgent", {"headline": "Fed cuts rates"})
    print(f"  generate_urgent -> routed to '{r3['server']}': {r3['result']}")
    print()

    # -- 4. Unknown tool --
    print("=== Unknown Tool ===\n")
    r4 = await registry.call_tool("nonexistent", {})
    print(f"  nonexistent -> {r4}")
    print()

    # -- 5. Parallel calls across servers --
    print("=== Parallel Calls Across Servers ===\n")
    results = await registry.call_tools_parallel([
        ("draft_story", {"topic": "AI regulation"}),
        ("search_archive", {"query": "regulation", "limit": 2}),
        ("generate_urgent", {"headline": "EU passes AI Act"}),
    ])
    for r in results:
        print(f"  [{r['server']}] {r['tool']}: done")
    print()
    print(f"  All {len(results)} calls completed in parallel.")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # In production, multiple MCP servers run on different ports/URLs:
    #   story-drafting  -> :8004
    #   urgent-drafting -> :8003
    #   text-archive    -> :8000
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
