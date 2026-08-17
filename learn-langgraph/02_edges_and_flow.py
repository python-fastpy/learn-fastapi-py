"""Lesson 02 — Edges & Flow
===========================

WHY THIS MATTERS
----------------
In lesson 01 you built a single-node graph. Real workflows have multiple steps
that must run in order -- greet, then decorate, then summarize. Edges define
that order. Without them, nodes would be isolated islands with no connection.

This is the foundation of every pipeline: the backend orchestrator chains
analyze -> route -> execute -> synthesize in exactly this pattern.

WHAT YOU'LL LEARN
-----------------
1. add_edge(): connect nodes into a sequential pipeline
2. State accumulation: each node reads output from prior nodes
3. Partial returns: nodes return only the keys they change
4. How LangGraph merges partial returns into the full state
5. The pattern behind every sequential workflow in production

Concepts
--------
- add_edge(A, B): after node A completes, always run node B
- State is a TypedDict -- all nodes share the same schema
- Partial return: {"greeting": "..."} updates only `greeting`, other keys untouched
- LangGraph merges returns automatically (no manual state management)

Graph
-----
  +-------+     +-------+     +----------+     +-----------+     +-----+
  | START | --> | greet | --> | decorate | --> | summarize | --> | END |
  +-------+     +-------+     +----------+     +-----------+     +-----+

  Execution trace (input: {"name": "Alice"}):
    greet     reads `name`                -> sets `greeting`  = "Hello, Alice!"
    decorate  reads `greeting`            -> sets `decorated` = "*** Hello, Alice! ***"
    summarize reads `name` + `greeting`   -> sets `summary`   = "Greeting for Alice: 13 chars"

Maps to
-------
  langgraph_mcp_orchestrator.py -> sequential node chaining (analyze -> route -> execute -> synthesize)
  story-drafting workflows      -> multi-step tool pipelines (RIC resolve -> fetch -> generate -> refine)

PREREQUISITES: Lesson 01 (basic StateGraph setup)

No LLM needed -- simulates a 3-step greeting pipeline.

Run:  uv run python 02_edges_and_flow.py

EXPECTED OUTPUT
---------------
  Greeting:  Hello, Alice!
  Decorated: *** Hello, Alice! ***
  Summary:   Greeting for Alice: 13 chars
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# -- Step 1: Define the state schema -----------------------------------------
# All nodes share this schema. Each node reads what it needs and returns only
# the keys it changes -- LangGraph merges the partial return into the full state.
class State(TypedDict):
    name: str
    greeting: str
    decorated: str
    summary: str


# -- Step 2: Define the nodes (one function per pipeline step) ----------------
# Each node receives the full state but returns ONLY the key(s) it sets.
# This "partial return" pattern keeps nodes focused and composable --
# they don't need to know about keys they don't touch.

def greet(state: State) -> dict:
    # Reads: name | Sets: greeting
    return {"greeting": f"Hello, {state['name']}!"}


def decorate(state: State) -> dict:
    # Reads: greeting (set by greet) | Sets: decorated
    return {"decorated": f"*** {state['greeting']} ***"}


def summarize(state: State) -> dict:
    # Reads: name + greeting | Sets: summary
    return {"summary": f"Greeting for {state['name']}: {len(state['greeting'])} chars"}


# -- Step 3: Build the pipeline (add_node + add_edge) ------------------------
# add_edge(A, B) means "after A finishes, always run B next."
# This creates a strict sequential pipeline: greet -> decorate -> summarize.
graph = StateGraph(State)
graph.add_node("greet", greet)
graph.add_node("decorate", decorate)
graph.add_node("summarize", summarize)

graph.add_edge(START, "greet")        # Entry point: start with greet
graph.add_edge("greet", "decorate")   # After greet, always decorate
graph.add_edge("decorate", "summarize")  # After decorate, always summarize
graph.add_edge("summarize", END)      # After summarize, we're done

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    result = app.invoke({"name": "Alice"})

    print(f"Greeting:  {result['greeting']}")
    print(f"Decorated: {result['decorated']}")
    print(f"Summary:   {result['summary']}")

    # -- Key takeaway --------------------------------------------------------
    # Each node returns ONLY the keys it changed -- greet returns {"greeting"},
    # decorate returns {"decorated"}, summarize returns {"summary"}.
    # LangGraph merges each partial return into the full state automatically.
    #
    # This is why nodes are composable: they don't need to know about the
    # full state schema. You can reorder, remove, or insert nodes without
    # rewriting the others -- as long as the keys they read are available.
    #
    # This pattern maps directly to the production orchestrator, where
    # analyze -> route -> execute -> synthesize each update different
    # parts of the state without touching each other's keys.
    #
    # -- Exercise -------------------------------------------------------------
    # Add a 4th node `farewell` between summarize and END that sets a
    # new state key `farewell_msg` to "Goodbye, {name}! Hope to see you soon."
