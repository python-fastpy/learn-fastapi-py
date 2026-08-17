"""Lesson 08 — Checkpointers & Memory
======================================

WHY THIS MATTERS:
  In lessons 05-07, every invoke() started fresh — the LLM had no memory
  of previous messages. Ask "My name is Alice" then "What's my name?" and
  the LLM would say "I don't know." That's useless for a real assistant.

  Checkpointers fix this. They save the entire graph state (all messages)
  after each invoke, keyed by a thread_id. Next time you invoke with the
  same thread_id, the saved messages are loaded back — the LLM sees the
  full conversation history and "remembers" everything.

  This is how the production assistant maintains sessions across requests:
  each user session gets a thread_id, and DynamoDB stores the checkpoint.

WHAT YOU'LL LEARN:
  1. MemorySaver: in-memory checkpointer (saves state in a Python dict)
  2. thread_id: each conversation gets its own isolated memory
  3. Same thread → LLM remembers prior messages (Turn 1 + Turn 2)
  4. Different thread → fresh start, no memory (Turn 3)
  5. How this maps to DynamoDB checkpointing in production

How checkpointing works under the hood:
  1. You call app.invoke(messages, config={"configurable": {"thread_id": "session-001"}})
  2. LangGraph loads any existing checkpoint for "session-001"
  3. The new messages are APPENDED to the loaded messages
  4. The graph runs (LLM sees the full history)
  5. LangGraph saves the updated state back to the checkpointer
  6. Next invoke with "session-001" picks up where it left off

  Without a checkpointer, step 2 finds nothing — every invoke is isolated.

Concepts:
  - MemorySaver(): in-memory checkpointer (dev/testing only)
  - graph.compile(checkpointer=memory): enables state persistence
  - config = {"configurable": {"thread_id": "..."}}: required for every invoke
  - Same thread_id = accumulated history, different thread_id = fresh start
  - Production uses DynamoDB (dynamodb_checkpointer.py), not MemorySaver

Graph:
  +-------+     +---------+     +-----+
  | START | --> | chatbot | --> | END |
  +-------+     +---------+     +-----+
                     |
              [MemorySaver]
              saves/loads state per thread_id

  Turn 1 (session-001): "My name is Alice. I prefer formal greetings."
    → checkpoint saved: [SystemMessage, HumanMessage, AIMessage]

  Turn 2 (session-001): "What's my name?"
    → checkpoint loaded, new message appended
    → LLM sees full history → "Your name is Alice!"

  Turn 3 (session-002): "What's my name?"
    → no checkpoint for this thread → fresh start
    → LLM has no history → "I don't know your name"

  Maps to:
    dynamodb_checkpointer.py  → production checkpointer (DynamoDB)
    session_manager.py        → session CRUD (list, delete, resume)
    langgraph_mcp_orchestrator.py → compile(checkpointer=...) for interrupt resume

PREREQUISITES: Lesson 05 (chat models — same graph, but without memory)

** Requires .env with orchestrator credentials **

Run:  uv run python 08_checkpointers.py

EXPECTED OUTPUT:
  === Graph Diagram (Mermaid) ===
  (mermaid graph text)

  === Turn 1 ===
  AI: Hello, Alice! I'll remember that you prefer formal greetings...

  === Turn 2 (same thread) ===
  AI: Your name is Alice, and you prefer formal greetings...

  === Turn 3 (different thread) ===
  AI: I don't know your name. Could you tell me?...
"""

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage
from llm_helper import get_llm


# ── Step 1: Same graph as lesson 05 — nothing new here ──────────────

llm = get_llm(model="gpt-4o")


def chatbot(state: MessagesState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


graph = StateGraph(MessagesState)
graph.add_node("chatbot", chatbot)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

# ── Step 2: The ONE change — compile with a checkpointer ────────────
# Without this, every invoke() is a blank slate.
# With this, messages accumulate per thread_id.
# MemorySaver stores checkpoints in a Python dict (lost on restart).
# Production uses DynamoDB (persists across deploys and restarts).
memory = MemorySaver()
app = graph.compile(checkpointer=memory)


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    # ── Step 3: Every invoke needs a config with thread_id ─────────────
    # thread_id is like a session ID — it tells the checkpointer
    # which conversation to load/save. No thread_id = error.
    config = {"configurable": {"thread_id": "session-001"}}

    # ── Turn 1: Introduce yourself ───────────────────────────────────
    # After this invoke, the checkpointer saves:
    #   [SystemMessage, HumanMessage("My name is Alice..."), AIMessage]
    print("=== Turn 1 ===")
    result1 = app.invoke(
        {"messages": [
            SystemMessage(content=(
                "You are a friendly greeting assistant. "
                "Remember names and preferred greeting styles."
            )),
            HumanMessage(content="My name is Alice. I prefer formal greetings."),
        ]},
        config=config,
    )
    print(f"AI: {result1['messages'][-1].content[:200]}\n")

    # ── Turn 2: Same thread → LLM remembers ─────────────────────────
    # The checkpointer loads Turn 1's messages, appends this new one.
    # The LLM sees the FULL history and knows Alice prefers formal.
    print("=== Turn 2 (same thread) ===")
    result2 = app.invoke(
        {"messages": [
            HumanMessage(content="What's my name and how should you greet me?"),
        ]},
        config=config,
    )
    print(f"AI: {result2['messages'][-1].content[:200]}\n")

    # ── Turn 3: Different thread → fresh start ───────────────────────
    # "session-002" has no checkpoint — the LLM sees only this message.
    # It has no idea who Alice is because that's in a different thread.
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
    # One line changes everything:
    #
    #   app = graph.compile()                    # no memory
    #   app = graph.compile(checkpointer=memory) # full memory
    #
    # That's the only code difference between a stateless chatbot
    # and one that remembers your entire conversation.
    #
    # How it maps to production:
    #   MemorySaver (this lesson)  → Python dict, lost on restart
    #   DynamoDB checkpointer      → persists across deploys
    #   thread_id                  → user's session ID in the frontend
    #
    # Checkpointers also enable lesson 09 (human-in-the-loop):
    # interrupt() saves state mid-graph, and Command(resume=...)
    # loads it back — that only works because of checkpointing.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Use app.get_state(config) to inspect the checkpoint —
    #    print the number of messages stored after each turn
    # 2. Try app.get_state_history(config) to see all snapshots
    # 3. Add a fourth turn on session-001 and verify the LLM still
    #    remembers Alice from Turn 1
