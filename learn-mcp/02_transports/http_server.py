"""The same greet server, served over HTTP
==========================================

The whole file is one call. The server object comes from greet_server.py
unchanged: a transport is a road, not a rewrite.

  greet_server.py   defines `mcp` (greet + /health)
        │
        ├── run greet_server.py ──► STDIO   (one client, its own parent)
        └── run THIS file ────────► HTTP    (many clients, by URL)

Run:  uv run python 02_transports/http_server.py

  It then serves, until you Ctrl+C it:
    POST /mcp     the MCP endpoint
    GET  /health  plain REST, for the load balancer

  Leave it running and start http_client.py in another terminal -- or just
  run that client on its own, and it will start this file for you.
"""

from greet_server import mcp

if __name__ == "__main__":
    print("serving http://127.0.0.1:8765/mcp  (Ctrl+C to stop)")
    mcp.run(
        transport="http", host="127.0.0.1", port=8765,
        json_response=True,       # reply with plain JSON, not a stream
        stateless_http=True,      # no session between requests -> any container can answer
        show_banner=False,
    )
