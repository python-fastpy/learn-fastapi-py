"""Lesson 05 — Chat Models + MessagesState
===========================================

WHY THIS MATTERS:
  Lessons 01-04 used pure Python functions -- no LLM. This lesson connects
  LangGraph to a real LLM (GPT-4o via the TR Orchestrator). The LLM generates
  text, but it still can't DO anything (no tools yet -- that's lesson 06).
  This is the simplest "chatbot" graph: one node that calls the LLM.

  Every graph in lessons 06-13 builds on this pattern. The production backend
  starts with exactly this: a single chatbot node inside a StateGraph with
  MessagesState.

WHAT YOU'LL LEARN:
  1. MessagesState: built-in state schema with a `messages` list and
     add_messages reducer
  2. HumanMessage, AIMessage, SystemMessage: the three message types
  3. How to call a real LLM inside a LangGraph node
  4. How the add_messages reducer accumulates messages automatically
  5. The pattern every LLM-powered graph in lessons 06-13 builds on

Concepts:
  - MessagesState = TypedDict with messages: Annotated[list, add_messages]
  - add_messages reducer: intelligently appends (deduplicates by ID,
    handles updates). You never manually manage the list.
  - SystemMessage: sets the LLM's persona/behavior (injected once at start)
  - HumanMessage: the user's input
  - AIMessage: the LLM's response (returned automatically by llm.invoke)
  - Node returns {"messages": [response]} -- reducer APPENDS, not replaces

Graph:
  +-------+     +---------+     +-----+
  | START | --> | chatbot | --> | END |
  +-------+     +---------+     +-----+

  Execution trace:
    Input:   [SystemMessage("You are a greeting assistant..."),
              HumanMessage("Write a warm greeting for Alice...")]
    chatbot: calls llm.invoke(messages) -> AIMessage("Welcome to our...")
    Output:  [SystemMessage, HumanMessage, AIMessage]  (3 messages, accumulated)

Maps to:
  langgraph_mcp_orchestrator.py -> chatbot node pattern
  chat.py                       -> initial message handling
  model_config.py               -> LLM model selection

PREREQUISITES: Lesson 04 (state reducers -- MessagesState uses the same pattern)

EXPECTED OUTPUT:
  === Graph Diagram (Mermaid) ===
  (mermaid graph text)

  [System] You are a friendly greeting assistant...
  [Human] Write a warm greeting for Alice who is visiting from Paris.
  [AI] Welcome, Alice! How wonderful that you're here from Paris...

** Requires .env with orchestrator credentials **

Run:  uv run python 05_chat_models.py
"""

from langgraph.graph import StateGraph, MessagesState, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from llm_helper import get_llm


# ── Step 1: MessagesState and the add_messages reducer ───────────────
# MessagesState is a built-in TypedDict that looks like this:
#   class MessagesState(TypedDict):
#       messages: Annotated[list, add_messages]
#
# The `add_messages` reducer intelligently appends new messages to the
# list. When your node returns {"messages": [new_msg]}, the reducer
# appends it -- it never replaces the existing list. This is why
# conversation history accumulates automatically across nodes.

llm = get_llm(model="gpt-4o")


# ── Step 2: The chatbot node ────────────────────────────────────────
# This is the simplest possible LLM node. It receives the full message
# history from state, passes it to the LLM, and returns the response.
# The add_messages reducer handles appending it to the conversation.

def chatbot(state: MessagesState) -> dict:
    """Call the LLM with the full message history.

    The LLM sees ALL prior messages (system prompt, user input, any
    previous AI responses) and generates a contextual reply. Returning
    {"messages": [response]} lets the reducer append it automatically.
    """
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


# ── Step 3: Build and compile the graph ─────────────────────────────
# This is the simplest possible LLM graph: one node, one edge in,
# one edge out. Every LLM graph in lessons 06-13 starts from this
# exact pattern and adds complexity (tools, branching, loops).

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
            SystemMessage(content="You are a friendly greeting assistant. Keep responses concise."),
            HumanMessage(content="Write a warm greeting for Alice who is visiting from Paris."),
        ]
    })

    # Print all messages
    for msg in result["messages"]:
        role = msg.__class__.__name__.replace("Message", "")
        print(f"[{role}] {msg.content[:200]}")
        print()

    # ── Key takeaway ─────────────────────────────────────────────────
    # MessagesState handles message accumulation automatically. Your
    # node just returns {"messages": [new_message]} and LangGraph
    # appends it to the list via the add_messages reducer.
    #
    # This is the foundation for EVERY LLM graph in this tutorial.
    # Without MessagesState and add_messages, you'd need to manually
    # track conversation history, handle deduplication, and manage
    # message ordering yourself. The reducer does all of that for you.
    #
    # In production (langgraph_mcp_orchestrator.py), the chatbot node
    # follows this exact same pattern -- it just adds tool-calling
    # capabilities on top (lesson 06).
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a second node `translate` after chatbot that sends a
    #    follow-up asking the LLM to translate the greeting to French
    # 2. Wire: START -> chatbot -> translate -> END
    # 3. Observe how messages accumulate across both nodes
