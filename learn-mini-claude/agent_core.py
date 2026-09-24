"""Shared core for the mini-Claude agent (lessons 04 and 05 both import this).

This is lessons 01-03 assembled into one reusable module:
  - Tool           (lesson 01) the shape everything conforms to
  - built-in tools (lesson 02) read/write/list/run + sandbox
  - MCP attachment (lesson 03) .mcp.json -> discovered tools
  - agent_loop     (lesson 01) the loop, now driving a real LLM

Nothing new is introduced here. It exists so the CLI (04) and the web UI
(05) are thin wrappers over the same agent instead of two copies of it.
"""

import asyncio
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from fastmcp import Client
from fastmcp.client.transports import StdioTransport, StreamableHttpTransport

HERE = Path(__file__).parent
WORKDIR = (HERE / "_sandbox").resolve()
CONFIG_PATH = HERE / ".mcp.json"


# ============================================================================
# Tool shape (lesson 01)
# ============================================================================

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable
    read_only: bool
    source: str

    def to_openai_spec(self) -> dict:
        """The format LangChain's bind_tools() expects."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


# ============================================================================
# Built-in tools (lesson 02)
# ============================================================================

class SandboxError(Exception):
    pass


def safe_path(raw: str) -> Path:
    candidate = (WORKDIR / raw).resolve()
    if candidate != WORKDIR and WORKDIR not in candidate.parents:
        raise SandboxError(f"path escapes the sandbox: {raw}")
    return candidate


async def read_file(path: str) -> dict:
    try:
        content = safe_path(path).read_text(encoding="utf-8")
        return {"content": content, "lines": len(content.splitlines())}
    except SandboxError as e:
        return {"error": str(e)}
    except FileNotFoundError:
        return {"error": f"no such file: {path}"}
    except UnicodeDecodeError:
        return {"error": f"not a text file: {path}"}


async def write_file(path: str, content: str) -> dict:
    try:
        target = safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"written": path, "bytes": len(content.encode())}
    except SandboxError as e:
        return {"error": str(e)}


async def list_files(subdir: str = ".") -> dict:
    try:
        target = safe_path(subdir)
        return {"files": sorted(p.name for p in target.iterdir())}
    except SandboxError as e:
        return {"error": str(e)}
    except FileNotFoundError:
        return {"error": f"no such directory: {subdir}"}


async def run_command(command: str) -> dict:
    try:
        proc = subprocess.run(command, shell=True, cwd=WORKDIR,
                              capture_output=True, text=True, timeout=15)
        return {"exit_code": proc.returncode,
                "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
    except subprocess.TimeoutExpired:
        return {"error": "command timed out after 15s"}


def builtin_tools() -> dict[str, Tool]:
    defs = [
        ("read_file", "Read a text file from the working directory.",
         {"path": {"type": "string", "description": "Relative file path"}},
         ["path"], read_file, True),
        ("list_files", "List files in the working directory.",
         {"subdir": {"type": "string", "description": "Relative subdirectory"}},
         [], list_files, True),
        ("write_file", "Write text to a file in the working directory. Overwrites if it exists.",
         {"path": {"type": "string", "description": "Relative file path"},
          "content": {"type": "string", "description": "Full text to write"}},
         ["path", "content"], write_file, False),
        ("run_command", "Run a shell command in the working directory.",
         {"command": {"type": "string", "description": "Shell command to run"}},
         ["command"], run_command, False),
    ]
    return {
        name: Tool(name, desc,
                   {"type": "object", "properties": props, "required": req},
                   fn, read_only=ro, source="builtin")
        for name, desc, props, req, fn, ro in defs
    }


# ============================================================================
# MCP attachment (lesson 03)
# ============================================================================

def load_mcp_config(path: Path = CONFIG_PATH) -> dict[str, dict]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig")).get("mcpServers", {})


def build_transport(cfg: dict):
    if "url" in cfg:
        return StreamableHttpTransport(url=cfg["url"])
    return StdioTransport(
        command=cfg["command"], args=cfg.get("args", []), env=cfg.get("env"),
        cwd=str(HERE), log_file=HERE / ".mcp-server.log",
    )


def _parse_mcp_result(result) -> Any:
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
        try:
            async with Client(transport=transport) as client:
                result = await asyncio.wait_for(
                    client.call_tool(spec.name, kwargs), timeout=30.0)
                return _parse_mcp_result(result)
        except Exception as e:
            return {"error": f"MCP call failed ({server_name}.{spec.name}): {e}"}

    schema = getattr(spec, "input_schema", None) or getattr(spec, "inputSchema", None)
    return Tool(
        name=f"{server_name}__{spec.name}",
        description=spec.description or "",
        parameters=schema or {"type": "object", "properties": {}},
        fn=call,
        # MCP tools are third-party code: always gate them, never auto-approve.
        read_only=False,
        source=f"mcp:{server_name}",
    )


async def attach_mcp_servers(config: dict[str, dict], log=print) -> dict[str, Tool]:
    tools: dict[str, Tool] = {}
    for server_name, cfg in config.items():
        transport = build_transport(cfg)
        try:
            async with Client(transport=transport) as client:
                specs = await client.list_tools()
            for spec in specs:
                tool = make_mcp_tool(server_name, transport, spec)
                tools[tool.name] = tool
            log(f"  MCP '{server_name}': {len(specs)} tools attached")
        except Exception as e:
            log(f"  MCP '{server_name}': FAILED ({type(e).__name__}) -- skipped")
    return tools


async def build_registry(log=print) -> dict[str, Tool]:
    """Built-ins + everything in .mcp.json, merged into one flat dict."""
    WORKDIR.mkdir(exist_ok=True)
    registry = builtin_tools()
    registry.update(await attach_mcp_servers(load_mcp_config(), log=log))
    return registry


# ============================================================================
# Token accounting
# ============================================================================
# Every model reply carries `usage_metadata`. The thing worth internalizing
# is that an agent turn is NOT one LLM call -- each tool round-trip is
# another call, and each one resends the whole conversation so far. That's
# why input tokens grow superlinearly across a session: turn 5 re-sends
# turns 1-4. Cached input (when the provider supports it) is what keeps
# that affordable, which is why it's tracked separately here.

# USD per 1M tokens. Public list prices for gpt-4.1 at time of writing --
# an ESTIMATE for orientation, not a billing source. Update as needed.
PRICING = {
    "input": 2.00,
    "cached_input": 0.50,
    "output": 8.00,
}


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    llm_calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost_usd(self) -> float:
        fresh_input = max(0, self.input_tokens - self.cached_tokens)
        return (
            fresh_input / 1_000_000 * PRICING["input"]
            + self.cached_tokens / 1_000_000 * PRICING["cached_input"]
            + self.output_tokens / 1_000_000 * PRICING["output"]
        )

    def add_reply(self, reply) -> None:
        meta = getattr(reply, "usage_metadata", None) or {}
        if not meta:
            return
        self.llm_calls += 1
        self.input_tokens += meta.get("input_tokens", 0)
        self.output_tokens += meta.get("output_tokens", 0)
        self.cached_tokens += (meta.get("input_token_details") or {}).get("cache_read", 0)

    def merge(self, other: "Usage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cached_tokens += other.cached_tokens
        self.llm_calls += other.llm_calls

    def as_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "total_tokens": self.total_tokens,
            "llm_calls": self.llm_calls,
            "cost_usd": round(self.cost_usd, 6),
        }

    def summary(self) -> str:
        cached = f", {self.cached_tokens} cached" if self.cached_tokens else ""
        calls = f"{self.llm_calls} call" + ("s" if self.llm_calls != 1 else "")
        return (
            f"{self.total_tokens} tokens "
            f"({self.input_tokens} in{cached}, {self.output_tokens} out) "
            f"in {calls}  ~${self.cost_usd:.4f}"
        )


# ============================================================================
# The agent loop (lesson 01, now with a real model)
# ============================================================================

BASE_SYSTEM_PROMPT = """You are a small coding assistant with tools.

Rules:
- Use tools to inspect and change files; never guess a file's contents.
- All paths are relative to the working directory. Never use absolute paths.
- If a tool returns an error, read it and adapt -- don't repeat the same call.
- Be concise. When the task is done, reply with a short plain-text summary.
"""

# Persistent project instructions, same idea as Claude Code's CLAUDE.md:
# a file in the project that gets appended to the system prompt every run.
# Committed to git, shared by the team, survives restarts.
AGENT_MD = HERE / "AGENT.md"


def read_agent_md() -> str:
    """The contents of AGENT.md, or '' if there isn't one."""
    if not AGENT_MD.exists():
        return ""
    return AGENT_MD.read_text(encoding="utf-8-sig").strip()


def build_system_prompt(extra: str = "") -> str:
    """Assemble the system prompt from three layers, least to most specific.

    1. BASE_SYSTEM_PROMPT -- the rules the agent needs to function at all
    2. AGENT.md           -- persistent project instructions (from disk)
    3. `extra`            -- per-session instructions (from the UI)

    Later layers come last in the prompt, which is also where a model
    weights them most heavily -- so the more specific instruction wins
    when two of them disagree. That ordering is the whole design.
    """
    parts = [BASE_SYSTEM_PROMPT]

    project = read_agent_md()
    if project:
        parts.append("## Project instructions (AGENT.md)\n\n" + project)

    if extra and extra.strip():
        parts.append("## Instructions for this session\n\n" + extra.strip())

    return "\n\n".join(parts)


# Back-compat for anything importing the old name.
SYSTEM_PROMPT = BASE_SYSTEM_PROMPT


def get_model(model_name: str = "gpt-4-1"):
    """The real LLM. Raises if .env isn't configured."""
    from llm_helper import get_llm
    return get_llm(model=model_name, temperature=0.0)


async def agent_loop(
    model,
    registry: dict[str, Tool],
    messages: list,
    *,
    approve,
    on_event=lambda kind, data: None,
    max_turns: int = 12,
    usage: "Usage | None" = None,
) -> str:
    """Run until the model stops requesting tools.

    `approve(tool, args) -> bool` is the permission gate -- the CLI prompts
    the terminal, the web UI applies a policy. `on_event` reports progress
    so a UI can show tool calls as they happen. Pass a `Usage` to
    accumulate token counts across the run.
    """
    from langchain_core.messages import AIMessage, ToolMessage

    bound = model.bind_tools([t.to_openai_spec() for t in registry.values()])

    for _ in range(max_turns):
        reply: AIMessage = await bound.ainvoke(messages)
        messages.append(reply)

        if usage is not None:
            usage.add_reply(reply)
            on_event("usage", reply.usage_metadata or {})

        if not reply.tool_calls:
            text = reply.content if isinstance(reply.content, str) else str(reply.content)
            on_event("text", text)
            return text

        for call in reply.tool_calls:
            name, args, call_id = call["name"], call["args"], call["id"]
            tool = registry.get(name)

            if tool is None:
                result: Any = {"error": f"unknown tool: {name}"}
            elif not tool.read_only and not approve(tool, args):
                result = {"error": "permission denied by user"}
                # Surface the refusal. Without this a denied tool is
                # invisible to the UI -- the agent quietly works around
                # it and the user never learns what it tried to do.
                on_event("tool_denied", {"name": name, "args": args})
            else:
                on_event("tool_call", {"name": name, "args": args})
                try:
                    result = await tool.fn(**args)
                except Exception as e:
                    result = {"error": f"{type(e).__name__}: {e}"}
                on_event("tool_result", {"name": name, "result": result})

            messages.append(ToolMessage(
                content=json.dumps(result, default=str)[:8000],
                tool_call_id=call_id,
            ))

    return "Stopped: hit the turn limit without finishing."
