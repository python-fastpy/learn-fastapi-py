"""Lesson 07 -- MCP over HTTP: the production transport
=======================================================

In production every skill is its own HTTP server (a container on ECS behind
an ALB), and the backend connects to it over the network. Four cases:

  1. SERVER    mcp.run(transport="http", ...)          serve POST /mcp
  2. HEALTH    @mcp.custom_route("/health")            plain GET for the load balancer
  3. CLIENT    Client(StreamableHttpTransport(url))    connect by URL
  4. HEADERS   StreamableHttpTransport(url, headers=)  JWT + tenant id on every request;
                                                       the tool reads them server-side

  FLOW
  ────
  CLIENT (backend)                                   HTTP SERVER  127.0.0.1:8765
  ────────────────                                   ───────────────────────────
                                                     1. mcp.run(transport="http")
                                                        starts FIRST, listens on
                                                          POST /mcp   (MCP)
                                                          GET  /health (plain REST)
         │
  2. GET /health  ────────────────────────────────►  health()
                  ◄───────────────────────────────  200 {"status": "healthy"}
         │
  3. Client(StreamableHttpTransport(url/mcp))
     list_tools()  ──── POST /mcp  tools/list ─────►
                  ◄───────────────────────────────  ["greet"]
         │
  4. for each tenant -- a NEW client with its own headers:
     ┌─ tenant-a ──────────────────────────────────────────────────────────────┐
     │ call_tool("greet") ── POST /mcp  X-Tenant-ID: tenant-a ─►  greet() reads │
     │                    ◄── "Hello, Shubham! (tenant: tenant-a)"   the header │
     └─────────────────────────────────────────────────────────────────────────┘
     ┌─ tenant-b ──────────────────────────────────────────────────────────────┐
     │ call_tool("greet") ── POST /mcp  X-Tenant-ID: tenant-b ─►  greet() reads │
     │                    ◄── "Hello, Shubham! (tenant: tenant-b)"   the header │
     └─────────────────────────────────────────────────────────────────────────┘

  Unlike stdio (lesson 02), the client does NOT start this server -- it must
  already be running, and many clients can share it.

  IN PRODUCTION
  ─────────────
  backend ──HTTPS──► ALB ──/story-drafting──► ECS container (MCP server, port 8004)
  (one-shot client      │   (health-checks
   per call, tenant     │    GET /health)
   headers)             └──/text-archive────► ECS container (MCP server)

  stateless_http=True is what lets the ALB send each request to ANY container:
  no request depends on a session kept in one container's memory.

Run:  uv run python 07_http_transport.py              (starts the server itself, runs the client)
  or, in two terminals:
      uv run python 07_http_transport.py --server     (terminal 1)
      uv run python 07_http_transport.py --client     (terminal 2)

Maps to: story-drafting/src/main.py run block (case 1 settings, /health);
         mcp_protocol.py: one-shot client per call with per-request tenant headers (case 4)
"""

import asyncio
import subprocess
import sys
import time

import httpx
from fastmcp import FastMCP, Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.server.dependencies import get_http_headers
from starlette.responses import JSONResponse

URL = "http://127.0.0.1:8765"
mcp = FastMCP("http-greetings")


# 2. HEALTH -- a normal REST endpoint next to /mcp (ALB/ECS health checks)
@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "healthy"})


@mcp.tool
def greet(name: str) -> str:
    """Greet someone by name."""
    tenant = get_http_headers().get("x-tenant-id", "none")     # 4. read a request header
    return f"Hello, {name}! (tenant: {tenant})"


def run_server():
    # 1. SERVER -- the exact settings production uses
    mcp.run(
        transport="http", host="127.0.0.1", port=8765,
        json_response=True,       # reply with plain JSON (not a stream)
        stateless_http=True,      # no session between requests -> any container can answer
        show_banner=False,
    )


async def run_client():
    # 2. HEALTH -- plain HTTP, no MCP involved
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{URL}/health")
        print("2. GET /health ->", r.status_code, r.json())          # 200 {'status': 'healthy'}

    # 3. CLIENT -- connect by URL
    async with Client(StreamableHttpTransport(f"{URL}/mcp")) as client:
        print("3. tools       ->", [t.name for t in await client.list_tools()])   # ['greet']

    # 4. HEADERS -- one NEW client per call, each with its own tenant headers
    #    (the production "one-shot client" pattern: tenants never share a client)
    for tenant in ("tenant-a", "tenant-b"):
        headers = {"Authorization": "Bearer fake-jwt", "X-Tenant-ID": tenant}
        async with Client(StreamableHttpTransport(f"{URL}/mcp", headers=headers)) as client:
            r = await client.call_tool("greet", {"name": "Shubham"})
            print(f"4. {tenant}     ->", r.data)   # Hello, Shubham! (tenant: tenant-a / -b)


if __name__ == "__main__":
    if "--server" in sys.argv:
        run_server()
    elif "--client" in sys.argv:
        asyncio.run(run_client())
    else:
        # One-script mode: start this file as the server, run the client, stop it.
        server = subprocess.Popen([sys.executable, __file__, "--server"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(50):                                   # wait for /health
                try:
                    httpx.get(f"{URL}/health", timeout=0.5)
                    break
                except httpx.HTTPError:
                    time.sleep(0.2)
            print("1. server running at", f"{URL}/mcp")
            asyncio.run(run_client())
        finally:
            server.terminate()
            server.wait()

# Exercises:
# 1. Add a second custom route, GET /status, returning the tool count.
# 2. Log every incoming header in greet (simulates tenant extraction).
# 3. Call the server with raw httpx to see the JSON-RPC envelope:
#      httpx.post(f"{URL}/mcp", json={"jsonrpc": "2.0", "id": 1,
#                 "method": "tools/list", "params": {}},
#                 headers={"Accept": "application/json, text/event-stream"})
#    (see lesson 15 for the full raw handshake)
