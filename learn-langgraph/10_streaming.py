"""Lesson 10 — Streaming
========================
Concepts:
  - app.stream(): get results as each node completes
  - stream_mode="values": stream the full state after each step
  - stream_mode="updates": stream only the changes from each node
  - stream_mode="messages": stream LLM tokens as they arrive

Graph:
  +-------+     +---------+     +-----------+     +-----+
  | START | --> | compose | --> | translate | --> | END |
  +-------+     +---------+     +-----------+     +-----+

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


def compose(state: MessagesState) -> dict:
    response = llm.invoke(state["messages"] + [
        HumanMessage(content="Write a warm greeting for this person. Be creative.")
    ])
    return {"messages": [response]}


def translate(state: MessagesState) -> dict:
    response = llm.invoke(state["messages"] + [
        HumanMessage(content="Now translate that greeting into French.")
    ])
    return {"messages": [response]}


graph = StateGraph(MessagesState)
graph.add_node("compose", compose)
graph.add_node("translate", translate)
graph.add_edge(START, "compose")
graph.add_edge("compose", "translate")
graph.add_edge("translate", END)

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    initial = {
        "messages": [
            SystemMessage(content="You are a greeting assistant. Be concise and creative."),
            HumanMessage(content="Person: Alice, visiting from London"),
        ]
    }

    # -- Mode 1: stream_mode="updates" ------------------------------------
    # Shows WHICH node produced WHAT change -- great for progress tracking
    print("=== Stream Mode: updates ===\n")
    for chunk in app.stream(initial, stream_mode="updates"):
        for node_name, update in chunk.items():
            msg = update["messages"][-1]
            print(f"[{node_name}] {msg.content[:100]}...")
            print()

    # -- Mode 2: stream_mode="values" -------------------------------------
    # Shows the complete state after each node -- good for debugging
    print("\n=== Stream Mode: values ===\n")
    for state_snapshot in app.stream(initial, stream_mode="values"):
        n = len(state_snapshot["messages"])
        last = state_snapshot["messages"][-1]
        role = last.__class__.__name__.replace("Message", "")
        print(f"[State has {n} messages] Latest: [{role}] {last.content[:80]}...")
        print()

    # -- Mode 3: Token-by-token streaming ---------------------------------
    # For real-time typing effect (what a frontend SSE stream does)
    print("\n=== Token-by-Token (messages mode) ===\n")
    for msg, metadata in app.stream(initial, stream_mode="messages"):
        if hasattr(msg, "content") and msg.content:
            print(msg.content, end="", flush=True)
    print("\n")

    # -- Key takeaway ------------------------------------------------------
    # - "updates" -> see which node did what (progress tracking)
    # - "values"  -> see full state after each step (debugging)
    # - "messages"-> token-by-token LLM output (live UI)
    #
    # All three modes run the same graph; they only change what you
    # observe while it runs. Pick the mode that fits your use case.
    #
    # -- Exercise ----------------------------------------------------------
    # 1. Add a third node "farewell" after translate that writes a goodbye
    # 2. Stream with mode="updates" and observe all three steps
    # 3. Try streaming with a checkpointer + thread_id
