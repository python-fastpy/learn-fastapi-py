"""Lesson 03 -- Attaching MCP Servers via .mcp.json
=====================================================

WHY THIS MATTERS:
  Lesson 02 gave the agent four hardcoded tools. That's a closed set --
  adding a capability means editing the agent's source. MCP breaks that
  open: any MCP server becomes a set of tools your agent can use, added
  by editing a config file, with no change to the agent's code at all.

  This is exactly how you attach an MCP server to Claude Code. The config
  file below uses the same `.mcp.json` shape Claude Code reads, so what
  you learn here transfers directly -- and vice versa: any server you
  write for Claude Code works with the agent you're building.

WHAT YOU'LL LEARN:
  1. The `.mcp.json` format: `mcpServers` keyed by name, each either a
     `command`+`args` (stdio subprocess) or a `url` (remote HTTP)
  2. Connecting to a server and discovering its tools at runtime
  3. Adapting an MCP tool into the same `Tool` shape as a built-in, so
     the agent loop genuinely cannot tell them apart
  4. Namespacing: why tools get prefixed (`notes__save_note`) once more
     than one server is attached
  5. Failure isolation: one broken server must not take down the agent

Concepts:
  - stdio server: your agent launches it as a subprocess and speaks
    JSON-RPC over stdin/stdout. Good for local tools. This is what
    `command`/`args` means in the config.
  - HTTP server: already running somewhere; you connect by URL. Good for
    shared/remote tools. This is what `url` means.
  - Tool discovery: `client.list_tools()` -- the server tells YOU what it
    offers, at runtime. That's the part that makes the set open-ended.
  - inputSchema: the JSON Schema the MCP server publishes per tool. It
    drops straight into the model's tool spec -- no translation needed.
  - Namespacing: two servers can both offer `search`. Prefix by server.

Flow:
  .mcp.json
     |
     |  {"mcpServers": {"notes": {"command": "python",
     |                            "args": ["demo_mcp_server.py"]}}}
     v
  +----------------------+     launch subprocess      +------------------+
  |  Your agent          | -------------------------> | demo_mcp_server  |
  |                      |                            |  (stdio)         |
  |  list_tools()        | <------------------------- |  save_note       |
  |                      |    tool specs + schemas    |  list_notes      |
  +----------+-----------+                            |  clear_notes     |
             |                                        +------------------+
             v
  +-------------------------------------------+
  |  One merged registry                      |
  |    read_file        (built-in, lesson 02) |
  |    write_file       (built-in)            |
  |    notes__save_note (from MCP)            |  <- agent sees no difference
  |    notes__list_notes(from MCP)            |
  +-------------------------------------------+

  Maps to:
    Claude Code's own `.mcp.json` handling; learn-mcp lesson 12
    (ServerRegistry / multi-server routing) is the same idea inside the
    production backend.

PREREQUISITES: Lessons 01-02. learn-mcp lessons 01/07 help but aren't required.

Run:  uv run python 03_attach_mcp.py

  No credentials needed. The agent launches `demo_mcp_server.py` itself
  as a subprocess -- you don't start it manually.

EXPECTED OUTPUT:
  === Reading .mcp.json ===
    notes -> stdio: python demo_mcp_server.py

  === Connecting and discovering tools ===
    notes: connected, 3 tools discovered

  === Merged registry (built-ins + MCP) ===
    read_file           builtin
    write_file          builtin
    notes__save_note    mcp:notes
    notes__list_notes   mcp:notes
    notes__clear_notes  mcp:notes

  === Calling an MCP tool through the registry ===
    notes__save_note({'text': 'ship the mini agent', 'tag': 'todo'})
    -> {'saved': {...}, 'total_notes': 1}
"""

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport

HERE = Path(__file__).parent
CONFIG_PATH = HERE / ".mcp.json"


# ============================================================================
# STEP 1: The tool shape (same as lesson 02 -- deliberately unchanged)
# ============================================================================
# The whole point: an MCP tool must end up in EXACTLY this shape, so the
# agent loop needs no special case for "is this MCP or built-in?"

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable
    source: str  # "builtin" or "mcp:<server>" -- for display only


async def _read_file(path: str) -> dict:
    target = (HERE / "_sandbox" / path).resolve()
    try:
        return {"content": target.read_text(encoding="utf-8")}
    except FileNotFoundError:
        return {"error": f"no such file: {path}"}


async def _write_file(path: str, content: str) -> dict:
    target = (HERE / "_sandbox" / path).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return {"written": path, "bytes": len(content.encode())}


def builtin_tools() -> dict[str, Tool]:
    """Lesson 02's tools, trimmed to two to keep the output readable."""
    return {
        "read_file": Tool(
            "read_file", "Read a text file from the working directory.",
            {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
            _read_file, source="builtin",
        ),
        "write_file": Tool(
            "write_file", "Write text to a file in the working directory.",
            {"type": "object",
             "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
             "required": ["path", "content"]},
            _write_file, source="builtin",
        ),
    }


# ============================================================================
# STEP 2: Read .mcp.json
# ============================================================================
# This is Claude Code's format. Two server kinds:
#   {"command": "python", "args": ["server.py"]}   -> stdio subprocess
#   {"url": "http://localhost:8000/mcp"}           -> remote HTTP
# Real Claude Code also supports "env" for per-server environment vars;
# StdioTransport takes that too, so it's wired up below.

def load_mcp_config(path: Path = CONFIG_PATH) -> dict[str, dict]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("mcpServers", {})


def build_transport(server_config: dict):
    """Turn one .mcp.json entry into a FastMCP transport."""
    if "url" in server_config:
        return StreamableHttpTransport(url=server_config["url"])
    return StdioTransport(
        command=server_config["command"],
        args=server_config.get("args", []),
        env=server_config.get("env"),
        cwd=str(HERE),  # so relative script paths in .mcp.json resolve
        # A stdio server shares your console, so its logs/banner would
        # interleave with the agent's output. Send its stderr to a file.
        log_file=HERE / ".mcp-server.log",
    )


# ============================================================================
# STEP 3: Adapt MCP tools into the registry
# ============================================================================
# The adapter is the interesting part. An MCP tool arrives as metadata
# (name, description, inputSchema). We wrap it in a closure that opens a
# one-shot client, calls it, and parses the result -- producing a plain
# async Python callable indistinguishable from a built-in.

def _parse_mcp_result(result) -> Any:
    """MCP returns content blocks. Prefer structured output; fall back to
    text, parsing JSON when the server sent JSON as text."""
    if getattr(result, "structured_content", None):
        return result.structured_content
    for block in result.content:
        if hasattr(block, "text"):
            try:
                return json.loads(block.text)
            except json.JSONDecodeError:
                return block.text
    return None


def make_mcp_tool(server_name: str, transport, spec) -> Tool:
    async def call(**kwargs):
        # One-shot client: connect -> call -> disconnect, per invocation.
        # Simple and robust (a crashed server can't leave a dead handle
        # behind); learn-mcp lesson 08 covers pooling if you need speed.
        try:
            async with Client(transport=transport) as client:
                result = await asyncio.wait_for(
                    client.call_tool(spec.name, kwargs), timeout=30.0
                )
                return _parse_mcp_result(result)
        except Exception as e:
            # Non-fatal: the model reads this and can try something else.
            return {"error": f"MCP call failed ({server_name}.{spec.name}): {e}"}

    # MCP SDK v2 renamed inputSchema -> input_schema; support both so this
    # works against older and newer servers/SDKs alike.
    schema = getattr(spec, "input_schema", None) or getattr(spec, "inputSchema", None)

    return Tool(
        # Namespaced so two servers offering `search` don't collide.
        name=f"{server_name}__{spec.name}",
        description=spec.description or "",
        parameters=schema or {"type": "object", "properties": {}},
        fn=call,
        source=f"mcp:{server_name}",
    )


async def attach_mcp_servers(config: dict[str, dict]) -> dict[str, Tool]:
    """Connect to every configured server and return their tools.

    One server failing must not stop the others -- a typo'd command or a
    down HTTP service should cost you that server's tools, nothing more.
    """
    tools: dict[str, Tool] = {}
    for server_name, server_config in config.items():
        transport = build_transport(server_config)
        try:
            async with Client(transport=transport) as client:
                specs = await client.list_tools()
            for spec in specs:
                tool = make_mcp_tool(server_name, transport, spec)
                tools[tool.name] = tool
            print(f"    {server_name}: connected, {len(specs)} tools discovered")
        except Exception as e:
            print(f"    {server_name}: FAILED to connect ({type(e).__name__}: {e})")
            print(f"       -> skipping; the agent keeps running without it")
    return tools


# ============================================================================
# Demo
# ============================================================================

async def main():
    (HERE / "_sandbox").mkdir(exist_ok=True)

    print("=== Reading .mcp.json ===")
    config = load_mcp_config()
    if not config:
        print("    No .mcp.json found -- nothing to attach.")
        return
    for name, cfg in config.items():
        if "url" in cfg:
            print(f"    {name} -> http: {cfg['url']}")
        else:
            print(f"    {name} -> stdio: {cfg['command']} {' '.join(cfg.get('args', []))}")
    print()

    print("=== Connecting and discovering tools ===")
    mcp_tools = await attach_mcp_servers(config)
    print()

    print("=== Merged registry (built-ins + MCP) ===")
    registry = {**builtin_tools(), **mcp_tools}
    for tool in registry.values():
        print(f"    {tool.name:<20} {tool.source}")
    print()
    print("    The agent loop from lesson 01 takes this dict as-is. It has")
    print("    no idea which entries came from a subprocess over JSON-RPC.")
    print()

    if not mcp_tools:
        return

    print("=== Calling an MCP tool through the registry ===")
    args = {"text": "ship the mini agent", "tag": "todo"}
    print(f"    notes__save_note({args})")
    result = await registry["notes__save_note"].fn(**args)
    print(f"    -> {result}")
    print()

    print("=== Reading it back ===")
    result = await registry["notes__list_notes"].fn()
    print(f"    notes__list_notes() -> {result}")
    print()

    # Clean up so re-running the lesson gives the same output.
    await registry["notes__clear_notes"].fn()
    print("    (notes cleared so this lesson is repeatable)")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Attaching MCP is three steps and none of them touch the agent loop:
    #   1. READ a config file naming the servers (.mcp.json -- same format
    #      Claude Code uses, so servers are portable between the two)
    #   2. DISCOVER each server's tools at runtime via list_tools(); the
    #      server publishes its own JSON Schema, so no hand-written specs
    #   3. ADAPT each one into the same Tool shape as a built-in
    #
    # After step 3 the distinction is invisible: `registry` is one flat
    # dict, and lesson 01's loop consumes it unchanged. That's the actual
    # value of MCP -- capability becomes configuration instead of code.
    #
    # Two details worth keeping:
    #   - NAMESPACE the names. The moment you attach a second server,
    #     unprefixed `search` from two servers silently shadows one.
    #   - ISOLATE failures. attach_mcp_servers() catches per server, so a
    #     typo'd command costs you one server's tools, not the session.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a second server to .mcp.json (copy demo_mcp_server.py to
    #    demo2.py, register it as "scratch") and confirm both sets appear
    #    namespaced in the merged registry.
    # 2. Break the command in .mcp.json ("pythonn") and confirm the agent
    #    still starts, reporting the failure and continuing without it.
    # 3. Run learn-mcp's 07_http_transport.py server, then attach it here
    #    with {"url": "http://localhost:8000/mcp"} -- same registry, no
    #    code change.
    # 4. Feed this merged registry into lesson 01's agent_loop() and watch
    #    the mock model call an MCP tool through it.
