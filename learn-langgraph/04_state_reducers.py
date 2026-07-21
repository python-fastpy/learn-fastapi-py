"""Lesson 04 — State Reducers
==============================
Concepts:
  - Annotated[list, operator.add] -- a reducer that APPENDS instead of replaces
  - Without a reducer: returning {"key": value} replaces the old value
  - With operator.add: returning {"key": [item]} appends to the list
  - Useful for accumulating results from multiple nodes or parallel branches

Graph:
  +-------+     +----------+     +-------+     +--------+     +-----+
  | START | --> | research | --> | draft | --> | review | --> | END |
  +-------+     +----------+     +-------+     +--------+     +-----+

  State key `log: Annotated[list[str], operator.add]` accumulates across all nodes:
    research appends: ["Researched 'topic'"]
    draft    appends: ["Drafted initial version"]
    review   appends: ["Reviewed and approved"]

No LLM needed -- demonstrates accumulating log entries.

Run:  uv run python 04_state_reducers.py
"""

import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    topic: str
    # This is the key idea: Annotated with operator.add means
    # each node's return value gets APPENDED, not replaced.
    log: Annotated[list[str], operator.add]
    result: str


def research(state: State) -> dict:
    return {
        "log": [f"Researched '{state['topic']}'"],
    }


def draft(state: State) -> dict:
    return {
        "log": ["Drafted initial version"],
        "result": f"Draft about {state['topic']}",
    }


def review(state: State) -> dict:
    return {
        "log": ["Reviewed and approved"],
        "result": state["result"] + " [REVIEWED]",
    }


graph = StateGraph(State)
graph.add_node("research", research)
graph.add_node("draft", draft)
graph.add_node("review", review)

graph.add_edge(START, "research")
graph.add_edge("research", "draft")
graph.add_edge("draft", "review")
graph.add_edge("review", END)

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    result = app.invoke({"topic": "Reuters Q3 Earnings"})

    print("Final result:", result["result"])
    print("\nExecution log:")
    for entry in result["log"]:
        print(f"  - {entry}")

    # Output:
    #   Final result: Draft about Reuters Q3 Earnings [REVIEWED]
    #   Execution log:
    #     - Researched 'Reuters Q3 Earnings'
    #     - Drafted initial version
    #     - Reviewed and approved

    # ── Key takeaway ─────────────────────────────────────────────────
    # Without Annotated[list, operator.add], each node would REPLACE
    # the log list. With the reducer, entries accumulate across nodes.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a `revisions: Annotated[list[str], operator.add]` key
    # 2. Make the review node sometimes return a revision request
    # 3. Use conditional edges to loop back to draft if revision needed
    # 4. Verify that revisions accumulate across loop iterations
