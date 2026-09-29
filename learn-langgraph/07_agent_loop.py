"""Lesson 07 -- The Agent Loop (ReAct), prebuilt
================================================

Lesson 06 wired the loop by hand: two nodes, a routing function, a
conditional edge, a loop-back edge. `create_react_agent` builds that exact
graph in one call. Same shape, none of the wiring.

  what you wrote in lesson 06          what you write now
  ───────────────────────────          ───────────────────
  StateGraph(MessagesState)            agent = create_react_agent(
  add_node("llm", call_llm)                model=llm,
  add_node("tools", ToolNode(tools))       tools=[...],
  add_edge(START, "llm")                   prompt="You are ...",
  add_conditional_edges(...)           )
  add_edge("tools", "llm")
  compile()

  and it produces the same loop, called ReAct -- reason, act, repeat:

    START ──► agent ◄────────────┐
                │                │
                ├── tool_calls ──► tools
                │
                └── prose ──► END

  1. create_react_agent(model, tools, prompt)  the whole graph, one call.
  2. prompt=      a system message. The agent sees it, the user's text, and
                  the tool schemas, and decides from all three.
  3. THE RESULT   an ordinary compiled graph. .invoke(), .stream() and
                  .get_graph() all work exactly as in lesson 06.
  4. REACT        reason (which tool?) -> act (run it) -> observe -> repeat
                  until the model answers in prose instead of asking.

  Use the prebuilt when the standard loop is what you want. Go back to
  lesson 06's manual version the moment you need something in between the
  steps -- an approval gate (lesson 09), a cache, a budget check, logging
  per step. You cannot insert a node into a graph you did not build.

  DEPRECATED, and it warns when you run this: LangGraph 1.0 moved this to
  `from langchain.agents import create_agent` (in the `langchain` package,
  which this folder does not install). The version pinned here still ships
  create_react_agent, and the loop and argument names are the same either
  way -- only the import moves. Lesson 06's hand-built graph has no such
  churn, which is its own argument.

** Requires .env with orchestrator credentials **

Run:  uv run python 07_agent_loop.py

Maps to: create_agent_orchestrator.py -> uses create_react_agent directly
"""

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from llm_helper import get_llm


@tool
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}! Welcome!"


@tool
def farewell(name: str) -> str:
    """Say goodbye to someone."""
    return f"Goodbye, {name}! See you soon!"


@tool
def translate_greeting(text: str, language: str) -> str:
    """Translate a greeting into another language."""
    return f"[{language}] {text}"


# 1 + 2. The whole of lesson 06, in one call.
agent = create_react_agent(
    model=get_llm(model="gpt-4o"),
    tools=[greet, farewell, translate_greeting],
    prompt="You are a greeting assistant. Use the tools to greet, translate and "
           "say goodbye. Do not do any of it yourself.",
)


if __name__ == "__main__":
    # 3. Same interface as a graph you built yourself.
    result = agent.invoke({
        "messages": [HumanMessage(
            content="Greet Shubham, translate the greeting to Spanish, then say goodbye."
        )]
    })

    rounds = 0
    for msg in result["messages"]:
        if getattr(msg, "tool_calls", None):
            rounds += 1
            for tc in msg.tool_calls:
                print(f"  reason -> {tc['name']}({tc['args']})")
        elif getattr(msg, "name", None):
            print(f"  act    <- {msg.content}")
        elif type(msg).__name__ == "AIMessage":
            print(f"\nanswer: {msg.content[:200]}")

    print(f"\n{rounds} reason/act rounds, then prose. Nobody wired that loop.")

# Exercises:
# 1. Print agent.get_graph().draw_mermaid() and compare it with lesson 06's.
#    They are the same graph.
# 2. Drop the "Do not do any of it yourself" line. The model often answers
#    from memory instead of calling tools -- the prompt is what forces it.
# 3. Ask for something no tool covers ("what is the weather?"). Watch it
#    answer in prose, which is the END branch of the same loop.
# 4. Now try to log every tool result to a file. You cannot, without
#    replacing the prebuilt with lesson 06's graph -- that is the trade.
