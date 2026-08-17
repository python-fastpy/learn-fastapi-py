"""Lesson 06 — Tool Calling
============================

WHY THIS MATTERS:
  In lessons 01-04 we hard-coded which node runs when. In lesson 05
  the LLM generated text, but it couldn't *do* anything. Tool calling
  changes that: you give the LLM a menu of functions it can call, and
  IT decides which ones to use and when. This is how the production
  assistant calls MCP tools — the LLM picks greet, farewell, search,
  or draft based on what the user asked for.

WHAT YOU'LL LEARN:
  1. Define tools with the @tool decorator (the LLM reads the docstring)
  2. Bind tools to an LLM with llm.bind_tools() (gives the LLM the menu)
  3. Use ToolNode to auto-execute tool calls from the LLM response
  4. Route with a conditional edge: tool_calls present → run tools,
     no tool_calls → done
  5. The LLM ↔ tools loop: LLM calls tool → gets result → decides next

Concepts:
  - @tool decorator: turns a Python function into something the LLM can call
  - llm.bind_tools(tools): attaches tool schemas to the LLM
  - ToolNode(tools): prebuilt node that reads tool_calls from the last
    message, executes the matching function, and returns the result
  - Conditional routing: check last message for tool_calls to decide
    whether to loop back or exit

Flow:
  +-------+     +----------+     has tool_calls?     +-----------+
  | START | --> | call_llm | ------------------->    | tool_node |
  +-------+     +----------+        YES              +-----------+
                     ^                                     |
                     |          (loop back with results)   |
                     +-------------------------------------+
                     |
                     |  NO tool_calls (LLM is done)
                     v
                  +-----+
                  | END |
                  +-----+

  The loop continues until the LLM responds with plain text
  (no tool_calls), meaning it has all the info it needs.

  Maps to:
    langgraph_mcp_orchestrator.py  → the same LLM ↔ tool loop
    mcp_protocol.py               → tool execution (call_tool)
    story-drafting/src/main.py    → @tool-decorated functions

PREREQUISITES: Lesson 05 (chat models — MessagesState, HumanMessage)

** Requires .env with orchestrator credentials **

Run:  uv run python 06_tool_calling.py

EXPECTED OUTPUT:
  === Graph Diagram (Mermaid) ===
  (mermaid graph text)

  === Conversation ===
  [Human] Greet Alice and then say goodbye to her

  [AI] Tool calls: ['greet', 'farewell']

  [Tool:greet] Hello, Alice! Welcome!

  [Tool:farewell] Goodbye, Alice! See you soon!

  [AI] I've greeted Alice and said goodbye to her! ...
"""

from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from llm_helper import get_llm


# ── Step 1: Define tools ─────────────────────────────────────────────
# @tool turns a normal function into something the LLM can call.
# The LLM sees the function name + docstring as its "menu" —
# it uses those to decide which tool fits the user's request.
# (This is why short, clear docstrings matter.)

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
# bind_tools attaches the tool schemas (name, description, params)
# to the LLM. Without this, the LLM doesn't know any tools exist.
# Think of it as handing the LLM a menu before it takes an order.

llm = get_llm(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)


# ── Step 3: Define nodes ────────────────────────────────────────────
# Two nodes: one for the LLM, one for executing tools.

def call_llm(state: MessagesState) -> dict:
    """Send messages to the LLM. It responds with either plain text
    (if it has the answer) or tool_calls (if it needs to use a tool)."""
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


# ToolNode is a prebuilt node from LangGraph. It reads tool_calls
# from the last AI message, runs the matching Python function, and
# returns the result as a ToolMessage. You don't write any dispatch
# logic — it handles the name→function lookup automatically.
tool_node = ToolNode(tools)


# ── Step 4: Route based on whether the LLM wants to call a tool ─────
# After the LLM responds, we check: did it ask to call a tool?
# If yes → route to tool_node to execute it.
# If no  → the LLM is done, route to END.
# This is what creates the loop: LLM → tools → LLM → ... → END.

def should_use_tool(state: MessagesState) -> str:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# ── Step 5: Build the graph ─────────────────────────────────────────
# Wire up the loop: START → llm → (tools → llm)* → END

graph = StateGraph(MessagesState)
graph.add_node("llm", call_llm)
graph.add_node("tools", tool_node)

graph.add_edge(START, "llm")

# add_conditional_edges takes three arguments:
#   1. "llm"            — after THIS node finishes...
#   2. should_use_tool  — call THIS function to decide where to go...
#   3. routing map      — translate the return value to a node name:
#
#   should_use_tool returns  │  map entry         │  goes to
#   ─────────────────────────┼─────────────────────┼──────────────────
#   "tools"                  │  "tools": "tools"   │  tool_node
#   END                      │  END: END           │  exit the graph
#
# Think of it as a switch:
#   match should_use_tool(state):
#       case "tools":  go to tools node
#       case END:      finish the graph
#
# The map is optional (LangGraph can infer it from the return values),
# but it makes the wiring visible and catches typos at build time.
graph.add_conditional_edges("llm", should_use_tool, {"tools": "tools", END: END})

graph.add_edge("tools", "llm")  # After tool runs, go back to LLM for next decision

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
    # Three pieces make tool calling work:
    #
    #   1. @tool         — defines what the LLM CAN call
    #   2. bind_tools()  — tells the LLM what's available
    #   3. ToolNode       — executes the tool the LLM chose
    #
    # The conditional edge creates the loop:
    #   LLM → has tool_calls? → YES → ToolNode → back to LLM
    #                         → NO  → END (respond to user)
    #
    # This is the foundation of the ReAct pattern (lesson 07).
    # The production orchestrator uses this same loop but calls
    # MCP servers instead of local Python functions.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a third tool: translate_greeting(text, language) that
    #    returns a fake translation of the greeting into that language
    # 2. Ask: "Greet Bob, translate it to French, then say goodbye"
    # 3. Watch the LLM call all three tools in sequence
