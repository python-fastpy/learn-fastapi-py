"""Lesson 14 -- The client-only package: fastmcp-slim
========================================================

Every lesson so far imported `from fastmcp import Client` -- but the full
`fastmcp` package also contains the entire SERVER framework (this whole
learn-fastmcp-server curriculum's worth of code): providers, transforms,
auth, middleware, the works. If your project only ever CONNECTS to MCP
servers and never builds one, that's a lot of dead weight to depend on.

`fastmcp-slim` is the same client, minus all of that.

    pip install "fastmcp-slim[client]"

SAME IMPORT NAMESPACE -- your code doesn't change:

    from fastmcp import Client        # works identically on either package

WHAT'S INCLUDED
    - Client() to a remote HTTP/SSE server
    - Client() to a local script over stdio
    - a single-server config dict
    - optional LLM sampling handlers: pip install "fastmcp-slim[client,openai]"
      (also available: anthropic, gemini)

WHAT'S NOT INCLUDED (needs the full `fastmcp` package instead)
    - defining or running a FastMCP server (`FastMCP(...)`, `@mcp.tool`, ...)
    - an in-memory Client(mcp) pointed at a server OBJECT (lessons 01-12
      all did this for convenience -- a slim-only project would connect
      over stdio or HTTP instead, exactly like lesson 02's other demos)
    - multi-server config dicts
    - proxies, server auth, middleware

WHY IT EXISTS

    If you're a framework author embedding MCP connectivity into your own
    tool, or building a custom LLM host, your users shouldn't need to
    install a whole server framework just so your code can call
    `Client(...)`. `fastmcp-slim[client]` is that smaller dependency.

    Most people building or serving MCP tools should still just use plain
    `fastmcp` -- it's the default, and it's a superset.

This lesson has no live demo: the point is a smaller pip install, not a
different API. Every earlier lesson's CLIENT code (not target_server.py,
which is a real server) would run unchanged on fastmcp-slim.
"""

print(__doc__)

# Exercises:
# 1. In a fresh virtualenv, `pip install "fastmcp-slim[client]"` and re-run
#    lesson 02's demo_http() and demo_stdio() against a target_server.py
#    process started separately -- both should work unchanged.
# 2. Try FastMCP(...) in that same environment and read the ImportError.
# 3. Try Client(mcp) (the in-memory transport every other lesson in this
#    folder uses) in that environment -- there's no local `mcp` object to
#    pass, since defining one needs the full package.
