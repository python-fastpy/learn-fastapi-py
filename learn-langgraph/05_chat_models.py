"""Lesson 05 — Chat Models + MessagesState
===========================================
Concepts:
  - MessagesState: built-in state schema with a `messages` list
  - Messages use the reducer pattern -- each node APPENDS messages
  - Integrating a real LLM (gpt-4o via TR Orchestrator)
  - HumanMessage, AIMessage, SystemMessage types

Graph:
  +-------+     +---------+     +-----+
  | START | --> | chatbot | --> | END |
  +-------+     +---------+     +-----+

  MessagesState uses `add_messages` reducer -- messages accumulate
  automatically. The chatbot node appends the LLM response.

** Requires .env with orchestrator credentials **

Run:  uv run python 05_chat_models.py
"""

from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from llm_helper import get_llm


# MessagesState is just:  class MessagesState(TypedDict):
#                             messages: Annotated[list, add_messages]
# The `add_messages` reducer intelligently appends new messages.

llm = get_llm(model="gpt-4o")


def chatbot(state: MessagesState) -> dict:
    """Call the LLM with the full message history."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


graph = StateGraph(MessagesState)
graph.add_node("chatbot", chatbot)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    result = app.invoke({
        "messages": [
            SystemMessage(content="You are a Reuters news editor. Be concise."),
            HumanMessage(content="What makes a good news headline?"),
        ]
    })

    # Print all messages
    for msg in result["messages"]:
        role = msg.__class__.__name__.replace("Message", "")
        print(f"[{role}] {msg.content[:200]}")
        print()

    # ── Key takeaway ─────────────────────────────────────────────────
    # MessagesState handles message accumulation automatically.
    # Your node just returns {"messages": [new_message]} and LangGraph
    # appends it to the list via the add_messages reducer.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a second node `fact_check` after chatbot that sends a
    #    follow-up question asking the LLM to verify its own claims
    # 2. Wire: START → chatbot → fact_check → END
    # 3. Observe how messages accumulate across both nodes
