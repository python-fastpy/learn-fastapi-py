"""Lesson 02 -- Edges and Flow
==============================

Lesson 01 had one node. Real work is a chain: greet, then decorate, then
summarise. `add_edge(A, B)` is what makes B run after A -- without edges,
nodes are islands and nothing runs at all.

  START ──► greet ──► decorate ──► summarize ──► END

  and the state grows as it goes, one key per node:

    {"name": "Shubham"}                         <- what you pass in
      │
      greet      reads name       sets greeting  = "Hello, Shubham!"
      │
      decorate   reads greeting   sets decorated = "*** Hello, Shubham! ***"
      │
      summarize  reads name       sets summary   = "Greeting for Shubham: 16 chars"
      │          + greeting
      ▼
    {"name", "greeting", "decorated", "summary"}   <- what comes out

  1. add_edge(A, B)   after A, ALWAYS run B. Unconditional (lesson 03 branches).
  2. ACCUMULATION     each node reads keys earlier nodes wrote.
  3. PARTIAL RETURN   each node returns only its own key.
  4. THE MERGE        LangGraph applies each partial return to the state, so
                      no node has to know the full schema.

  That last point is what makes nodes reorderable: you can insert or remove a
  step without touching the others, as long as the keys it reads already exist.
  Read a key nobody has written yet and you get a KeyError -- the order of your
  edges IS the contract.

Run:  uv run python 02_edges_and_flow.py

Maps to: langgraph_mcp_orchestrator.py -> analyze -> route -> execute ->
synthesize; story-drafting workflows -> resolve -> fetch -> generate -> refine
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    name: str
    greeting: str
    decorated: str
    summary: str


# -- The nodes. Each reads what it needs, returns only what it sets ----------

def greet(state: State) -> dict:
    return {"greeting": f"Hello, {state['name']}!"}


def decorate(state: State) -> dict:
    return {"decorated": f"*** {state['greeting']} ***"}          # reads greet's output


def summarize(state: State) -> dict:
    return {"summary": f"Greeting for {state['name']}: {len(state['greeting'])} chars"}


# -- The chain: one add_edge per arrow in the diagram ------------------------

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
    result = app.invoke({"name": "Shubham"})

    print("1. greeting :", result["greeting"])
    print("2. decorated:", result["decorated"])
    print("3. summary  :", result["summary"])
    print("\nOne invoke, three nodes, four keys. Each node wrote exactly one.")

# Exercises:
# 1. Add a `farewell` node between summarize and END that sets `farewell_msg`.
#    You add a key to State, a node, and re-point two edges -- that is all.
# 2. Swap the order of greet and decorate. The KeyError you get names the
#    contract you just broke.
# 3. Point both greet AND decorate at summarize. LangGraph runs what it can in
#    parallel -- lesson 04's reducers are what make that safe.
