"""Lesson 04 -- The Mini Claude Code CLI
==========================================

WHY THIS MATTERS:
  Lessons 01-03 built the pieces: a loop, safe tools, MCP attachment.
  This is them wired together into something you actually use -- a
  terminal REPL that reads your files, edits them, runs commands, and
  reaches any MCP server listed in .mcp.json. About 100 lines on top of
  `agent_core.py`.

  Everything here is a thin shell around `agent_core.agent_loop()`. The
  CLI's only real jobs are: print things nicely, and answer the
  permission prompt.

WHAT YOU'LL LEARN:
  1. Wiring a real LLM into the loop (bind_tools + tool_calls)
  2. Keeping conversation state across turns so the agent remembers
  3. An interactive permission gate -- y / n / a (allow for session)
  4. Slash commands (/tools, /clear, /exit) -- how a REPL stays usable
  5. That "an AI coding assistant" is genuinely this small once the
     pieces from 01-03 are in place

REQUIRES CREDENTIALS: unlike lessons 01-03, this one calls a real model.
  Copy .env.example to .env and fill it in (or run the fetch-secrets
  skill). Without .env it exits with a message instead of failing oddly.

Run:  uv run python 04_mini_claude_cli.py

  Everything the agent touches is confined to ./_sandbox/ -- it cannot
  read or write anything else, even if you approve a prompt (lesson 02).

Try these once it starts:
    > list the files you can see
    > create hello.py that prints the first 10 fibonacci numbers
    > run it
    > save a note saying the demo works          <- goes to the MCP server
    > /tools                                      <- see builtin vs MCP
    > /exit

EXAMPLE SESSION:
  mini-claude -- 4 builtin tools, 3 MCP tools
  Working directory: _sandbox/  (everything is sandboxed here)

  > create hello.py that prints hello
    * write_file {'path': 'hello.py', 'content': "print('hello')"}
      Allow write_file? [y]es / [n]o / [a]lways  y
    -> {'written': 'hello.py', 'bytes': 15}
  Created hello.py.

  > /exit
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

import agent_core
from agent_core import (
    Tool, Usage, agent_loop, build_registry, build_system_prompt, get_model,
)

load_dotenv()

# Tools the user approved with "a" -- skipped on subsequent calls.
SESSION_ALLOW: set[str] = set()

# Token usage across the whole session.
SESSION_USAGE = Usage()


def approve(tool: Tool, args: dict) -> bool:
    """Interactive permission gate. Read-only tools never reach here."""
    if tool.name in SESSION_ALLOW:
        return True

    preview = ", ".join(f"{k}={str(v)[:50]!r}" for k, v in args.items())
    print(f"    * {tool.name}  {preview}")
    answer = input(f"      Allow {tool.name}? [y]es / [n]o / [a]lways  ").strip().lower()

    if answer == "a":
        SESSION_ALLOW.add(tool.name)
        return True
    return answer == "y"


def on_event(kind: str, data) -> None:
    if kind == "tool_call":
        # Read-only calls never hit approve(), so print them here instead.
        if data["name"] not in SESSION_ALLOW:
            print(f"    * {data['name']}  {data['args']}")
    elif kind == "tool_denied":
        print(f"    x {data['name']} denied -- the agent will work around it")
    elif kind == "tool_result":
        preview = str(data["result"])
        if len(preview) > 160:
            preview = preview[:160] + "..."
        print(f"    -> {preview}")


HELP = """
  /tools    list every tool, and where it came from
  /usage    token usage and estimated cost for this session
  /prompt   show the system prompt currently in effect
  /system   <text>  add instructions for this session (restarts the chat)
  /clear    forget the conversation and start fresh
  /help     this message
  /exit     quit

  Persistent instructions go in AGENT.md (like Claude Code's CLAUDE.md).
"""


async def main():
    if not os.getenv("ORCHESTRATOR_ENDPOINT"):
        print("No .env found.")
        print("  This lesson needs a real model. Copy .env.example to .env and")
        print("  fill in the orchestrator credentials, then run it again.")
        print("  (Lessons 01-03 run without credentials if you want the mechanics.)")
        sys.exit(1)

    print("Starting mini-claude...")
    registry = await build_registry(log=lambda m: print(m))

    builtin_count = sum(1 for t in registry.values() if t.source == "builtin")
    mcp_count = len(registry) - builtin_count

    model = get_model("gpt-4-1")

    from langchain_core.messages import HumanMessage, SystemMessage

    # Per-session instructions added with /system. Empty to start.
    session_extra = ""
    messages: list = [SystemMessage(content=build_system_prompt(session_extra))]

    print()
    print(f"mini-claude -- {builtin_count} builtin tools, {mcp_count} MCP tools")
    print(f"Working directory: {agent_core.WORKDIR.name}/  (everything is sandboxed here)")
    project_instructions = agent_core.read_agent_md()
    if project_instructions:
        print(f"Project instructions: AGENT.md loaded "
              f"({len(project_instructions)} chars)")
    print("Type /help for commands.")
    print()

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        if user_input == "/exit":
            break
        if user_input == "/help":
            print(HELP)
            continue
        if user_input == "/clear":
            # Re-reads AGENT.md, so edits to it take effect without a restart.
            messages = [SystemMessage(content=build_system_prompt(session_extra))]
            print("  (conversation cleared; AGENT.md re-read)")
            continue
        if user_input == "/prompt":
            print("  ---- system prompt in effect ----")
            for line in messages[0].content.splitlines():
                print(f"  {line}")
            print("  ---------------------------------")
            continue
        if user_input.startswith("/system"):
            session_extra = user_input[len("/system"):].strip()
            # The system prompt is the first message, so changing it means
            # starting the conversation over -- you can't retroactively
            # alter instructions the model has already been answering under.
            messages = [SystemMessage(content=build_system_prompt(session_extra))]
            if session_extra:
                print(f"  session instructions set; conversation restarted")
                print(f"  > {session_extra}")
            else:
                print("  session instructions cleared; conversation restarted")
            continue
        if user_input == "/tools":
            for t in sorted(registry.values(), key=lambda t: (t.source, t.name)):
                flag = "ro" if t.read_only else "  "
                print(f"  [{flag}] {t.name:<22} {t.source:<12} {t.description[:50]}")
            continue
        if user_input == "/usage":
            print(f"  session: {SESSION_USAGE.summary()}")
            print(f"  messages in context: {len(messages)}")
            continue

        messages.append(HumanMessage(content=user_input))
        turn_usage = Usage()
        try:
            answer = await agent_loop(
                model, registry, messages,
                approve=approve, on_event=on_event, usage=turn_usage,
            )
            print(answer)
        except Exception as e:
            print(f"  error: {type(e).__name__}: {e}")
        finally:
            # Print even on error -- a failed turn still cost tokens.
            SESSION_USAGE.merge(turn_usage)
            if turn_usage.llm_calls:
                print(f"  [{turn_usage.summary()}  |  session {SESSION_USAGE.total_tokens} tok "
                      f"~${SESSION_USAGE.cost_usd:.4f}]")
        print()

    print("bye.")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Count what's actually here: a loop (lesson 01), four tools and a
    # sandbox (lesson 02), a config-driven MCP attachment (lesson 03), and
    # ~100 lines of printing and prompting. That's a working coding agent.
    #
    # What real Claude Code adds on top is not a different architecture --
    # it's depth on each piece: smarter tools (Edit with ambiguity checks,
    # Grep/Glob), context compaction when the conversation outgrows the
    # window, subagents, hooks, richer permission rules, streaming output,
    # and a lot of prompt engineering. The loop underneath is this loop.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add an `edit_file(path, old, new)` tool -- far more token-efficient
    #    than write_file for small changes, since the model doesn't have to
    #    reproduce the whole file.
    # 2. Print token usage per turn (`reply.usage_metadata`) so you can see
    #    what a long conversation actually costs.
    # 3. Add /compact: summarize old messages into one and drop the rest,
    #    so long sessions don't blow the context window.
    # 4. Point .mcp.json at a real MCP server you use with Claude Code and
    #    confirm it works here unchanged -- same config, same protocol.
