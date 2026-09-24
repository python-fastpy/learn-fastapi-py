"""The same notes server, but served over HTTP instead of stdio.

Use this to try the `url` style of .mcp.json entry:

  1. Start it in its own terminal:
         uv run python demo_mcp_http.py

  2. Add it to .mcp.json alongside (or instead of) the stdio entry:
         "notes_http": { "url": "http://127.0.0.1:8200/mcp" }

  3. Check it connected:
         uv run python check_mcp.py

  4. Restart the CLI or web server to pick it up.

Note the URL ends in /mcp -- that's the path FastMCP mounts the protocol
on. Pointing at http://127.0.0.1:8200 (no /mcp) is the single most common
mistake: the host answers, so it looks reachable, but the handshake fails.
"""

from demo_mcp_server import mcp

if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=8200,
        json_response=True,
        stateless_http=True,
        show_banner=False,
    )
