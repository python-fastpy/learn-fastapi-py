"""Lesson 06 — Tool Calling
============================
Concepts:
  - Defining tools with @tool decorator
  - Binding tools to an LLM with llm.bind_tools()
  - ToolNode: auto-executes tool calls from the LLM
  - The LLM decides WHEN and WHICH tool to call

Graph:
  +-------+     +-----+
  | START | --> | llm |
  +-------+     +-----+
                  |
          should_use_tool()
            /          \
           v            v
      +-------+      +-----+
      | tools | ---> | END |
      +-------+  |
           |     (no tool_calls)
           +---> llm
        (loop back)

  The LLM -> tools -> LLM loop continues until the LLM responds
  without any tool_calls, then it exits to END.

** Requires .env with orchestrator credentials **

Run:  uv run python 06_tool_calling.py
"""

from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from llm_helper import get_llm


# ── Step 1: Define tools ─────────────────────────────────────────────
# Tools are just Python functions with the @tool decorator.
# The docstring becomes the tool description the LLM sees.

@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! Welcome!"


@tool
def farewell(name: str) -> str:
    """Say goodbye to someone."""
    return f"Goodbye, {name}! See you soon!"


tools = [greet, farewell]


# ── Step 2: Bind tools to the LLM ───────────────────────────────────
# bind_tools tells the LLM about available tools so it can call them.

llm = get_llm(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)


# ── Step 3: Define nodes ────────────────────────────────────────────

def call_llm(state: MessagesState) -> dict:
    """Let the LLM decide whether to call a tool or respond directly."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# ToolNode automatically executes any tool calls in the last message
tool_node = ToolNode(tools)


# ── Step 4: Route based on whether the LLM wants to call a tool ─────

def should_use_tool(state: MessagesState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# ── Step 5: Build the graph ─────────────────────────────────────────

graph = StateGraph(MessagesState)
graph.add_node("llm", call_llm)
graph.add_node("tools", tool_node)

graph.add_edge(START, "llm")
graph.add_conditional_edges("llm", should_use_tool, {"tools": "tools", END: END})
graph.add_edge("tools", "llm")  # After tool runs, go back to LLM

app = graph.compile()


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(app.get_graph().draw_mermaid())
    print()

    # The LLM will decide to call greet and farewell
    result = app.invoke({
        "messages": [
            HumanMessage(content="Greet Alice and then say goodbye to her")
        ]
    })

    print("=== Conversation ===")
    for msg in result["messages"]:
        role = msg.__class__.__name__.replace("Message", "")
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            print(f"[{role}] Tool calls: {[tc['name'] for tc in msg.tool_calls]}")
        elif hasattr(msg, "name") and msg.name:
            print(f"[Tool:{msg.name}] {msg.content}")
        else:
            print(f"[{role}] {msg.content[:200]}")
        print()

    # ── Key takeaway ─────────────────────────────────────────────────
    # Flow: LLM → (tool_calls?) → ToolNode executes → back to LLM
    # The LLM sees the tool results and formulates a final answer.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a third tool: translate_greeting(text, language) that
    #    returns a fake translation of the greeting into that language
    # 2. Ask: "Greet Bob, translate it to French, then say goodbye"
    # 3. Watch the LLM call all three tools in sequence
