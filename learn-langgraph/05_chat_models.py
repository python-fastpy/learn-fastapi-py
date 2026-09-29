"""Lesson 05 -- Chat Models and MessagesState
=============================================

Lessons 01-04 were pure Python. This is the first graph with a real LLM in
it: one node that calls the model. It can talk but not DO anything yet --
tools are lesson 06. Every LLM graph that follows starts from this shape.

  START ──► chatbot ──► END          chatbot calls the model and returns
               │                     whatever it said
               └──► gpt-4o

  the `messages` list before and after that one node:

    in   [ System("You are a friendly greeting assistant"),
           Human("Write a warm greeting for Shubham ...") ]
             │
             ▼   chatbot: llm.invoke(state["messages"])  -> AIMessage
    out  [ System, Human, AI("Welcome, Shubham! ...") ]
                          └── add_messages APPENDED it; nothing was replaced

  1. MessagesState  a built-in state class. It is exactly lesson 04's idea:
                    messages: Annotated[list, add_messages]
  2. THREE TYPES    SystemMessage sets behaviour, HumanMessage is the user,
                    AIMessage is the reply. `.content` holds the text.
  3. THE NODE       llm.invoke(state["messages"]) -- you hand the model the
                    WHOLE history, every time. It remembers nothing itself.
  4. THE RETURN     {"messages": [response]} and add_messages appends it, so
                    you never manage the list by hand.
  5. add_messages   is add-with-judgement: it de-duplicates by message id, so
                    a re-emitted message updates rather than doubling up.

  Point 3 is also the bill: the model re-reads every message on every call,
  so a long conversation costs more per turn than a short one. That is why
  lesson 09's interrupts and lesson 11's subgraphs keep histories small.

** Requires .env with orchestrator credentials **

Run:  uv run python 05_chat_models.py

Maps to: langgraph_mcp_orchestrator.py -> the chatbot node; chat.py -> initial
message handling; model_config.py -> model selection
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, MessagesState, StateGraph

from llm_helper import get_llm

llm = get_llm(model="gpt-4o")


def chatbot(state: MessagesState) -> dict:
    """The whole node. The history goes in, one AIMessage comes out."""
    response = llm.invoke(state["messages"])
    return {"messages": [response]}          # appended by add_messages


graph = StateGraph(MessagesState)
graph.add_node("chatbot", chatbot)
graph.add_edge(START, "chatbot")
graph.add_edge("chatbot", END)

app = graph.compile()


if __name__ == "__main__":
    result = app.invoke({
        "messages": [
            SystemMessage(content="You are a friendly greeting assistant. Keep replies to one sentence."),
            HumanMessage(content="Write a warm greeting for Shubham, who is visiting from Paris."),
        ]
    })

    print(f"messages in: 2, messages out: {len(result['messages'])}\n")
    for msg in result["messages"]:
        role = type(msg).__name__.replace("Message", "")
        print(f"[{role:<6}] {msg.content[:160]}")

    print("\nThe System and Human messages are still there -- the reducer appended.")

# Exercises:
# 1. Add a `translate` node after chatbot that appends
#    HumanMessage("Now in French") and calls the LLM again. Watch the list
#    reach five, and note the second call re-read all four earlier messages.
# 2. Invoke twice in a row with two separate app.invoke() calls. The second
#    starts empty -- the graph has no memory yet. That is lesson 08.
# 3. Return {"messages": response} (not a list). Does add_messages cope?
# 4. Drop the SystemMessage and rerun. Same model, noticeably different voice.
