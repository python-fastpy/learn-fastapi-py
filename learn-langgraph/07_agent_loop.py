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

  This is the same Reason -> Act -> Observe loop that your backend
  uses in langgraph_mcp_orchestrator.py!

** Requires .env with orchestrator credentials **

Run:  uv run python 07_agent_loop.py
"""

from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from llm_helper import get_llm


# ── Tools for the agent ──────────────────────────────────────────────

@tool
def search_archive(query: str, max_results: int = 3) -> str:
    """Search the Reuters text archive for articles matching a query."""
    articles = [
        {"title": "Fed Holds Rates Steady", "date": "2024-12-18", "snippet": "The Federal Reserve kept rates unchanged..."},
        {"title": "Markets Rally on Rate Pause", "date": "2024-12-19", "snippet": "Global markets surged following..."},
        {"title": "Bond Yields Drop Sharply", "date": "2024-12-20", "snippet": "Treasury yields fell across the curve..."},
    ]
    return "\n".join(
        f"- [{a['date']}] {a['title']}: {a['snippet']}"
        for a in articles[:max_results]
    )


@tool
def get_market_data(index: str) -> str:
    """Get current data for a market index (e.g., S&P500, NASDAQ, FTSE)."""
    data = {
        "S&P500": "5,930.85 (+1.2%)",
        "NASDAQ": "19,752.30 (+1.5%)",
        "FTSE": "8,105.40 (+0.3%)",
        "DAX": "20,400.15 (+0.8%)",
    }
    return data.get(index, f"No data for index: {index}")


@tool
def calculate_change(old_value: float, new_value: float) -> str:
    """Calculate the percentage change between two values."""
    change = ((new_value - old_value) / old_value) * 100
    return f"{change:+.2f}%"


# ── Create the agent ─────────────────────────────────────────────────
# create_react_agent builds the full ReAct loop automatically:
#   LLM → tool call? → execute tool → back to LLM → done?

llm = get_llm(model="gpt-4o")

agent = create_react_agent(
    model=llm,
    tools=[search_archive, get_market_data, calculate_change],
    prompt="You are a Reuters financial analyst assistant. "
           "Use the available tools to research and answer questions. "
           "Always cite your sources when using archive search results.",
)


if __name__ == "__main__":
    print("=== Graph Diagram (Mermaid) ===")
    print(agent.get_graph().draw_mermaid())
    print()

    result = agent.invoke({
        "messages": [
            HumanMessage(
                content="What's happening with the S&P 500 and NASDAQ today? "
                        "Also find any recent articles about the Fed."
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
    # create_react_agent handles the full loop:
    #   1. LLM reasons about what to do
    #   2. LLM calls one or more tools
    #   3. Tool results feed back to LLM
    #   4. LLM either calls more tools or gives a final answer
    #
    # This is essentially what your backend's orchestrator does with
    # MCP tools — same pattern, different tool source.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a `draft_headline` tool that takes a topic and returns
    #    a Reuters-style headline
    # 2. Ask the agent: "Research the Fed's latest decision and draft
    #    a headline about it"
    # 3. Watch the agent use search_archive THEN draft_headline
