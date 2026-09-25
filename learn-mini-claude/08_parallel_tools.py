"""Lesson 08 -- Parallel Tool Calls: when to run them together
================================================================

WHY THIS MATTERS:
  A model can ask for several tools in ONE reply: "read these three
  files", "look up these four packages". agent_core.agent_loop() runs
  them one after another. For three 1-second lookups that's 3 seconds of
  the user watching a spinner for work that could take 1.

  But "just asyncio.gather() everything" is a bug. Two edits to the same
  file, run concurrently, can each read the old text and each write back
  their own version -- and one edit silently disappears. This lesson
  shows both halves: the speed-up, and the data loss.

WHAT YOU'LL LEARN:
  1. The model already batches -- `reply.tool_calls` is a list; the loop
     decides whether to run it serially or concurrently
  2. Running read-only calls with asyncio.gather, and keeping results in
     the ORDER THE MODEL ASKED, whatever order they finish in
  3. The lost-update race, reproduced: three concurrent appends, one line
     survives
  4. The rule real agents use: reads run together, writes run alone and
     in order -- and a write waits for every read queued before it
  5. Why approvals still happen one at a time (a human can only answer
     one prompt at once)

Concepts:
  - Batch: consecutive read-only calls from one reply, run concurrently
  - Barrier: a write call flushes the batch before it runs, so it sees
    the world the model expected when it asked
  - Result order: ToolMessages go back in request order; providers
    expect each tool_call_id answered, and humans reading logs do too

Flow:
  reply.tool_calls = [read A, read B, write C, read D]

      read A --+
               +-- gather --> |  write C  | --> read D
      read B --+   (batch)    | (alone)   |    (new batch)
                              ^
                        barrier: A and B finish first

  Maps to:
    Claude Code runs independent read-only tools (Read, Grep, Glob, and
    read-only subagents) concurrently, and runs edits one at a time.

PREREQUISITES: Lesson 01 (the loop), lesson 02 (read_only). No credentials.

Run:  uv run python 08_parallel_tools.py

EXPECTED OUTPUT:
  === Three slow lookups in one reply ===
    sequential (agent_core.agent_loop):  3.0s
    parallel   (this lesson's loop):     1.0s
    answer: fastapi 0.115.0, pydantic 2.9.2, uvicorn 0.30.6

  === Three appends to one file in one reply ===
    unsafe (gather everything):  1 of 3 lines survived  <- lost updates
    safe   (writes in order):    3 of 3 lines survived
"""

import asyncio
import json
import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from agent_core import WORKDIR, Tool, Usage, agent_loop, safe_path
from scripted_model import ScriptedModel, tool_results


# ============================================================================
# STEP 1: Running one call (shared by both paths)
# ============================================================================
# Same behaviour as agent_core: report, run, catch, report. It's pulled
# out so a batch can gather several of these at once.

async def _execute(tool: Tool, args: dict, on_event) -> Any:
    on_event("tool_call", {"name": tool.name, "args": args})
    try:
        result = await tool.fn(**args)
    except Exception as e:
        result = {"error": f"{type(e).__name__}: {e}"}
    on_event("tool_result", {"name": tool.name, "result": result})
    return result


# ============================================================================
# STEP 2: Running a whole reply's worth of calls
# ============================================================================
# Walk the calls in the order the model asked. Read-only calls queue up.
# A write flushes the queue (gather), gets approved, then runs alone.
# Results are stored by call id, so they go back in request order even
# though the batch finishes in whatever order the tasks do.

async def run_tool_calls(
    calls: list[dict],
    registry: dict[str, Tool],
    *,
    approve,
    on_event,
    unsafe_parallel_writes: bool = False,
) -> dict[str, Any]:
    results: dict[str, Any] = {}
    batch: list[tuple[str, Tool, dict]] = []

    async def flush():
        outs = await asyncio.gather(*(_execute(t, a, on_event) for _, t, a in batch))
        for (call_id, _, _), out in zip(batch, outs):
            results[call_id] = out
        batch.clear()

    for call in calls:
        name, args, call_id = call["name"], call["args"], call["id"]
        tool = registry.get(name)
        if tool is None:
            results[call_id] = {"error": f"unknown tool: {name}"}
            continue

        if tool.read_only:
            batch.append((call_id, tool, args))
            continue

        if not unsafe_parallel_writes:
            # Barrier: every read the model asked for BEFORE this write
            # finishes first. Then approve -- one prompt at a time.
            await flush()
        if not approve(tool, args):
            results[call_id] = {"error": "permission denied by user"}
            on_event("tool_denied", {"name": name, "args": args})
            continue

        if unsafe_parallel_writes:
            batch.append((call_id, tool, args))  # the bug, on purpose
        else:
            results[call_id] = await _execute(tool, args, on_event)

    await flush()
    return results


# ============================================================================
# STEP 3: The loop -- agent_core.agent_loop with STEP 2 swapped in
# ============================================================================
# Everything else is identical: bind tools, call the model, stop on text,
# append results, cap the turns. Only "run the calls" changed.

async def agent_loop_parallel(
    model,
    registry: dict[str, Tool],
    messages: list,
    *,
    approve,
    on_event=lambda kind, data: None,
    max_turns: int = 12,
    usage: Usage | None = None,
    unsafe_parallel_writes: bool = False,
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

        results = await run_tool_calls(
            reply.tool_calls, registry, approve=approve, on_event=on_event,
            unsafe_parallel_writes=unsafe_parallel_writes,
        )
        for call in reply.tool_calls:  # request order, not finish order
            messages.append(ToolMessage(
                content=json.dumps(results[call["id"]], default=str)[:8000],
                tool_call_id=call["id"],
            ))

    return "Stopped: hit the turn limit without finishing."


# ============================================================================
# Demo tools
# ============================================================================
# pypi_latest stands in for anything slow and read-only: an HTTP API, an
# MCP server on another machine, a big grep. append_line is a write that
# does read -> (slow) -> write, like any edit through a remote tool.

FAKE_PYPI = {"fastapi": "0.115.0", "pydantic": "2.9.2", "uvicorn": "0.30.6"}


async def pypi_latest(package: str) -> dict:
    await asyncio.sleep(1.0)  # network round-trip
    return {"package": package, "version": FAKE_PYPI.get(package, "unknown")}


async def append_line(path: str, line: str) -> dict:
    target = safe_path(path)
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    await asyncio.sleep(0.05)  # the gap where another write can sneak in
    target.write_text(text + line + "\n", encoding="utf-8")
    return {"appended": line}


def obj(props: dict) -> dict:
    return {"type": "object", "properties": props, "required": list(props)}


REGISTRY = {
    "pypi_latest": Tool(
        "pypi_latest", "Look up the latest released version of a Python package.",
        obj({"package": {"type": "string"}}), pypi_latest, read_only=True, source="builtin"),
    "append_line": Tool(
        "append_line", "Append one line to a text file.",
        obj({"path": {"type": "string"}, "line": {"type": "string"}}),
        append_line, read_only=False, source="builtin"),
}


def answer_versions(messages) -> str:
    return ", ".join(f"{r['package']} {r['version']}" for r in tool_results(messages))


LOOKUP_SCRIPT = [
    [("pypi_latest", {"package": p}) for p in FAKE_PYPI],  # three calls, ONE reply
    answer_versions,
]

CHANGELOG = "changelog.md"
APPEND_SCRIPT = [
    [("append_line", {"path": CHANGELOG, "line": f"- change {n}"}) for n in (1, 2, 3)],
    "Added three entries to changelog.md.",
]


def fresh(prompt: str) -> list:
    return [HumanMessage(content=prompt)]


def allow(tool, args) -> bool:
    return True


async def main():
    WORKDIR.mkdir(exist_ok=True)

    print("=== Three slow lookups in one reply ===")
    prompt = "What are the latest versions of fastapi, pydantic and uvicorn?"

    t0 = time.perf_counter()
    await agent_loop(ScriptedModel(LOOKUP_SCRIPT), REGISTRY, fresh(prompt), approve=allow)
    print(f"    sequential (agent_core.agent_loop):  {time.perf_counter() - t0:.1f}s")

    t0 = time.perf_counter()
    answer = await agent_loop_parallel(ScriptedModel(LOOKUP_SCRIPT), REGISTRY, fresh(prompt), approve=allow)
    print(f"    parallel   (this lesson's loop):     {time.perf_counter() - t0:.1f}s")
    print(f"    answer: {answer}")
    print()

    print("=== Three appends to one file in one reply ===")
    prompt = "Add three changelog entries."
    for label, unsafe in (("unsafe (gather everything):", True), ("safe   (writes in order):  ", False)):
        safe_path(CHANGELOG).write_text("", encoding="utf-8")
        await agent_loop_parallel(ScriptedModel(APPEND_SCRIPT), REGISTRY, fresh(prompt),
                                  approve=allow, unsafe_parallel_writes=unsafe)
        survived = len(safe_path(CHANGELOG).read_text(encoding="utf-8").splitlines())
        note = "  <- lost updates" if survived < 3 else ""
        print(f"    {label}  {survived} of 3 lines survived{note}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Parallelism is a property of the TOOL, not the loop. The loop can only
    # run calls together if it knows they can't interfere -- and the
    # `read_only` flag from lesson 02 is exactly that knowledge. The same
    # flag that says "no permission prompt needed" also says "safe to run
    # alongside other reads".
    #
    # Notice the unsafe run reported success for all three appends. Every
    # tool returned {"appended": ...}; the model would tell the user "done".
    # Races don't raise -- they just quietly lose work.
    #
    # agent_core marks every MCP tool read_only=False (lesson 03), so under
    # this rule MCP calls always run one at a time. That's the conservative
    # choice for third-party code you can't inspect.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a read between the writes -- [append, read_file, append] -- and
    #    confirm the read sees the first append (the barrier at work).
    # 2. Writes to DIFFERENT files could safely run together. Add a
    #    `conflict_key(args)` to Tool (e.g. the path) and only serialise
    #    writes that share a key.
    # 3. Cap concurrency with asyncio.Semaphore(4). Why might you want to,
    #    even for reads? (Hint: rate limits, and 50 subagents at once.)
    # 4. Swap run_tool_calls into agent_core.agent_loop and try lesson 04
    #    with "read every .py file in the sandbox". Watch the timing.
