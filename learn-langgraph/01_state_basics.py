"""Lesson 01 -- State and Graph Basics
======================================

A LangGraph app is three things: a STATE that flows, NODES that change it, and
EDGES that decide what runs next. No LLM involved -- this is the mechanics.

  ┌──── the graph ────┐        what travels along the edges
  │                   │
  │      START        │        START   {"name": "Shubham"}
  │        │          │          │
  │        ▼          │          ▼
  │      greet        │        greet   reads `name`, returns ONLY
  │        │          │                {"greeting": "Hello, Shubham!"}
  │        ▼          │          │
  │       END         │          ▼
  │                   │        END     {"name": "Shubham",
  └───────────────────┘                 "greeting": "Hello, Shubham!"}

  1. STATE     a TypedDict. Every node is handed the whole thing.
  2. NODE      a plain function: state in, a PARTIAL dict out.
  3. PARTIAL   return only the keys you changed. LangGraph merges them into
               the state, so nodes cannot clobber each other by accident.
  4. EDGES     add_edge(START, "greet") is the entry, add_edge("greet", END)
               the exit. A node with no edges never runs.
  5. COMPILE   graph.compile() turns the builder into something invokable.
               Forget it and there is nothing to call.

Run:  uv run python 01_state_basics.py
      uv run python 01_state_basics.py --png    (also render the graph as an image;
                                                 needs the network -- see below)

Maps to: every StateGraph in langgraph_mcp_orchestrator.py
"""

import sys
from typing import TypedDict

from langgraph.graph import END, START, StateGraph


# -- 1. STATE: the shape that flows through the graph ------------------------

class State(TypedDict):
    name: str
    greeting: str


# -- 2 + 3. NODE: state in, partial dict out ---------------------------------
# It reads `name` and sets `greeting`. It says nothing about `name`, so `name`
# survives untouched.

def greet(state: State) -> dict:
    return {"greeting": f"Hello, {state['name']}! Welcome to LangGraph."}


# -- 4. EDGES: wire START -> greet -> END ------------------------------------

graph = StateGraph(State)
graph.add_node("greet", greet)
graph.add_edge(START, "greet")
graph.add_edge("greet", END)

# -- 5. COMPILE: builder -> runnable -----------------------------------------
app = graph.compile()


if __name__ == "__main__":
    # The graph can describe itself. This is text, so it costs nothing.
    print("=== graph (mermaid -- paste into mermaid.live) ===")
    print(app.get_graph().draw_mermaid())

    result = app.invoke({"name": "Shubham"})
    print("=== result ===")
    print(result)
    print("\n`name` is still there: a partial return MERGED, it did not replace.")

    # draw_mermaid_png() renders via the remote mermaid.ink service, so it
    # needs the network and it opens an image viewer. Opt in with --png.
    if "--png" in sys.argv:
        import os
        import tempfile

        png = app.get_graph().draw_mermaid_png()
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        tmp.write(png)
        tmp.close()
        os.startfile(tmp.name)
        print(f"\nwrote {tmp.name}")

# Exercises:
# 1. Add `farewell: str` to State, a `say_goodbye` node that sets it, and wire
#    START -> greet -> say_goodbye -> END. Both keys should survive.
# 2. Make greet return {"name": "someone else"} as well. Which wins, and why
#    is that different from the `log` case in lesson 04?
# 3. Delete the add_edge(START, "greet") line. What does invoke() do now?
# 4. Skip graph.compile() and call graph.invoke() instead. Read the error --
#    it is the most common LangGraph mistake.
