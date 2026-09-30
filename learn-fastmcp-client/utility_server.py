"""A second, unrelated server -- used only by lesson 02 to demo a
multi-server client (a Client that talks to more than one server at once).

    uv run python utility_server.py --stdio
"""

import sys

from fastmcp import FastMCP

mcp = FastMCP(name="UtilityService")


@mcp.tool
def shout(text: str) -> str:
    """Uppercases text and adds emphasis."""
    return f"{text.upper()}!!!"


if __name__ == "__main__":
    if "--stdio" in sys.argv:
        mcp.run(show_banner=False)
    else:
        print("Run with --stdio -- this file is only used by lesson 02.")
