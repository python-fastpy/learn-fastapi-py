"""Lesson 04 -- State Reducers
==============================

Returning {"greeting": "..."} REPLACES the old value. That is right for a
greeting and wrong for a log: if three nodes each return {"log": [...]}, the
last one wins and the first two entries are gone. A REDUCER says how the old
and new values COMBINE instead of one replacing the other.

      Annotated[list[str], operator.add]
                  │             │
                  │             └── how to combine:  old + new
                  └── what the key holds

  WITHOUT a reducer                WITH operator.add
  ─────────────────                ─────────────────
  greet     log = ["a"]            greet     log = ["a"]
  decorate  log = ["b"]  ← lost a  decorate  log = ["a", "b"]
  review    log = ["c"]  ← lost b  review    log = ["a", "b", "c"]
            only "c" survives                all three survive

  1. NO REDUCER   a plain str / int / list key -> last write wins.
  2. REDUCER      Annotated[T, fn] -> LangGraph calls fn(old, new) per write.
  3. operator.add on lists is concatenation, so a write APPENDS.
  4. PER KEY      in the SAME state class, `log` accumulates while `greeting`
                  still replaces. You pick per key, not per graph.
  5. add_messages is this idea one step smarter: MessagesState uses it to
                  append messages and de-duplicate by id (lesson 05 onward).

  Rule of thumb: a list that several nodes contribute to needs a reducer; a
  value that one node owns at a time does not. This is also what makes
  parallel branches safe -- two nodes writing one key is a conflict unless a
  reducer says how to merge them.

Run:  uv run python 04_state_reducers.py

Maps to: MessagesState (add_messages); OrchestratorState.errors ->
Annotated[list[str], operator.add], so errors from several tool calls
accumulate instead of overwriting each other
"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    name: str
    log: Annotated[list[str], operator.add]    # reducer: append
    greeting: str                              # no reducer: replace


# These three are annotated `dict`, not `State`, because both graphs below
# share them. LangGraph reads a node's type hint to register its channels, so
# a `State` hint would clash with NoReducerState's plain `log`. The hint is
# not decoration -- it is schema.

def greet(state: dict) -> dict:
    return {"log": [f"greeted {state['name']}"], "greeting": f"Hello, {state['name']}!"}


def decorate(state: dict) -> dict:
    return {"log": ["added decoration"], "greeting": f"*** {state['greeting']} ***"}


def review(state: dict) -> dict:
    return {"log": ["reviewed"], "greeting": state["greeting"] + " [APPROVED]"}


def build(state_class) -> object:
    """Same three nodes, same edges -- only the state class differs."""
    g = StateGraph(state_class)
    g.add_node("greet", greet)
    g.add_node("decorate", decorate)
    g.add_node("review", review)
    g.add_edge(START, "greet")
    g.add_edge("greet", "decorate")
    g.add_edge("decorate", "review")
    g.add_edge("review", END)
    return g.compile()


# The same state, with the reducer taken off `log`. Nothing else changes.
class NoReducerState(TypedDict):
    name: str
    log: list[str]
    greeting: str


if __name__ == "__main__":
    start = {"name": "Shubham", "log": [], "greeting": ""}

    with_reducer = build(State).invoke(start)
    without = build(NoReducerState).invoke(start)

    print("1. with Annotated[list, operator.add]:")
    for entry in with_reducer["log"]:
        print(f"     - {entry}")

    print("\n2. same nodes, reducer removed:")
    for entry in without["log"]:
        print(f"     - {entry}")
    print(f"     ({len(with_reducer['log'])} entries vs {len(without['log'])} "
          f"-- the first two writes were overwritten, not merged)")

    print("\n3. `greeting` has no reducer in EITHER, and that is correct:")
    print("     ", with_reducer["greeting"])
    print("      each node deliberately replaced it, building on the last value.")

# Exercises:
# 1. Add a `farewell` node that appends to log and extends greeting. The log
#    grows to four; you changed no other node.
# 2. Put a reducer on `greeting` too and run again. The greetings concatenate
#    into nonsense -- a reducer is not a default, it is a decision.
# 3. Swap operator.add for a lambda that keeps only the last two entries:
#    Annotated[list[str], lambda old, new: (old + new)[-2:]]. Any callable
#    taking (old, new) is a valid reducer.
# 4. Point greet and decorate both at review (parallel). With the reducer it
#    merges; on a plain key LangGraph raises an update conflict instead.
