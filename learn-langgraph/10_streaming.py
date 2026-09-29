"""Lesson 10 -- Streaming
=========================

`invoke()` returns once, at the end. For a two-LLM-call graph that is several
seconds of blank screen. `stream()` yields as the run progresses -- same
graph, same nodes, you only change what you WATCH.

  START ──► compose ──► translate ──► END        two LLM calls, ~2-4 seconds

  three ways to observe exactly that run:

  stream_mode="updates"   what CHANGED, per node        -> progress bars
    {"compose":   {"messages": [AI("Welcome, Shubham!")]}}
    {"translate": {"messages": [AI("Bienvenue, Shubham!")]}}

  stream_mode="values"    the WHOLE state, per step     -> debugging
    {"messages": [System, Human]}                  (before anything ran)
    {"messages": [System, Human, AI]}              (after compose)
    {"messages": [System, Human, AI, AI]}          (after translate)

  stream_mode="messages"  one LLM TOKEN at a time       -> live typing
    "Bien" "venue" "," " Shubham" "!" ...

  1. invoke()     runs everything, returns the final state.
  2. stream()     a generator: you get chunks as nodes finish.
  3. "updates"    {node: {changed keys}} -- the least data, enough to drive
                  "composing... translating..." in a UI.
  4. "values"     a full snapshot per step. Verbose, but it shows you
                  precisely what each node added.
  5. "messages"   token-level, straight from the model, for a typing effect.
                  Yields (message_chunk, metadata) pairs.

  Streaming does not make the graph faster -- the two LLM calls take just as
  long. It moves the waiting somewhere the user can see, which is why every
  chat UI uses it. Lesson 15 puts these chunks on the wire as SSE.

** Requires .env with orchestrator credentials **

Run:  uv run python 10_streaming.py

Maps to: chat.py -> the SSE endpoint; langgraph_mcp_orchestrator.py ->
app.stream() with progress events; progress_websocket.py
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph

from llm_helper import get_llm

llm = get_llm(model="gpt-4o")


def compose(state: MessagesState) -> dict:
    return {"messages": [llm.invoke(state["messages"] + [
        HumanMessage(content="Write a warm one-line greeting for this person.")
    ])]}


def translate(state: MessagesState) -> dict:
    return {"messages": [llm.invoke(state["messages"] + [
        HumanMessage(content="Now translate that greeting into French. French only.")
    ])]}


graph = StateGraph(MessagesState)
graph.add_node("compose", compose)
graph.add_node("translate", translate)
graph.add_edge(START, "compose")
graph.add_edge("compose", "translate")
graph.add_edge("translate", END)

app = graph.compile()


if __name__ == "__main__":
    start = {"messages": [
        SystemMessage(content="You are a greeting assistant. Be concise."),
        HumanMessage(content="Person: Shubham, visiting from London"),
    ]}

    # 3. updates -- one chunk per node, holding only what it changed
    print("=== stream_mode='updates' (progress) ===")
    for chunk in app.stream(start, stream_mode="updates"):
        for node, update in chunk.items():
            print(f"  [{node:<9}] {update['messages'][-1].content[:70]}")

    # 4. values -- one full snapshot per step, so the list visibly grows
    print("\n=== stream_mode='values' (debugging) ===")
    for snapshot in app.stream(start, stream_mode="values"):
        kinds = [type(m).__name__.replace("Message", "") for m in snapshot["messages"]]
        print(f"  {len(kinds)} messages: {kinds}")

    # 5. messages -- token by token, as the model emits them
    print("\n=== stream_mode='messages' (live typing) ===")
    tokens = 0
    for chunk, _meta in app.stream(start, stream_mode="messages"):
        if chunk.content:
            tokens += 1
            print(chunk.content, end="", flush=True)
    print(f"\n  ({tokens} token chunks -- the same run, at a finer grain)")

# Exercises:
# 1. Time invoke() against the "updates" loop. Identical totals: streaming
#    changes when you SEE output, never how long the work takes.
# 2. Pass stream_mode=["updates", "messages"] to get both at once. The
#    chunks arrive tagged with their mode.
# 3. In "values" mode, print snapshot["messages"][-1] instead of the count --
#    that is the debugging view the mode exists for.
# 4. Replace print(end="") in mode 5 with a 0.02s sleep per token to see why
#    a UI feels faster even though the graph is not.
