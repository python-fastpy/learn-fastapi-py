"""Lesson 02 — Edges & Flow
===========================
Concepts:
  - Sequential pipelines: node A -> node B -> node C
  - Each node sees the accumulated state from all prior nodes
  - State keys are merged (not replaced) -- you return only what changed

Graph:
  +-------+     +-------+     +----------+     +-----------+     +-----+
  | START | --> | greet | --> | decorate | --> | summarize | --> | END |
  +-------+     +-------+     +----------+     +-----------+     +-----+

  State accumulates through each node:
    greet     sets: greeting    (reads: name)
    decorate  sets: decorated   (reads: greeting)
    summarize sets: summary     (reads: name, greeting)

No LLM needed — simulates a 3-step greeting pipeline.

Run:  uv run python 02_edges_and_flow.py

Expected output:
  Greeting:  Hello, Alice!
  Decorated: *** Hello, Alice! ***
  Summary:   Greeting for Alice: 13 chars
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    name: str
    greeting: str
    decorated: str
    summary: str


def greet(state: State) -> dict:
    return {"greeting": f"Hello, {state['name']}!"}


def decorate(state: State) -> dict:
    return {"decorated": f"*** {state['greeting']} ***"}


def summarize(state: State) -> dict:
    return {"summary": f"Greeting for {state['name']}: {len(state['greeting'])} chars"}


# Build the pipeline: greet → decorate → summarize
graph = StateGraph(State)
graph.add_node("greet", greet)
graph.add_node("decorate", decorate)
graph.add_node("summarize", summarize)

graph.add_edge(START, "greet")
graph.add_edge("greet", "decorate")
graph.add_edge("decorate", "summarize")
graph.add_edge("summarize", END)

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
    # Each node only returns the keys it modifies.
    # LangGraph merges them into the full state automatically.
    #
    # -- Exercise -------------------------------------------------------------
    # Add a 4th node `farewell` between summarize and END that sets a
    # new state key `farewell_msg` to "Goodbye, {name}! Hope to see you soon."
