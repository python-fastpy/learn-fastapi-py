"""Lesson 11 — Subgraphs
========================
Concepts:
  - Composing graphs: one graph can be a node in another
  - Subgraphs have their own state (can differ from parent)
  - Parent <-> subgraph communication via shared state keys
  - This maps to your skill workflows: each skill is like a subgraph

Graph (Parent):
  +-------+     +----------+     +-------------------+     +----------+     +-----+
  | START | --> | greeting | --> | farewell_pipeline | --> | finalize | --> | END |
  +-------+     +----------+     +-------------------+     +----------+     +-----+
                (subgraph)       (subgraph)

  Greeting subgraph:              Farewell subgraph:
  +---------+     +----------+    +----------------+     +-----------------+
  | compose | --> | decorate |    | write_farewell | --> | format_farewell |
  +---------+     +----------+    +----------------+     +-----------------+

No LLM needed -- demonstrates the composition pattern with pure logic.

Run:  uv run python 11_subgraphs.py
"""

import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END


# -- Subgraph 1: Greeting Pipeline -------------------------------------------

class GreetingState(TypedDict):
    name: str
    steps: Annotated[list[str], operator.add]


def compose(state: GreetingState) -> dict:
    return {"steps": [f"Composed greeting for '{state['name']}'"]}


def decorate(state: GreetingState) -> dict:
    return {"steps": ["Decorated greeting"]}


greeting_graph = StateGraph(GreetingState)
greeting_graph.add_node("compose", compose)
greeting_graph.add_node("decorate", decorate)
greeting_graph.add_edge(START, "compose")
greeting_graph.add_edge("compose", "decorate")
greeting_graph.add_edge("decorate", END)

greeting_subgraph = greeting_graph.compile()


# -- Subgraph 2: Farewell Pipeline -------------------------------------------

class FarewellState(TypedDict):
    steps: list[str]
    farewell: str


def write_farewell(state: FarewellState) -> dict:
    return {"farewell": f"Goodbye! Based on {len(state['steps'])} steps so far."}


def format_farewell(state: FarewellState) -> dict:
    return {"farewell": state["farewell"] + " [FORMATTED]"}


farewell_graph = StateGraph(FarewellState)
farewell_graph.add_node("write_farewell", write_farewell)
farewell_graph.add_node("format_farewell", format_farewell)
farewell_graph.add_edge(START, "write_farewell")
farewell_graph.add_edge("write_farewell", "format_farewell")
farewell_graph.add_edge("format_farewell", END)

farewell_subgraph = farewell_graph.compile()


# -- Parent graph: composes both subgraphs ------------------------------------

class ParentState(TypedDict):
    name: str
    steps: Annotated[list[str], operator.add]
    farewell: str
    status: str


def finalize(state: ParentState) -> dict:
    return {"status": f"Complete: {state['farewell'][:60]}..."}


parent = StateGraph(ParentState)

# Add compiled subgraphs as nodes -- they run as self-contained units
parent.add_node("greeting", greeting_subgraph)
parent.add_node("farewell_pipeline", farewell_subgraph)
parent.add_node("finalize", finalize)

parent.add_edge(START, "greeting")
parent.add_edge("greeting", "farewell_pipeline")
parent.add_edge("farewell_pipeline", "finalize")
parent.add_edge("finalize", END)

app = parent.compile()


if __name__ == "__main__":
    result = app.invoke({"name": "Alice"})

    print(f"Name:     {result['name']}")
    print(f"Steps:    {result['steps']}")
    print(f"Farewell: {result['farewell']}")
    print(f"Status:   {result['status']}")

    # NOTE: Steps may appear duplicated. This happens because both
    # the subgraph (GreetingState) and parent (ParentState) define
    # `steps` with operator.add. When the subgraph returns, LangGraph
    # merges its output into the parent using the parent's reducer too.
    # Fix: use a plain list (no reducer) in either the subgraph or parent.
    # The FarewellState intentionally uses a plain list to avoid this.

    # Visualize the graph structure (Mermaid)
    print("\n=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())

    # -- Key takeaway ---------------------------------------------------------
    # Subgraphs let you build complex systems from smaller, testable
    # units. Each subgraph:
    #   - Has its own state schema
    #   - Shares keys with the parent via matching key names
    #   - Can be tested independently
    #
    # Notice GreetingState uses Annotated[list[str], operator.add] for
    # `steps` (same reducer as the parent), while FarewellState uses a
    # plain list[str]. This shows how reducer mismatches between parent
    # and subgraph affect merged output.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a third subgraph: "personalize" between greeting and farewell
    # 2. Give it its own state with a `tone: str` key (e.g., "formal")
    # 3. In the parent, use conditional edges: if tone == "formal" -> skip
    #    farewell and go directly to finalize
