"""Lesson 11 -- Subgraphs
=========================

A compiled graph is a runnable, and `add_node` takes a runnable. So a whole
graph can be one node inside a bigger graph. That is a subgraph: a unit you
can test alone and reuse, instead of one flat graph of twenty nodes.

  parent graph                        each box is itself a graph:
  ┌──────────────────────────┐
  │ START                    │        greeting subgraph
  │   │                      │        ┌─────────────────────────┐
  │   ▼                      │        │ START ► compose ►       │
  │ greeting ────────────────┼───────►│         decorate ► END  │
  │   │                      │        └─────────────────────────┘
  │   ▼                      │        farewell subgraph
  │ farewell_pipeline ───────┼───────►┌─────────────────────────┐
  │   │                      │        │ START ► write ►         │
  │   ▼                      │        │         format ► END    │
  │ finalize ► END           │        └─────────────────────────┘
  └──────────────────────────┘

  1. COMPILE THEN NEST   parent.add_node("greeting", greeting_subgraph) --
                         a compiled graph goes wherever a function would.
  2. OWN STATE           each subgraph has its own schema and nodes, and
                         knows nothing about its parent.
  3. THE BORDER          only keys that share a NAME cross it. A key the
                         subgraph never declares is passed over untouched;
                         a key it does declare is handed in AND echoed back
                         in its output.
  4. THE TRAP            that echo is the thing that bites. If the parent has
                         an APPENDING reducer on a key, and the subgraph
                         merely declares that key without owning it, the echo
                         gets appended a second time and the list doubles.
                         The subgraph does not need a reducer of its own for
                         this to happen -- declaring the key is enough.
  5. THE FIX             a subgraph declares only the keys it actually reads
                         or writes. `clean_farewell` below omits `steps` and
                         the parent's list stays correct; `leaky_farewell`
                         declares it, touches it, and doubles it.
  6. TEST IN ISOLATION   greeting_subgraph.invoke({...}) runs on its own.
                         That is the real payoff.

  Subgraphs and MCP skills solve the same problem -- break a system into
  units -- by opposite means. A subgraph runs in-process and shares state; an
  MCP skill is a separate service taking parameters and returning JSON
  (lesson 14). Production uses the latter, which has no border to leak across.

Run:  uv run python 11_subgraphs.py      (no LLM needed)

Maps to: skill composition -- each skill is a unit the orchestrator calls,
though over MCP rather than as a nested graph
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


# -- Subgraph 1: greeting. It owns `steps`, so declaring it is correct -----

class GreetingState(TypedDict):
    name: str
    steps: Annotated[list[str], operator.add]


def compose(state: GreetingState) -> dict:
    return {"steps": [f"composed a greeting for {state['name']}"]}


def decorate(state: GreetingState) -> dict:
    return {"steps": ["decorated it"]}


_g = StateGraph(GreetingState)
_g.add_node("compose", compose)
_g.add_node("decorate", decorate)
_g.add_edge(START, "compose")
_g.add_edge("compose", "decorate")
_g.add_edge("decorate", END)
greeting_subgraph = _g.compile()


# -- Subgraph 2, two versions of the same work ----------------------------
# clean: declares only what it owns.     leaky: also declares `steps`.

class CleanFarewell(TypedDict):
    farewell: str


class LeakyFarewell(TypedDict):
    steps: list[str]                 # declared but not owned -> echoed back
    farewell: str


def write_farewell(state: dict) -> dict:
    return {"farewell": "Goodbye, and thanks for visiting!"}


def format_farewell(state: dict) -> dict:
    return {"farewell": state["farewell"] + " [FORMATTED]"}


def farewell_subgraph(state_class):
    f = StateGraph(state_class)
    f.add_node("write", write_farewell)
    f.add_node("format", format_farewell)
    f.add_edge(START, "write")
    f.add_edge("write", "format")
    f.add_edge("format", END)
    return f.compile()


# -- The parent ------------------------------------------------------------

class ParentState(TypedDict):
    name: str
    steps: Annotated[list[str], operator.add]      # appending reducer
    farewell: str
    status: str


def finalize(state: ParentState) -> dict:
    return {"status": f"done after {len(state['steps'])} recorded steps"}


def build_parent(farewell_state_class):
    p = StateGraph(ParentState)
    p.add_node("greeting", greeting_subgraph)          # 1. a graph as a node
    p.add_node("farewell_pipeline", farewell_subgraph(farewell_state_class))
    p.add_node("finalize", finalize)
    p.add_edge(START, "greeting")
    p.add_edge("greeting", "farewell_pipeline")
    p.add_edge("farewell_pipeline", "finalize")
    p.add_edge("finalize", END)
    return p.compile()


if __name__ == "__main__":
    start = {"name": "Shubham", "steps": [], "farewell": "", "status": ""}

    # 6. The subgraph stands alone.
    alone = greeting_subgraph.invoke({"name": "Shubham", "steps": []})
    print(f"1. greeting subgraph alone : {len(alone['steps'])} steps  {alone['steps']}")

    clean = build_parent(CleanFarewell).invoke(dict(start))
    print(f"\n2. parent, clean farewell  : {len(clean['steps'])} steps  <- correct")
    print(f"   {clean['farewell']}")

    leaky = build_parent(LeakyFarewell).invoke(dict(start))
    print(f"\n3. parent, leaky farewell  : {len(leaky['steps'])} steps  <- doubled")
    print(f"   {leaky['steps']}")

    print("\nThe only difference is that LeakyFarewell declares `steps`. It never")
    print("writes the key -- the echo alone is enough for the parent's reducer")
    print("to append it twice (point 4).")
    print(f"\n4. finalize saw            : {clean['status']}")

# Exercises:
# 1. Add a reducer to LeakyFarewell's `steps` as well. Still 4 -- the
#    subgraph's own reducer was never the cause.
# 2. Give the greeting subgraph a key the parent does not declare (say
#    `draft: str`). It vanishes on merge: the border works both ways.
# 3. Rename the parent key to `parent_steps`. The leak stops, because the
#    names no longer match -- distinct names are the other fix.
# 4. Print app.get_graph().draw_mermaid() -- subgraphs appear as one node.
#    Then try draw_mermaid(xray=1) to see inside them.
