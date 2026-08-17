"""Lesson 11 — Subgraphs
========================

WHY THIS MATTERS:
  Real systems are too complex for a single flat graph. The production assistant
  has greeting workflows, farewell workflows, translation workflows — each is a
  self-contained unit. Subgraphs let you build complex systems from smaller,
  testable pieces. Each subgraph has its own state schema and can be developed
  and tested independently, then composed into a parent graph.

  This is how the production skill system works: each MCP skill (story-drafting,
  urgent-drafting, text-archive) is like a subgraph — a self-contained workflow
  that the orchestrator calls as a node.

WHAT YOU'LL LEARN:
  1. Composing graphs: one compiled graph can be a node in another
  2. Subgraph state: each subgraph has its OWN state schema
  3. Parent <-> subgraph communication via shared state key names
  4. Reducer gotcha: matching key names with different reducers cause duplication
  5. How this maps to the skill architecture (each skill = a subgraph)

Concepts:
  - subgraph = StateGraph(SubState).compile()
        A standalone compiled graph, ready to be embedded as a node.
  - parent.add_node("name", subgraph)
        Adds the compiled subgraph as a node in the parent graph.
  - Shared keys: parent and subgraph communicate via keys with the SAME name.
        When a subgraph finishes, LangGraph merges its output state back into
        the parent state using the parent's reducer for each key.
  - Reducer warning: if both parent AND subgraph define the same key with
        operator.add, values get doubled — the subgraph appends internally,
        then the parent appends the subgraph's output again.
  - Fix: use a plain list (no reducer) in either the subgraph or parent to
        prevent double-appending.

Graph (Parent):
  +-------+     +----------+     +-------------------+     +----------+     +-----+
  | START | --> | greeting | --> | farewell_pipeline | --> | finalize | --> | END |
  +-------+     +----------+     +-------------------+     +----------+     +-----+
                (subgraph)       (subgraph)

  Greeting subgraph:              Farewell subgraph:
  +---------+     +----------+    +----------------+     +-----------------+
  | compose | --> | decorate |    | write_farewell | --> | format_farewell |
  +---------+     +----------+    +----------------+     +-----------------+

Graph trace (what happens when you invoke with {"name": "Alice"}):
  Parent invoke({"name": "Alice"})
    -> greeting subgraph runs:
        compose:  steps = ["Composed greeting for 'Alice'"]
        decorate: steps = ["Composed...", "Decorated greeting"]
    -> farewell_pipeline subgraph runs:
        write_farewell:  farewell = "Goodbye! Based on 2 steps so far."
        format_farewell: farewell = "Goodbye! Based on 2 steps so far. [FORMATTED]"
    -> finalize: status = "Complete: Goodbye! Based on 2 steps so far. [FORMATTED]..."

Maps to production:
  MCP skills                    -> each skill is a self-contained subgraph
  mcp_server_registry.py        -> discovers and registers skill subgraphs
  langgraph_mcp_orchestrator.py -> parent graph that calls skill subgraphs
  story-drafting workflows      -> multi-step workflows within a skill

PREREQUISITES: Lesson 04 (state reducers — understanding shared state keys)

EXPECTED OUTPUT:
  Name:     Alice
  Steps:    ['Composed greeting for 'Alice'', 'Decorated greeting', ...]
  Farewell: Goodbye! Based on ... steps so far. [FORMATTED]
  Status:   Complete: Goodbye! Based on ... steps so far. [FORMATTED]...

  === Graph Diagram (Mermaid) ===
  (mermaid graph text)

No LLM needed -- demonstrates the composition pattern with pure logic.

Run:  uv run python 11_subgraphs.py
"""

import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END


# ── Step 1: Subgraph 1 — Greeting Pipeline (compose -> decorate) ────────────
# This subgraph is a self-contained unit: it has its own state schema
# (GreetingState), its own nodes, and its own edges.  It knows nothing about
# the parent graph.  In production, each MCP skill is structured the same way —
# a standalone workflow that can be tested independently.

class GreetingState(TypedDict):
    name: str
    # IMPORTANT: uses operator.add reducer — same as the parent's `steps` key.
    # This causes the "reducer gotcha" explained in the docstring: values
    # appended here get appended AGAIN when merged into the parent.
    steps: Annotated[list[str], operator.add]


def compose(state: GreetingState) -> dict:
    """First node in the greeting pipeline: compose a raw greeting."""
    return {"steps": [f"Composed greeting for '{state['name']}'"]}


def decorate(state: GreetingState) -> dict:
    """Second node: decorate the greeting (add formatting, emoji, etc.)."""
    return {"steps": ["Decorated greeting"]}


# Build and compile the greeting subgraph — compile() makes it a standalone
# runnable that can be invoked directly OR embedded as a node in a parent graph.
greeting_graph = StateGraph(GreetingState)
greeting_graph.add_node("compose", compose)
greeting_graph.add_node("decorate", decorate)
greeting_graph.add_edge(START, "compose")
greeting_graph.add_edge("compose", "decorate")
greeting_graph.add_edge("decorate", END)

greeting_subgraph = greeting_graph.compile()


# ── Step 2: Subgraph 2 — Farewell Pipeline (write_farewell -> format_farewell)
# Compare with GreetingState above: FarewellState uses a PLAIN list[str] for
# `steps` (no operator.add reducer).  This is intentional — it avoids the
# reducer gotcha.  When this subgraph's output merges into the parent, the
# parent's operator.add reducer handles appending, so values are not doubled.

class FarewellState(TypedDict):
    # Plain list[str] — NO reducer.  This is the fix for the reducer gotcha.
    # The parent's operator.add on `steps` will handle merging correctly.
    steps: list[str]
    farewell: str


def write_farewell(state: FarewellState) -> dict:
    """Compose a farewell message based on how many steps have run so far."""
    return {"farewell": f"Goodbye! Based on {len(state['steps'])} steps so far."}


def format_farewell(state: FarewellState) -> dict:
    """Add formatting to the farewell (e.g., rich text, branding)."""
    return {"farewell": state["farewell"] + " [FORMATTED]"}


# Build and compile the farewell subgraph — same pattern as greeting.
farewell_graph = StateGraph(FarewellState)
farewell_graph.add_node("write_farewell", write_farewell)
farewell_graph.add_node("format_farewell", format_farewell)
farewell_graph.add_edge(START, "write_farewell")
farewell_graph.add_edge("write_farewell", "format_farewell")
farewell_graph.add_edge("format_farewell", END)

farewell_subgraph = farewell_graph.compile()


# ── Step 3: Parent Graph — composes both subgraphs as nodes ─────────────────
# The parent graph is the orchestrator.  In production, the
# langgraph_mcp_orchestrator.py plays this role: it discovers skill subgraphs
# via the MCP server registry and calls them as nodes in its own graph.

class ParentState(TypedDict):
    name: str
    # operator.add reducer — same key name as GreetingState.steps.
    # This is where the reducer gotcha bites: both parent and greeting
    # subgraph use operator.add, so greeting results get double-appended.
    steps: Annotated[list[str], operator.add]
    farewell: str
    status: str


def finalize(state: ParentState) -> dict:
    """Final node: summarize the workflow result into a status string."""
    return {"status": f"Complete: {state['farewell'][:60]}..."}


parent = StateGraph(ParentState)

# Add compiled subgraphs as nodes — they run as self-contained units.
# parent.add_node() accepts a compiled graph just like a regular function.
# LangGraph handles state mapping: keys with matching names are passed through.
parent.add_node("greeting", greeting_subgraph)
parent.add_node("farewell_pipeline", farewell_subgraph)
parent.add_node("finalize", finalize)

# Wire the parent graph: greeting -> farewell_pipeline -> finalize
parent.add_edge(START, "greeting")
parent.add_edge("greeting", "farewell_pipeline")
parent.add_edge("farewell_pipeline", "finalize")
parent.add_edge("finalize", END)

app = parent.compile()


if __name__ == "__main__":
    result = app.invoke({"name": "Alice"})

    print(f"Name:     {result['name']}")
    print(f"Steps:    {result['steps']}")
    print(f"Farewell: {result['farewell']}")
    print(f"Status:   {result['status']}")

    # NOTE on the reducer gotcha:
    # Steps may appear duplicated in the output.  This happens because both
    # GreetingState and ParentState define `steps` with operator.add.
    # Here's the sequence:
    #   1. greeting subgraph runs compose + decorate internally
    #      -> subgraph's steps = ["Composed...", "Decorated greeting"]
    #        (operator.add appended each one inside the subgraph)
    #   2. LangGraph merges subgraph output into parent state
    #      -> parent's operator.add appends the ENTIRE list again
    #      -> parent steps = original + ["Composed...", "Decorated greeting"]
    #
    # Fix: use a plain list (no reducer) in either the subgraph or parent.
    # FarewellState intentionally uses plain list[str] to demonstrate the fix.

    # Visualize the graph structure (Mermaid)
    print("\n=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())

    # ── Key takeaway ─────────────────────────────────────────────────────
    # Subgraphs are independent, testable units — the building blocks of
    # complex LangGraph applications.  Each subgraph:
    #   - Has its OWN state schema (GreetingState, FarewellState)
    #   - Communicates with the parent via SHARED KEY NAMES (not references)
    #   - Can be compiled and tested independently before composition
    #   - Runs as a black box inside the parent graph
    #
    # The REDUCER GOTCHA is the most common subgraph bug:
    #   GreetingState.steps  = Annotated[list[str], operator.add]  (HAS reducer)
    #   ParentState.steps    = Annotated[list[str], operator.add]  (HAS reducer)
    #   -> BOTH apply operator.add -> values get doubled on merge
    #
    #   FarewellState.steps  = list[str]                           (NO reducer)
    #   ParentState.steps    = Annotated[list[str], operator.add]  (HAS reducer)
    #   -> ONLY parent applies operator.add -> values merge correctly
    #
    # Production mapping:
    #   Each MCP skill (story-drafting, urgent-drafting, text-archive) is
    #   essentially a subgraph with its own state.  The orchestrator
    #   (langgraph_mcp_orchestrator.py) is the parent graph that discovers
    #   skills via mcp_server_registry.py and calls them as nodes.  Each
    #   skill can be deployed, versioned, and tested independently — just
    #   like these subgraphs.
    #
    # ── Exercise ─────────────────────────────────────────────────────────
    # 1. Add a third subgraph: "personalize" between greeting and farewell
    # 2. Give it its own state with a `tone: str` key (e.g., "formal")
    # 3. In the parent, use conditional edges: if tone == "formal" -> skip
    #    farewell and go directly to finalize
