"""Lesson 12 — Error Handling & Retry
======================================
Concepts:
  - RetryPolicy: automatic retries with exponential backoff
  - Error edges: route to fallback nodes on failure
  - Graceful degradation in agent workflows
  - Maps to your backend's retry logic in the orchestrator

Graph A (RetryPolicy):
  +-------+     +----------+     +--------+     +-----+
  | START | --> | api_call | --> | format | --> | END |
  +-------+     +----------+     +--------+     +-----+
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
"""

import random
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

_call_count = 0


# ── Part A: RetryPolicy ─────────────────────────────────────────────

class State(TypedDict):
    query: str
    result: str
    error: str
    attempts: int


def flaky_api_call(state: State) -> dict:
    """Simulates a flaky API -- fails 60% of the time."""
    global _call_count
    _call_count += 1
    print(f"  Attempt #{_call_count}...")

    if random.random() < 0.6:
        raise ConnectionError(f"API timeout on attempt {_call_count}")

    return {
        "result": f"Data for '{state['query']}' (succeeded on attempt {_call_count})",
        "attempts": _call_count,
    }


def format_result(state: State) -> dict:
    return {"result": f"FORMATTED: {state['result']}"}


def handle_error(state: State) -> dict:
    return {
        "result": "Service temporarily unavailable. Please try again.",
        "error": "All retry attempts exhausted",
    }


# Build graph with RetryPolicy on the flaky node
graph_a = StateGraph(State)
graph_a.add_node(
    "api_call",
    flaky_api_call,
    retry=RetryPolicy(
        max_attempts=5,
        initial_interval=0.1,
        backoff_factor=2.0,
    ),
)
graph_a.add_node("format", format_result)

graph_a.add_edge(START, "api_call")
graph_a.add_edge("api_call", "format")
graph_a.add_edge("format", END)

app_a = graph_a.compile()


# ── Part B: Error edges with try/except in nodes ─────────────────────

class SafeState(TypedDict):
    topic: str
    primary_result: str
    fallback_result: str
    source: str


def primary_lookup(state: SafeState) -> dict:
    """Try the primary data source -- may fail."""
    if "unknown" in state["topic"].lower():
        raise ValueError(f"No data found for topic: {state['topic']}")
    return {
        "primary_result": f"Premium data about {state['topic']}",
        "source": "primary",
    }


def fallback_lookup(state: SafeState) -> dict:
    """Fallback data source -- always works but less detailed."""
    return {
        "fallback_result": f"Basic info about {state['topic']} (from cache)",
        "source": "fallback",
    }


def safe_primary(state: SafeState) -> dict:
    """Wrapper that catches errors and signals for routing."""
    try:
        return primary_lookup(state)
    except Exception as e:
        print(f"  Primary failed: {e}")
        return {"source": "error"}


def route_after_primary(state: SafeState) -> Literal["format_output", "fallback"]:
    if state.get("source") == "error":
        return "fallback"
    return "format_output"


def format_output(state: SafeState) -> dict:
    data = state.get("primary_result") or state.get("fallback_result", "")
    return {"primary_result": f"FINAL [{state['source']}]: {data}"}


graph_b = StateGraph(SafeState)
graph_b.add_node("primary", safe_primary)
graph_b.add_node("fallback", fallback_lookup)
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

    # ── Part A: RetryPolicy demo ─────────────────────────────────────
    print("=== Part A: RetryPolicy ===\n")
    _call_count = 0
    try:
        result_a = app_a.invoke({"query": "OPEC production data"})
        print(f"\nResult: {result_a['result']}")
        print(f"Took {result_a['attempts']} attempts")
    except Exception as e:
        print(f"\nAll retries failed: {e}")

    # ── Part B: Error routing demo ───────────────────────────────────
    print("\n=== Part B: Error Routing ===\n")

    print("--- Known topic ---")
    r1 = app_b.invoke({"topic": "Oil Markets"})
    print(f"Result: {r1['primary_result']}\n")

    print("--- Unknown topic (triggers fallback) ---")
    r2 = app_b.invoke({"topic": "Unknown Sector XYZ"})
    print(f"Result: {r2.get('primary_result') or r2.get('fallback_result')}")

    # ── Key takeaway ─────────────────────────────────────────────────
    # Two strategies for handling failures:
    #
    # 1. RetryPolicy — automatic retries with backoff for transient
    #    errors (API timeouts, rate limits). Your backend uses this
    #    for MCP tool calls.
    #
    # 2. Error routing — catch errors in nodes and use conditional
    #    edges to route to fallback nodes. This gives you graceful
    #    degradation instead of hard failures.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Combine both: add RetryPolicy to primary_lookup AND keep
    #    the fallback routing for when all retries fail
    # 2. Add a node that logs the error to a "log" state key
    #    (use Annotated[list, operator.add] to accumulate logs)
