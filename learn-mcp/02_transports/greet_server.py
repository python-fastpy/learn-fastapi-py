"""The greet server -- ONE definition, reached over either transport
====================================================================

This file is only the SERVER. It does not call itself and takes no
command-line flags. The other files in this folder use it:

  greet_server.py   (this file)  run it -> it speaks STDIO
  http_server.py                 imports `mcp` below -> serves it over HTTP
  stdio_client.py                launches this file as a child process

Run:  uv run python 02_transports/greet_server.py

  Nothing prints. That is correct: over stdio, stdout is reserved for
  JSON-RPC replies, so the server must stay silent and wait on stdin.
  Exercise 3 in stdio_client.py has you type those messages by hand.
  Ctrl+C to stop.
"""

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_http_headers
from starlette.responses import JSONResponse

mcp = FastMCP("greetings")


@mcp.tool
def greet(name: str) -> dict:
    """Greet someone by name."""
    if not name.strip():
        raise ToolError("name cannot be empty")          # the client sees this message
    result = {"greeting": f"Hello, {name}!"}

    # HTTP requests can carry headers; stdio has none, so this is empty
    # there. One tool, behaving correctly on both transports.
    tenant = get_http_headers().get("x-tenant-id")
    if tenant:
        result["tenant"] = tenant
    return result


# A normal REST endpoint next to /mcp, for ALB/ECS health checks. It only
# exists when this server is served over HTTP -- stdio has no URLs.
@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "healthy"})


if __name__ == "__main__":
    # stdio is mcp.run()'s default: requests arrive on stdin, replies leave
    # on stdout. http_server.py serves this same `mcp` over HTTP instead.
    mcp.run(show_banner=False)
