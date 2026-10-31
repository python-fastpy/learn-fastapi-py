"""12 -- MCP server: share your tools with ANY AI app, in one standard way
=========================================================================

CONCEPT IN ONE LINE:
  MCP (Model Context Protocol) is a standard plug for tools. Write your tools ONCE as
  an MCP server, and any MCP app (Claude Desktop, VS Code, Cursor, your own app) can use them.

  WITHOUT MCP (lesson 10)                   WITH MCP
  each app re-writes the same tools         one server, many apps
  ┌───────┐  ┌───────┐  ┌───────┐           ┌───────┐ ┌───────┐ ┌──────────┐
  │ app A │  │ app B │  │ app C │           │ app A │ │Claude │ │ VS Code  │  ◀ MCP CLIENTS
  │+tools │  │+tools │  │+tools │           └───┬───┘ └───┬───┘ └────┬─────┘
  └───────┘  └───────┘  └───────┘               └─────────┼──────────┘
                                                          ▼  JSON-RPC over stdin/stdout
                                               ┌─────────────────────┐
                                               │ THIS FILE           │  ◀ MCP SERVER
                                               │ tools: order status │
                                               │ resource: policy    │
                                               └─────────────────────┘

  An MCP server offers 3 kinds of things:
    TOOLS      functions the model can CALL           get_order_status(order_id)
    RESOURCES  data the app can READ                  docs://refund-policy
    PROMPTS    ready-made prompt templates            (not used here)

  THE PROTOCOL = JSON-RPC 2.0, one JSON message per line on stdin/stdout:
    client ─▶ {"jsonrpc":"2.0","id":1,"method":"tools/list"}
    server ◀─ {"jsonrpc":"2.0","id":1,"result":{"tools":[...]}}
    client ─▶ {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get_order_status",...}}
    server ◀─ {"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"..."}]}}

  VERSIONS: the newest spec (2026-07-28) is stateless: clients start with "server/discover".
  Older clients (spec 2025-11-25) start with "initialize". This server answers both.

YOU DON'T RUN THIS FILE YOURSELF -- an MCP client starts it:
  - lesson 13 (13_mcp_client.py) starts it and connects llama3.2 to it
  - or add it to Claude Desktop / VS Code (see "CONNECT TO A REAL APP" at the bottom)
"""

import json
import sys

ORDERS = {"A-1001": {"status": "shipped", "eta_days": 2}, "A-1002": {"status": "processing", "eta_days": 5}}
REFUND_POLICY = "Refunds within 14 days of delivery. Money returns to the card in 5-7 business days."

TOOLS = [
    {"name": "get_order_status", "description": "Get the shipping status of an order",
     "inputSchema": {"type": "object", "required": ["order_id"],
                     "properties": {"order_id": {"type": "string", "description": "e.g. A-1001"}}}},
    {"name": "get_refund_policy", "description": "Get the company's refund policy",
     "inputSchema": {"type": "object", "properties": {}}},
]
RESOURCES = [{"uri": "docs://refund-policy", "name": "refund-policy", "mimeType": "text/plain"}]
SERVER_INFO = {"name": "acme-support", "version": "1.0.0"}
CAPABILITIES = {"tools": {}, "resources": {}}


# ---------------------------------------------------------------------------
# the real work: your tools
# ---------------------------------------------------------------------------
def call_tool(name, args):
    if name == "get_order_status":
        order = ORDERS.get(args.get("order_id", ""))
        text = json.dumps(order) if order else f"No order {args.get('order_id')!r} found"
        return {"content": [{"type": "text", "text": text}], "isError": order is None}
    if name == "get_refund_policy":
        return {"content": [{"type": "text", "text": REFUND_POLICY}], "isError": False}
    return {"content": [{"type": "text", "text": f"Unknown tool {name}"}], "isError": True}


# ---------------------------------------------------------------------------
# the protocol: one JSON-RPC request in -> one result out
# ---------------------------------------------------------------------------
def handle(method, params):
    cache = {"ttlMs": 60000, "cacheScope": "public"}
    if method == "server/discover":                                   # new clients (2026-07-28)
        return {"supportedVersions": ["2026-07-28"], "capabilities": CAPABILITIES,
                "_meta": {"io.modelcontextprotocol/serverInfo": SERVER_INFO}, **cache}
    if method == "initialize":                                        # older clients (2025-11-25)
        return {"protocolVersion": "2025-11-25", "capabilities": CAPABILITIES, "serverInfo": SERVER_INFO}
    if method == "ping":
        return {}
    if method == "tools/list":
        return {"tools": TOOLS, **cache}
    if method == "tools/call":
        return call_tool(params["name"], params.get("arguments", {}))
    if method == "resources/list":
        return {"resources": RESOURCES, **cache}
    if method == "resources/read" and params.get("uri") == "docs://refund-policy":
        return {"contents": [{"uri": params["uri"], "mimeType": "text/plain", "text": REFUND_POLICY}], **cache}
    raise LookupError(method)


def main():
    print("acme-support MCP server started (waiting for JSON-RPC on stdin)", file=sys.stderr)
    for line in sys.stdin:                         # one message per line
        msg = json.loads(line)
        if "id" not in msg:                        # a notification (e.g. notifications/initialized)
            continue                               # -> no reply allowed
        try:
            result = {"resultType": "complete", **handle(msg["method"], msg.get("params", {}))}
            reply = {"jsonrpc": "2.0", "id": msg["id"], "result": result}
        except LookupError:
            reply = {"jsonrpc": "2.0", "id": msg["id"],
                     "error": {"code": -32601, "message": f"Method not found: {msg['method']}"}}
        print(json.dumps(reply), flush=True)      # stdout is ONLY for protocol messages
        # (logs must go to stderr, never stdout -- or the client gets broken JSON)


if __name__ == "__main__":
    main()

# CONNECT TO A REAL APP -- e.g. Claude Desktop: Settings > Developer > Edit Config, add:
#   {"mcpServers": {"acme-support": {
#       "command": "python",
#       "args": ["C:\\new-assistant-v6\\learn-fastapi-py\\learn-llm-fundamentals\\simple\\ollama\\12_mcp_server.py"]}}}
# Restart the app; ask "What is the status of order A-1001?" and it will call YOUR tool.
#
# IN REAL PROJECTS use the official SDK instead of writing JSON-RPC by hand:
#   from mcp.server.fastmcp import FastMCP          # uv add mcp
#   mcp = FastMCP("acme-support")
#   @mcp.tool()
#   def get_order_status(order_id: str) -> dict: ...
#   mcp.run()
# Same protocol underneath -- this file shows you what the SDK does for you.
