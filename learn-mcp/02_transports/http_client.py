"""Lesson 02, part B -- MCP Client over HTTP: the server is already running
===========================================================================

Part A's client started its server and owned it. Over HTTP nobody starts the
server for you -- it is a service that was already up, and clients arrive by
URL. That one difference is the whole lesson.

  5. SERVER    http_server.py                          serve POST /mcp
  6. HEALTH    @mcp.custom_route("/health")            plain GET for the load balancer
  7. CONNECT   Client(StreamableHttpTransport(url))    connect by URL, same calls as part A
  8. HEADERS   StreamableHttpTransport(url, headers=)  JWT + tenant id on every request;
                                                       the tool reads them server-side

  ════════════════════════════════════════════════════════════════════════════
  PART B FLOW
  ════════════════════════════════════════════════════════════════════════════
  CLIENT (this file)                                 HTTP SERVER  127.0.0.1:8765
  ──────────────────                                 ───────────────────────────
                                                     5. http_server.py starts
                                                        FIRST and listens on
                                                          POST /mcp    (MCP)
                                                          GET  /health (plain REST)
         │
  6. GET /health  ────────────────────────────────►  health()
                  ◄───────────────────────────────  200 {"status": "healthy"}
         │
  7. Client(StreamableHttpTransport(url/mcp))
     list_tools()  ──── POST /mcp  tools/list ─────►
                  ◄───────────────────────────────  ["greet"]
         │
  8. for each tenant -- a NEW client with its own headers:
     ┌─ tenant-a ──────────────────────────────────────────────────────────────┐
     │ call_tool("greet") ── POST /mcp  X-Tenant-ID: tenant-a ─►  greet() reads │
     │                    ◄── {"greeting": ..., "tenant": "tenant-a"}  header   │
     └─────────────────────────────────────────────────────────────────────────┘
     ┌─ tenant-b ──────────────────────────────────────────────────────────────┐
     │ call_tool("greet") ── POST /mcp  X-Tenant-ID: tenant-b ─►  greet() reads │
     │                    ◄── {"greeting": ..., "tenant": "tenant-b"}  header   │
     └─────────────────────────────────────────────────────────────────────────┘

  IN PRODUCTION
  ─────────────
  backend ──HTTPS──► ALB ──/story-drafting──► ECS container (MCP server, port 8004)
  (one-shot client      │   (health-checks
   per call, tenant     │    GET /health)
   headers)             └──/text-archive────► ECS container (MCP server)

  stateless_http=True is what lets the ALB send each request to ANY container:
  no request depends on a session kept in one container's memory.

Run:  uv run python 02_transports/http_client.py

  If http_server.py is already running, this connects to it and leaves it
  alone. If not, this file starts it for the demo and stops it at the end --
  because with HTTP somebody has to, and the client never does it for you.
  Try it both ways: step 5 tells you which happened.

Maps to: mcp_protocol.py -- one-shot client per call with per-request tenant
headers (case 8); story-drafting/src/main.py run block (case 5, /health)
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

URL = "http://127.0.0.1:8765"
SERVER_FILE = Path(__file__).with_name("http_server.py")


def is_up() -> bool:
    """Is anything answering /health yet?"""
    try:
        return httpx.get(f"{URL}/health", timeout=0.5).status_code == 200
    except httpx.HTTPError:
        return False


def start_server_if_needed() -> subprocess.Popen | None:
    """Start the server only if it isn't already running. Returns it if we did."""
    if is_up():
        print("5. server       -> already running (you started it yourself)")
        return None

    proc = subprocess.Popen([sys.executable, str(SERVER_FILE)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        if is_up():
            break
        time.sleep(0.2)
    print("5. server       -> we started http_server.py for this demo")
    return proc


async def main():
    # 6. HEALTH -- plain HTTP, no MCP involved
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{URL}/health")
        print("6. GET /health  ->", r.status_code, r.json())          # 200 {'status': 'healthy'}

    # 7. CONNECT -- by URL. Everything inside the block is the same as part A.
    async with Client(StreamableHttpTransport(f"{URL}/mcp")) as client:
        print("7. tools        ->", [t.name for t in await client.list_tools()])   # ['greet']
        r = await client.call_tool("greet", {"name": "Shubham"})
        print("   data         ->", r.data)          # {'greeting': 'Hello, Shubham!'}

    # 8. HEADERS -- one NEW client per call, each with its own tenant headers
    #    (the production "one-shot client" pattern: tenants never share a client)
    for tenant in ("tenant-a", "tenant-b"):
        headers = {"Authorization": "Bearer fake-jwt", "X-Tenant-ID": tenant}
        async with Client(StreamableHttpTransport(f"{URL}/mcp", headers=headers)) as client:
            r = await client.call_tool("greet", {"name": "Shubham"})
            print(f"8. {tenant:<13}->", r.data)      # {... 'tenant': 'tenant-a'} / 'tenant-b'


if __name__ == "__main__":
    server = start_server_if_needed()
    try:
        asyncio.run(main())
    finally:
        if server:                      # only ours to stop; never yours
            server.terminate()
            server.wait()
            print("   stopped         -> the server we started; it had outlived both clients")

# Exercises:
# 1. Start http_server.py in one terminal, then run this file in two others
#    at once. Could you do that with part A's stdio? Why not?
# 2. With the server running, run this file and watch step 5 change.
# 3. Add a second custom route to greet_server.py, GET /status, returning the
#    tool count, and fetch it here the way step 6 fetches /health.
# 4. Drop the X-Tenant-ID header from one call -- what does greet() return
#    then, and why is that the same result stdio always gives?
