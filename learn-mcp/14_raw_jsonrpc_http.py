"""Lesson 14 -- Raw JSON-RPC over HTTP (What the SDK Does Under the Hood)
=========================================================================

WHY THIS MATTERS:
  In all previous lessons, we used the FastMCP SDK (Client + StreamableHttpTransport)
  which hides the HTTP and JSON-RPC details. But when debugging production issues,
  reading network traces, or understanding the MCP spec, you need to know what
  actually goes over the wire.

  This lesson strips away the SDK and shows the raw HTTP POST requests with
  JSON-RPC 2.0 bodies — exactly what the backend sends to skills like
  story-drafting, text-archive, and urgent-drafting.

WHAT YOU'LL LEARN:
  1. The MCP Streamable HTTP handshake (initialize → initialized → ready)
  2. Raw JSON-RPC 2.0 request/response format for tools/list and tools/call
  3. How _meta is injected for human-in-the-loop (HITL) resume
  4. How to parse structuredContent and interrupt payloads
  5. How headers (Authorization, X-Tenant-ID) are forwarded per request
  6. Side-by-side comparison: raw HTTP vs SDK calls

Concepts:
  - JSON-RPC 2.0: { "jsonrpc": "2.0", "id": ..., "method": ..., "params": ... }
  - MCP methods: "initialize", "notifications/initialized", "tools/list", "tools/call"
  - Mcp-Session-Id: session header returned by server, sent back on subsequent requests
  - structuredContent: where interrupt/status/continuation_token live in the response
  - _meta injection: how the backend resumes interrupted skills

Flow:
  +----------+                              +------------------+
  | This     |  1. POST /mcp               | MCP Server       |
  | Script   |     {"method":"initialize"}  | (child process)  |
  | (httpx)  |  <-- {"result":{caps}}       |                  |
  |          |  <-- Mcp-Session-Id header   | Same server as   |
  |          |                              | lesson 05, but   |
  |          |  2. POST /mcp               | we call it with  |
  |          |     {"method":"notif/init"}  | raw HTTP instead |
  |          |                              | of the SDK.      |
  |          |  3. POST /mcp               |                  |
  |          |     {"method":"tools/list"}  |                  |
  |          |  <-- tool definitions        |                  |
  |          |                              |                  |
  |          |  4. POST /mcp               |                  |
  |          |     {"method":"tools/call",  |                  |
  |          |      "params":{"name":...,   |                  |
  |          |       "arguments":{...}}}    |                  |
  |          |  <-- tool result             |                  |
  +----------+                              +------------------+

  Maps to:
    mcp_protocol.py -> _one_shot_client() and call_tool_enhanced()
    What StreamableHttpTransport does internally on every call

PREREQUISITES: Lesson 05 (HTTP transport), Lesson 06 (client patterns)

Run:  uv run python 14_raw_jsonrpc_http.py

EXPECTED OUTPUT:
  Starting MCP server on port 8766...
  Server is ready.

  ============================================================
  PART 1: Raw JSON-RPC Handshake (what the SDK does on connect)
  ============================================================

  --- Step 1: initialize ---
    REQUEST:
      POST http://localhost:8766/mcp
      Headers: {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}
      Body: {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {...}}

    RESPONSE:
      Status: 200
      Mcp-Session-Id: <session-id>
      Body: {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "...", ...}}

  --- Step 2: notifications/initialized ---
    REQUEST:
      POST http://localhost:8766/mcp
      Body: {"jsonrpc": "2.0", "method": "notifications/initialized"}
    (No response body -- notifications are fire-and-forget)

  ============================================================
  PART 2: tools/list -- Discover available tools
  ============================================================

    REQUEST:
      Body: {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}

    RESPONSE:
      Tools found: 3
        - greet: Greet someone by name.
        - farewell: Say goodbye to someone by name.
        - get_weather: Get weather for a city (returns structuredContent).

  ============================================================
  PART 3: tools/call -- Call a tool
  ============================================================

    REQUEST:
      Body: {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "greet", "arguments": {"name": "Alice"}}}

    RESPONSE:
      Body: {"jsonrpc": "2.0", "id": 3, "result": {"content": [...], "isError": false}}
      Tool result text: Hello, Alice!

  ============================================================
  PART 4: tools/call with _meta (HITL resume pattern)
  ============================================================

    REQUEST:
      Body: {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "greet", "arguments": {"name": "Bob", "_meta": {"session_id": "sess_abc123", "continuation_token": "ct_xyz789", "user_response": {"action": "approve"}}}}}

    RESPONSE:
      Tool result text: Hello, Bob!
      _meta was passed to the tool (visible in server logs)

  ============================================================
  PART 5: structuredContent in response
  ============================================================

    REQUEST:
      Body: {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "get_weather", "arguments": {"city": "London"}}}

    RESPONSE:
      structuredContent: {"temperature": 18, "unit": "celsius", ...}

  ============================================================
  PART 6: Side-by-side -- SDK vs Raw HTTP
  ============================================================

    SDK call:
      result = await client.call_tool("greet", {"name": "Eve"})
      -> Hello, Eve!

    Raw HTTP call (same result):
      POST /mcp {"method": "tools/call", "params": {"name": "greet", ...}}
      -> Hello, Eve!

    Both produce identical results. The SDK just handles
    JSON-RPC framing, session headers, and handshake for you.

  Server stopped.
"""

import asyncio
import json
import multiprocessing
import time
from typing import Annotated, Any

import httpx
from fastmcp import FastMCP, Client
from fastmcp.client.transports import StreamableHttpTransport
from pydantic import Field

SERVER_PORT = 8766
SERVER_URL = f"http://localhost:{SERVER_PORT}"
MCP_ENDPOINT = f"{SERVER_URL}/mcp"

# ============================================================================
# SERVER SIDE -- same pattern as lesson 05, runs in a child process
# ============================================================================

mcp = FastMCP(name="jsonrpc-demo")


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "healthy"})


@mcp.tool
async def greet(
    name: Annotated[str, Field(description="Name to greet")],
) -> dict:
    """Greet someone by name."""
    return {"message": f"Hello, {name}!"}


@mcp.tool
async def farewell(
    name: Annotated[str, Field(description="Name to say goodbye to")],
) -> dict:
    """Say goodbye to someone by name."""
    return {"message": f"Goodbye, {name}!"}


@mcp.tool
async def get_weather(
    city: Annotated[str, Field(description="City name")],
) -> dict:
    """Get weather for a city (returns structuredContent)."""
    return {
        "temperature": 18,
        "unit": "celsius",
        "city": city,
        "condition": "partly cloudy",
    }


def run_server():
    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=SERVER_PORT,
        json_response=True,
        stateless_http=True,
    )


# ============================================================================
# RAW JSON-RPC CLIENT -- no SDK, just httpx + hand-crafted JSON-RPC
# ============================================================================

class RawMCPClient:
    """Minimal MCP client using raw HTTP POST + JSON-RPC 2.0.

    This is what StreamableHttpTransport does internally.
    In production, the SDK handles all of this -- this class
    exists purely for learning.
    """

    def __init__(self, url: str, headers: dict[str, str] | None = None):
        self.url = url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            **(headers or {}),
        }
        self.session_id: str | None = None
        self._next_id = 1

    def _make_request(self, method: str, params: dict | None = None) -> dict:
        """Build a JSON-RPC 2.0 request envelope."""
        req: dict[str, Any] = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if not method.startswith("notifications/"):
            req["id"] = self._next_id
            self._next_id += 1
        if params is not None:
            req["params"] = params
        return req

    def _get_headers(self) -> dict[str, str]:
        """Include Mcp-Session-Id if we have one from a previous response."""
        hdrs = dict(self.headers)
        if self.session_id:
            hdrs["Mcp-Session-Id"] = self.session_id
        return hdrs

    async def send(
        self,
        http: httpx.AsyncClient,
        method: str,
        params: dict | None = None,
        label: str = "",
    ) -> dict | None:
        """Send a JSON-RPC request and return the parsed response."""
        body = self._make_request(method, params)
        headers = self._get_headers()

        if label:
            print(f"  --- {label} ---")
        print(f"    REQUEST:")
        print(f"      POST {self.url}")
        if label == "Step 1: initialize":
            print(f"      Headers: {{'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}}")
        print(f"      Body: {json.dumps(body)}")
        print()

        resp = await http.post(self.url, json=body, headers=headers)

        # Capture session ID from response headers
        new_session_id = resp.headers.get("mcp-session-id")
        if new_session_id:
            self.session_id = new_session_id

        # Notifications have no response body
        if method.startswith("notifications/"):
            print(f"    (No response body -- notifications are fire-and-forget)")
            print()
            return None

        print(f"    RESPONSE:")
        print(f"      Status: {resp.status_code}")
        if new_session_id:
            print(f"      Mcp-Session-Id: {new_session_id}")

        result = resp.json()
        print(f"      Body: {json.dumps(result, indent=None)[:200]}...")
        print()
        return result


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

async def part1_handshake(raw: RawMCPClient, http: httpx.AsyncClient):
    """The 3-step MCP handshake that happens on every SDK client connect."""
    print("=" * 60)
    print("PART 1: Raw JSON-RPC Handshake (what the SDK does on connect)")
    print("=" * 60)
    print()

    # Step 1: initialize -- announce client capabilities
    result = await raw.send(http, "initialize", params={
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "learn-mcp-raw-client", "version": "0.1.0"},
    }, label="Step 1: initialize")

    if result and "result" in result:
        proto = result["result"].get("protocolVersion", "unknown")
        print(f"    Server protocol version: {proto}")
        caps = list(result["result"].get("capabilities", {}).keys())
        print(f"    Server capabilities: {caps}")
        print()

    # Step 2: notifications/initialized -- tell server we're ready
    await raw.send(http, "notifications/initialized", label="Step 2: notifications/initialized")


async def part2_list_tools(raw: RawMCPClient, http: httpx.AsyncClient):
    """Discover tools -- the raw version of client.list_tools()."""
    print("=" * 60)
    print("PART 2: tools/list -- Discover available tools")
    print("=" * 60)
    print()

    result = await raw.send(http, "tools/list", params={})

    if result and "result" in result:
        tools = result["result"].get("tools", [])
        print(f"    Tools found: {len(tools)}")
        for t in tools:
            print(f"      - {t['name']}: {t.get('description', '')}")
        print()


async def part3_call_tool(raw: RawMCPClient, http: httpx.AsyncClient):
    """Call a tool -- the raw version of client.call_tool()."""
    print("=" * 60)
    print("PART 3: tools/call -- Call a tool")
    print("=" * 60)
    print()

    result = await raw.send(http, "tools/call", params={
        "name": "greet",
        "arguments": {"name": "Alice"},
    })

    if result and "result" in result:
        content = result["result"].get("content", [])
        for block in content:
            if block.get("type") == "text":
                text = block["text"]
                try:
                    parsed = json.loads(text)
                    print(f"    Tool result: {parsed.get('message', text)}")
                except (json.JSONDecodeError, ValueError):
                    print(f"    Tool result text: {text}")
        print()


async def part4_meta_injection(raw: RawMCPClient, http: httpx.AsyncClient):
    """Call a tool with _meta -- how the backend resumes interrupted skills."""
    print("=" * 60)
    print("PART 4: tools/call with _meta (HITL resume pattern)")
    print("=" * 60)
    print()

    # In production, mcp_protocol.py injects _meta like this:
    #   tool_arguments["_meta"] = {
    #       "session_id": session_id,
    #       "continuation_token": continuation_token,
    #       "user_response": user_response,
    #   }
    result = await raw.send(http, "tools/call", params={
        "name": "greet",
        "arguments": {
            "name": "Bob",
            "_meta": {
                "session_id": "sess_abc123",
                "continuation_token": "ct_xyz789",
                "user_response": {"action": "approve"},
            },
        },
    })

    if result and "result" in result:
        content = result["result"].get("content", [])
        for block in content:
            if block.get("type") == "text":
                text = block["text"]
                try:
                    parsed = json.loads(text)
                    print(f"    Tool result: {parsed.get('message', text)}")
                except (json.JSONDecodeError, ValueError):
                    print(f"    Tool result text: {text}")
        print(f"    _meta was passed in arguments (production skills read it for resume)")
        print()

    # -- Annotation: What an interrupt response looks like --
    print("    [INFO] In production, an interrupted skill returns:")
    print('    {')
    print('      "jsonrpc": "2.0", "id": 4,')
    print('      "result": {')
    print('        "content": [{"type": "text", "text": "Review the draft"}],')
    print('        "isError": false,')
    print('        "structuredContent": {')
    print('          "status": "interrupted",')
    print('          "interrupt": {')
    print('            "type": "NEWS_BUZZ.REVIEW",')
    print('            "message": "Review the generated buzz",')
    print('            "actions": ["approve", "refine", "reject"]')
    print("          },")
    print('          "continuation_token": "ct_xyz789"')
    print("        }")
    print("      }")
    print("    }")
    print()
    print("    The backend then calls _call_tool_result_to_dict() which flattens")
    print("    structuredContent to top-level keys (status, interrupt, continuation_token)")
    print("    so downstream consumers can read them directly.")
    print()


async def part5_structured_content(raw: RawMCPClient, http: httpx.AsyncClient):
    """Show structuredContent in responses."""
    print("=" * 60)
    print("PART 5: structuredContent in response")
    print("=" * 60)
    print()

    result = await raw.send(http, "tools/call", params={
        "name": "get_weather",
        "arguments": {"city": "London"},
    })

    if result and "result" in result:
        content = result["result"].get("content", [])
        structured = result["result"].get("structuredContent")

        print(f"    content blocks: {len(content)}")
        for block in content:
            if block.get("type") == "text":
                text = block["text"]
                try:
                    parsed = json.loads(text)
                    print(f"    content[0].text (parsed): {json.dumps(parsed)}")
                except (json.JSONDecodeError, ValueError):
                    print(f"    content[0].text: {text}")

        if structured:
            print(f"    structuredContent: {json.dumps(structured)}")
        else:
            print(f"    structuredContent: null (data is in content[0].text as JSON)")
            print(f"    -> Backend fallback: parse content[0].text as JSON and flatten")
        print()


async def part6_sdk_vs_raw(raw: RawMCPClient, http: httpx.AsyncClient):
    """Side-by-side: SDK call vs raw HTTP call -- same result."""
    print("=" * 60)
    print("PART 6: Side-by-side -- SDK vs Raw HTTP")
    print("=" * 60)
    print()

    # SDK call
    print("  SDK call:")
    print('    result = await client.call_tool("greet", {"name": "Eve"})')
    transport = StreamableHttpTransport(url=MCP_ENDPOINT)
    async with Client(transport) as client:
        sdk_result = await client.call_tool("greet", {"name": "Eve"})
        first_block = sdk_result.content[0] if hasattr(sdk_result, "content") else sdk_result[0]
        text = getattr(first_block, "text", str(first_block))
        try:
            parsed = json.loads(text)
            print(f"    -> {parsed.get('message', text)}")
        except (json.JSONDecodeError, ValueError):
            print(f"    -> {text}")
    print()

    # Raw HTTP call
    print("  Raw HTTP call (same result):")
    print('    POST /mcp {"method": "tools/call", "params": {"name": "greet", ...}}')

    # Need a fresh handshake for a new raw client
    raw2 = RawMCPClient(MCP_ENDPOINT)

    # Silent handshake (no printing)
    init_body = {
        "jsonrpc": "2.0", "id": 100, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "compare", "version": "0.1.0"}},
    }
    resp = await http.post(MCP_ENDPOINT, json=init_body, headers=raw2._get_headers())
    sid = resp.headers.get("mcp-session-id")
    if sid:
        raw2.session_id = sid

    notif_body = {"jsonrpc": "2.0", "method": "notifications/initialized"}
    await http.post(MCP_ENDPOINT, json=notif_body, headers=raw2._get_headers())

    call_body = {
        "jsonrpc": "2.0", "id": 101, "method": "tools/call",
        "params": {"name": "greet", "arguments": {"name": "Eve"}},
    }
    resp = await http.post(MCP_ENDPOINT, json=call_body, headers=raw2._get_headers())
    result = resp.json()
    content = result.get("result", {}).get("content", [])
    for block in content:
        if block.get("type") == "text":
            try:
                parsed = json.loads(block["text"])
                print(f"    -> {parsed.get('message', block['text'])}")
            except (json.JSONDecodeError, ValueError):
                print(f"    -> {block['text']}")
    print()
    print("  Both produce identical results. The SDK just handles")
    print("  JSON-RPC framing, session headers, and handshake for you.")
    print()


# ============================================================================
# BONUS: Show what production headers look like
# ============================================================================

def print_production_headers():
    """Show what the backend sends in production (for reference)."""
    print("=" * 60)
    print("REFERENCE: Production HTTP headers (from mcp_protocol.py)")
    print("=" * 60)
    print()
    print("  When the backend calls a skill, it sends these headers:")
    print()
    print("    POST https://mcp-story-drafting.internal/mcp")
    print("    Content-Type: application/json")
    print("    Accept: application/json, text/event-stream")
    print("    Authorization: Bearer eyJhbGciOiJSUzI1NiIs...")
    print("    X-Tenant-ID: leon-shubham")
    print("    X-User-ID: john.doe@reuters.com")
    print("    X-Request-ID: req_a1b2c3d4")
    print("    Mcp-Session-Id: <from-previous-response>")
    print()
    print("  These are passed via StreamableHttpTransport(url=..., headers=...):")
    print()
    print("    transport = StreamableHttpTransport(")
    print("        url=server.endpoint_url,")
    print("        headers=dict(usr_ctx_original_headers),  # JWT, tenant, tracing")
    print("    )")
    print("    client = Client(transport, timeout=timeout)")
    print()
    print("  The SDK adds Content-Type, Accept, and Mcp-Session-Id automatically.")
    print()


# ============================================================================
# MAIN
# ============================================================================

async def run_demo():
    async with httpx.AsyncClient(timeout=30.0) as http:
        raw = RawMCPClient(
            url=MCP_ENDPOINT,
            headers={
                "Authorization": "Bearer fake-jwt-for-demo",
                "X-Tenant-ID": "demo-tenant",
            },
        )

        await part1_handshake(raw, http)
        await part2_list_tools(raw, http)
        await part3_call_tool(raw, http)
        await part4_meta_injection(raw, http)
        await part5_structured_content(raw, http)
        await part6_sdk_vs_raw(raw, http)

    print_production_headers()


if __name__ == "__main__":
    server_proc = multiprocessing.Process(target=run_server, daemon=True)
    server_proc.start()

    print(f"Starting MCP server on port {SERVER_PORT}...")
    for _ in range(30):
        try:
            import urllib.request
            urllib.request.urlopen(f"{SERVER_URL}/health", timeout=1)
            break
        except Exception:
            time.sleep(0.3)
    else:
        print("Server failed to start!")
        server_proc.terminate()
        raise SystemExit(1)

    print("Server is ready.\n")

    try:
        asyncio.run(run_demo())
    finally:
        server_proc.terminate()
        server_proc.join(timeout=3)
        print("Server stopped.")

    # -- Key takeaway --------------------------------------------------------
    # The MCP protocol over HTTP is just JSON-RPC 2.0 over POST:
    #
    # 1. HANDSHAKE (per connection):
    #    POST /mcp  {"method": "initialize", ...}    -> server caps + session ID
    #    POST /mcp  {"method": "notifications/initialized"}  -> fire-and-forget
    #
    # 2. DISCOVERY:
    #    POST /mcp  {"method": "tools/list"}          -> tool definitions
    #    POST /mcp  {"method": "resources/list"}      -> resource URIs
    #    POST /mcp  {"method": "prompts/list"}        -> prompt templates
    #
    # 3. TOOL CALLS:
    #    POST /mcp  {"method": "tools/call", "params": {"name": ..., "arguments": {...}}}
    #    Response:   {"result": {"content": [...], "isError": false, "structuredContent": {...}}}
    #
    # 4. HITL RESUME (backend injects _meta):
    #    arguments: {"param1": "val", "_meta": {"session_id": ..., "continuation_token": ..., "user_response": ...}}
    #
    # 5. INTERRUPT RESPONSE (skill pauses):
    #    structuredContent: {"status": "interrupted", "interrupt": {...}, "continuation_token": "..."}
    #
    # In production, the FastMCP SDK (Client + StreamableHttpTransport)
    # handles all of this. You never write raw JSON-RPC -- but knowing
    # the wire format is essential for debugging and understanding the system.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a tool that returns an interrupt (status: "interrupted") and
    #    parse the structuredContent in the raw client
    # 2. Implement the full _call_tool_result_to_dict() logic from
    #    mcp_protocol.py that flattens structuredContent to top-level keys
    # 3. Add a raw call to resources/list and prompts/list
    # 4. Use Wireshark or mitmproxy to capture real traffic between
    #    the backend and a locally running skill server
