"""Lesson 05 -- Real HTTP Server
=================================
Concepts:
  - mcp.run(transport="http"): start a real HTTP server
  - StreamableHttpTransport: connect a client over HTTP
  - @mcp.custom_route("/health"): custom REST endpoints
  - stateless_http=True: no session state between requests
  - json_response=True: JSON-formatted responses
  - multiprocessing: run server + client in one script

Flow:
  +--------+     HTTP      +------------------+
  | Client |  --------->   | MCP Server       |
  | (main) |  POST /mcp    | (child process)  |
  +--------+  <---------   +------------------+
       |       JSON resp   | Endpoints:       |
       |                   |  POST /mcp       |
       |                   |  GET  /health    |
       +---list_tools()    +------------------+
       +---call_tool()
       +---GET /health

  Maps to:
    story-drafting/src/main.py run block:
      mcp.run(transport="http", host="0.0.0.0", port=8004,
              json_response=True, stateless_http=True)
    @mcp.custom_route("/health") for ALB health checks

No LLM needed -- demonstrates real HTTP transport.

Run:  uv run python 05_http_transport.py
"""

import asyncio
import multiprocessing
import time
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client
from fastmcp.client.transports import StreamableHttpTransport
import httpx

SERVER_PORT = 8765
SERVER_URL = f"http://localhost:{SERVER_PORT}"


# ============================================================================
# SERVER SIDE -- runs in a child process
# ============================================================================

mcp = FastMCP(name="http-demo")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health endpoint for load balancer checks (ALB, ECS, etc.)."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy", "server": "http-demo"})


@mcp.tool
async def word_count(
    text: Annotated[str, Field(description="Text to count words in")],
) -> dict:
    """Count words in the given text."""
    words = text.split()
    return {"word_count": len(words), "char_count": len(text)}


@mcp.tool
async def uppercase(
    text: Annotated[str, Field(description="Text to convert to uppercase")],
) -> dict:
    """Convert text to uppercase."""
    return {"original": text, "uppercased": text.upper()}


def run_server():
    """Entry point for the child process."""
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=SERVER_PORT,
        json_response=True,
        stateless_http=True,
    )


# ============================================================================
# CLIENT SIDE -- runs in the main process
# ============================================================================

async def run_client():
    """Connect to the HTTP server and call tools."""

    # -- 1. Check health endpoint (plain HTTP, not MCP) -----------------------
    print("=== Health Check ===")
    async with httpx.AsyncClient() as http:
        resp = await http.get(f"{SERVER_URL}/health")
        print(f"  GET /health -> {resp.status_code}: {resp.json()}")
    print()

    # -- 2. Connect via MCP over HTTP -----------------------------------------
    transport = StreamableHttpTransport(url=f"{SERVER_URL}/mcp")

    async with Client(transport) as client:
        # Discover tools
        tools = await client.list_tools()
        print("=== Tools (via HTTP) ===")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
        print()

        # Call tools
        print("=== word_count ===")
        r1 = await client.call_tool("word_count", {
            "text": "Reuters reports that oil prices surged today"
        })
        print(f"  {r1}")

        print("\n=== uppercase ===")
        r2 = await client.call_tool("uppercase", {
            "text": "breaking news"
        })
        print(f"  {r2}")


# ============================================================================
# MAIN -- spawn server process, run client, clean up
# ============================================================================

if __name__ == "__main__":
    # Start server in a child process
    server_proc = multiprocessing.Process(target=run_server, daemon=True)
    server_proc.start()

    # Wait for server to be ready
    print(f"Starting HTTP server on port {SERVER_PORT}...")
    for _ in range(30):
        try:
            import urllib.request
            urllib.request.urlopen(f"{SERVER_URL}/health", timeout=1)
            break
        except Exception:
            time.sleep(0.3)
    else:
        print("Server failed to start!")
        server_proc.terminate()
        raise SystemExit(1)

    print("Server is ready.\n")

    # Run client
    try:
        asyncio.run(run_client())
    finally:
        server_proc.terminate()
        server_proc.join(timeout=3)
        print("\nServer stopped.")

    # -- Key takeaway --------------------------------------------------------
    # Production servers use these exact settings:
    #   mcp.run(transport="http", host="0.0.0.0", port=8004,
    #           json_response=True, stateless_http=True)
    #
    # The /health endpoint is critical for ALB health checks in ECS.
    # StreamableHttpTransport connects any client over standard HTTP.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add headers to StreamableHttpTransport:
    #      StreamableHttpTransport(url=..., headers={"Authorization": "Bearer X"})
    # 2. Add a second custom_route for metrics/status info
    # 3. Try running the server standalone and calling it from another terminal
