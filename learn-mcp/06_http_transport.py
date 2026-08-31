"""
Lesson 6: HTTP Transport (Production Pattern)
===============================================
Goal: Run MCP over Streamable HTTP — the production transport used by
all Reuters skill servers (ECS Fargate behind ALB).

What you'll learn:
  - Running FastMCP with transport="http" (Streamable HTTP)
  - Connecting with StreamableHttpTransport
  - Per-request headers (JWT, tenant ID) — the tenant isolation pattern
  - Health check endpoint

Run (two terminals):
  Terminal 1:  uv run python 06_http_transport.py --server
  Terminal 2:  uv run python 06_http_transport.py --client

Production parallel:
  - Server side: ECS Fargate container with path-based ALB routing
    (/story-drafting, /urgent-drafting, /text-archive)
  - Client side: mcp_protocol.py creates one-shot clients with
    StreamableHttpTransport + per-request tenant headers
"""

import asyncio
import sys
from fastmcp import FastMCP, Client
from fastmcp.client.transports import StreamableHttpTransport

# ===== SERVER =====

def create_server() -> FastMCP:
    mcp = FastMCP("news-skill-http")

    @mcp.tool()
    def search_headlines(query: str, limit: int = 5) -> list[dict]:
        """Search recent news headlines."""
        return [
            {"id": f"HL{i+1}", "text": f"{query} headline {i+1}", "time": "14:30"}
            for i in range(limit)
        ]

    @mcp.tool()
    def generate_summary(headline_ids: list[str]) -> str:
        """Generate a summary from selected headlines."""
        return f"Summary of {len(headline_ids)} headlines: Key developments noted."

    return mcp


def run_server():
    mcp = create_server()
    print("Starting HTTP MCP server on http://localhost:8010/mcp")
    print("Health check: http://localhost:8010/health")
    # transport="http" uses Streamable HTTP (not SSE, not stdio)
    # This is the same transport all Reuters skills use in production.
    mcp.run(transport="http", host="0.0.0.0", port=8010)


# ===== CLIENT =====

async def run_client():
    # --- The production pattern: per-request headers ---
    # In production, mcp_protocol.py injects JWT + tenant headers
    # into every request for tenant isolation.
    headers = {
        "Authorization": "Bearer fake-jwt-token",
        "X-Tenant-ID": "leon-shubham",
        "X-Request-ID": "req-demo-001",
    }

    transport = StreamableHttpTransport(
        url="http://localhost:8010/mcp",
        headers=headers,
    )
    client = Client(transport=transport, timeout=30)

    async with client:
        # Step 1: List tools
        tools = await client.list_tools()
        print("=== Available Tools ===")
        for t in tools:
            print(f"  {t.name}: {t.description}")

        # Step 2: Call tool
        print("\n=== search_headlines ===")
        result = await client.call_tool(
            "search_headlines",
            {"query": "Apple earnings", "limit": 3},
        )
        for c in result:
            print(f"  {c.text}")

        # Step 3: Call another tool
        print("\n=== generate_summary ===")
        result = await client.call_tool(
            "generate_summary",
            {"headline_ids": ["HL1", "HL2", "HL3"]},
        )
        for c in result:
            print(f"  {c.text}")

    print("\nDone! The client opened/closed a connection automatically.")
    print("In production, this is a one-shot pattern: new client per tool call.")


# ===== MAIN =====

if __name__ == "__main__":
    if "--server" in sys.argv:
        run_server()
    elif "--client" in sys.argv:
        asyncio.run(run_client())
    else:
        print("Usage:")
        print("  Terminal 1:  uv run python 06_http_transport.py --server")
        print("  Terminal 2:  uv run python 06_http_transport.py --client")
        print()
        print("The server runs on http://localhost:8010/mcp")
        print("This is the exact transport used in production (Streamable HTTP).")


# ============================================================
# EXERCISES:
#
# 1. Add a middleware/hook that logs incoming headers on the
#    server side (simulating tenant extraction)
# 2. Test calling the server with httpx directly (raw HTTP POST)
#    to see the JSON-RPC envelope:
#      import httpx
#      resp = httpx.post("http://localhost:8010/mcp", json={
#          "jsonrpc": "2.0", "id": "1", "method": "tools/list", "params": {}
#      })
# 3. Try running two clients with different X-Tenant-ID headers
# ============================================================
