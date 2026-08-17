"""Lesson 03 — Conditional Edges
=================================

WHY THIS MATTERS
----------------
Sequential pipelines (lesson 02) always run the same path. But real systems
need branching: formal greeting for executives, casual for friends. Conditional
edges let the graph decide at runtime which node to run next, based on the
current state.

This is how the production orchestrator routes between different execution
strategies (none, single, sequential, parallel) and how skills decide between
different drafting modes.

WHAT YOU'LL LEARN
-----------------
1. add_conditional_edges(): route to different nodes based on state
2. Routing functions: inspect state, return the NAME of the next node
3. Literal type hints for valid route targets
4. How this replaces if/else inside nodes (separation of concerns)
5. The pattern behind every routing decision in the orchestrator

Concepts
--------
- add_conditional_edges(source, routing_fn): after source runs, call routing_fn to pick the next node
- Routing function returns a string -- the NAME of the node to go to
- Literal["formal_greet", "casual_greet"] -- type-safe route targets
- Routing logic lives in ONE function, not scattered across nodes

Graph
-----
  +-------+     +----------+
  | START | --> | classify |
  +-------+     +----------+
                     |
             route_by_style()
               /            \\
              v               v
  +----------------+   +----------------+
  | formal_greet   |   | casual_greet   |
  +----------------+   +----------------+
              \\            /
               v          v
              +-----+
              | END |
              +-----+

  Execution traces:
    Input: {"name": "Alice", "style": "formal"}
      classify -> route_by_style() returns "formal_greet" -> formal_greet -> END
      Result: "Dear Alice, it is a pleasure to meet you."

    Input: {"name": "Bob", "style": "casual"}
      classify -> route_by_style() returns "casual_greet" -> casual_greet -> END
      Result: "Hey Bob! What's up?"

Maps to
-------
  langgraph_mcp_orchestrator.py -> route_after_analysis() (picks execution strategy)
  fast_path_matcher.py          -> pattern matching to skip LLM analysis
  06_tool_calling.py            -> should_use_tool() routing function (same pattern)

PREREQUISITES: Lesson 02 (edges and sequential flow)

No LLM needed -- demonstrates branching based on a "style" field.

Run:  uv run python 03_conditional_edges.py

EXPECTED OUTPUT
---------------
  Dear Alice, it is a pleasure to meet you.
  Hey Bob! What's up?
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, START, END


# -- Step 1: Define the state (name, style, greeting) ------------------------
# `style` is the input that drives branching -- the graph reads it at runtime
# to decide which greeting node to execute.
class State(TypedDict):
    name: str
    style: str        # "formal" | "casual"
    greeting: str


# -- Step 2: Define the nodes (classify, formal_greet, casual_greet) ----------
# classify is the entry node -- it passes the style through so the routing
# function can inspect it. The two greet nodes are the branch targets.

def classify(state: State) -> dict:
    # Pass style through so the routing function can read it from state
    return {"style": state["style"]}


def formal_greet(state: State) -> dict:
    # Only runs when route_by_style returns "formal_greet"
    return {"greeting": f"Dear {state['name']}, it is a pleasure to meet you."}


def casual_greet(state: State) -> dict:
    # Only runs when route_by_style returns "casual_greet"
    return {"greeting": f"Hey {state['name']}! What's up?"}


# -- Step 3: The routing function -- returns the node NAME to go to next ------
# This is the key idea: instead of putting if/else inside nodes, you put
# the branching logic in a dedicated function. It inspects state and returns
# a string matching one of the registered node names.
# Literal[] type hints ensure only valid node names are returned.
def route_by_style(state: State) -> Literal["formal_greet", "casual_greet"]:
    return "formal_greet" if state["style"] == "formal" else "casual_greet"


# -- Step 4: Wire the graph (START -> classify -> conditional -> branches -> END)
graph = StateGraph(State)
graph.add_node("classify", classify)
graph.add_node("formal_greet", formal_greet)
graph.add_node("casual_greet", casual_greet)

graph.add_edge(START, "classify")

# After classify, call route_by_style to decide the next node.
# This replaces a manual if/else -- the graph handles the branching.
graph.add_conditional_edges("classify", route_by_style)

# Both branches converge to END
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

    # ── Key takeaway ─────────────────────────────────────────────────
    # Routing logic lives in ONE function (route_by_style), not scattered
    # across nodes. This separation of concerns makes graphs maintainable:
    # - Nodes focus on WHAT to do (generate a greeting)
    # - The routing function focuses on WHERE to go next
    # - The graph definition focuses on HOW they connect
    #
    # This is the same pattern used in lesson 06 (tool calling), where
    # should_use_tool() routes between calling a tool and returning a
    # direct response -- conditional edges are the backbone of agent loops.
    #
    # In production, route_after_analysis() in the orchestrator uses this
    # exact pattern to pick between execution strategies (none, single,
    # sequential, parallel) based on the LLM's analysis of the user query.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a third style: "warm"
    # 2. Add a warm_greet node: "So lovely to see you, {name}!"
    # 3. Update route_by_style to return Literal["formal_greet", "casual_greet", "warm_greet"]
