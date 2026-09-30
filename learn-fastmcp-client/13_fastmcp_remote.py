"""Lesson 13 -- fastmcp-remote: bridging a remote server to a local host
============================================================================

Every earlier lesson called `Client(...)` from your OWN Python code. But
some MCP hosts (certain desktop apps, IDE extensions) only know how to
launch a local command over stdio -- they can't speak HTTP directly to a
remote server. `fastmcp-remote` is a small standalone tool that closes that
gap: it's a stdio process that internally opens a normal FastMCP `Client`
to a remote HTTP/SSE server and relays everything between the two.

    host expecting stdio  <-->  fastmcp-remote  <-->  Client  <-->  remote HTTP server

Use it ONLY for this bridging job. For running your own local Python server
files, `fastmcp run` (lesson 02's territory) is the right tool instead.

RUNNING IT (no separate install needed for most hosts)

    uvx fastmcp-remote https://example.com/mcp

HOST CONFIG (e.g. in a desktop app's MCP settings)

    {
      "mcpServers": {
        "remote-api": {
          "command": "uvx",
          "args": ["fastmcp-remote", "https://example.com/mcp"]
        }
      }
    }

AUTH

    OAuth is on by default (opens a browser the first time, then caches
    tokens under ~/.fastmcp/remote). For a bearer token instead:

        uvx fastmcp-remote https://example.com/mcp \\
            --header "Authorization: Bearer <token>"

    For an unauthenticated dev server:  --auth none

TLS

    --verify /path/to/ca-bundle.pem     trust a self-signed certificate
    --verify false                      skip verification (insecure -- dev only)

This lesson has no live demo function -- there's no Python API here, just a
CLI. The "try it yourself" step below uses this project's own HTTP server
as the remote end.
"""

print(__doc__)

print(
    "Try it yourself:\n"
    "  1. uv run python target_server.py --http 8791\n"
    "  2. in another terminal: uvx fastmcp-remote http://127.0.0.1:8791/mcp --auth none\n"
    "  3. point a stdio-only MCP host at that second command.\n"
)

# Exercises:
# 1. Run the two commands above and confirm fastmcp-remote's own log shows
#    a successful connection to target_server.py.
# 2. Add --header "X-Debug: 1" and check (via a custom_route on the server)
#    that the header actually arrives.
# 3. Compare this to lesson 02's demo_http(): fastmcp-remote is doing
#    exactly what StreamableHttpTransport does there, just packaged as a
#    subprocess a non-Python host can launch.
