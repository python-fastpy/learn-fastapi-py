"""Lesson 07 — Agent Loop (ReAct Pattern)
=========================================

WHY THIS MATTERS:
  In lesson 06 you built the LLM ↔ tool loop by hand — two nodes,
  a conditional edge, and a routing function. That's useful to understand,
  but in practice you'd do it for every agent you build. LangGraph's
  create_react_agent does all of that in one call. This is the pattern
  your production backend uses: give the agent tools and a prompt, and
  it figures out the order of calls on its own.

  The "ReAct" pattern (Reason + Act) means the agent:
    1. REASONS about what to do next  (reads the conversation so far)
    2. ACTS by calling a tool          (greet, translate, farewell)
    3. OBSERVES the result             (tool output comes back as a message)
    4. REPEATS until it can answer     (no more tool_calls → done)

  This is how the production assistant handles multi-step requests like
  "draft a story, validate the RIC, then generate a bulletin" — the LLM
  chains tools in the right order without anyone hard-coding the sequence.

WHAT YOU'LL LEARN:
  1. create_react_agent: builds the full LLM ↔ tool loop in one call
  2. How the ReAct loop decides tool order automatically
  3. System prompts to steer the agent's behavior
  4. How this replaces the manual graph you built in lesson 06
  5. The agent decides when to stop (no more tool_calls = final answer)

Lesson 06 vs Lesson 07 — what's different:

  │                    │ Lesson 06 (Tool Calling)       │ Lesson 07 (Agent Loop)       │
  │────────────────────│───────────────────────────────│──────────────────────────────│
  │ What you build     │ The loop manually              │ The loop is prebuilt         │
  │ Lines of code      │ ~15 lines of graph setup       │ 1 function call              │
  │ Same result?       │ Yes                            │ Yes                          │
  │ Customizable?      │ Fully — add extra nodes,       │ Limited — standard ReAct     │
  │                    │ custom routing, max-call limits │ only                         │
  │ Production use     │ langgraph_mcp_orchestrator.py   │ create_agent_orchestrator.py │
  │                    │ (needs interrupts, checkpoints) │ (simpler PoC)                │

  When to use which:
    - create_react_agent: standard agent, no custom logic needed
    - Manual graph (06): need interrupt handling, validation nodes,
      error routing, or DynamoDB checkpointing

  Lesson 06 teaches how the engine works. Lesson 07 gives you the shortcut.

Concepts:
  - create_react_agent(model, tools, prompt): prebuilt ReAct agent
  - ReAct loop: reason → act → observe → repeat
  - prompt parameter: system message that shapes how the agent behaves
  - The graph built by create_react_agent is identical to lesson 06's
    manual graph — same nodes, same conditional edge, same loop

Graph (built automatically by create_react_agent):

  +-------+     +-------+     has tool_calls?     +-------+
  | START | --> | agent | ----------------------> | tools |
  +-------+     +-------+        YES              +-------+
                   ^                                  |
                   |       (loop back with results)   |
                   +----------------------------------+
                   |
                   |  NO tool_calls (agent is done)
                   v
                +-----+
                | END |
                +-----+

  For "Greet Alice, translate to Spanish, say goodbye":
    Loop 1: agent → calls greet("Alice")        → tools → agent
    Loop 2: agent → calls translate_greeting()   → tools → agent
    Loop 3: agent → calls farewell("Alice")      → tools → agent
    Loop 4: agent → no tool_calls, gives summary → END

  Maps to:
    langgraph_mcp_orchestrator.py  → same ReAct loop with MCP tools
    create_agent_orchestrator.py   → uses create_react_agent directly
    story-drafting tools           → the tools the production agent calls

PREREQUISITES: Lesson 06 (tool calling — the manual version of this loop)

** Requires .env with orchestrator credentials **

Run:  uv run python 07_agent_loop.py

EXPECTED OUTPUT:
  === Graph Diagram (Mermaid) ===
  (mermaid graph text)

  === Agent Execution ===

  [Tool Call] greet({"name": "Alice"})
  [Tool Result: greet] Hello, Alice! Welcome!...

  [Tool Call] translate_greeting({"text": "Hello, Alice! Welcome!", "language": "Spanish"})
  [Tool Result: translate_greeting] [Spanish] Hello, Alice! Welcome!...

  [Tool Call] farewell({"name": "Alice"})
  [Tool Result: farewell] Goodbye, Alice! See you soon!...

  [Agent Response]
  I've completed all three tasks: greeted Alice, translated ...
"""

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from llm_helper import get_llm


# ── Step 1: Define tools ─────────────────────────────────────────────
# Same @tool pattern as lesson 06 — the agent reads the docstring
# to know when each tool is appropriate.

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


# ── Step 2: Create the agent ─────────────────────────────────────────
# create_react_agent replaces the ENTIRE manual setup from lesson 06:
#   - No StateGraph()
#   - No add_node(), add_edge(), add_conditional_edges()
#   - No should_use_tool routing function
#   - No ToolNode
#
# It builds the same graph internally — agent node, tools node,
# conditional edge, and the loop-back edge. One function call.

llm = get_llm(model="gpt-4o")

# prompt = system message that shapes the agent's behavior.
# The agent sees this + the user message + tool schemas, and
# uses all three to decide what to do.
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

    # ── Key takeaway ─────────────────────────────────────────────────
    # Lesson 06 (manual)  vs  Lesson 07 (create_react_agent):
    #
    #   Manual (06):                  ReAct (07):
    #   ─────────────────────────     ────────────────────────
    #   StateGraph(MessagesState)     create_react_agent(
    #   add_node("llm", call_llm)         model=llm,
    #   add_node("tools", ToolNode)       tools=[...],
    #   add_conditional_edges(...)        prompt="...",
    #   add_edge("tools", "llm")     )
    #   graph.compile()
    #
    # Same graph, same loop, same result — but one function call.
    #
    # WHY USE create_react_agent:
    #   - Less boilerplate for standard ReAct agents
    #   - The production create_agent_orchestrator.py uses it directly
    #
    # WHY STILL LEARN THE MANUAL WAY (lesson 06):
    #   - Custom routing logic (e.g., max 3 tool calls, then stop)
    #   - Extra nodes (validation, logging, interrupts)
    #   - The main langgraph_mcp_orchestrator.py uses the manual approach
    #     because it needs interrupt handling and DynamoDB checkpointing
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a `personalize_greeting` tool that takes a name and a hobby,
    #    returning a greeting that mentions the hobby
    # 2. Ask the agent: "Greet Bob who loves painting, translate it to
    #    French, and say goodbye"
    # 3. Watch the agent chain personalize_greeting -> translate_greeting
    #    -> farewell automatically
