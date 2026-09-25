"""Lesson 09 -- Hooks: code that runs on every tool call
==========================================================

WHY THIS MATTERS:
  You now have three ways to shape what the agent does, and none of them
  is quite right for rules like "syntax-check every Python file it
  writes" or "never let a shell command reach outside the project":

    - AGENT.md is a REQUEST. The model can forget it or be talked out of it.
    - approve() is a HUMAN decision. It asks, and "always allow" stops
      asking -- and read-only tools never reach it at all.
    - Editing each tool means every tool, and every MCP server you don't
      own, needs the same logic copied into it.

  A hook is a function the LOOP calls before or after every tool, no
  matter which tool, no matter what the user approved. It's deterministic
  code, so it's the place for rules that must always hold.

WHAT YOU'LL LEARN:
  1. Two hook points: pre_tool (can BLOCK a call) and post_tool (can
     ADD to the result the model sees)
  2. Where they sit: pre_tool runs before approve(), so a blocked call
     never bothers the user; post_tool runs after the tool, before the
     result goes back
  3. Feedback hooks: a post_tool hook that syntax-checks written Python
     and hands the error back -- the model fixes it without being asked
  4. The limit of pattern-matching hooks, demonstrated: the shell hook
     below blocks `../` and is bypassed in one line
  5. Audit hooks: see every call, including the read-only ones approve()
     never sees

Concepts:
  - pre_tool(tool, args) -> None to allow, or a string reason to block
  - post_tool(tool, args, result) -> None to leave the result alone, or a
    new result (usually the old one plus a "hook_feedback" key)
  - A blocked call is a normal tool RESULT, same as a denied permission

Flow:
  model asks for a tool
        |
        v
  pre_tool hooks ---- any returns a reason? ---> {"error": "blocked by hook: ..."}
        |  all None
        v
  approve()  (skipped for read-only, as before)
        |
        v
  tool runs
        |
        v
  post_tool hooks --- may add "hook_feedback" to the result
        |
        v
  ToolMessage back to the model

  Maps to:
    Claude Code's PreToolUse and PostToolUse hooks in settings.json. A
    PreToolUse hook that exits with code 2 blocks the call and its stderr
    goes to the model -- the same contract as returning a reason here.

PREREQUISITES: Lessons 01-02. Runs with no credentials (scripted model).

Run:  uv run python 09_hooks.py

EXPECTED OUTPUT (abridged; the "<-" notes are annotations):
  === 1. The shell reaches outside the sandbox (no hooks) ===
    * run_command  python -c "print(open('../pyproject.toml').read()...
      -> exit 0: name = "learn-mini-claude"        <- read a file outside _sandbox/

  === 2. Same command, with a pre_tool hook ===
    x run_command blocked: command refers to a parent or absolute path ('..')

  === 3. ...and the one-line bypass ===
    * run_command  python -c "import pathlib; print(pathlib.Path.cwd().parent.name)"
      -> exit 0: learn-mini-claude                  <- still outside. Hooks aren't a sandbox.

  === 4. A post_tool hook that feeds back syntax errors ===
    * write_file  {'path': 'hooks_demo/add.py', ...}
      -> hook_feedback: SyntaxError on line 1: expected ':' -- fix the file before continuing
    * write_file  {'path': 'hooks_demo/add.py', ...}
    answer: Wrote hooks_demo/add.py (fixed a missing colon the syntax check caught).

  === Audit log (every call, including read-only ones) ===
    run_command, run_command, run_command, write_file, write_file, read_file
"""

import asyncio
import inspect
import json
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent_core import WORKDIR, Tool, Usage, builtin_tools, safe_path
from scripted_model import ScriptedModel, last_result


# ============================================================================
# STEP 1: What a hook is
# ============================================================================
# Two lists of plain functions. Sync or async both work -- a hook that
# shells out to a linter is naturally async, a regex check isn't.

@dataclass
class Hooks:
    pre_tool: list[Callable] = field(default_factory=list)   # (tool, args) -> str | None
    post_tool: list[Callable] = field(default_factory=list)  # (tool, args, result) -> result | None


async def _call(fn, *args):
    out = fn(*args)
    return await out if inspect.isawaitable(out) else out


async def run_pre_hooks(hooks: Hooks, tool: Tool, args: dict) -> str | None:
    """The first hook that returns a reason wins; the call is blocked."""
    for hook in hooks.pre_tool:
        reason = await _call(hook, tool, args)
        if reason:
            return reason
    return None


async def run_post_hooks(hooks: Hooks, tool: Tool, args: dict, result: Any) -> Any:
    """Each hook sees the previous hook's output, so they chain."""
    for hook in hooks.post_tool:
        changed = await _call(hook, tool, args, result)
        if changed is not None:
            result = changed
    return result


# ============================================================================
# STEP 2: The loop, with the two hook points added
# ============================================================================
# agent_core.agent_loop plus four lines. Look for PRE and POST.

async def agent_loop_with_hooks(
    model,
    registry: dict[str, Tool],
    messages: list,
    *,
    approve,
    hooks: Hooks,
    on_event=lambda kind, data: None,
    max_turns: int = 12,
    usage: Usage | None = None,
) -> str:
    bound = model.bind_tools([t.to_openai_spec() for t in registry.values()])

    for _ in range(max_turns):
        reply: AIMessage = await bound.ainvoke(messages)
        messages.append(reply)
        if usage is not None:
            usage.add_reply(reply)

        if not reply.tool_calls:
            text = reply.content if isinstance(reply.content, str) else str(reply.content)
            on_event("text", text)
            return text

        for call in reply.tool_calls:
            name, args, call_id = call["name"], call["args"], call["id"]
            tool = registry.get(name)

            if tool is None:
                result: Any = {"error": f"unknown tool: {name}"}
            elif reason := await run_pre_hooks(hooks, tool, args):          # PRE
                result = {"error": f"blocked by hook: {reason}"}
                on_event("hook_blocked", {"name": name, "args": args, "reason": reason})
            elif not tool.read_only and not approve(tool, args):
                result = {"error": "permission denied by user"}
                on_event("tool_denied", {"name": name, "args": args})
            else:
                on_event("tool_call", {"name": name, "args": args})
                try:
                    result = await tool.fn(**args)
                except Exception as e:
                    result = {"error": f"{type(e).__name__}: {e}"}
                result = await run_post_hooks(hooks, tool, args, result)    # POST
                on_event("tool_result", {"name": name, "result": result})

            messages.append(ToolMessage(
                content=json.dumps(result, default=str)[:8000],
                tool_call_id=call_id,
            ))

    return "Stopped: hit the turn limit without finishing."


# ============================================================================
# STEP 3: Three hooks worth having
# ============================================================================

# -- A blocking hook ---------------------------------------------------------
# run_command runs with cwd=_sandbox/, but a shell doesn't care about cwd:
# `type ..\..\.env` or `cat ../../.env` works fine. safe_path() only
# protects the FILE tools. This hook refuses commands that name a parent
# or absolute path. Demo 3 shows why that is a speed bump, not a wall.

_ESCAPE_PATTERNS = [
    (r"\.\.", "'..'"),
    (r"(?<![\w])[A-Za-z]:[\\/]", "a drive path"),
    (r"(?<![\w])~[\\/]", "a home-directory path"),
]


def block_shell_escapes(tool: Tool, args: dict) -> str | None:
    if tool.name != "run_command":
        return None
    for pattern, label in _ESCAPE_PATTERNS:
        if re.search(pattern, args.get("command", "")):
            return f"command refers to a parent or absolute path ({label})"
    return None


# -- A feedback hook ---------------------------------------------------------
# After any write to a .py file, compile it. On failure, add the error to
# the result. The write still happened -- the hook doesn't undo it -- but
# the model now KNOWS the file is broken, on this turn, without having to
# think of running it.

def check_python_syntax(tool: Tool, args: dict, result: Any) -> Any:
    path = args.get("path", "")
    if tool.name not in ("write_file", "edit_file") or not path.endswith(".py"):
        return None
    if isinstance(result, dict) and "error" in result:
        return None
    try:
        compile(safe_path(path).read_text(encoding="utf-8"), path, "exec")
    except SyntaxError as e:
        return {**result, "hook_feedback":
                f"SyntaxError on line {e.lineno}: {e.msg} -- fix the file before continuing"}
    return None  # only speak up when something is wrong -- silence is cheaper


# -- An audit hook -----------------------------------------------------------
# Never blocks, never changes anything -- just watches. Because it's a
# pre_tool hook it sees read-only calls too, which approve() never does.

AUDIT: list[str] = []


def audit(tool: Tool, args: dict) -> None:
    AUDIT.append(tool.name)
    return None


HOOKS = Hooks(pre_tool=[audit, block_shell_escapes], post_tool=[check_python_syntax])
NO_HOOKS = Hooks(pre_tool=[audit])  # audit only, so demo 1 is still logged


# ============================================================================
# Demo
# ============================================================================

def on_event(kind: str, data) -> None:
    if kind == "tool_call":
        args = data["args"]
        shown = args["command"] if "command" in args else {k: str(v)[:30] for k, v in args.items()}
        print(f"    * {data['name']}  {str(shown)[:70]}")
    elif kind == "hook_blocked":
        print(f"    x {data['name']} blocked: {data['reason']}")
    elif kind == "tool_result":
        r = data["result"]
        if isinstance(r, dict) and "exit_code" in r:
            print(f"      -> exit {r['exit_code']}: {(r['stdout'] or r['stderr']).strip()[:60]}")
        elif isinstance(r, dict) and "hook_feedback" in r:
            print(f"      -> hook_feedback: {r['hook_feedback']}")


def allow(tool, args) -> bool:
    return True  # everything approved -- so anything stopped below was a HOOK


READ_OUTSIDE = "python -c \"print(open('../pyproject.toml').read().splitlines()[1])\""
BYPASS = "python -c \"import pathlib; print(pathlib.Path.cwd().parent.name)\""

BROKEN = "def add(a, b)\n    return a + b\n"
FIXED = "def add(a, b):\n    return a + b\n"


def fix_if_told(messages):
    result = last_result(messages)
    if isinstance(result, dict) and "hook_feedback" in result:
        return [("write_file", {"path": "hooks_demo/add.py", "content": FIXED})]
    return "Wrote hooks_demo/add.py."


SYNTAX_SCRIPT = [
    [("write_file", {"path": "hooks_demo/add.py", "content": BROKEN})],
    fix_if_told,
    [("read_file", {"path": "hooks_demo/add.py"})],
    "Wrote hooks_demo/add.py (fixed a missing colon the syntax check caught).",
]


async def demo(title: str, script: list, hooks: Hooks) -> None:
    print(f"=== {title} ===")
    answer = await agent_loop_with_hooks(
        ScriptedModel(script), builtin_tools(), [HumanMessage(content=title)],
        approve=allow, hooks=hooks, on_event=on_event,
    )
    if not answer.startswith("("):
        print(f"    answer: {answer}")
    print()


async def main():
    WORKDIR.mkdir(exist_ok=True)

    one_command = lambda cmd: [[("run_command", {"command": cmd})], "(done)"]
    await demo("1. The shell reaches outside the sandbox (no hooks)", one_command(READ_OUTSIDE), NO_HOOKS)
    await demo("2. Same command, with a pre_tool hook", one_command(READ_OUTSIDE), HOOKS)
    await demo("3. ...and the one-line bypass", one_command(BYPASS), HOOKS)
    await demo("4. A post_tool hook that feeds back syntax errors", SYNTAX_SCRIPT, HOOKS)

    print("=== Audit log (every call, including read-only ones) ===")
    print("    " + ", ".join(AUDIT))


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Four layers now, each with a different job:
    #
    #   AGENT.md / system prompt  asks          the model may not comply
    #   hooks                     enforces      runs every time, on every tool
    #   approve()                 decides       a human, case by case
    #   safe_path()               constrains    structural; can't be talked past
    #
    # Demo 3 is the important one. The pre_tool hook is real enforcement of
    # the rule it checks -- but the rule is a string pattern, and a shell
    # has endless ways to say "the parent directory". Hooks are the right
    # place for POLICY (lint, audit, "no force-push"). They are the wrong
    # place for ISOLATION. For that the command has to run somewhere that
    # physically can't see outside: a container, a VM, a locked-down user.
    #
    # Demo 4 is the pattern that pays off most in practice: a post_tool
    # hook that turns a silent failure into feedback on the same turn.
    # The model didn't have to decide to check its work -- the loop did it.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a pre_tool hook that blocks `git push --force` and `rm -rf`.
    #    Compare with lesson 02's exercise 2, which did it inside approve():
    #    which one still holds after the user answers "a" (always)?
    # 2. Make check_python_syntax async and run `ruff check` on the file
    #    instead of compile(). Feed the lint output back as hook_feedback.
    # 3. Add a stop hook: when the model replies with text, check the
    #    lesson 10 todo list and, if items remain, append a HumanMessage
    #    ("you still have N open items") and keep looping.
    # 4. Wire HOOKS into agent_core.agent_loop so the lesson 04 CLI and
    #    lesson 05 web UI both get them. Where should a hook's block show
    #    up in the web UI's tool chips?
