"""Test a workflow without spending a single token.

    uv run python test_workflow.py                 # test every workflow
    uv run python test_workflow.py code-review     # just one

Why this exists: driving a workflow with the real agent costs ~10 LLM
calls (~$0.02) and 30+ seconds, and if it misbehaves you can't tell
whether the *workflow* is wrong or the *model* was having an off day.

This harness plays the part of the agent mechanically -- start, then
complete_step until done -- so it tests the thing you actually wrote:
the .md file and the server's state machine. Fast, free, deterministic.

What it checks:
  1. Every step is handed out, in order, exactly once
  2. <target> substitution happens
  3. The run reaches "complete" with a full log
  4. workflow_status reports progress without advancing it
  5. The guards reject bad input (unknown workflow, unknown run_id)
  6. Steps that mention a tool name reference a tool that EXISTS
     -- catches typos like `notes_save_note` for `notes__save_note`

Exit code 0 = all passed, 1 = something failed. Usable in CI.
"""

import asyncio
import re
import sys

from agent_core import build_registry

PASS, FAIL = "PASS", "FAIL"
_results: list[tuple[str, str, str]] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    _results.append((PASS if ok else FAIL, name, detail))
    print(f"  [{PASS if ok else FAIL}] {name}" + (f"  -- {detail}" if detail else ""))
    return ok


async def test_workflow(reg: dict, wf_name: str, target: str = "sample.py") -> None:
    print(f"\n=== {wf_name} ===")

    start = reg["workflow__start_workflow"].fn
    complete = reg["workflow__complete_step"].fn
    status = reg["workflow__workflow_status"].fn

    # --- start -------------------------------------------------------
    run = await start(name=wf_name, target=target)
    if not check("starts and returns a run_id", bool(run.get("run_id")), str(run)[:90]):
        return
    run_id = run["run_id"]

    total = run.get("total_steps", 0)
    check("reports a step count", total > 0, f"{total} steps")
    check("hands out step 1 first", run.get("step_number") == 1)

    # --- <target> substitution ---------------------------------------
    first = run.get("current_step", "")
    check("no unsubstituted <target> left", "<target>" not in first, first[:70])

    # --- walk every step ---------------------------------------------
    seen = [first]
    for expected_step in range(2, total + 1):
        nxt = await complete(run_id=run_id, result=f"did step {expected_step - 1}")
        if nxt.get("status") == "complete":
            check(f"still running at step {expected_step}", False,
                  "completed early -- fewer steps than advertised")
            return
        if not check(f"advances to step {expected_step}",
                     nxt.get("step_number") == expected_step,
                     f"got {nxt.get('step_number')}"):
            return
        seen.append(nxt.get("current_step", ""))

        # status must NOT advance the run
        peek = await status(run_id=run_id)
        check(f"  status at {expected_step} doesn't advance",
              peek.get("step_number") == expected_step)

    # --- final step completes the run --------------------------------
    done = await complete(run_id=run_id, result=f"did step {total}")
    check("reaches complete", done.get("status") == "complete", str(done.get("message", ""))[:60])
    check("logs every step", len(done.get("log", [])) == total,
          f"{len(done.get('log', []))} log entries for {total} steps")

    # --- steps in order, none repeated -------------------------------
    check("every step unique", len(set(seen)) == len(seen))

    # --- tool names referenced in steps actually exist ---------------
    # Steps say things like "use write_file" or "via notes__save_note".
    # A typo there sends the agent hunting for a tool that isn't there.
    #
    # The trap worth catching: MCP tools are namespaced with a DOUBLE
    # underscore (notes__save_note). Writing one underscore is the single
    # easiest mistake to make and impossible to see by eye. So compare on
    # a form with runs of underscores collapsed -- if a step's token
    # matches a real tool that way but isn't identical, it's a typo.
    collapse = lambda s: re.sub(r"_+", "_", s)
    known = set(reg)
    known_by_shape = {collapse(k): k for k in known}

    typos, mentioned = [], set()
    for step in seen:
        for token in re.findall(r"\b[a-z][a-z0-9]*(?:_+[a-z0-9]+)+\b", step):
            if token in known:
                mentioned.add(token)
                continue
            actual = known_by_shape.get(collapse(token))
            if actual:
                typos.append(f"{token} -> {actual}")

    check("step tool names all exist",
          not typos,
          "; ".join(typos) if typos else f"checked {len(mentioned)}")


async def test_guards(reg: dict) -> None:
    print("\n=== guards ===")
    start = reg["workflow__start_workflow"].fn
    complete = reg["workflow__complete_step"].fn

    # An MCP ToolError comes back through our adapter as {"error": ...}
    bad = await start(name="does-not-exist")
    check("unknown workflow is rejected",
          isinstance(bad, dict) and "error" in bad, str(bad)[:80])

    bad2 = await complete(run_id="wf-nope", result="x")
    check("unknown run_id is rejected",
          isinstance(bad2, dict) and "error" in bad2, str(bad2)[:80])


async def main() -> int:
    reg = await build_registry(log=lambda m: None)

    missing = [t for t in ("workflow__start_workflow", "workflow__complete_step",
                           "workflow__workflow_status", "workflow__list_workflows")
               if t not in reg]
    if missing:
        print(f"Workflow server not attached (missing {missing}).")
        print("Check .mcp.json, then: uv run python check_mcp.py")
        return 1

    listing = await reg["workflow__list_workflows"].fn()
    names = [w["name"] for w in listing.get("workflows", [])]
    if not names:
        print("No workflows found. Add a .md to workflows/")
        return 1

    wanted = sys.argv[1:] or names
    for name in wanted:
        if name not in names:
            print(f"No such workflow '{name}'. Available: {names}")
            return 1
        await test_workflow(reg, name)

    await test_guards(reg)

    failed = [r for r in _results if r[0] == FAIL]
    print(f"\n{'=' * 52}")
    print(f"{len(_results) - len(failed)}/{len(_results)} checks passed")
    for _, name, detail in failed:
        print(f"  FAILED: {name}  {detail}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
