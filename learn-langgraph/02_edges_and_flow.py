"""Lesson 02 — Edges & Flow
===========================
Concepts:
  - Sequential pipelines: node A -> node B -> node C
  - Each node sees the accumulated state from all prior nodes
  - State keys are merged (not replaced) -- you return only what changed

Graph:
  +-------+     +------------+     +-------------+     +-----------+     +-----+
  | START | --> | clean_text | --> | count_words | --> | summarize | --> | END |
  +-------+     +------------+     +-------------+     +-----------+     +-----+

  State accumulates through each node:
    clean_text  sets: cleaned
    count_words sets: word_count    (reads: cleaned)
    summarize   sets: summary       (reads: cleaned, word_count)

No LLM needed — simulates a 3-step data processing pipeline.

Run:  uv run python 02_edges_and_flow.py
"""

from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    raw_text: str
    cleaned: str
    word_count: int
    summary: str


def clean_text(state: State) -> dict:
    text = state["raw_text"].strip().lower()
    return {"cleaned": text}


def count_words(state: State) -> dict:
    count = len(state["cleaned"].split())
    return {"word_count": count}


def summarize(state: State) -> dict:
    return {
        "summary": f"Text has {state['word_count']} words. "
                   f"First 50 chars: '{state['cleaned'][:50]}...'"
    }


# Build the pipeline: clean → count → summarize
graph = StateGraph(State)
graph.add_node("clean_text", clean_text)
graph.add_node("count_words", count_words)
graph.add_node("summarize", summarize)

graph.add_edge(START, "clean_text")
graph.add_edge("clean_text", "count_words")
graph.add_edge("count_words", "summarize")
graph.add_edge("summarize", END)

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    result = app.invoke({
        "raw_text": "  Reuters reported that MARKETS surged on Monday "
                    "after the Federal Reserve signaled a pause in rate hikes.  "
    })

    print(f"Cleaned: {result['cleaned']}")
    print(f"Words:   {result['word_count']}")
    print(f"Summary: {result['summary']}")

    # ── Key takeaway ─────────────────────────────────────────────────
    # Each node only returns the keys it modifies.
    # LangGraph merges them into the full state automatically.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # Add a 4th node `classify` between summarize and END that sets a
    # new state key `category` to "short" or "long" based on word_count.
