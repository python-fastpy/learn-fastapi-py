"""Lesson 10 — Streaming
========================
Concepts:
  - app.stream(): get results as each node completes
  - stream_mode="values": stream the full state after each step
  - stream_mode="updates": stream only the changes from each node
  - stream_mode="messages": stream LLM tokens as they arrive
  - Your backend uses SSE streaming to send responses to the frontend

Graph:
  +-------+     +----------+     +-------+     +-----+
  | START | --> | research | --> | draft | --> | END |
  +-------+     +----------+     +-------+     +-----+

  Streaming modes control WHAT you see as the graph runs:
    "updates"  -> which node produced what change
    "values"   -> full state snapshot after each node
    "messages" -> token-by-token LLM output (live UI)

** Requires .env with orchestrator credentials **

Run:  uv run python 10_streaming.py
"""

from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from llm_helper import get_llm

llm = get_llm(model="gpt-4o")


def research(state: MessagesState) -> dict:
    response = llm.invoke(state["messages"] + [
        HumanMessage(content="List 3 key facts about this topic. Be brief.")
    ])
    return {"messages": [response]}


def draft(state: MessagesState) -> dict:
    response = llm.invoke(state["messages"] + [
        HumanMessage(content="Now write a 2-sentence news summary using those facts.")
    ])
    return {"messages": [response]}


graph = StateGraph(MessagesState)
graph.add_node("research", research)
graph.add_node("draft", draft)
graph.add_edge(START, "research")
graph.add_edge("research", "draft")
graph.add_edge("draft", END)

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    initial = {
        "messages": [
            SystemMessage(content="You are a Reuters journalist. Be concise."),
            HumanMessage(content="Topic: renewable energy investment in 2024"),
        ]
    }

    # ── Mode 1: stream_mode="updates" ────────────────────────────────
    # Shows WHICH node produced WHAT change — great for progress tracking
    print("=== Stream Mode: updates ===\n")
    for chunk in app.stream(initial, stream_mode="updates"):
        for node_name, update in chunk.items():
            msg = update["messages"][-1]
            print(f"[{node_name}] {msg.content[:100]}...")
            print()

    # ── Mode 2: stream_mode="values" ─────────────────────────────────
    # Shows the complete state after each node — good for debugging
    print("\n=== Stream Mode: values ===\n")
    for state_snapshot in app.stream(initial, stream_mode="values"):
        n = len(state_snapshot["messages"])
        last = state_snapshot["messages"][-1]
        role = last.__class__.__name__.replace("Message", "")
        print(f"[State has {n} messages] Latest: [{role}] {last.content[:80]}...")
        print()

    # ── Mode 3: Token-by-token streaming ─────────────────────────────
    # For real-time typing effect (what your frontend SSE does)
    print("\n=== Token-by-Token (messages mode) ===\n")
    for msg, metadata in app.stream(initial, stream_mode="messages"):
        if hasattr(msg, "content") and msg.content:
            print(msg.content, end="", flush=True)
    print("\n")

    # ── Key takeaway ─────────────────────────────────────────────────
    # - "updates" → see which node did what (progress tracking)
    # - "values"  → see full state after each step (debugging)
    # - "messages"→ token-by-token LLM output (live UI)
    #
    # Your backend's chat.py uses SSE streaming, which maps to the
    # "messages" mode — tokens flow to the frontend as they arrive.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a third node "edit" after draft
    # 2. Stream with mode="updates" and observe all three steps
    # 3. Try streaming with a checkpointer + thread_id
