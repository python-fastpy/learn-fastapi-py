"""Lesson 11 -- Subagents: a fresh context for the messy part
===============================================================

WHY THIS MATTERS:
  Lesson 01's takeaway: `messages` is the agent's entire memory, and
  every turn resends all of it. So when the agent reads five files to
  answer one question, those five files ride along on EVERY later turn
  of the session -- long after anyone cares about them.

  A subagent is the fix, and it's almost nothing new: a tool whose
  implementation calls agent_loop() again, with a brand-new `messages`
  list. The child does the reading in ITS context, returns a short
  report, and its context is thrown away. The parent only ever sees the
  report.

WHAT YOU'LL LEARN:
  1. A subagent is a Tool that runs agent_loop() -- same loop, fresh
     messages, a narrower set of tools
  2. Context isolation, measured: what the parent's conversation holds
     with and without subagents, and what a follow-up question then costs
  3. Why the child gets READ-ONLY tools: it can't ask the user anything,
     and nobody reviews what it did -- only what it said
  4. No recursion: the child's registry doesn't include the `task` tool
  5. Subagents aren't free -- they spend tokens too. What you buy is a
     parent context that stays small

Concepts:
  - Parent / child: the agent the user talks to, and the one it spawns
  - Task prompt: the child starts with NOTHING but this -- no chat
    history, no AGENT.md unless you pass it -- so it must be complete
  - Report: the child's final text, the only thing that crosses back
  - Tool subset: `{n: t for n, t in registry.items() if t.read_only}`

Flow:
   parent messages                         child messages (thrown away)
   ---------------                         ----------------------------
   user: "summarise each module"
   task("orders.py + payments.py") ------> system: SUBAGENT_PROMPT
                                           user:   <task prompt>
                                           read_file orders.py   (big)
                                           read_file payments.py (big)
   tool result: "orders.py: ...  <-------- report: 2 lines
                 payments.py: ..."
   (the file contents never enter the parent)

  Maps to:
    Claude Code's Task / Agent tool and its subagent types (Explore,
    Plan, ...): a separate context window with its own tools, returning
    one final message to the caller.

PREREQUISITES: Lesson 01 (messages = memory). Lesson 06 introduces
  subagents next to a bare LLM and a plain agent; this lesson builds on
  it by running the real agent_core loop and measuring what isolation
  saves, including on the follow-up turns. Lesson 08 helps too: `task`
  is read-only, so a parallel loop could run several at once.
  Runs with no credentials (scripted model).

Run:  uv run python 11_subagents.py

EXPECTED OUTPUT (abridged):
  === Run A: the parent reads everything itself ===
    * list_files  subagent_demo
    * read_file  subagent_demo/emails.py
    ... (all four files)

  === Run B: the parent delegates to two subagents ===
    * list_files  subagent_demo
    * task  Summarise emails.py, orders.py
        [sub] * read_file  subagent_demo/emails.py
        [sub] * read_file  subagent_demo/orders.py
    * task  Summarise payments.py, users.py
        [sub] * read_file  subagent_demo/payments.py
        [sub] * read_file  subagent_demo/users.py

                                           Run A     Run B
    parent context after Q1 (chars)       16,304     1,826
    follow-up question (tokens)            4,389       912
    parent tokens, whole session          10,029     3,404
    subagent tokens                            0     4,757
    total tokens (estimated)              10,029     8,161
"""

import asyncio
import re
import textwrap

from langchain_core.messages import HumanMessage, SystemMessage

from agent_core import WORKDIR, Tool, Usage, agent_loop, build_system_prompt, builtin_tools
from scripted_model import ScriptedModel, last_result, tool_results, user_prompt

DEMO_DIR = WORKDIR / "subagent_demo"


# ============================================================================
# STEP 1: The subagent tool
# ============================================================================

SUBAGENT_PROMPT = """You are a research subagent working for another agent.

- You have read-only tools. You cannot change files or run commands.
- Investigate the task you were given, then reply with a concise report.
- Your final message is the ONLY thing the caller will see. Include the
  file names and facts it needs; leave out everything else.
"""


def make_subagent_tool(
    model,
    parent_registry: dict[str, Tool],
    *,
    usage: Usage | None = None,
    on_event=lambda kind, data: None,
    max_turns: int = 8,
) -> Tool:
    # Read-only tools only. The child can't prompt the user (who would it
    # ask, mid-tool-call?), and the parent only sees its REPORT, not what
    # it did -- so it must not be able to do anything worth reviewing.
    #
    # Built before `task` is added to the parent's registry, so the child
    # can't spawn children of its own. Unbounded recursion is a real
    # failure mode: a confused model delegating the same task forever.
    child_tools = {n: t for n, t in parent_registry.items() if t.read_only}

    async def task(description: str, prompt: str) -> dict:
        # A brand-new conversation. This line IS the context isolation.
        messages = [SystemMessage(content=SUBAGENT_PROMPT), HumanMessage(content=prompt)]
        report = await agent_loop(
            model, child_tools, messages,
            approve=lambda tool, args: False,  # never reached: all read-only
            on_event=on_event, usage=usage, max_turns=max_turns,
        )
        # `messages` goes out of scope here -- everything the child read
        # is gone. Only `report` crosses back to the parent.
        return {"report": report}

    return Tool(
        name="task",
        description=(
            "Delegate a self-contained research task to a subagent with read-only "
            "tools. Use it when answering would mean reading many files and you "
            "only need the conclusion. The subagent sees NOTHING of this "
            "conversation -- `prompt` must contain everything it needs to know."
        ),
        parameters={
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "3-5 word label"},
                "prompt": {"type": "string", "description": "The full, self-contained task"},
            },
            "required": ["description", "prompt"],
        },
        fn=task,
        # Side-effect free, so no permission prompt -- and lesson 08's loop
        # would run several subagents at once. It still COSTS tokens.
        read_only=True,
        source="builtin",
    )


# ============================================================================
# Demo setup: four modules, each mostly bulk
# ============================================================================

MODULES = {
    "orders.py": "Create, update and cancel customer orders.",
    "payments.py": "Charge cards and issue refunds through the payment gateway.",
    "users.py": "Sign-up, login and profile management.",
    "emails.py": "Render and send transactional emails.",
}


def make_demo_project() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    for name, purpose in MODULES.items():
        stem = name[:-3]
        body = "\n".join(textwrap.dedent(f'''
            def {stem}_handler_{i}(request: dict) -> dict:
                """Handle {stem} request type {i}."""
                payload = request.get("payload") or {{}}
                if not payload.get("id"):
                    return {{"ok": False, "error": "missing id"}}
                return {{"ok": True, "id": payload["id"], "kind": {i}}}
            ''') for i in range(12))
        (DEMO_DIR / name).write_text(f'"""{purpose}"""\n{body}', encoding="utf-8")


def docstring(source: str) -> str:
    match = re.search(r'"""(.+?)"""', source)
    return match.group(1) if match else "(no docstring)"


# ============================================================================
# The scripts: what a model plausibly does in each setup
# ============================================================================

def read_all(messages):
    return [("read_file", {"path": f"subagent_demo/{f}"}) for f in last_result(messages)["files"]]


def summarise_reads(messages) -> str:
    return "\n".join(f"- {docstring(r['content'])}" for r in tool_results(messages))


def delegate(messages):
    files = last_result(messages)["files"]
    halves = [files[:2], files[2:]]
    return [("task", {
        "description": f"Summarise {', '.join(h)}",
        "prompt": ("In the subagent_demo/ directory, read these files and give a "
                   f"one-line summary of what each does: {', '.join(h)}"),
    }) for h in halves]


def combine_reports(messages) -> str:
    return "\n".join(r["report"] for r in tool_results(messages))


FOLLOW_UP = "Which module should I look at first for a refund bug?"
FOLLOW_UP_ANSWER = "Start with payments.py -- it issues refunds through the gateway."

PARENT_DIRECT = ScriptedModel(
    [[("list_files", {"subdir": "subagent_demo"})], read_all, summarise_reads],
    [FOLLOW_UP_ANSWER],
)
PARENT_DELEGATING = ScriptedModel(
    [[("list_files", {"subdir": "subagent_demo"})], delegate, combine_reports],
    [FOLLOW_UP_ANSWER],
)


# The child reads the files its prompt names, then reports. One model
# instance serves both subagents: ScriptedModel works out its place in
# the script from each conversation, so they don't interfere.
def child_read(messages):
    names = re.findall(r"\w+\.py", user_prompt(messages))
    return [("read_file", {"path": f"subagent_demo/{n}"}) for n in names]


def child_report(messages) -> str:
    names = re.findall(r"\w+\.py", user_prompt(messages))
    return "\n".join(f"- {n}: {docstring(r['content'])}" for n, r in zip(names, tool_results(messages)))


CHILD = ScriptedModel([child_read, child_report])


# ============================================================================
# Demo
# ============================================================================

def printer(indent: str, tag: str = ""):
    def on_event(kind, data):
        if kind == "tool_call":
            args = data["args"]
            shown = args.get("description") or args.get("path") or args.get("subdir") or ""
            print(f"{indent}{tag}* {data['name']}  {shown}")
    return on_event


def context_chars(messages) -> int:
    return sum(len(str(m.content)) for m in messages)


async def run(label: str, parent_model, registry) -> dict:
    print(f"=== {label} ===")
    messages = [SystemMessage(content=build_system_prompt()),
                HumanMessage(content="Summarise what each module in subagent_demo/ does.")]
    parent = Usage()
    answer = await agent_loop(parent_model, registry, messages,
                              approve=lambda t, a: True, on_event=printer("    "), usage=parent)
    for line in answer.splitlines():
        print(f"      {line}")
    after_first = context_chars(messages)

    # The follow-up is where the difference shows: this call resends
    # whatever the first question left behind in `messages`.
    messages.append(HumanMessage(content=FOLLOW_UP))
    follow = Usage()
    await agent_loop(parent_model, registry, messages, approve=lambda t, a: True, usage=follow)
    parent.merge(follow)
    print()
    return {"context": after_first, "follow_up": follow.total_tokens, "parent": parent.total_tokens}


async def main():
    make_demo_project()

    a = await run("Run A: the parent reads everything itself", PARENT_DIRECT, builtin_tools())
    a["child"] = 0

    registry = builtin_tools()
    child_usage = Usage()
    registry["task"] = make_subagent_tool(CHILD, registry, usage=child_usage,
                                          on_event=printer("        ", "[sub] "))
    b = await run("Run B: the parent delegates to two subagents", PARENT_DELEGATING, registry)
    b["child"] = child_usage.total_tokens

    rows = [
        ("parent context after Q1 (chars)", "context"),
        ("follow-up question (tokens)", "follow_up"),
        ("parent tokens, whole session", "parent"),
        ("subagent tokens", "child"),
    ]
    print(f"    {'':34}{'Run A':>10}{'Run B':>10}")
    for label, key in rows:
        print(f"    {label:34}{a[key]:>10,}{b[key]:>10,}")
    total_a, total_b = a["parent"] + a["child"], b["parent"] + b["child"]
    print(f"    {'total tokens (estimated)':34}{total_a:>10,}{total_b:>10,}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Look at the follow-up row. After Run A, every later question in the
    # session pays for four files nobody needs any more. After Run B, it
    # pays for a four-line summary. That gap is per turn, for the rest of
    # the session -- the longer the session, the more it matters.
    #
    # Now the total row. Run B came out lower here, but only because Run A
    # paid for the four files twice more (on its summary turn and on the
    # follow-up). That isn't guaranteed: the children read the same files
    # plus their own prompts, so with a single question and no follow-up
    # -- or a child that reads more than it needs -- subagents cost MORE in
    # total. What they reliably buy is a small, focused parent context:
    # cheaper follow-ups, and a model that isn't wading through stale file
    # contents to find what matters. That's the real trade.
    #
    # The design rules all come from one fact -- the child starts from
    # nothing and only its final text comes back:
    #   - the task prompt must be self-contained (it can't see the chat)
    #   - the report must contain everything the parent needs
    #   - the child's tools must be safe to use unsupervised (read-only)
    #   - the child must not be able to spawn more children
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Run the two tasks concurrently: use lesson 08's
    #    agent_loop_parallel for the parent. `task` is read_only=True, so
    #    they batch. How much faster is it with a real model?
    # 2. Pass AGENT.md into the child: build its system prompt with
    #    build_system_prompt() + SUBAGENT_PROMPT. When would you NOT want to?
    # 3. Give the child lesson 07's grep. Rewrite child_read to grep first
    #    and read only the matching files. What happens to subagent tokens?
    # 4. Add task to the lesson 04 CLI (it needs the model, so add it after
    #    get_model()). Ask "summarise every file in the sandbox" and compare
    #    /usage with and without it.
