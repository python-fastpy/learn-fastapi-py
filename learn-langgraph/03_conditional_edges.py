"""Lesson 03 — Conditional Edges
=================================
Concepts:
  - add_conditional_edges(): route to different nodes based on state
  - The routing function returns the NAME of the next node
  - This is how LangGraph handles if/else branching

Graph:
  +-------+     +----------+
  | START | --> | classify |
  +-------+     +----------+
                     |
            route_by_priority()
               /            \\
              v               v
  +---------------+   +---------------+
  | handle_urgent |   | handle_normal |
  +---------------+   +---------------+
              \\            /
               v          v
              +-----+
              | END |
              +-----+

No LLM needed -- demonstrates branching based on a "priority" field.

Run:  uv run python 03_conditional_edges.py
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    headline: str
    priority: str   # "urgent" | "normal"
    result: str


def classify(state: State) -> dict:
    headline = state["headline"].lower()
    if any(word in headline for word in ["breaking", "urgent", "alert"]):
        return {"priority": "urgent"}
    return {"priority": "normal"}


def handle_urgent(state: State) -> dict:
    return {"result": f"URGENT WIRE: {state['headline']}"}


def handle_normal(state: State) -> dict:
    return {"result": f"Queued for review: {state['headline']}"}


# The routing function — returns the node name to go to next
def route_by_priority(state: State) -> Literal["handle_urgent", "handle_normal"]:
    if state["priority"] == "urgent":
        return "handle_urgent"
    return "handle_normal"


graph = StateGraph(State)
graph.add_node("classify", classify)
graph.add_node("handle_urgent", handle_urgent)
graph.add_node("handle_normal", handle_normal)

graph.add_edge(START, "classify")

# After classify, use route_by_priority to pick the next node
graph.add_conditional_edges("classify", route_by_priority)

graph.add_edge("handle_urgent", END)
graph.add_edge("handle_normal", END)

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    # Test with an urgent headline
    r1 = app.invoke({"headline": "BREAKING: Fed raises rates by 50bps"})
    print(r1["result"])
    # URGENT WIRE: BREAKING: Fed raises rates by 50bps

    # Test with a normal headline
    r2 = app.invoke({"headline": "Quarterly earnings beat expectations"})
    print(r2["result"])
    # Queued for review: Quarterly earnings beat expectations

    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a third priority: "flash" for headlines containing "FLASH"
    # 2. Add a handle_flash node that formats differently
    # 3. Update route_by_priority to handle the new branch
