"""Lesson 14 -- The Raw Wire: JSON-RPC 2.0 over HTTP
====================================================

Every lesson so far called greet through Client(...). Here we send the same
call by hand with httpx, so you can read what the SDK puts on the wire.

Every MCP message is a JSON-RPC 2.0 envelope POSTed to /mcp:

    {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {...}}
     └─ always "2.0"   └─ ties   └─ what to do      └─ the arguments
                          the reply                    (drop "id" and it
                          to this request               becomes a one-way
                                                        notification)

  ┌─── THIS SCRIPT (httpx) ───┐                 ┌── greet-server :8766 ──┐
  │ 1. POST initialize        │ ──────────────► │ protocol + capabilities│
  │                           │ ◄────────────── │ (+ a session id, if the│
  │                           │                 │  server is stateful)   │
  │ 2. POST notifications/    │ ──────────────► │ no id -> no reply body,│
  │        initialized        │                 │ just 202 Accepted      │
  │ 3. POST tools/list        │ ──────────────► │ greet's schema         │
  │ 4. POST tools/call        │ ──────────────► │ greet("Shubham") runs  │
  │        name + arguments   │ ◄────────────── │ content +              │
  │                           │                 │ structuredContent      │
  │ 5. POST tools/call        │ ──────────────► │ params._meta -> the    │
  │        + params._meta     │                 │ tool reads it via ctx  │
  └───────────────────────────┘                 └────────────────────────┘

  1-2 are the handshake, done once per connection -- that is what `async with
      Client(...)` is quietly doing before your first call.
  3   is client.list_tools().
  4   is client.call_tool("greet", {...}).
  5   is how a paused skill gets resumed: the backend puts the session id,
      continuation token and the user's answer in params._meta (NOT in
      arguments -- arguments are the tool's own parameters). The tool reads
      them from ctx.request_context.meta (lesson 06).

  Mcp-Session-Id: a STATEFUL server hands one back on initialize and expects
  every later POST to echo it. This server runs stateless_http=True -- the way
  skills run behind a load balancer, where any instance may take the next
  request -- so no session is issued and step 1 prints None. The SDK copes
  with either.

Run:  uv run python 14_raw_jsonrpc_http.py      (spawns the server, then stops it)

Maps to: mcp_protocol.py (_one_shot_client, call_tool_enhanced) -- and what
StreamableHttpTransport does internally on every single call
"""

import asyncio
import json
import multiprocessing
import time
import urllib.request
from typing import Any

import httpx
from fastmcp import Client, Context, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from starlette.responses import JSONResponse

PORT = 8766
MCP_URL = f"http://localhost:{PORT}/mcp"

# -- The server: one greet tool ----------------------------------------------

mcp = FastMCP(name="greet-server")


@mcp.tool
async def greet(name: str, ctx: Context) -> dict:
    """Greet someone by name."""
    meta = ctx.request_context.meta                 # params._meta, if the caller sent any
    return {
        "message": f"Hello, {name}!",
        "resumed": bool(meta and getattr(meta, "continuation_token", None)),
    }


@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    return JSONResponse({"status": "ok"})


def serve():
    mcp.run(transport="http", host="127.0.0.1", port=PORT, json_response=True,
            stateless_http=True, show_banner=False, log_level="warning")


# -- A hand-rolled MCP client: httpx + JSON-RPC envelopes --------------------

class RawMCPClient:
    """What StreamableHttpTransport does internally. For learning only."""

    def __init__(self, url: str, headers: dict[str, str] | None = None):
        self.url = url
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",   # both, per the MCP spec
            **(headers or {}),                                 # prod: Authorization, X-Tenant-ID
        }
        self.session_id: str | None = None
        self._next_id = 0

    async def send(self, http: httpx.AsyncClient, method: str, params: dict | None = None) -> dict | None:
        body: dict[str, Any] = {"jsonrpc": "2.0", "method": method}
        if not method.startswith("notifications/"):    # notifications carry no id
            self._next_id += 1
            body["id"] = self._next_id
        if params is not None:
            body["params"] = params

        headers = dict(self.headers)
        if self.session_id:                            # echo the session back
            headers["Mcp-Session-Id"] = self.session_id

        print(f"  --> {json.dumps(body)[:150]}")
        resp = await http.post(self.url, json=body, headers=headers)

        self.session_id = resp.headers.get("mcp-session-id") or self.session_id
        if method.startswith("notifications/"):
            print(f"  <-- {resp.status_code} (no body: nothing to reply to)")
            return None

        print(f"  <-- {resp.status_code} {json.dumps(resp.json())[:150]}")
        return resp.json()


async def demo():
    async with httpx.AsyncClient(timeout=30.0) as http:
        raw = RawMCPClient(MCP_URL, headers={"Authorization": "Bearer fake-jwt-for-demo"})

        # 1. initialize -- announce who we are, learn what the server supports
        print("1. initialize")
        r = await raw.send(http, "initialize", {
            "protocolVersion": "2025-03-26",
            "capabilities": {},
            "clientInfo": {"name": "raw-client", "version": "0.1.0"},
        })
        print(f"     protocol    : {r['result']['protocolVersion']}")
        print(f"     capabilities: {list(r['result']['capabilities'])}")
        print(f"     session id  : {raw.session_id}   (stateless server -> none issued)\n")

        # 2. notifications/initialized -- no id, so the server sends no result
        print("2. notifications/initialized")
        await raw.send(http, "notifications/initialized")
        print()

        # 3. tools/list == client.list_tools()
        print("3. tools/list")
        r = await raw.send(http, "tools/list", {})
        for t in r["result"]["tools"]:
            print(f"     {t['name']}({', '.join(t['inputSchema']['properties'])}) -- {t['description']}")
        print()

        # 4. tools/call == client.call_tool("greet", {...})
        print("4. tools/call")
        r = await raw.send(http, "tools/call", {"name": "greet", "arguments": {"name": "Shubham"}})
        print(f"     content[0].text   : {r['result']['content'][0]['text']}")
        print(f"     structuredContent: {r['result'].get('structuredContent')}")
        print(f"     isError          : {r['result'].get('isError')}\n")

        # 5. params._meta -- the HITL resume channel (lesson 06)
        print("5. tools/call with params._meta (resume)")
        r = await raw.send(http, "tools/call", {
            "name": "greet",
            "arguments": {"name": "Shubham"},          # the tool's own parameters
            "_meta": {                                  # sibling of arguments, NOT inside it
                "session_id": "sess_abc123",
                "continuation_token": "ct_xyz789",
                "user_response": {"action": "approve"},
            },
        })
        print(f"     tool saw a continuation_token: {r['result']['structuredContent']['resumed']}")
        print("     an interrupted skill replies with structuredContent:")
        print('       {"status": "interrupted", "interrupt": {...}, "continuation_token": "..."}\n')

        # 6. The SDK does all five steps for you
        print("6. the same call through the SDK")
        async with Client(StreamableHttpTransport(url=MCP_URL)) as client:
            r = await client.call_tool("greet", {"name": "Shubham"})
            print(f"     call_tool -> {r.data['message']}")
        print("     one line; the handshake, session header and framing are hidden")


if __name__ == "__main__":
    proc = multiprocessing.Process(target=serve, daemon=True)
    proc.start()
    for _ in range(40):
        try:
            urllib.request.urlopen(f"http://localhost:{PORT}/health", timeout=1)
            break
        except Exception:
            time.sleep(0.25)
    else:
        proc.terminate()
        raise SystemExit(f"server on :{PORT} never came up")

    print(f"greet-server up on :{PORT}\n")
    try:
        asyncio.run(demo())
    finally:
        proc.terminate()
        proc.join(timeout=3)
        print("\nserver stopped")

# Exercises:
# 1. Move the _meta block from step 5 inside "arguments" -- the tool no longer
#    sees it. That is why it is a sibling of arguments, not a member.
# 2. Skip step 1 and call tools/list first. What error does the server return?
# 3. Send two requests with the same "id" -- does anything complain?
# 4. Add raw resources/list and prompts/list calls (lesson 04 over the wire).
