"""
Lesson 9 (LangGraph 3): Tool-Calling Agent
============================================
Goal: Build an agent that uses an LLM to decide which tools to call.

What you'll learn:
  - Binding tools to a ChatModel
  - ToolNode for automatic tool execution
  - The agent loop: LLM decides -> tool executes -> LLM summarizes
  - Connecting to TR LLM Orchestrator (Azure OpenAI)

Run:
  uv run python 03_tool_calling_agent.py

  REQUIRES: .env file with TR LLM Orchestrator credentials

Production parallel:
  This is the core pattern in langgraph_mcp_orchestrator.py — the agent
  calls the LLM, the LLM returns tool_calls, ToolNode executes them,
  results go back to the LLM for the next decision.
"""

import os
import operator
from typing import TypedDict, Annotated
from dotenv import load_dotenv

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

load_dotenv()


# --- Step 1: Define tools ---
# These are LangChain tools (not MCP tools — we'll combine them in lesson 11).
# Each tool has a docstring the LLM reads to decide when to use it.

@tool
def get_stock_price(ticker: str) -> str:
    """Get the current stock price for a given ticker symbol (e.g. AAPL, MSFT)."""
    prices = {"AAPL": 227.50, "MSFT": 415.30, "GOOGL": 178.90, "TSLA": 245.60}
    price = prices.get(ticker.upper())
    if price:
        return f"{ticker.upper()}: ${price:.2f}"
    return f"Unknown ticker: {ticker}"


@tool
def search_news(query: str) -> str:
    """Search for recent news articles about a topic. Returns headlines."""
    return f"Headlines for '{query}': 1) {query} sees major development. 2) Analysts weigh in on {query}. 3) Market reacts to {query} news."


@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression. Example: '100 * 1.05' returns '105.0'."""
    try:
        result = eval(expression)  # safe enough for learning
        return str(result)
    except Exception as e:
        return f"Error: {e}"


tools = [get_stock_price, search_news, calculate]


# --- Step 2: Create the LLM ---
# Connects to TR LLM Orchestrator (Azure OpenAI proxy)

def create_llm():
    endpoint = os.getenv("ORCHESTRATOR_ENDPOINT", "https://llmorch-ha.int.thomsonreuters.com")
    api_key = os.getenv("LEON_ORCHESTRATOR_API_KEY", "")

    if not api_key:
        print("WARNING: No API key found. Set LEON_ORCHESTRATOR_API_KEY in .env")
        print("Falling back to mock mode...\n")
        return None

    return AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-08-01-preview",
        model="gpt-4o",
        temperature=0,
    )


# --- Step 3: Define the agent state ---

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]


# --- Step 4: Build the agent graph ---

def build_agent(llm):
    # Bind tools to the LLM so it knows what's available
    llm_with_tools = llm.bind_tools(tools)

    def call_llm(state: AgentState) -> dict:
        """Call the LLM with the current message history."""
        messages = state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        """Check if the LLM wants to call more tools or is done."""
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return "end"

    # Build the graph
    graph = StateGraph(AgentState)

    graph.add_node("agent", call_llm)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "end": END},
    )
    graph.add_edge("tools", "agent")  # after tool execution, go back to LLM

    return graph.compile()


# --- Step 5: Run ---

def mock_demo():
    """Demo without LLM credentials."""
    print("=== Mock Demo (no LLM credentials) ===\n")
    print("The agent graph structure:")
    print("  START -> agent -> [tools -> agent]* -> END")
    print()
    print("In production, the loop works like this:")
    print("  1. User says: 'What is Apple stock price?'")
    print("  2. LLM decides to call get_stock_price(ticker='AAPL')")
    print("  3. ToolNode executes -> returns '$227.50'")
    print("  4. LLM sees the result -> generates response")
    print("  5. No more tool calls -> END")
    print()
    print("Set LEON_ORCHESTRATOR_API_KEY in .env to run the real agent.")


def live_demo(app):
    """Demo with real LLM."""
    queries = [
        "What is the current price of Apple stock?",
        "Search for news about Tesla and tell me the stock price too.",
        "If I bought 100 shares of MSFT at the current price, how much would that cost?",
    ]

    for query in queries:
        print(f"\n{'='*60}")
        print(f"User: {query}")
        print(f"{'='*60}")

        result = app.invoke({
            "messages": [
                SystemMessage(content="You are a helpful financial assistant. Use tools when needed."),
                HumanMessage(content=query),
            ]
        })

        # Print the conversation
        for msg in result["messages"]:
            role = msg.__class__.__name__.replace("Message", "")
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"  [Tool Call] {tc['name']}({tc['args']})")
            elif hasattr(msg, "content") and msg.content:
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                if len(content) > 200:
                    content = content[:200] + "..."
                if role not in ("Human", "System"):
                    print(f"  [{role}] {content}")


if __name__ == "__main__":
    llm = create_llm()
    if llm:
        app = build_agent(llm)
        live_demo(app)
    else:
        mock_demo()


# ============================================================
# EXERCISES:
#
# 1. Add a "get_exchange_rate" tool and ask: "How much is 100
#    shares of AAPL worth in euros?"
# 2. Add a system message that restricts the agent to only
#    answer financial questions
# 3. Print the full message history to see the tool call and
#    tool result messages in detail
# ============================================================
