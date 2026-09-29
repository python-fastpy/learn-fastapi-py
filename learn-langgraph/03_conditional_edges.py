"""Lesson 03 -- Conditional Edges
=================================

Lesson 02's chain always ran the same path. Branching needs a ROUTING
FUNCTION: it reads the state and returns the NAME of the node to run next.
The graph decides at runtime, so the if/else lives in one place instead of
being scattered through the nodes.

  START
    │
    ▼
  classify
    │   route_by_style(state) -> "formal" | "casual" | "warm"      <- STAGE 1
    ├────────────────┬─────────────────┐
    ▼                ▼                 ▼
  formal_greet   casual_greet      warm_greet
    │                │                 │
    │   route_after_greet(state) -> "review" | "send"              <- STAGE 2
    ├────────────────┴─────────────────┤
    ▼                                  ▼
  review                             send
    │                                  │
    └────────────────┬─────────────────┘
                     ▼
                    END

  1. ROUTING FN   returns a STRING -- the name of the next node, never data.
  2. Literal[...] as the return type, so a typo is a type error not a 3am page.
  3. IMPLICIT MAP add_conditional_edges("classify", fn) -- what fn returns must
                  BE a node name.
  4. EXPLICIT MAP add_conditional_edges("classify", fn, {...}) -- a dict from
                  what fn returns to the node to run. Use it when the two
                  differ, or to make the branches readable at a glance.
  5. MULTI-WAY    two branches or ten, it is the same call.
  6. TWO STAGES   branches can converge and then route AGAIN. Formal greetings
                  go to review; the friendlier ones skip it.

  The routing function must return a registered node name (or END). Return
  anything else and you get a runtime error naming the value -- which is
  exactly why 2 and 4 are worth the extra typing.

Run:  uv run python 03_conditional_edges.py

Maps to: langgraph_mcp_orchestrator.py -> route_after_analysis() picking an
execution strategy; fast_path_matcher.py -> the regex shortcut before it
"""

from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    name: str
    style: str          # "formal" | "casual" | "warm" -- drives stage 1
    greeting: str
    status: str


def classify(state: State) -> dict:
    return {"status": f"style={state['style']}"}


def formal_greet(state: State) -> dict:
    return {"greeting": f"Dear {state['name']}, it is a pleasure to meet you."}


def casual_greet(state: State) -> dict:
    return {"greeting": f"Hey {state['name']}! What's up?"}


def warm_greet(state: State) -> dict:
    return {"greeting": f"So lovely to see you, {state['name']}!"}


def review(state: State) -> dict:
    return {"status": "reviewed before sending"}


def send(state: State) -> dict:
    return {"status": "sent straight away"}


# -- STAGE 1: pick a greeting style -----------------------------------------
# Returns a short label, NOT a node name -- the explicit map below translates.

def route_by_style(state: State) -> Literal["formal", "casual", "warm"]:
    if state["style"] == "formal":
        return "formal"
    return "casual" if state["style"] == "casual" else "warm"


# -- STAGE 2: does this greeting need a human first? ------------------------
# Returns the node name itself, so no map is needed.

def route_after_greet(state: State) -> Literal["review", "send"]:
    return "review" if state["greeting"].startswith("Dear") else "send"


graph = StateGraph(State)
for name, fn in [("classify", classify), ("formal_greet", formal_greet),
                 ("casual_greet", casual_greet), ("warm_greet", warm_greet),
                 ("review", review), ("send", send)]:
    graph.add_node(name, fn)

graph.add_edge(START, "classify")

# 4 + 5. EXPLICIT map: label -> node. Three branches from one call.
graph.add_conditional_edges("classify", route_by_style, {
    "formal": "formal_greet",
    "casual": "casual_greet",
    "warm": "warm_greet",
})

# 3 + 6. IMPLICIT map, applied to every branch: they converge, then split again.
for branch in ("formal_greet", "casual_greet", "warm_greet"):
    graph.add_conditional_edges(branch, route_after_greet)

graph.add_edge("review", END)
graph.add_edge("send", END)

app = graph.compile()


if __name__ == "__main__":
    for style in ("formal", "casual", "warm"):
        r = app.invoke({"name": "Shubham", "style": style, "greeting": "", "status": ""})
        print(f"{style:<7} -> {r['greeting']}")
        print(f"{'':<7}    {r['status']}")

    print("\nOne graph, three paths in, two paths out. No node contains an if.")

# Exercises:
# 1. Add a "brief" style and a brief_greet node -- one label in the dict, one
#    entry in the Literal, one node. No existing node changes.
# 2. Make route_by_style return "formal_greet" directly and drop the dict.
#    Same behaviour; which version would you rather debug in six months?
# 3. Return "frmal" from route_by_style (a typo) and read the error.
# 4. Route warm_greet to review as well, by giving route_after_greet a second
#    condition -- a branch can rejoin either path.
