"""Lesson 08 — Checkpointers & Memory
======================================
Concepts:
  - MemorySaver: in-memory checkpointer for conversation persistence
  - thread_id: each conversation gets its own thread
  - The LLM remembers prior messages within the same thread
  - config: {"configurable": {"thread_id": "..."}}

Graph:
  +-------+     +---------+     +-----+
  | START | --> | chatbot | --> | END |
  +-------+     +---------+     +-----+
                     |
              [MemorySaver]
              checkpoints state per thread_id

  Same graph as lesson 05, but compiled with a checkpointer.
  Each thread_id gets its own isolated message history.
  Your backend uses DynamoDB checkpointer for the same purpose!

** Requires .env with orchestrator credentials **

Run:  uv run python 08_checkpointers.py
"""

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
from llm_helper import get_llm


llm = get_llm(model="gpt-4o")


def chatbot(state: MessagesState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


graph = StateGraph(MessagesState)
graph.add_node("chatbot", chatbot)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

# The key difference: compile WITH a checkpointer
memory = MemorySaver()
app = graph.compile(checkpointer=memory)


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    # Every invoke needs a config with a thread_id
    config = {"configurable": {"thread_id": "session-001"}}

    # ── Turn 1 ───────────────────────────────────────────────────────
    print("=== Turn 1 ===")
    result1 = app.invoke(
        {"messages": [
            SystemMessage(content="You are a helpful Reuters editor. Be concise."),
            HumanMessage(content="My name is Shubham. I work on the AI assistant."),
        ]},
        config=config,
    )
    print(f"AI: {result1['messages'][-1].content[:200]}\n")

    # ── Turn 2 — same thread, LLM remembers the name ────────────────
    print("=== Turn 2 (same thread) ===")
    result2 = app.invoke(
        {"messages": [
            HumanMessage(content="What's my name and what do I work on?"),
        ]},
        config=config,
    )
    print(f"AI: {result2['messages'][-1].content[:200]}\n")

    # ── Turn 3 — DIFFERENT thread, LLM does NOT know ────────────────
    print("=== Turn 3 (different thread) ===")
    config_new = {"configurable": {"thread_id": "session-002"}}
    result3 = app.invoke(
        {"messages": [
            HumanMessage(content="What's my name?"),
        ]},
        config=config_new,
    )
    print(f"AI: {result3['messages'][-1].content[:200]}\n")

    # ── Key takeaway ─────────────────────────────────────────────────
    # - Same thread_id → messages accumulate, LLM has memory
    # - Different thread_id → fresh conversation, no memory
    # - Your backend uses DynamoDB instead of MemorySaver but the
    #   pattern is identical (see dynamodb_checkpointer.py)
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Use app.get_state(config) to inspect the checkpoint
    # 2. Print how many messages are stored after each turn
    # 3. Try app.get_state_history(config) to see all snapshots
