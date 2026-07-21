"""Lesson 01 — State & Graph Basics
===================================
Concepts:
  - StateGraph: the container for your entire workflow
  - State: a TypedDict that flows through every node
  - Nodes: plain Python functions that receive state and return partial updates
  - START / END: special markers for graph entry/exit

Graph:
  +-------+     +-------+     +-----+
  | START | --> | greet | --> | END |
  +-------+     +-------+     +-----+

  State flows:
    START sends {name: "Shubham"}
    greet receives it, returns {greeting: "Hello, Shubham!..."}
    END receives {name: "Shubham", greeting: "Hello, Shubham!..."}

No LLM needed — pure Python logic to learn the mechanics.

Run:  uv run python 01_state_basics.py
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


# ── Step 1: Define your State ────────────────────────────────────────
# State is just a TypedDict. Every node receives it and returns a
# partial dict of the keys it wants to update.

class State(TypedDict):
    name: str
    greeting: str


# ── Step 2: Define node functions ────────────────────────────────────
# A node is a plain function: it takes the current state, does work,
# and returns a dict with the keys to update.

def greet(state: State) -> dict:
    return {"greeting": f"Hello, {state['name']}! Welcome to LangGraph."}


# ── Step 3: Build the graph ──────────────────────────────────────────

graph = StateGraph(State)

# Register the node
graph.add_node("greet", greet)

# Wire: START → greet → END
graph.add_edge(START, "greet")
graph.add_edge("greet", END)

# Compile turns the builder into a runnable
app = graph.compile()


# ── Step 4: Run it ───────────────────────────────────────────────────

if __name__ == "__main__":
    # Print the graph structure (Mermaid diagram you can paste into mermaid.live)
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    # Render the graph as a PNG and open it in the default image viewer
    import tempfile, os
    png_data = app.get_graph().draw_mermaid_png()
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.write(png_data)
    tmp.close()
    os.startfile(tmp.name)


    result = app.invoke({"name": "Shubham"})
    print("=== Result ===")
    print(result)
    # {'name': 'Shubham', 'greeting': 'Hello, Shubham! Welcome to LangGraph.'}

    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a new key `farewell: str` to State
    # 2. Add a second node `say_goodbye` that sets farewell
    # 3. Wire: START → greet → say_goodbye → END
    # 4. Run and verify both greeting and farewell are in the result
