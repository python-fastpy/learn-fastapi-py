"""Lesson 12 --- Error Handling & Retry
======================================

WHY THIS MATTERS:
  Real systems fail: APIs timeout, services go down, inputs are invalid. Without
  error handling, one flaky tool call crashes the entire workflow. LangGraph
  provides two strategies: (1) RetryPolicy for transient failures (auto-retry
  with exponential backoff), and (2) error routing for permanent failures (catch
  the error and route to a fallback node).

  The production backend uses both: MCP tool calls have retry logic for timeouts,
  and the orchestrator has fallback paths when a skill is unavailable.

WHAT YOU'LL LEARN:
  1. RetryPolicy: automatic retries with exponential backoff for transient errors
  2. Error routing: catch errors in nodes and route to fallback nodes
  3. Graceful degradation: fallback responses instead of hard crashes
  4. How retry and fallback combine in production systems
  5. The try/except + conditional edge pattern for error routing

Concepts:
  - RetryPolicy(max_attempts=5, backoff_factor=2.0)
        Automatically retries a node when it raises an exception.  Waits
        initial_interval * backoff_factor^attempt between retries.
  - Node-level retry: add_node("name", fn, retry=RetryPolicy(...))
        Attach a retry policy to a specific node — other nodes are unaffected.
  - Error routing: wrap node logic in try/except, set source="error" in state,
        then use a conditional edge to route to a fallback node.
  - Graceful degradation: the fallback node provides a cached or default
        response so the user still gets an answer.
  - Production pattern: retry transient errors (timeouts, rate limits) with
        RetryPolicy; route to fallback for permanent errors (bad input, missing
        service).

Graph A (RetryPolicy):
  +-------+     +-------------+     +------------------+     +-----+
  | START | --> | flaky_greet | --> | format_greeting  | --> | END |
  +-------+     +-------------+     +------------------+     +-----+
                  RetryPolicy:
                  max_attempts=5
                  backoff_factor=2.0

  Graph A trace:
    Attempt 1: flaky_greet raises ConnectionError -> RetryPolicy catches, waits 0.1s
    Attempt 2: flaky_greet raises ConnectionError -> RetryPolicy catches, waits 0.2s
    Attempt 3: flaky_greet succeeds -> format_greeting -> END
    (if all 5 attempts fail -> exception propagates to caller)

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

  Graph B trace — Known name ("Alice"):
    primary -> source="primary" -> route_after_primary -> "format_output" -> END
    Result: "FINAL [primary]: Hello, Alice! Welcome!"

  Graph B trace — Unknown name ("Unknown Person"):
    primary -> raises ValueError -> caught by safe_primary -> source="error"
    -> route_after_primary -> "fallback" -> fallback_greet -> format_output -> END
    Result: "FINAL [fallback]: Hi Unknown Person! (from cache)"

Maps to production:
  langgraph_mcp_orchestrator.py -> retry logic for MCP tool calls
  mcp_protocol.py               -> connection retry on tool execution
  fast_path_matcher.py          -> fallback to LLM analysis when fast-path fails

PREREQUISITES: Lesson 03 (conditional edges — error routing uses the same pattern)

EXPECTED OUTPUT (Part A — attempts vary due to randomness):
  === Part A: RetryPolicy ===

    Attempt #1...
    Attempt #2...
    Attempt #3...

  Result: FORMATTED: Hello, Alice! (attempt 3)
  Took 3 attempts

EXPECTED OUTPUT (Part B):
  === Part B: Error Routing ===

  --- Known name ---
  Result: FINAL [primary]: Hello, Alice! Welcome!

  --- Unknown name (triggers fallback) ---
    Primary failed: Cannot greet: Unknown Person
  Result: FINAL [fallback]: Hi Unknown Person! (from cache)

No LLM needed -- demonstrates retry and fallback patterns with pure logic.

Run:  uv run python 12_error_handling.py
"""

import random
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

_call_count = 0


# ── Step 1: Part A — RetryPolicy (automatic retries with backoff) ───────────
# RetryPolicy is for TRANSIENT errors: the operation might succeed if you try
# again (network timeouts, rate limits, temporary service outages).  LangGraph
# handles the retry loop automatically — your node just raises an exception and
# RetryPolicy decides whether to retry or give up.

class State(TypedDict):
    name: str
    greeting: str
    error: str
    attempts: int


def flaky_greet(state: State) -> dict:
    """Simulates a flaky greeting API -- fails 60% of the time.

    In production, this is like an MCP tool call that times out due to network
    issues.  The node raises ConnectionError on failure, and RetryPolicy
    catches it automatically — no try/except needed here.
    """
    global _call_count
    _call_count += 1
    print(f"  Attempt #{_call_count}...")

    # 60% chance of failure — simulates an unreliable external service
    if random.random() < 0.6:
        raise ConnectionError(f"Greeting service timeout on attempt {_call_count}")

    return {
        "greeting": f"Hello, {state['name']}! (attempt {_call_count})",
        "attempts": _call_count,
    }


def format_greeting(state: State) -> dict:
    """Format the greeting for display — only runs after flaky_greet succeeds."""
    return {"greeting": f"FORMATTED: {state['greeting']}"}


# Build graph with RetryPolicy on the flaky node.
# RetryPolicy params:
#   max_attempts=5      -> try up to 5 times before giving up
#   initial_interval=0.1 -> wait 0.1s before first retry
#   backoff_factor=2.0   -> double the wait each time (0.1s, 0.2s, 0.4s, 0.8s)
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


# ── Step 2: Part B — Error Routing (catch + conditional edge to fallback) ───
# Error routing is for PERMANENT errors: the operation will never succeed with
# the same input (bad data, missing service, invalid parameters).  Instead of
# crashing, you catch the error, signal it in state, and route to a fallback
# node via a conditional edge.  The user gets a degraded-but-valid response.

class SafeState(TypedDict):
    name: str
    greeting: str
    fallback_greeting: str
    # source tracks which path produced the final result: "primary" or "error"
    source: str


def primary_greet(state: SafeState) -> dict:
    """Try the primary greeting source -- may fail for unknown names.

    In production, this is like calling an MCP tool that fails because the
    input is invalid (e.g., unknown RIC code, missing story ID).
    """
    if "unknown" in state["name"].lower():
        raise ValueError(f"Cannot greet: {state['name']}")
    return {"greeting": f"Hello, {state['name']}! Welcome!", "source": "primary"}


def fallback_greet(state: SafeState) -> dict:
    """Fallback: provide a cached/default response when primary fails.

    In production, this could return cached data, a generic response, or
    results from an alternative service.
    """
    return {"fallback_greeting": f"Hi {state['name']}! (from cache)", "source": "fallback"}


def safe_primary(state: SafeState) -> dict:
    """Wrapper that catches errors and signals for routing.

    This is the key pattern: wrap the risky operation in try/except, and
    set a state key (source="error") that the conditional edge can inspect.
    The error does NOT propagate — it's absorbed and turned into a routing signal.
    """
    try:
        return primary_greet(state)
    except Exception as e:
        print(f"  Primary failed: {e}")
        return {"source": "error"}


def route_after_primary(state: SafeState) -> Literal["format_output", "fallback"]:
    """Conditional edge: route based on whether primary succeeded or failed."""
    if state.get("source") == "error":
        return "fallback"
    return "format_output"


def format_output(state: SafeState) -> dict:
    """Final formatting — works with output from either primary or fallback."""
    data = state.get("greeting") or state.get("fallback_greeting", "")
    return {"greeting": f"FINAL [{state['source']}]: {data}"}


# Build the error-routing graph:
#   primary -> (success) -> format_output -> END
#   primary -> (error)   -> fallback -> format_output -> END
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

    # ── Part A demo: RetryPolicy ─────────────────────────────────────
    # Watch the retry attempts — each one waits longer than the last
    # (exponential backoff).  If all 5 attempts fail, the exception
    # propagates to the caller.
    print("=== Part A: RetryPolicy ===\n")
    _call_count = 0
    try:
        result_a = app_a.invoke({"name": "Alice"})
        print(f"\nResult: {result_a['greeting']}")
        print(f"Took {result_a['attempts']} attempts")
    except Exception as e:
        print(f"\nAll retries failed: {e}")

    # ── Part B demo: Error routing ───────────────────────────────────
    # Two scenarios: known name (primary succeeds) and unknown name
    # (primary fails, fallback provides a cached response).
    print("\n=== Part B: Error Routing ===\n")

    print("--- Known name ---")
    r1 = app_b.invoke({"name": "Alice"})
    print(f"Result: {r1['greeting']}\n")

    print("--- Unknown name (triggers fallback) ---")
    r2 = app_b.invoke({"name": "Unknown Person"})
    print(f"Result: {r2.get('greeting') or r2.get('fallback_greeting')}")

    # ── Key takeaway ─────────────────────────────────────────────────
    # Two complementary strategies for handling failures in LangGraph:
    #
    # 1. RetryPolicy — AUTOMATIC retries with exponential backoff for
    #    TRANSIENT errors (API timeouts, rate limits, temporary outages).
    #    You attach it to a node and LangGraph handles the retry loop.
    #    The node just raises an exception — no try/except needed.
    #    Production: mcp_protocol.py retries MCP tool calls on timeout.
    #
    # 2. Error routing — MANUAL catch + conditional edge for PERMANENT
    #    errors (bad input, missing service, invalid data).  You wrap
    #    the risky logic in try/except, set a signal in state
    #    (source="error"), and use a conditional edge to route to a
    #    fallback node.  The user gets a degraded-but-valid response
    #    instead of a crash.
    #    Production: fast_path_matcher.py falls back to LLM analysis
    #    when pattern matching fails.
    #
    # In production, BOTH strategies are used together:
    #   - RetryPolicy on MCP tool calls (transient network issues)
    #   - Error routing to fallback when a skill is completely unavailable
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Combine both: add RetryPolicy to primary_greet AND keep
    #    the fallback routing for when all retries fail
    # 2. Add a node that logs the error to a "log" state key
    #    (use Annotated[list, operator.add] to accumulate logs)
