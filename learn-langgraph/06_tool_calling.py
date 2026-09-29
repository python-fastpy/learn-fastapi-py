"""Lesson 06 -- Tool Calling
============================

Lesson 05's model could only talk. Give it tools and the graph gains a LOOP:
the model asks for a tool, the tool runs, the model sees the result and
decides again -- until it has nothing left to ask for.

  START
    │
    ▼
   llm ◄──────────────────┐        one model call, then one decision
    │                     │
    │  did it ask for a   │
    │  tool?              │
    ├── yes ──► tools ────┘        ToolNode runs it and appends the result,
    │                              then hands control straight back
    └── no ───► END                the model answered in prose: done

  messages after "Greet Shubham and then say goodbye to her":

    Human  "Greet Shubham and then say goodbye"
    AI     tool_calls = [greet, farewell]        <- no prose, just requests
    Tool   "Hello, Shubham! Welcome!"            <- one ToolMessage per call
    Tool   "Goodbye, Shubham! See you soon!"
    AI     "I've greeted Shubham and said goodbye."   <- no tool_calls -> END

  1. @tool        turns a function into something callable. The NAME and
                  DOCSTRING are what the model reads to choose -- they are
                  prompt, not comments.
  2. bind_tools   hands the model the menu. Without it the model cannot know
                  any tool exists and will only ever reply in prose.
  3. ToolNode     prebuilt: reads tool_calls off the last AIMessage, runs the
                  matching function, appends a ToolMessage per call. You
                  write no name->function dispatch.
  4. should_use_tool  the conditional edge (lesson 03) that closes the loop:
                  "tools" while requests keep coming, END when they stop.
  5. THE CYCLE    add_edge("tools", "llm") is the line that makes it a loop
                  rather than a pipeline.

  Nothing here limits the iterations. A model that keeps asking will keep
  looping until LangGraph raises GraphRecursionError -- the default
  recursion_limit is 10007 in this version, so treat it as a crash backstop,
  not a design. Real agents cap turns themselves.

** Requires .env with orchestrator credentials **

Run:  uv run python 06_tool_calling.py

Maps to: langgraph_mcp_orchestrator.py -> the same loop, where the tools are
MCP servers instead of local functions (lesson 14)
"""

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from llm_helper import get_llm


# -- 1. The tools. The docstring IS the model's instruction manual ----------

@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! Welcome!"


@tool
def farewell(name: str) -> str:
    """Say goodbye to someone."""
    return f"Goodbye, {name}! See you soon!"


tools = [greet, farewell]

# -- 2. Hand the model the menu ---------------------------------------------
llm_with_tools = get_llm(model="gpt-4o").bind_tools(tools)


def call_llm(state: MessagesState) -> dict:
    """Either prose, or tool_calls. The model chooses."""
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# -- 4. The decision that closes the loop -----------------------------------

def should_use_tool(state: MessagesState) -> str:
    return "tools" if state["messages"][-1].tool_calls else END


graph = StateGraph(MessagesState)
graph.add_node("llm", call_llm)
graph.add_node("tools", ToolNode(tools))      # 3. no dispatch code needed

graph.add_edge(START, "llm")
# The map is optional -- LangGraph can infer it -- but writing it out makes
# the two exits visible and catches a typo at build time instead of at 3am.
graph.add_conditional_edges("llm", should_use_tool, {"tools": "tools", END: END})
graph.add_edge("tools", "llm")                # 5. the cycle

app = graph.compile()


if __name__ == "__main__":
    result = app.invoke({
        "messages": [HumanMessage(content="Greet Shubham and then say goodbye to her")]
    })

    for msg in result["messages"]:
        role = type(msg).__name__.replace("Message", "")
        if getattr(msg, "tool_calls", None):
            print(f"[{role:<6}] wants: {[tc['name'] for tc in msg.tool_calls]}")
        elif getattr(msg, "name", None):
            print(f"[Tool:{msg.name:<8}] {msg.content}")
        else:
            print(f"[{role:<6}] {msg.content[:150]}")

    llm_turns = sum(1 for m in result["messages"] if type(m).__name__ == "AIMessage")
    print(f"\nThe graph went round {llm_turns} times: ask -> run -> answer.")

# Exercises:
# 1. Add translate(text, language) and ask for a greeting in French. The loop
#    length changes; none of the wiring does.
# 2. Change greet's docstring to "Do the thing." and rerun. The model stops
#    choosing it correctly -- that docstring was load-bearing.
# 3. Drop .bind_tools(tools) and rerun. You get prose describing a greeting
#    instead of a tool call, because the model never learned the tools exist.
# 4. Delete add_edge("tools", "llm") and add_edge("tools", END) instead. The
#    tools still run, but the model never gets to see their results.
