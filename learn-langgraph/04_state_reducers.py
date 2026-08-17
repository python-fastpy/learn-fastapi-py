"""Lesson 04 — State Reducers
==============================

WHY THIS MATTERS
----------------
In lessons 02-03, returning {"key": value} REPLACES the old value. But what if
multiple nodes need to ADD to a list -- like an execution log, error list, or
message history? Without a reducer, the last node wins and earlier entries are
lost. Reducers fix this by defining HOW values combine instead of just replacing.

This is how MessagesState works (lesson 05+): messages use the add_messages
reducer to accumulate. The backend's error tracking and the orchestrator's tool
results use the same pattern.

WHAT YOU'LL LEARN
-----------------
1. Annotated[list, operator.add]: a reducer that APPENDS instead of replaces
2. Without a reducer: last write wins (data loss)
3. With operator.add: entries accumulate across all nodes
4. How this powers MessagesState (the reducer behind message history)
5. How production tracks errors and logs across nodes

Concepts
--------
- Annotated[list[str], operator.add] -- tells LangGraph to APPEND, not replace
- Without reducer: node B returns {"log": ["B"]} -> replaces node A's ["A"]
- With reducer: node B returns {"log": ["B"]} -> result is ["A", "B"]
- MessagesState uses add_messages reducer (smarter version of operator.add)
- Only list keys need reducers -- string/int keys replace as expected

Graph
-----
  +-------+     +-------+     +----------+     +--------+     +-----+
  | START | --> | greet | --> | decorate | --> | review | --> | END |
  +-------+     +-------+     +----------+     +--------+     +-----+

  Execution trace (input: {"name": "Alice"}):
    greet:    returns {"log": ["Greeted 'Alice'"]}      -> log = ["Greeted 'Alice'"]
    decorate: returns {"log": ["Added decoration"]}     -> log = ["Greeted 'Alice'", "Added decoration"]
    review:   returns {"log": ["Reviewed and approved"]} -> log = ["Greeted 'Alice'", "Added decoration", "Reviewed and approved"]

  Notice: each node APPENDS its entry. Without the reducer, only the last
  node's entry would survive.

Maps to
-------
  MessagesState              -> uses add_messages reducer (lesson 05+)
  OrchestratorState          -> errors: Annotated[list[str], operator.add]
  langgraph_mcp_orchestrator -> accumulates tool results and errors across execution nodes

PREREQUISITES: Lesson 02 (edges -- understanding state flow)

No LLM needed -- demonstrates accumulating log entries.

Run:  uv run python 04_state_reducers.py

EXPECTED OUTPUT
---------------
  Final greeting: *** Hello, Alice! *** [APPROVED]

  Execution log:
    - Greeted 'Alice'
    - Added decoration
    - Reviewed and approved
"""

import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END


# -- Step 1: Define state with a reducer on the `log` key --------------------
# The key idea: Annotated[list[str], operator.add] tells LangGraph to APPEND
# new entries to the list instead of replacing it. Without this annotation,
# returning {"log": ["B"]} would overwrite ["A"] entirely.
#
# `greeting` has NO reducer -- it's a plain str, so normal "last write wins"
# behavior applies (which is what we want for greeting text).
class State(TypedDict):
    name: str
    log: Annotated[list[str], operator.add]   # reducer: APPEND, don't replace
    greeting: str                              # no reducer: last write wins


# -- Step 2: Each node appends to the log (not replaces) ---------------------
# Because `log` has the operator.add reducer, returning {"log": ["entry"]}
# APPENDS "entry" to the existing list. Each node also updates `greeting`
# (which has no reducer, so the new value replaces the old one as expected).

def greet(state: State) -> dict:
    # log: ["Greeted 'Alice'"] is APPENDED to the (initially empty) log list
    return {"log": [f"Greeted '{state['name']}'"], "greeting": f"Hello, {state['name']}!"}


def decorate(state: State) -> dict:
    # log: ["Added decoration"] is APPENDED -- log is now 2 entries
    return {"log": ["Added decoration"], "greeting": f"*** {state['greeting']} ***"}


def review(state: State) -> dict:
    # log: ["Reviewed and approved"] is APPENDED -- log is now 3 entries
    return {"log": ["Reviewed and approved"], "greeting": state["greeting"] + " [APPROVED]"}


# -- Step 3: Build the pipeline and run it ------------------------------------
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
    # the log list -- only the last node's entry would survive.
    # With the reducer, entries ACCUMULATE across all nodes.
    #
    # This is the same mechanism behind MessagesState's message history
    # -- the most important state pattern in LangGraph. In lesson 05+,
    # you'll see MessagesState use the add_messages reducer, which is
    # a smarter version of operator.add that handles message deduplication
    # and updates.
    #
    # In production, the orchestrator's OrchestratorState uses
    # Annotated[list[str], operator.add] for error tracking, so errors
    # from multiple tool executions accumulate instead of overwriting
    # each other. The same pattern applies to tool results.
    #
    # Rule of thumb:
    #   - List keys that should accumulate -> use a reducer
    #   - String/int/bool keys that should update -> no reducer needed
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a `farewell` node between review and END
    # 2. Have it return {"log": ["Said farewell"], "greeting": state["greeting"] + " Goodbye!"}
    # 3. Run the graph and observe the log growing to four entries
