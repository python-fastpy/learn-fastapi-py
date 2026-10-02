"""Lesson 04 -- Delegation vs. control handoff: two different call shapes
=============================================================================

Lesson 03's supervisor called the subagent and waited for it to return --
that's DELEGATION. There's a second, different thing people mean by
"hand this off to another agent": a CONTROL HANDOFF, where the current
agent steps aside entirely and a separate runner loop moves control to
the next one. Both are real patterns; they produce different call stacks,
which this lesson makes visible instead of just describing.

    3. DELEGATION                       4. CONTROL HANDOFF
       supervisor                           runner_loop
         |- await specialist_a                 current = "agent_a"
         |    |- await specialist_b            while True:
         |                                          result = AGENTS[current]()
       nested stack: supervisor's frame           if isinstance(result, Handoff):
       is still on the stack the whole                current = result.next_agent
       time both specialists run                      continue
                                                    return result

       each call ADDS to the stack              flat stack: nobody is
       (depth grows: 0 -> 1 -> 2)                "waiting" on anybody else
                                                  (depth stays 1 the whole time)

Delegation is simpler and is what lesson 03 used. Handoff is what you
reach for once a step might run long, pause for a human (a guard-pattern
return, same idea as learn-fastmcp-server lesson 15), or resume on a
totally different process later -- there's no stack frame anywhere still
waiting for it. This is LangGraph's `Command(goto=...)` under the hood.

Run:  uv run python 04_delegation_vs_handoff.py
"""

import inspect
from dataclasses import dataclass


def stack_depth() -> int:
    return len(inspect.stack())


# ------------------------------------------------------------- 1. delegation
def demo_delegation() -> None:
    print("=== part 1: delegation -- nested calls, growing stack ===")
    base = stack_depth()

    def specialist_a():
        print("  specialist_a: depth relative to supervisor ->", stack_depth() - base)
        specialist_b()   # called FROM INSIDE specialist_a -- this is the nesting

    def specialist_b():
        print("  specialist_b: depth relative to supervisor ->", stack_depth() - base)

    print("supervisor: depth relative to itself -> 0")
    specialist_a()
    print("supervisor: back here, was on the stack the whole time")


# -------------------------------------------------------- 2. control handoff
@dataclass
class Handoff:
    next_agent: str


def demo_handoff() -> None:
    print("\n=== part 2: control handoff -- a runner loop, flat stack ===")

    def agent_a(base: int):
        print("  agent_a: depth relative to runner ->", stack_depth() - base)
        return Handoff("agent_b")   # steps ASIDE -- does not call agent_b itself

    def agent_b(base: int):
        print("  agent_b: depth relative to runner ->", stack_depth() - base)
        return "done"

    agents = {"agent_a": agent_a, "agent_b": agent_b}

    def runner_loop(start: str) -> str:
        base = stack_depth()
        current = start
        while True:
            result = agents[current](base)
            if isinstance(result, Handoff):
                current = result.next_agent
                continue   # back to the TOP of this loop -- not a nested call
            return result

    print("runner result:", runner_loop("agent_a"))


if __name__ == "__main__":
    demo_delegation()
    demo_handoff()

# Expected output:
#
# === part 1: delegation -- nested calls, growing stack ===
# supervisor: depth relative to itself -> 0
#   specialist_a: depth relative to supervisor -> 1
#   specialist_b: depth relative to supervisor -> 2
# supervisor: back here, was on the stack the whole time
#
# === part 2: control handoff -- a runner loop, flat stack ===
#   agent_a: depth relative to runner -> 1
#   agent_b: depth relative to runner -> 1     <- SAME depth as agent_a, not +1
# runner result: done
#
# agent_b's depth matches agent_a's exactly -- the runner called it fresh,
# not from inside agent_a. That flatness is the entire point of a handoff:
# no frame is left anywhere waiting on anything.
