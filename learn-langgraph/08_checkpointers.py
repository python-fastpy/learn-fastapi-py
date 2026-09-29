"""Lesson 08 -- Checkpointers and Memory
========================================

Lesson 05's graph forgot everything between calls: each invoke() started
from an empty list. A CHECKPOINTER saves the state after every invoke, keyed
by a thread_id, and loads it back next time. That is the whole of "memory".

  compile(checkpointer=MemorySaver())   <- the only change to the graph

  invoke #1, thread "session-001"        invoke #2, SAME thread
  ───────────────────────────────        ──────────────────────
  in   [System, Human("I'm Shubham")]    loaded  [System, Human, AI]  ◄─ saved
         │                                         + Human("what's my name?")
         ▼                                            │
       chatbot                                        ▼
         │                                          chatbot  (sees all four)
         ▼                                            │
  saved  [System, Human, AI]  ──────────────────────►  ▼
                                         saved  [... , AI("Shubham")]

  invoke #3, thread "session-002"  ->  nothing saved under that key, so the
                                       model has never heard of Shubham

  1. MemorySaver()    a checkpointer backed by a dict. Dies with the process.
  2. compile(checkpointer=...)  the one line that turns a stateless graph
                      into a stateful one. The nodes do not change at all.
  3. thread_id        passed per call in config={"configurable": {...}}.
                      It IS the session key. Omit it and you get an error.
  4. SAME id          -> history accumulates. DIFFERENT id -> fresh start.
                      Isolation between users is just a different string.
  5. WHAT IS SAVED    the whole state, not only messages. That is what makes
                      lesson 09's interrupt/resume possible.

  MemorySaver is for learning. Swap in SqliteSaver or the production DynamoDB
  checkpointer and the graph code is untouched -- only the constructor moves.

** Requires .env with orchestrator credentials **

Run:  uv run python 08_checkpointers.py

Maps to: dynamodb_checkpointer.py -> the production checkpointer;
thread_id -> the user's session id from the frontend
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from llm_helper import get_llm

llm = get_llm(model="gpt-4o")


def chatbot(state: MessagesState) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}


# Exactly lesson 05's graph...
graph = StateGraph(MessagesState)
graph.add_node("chatbot", chatbot)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

# ...plus a checkpointer. That is the entire difference.
app = graph.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    first = {"configurable": {"thread_id": "session-001"}}

    # 1. Tell it something.
    r = app.invoke({"messages": [
        SystemMessage(content="You are a greeting assistant. Remember names and preferences."),
        HumanMessage(content="My name is Shubham and I prefer formal greetings."),
    ]}, config=first)
    print("1. turn one        :", r["messages"][-1].content[:110])
    print(f"   state saved     : {len(r['messages'])} messages under 'session-001'")

    # 2. Same thread: we send ONE message, the model sees all of them.
    r = app.invoke({"messages": [
        HumanMessage(content="What is my name, and how should you greet me?"),
    ]}, config=first)
    print("\n2. same thread     :", r["messages"][-1].content[:110])
    print(f"   we sent 1 message, the model saw {len(r['messages']) - 1}")

    # 3. Different thread: same graph, no shared memory.
    other = {"configurable": {"thread_id": "session-002"}}
    r = app.invoke({"messages": [
        HumanMessage(content="What is my name?"),
    ]}, config=other)
    print("\n3. other thread    :", r["messages"][-1].content[:110])
    print(f"   {len(r['messages'])} messages here -- 'session-001' was never loaded")

# Exercises:
# 1. Drop the config= argument from any invoke. Read the error -- it names
#    thread_id, and it is the most common checkpointer mistake.
# 2. Call app.get_state(first) and print .values and .next. This is the same
#    snapshot lesson 09 reads while a graph is paused.
# 3. Run the file twice. Turn 2 forgets again between runs, because
#    MemorySaver lives in the process. Swap in SqliteSaver and it will not.
# 4. Print len(r["messages"]) after ten turns on one thread. That number is
#    what you are billed for on turn eleven (lesson 05, point 3).
