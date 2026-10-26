"""HTTP client -- the server is ALREADY running
=====================================================

The stdio client started its server and owned it. Over HTTP nobody starts
the server for you: it's a service that's already up, and clients arrive by
URL. That one difference is the whole lesson.

THE FLOW
  CLIENT (this file)                              SERVER  127.0.0.1:8765
                                                  greet_server.py --http starts FIRST
  GET /health ─────────────────────────────────►  health()
              ◄────────────────────────────────   200 {"status": "healthy"}
  Client(StreamableHttpTransport(url/mcp))
  list_tools() ── POST /mcp  tools/list ───────►
              ◄────────────────────────────────   ["greet"]
  per tenant, a NEW client with its own headers:
  call_tool ── POST /mcp  X-Tenant-ID: tenant-a ►  greet() reads the header
            ◄─────────────────────────────────    {..., "tenant": "tenant-a"}

IN PRODUCTION
  backend ──HTTPS──► load balancer ──/greet──► container (MCP server)
  (one client per call,   │ health-checks GET /health
   tenant headers)        └──/other──► container (another MCP server)

  stateless_http=True is what lets the load balancer send each request to ANY
  container: no request depends on a session held in one container's memory.

Level: BASIC
Run:  uv run python basic/02_http_client.py
      (starts the server if it isn't running, and stops it again at the end --
       or run `uv run python greet_server.py --http` yourself in another terminal)
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
SERVER_FILE = Path(__file__).parent.parent / "greet_server.py"   # mcp/client/greet_server.py


def is_up() -> bool:
    try:
        return httpx.get(f"{URL}/health", timeout=0.5).status_code == 200
    except httpx.HTTPError:
        return False


def start_server_if_needed() -> subprocess.Popen | None:
    """With HTTP, somebody has to start the server -- the client never does."""
    if is_up():
        print("server      -> already running (you started it)")
        return None
    proc = subprocess.Popen([sys.executable, str(SERVER_FILE), "--http"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        if is_up():
            break
        time.sleep(0.2)
    print("server      -> started greet_server.py --http for this demo")
    return proc


async def main():
    # 1. HEALTH -- plain HTTP, no MCP involved
    async with httpx.AsyncClient() as http:
        r = await http.get(f"{URL}/health")
        print("GET /health ->", r.status_code, r.json())

    # 2. CONNECT by URL -- everything inside is the same as the stdio client
    async with Client(StreamableHttpTransport(f"{URL}/mcp")) as client:
        print("tools       ->", [t.name for t in await client.list_tools()])
        print("data        ->", (await client.call_tool("greet", {"name": "Ada"})).data)

    # a bare URL string guesses the same transport -- less to import, no headers option
    async with Client(f"{URL}/mcp") as client:
        print("bare URL    ->", (await client.call_tool("greet", {"name": "Bob"})).data)

    # 3. HEADERS -- one NEW client per call, each with its own tenant headers
    #    (tenants never share a client)
    for tenant in ("tenant-a", "tenant-b"):
        headers = {"Authorization": "Bearer fake-jwt", "X-Tenant-ID": tenant}
        async with Client(StreamableHttpTransport(f"{URL}/mcp", headers=headers)) as client:
            print(f"{tenant:<12}->", (await client.call_tool("greet", {"name": "Ada"})).data)


if __name__ == "__main__":
    server = start_server_if_needed()
    try:
        asyncio.run(main())
    finally:
        if server:                     # only stop it if WE started it
            server.terminate()
            server.wait()
            print("stopped     -> the server we started (it outlived every client)")
