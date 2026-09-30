"""Lesson 02 -- Transports: how the client actually reaches the server
=======================================================================

A transport is the wire underneath the Client. `Client(...)` guesses one
from whatever you pass it:

    a FastMCP server object   -> in-memory   (same process, no network)
    a URL string               -> HTTP        (fastmcp.client.transports.StreamableHttpTransport)
    a Path to a .py script     -> stdio       (subprocess, PythonStdioTransport)
    a dict with "mcpServers"   -> multi-server (one client, many servers, namespaced)

You can also build a transport explicitly instead of relying on the guess --
worth doing whenever the source of the path/URL isn't trusted, since
inference will happily run a "user-supplied .py file" as a subprocess.

SSE (`SSETransport`) exists for older servers only -- prefer HTTP for
anything new.

Run:  uv run python 02_transports.py
"""

import asyncio
import subprocess
import sys
import time
import urllib.request

from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport, StreamableHttpTransport
from target_server import mcp

PORT = 8791


# ------------------------------------------------------------- 1. in-memory
async def demo_in_memory():
    async with Client(mcp) as client:
        r = await client.call_tool("greet", {"name": "Ada"})
        print("in-memory ->", r.data)


# ----------------------------------------------------------------- 2. stdio
async def demo_stdio():
    # explicit transport -- same as Client("target_server.py") would infer,
    # but with real control over args/env/cwd
    transport = PythonStdioTransport("target_server.py", args=["--stdio"])
    async with Client(transport) as client:
        r = await client.call_tool("greet", {"name": "Bob"})
        print("stdio      ->", r.data)


# ------------------------------------------------------------------ 3. http
async def demo_http():
    proc = subprocess.Popen([sys.executable, "target_server.py", "--http", str(PORT)])
    try:
        for _ in range(40):                      # wait for the /health route
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1)
                break
            except Exception:
                time.sleep(0.25)

        async with Client(StreamableHttpTransport(url=f"http://127.0.0.1:{PORT}/mcp")) as client:
            r = await client.call_tool("greet", {"name": "Cleo"})
            print("http       ->", r.data)

        # a bare URL string infers the same transport -- less to import
        async with Client(f"http://127.0.0.1:{PORT}/mcp") as client:
            r = await client.call_tool("greet", {"name": "Dee"})
            print("http (URL) ->", r.data)
    finally:
        proc.terminate()
        proc.wait(timeout=5)


# -------------------------------------------------------- 4. multi-server
async def demo_multi_server():
    """One client, two servers -- tools/resources are namespaced by server name."""
    config = {
        "mcpServers": {
            "greet": {"command": sys.executable, "args": ["target_server.py", "--stdio"]},
            "util": {"command": sys.executable, "args": ["utility_server.py", "--stdio"]},
        }
    }
    async with Client(config) as client:
        tools = sorted(t.name for t in await client.list_tools())
        print("multi-server tools:", tools)
        print("  greet_greet ->", (await client.call_tool("greet_greet", {"name": "Ada"})).data)
        print("  util_shout  ->", (await client.call_tool("util_shout", {"text": "hi"})).data)


async def main():
    await demo_in_memory()
    await demo_stdio()
    await demo_http()
    await demo_multi_server()


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Replace Client(transport) in demo_stdio with the shorthand
#    Client("target_server.py") -- same result, one less import, but note
#    the docs call bare-string inference deprecated as of fastmcp 4.0.
# 2. In demo_multi_server, call "util_shout" with a typo'd server prefix
#    ("shout" instead of "util_shout") and read the error.
# 3. Point Client() at a URL you don't control and think about what
#    "transport inference trusts its input" means for that case.
