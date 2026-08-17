"""Lesson 10 — Streaming
========================

WHY THIS MATTERS:
  Without streaming, users stare at a blank screen until the entire graph
  finishes -- which can take seconds for multi-step LLM workflows. Streaming
  lets you show progress as it happens: "composing greeting..." then
  "translating..." then tokens appearing one by one. This is how the
  production assistant shows live typing and progress updates.

  The backend uses SSE (Server-Sent Events) to stream results to the
  frontend. Under the hood, it's the same concept: app.stream() produces
  chunks that get forwarded as SSE events.

WHAT YOU'LL LEARN:
  1. app.stream() vs app.invoke(): streaming vs batch execution
  2. stream_mode="updates": see which node produced what change (progress)
  3. stream_mode="values": see full state snapshot after each node (debug)
  4. stream_mode="messages": token-by-token LLM output (live typing in UI)
  5. How this maps to SSE streaming in the production backend

Concepts:
  - app.invoke(): runs entire graph, returns final state (blocking)
  - app.stream(): yields results as each node completes (non-blocking)
  - "updates" mode: {node_name: {changed_keys}} -- perfect for progress bars
  - "values" mode: full state after each step -- perfect for debugging
  - "messages" mode: individual LLM tokens -- perfect for live typing UI
  - All three modes run the SAME graph -- they only change what you observe

Graph:
  +-------+     +---------+     +-----------+     +-----+
  | START | --> | compose | --> | translate | --> | END |
  +-------+     +---------+     +-----------+     +-----+

  Execution traces by mode:

    stream_mode="updates":
      chunk 1: {"compose": {"messages": [AIMessage("Welcome, Alice! ...")]}}
      chunk 2: {"translate": {"messages": [AIMessage("Bienvenue, Alice! ...")]}}

    stream_mode="values":
      snapshot 1: {"messages": [System, Human]}  (initial state)
      snapshot 2: {"messages": [System, Human, AI("Welcome...")]}  (after compose)
      snapshot 3: {"messages": [System, Human, AI("Welcome..."), AI("Bienvenue...")]}

    stream_mode="messages":
      token: "Bien"
      token: "venue"
      token: ","
      token: " Alice"
      ...

Maps to:
  chat.py               -> SSE streaming endpoint
  langgraph_mcp_orchestrator.py -> app.stream() with progress events
  progress_websocket.py -> WebSocket progress updates to frontend
  reuter-ai-assistant-v2 -> typing indicator, progress tracker

PREREQUISITES: Lesson 05 (chat models -- same graph structure, now with
  streaming)

EXPECTED OUTPUT:
  === Graph Diagram (Mermaid) ===
  (mermaid graph text)

  === Stream Mode: updates ===
  [compose] Welcome, Alice! So delighted...
  [translate] Bienvenue, Alice! ...

  === Stream Mode: values ===
  [State has 2 messages] Latest: [Human] Person: Alice...
  [State has 3 messages] Latest: [AI] Welcome, Alice!...
  [State has 4 messages] Latest: [AI] Bienvenue, Alice!...

  === Token-by-Token (messages mode) ===
  Welcome, Alice! So delighted to have you here from London...

** Requires .env with orchestrator credentials **

Run:  uv run python 10_streaming.py
"""

from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from llm_helper import get_llm

llm = get_llm(model="gpt-4o")


# ── Step 1: Define the graph nodes ──────────────────────────────────
# Two nodes that each call the LLM: compose writes the greeting,
# translate converts it to French. This gives us a multi-step graph
# where streaming can show progress between steps.

def compose(state: MessagesState) -> dict:
    """Generate the initial greeting in English.

    Appends a HumanMessage prompt to guide the LLM, then returns the
    response. In streaming mode, each token from this LLM call can be
    observed individually (messages mode) or as a batch (updates mode).
    """
    response = llm.invoke(state["messages"] + [
        HumanMessage(content="Write a warm greeting for this person. Be creative.")
    ])
    return {"messages": [response]}


def translate(state: MessagesState) -> dict:
    """Translate the greeting into French.

    The LLM sees the full conversation (including the English greeting
    from compose) and produces a French translation. Streaming shows
    this as a second progress step after compose completes.
    """
    response = llm.invoke(state["messages"] + [
        HumanMessage(content="Now translate that greeting into French.")
    ])
    return {"messages": [response]}


# ── Step 2: Build the graph ─────────────────────────────────────────
# Same structure as lesson 05 but with two nodes. The graph itself is
# identical whether you use invoke() or stream() -- streaming only
# changes how you OBSERVE the execution, not how it runs.

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

    # ── Mode 1: stream_mode="updates" ───────────────────────────────
    # Shows WHICH node produced WHAT change. Each chunk is a dict:
    #   {node_name: {keys_that_changed}}
    # This is ideal for progress tracking -- in production, each chunk
    # maps to a progress event sent to the frontend via SSE/WebSocket.
    print("=== Stream Mode: updates ===\n")
    for chunk in app.stream(initial, stream_mode="updates"):
        for node_name, update in chunk.items():
            msg = update["messages"][-1]
            print(f"[{node_name}] {msg.content[:100]}...")
            print()

    # ── Mode 2: stream_mode="values" ────────────────────────────────
    # Shows the FULL state snapshot after each node completes. You see
    # the entire messages list growing with each step. This is ideal
    # for debugging -- you can inspect exactly what each node added.
    print("\n=== Stream Mode: values ===\n")
    for state_snapshot in app.stream(initial, stream_mode="values"):
        n = len(state_snapshot["messages"])
        last = state_snapshot["messages"][-1]
        role = last.__class__.__name__.replace("Message", "")
        print(f"[State has {n} messages] Latest: [{role}] {last.content[:80]}...")
        print()

    # ── Mode 3: stream_mode="messages" ──────────────────────────────
    # Yields individual LLM tokens as they're generated. This is what
    # powers the "live typing" effect in the frontend. In production,
    # these tokens are forwarded as SSE events to the browser, where
    # the typing indicator renders them character by character.
    print("\n=== Token-by-Token (messages mode) ===\n")
    for msg, metadata in app.stream(initial, stream_mode="messages"):
        if hasattr(msg, "content") and msg.content:
            print(msg.content, end="", flush=True)
    print("\n")

    # ── Key takeaway ─────────────────────────────────────────────────
    # All three modes run the SAME graph -- they only change what you
    # observe while it runs. Pick the mode that fits your use case:
    #
    #   "updates"  -> progress tracking (which node did what)
    #   "values"   -> debugging (full state after each step)
    #   "messages" -> live UI (token-by-token typing effect)
    #
    # In the production backend, chat.py uses app.stream() to produce
    # SSE events. The frontend's typing indicator and progress tracker
    # consume these events to show real-time feedback. Without
    # streaming, users would wait for the entire multi-step workflow
    # to finish before seeing anything -- a poor experience for
    # workflows that take 5-10 seconds across multiple LLM calls.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a third node "farewell" after translate that writes a goodbye
    # 2. Stream with mode="updates" and observe all three steps
    # 3. Try streaming with a checkpointer + thread_id
