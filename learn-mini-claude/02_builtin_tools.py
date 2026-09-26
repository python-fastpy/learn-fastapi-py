"""Lesson 02 -- Built-in Tools and the Permission Gate
=========================================================

WHY THIS MATTERS:
  Lesson 01's loop had one harmless tool. Real coding agents get tools
  that touch your filesystem and run shell commands -- that's what makes
  them useful and what makes them dangerous. Claude Code's whole safety
  model lives in the gap lesson 01 identified: the model can only *ask*
  for a tool, so your code gets to decide whether to run it.

  This lesson builds the four tools that cover most of what a coding
  agent does (read, write, list, run) and the two controls that keep them
  safe: a path sandbox and a permission gate.

WHAT YOU'LL LEARN:
  1. The core tool set: read_file, write_file, list_files, run_command
  2. Path sandboxing: why `../../etc/passwd` must be rejected *before*
     the tool runs, not trusted to the model's good behavior
  3. Read vs. write classification: why reads can auto-approve and writes
     should not -- the same split Claude Code makes
  4. The permission gate: one function between "model asked" and "code ran"
  5. Returning errors to the model instead of raising -- a denied or
     failed tool should teach the model, not crash the loop

Concepts:
  - Path sandbox: resolve the path, confirm it's inside the working
    directory, reject otherwise. Never string-match on ".." -- resolve it.
  - Permission gate: a policy function (tool, args) -> allow / deny / ask
  - Auto-approve list: read-only tools that don't need a prompt
  - Non-fatal errors: tool failures come back as tool RESULTS, so the
    model can try something else (same instinct as learn-mcp lesson 16)

Flow:
     model asks: write_file(path="../secrets.txt", content="...")
              |
              v
     +-----------------------+
     |  1. Path sandbox      |  resolve -> outside workdir? -> DENY
     +-----------+-----------+
                 | inside
                 v
     +-----------------------+
     |  2. Permission gate   |  read-only? -> auto-approve
     |                       |  writes/shell? -> ask the user
     +-----------+-----------+
                 | approved
                 v
     +-----------------------+
     |  3. Run the tool      |  -> result (or error) back to the model
     +-----------------------+

  Maps to:
    Claude Code's permission modes and its allow/deny rules in
    settings.json; this is a stripped-down version of the same idea.

PREREQUISITES: Lesson 01 (the loop these tools plug into)

Run:  uv run python 02_builtin_tools.py

  This lesson runs non-interactively: the demo uses a scripted policy
  (auto-approve reads, auto-DENY writes) so you can see both paths
  without typing. Lesson 04's CLI prompts you for real.

EXPECTED OUTPUT:
  === The built-in tool set ===
    read_file, write_file, list_files, run_command

  === Safe read (auto-approved) ===
    read_file(path='sample.txt') -> allowed
    result: {'content': 'hello from the sandbox\n', 'lines': 1}

  === Path escape attempt (blocked by the sandbox) ===
    read_file(path='../../../etc/passwd') -> DENIED (outside the sandbox)

  === Write (requires permission -- denied by this demo's policy) ===
    write_file(path='notes.txt') -> DENIED by permission gate
    result: {'error': 'permission denied by user'}
"""

import asyncio
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# The sandbox root: everything the agent touches must live under here.
# A real agent uses the project directory; this lesson uses a scratch dir
# so running it can't touch anything you care about.
WORKDIR = (Path(__file__).parent / "_sandbox").resolve()


# ============================================================================
# STEP 1: Path sandboxing
# ============================================================================
# The model WILL sometimes produce a path outside your project -- usually
# by accident (a hallucinated absolute path), occasionally because a
# poisoned file told it to (see learn-ai-advanced lesson 04). Either way,
# you resolve the path and check containment. Never trust the string.

class SandboxError(Exception):
    pass


def safe_path(raw: str) -> Path:
    """Resolve `raw` against WORKDIR and confirm it stays inside.

    `.resolve()` collapses `..` and symlinks BEFORE the check -- that's
    what makes this safe. Matching on the literal string ".." is not:
    `notes/../../etc` and a symlink both slip past a string check.
    """
    candidate = (WORKDIR / raw).resolve()
    if candidate != WORKDIR and WORKDIR not in candidate.parents:
        raise SandboxError(f"path escapes the sandbox: {raw}")
    return candidate


# ============================================================================
# STEP 2: The built-in tools
# ============================================================================
# These four cover most of what a coding agent does. Note every one of
# them returns a dict -- including on failure. Raising would kill the
# loop; returning an error lets the model read it and adapt.

async def read_file(path: str) -> dict:
    """Read a text file from the working directory."""
    try:
        target = safe_path(path)
        content = target.read_text(encoding="utf-8")
        return {"content": content, "lines": len(content.splitlines())}
    except SandboxError as e:
        return {"error": str(e)}
    except FileNotFoundError:
        return {"error": f"no such file: {path}"}


async def write_file(path: str, content: str) -> dict:
    """Write text to a file in the working directory."""
    try:
        target = safe_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"written": path, "bytes": len(content.encode())}
    except SandboxError as e:
        return {"error": str(e)}


async def list_files(subdir: str = ".") -> dict:
    """List files in the working directory."""
    try:
        target = safe_path(subdir)
        names = sorted(p.name for p in target.iterdir())
        return {"files": names, "count": len(names)}
    except SandboxError as e:
        return {"error": str(e)}
    except FileNotFoundError:
        return {"error": f"no such directory: {subdir}"}


async def run_command(command: str) -> dict:
    """Run a shell command in the working directory."""
    try:
        proc = subprocess.run(
            command, shell=True, cwd=WORKDIR, capture_output=True,
            text=True, timeout=15,
        )
        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout[-2000:],
            "stderr": proc.stderr[-2000:],
        }
    except subprocess.TimeoutExpired:
        return {"error": "command timed out after 15s"}


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable
    read_only: bool  # drives the auto-approve decision below


BUILTIN_TOOLS: dict[str, Tool] = {
    "read_file": Tool(
        "read_file", "Read a text file from the working directory.",
        {"type": "object",
         "properties": {"path": {"type": "string", "description": "Relative file path"}},
         "required": ["path"]},
        read_file, read_only=True,
    ),
    "list_files": Tool(
        "list_files", "List files in the working directory.",
        {"type": "object",
         "properties": {"subdir": {"type": "string", "description": "Relative subdirectory"}},
         "required": []},
        list_files, read_only=True,
    ),
    "write_file": Tool(
        "write_file", "Write text to a file in the working directory.",
        {"type": "object",
         "properties": {"path": {"type": "string", "description": "Relative file path"},
                        "content": {"type": "string", "description": "Text to write"}},
         "required": ["path", "content"]},
        write_file, read_only=False,
    ),
    "run_command": Tool(
        "run_command", "Run a shell command in the working directory.",
        {"type": "object",
         "properties": {"command": {"type": "string", "description": "Shell command"}},
         "required": ["command"]},
        run_command, read_only=False,
    ),
}


# ============================================================================
# STEP 3: The permission gate
# ============================================================================
# One function sits between "the model asked" and "the code ran". Claude
# Code's real gate is richer (allow/deny rule matching, permission modes,
# per-directory settings) but the position in the flow is identical --
# and the position is what matters.

def permission_gate(tool: Tool, args: dict, *, interactive: bool) -> bool:
    """Return True to run the tool, False to refuse."""
    if tool.read_only:
        return True  # reads are cheap to undo -- auto-approve

    if not interactive:
        return False  # non-interactive demo: refuse writes so the run is safe

    preview = ", ".join(f"{k}={v!r}"[:60] for k, v in args.items())
    answer = input(f"    Allow {tool.name}({preview})? [y/N] ").strip().lower()
    return answer == "y"


async def call_tool(name: str, args: dict, *, interactive: bool = False) -> Any:
    """The full path: look up -> gate -> run. Everything the agent loop
    from lesson 01 needs, with safety in the middle."""
    tool = BUILTIN_TOOLS.get(name)
    if tool is None:
        return {"error": f"unknown tool: {name}"}

    if not permission_gate(tool, args, interactive=interactive):
        return {"error": "permission denied by user"}

    return await tool.fn(**args)


# ============================================================================
# Demo
# ============================================================================

async def main():
    # Set up a scratch sandbox so the demo has something real to read.
    WORKDIR.mkdir(exist_ok=True)
    (WORKDIR / "sample.txt").write_text("hello from the sandbox\n", encoding="utf-8")

    print("=== The built-in tool set ===")
    for t in BUILTIN_TOOLS.values():
        kind = "read-only" if t.read_only else "WRITES"
        print(f"    {t.name:<14} [{kind:^9}] {t.description}")
    print()

    print("=== Safe read (auto-approved) ===")
    result = await call_tool("read_file", {"path": "sample.txt"})
    print("    read_file(path='sample.txt') -> allowed")
    print(f"    result: {result}")
    print()

    print("=== Path escape attempt (blocked by the sandbox) ===")
    result = await call_tool("read_file", {"path": "../../../etc/passwd"})
    print("    read_file(path='../../../etc/passwd') -> blocked before running")
    print(f"    result: {result}")
    print()

    print("=== Write (requires permission -- denied by this demo's policy) ===")
    result = await call_tool("write_file", {"path": "notes.txt", "content": "hi"})
    print("    write_file(path='notes.txt') -> DENIED by permission gate")
    print(f"    result: {result}")
    print()

    print("=== Same write, with permission granted ===")
    # Bypassing the gate here only to show the tool itself works.
    result = await BUILTIN_TOOLS["write_file"].fn(path="notes.txt", content="hi from the agent\n")
    print(f"    result: {result}")
    listing = await call_tool("list_files", {})
    print(f"    list_files() -> {listing}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Two controls, in this order, and the order matters:
    #   1. SANDBOX first -- structural, not negotiable, not a prompt. Resolve
    #      the path and check containment. A user who clicks "yes" on every
    #      prompt is still protected from a path escape.
    #   2. PERMISSION GATE second -- a judgment call the user makes. Split by
    #      reversibility: reads auto-approve, writes and shell commands ask.
    #
    # Note what is NOT a control: the tool description. Writing "only use
    # paths inside the project" in the description is a request, not a
    # guarantee -- the model can ignore it, and poisoned content can talk it
    # into ignoring it. Enforce in code, request in the description.
    #
    # Every tool returns a dict even when it fails, so a denied write or a
    # missing file comes back as a tool RESULT the model can read and work
    # around, rather than an exception that kills the session.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add an `edit_file(path, old, new)` tool that does a string replace
    #    and errors if `old` appears zero or 2+ times (that's how Claude
    #    Code's Edit tool avoids ambiguous replacements).
    # 2. Add a deny-list to permission_gate for dangerous commands
    #    (`rm -rf`, `git push --force`) that refuses even on "y".
    # 3. Add a `session_allow` set so approving a tool once stops re-asking
    #    for that tool for the rest of the run.
    # 4. Confirm the sandbox holds against a symlink: create one inside
    #    _sandbox pointing outside, then try to read through it.
