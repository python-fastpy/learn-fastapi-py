"""Lesson 10 -- Planning: a todo list the model writes itself
==============================================================

WHY THIS MATTERS:
  On a task with several steps, a model tends to do the first two,
  then summarise as if it had done all four. Nothing forgot on purpose --
  step 4 was just a long way back up the conversation.

  The workflow server (README, "Making the agent follow a procedure")
  fixes that from OUTSIDE: a server owns the steps and hands them out.
  That's right when YOU know the procedure in advance. Most tasks aren't
  like that -- the model has to work out the steps itself. For those,
  Claude Code gives the model a tool to write its own plan down: TodoWrite.

  The surprising part is how little the tool does. It stores nothing.
  It validates the list and echoes it back. All of the value comes from
  WHERE the plan ends up: in the conversation, fresh, every time the
  model updates it.

WHAT YOU'LL LEARN:
  1. A stateless planning tool: the model sends the FULL list every call
  2. Why "full list, replace" beats "add item / tick item" operations --
     there's no server-side state to drift out of sync with the model
  3. Validating the plan (one item in progress at a time) and returning
     the problem as a result, so the model corrects itself
  4. Surfacing the plan to the user via on_event -- the list is as much
     for the human watching as for the model
  5. Model-owned plan (todo_write) vs server-owned procedure (workflows):
     when to use which

Concepts:
  - Todo item: {content, status} with status pending / in_progress / completed
  - Replace semantics: each call is the whole truth; the latest call wins
  - The plan is context: it costs tokens every turn, like anything else
    in the conversation -- which is why the tool says "3+ steps only"

Flow:
  user: "create slug.py, test it, run the tests"
          |
          v
  todo_write([ [>] write slug.py, [ ] write tests, [ ] run tests ])
  write_file slug.py   + todo_write([ [x] ..., [>] ..., [ ] ... ])
  write_file tests     + todo_write([ [x] ..., [x] ..., [>] ... ])
  run_command          + todo_write([ [x] ..., [x] ..., [x] ... ])
          |
          v
  "Done: all 3 items complete."

  Maps to:
    Claude Code's TodoWrite tool -- same shape, same replace semantics,
    same "exactly one in_progress" rule.

PREREQUISITES: Lessons 01-02. Runs with no credentials (scripted model).

Run:  uv run python 10_todo_planning.py

EXPECTED OUTPUT (abridged):
    * todo_write
      -> {'error': '2 items are in_progress -- work on one at a time'}
    * todo_write
        [>] Write todo_demo/slug.py with slugify()
        [ ] Write todo_demo/test_slug.py
        [ ] Run the tests
    * write_file  todo_demo/slug.py
    * todo_write
        [x] Write todo_demo/slug.py with slugify()
        [>] Write todo_demo/test_slug.py
        [ ] Run the tests
    ...
    * run_command  python todo_demo/test_slug.py
      -> exit 0: 3 tests passed
    * todo_write
        [x] Write todo_demo/slug.py with slugify()
        [x] Write todo_demo/test_slug.py
        [x] Run the tests

  answer: Done -- slugify() written and all 3 tests pass.
  todo_write calls: 5 (the model re-sent its whole plan each time)
"""

import asyncio

from langchain_core.messages import HumanMessage, SystemMessage

from agent_core import WORKDIR, Tool, Usage, agent_loop, build_system_prompt, builtin_tools
from scripted_model import ScriptedModel, last_result


# ============================================================================
# STEP 1: The tool
# ============================================================================
# Validate, render, echo. No storage: if you stored the list server-side,
# you'd have two copies of the plan (yours and the model's memory of what
# it sent) and they WILL drift. With replace semantics there's one copy,
# and it's in the conversation where the model reads it.

TODO_MARKS = {"pending": "[ ]", "in_progress": "[>]", "completed": "[x]"}


async def todo_write(todos: list[dict]) -> dict:
    """Record the current plan. Replaces any previous list."""
    for i, item in enumerate(todos, 1):
        if not isinstance(item, dict) or not item.get("content"):
            return {"error": f"todo #{i} needs a 'content' string"}
        if item.get("status") not in TODO_MARKS:
            return {"error": f"todo #{i} status must be one of {sorted(TODO_MARKS)}"}
    # One thing at a time keeps the model -- and the user watching -- clear
    # about what's happening NOW. Two in_progress items usually means the
    # model marked the next item before finishing the current one.
    active = sum(1 for t in todos if t["status"] == "in_progress")
    if active > 1:
        return {"error": f"{active} items are in_progress -- work on one at a time"}

    checklist = "\n".join(f"{TODO_MARKS[t['status']]} {t['content']}" for t in todos)
    remaining = sum(1 for t in todos if t["status"] != "completed")
    return {"checklist": checklist, "remaining": remaining}


# The description carries the usage rules. The model never sees the code
# above -- only this text (lesson 01) -- so "when to use it" lives here.
TODO_TOOL = Tool(
    name="todo_write",
    description=(
        "Record your plan for a multi-step task (3+ steps). Send the FULL list "
        "every time -- it replaces the previous one. Keep exactly one item "
        "in_progress, and mark items completed as soon as they're done. "
        "Skip this for simple one-step requests."
    ),
    parameters={
        "type": "object",
        "properties": {"todos": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "What to do, imperative form"},
                "status": {"type": "string", "enum": list(TODO_MARKS)},
            },
            "required": ["content", "status"],
        }}},
        "required": ["todos"],
    },
    fn=todo_write,
    read_only=True,  # changes nothing on disk -- no permission prompt
    source="builtin",
)


# ============================================================================
# STEP 2: Showing the plan to the user
# ============================================================================
# The CLI in lesson 04 truncates tool results to 160 chars -- fine for a
# file write, useless for a checklist. Special-case it: the plan is the
# most useful thing the user can see while a long task runs.

TODO_CALLS = 0


def on_event(kind: str, data) -> None:
    global TODO_CALLS
    if kind == "tool_call":
        args = data["args"]
        shown = args.get("path") or args.get("command") or ""
        print(f"    * {data['name']}  {shown}".rstrip())
        if data["name"] == "todo_write":
            TODO_CALLS += 1
    elif kind == "tool_result":
        r = data["result"]
        if isinstance(r, dict) and "checklist" in r:
            for line in r["checklist"].splitlines():
                print(f"        {line}")
        elif isinstance(r, dict) and "error" in r:
            print(f"      -> {r}")
        elif isinstance(r, dict) and "exit_code" in r:
            print(f"      -> exit {r['exit_code']}: {(r['stdout'] or r['stderr']).strip()[:60]}")


# ============================================================================
# The scripted run
# ============================================================================

STEPS = ["Write todo_demo/slug.py with slugify()", "Write todo_demo/test_slug.py", "Run the tests"]


def plan(*statuses: str) -> tuple:
    return ("todo_write", {"todos": [{"content": c, "status": s} for c, s in zip(STEPS, statuses)]})


SLUG_PY = '''# Turns a title into a URL-safe slug
import re


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
'''

TEST_PY = '''# Tests for slug.py
from slug import slugify

assert slugify("Hello World") == "hello-world"
assert slugify("  Already--slugged  ") == "already-slugged"
assert slugify("C'est la vie!") == "c-est-la-vie"
print("3 tests passed")
'''


def after_tests(messages):
    # Tools in one reply run in order, so the run_command result is last.
    result = last_result(messages)
    if result.get("exit_code") == 0:
        return [plan("completed", "completed", "completed")]
    return "The tests failed -- see the output above."


SCRIPT = [
    # A realistic first mistake: marking everything as started.
    [plan("in_progress", "in_progress", "pending")],
    [plan("in_progress", "pending", "pending")],
    [("write_file", {"path": "todo_demo/slug.py", "content": SLUG_PY}),
     plan("completed", "in_progress", "pending")],
    [("write_file", {"path": "todo_demo/test_slug.py", "content": TEST_PY}),
     plan("completed", "completed", "in_progress")],
    [("run_command", {"command": "python todo_demo/test_slug.py"})],
    after_tests,
    "Done -- slugify() written and all 3 tests pass.",
]


def allow(tool, args) -> bool:
    return True  # scripted demo in the sandbox -- lesson 04 asks for real


async def main():
    WORKDIR.mkdir(exist_ok=True)
    registry = {**builtin_tools(), "todo_write": TODO_TOOL}

    task = "In todo_demo/, create slug.py with a slugify() function, write tests for it, and run them."
    print(f"> {task}\n")
    messages = [SystemMessage(content=build_system_prompt()), HumanMessage(content=task)]
    usage = Usage()
    answer = await agent_loop(ScriptedModel(SCRIPT), registry, messages,
                              approve=allow, on_event=on_event, usage=usage)

    print(f"\n  answer: {answer}")
    print(f"  todo_write calls: {TODO_CALLS} (the model re-sent its whole plan each time)")
    print(f"  {usage.llm_calls} LLM calls, ~{usage.total_tokens:,} tokens (estimated)")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # A planning tool works by putting the plan where the model will re-read
    # it -- the end of the conversation -- every time it changes. The tool
    # itself is ~15 lines of validation. That's the whole trick.
    #
    # When to use which:
    #
    #   todo_write (this lesson)         workflow server (README)
    #   ------------------------         ------------------------
    #   model writes the steps           you write the steps
    #   model can revise the plan        steps are fixed in a .md file
    #   state lives in the conversation  state lives in the server
    #   nothing stops it skipping one    can't reach the end without them
    #   cheap: no extra round-trips      every complete_step is a call
    #
    # Use todo_write for open-ended work. Use a workflow when the steps are
    # a requirement ("always run the tests before saying done"), not a plan.
    #
    # Note the cost: every todo_write puts the whole list into the
    # conversation again, and every later turn resends it. That's why the
    # description says "3+ steps" -- on a one-liner it's pure overhead.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add todo_write to agent_core.builtin_tools(), and special-case its
    #    result in the lesson 04 CLI's on_event. Ask for a 4-step task and
    #    see whether the real model uses it unprompted.
    # 2. Delete the "exactly one in_progress" check and the sentence about
    #    it in the description. Does the model's plan get less useful?
    # 3. Build a "stop check": when agent_loop is about to return text,
    #    find the latest todo_write result in `messages`. If `remaining` > 0,
    #    append a HumanMessage saying so and keep looping (lesson 09's
    #    hooks exercise 3 is the same idea).
    # 4. Show the checklist in the lesson 05 web UI as a panel that updates
    #    live, instead of a tool chip.
