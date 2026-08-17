"""Lesson 07 — Agent Loop (ReAct Pattern)
=========================================
Concepts:
  - The ReAct loop: Reason -> Act -> Observe -> repeat
  - create_react_agent: LangGraph's prebuilt agent
  - How the agent decides when to stop calling tools
  - System prompts to control agent behavior

Graph (built automatically by create_react_agent):
  +-------+     +-------+
  | START | --> | agent |
  +-------+     +-------+
                   |
            has tool_calls?
              /         \\
             v           v
        +-------+    +-----+
        | tools |    | END |
        +-------+    +-----+
             |
             +-----> agent
           (loop back with tool results)

  The agent reasons about the request, calls greet/farewell/translate
  tools as needed, observes results, and loops until it has a final answer.

** Requires .env with orchestrator credentials **

Run:  uv run python 07_agent_loop.py

Expected output:
  [Tool Call] greet({"name": "Alice"})
  [Tool Result: greet] Hello, Alice! Welcome!
  [Tool Call] translate_greeting({"text": "Hello, Alice! Welcome!", "language": "Spanish"})
  [Tool Result: translate_greeting] [Spanish] Hello, Alice! Welcome!
  [Tool Call] farewell({"name": "Alice"})
  [Tool Result: farewell] Goodbye, Alice! See you soon!
  [Agent Response] ...summary of all three actions...
"""

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from llm_helper import get_llm


# -- Tools for the agent ------------------------------------------------------

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


# -- Create the agent ---------------------------------------------------------
# create_react_agent builds the full ReAct loop automatically:
#   LLM -> tool call? -> execute tool -> back to LLM -> done?

llm = get_llm(model="gpt-4o")

agent = create_react_agent(
    model=llm,
    tools=[greet, farewell, translate_greeting],
    prompt="You are a greeting assistant. "
           "Use the available tools to greet and farewell people. "
           "You can also translate greetings.",
)


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(agent.get_graph().draw_mermaid())
    print()

    result = agent.invoke({
        "messages": [
            HumanMessage(
                content="Greet Alice, translate the greeting to Spanish, "
                        "and then say goodbye to her."
            )
        ]
    })

    print("=== Agent Execution ===\n")
    for msg in result["messages"]:
        role = msg.__class__.__name__.replace("Message", "")
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"[Tool Call] {tc['name']}({tc['args']})")
        elif hasattr(msg, "name") and msg.name:
            print(f"[Tool Result: {msg.name}] {msg.content[:150]}...")
        elif role == "AI":
            print(f"\n[Agent Response]\n{msg.content[:500]}")
        else:
            print(f"[{role}] {msg.content[:150]}")
        print()

    # -- Key takeaway ----------------------------------------------------------
    # create_react_agent handles the full loop:
    #   1. LLM reasons about what to do
    #   2. LLM calls one or more tools (greet, farewell, translate_greeting)
    #   3. Tool results feed back to LLM
    #   4. LLM either calls more tools or gives a final answer
    #
    # The agent autonomously decided the order: greet first, then translate
    # the greeting, then farewell — all from a single natural-language request.
    #
    # -- Exercise --------------------------------------------------------------
    # 1. Add a `personalize_greeting` tool that takes a name and a hobby,
    #    returning a greeting that mentions the hobby
    # 2. Ask the agent: "Greet Bob who loves painting, translate it to
    #    French, and say goodbye"
    # 3. Watch the agent chain personalize_greeting -> translate_greeting
    #    -> farewell automatically
