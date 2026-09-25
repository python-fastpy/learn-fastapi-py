"""Lesson 06 -- LLM vs Agent vs Subagent: three layers, one loop
================================================================

WHY THIS MATTERS:
  "LLM", "agent" and "subagent" get used interchangeably, but they are
  three distinct layers, each built from the one below:

      LLM       text in -> text out. Stateless. Can't touch anything.
      Agent     an LLM inside a LOOP, with TOOLS your code runs for it.
      Subagent  an agent that ANOTHER agent starts via a tool call --
                fresh context, its own loop, returns only a summary.

  Lessons 01-05 built the middle layer. This lesson puts all three side
  by side so you can see exactly what each one adds -- and why Claude
  Code hands big searches to subagents instead of doing them itself.

WHAT YOU'LL LEARN:
  1. An LLM call is a pure function: no memory, no tools, no actions.
     "Memory" is just you resending the history every call.
  2. An agent = LLM + tools + loop + message history. Same as lesson 01.
  3. A subagent is just a TOOL whose implementation runs another
     agent_loop() with an EMPTY message list.
  4. Why that matters: context isolation. The subagent reads every file;
     the parent only ever sees a one-line answer.
  5. Several subagents can run in parallel from a single turn.
  6. Why subagents usually get a restricted tool set (no spawn_subagent,
     so they can't recurse forever).

Concepts:
  - LLM call: messages -> text. Nothing else.
  - Agent: the loop that turns "the model asked for a tool" into "the
    tool ran and the model saw the result".
  - Subagent: agent-as-a-tool. Parent sends a task string, gets back a
    summary string. Everything in between is invisible to the parent.
  - Context window: the messages list. Every token in it is resent on
    every call, so keeping it small keeps the agent cheap and focused.

Flow:
     LLM                    AGENT                      AGENT + SUBAGENT

  messages                 messages <---------+       parent messages
     |                        |               |          |
     v                        v               |          v
   MODEL                    MODEL             |        MODEL
     |                        |               |          |
     v                        v               |          v
   text                  tool_calls?          |   spawn_subagent(task)
   (done)                     |               |          |
                              v               |          v
                       YOUR CODE runs --------+   +-- NEW agent_loop ---+
                              |                   | fresh messages      |
                              v                   | own tools           |
                            text                  | reads 4 files       |
                                                  +--------+------------+
                                                           | summary only
                                                           v
                                                  parent sees ~50 chars,
                                                  not ~1,000 of file dumps

  Maps to:
    Claude Code's Agent/Task tool -- the parent calls it with a prompt,
    a subagent (e.g. "Explore") runs its own loop with its own tools,
    and only its final report comes back. learn-langgraph lesson 11
    (subgraphs) and 13 (orchestrator) are the graph-shaped version.

PREREQUISITES: Lesson 01 (the agent loop). Runs with no credentials.

Run:  uv run python 06_llm_vs_agent_vs_subagent.py

EXPECTED OUTPUT (abridged):
  ######## PART 1 -- A bare LLM call ########
    call 1  [1 msg ]  'My favourite colour is blue.'  ->  'Got it.'
    call 2  [1 msg ]  'What is my favourite colour?'  ->  "I don't know -- ..."
    ...
  ######## PART 3 -- Agent + subagent ########
  [parent] turn 1: TOOL CALL spawn_subagent(...)
        [subagent] turn 1: TOOL CALL list_files({})
        ...
  Context comparison:
    subagent context :  9 messages, 1041 chars   <- all the file contents
    parent context   :  4 messages,  223 chars   <- only the summary
  ...
  ######## PART 4 -- Parallel subagents ########
    2 subagents x 3 model calls x 0.2s = 1.2s if run one after another
    wall clock: 0.6s  <- they ran concurrently
"""

import asyncio
import json
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Callable


# ============================================================================
# A tiny fake repo, so the tools have something real to read
# ============================================================================

FAKE_REPO = {
    "app.py": (
        "import db\n\n"
        "def get_user(uid):\n"
        "    return db.query('SELECT * FROM users WHERE id=?', uid)\n"
    ),
    "db.py": (
        "import sqlite3\n\n"
        "def query(sql, *args):\n"
        "    conn = sqlite3.connect('app.db')\n"
        "    return conn.execute(sql, args).fetchall()\n"
    ),
    "reports.py": (
        "import db\n\n"
        "def monthly_total():\n"
        "    rows = db.query('SELECT amount FROM orders')\n"
        "    return sum(r[0] for r in rows)\n"
        "# TODO: timezone handling\n"
    ),
    "utils.py": (
        "def slugify(s):\n"
        "    return s.lower().replace(' ', '-')\n"
        "# TODO: handle unicode\n"
    ),
}


# ============================================================================
# PART 1: The LLM -- text in, text out
# ============================================================================
# This is ALL an LLM is from your code's point of view: a function that
# takes a list of messages and returns a string. It has no memory between
# calls and no way to read a file, run a command, or call an API.
#
# The mock below fakes the "intelligence" with a few if-statements, but
# its SHAPE is exactly a real chat-completion call.

async def llm_call(messages: list[dict]) -> str:
    """A bare LLM: messages in, text out. No tools, no loop, no memory."""
    last = messages[-1]["content"]
    earlier = " ".join(m["content"] for m in messages[:-1])

    if "files" in last and last.endswith("?"):
        return "I can't see your files. Paste them in and I'll take a look."
    if "favourite colour" in last and last.endswith("?"):
        if "blue" in earlier:
            return "Your favourite colour is blue."
        return "I don't know -- you haven't told me."
    return "Got it."


async def part1_bare_llm():
    print("######## PART 1 -- A bare LLM call ########\n")

    async def show(n: int, messages: list[dict]):
        reply = await llm_call(messages)
        print(f"  call {n}  [{len(messages)} msg{'s' if len(messages) > 1 else ' '}]  "
              f"{messages[-1]['content']!r}  ->  {reply!r}")
        return reply

    # Two SEPARATE calls. The second has no idea the first happened.
    first = [{"role": "user", "content": "My favourite colour is blue."}]
    r1 = await show(1, first)
    await show(2, [{"role": "user", "content": "What is my favourite colour?"}])

    # "Memory" is just you resending the history. The model didn't
    # remember -- your code did, by keeping the list and sending it again.
    await show(3, first + [
        {"role": "assistant", "content": r1},
        {"role": "user", "content": "What is my favourite colour?"},
    ])

    # And no amount of history lets it see your disk.
    await show(4, [{"role": "user", "content": "Which files in my repo call db.query?"}])
    print("\n  -> Stateless, and blind to your machine. That's the LLM layer.\n")


# ============================================================================
# PART 2: The agent -- LLM + tools + loop
# ============================================================================
# Same pieces as lesson 01: a Tool, a ModelReply that may contain tool
# calls, and a loop that runs them and feeds results back.

@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class ModelReply:
    text: str | None = None
    tool_calls: list[ToolCall] | None = None


class ScriptedModel:
    """Mock model that replays a fixed list of steps.

    Each step is a function (messages) -> ModelReply, so the "reasoning"
    can still depend on what the tools actually returned. `latency`
    simulates a real network round-trip -- used in part 4 to show
    parallel subagents finishing faster than sequential ones.
    """

    def __init__(self, steps: list[Callable[[list[dict]], ModelReply]], latency: float = 0.0):
        self.steps = steps
        self.turn = 0
        self.latency = latency

    async def complete(self, messages: list[dict], tools: dict[str, Tool]) -> ModelReply:
        if self.latency:
            await asyncio.sleep(self.latency)
        step = self.steps[min(self.turn, len(self.steps) - 1)]
        self.turn += 1
        return step(messages)


async def list_files() -> dict:
    return {"files": sorted(FAKE_REPO)}


async def read_file(path: str) -> dict:
    if path not in FAKE_REPO:
        return {"error": f"no such file: {path}"}
    return {"path": path, "content": FAKE_REPO[path]}


READ_TOOLS = {
    "list_files": Tool("list_files", "List every file in the repo.",
                       {"type": "object", "properties": {}}, list_files),
    "read_file": Tool("read_file", "Read one file from the repo.",
                      {"type": "object",
                       "properties": {"path": {"type": "string"}},
                       "required": ["path"]}, read_file),
}


def context_chars(messages: list[dict]) -> int:
    """Rough size of the context window -- what gets resent every call."""
    return sum(len(m["content"]) for m in messages)


async def run_tool(tools: dict[str, Tool], call: ToolCall) -> Any:
    tool = tools.get(call.name)
    if tool is None:
        return {"error": f"unknown tool: {call.name}"}
    return await tool.fn(**call.arguments)


async def agent_loop(label: str, model, tools: dict[str, Tool], task: str,
                     max_turns: int = 8, indent: str = "",
                     verbose: bool = True) -> tuple[str, list[dict]]:
    """The lesson 01 loop, plus two things this lesson needs:

    - returns the messages too, so we can measure the context size
    - runs multiple tool calls from one turn concurrently (asyncio.gather),
      which is what lets a parent fan out several subagents at once
    """
    def log(line: str):
        if verbose:
            print(f"{indent}[{label}] {line}")

    messages: list[dict] = [{"role": "user", "content": task}]

    for turn in range(1, max_turns + 1):
        reply = await model.complete(messages, tools)

        if not reply.tool_calls:
            messages.append({"role": "assistant", "content": reply.text or ""})
            log(f"turn {turn}: TEXT {reply.text!r}")
            return reply.text or "", messages

        # The model's request is part of the conversation too.
        messages.append({"role": "assistant",
                         "content": json.dumps([asdict(c) for c in reply.tool_calls])})
        for call in reply.tool_calls:
            log(f"turn {turn}: TOOL CALL {call.name}({call.arguments})")

        results = await asyncio.gather(*(run_tool(tools, c) for c in reply.tool_calls))

        for call, result in zip(reply.tool_calls, results):
            content = json.dumps(result)
            log(f"         result <- {content[:70]}{'...' if len(content) > 70 else ''}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": content})

    return "Stopped: hit the turn limit.", messages


def explorer_steps() -> list[Callable[[list[dict]], ModelReply]]:
    """What a model "decides" when asked to find files containing `pattern`:
    list the files, read them all, then answer from what it read."""

    def step_list(messages):
        return ModelReply(tool_calls=[ToolCall("c1", "list_files", {})])

    def step_read(messages):
        files = json.loads(messages[-1]["content"])["files"]
        return ModelReply(tool_calls=[
            ToolCall(f"r{i}", "read_file", {"path": p}) for i, p in enumerate(files)
        ])

    def step_answer(messages):
        # The answer is computed from the REAL tool results in `messages`,
        # not hardcoded -- change FAKE_REPO and the answer changes.
        pattern = re.search(r"`([^`]+)`", messages[0]["content"]).group(1)
        hits = []
        for m in messages:
            if m["role"] == "tool":
                result = json.loads(m["content"])
                if pattern in result.get("content", ""):
                    hits.append(result["path"])
        return ModelReply(text=f"`{pattern}` is in: {', '.join(hits) or 'no files'}")

    return [step_list, step_read, step_answer]


async def part2_agent():
    print("######## PART 2 -- An agent (LLM + tools + loop) ########\n")
    answer, messages = await agent_loop(
        "agent", ScriptedModel(explorer_steps()), READ_TOOLS,
        "Which files contain `db.query(`?",
    )
    print(f"\n  Answer: {answer}")
    print(f"  Context now holds {len(messages)} messages, {context_chars(messages)} chars"
          f" -- including every file it read.")
    print("  -> It can act now. But everything it touched is still in its context.\n")


# ============================================================================
# PART 3: The subagent -- an agent used as a tool
# ============================================================================
# There is no new machinery here. A subagent is:
#
#     a Tool whose fn() calls agent_loop() with a FRESH messages list
#
# The parent sends a task string. The subagent does all the reading in
# its own context, then returns ONE string. The parent never sees the
# file contents -- only the summary.

SUBAGENT_RUNS: list[dict] = []   # stats, so the demo can compare context sizes


def make_spawn_tool(verbose: bool = True, latency: float = 0.0) -> Tool:
    async def spawn_subagent(task: str) -> dict:
        answer, sub_messages = await agent_loop(
            "subagent",
            ScriptedModel(explorer_steps(), latency=latency),
            # Restricted tools: read-only, and crucially NO spawn_subagent.
            # A subagent that can spawn subagents can recurse forever.
            READ_TOOLS,
            task,
            indent="        ",
            verbose=verbose,
        )
        SUBAGENT_RUNS.append({"task": task, "messages": len(sub_messages),
                              "chars": context_chars(sub_messages)})
        # Only this crosses back into the parent's context.
        return {"summary": answer}

    return Tool(
        "spawn_subagent",
        "Hand a self-contained task to a fresh agent with read-only tools. "
        "Returns only its final answer. Use for searches that would read many files.",
        {"type": "object",
         "properties": {"task": {"type": "string"}},
         "required": ["task"]},
        spawn_subagent,
    )


def parent_steps(tasks: list[str]) -> list[Callable[[list[dict]], ModelReply]]:
    """Parent "decides" to delegate each task, then answers from the summaries."""

    def delegate(messages):
        return ModelReply(tool_calls=[
            ToolCall(f"s{i}", "spawn_subagent", {"task": t}) for i, t in enumerate(tasks)
        ])

    def answer(messages):
        summaries = [json.loads(m["content"])["summary"]
                     for m in messages if m["role"] == "tool"]
        return ModelReply(text=" | ".join(summaries))

    return [delegate, answer]


async def part3_subagent():
    print("######## PART 3 -- Agent + subagent ########\n")
    SUBAGENT_RUNS.clear()

    parent_tools = {**READ_TOOLS, "spawn_subagent": make_spawn_tool()}
    answer, parent_messages = await agent_loop(
        "parent", ScriptedModel(parent_steps(["Which files contain `db.query(`?"])),
        parent_tools, "Find where the database is queried.",
    )

    sub = SUBAGENT_RUNS[0]
    print(f"\n  Answer: {answer}")
    print("\n  Context comparison:")
    print(f"    subagent context : {sub['messages']:>2} messages, {sub['chars']:>4} chars"
          f"   <- all the file contents")
    print(f"    parent context   : {len(parent_messages):>2} messages, "
          f"{context_chars(parent_messages):>4} chars   <- only the summary")
    print("  -> Same answer as part 2. The parent's context stayed small.\n")


# ============================================================================
# PART 4: Parallel subagents
# ============================================================================
# One parent turn can request several spawn_subagent calls. Because the
# loop runs a turn's tool calls with asyncio.gather, they run at the same
# time. Each subagent here "waits" 0.2s per model call (3 calls each).

async def part4_parallel():
    print("######## PART 4 -- Parallel subagents ########\n")
    SUBAGENT_RUNS.clear()
    tasks = ["Which files contain `db.query(`?", "Which files contain `TODO`?"]

    parent_tools = {"spawn_subagent": make_spawn_tool(verbose=False, latency=0.2)}
    start = time.perf_counter()
    answer, _ = await agent_loop(
        "parent", ScriptedModel(parent_steps(tasks)), parent_tools,
        "Find DB queries and TODOs.",
    )
    elapsed = time.perf_counter() - start

    print(f"\n  Answer: {answer}")
    print(f"  {len(tasks)} subagents x 3 model calls x 0.2s = "
          f"{len(tasks) * 0.6:.1f}s if run one after another")
    print(f"  wall clock: {elapsed:.1f}s  <- they ran concurrently\n")


# ============================================================================
# Demo
# ============================================================================

async def main():
    await part1_bare_llm()
    await part2_agent()
    await part3_subagent()
    await part4_parallel()

    print("######## Summary ########\n")
    print("  | Layer    | What it is                         | Memory              |")
    print("  |----------|------------------------------------|---------------------|")
    print("  | LLM      | messages -> text                   | none (you resend)   |")
    print("  | Agent    | LLM + tools + loop                 | its messages list   |")
    print("  | Subagent | an agent another agent calls as a  | its OWN fresh list; |")
    print("  |          | tool                               | parent gets summary |")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Each layer is the previous one plus exactly one idea:
    #   LLM      -> a stateless function. It cannot act and cannot remember.
    #   Agent    -> + a loop and tools. Now it can act, and `messages` is
    #               its memory. But that memory fills with everything it
    #               touches, and all of it is resent on every call.
    #   Subagent -> + context isolation. Push a noisy sub-task into a fresh
    #               loop and keep only the answer. It's not a new kind of
    #               thing -- it's agent_loop() wrapped in a Tool.
    #
    # When to reach for a subagent:
    #   - The sub-task reads a lot but the answer is short (search, audit).
    #   - Several independent sub-tasks can run in parallel.
    #   - The sub-task needs different tools, instructions or a cheaper model.
    # When NOT to:
    #   - The parent needs the raw details anyway (you'd just re-read them).
    #   - The task is small -- a subagent costs its own LLM calls, and the
    #     parent loses the details it didn't ask for in the summary.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add "spawn_subagent" to the subagent's own tools and make its
    #    script call it. Watch the recursion, then add a `depth` argument
    #    that refuses past depth 2 -- this is why real harnesses restrict it.
    # 2. Give the subagent a different ScriptedModel latency (a "cheaper,
    #    faster model") and confirm the parent code doesn't change at all.
    # 3. Make the subagent return the full file contents instead of a
    #    summary, and re-check the context comparison -- the benefit vanishes.
    # 4. Wire a real subagent into agent_core: a Tool whose fn builds a new
    #    messages list and calls agent_loop() with a read-only registry.
