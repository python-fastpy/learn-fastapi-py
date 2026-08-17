"""Lesson 12 --- Error Handling & Retry
======================================
Concepts:
  - RetryPolicy: automatic retries with exponential backoff
  - Error edges: route to fallback nodes on failure
  - Graceful degradation in agent workflows
  - Maps to your backend's retry logic in the orchestrator

Graph A (RetryPolicy):
  +-------+     +-------------+     +------------------+     +-----+
  | START | --> | flaky_greet | --> | format_greeting  | --> | END |
  +-------+     +-------------+     +------------------+     +-----+
                  RetryPolicy:
                  max_attempts=5
                  backoff_factor=2.0

Graph B (Error Routing with Fallback):
  +-------+     +---------+
  | START | --> | primary |
  +-------+     +---------+
                     |
          route_after_primary()
              /            \\
             v              v
       +----------+   +---------------+
       | fallback |   | format_output |
       +----------+   +---------------+
             |              |
             +-> format_output -> END

No LLM needed -- demonstrates retry and fallback patterns with pure logic.

Run:  uv run python 12_error_handling.py

Expected output (Part A -- attempts vary due to randomness):
  === Part A: RetryPolicy ===

    Attempt #1...
    Attempt #2...
    Attempt #3...

  Result: FORMATTED: Hello, Alice! (attempt 3)
  Took 3 attempts

Expected output (Part B):
  === Part B: Error Routing ===

  --- Known name ---
  Result: FINAL [primary]: Hello, Alice! Welcome!

  --- Unknown name (triggers fallback) ---
    Primary failed: Cannot greet: Unknown Person
  Result: FINAL [fallback]: Hi Unknown Person! (from cache)
"""

import random
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

_call_count = 0


# -- Part A: RetryPolicy -----------------------------------------------

class State(TypedDict):
    name: str
    greeting: str
    error: str
    attempts: int


def flaky_greet(state: State) -> dict:
    """Simulates a flaky greeting API -- fails 60% of the time."""
    global _call_count
    _call_count += 1
    print(f"  Attempt #{_call_count}...")

    if random.random() < 0.6:
        raise ConnectionError(f"Greeting service timeout on attempt {_call_count}")

    return {
        "greeting": f"Hello, {state['name']}! (attempt {_call_count})",
        "attempts": _call_count,
    }


def format_greeting(state: State) -> dict:
    return {"greeting": f"FORMATTED: {state['greeting']}"}


# Build graph with RetryPolicy on the flaky node
graph_a = StateGraph(State)
graph_a.add_node(
    "flaky_greet",
    flaky_greet,
    retry=RetryPolicy(
        max_attempts=5,
        initial_interval=0.1,
        backoff_factor=2.0,
    ),
)
graph_a.add_node("format_greeting", format_greeting)

graph_a.add_edge(START, "flaky_greet")
graph_a.add_edge("flaky_greet", "format_greeting")
graph_a.add_edge("format_greeting", END)

app_a = graph_a.compile()


# -- Part B: Error edges with try/except in nodes ----------------------

class SafeState(TypedDict):
    name: str
    greeting: str
    fallback_greeting: str
    source: str


def primary_greet(state: SafeState) -> dict:
    """Try the primary greeting source -- may fail."""
    if "unknown" in state["name"].lower():
        raise ValueError(f"Cannot greet: {state['name']}")
    return {"greeting": f"Hello, {state['name']}! Welcome!", "source": "primary"}


def fallback_greet(state: SafeState) -> dict:
    return {"fallback_greeting": f"Hi {state['name']}! (from cache)", "source": "fallback"}


def safe_primary(state: SafeState) -> dict:
    """Wrapper that catches errors and signals for routing."""
    try:
        return primary_greet(state)
    except Exception as e:
        print(f"  Primary failed: {e}")
        return {"source": "error"}


def route_after_primary(state: SafeState) -> Literal["format_output", "fallback"]:
    if state.get("source") == "error":
        return "fallback"
    return "format_output"


def format_output(state: SafeState) -> dict:
    data = state.get("greeting") or state.get("fallback_greeting", "")
    return {"greeting": f"FINAL [{state['source']}]: {data}"}


graph_b = StateGraph(SafeState)
graph_b.add_node("primary", safe_primary)
graph_b.add_node("fallback", fallback_greet)
graph_b.add_node("format_output", format_output)

graph_b.add_edge(START, "primary")
graph_b.add_conditional_edges("primary", route_after_primary)
graph_b.add_edge("fallback", "format_output")
graph_b.add_edge("format_output", END)

app_b = graph_b.compile()


if __name__ == "__main__":
    print("=== Graph A Diagram (Mermaid) - RetryPolicy ===")
    print(app_a.get_graph().draw_mermaid())
    print()
    print("=== Graph B Diagram (Mermaid) - Error Routing ===")
    print(app_b.get_graph().draw_mermaid())
    print()

    # -- Part A: RetryPolicy demo --------------------------------------
    print("=== Part A: RetryPolicy ===\n")
    _call_count = 0
    try:
        result_a = app_a.invoke({"name": "Alice"})
        print(f"\nResult: {result_a['greeting']}")
        print(f"Took {result_a['attempts']} attempts")
    except Exception as e:
        print(f"\nAll retries failed: {e}")

    # -- Part B: Error routing demo ------------------------------------
    print("\n=== Part B: Error Routing ===\n")

    print("--- Known name ---")
    r1 = app_b.invoke({"name": "Alice"})
    print(f"Result: {r1['greeting']}\n")

    print("--- Unknown name (triggers fallback) ---")
    r2 = app_b.invoke({"name": "Unknown Person"})
    print(f"Result: {r2.get('greeting') or r2.get('fallback_greeting')}")

    # -- Key takeaway --------------------------------------------------
    # Two strategies for handling failures:
    #
    # 1. RetryPolicy -- automatic retries with backoff for transient
    #    errors (API timeouts, rate limits). Your backend uses this
    #    for MCP tool calls.
    #
    # 2. Error routing -- catch errors in nodes and use conditional
    #    edges to route to fallback nodes. This gives you graceful
    #    degradation instead of hard failures.
    #
    # -- Exercise ------------------------------------------------------
    # 1. Combine both: add RetryPolicy to primary_greet AND keep
    #    the fallback routing for when all retries fail
    # 2. Add a node that logs the error to a "log" state key
    #    (use Annotated[list, operator.add] to accumulate logs)
