"""Lesson 04 — State Reducers
==============================
Concepts:
  - Annotated[list, operator.add] -- a reducer that APPENDS instead of replaces
  - Without a reducer: returning {"key": value} replaces the old value
  - With operator.add: returning {"key": [item]} appends to the list
  - Useful for accumulating results from multiple nodes or parallel branches

Graph:
  +-------+     +-------+     +----------+     +--------+     +-----+
  | START | --> | greet | --> | decorate | --> | review | --> | END |
  +-------+     +-------+     +----------+     +--------+     +-----+

  State key `log: Annotated[list[str], operator.add]` accumulates across all nodes:
    greet    appends: ["Greeted 'Alice'"]
    decorate appends: ["Added decoration"]
    review   appends: ["Reviewed and approved"]

No LLM needed -- demonstrates accumulating log entries.

Run:  uv run python 04_state_reducers.py

Expected output:
  Final greeting: *** Hello, Alice! *** [APPROVED]

  Execution log:
    - Greeted 'Alice'
    - Added decoration
    - Reviewed and approved

Key takeaway:
  Without Annotated[list, operator.add], each node would REPLACE
  the log list. With the reducer, entries accumulate across nodes.

Exercise:
  1. Add a `farewell` node between review and END
  2. Have it return {"log": ["Said farewell"], "greeting": state["greeting"] + " Goodbye!"}
  3. Run the graph and observe the log growing to four entries
"""

import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    name: str
    # This is the key idea: Annotated with operator.add means
    # each node's return value gets APPENDED, not replaced.
    log: Annotated[list[str], operator.add]
    greeting: str


def greet(state: State) -> dict:
    return {"log": [f"Greeted '{state['name']}'"], "greeting": f"Hello, {state['name']}!"}


def decorate(state: State) -> dict:
    return {"log": ["Added decoration"], "greeting": f"*** {state['greeting']} ***"}


def review(state: State) -> dict:
    return {"log": ["Reviewed and approved"], "greeting": state["greeting"] + " [APPROVED]"}


graph = StateGraph(State)
graph.add_node("greet", greet)
graph.add_node("decorate", decorate)
graph.add_node("review", review)

graph.add_edge(START, "greet")
graph.add_edge("greet", "decorate")
graph.add_edge("decorate", "review")
graph.add_edge("review", END)

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    result = app.invoke({"name": "Alice"})

    print("Final greeting:", result["greeting"])
    print("\nExecution log:")
    for entry in result["log"]:
        print(f"  - {entry}")

    # Output:
    #   Final greeting: *** Hello, Alice! *** [APPROVED]
    #   Execution log:
    #     - Greeted 'Alice'
    #     - Added decoration
    #     - Reviewed and approved

    # ── Key takeaway ─────────────────────────────────────────────────
    # Without Annotated[list, operator.add], each node would REPLACE
    # the log list. With the reducer, entries accumulate across nodes.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a `farewell` node between review and END
    # 2. Have it return {"log": ["Said farewell"], "greeting": state["greeting"] + " Goodbye!"}
    # 3. Run the graph and observe the log growing to four entries
