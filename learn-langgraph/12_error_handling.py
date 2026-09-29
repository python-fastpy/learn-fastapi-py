"""Lesson 12 -- Error Handling and Retry
=======================================

Things fail: services time out, inputs are wrong. One unhandled exception in
one node kills the whole run. There are two answers, and picking the wrong
one is the mistake worth avoiding.

  TRANSIENT failure -- might work if you just try again (timeout, rate limit)
  ► RetryPolicy on the node. LangGraph re-runs it for you.

    START ──► flaky_greet ──► format ──► END
                  ↺ retry=RetryPolicy(max_attempts=5,
                       initial_interval=0.1, backoff_factor=2.0)
                    waits 0.1s, 0.2s, 0.4s, 0.8s between attempts

  PERMANENT failure -- will never work with this input (unknown name, bad id)
  ► catch it, record it in state, and route somewhere useful.

    START ──► primary ──┬── ok ─────────────► format ──► END
                        │                       ▲
                        └── error ──► fallback ─┘
                                      a cached answer: degraded, not dead

  1. RetryPolicy      add_node("x", fn, retry=RetryPolicy(...)). Per node --
                      the others are unaffected. Your node just raises.
  2. BACKOFF          initial_interval * backoff_factor ** attempt, so the
                      gaps widen instead of hammering a struggling service.
  3. GIVING UP        after max_attempts the exception propagates to the
                      caller. Retry defers failure, it does not remove it.
  4. ERROR ROUTING    try/except inside the node, write a flag into state,
                      and let a conditional edge (lesson 03) read it.
  5. DEGRADE          the fallback returns something usable, so the user gets
                      an answer rather than a stack trace.

  Retry re-runs the WHOLE node, exactly like lesson 09's resume. Anything in
  it that is not safe to repeat -- a charge, an insert, an email -- will
  happen once per attempt. Retry only belongs on idempotent work.

Run:  uv run python 12_error_handling.py      (no LLM needed)

Maps to: MCP tool calls retry on timeout; the orchestrator routes to a
fallback when a skill is unavailable
"""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import RetryPolicy

# -- Part A: a transient failure, fixed by retrying -------------------------

attempts = 0            # deterministic on purpose: fail twice, then succeed


class State(TypedDict):
    name: str
    greeting: str


def flaky_greet(state: State) -> dict:
    """Stands in for an MCP call that times out. It just raises."""
    global attempts
    attempts += 1
    print(f"     attempt #{attempts}")
    if attempts < 3:
        raise ConnectionError("greeting service timed out")
    return {"greeting": f"Hello, {state['name']}! (succeeded on attempt {attempts})"}


def format_greeting(state: State) -> dict:
    return {"greeting": f"FORMATTED: {state['greeting']}"}


graph_a = StateGraph(State)
graph_a.add_node("flaky_greet", flaky_greet,
                 retry=RetryPolicy(max_attempts=5, initial_interval=0.1, backoff_factor=2.0))
graph_a.add_node("format", format_greeting)
graph_a.add_edge(START, "flaky_greet")
graph_a.add_edge("flaky_greet", "format")
graph_a.add_edge("format", END)
app_a = graph_a.compile()


# -- Part B: a permanent failure, routed to a fallback ---------------------

KNOWN = {"Shubham", "Ben"}


class SafeState(TypedDict):
    name: str
    greeting: str
    source: str          # "primary" | "error" -- what the router reads


def primary_greet(state: SafeState) -> dict:
    """Retrying this would fail identically forever, so catch and flag."""
    try:
        if state["name"] not in KNOWN:
            raise ValueError(f"no record of {state['name']}")
        return {"greeting": f"Hello, {state['name']}! Welcome!", "source": "primary"}
    except ValueError as e:
        print(f"     primary failed: {e}")
        return {"source": "error"}


def fallback_greet(state: SafeState) -> dict:
    return {"greeting": f"Hi {state['name']}! (generic greeting)", "source": "fallback"}


def format_output(state: SafeState) -> dict:
    return {"greeting": f"[{state['source']}] {state['greeting']}"}


def route_after_primary(state: SafeState) -> Literal["fallback", "format"]:
    return "fallback" if state["source"] == "error" else "format"


graph_b = StateGraph(SafeState)
graph_b.add_node("primary", primary_greet)
graph_b.add_node("fallback", fallback_greet)
graph_b.add_node("format", format_output)
graph_b.add_edge(START, "primary")
graph_b.add_conditional_edges("primary", route_after_primary)
graph_b.add_edge("fallback", "format")
graph_b.add_edge("format", END)
app_b = graph_b.compile()


if __name__ == "__main__":
    print("A. transient failure + RetryPolicy")
    r = app_a.invoke({"name": "Shubham", "greeting": ""})
    print(f"   -> {r['greeting']}")
    print(f"   the node ran {attempts} times; the graph ran once\n")

    print("B. permanent failure + error routing")
    for name in ("Shubham", "Nobody"):
        r = app_b.invoke({"name": name, "greeting": "", "source": ""})
        print(f"   {name:<8} -> {r['greeting']}")

    print("\nRetrying 'Nobody' would have failed five times and still crashed;")
    print("routing gave an answer on the first try. Match the tool to the fault.")

# Exercises:
# 1. Change `attempts < 3` to `attempts < 9`. Five attempts are exhausted and
#    the exception reaches you -- point 3, retry is not a guarantee.
# 2. Put RetryPolicy on `primary` too and add "Nobody". Watch it burn five
#    attempts on an error that could never succeed.
# 3. Add a print at the TOP of flaky_greet, before the raise. It fires on
#    every attempt -- that is the idempotency warning, made visible.
# 4. Give fallback its own `source` value and route a third way on it, so the
#    caller can tell a cached answer from a live one.
