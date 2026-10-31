"""13 -- MCP client: connect llama3.2 to the MCP server from lesson 12
=====================================================================

CONCEPT IN ONE LINE:
  Your app (the MCP HOST) starts the server, ASKS it which tools it has, gives those
  tools to the model, and forwards the model's tool calls to the server.

   ┌──────────────────────── YOUR APP (this file) = MCP HOST ─────────────────────────┐
   │                                                                                  │
   │  1. start server ──────────────────────────────▶ ┌──────────────────────────┐    │
   │  2. "server/discover"  (who are you?)  ────────▶ │  12_mcp_server.py        │    │
   │  3. "tools/list"       (what can you do?) ─────▶ │  (separate process,      │    │
   │                        ◀── get_order_status, ... │   talks on stdin/stdout) │    │
   │  4. give tools to llama3.2 (Ollama format)       │                          │    │
   │  5. model asks get_order_status("A-1001")        │                          │    │
   │  6. "tools/call" ──────────────────────────────▶ │  runs the function       │    │
   │                  ◀── {"status": "shipped", ...}  └──────────────────────────┘    │
   │  7. send result to model ──▶ final answer                                        │
   └──────────────────────────────────────────────────────────────────────────────────┘

  The model never talks to the MCP server. Your app is always in the middle.
  Compare with lesson 10: same tool loop -- only now the tools come from a SERVER,
  so you can add new tools without changing this file.
"""

import json
import subprocess
import sys
from pathlib import Path

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"

META = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",      # sent on every request
        "io.modelcontextprotocol/clientInfo": {"name": "lesson-13", "version": "1.0"},
        "io.modelcontextprotocol/clientCapabilities": {}}


class MCPClient:
    """Talks JSON-RPC to an MCP server process over stdin/stdout."""

    def __init__(self, server_file):
        self.proc = subprocess.Popen([sys.executable, str(server_file)], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, text=True, encoding="utf-8")
        self.next_id = 0

    def request(self, method, params=None):
        self.next_id += 1
        msg = {"jsonrpc": "2.0", "id": self.next_id, "method": method,
               "params": {**(params or {}), "_meta": META}}
        print(f"    ─▶ {json.dumps(msg)[:110]}")
        self.proc.stdin.write(json.dumps(msg) + "\n")            # one message per line
        self.proc.stdin.flush()
        reply = json.loads(self.proc.stdout.readline())
        print(f"    ◀─ {json.dumps(reply)[:110]}")
        if "error" in reply:
            raise RuntimeError(reply["error"]["message"])
        return reply["result"]

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=5)


def mcp_to_ollama(tool):
    """MCP tool format -> Ollama tool format (same JSON schema, different wrapper)."""
    return {"type": "function", "function": {"name": tool["name"], "description": tool["description"],
                                             "parameters": tool["inputSchema"]}}


def main():
    server = MCPClient(Path(__file__).with_name("12_mcp_server.py"))
    try:
        print("STEP 1: discover the server")
        info = server.request("server/discover")
        print(f"  connected to {info['_meta']['io.modelcontextprotocol/serverInfo']['name']}\n")

        print("STEP 2: ask which tools it has")
        mcp_tools = server.request("tools/list")["tools"]
        print(f"  tools: {[t['name'] for t in mcp_tools]}\n")

        print("STEP 3: read a resource (data, not a function)")
        text = server.request("resources/read", {"uri": "docs://refund-policy"})["contents"][0]["text"]
        print(f"  docs://refund-policy = {text!r}\n")

        print("STEP 4: let llama3.2 use the server's tools")
        tools = [mcp_to_ollama(t) for t in mcp_tools]
        messages = [{"role": "user", "content": "What is the status of order A-1001?"}]
        for turn in range(1, 5):
            body = {"model": CHAT_MODEL, "messages": messages, "stream": False,
                    "tools": tools, "options": {"temperature": 0}}      # tools from the server
            resp = httpx.post(OLLAMA + "/api/chat", json=body, timeout=300).raise_for_status()
            msg = resp.json()["message"]
            messages.append(msg)
            if not msg.get("tool_calls"):
                print(f"  final answer: {msg['content']}")
                break
            for call in msg["tool_calls"]:
                name, args = call["function"]["name"], call["function"]["arguments"]
                print(f"  model wants {name}({args}) -> forwarding to the MCP server:")
                result = server.request("tools/call", {"name": name, "arguments": args})
                text = " ".join(c["text"] for c in result["content"] if c["type"] == "text")
                messages.append({"role": "tool", "tool_name": name, "content": text})
    finally:
        server.close()


if __name__ == "__main__":
    main()

# Try: add a tool "cancel_order" to 12_mcp_server.py. Run this file again -- the model
# sees the new tool automatically, without ANY change here. That is the point of MCP.
