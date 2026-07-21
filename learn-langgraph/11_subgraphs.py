"""Lesson 11 — Subgraphs
========================
Concepts:
  - Composing graphs: one graph can be a node in another
  - Subgraphs have their own state (can differ from parent)
  - Parent <-> subgraph communication via shared state keys
  - This maps to your skill workflows: each skill is like a subgraph

Graph (Parent):
  +-------+     +----------+     +----------+     +----------+     +-----+
  | START | --> | research | --> | drafting | --> | finalize | --> | END |
  +-------+     +----------+     +----------+     +----------+     +-----+
                (subgraph)       (subgraph)

  Research subgraph:          Drafting subgraph:
  +--------+     +---------+  +-------+     +------+
  | gather | --> | analyze |  | write | --> | edit |
  +--------+     +---------+  +-------+     +------+

No LLM needed -- demonstrates the composition pattern with pure logic.

Run:  uv run python 11_subgraphs.py
"""

import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END


# ── Subgraph 1: Research Pipeline ────────────────────────────────────

class ResearchState(TypedDict):
    topic: str
    findings: Annotated[list[str], operator.add]


def gather_sources(state: ResearchState) -> dict:
    return {"findings": [f"Source A says '{state['topic']}' is trending"]}


def analyze(state: ResearchState) -> dict:
    return {"findings": [f"Analysis: {len(state['findings'])} sources reviewed"]}


research_graph = StateGraph(ResearchState)
research_graph.add_node("gather", gather_sources)
research_graph.add_node("analyze", analyze)
research_graph.add_edge(START, "gather")
research_graph.add_edge("gather", "analyze")
research_graph.add_edge("analyze", END)

research_subgraph = research_graph.compile()


# ── Subgraph 2: Drafting Pipeline ────────────────────────────────────

class DraftState(TypedDict):
    findings: list[str]
    draft: str


def write_draft(state: DraftState) -> dict:
    summary = "; ".join(state["findings"])
    return {"draft": f"DRAFT: Based on research -- {summary}"}


def edit_draft(state: DraftState) -> dict:
    return {"draft": state["draft"] + " [EDITED]"}


draft_graph = StateGraph(DraftState)
draft_graph.add_node("write", write_draft)
draft_graph.add_node("edit", edit_draft)
draft_graph.add_edge(START, "write")
draft_graph.add_edge("write", "edit")
draft_graph.add_edge("edit", END)

draft_subgraph = draft_graph.compile()


# ── Parent graph: composes both subgraphs ────────────────────────────

class ParentState(TypedDict):
    topic: str
    findings: Annotated[list[str], operator.add]
    draft: str
    status: str


def finalize(state: ParentState) -> dict:
    return {"status": f"Published: {state['draft'][:80]}..."}


parent = StateGraph(ParentState)

# Add compiled subgraphs as nodes — they run as self-contained units
parent.add_node("research", research_subgraph)
parent.add_node("drafting", draft_subgraph)
parent.add_node("finalize", finalize)

parent.add_edge(START, "research")
parent.add_edge("research", "drafting")
parent.add_edge("drafting", "finalize")
parent.add_edge("finalize", END)

app = parent.compile()


if __name__ == "__main__":
    result = app.invoke({"topic": "AI in newsrooms"})

    print(f"Topic:    {result['topic']}")
    print(f"Findings: {result['findings']}")
    print(f"Draft:    {result['draft']}")
    print(f"Status:   {result['status']}")

    # NOTE: Findings may appear duplicated. This happens because both
    # the subgraph (ResearchState) and parent (ParentState) define
    # `findings` with operator.add. When the subgraph returns, LangGraph
    # merges its output into the parent using the parent's reducer too.
    # Fix: use a plain list (no reducer) in either the subgraph or parent.

    # Visualize the graph structure (Mermaid)
    print("\n=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())

    # ── Key takeaway ─────────────────────────────────────────────────
    # Subgraphs let you build complex systems from smaller, testable
    # units. Each subgraph:
    #   - Has its own state schema
    #   - Shares keys with the parent via matching key names
    #   - Can be tested independently
    #
    # In your architecture, each MCP skill is like a subgraph:
    #   - story-drafting, urgent-drafting, text-archive are independent
    #   - The backend orchestrator composes them like a parent graph
    #   - State flows via the MCP protocol instead of shared TypedDicts
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a third subgraph: "fact_check" between drafting and finalize
    # 2. Give it its own state with a `verified: bool` key
    # 3. In the parent, use conditional edges: if not verified -> loop
    #    back to drafting
