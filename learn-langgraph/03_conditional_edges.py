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
             route_by_style()
               /            \
              v               v
  +----------------+   +----------------+
  | formal_greet   |   | casual_greet   |
  +----------------+   +----------------+
              \            /
               v          v
              +-----+
              | END |
              +-----+

No LLM needed -- demonstrates branching based on a "style" field.

Run:  uv run python 03_conditional_edges.py

Expected output:
  Dear Alice, it is a pleasure to meet you.
  Hey Bob! What's up?

Key takeaway:
  add_conditional_edges() lets a routing function inspect state and return
  the name of the next node. The graph branches without any if/else inside
  the nodes themselves — the routing logic lives in one small function.

Exercise:
  1. Add a third style: "warm"
  2. Add a warm_greet node: "So lovely to see you, {name}!"
  3. Update route_by_style to return Literal["formal_greet", "casual_greet", "warm_greet"]
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    name: str
    style: str        # "formal" | "casual"
    greeting: str


def classify(state: State) -> dict:
    return {"style": state["style"]}


def formal_greet(state: State) -> dict:
    return {"greeting": f"Dear {state['name']}, it is a pleasure to meet you."}


def casual_greet(state: State) -> dict:
    return {"greeting": f"Hey {state['name']}! What's up?"}


# The routing function — returns the node name to go to next
def route_by_style(state: State) -> Literal["formal_greet", "casual_greet"]:
    return "formal_greet" if state["style"] == "formal" else "casual_greet"


graph = StateGraph(State)
graph.add_node("classify", classify)
graph.add_node("formal_greet", formal_greet)
graph.add_node("casual_greet", casual_greet)

graph.add_edge(START, "classify")

# After classify, use route_by_style to pick the next node
graph.add_conditional_edges("classify", route_by_style)

graph.add_edge("formal_greet", END)
graph.add_edge("casual_greet", END)

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    # Test with formal style
    r1 = app.invoke({"name": "Alice", "style": "formal"})
    print(r1["greeting"])
    # Dear Alice, it is a pleasure to meet you.

    # Test with casual style
    r2 = app.invoke({"name": "Bob", "style": "casual"})
    print(r2["greeting"])
    # Hey Bob! What's up?

    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a third style: "warm"
    # 2. Add a warm_greet node: "So lovely to see you, {name}!"
    # 3. Update route_by_style to return Literal["formal_greet", "casual_greet", "warm_greet"]
