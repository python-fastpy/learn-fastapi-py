"""Lesson 02 -- Backend Tools: Give Your Agent Superpowers
==========================================================

WHY THIS MATTERS:
  A chat agent that can only talk is limited. Tools let the agent DO things:
  look up data, call APIs, run calculations. In production, Reuters MCP
  skill servers (story-drafting, text-archive) expose tools that the agent
  can call to generate stories, search archives, and validate RICs.

  This lesson teaches how to define tools on the backend that the agent
  can call during a conversation.

WHAT YOU'LL LEARN:
  1. Define Python functions as tools using @tool decorator
  2. Tools become available to the LLM alongside any frontend actions
  3. The LLM decides when to call a tool based on the user's message
  4. Tool results are sent back to the LLM, which formats the response

Concepts:
  - @tool decorator: marks a function as callable by the LLM
  - Tool schema: name, description, and parameter types (auto-generated)
  - Backend tools vs frontend actions:
      Backend tools (@tool):              Run on the server (Python)
      Frontend actions (useCopilotAction): Run in the browser (JavaScript)
  - Both appear as "tools" to the LLM — it picks whichever fits

Flow:
  User: "What time is it?"
       |
       v
  +------------+  "call get_current_time"  +------------------+
  | LLM (GPT)  | -----------------------> | @tool             |
  |            | <----------------------- | get_current_time() |
  |            |  "2026-08-20 14:30:00"   +------------------+
  |            |
  | "It's 2:30 PM"
       |
       v
  User sees: "It's 2:30 PM"

Run:  uv run python 02_backend_with_tools.py

EXPECTED OUTPUT:
  INFO:     Uvicorn running on http://0.0.0.0:8000
  INFO:     Application startup complete.

  Try in the chat:
    "What time is it?"          → agent calls get_current_time
    "Calculate 15% tip on $85"  → agent calls calculate_tip
    "Search for Apple news"     → agent calls search_articles

USED IN REUTERS:
  sphinx_leon-assistant-skills/story-drafting/src/tools/
    — Production tools: generate_spot_story, generate_news_bulletin, etc.
  sphinx_leon-assistant-skills/text-archive/src/tools/
    — search_reuters_text_archive tool
  sphinx_leon-assistant-skills/shared/src/shared/rma/rma_client.py
    — validate_ric, search_rics tools
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: Set OPENAI_API_KEY in your .env file")
    exit(1)


# =================================================================
# STEP 1: DEFINE TOOLS
# =================================================================
# Each @tool function becomes a tool the LLM can call.
# The docstring becomes the tool description the LLM sees.
# Type hints become the parameter schema.

from langchain_core.tools import tool


@tool
def get_current_time() -> str:
    """Get the current date and time. Use when the user asks what time it is."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S (%A)")


@tool
def calculate_tip(bill_amount: float, tip_percentage: float = 18.0) -> str:
    """Calculate tip amount and total bill.

    Args:
        bill_amount: The bill total before tip
        tip_percentage: Tip percentage (default 18%)
    """
    tip = bill_amount * (tip_percentage / 100)
    total = bill_amount + tip
    return f"Bill: ${bill_amount:.2f} | Tip ({tip_percentage}%): ${tip:.2f} | Total: ${total:.2f}"


@tool
def search_articles(query: str, max_results: int = 5) -> str:
    """Search for news articles matching a query.

    Args:
        query: Search keywords
        max_results: Maximum number of results to return (default 5)
    """
    # In production, this would call the Reuters Text Archive API.
    # Here we return mock data to keep the lesson self-contained.
    mock_articles = [
        {"headline": f"Breaking: {query} sees major developments", "date": "2026-08-20", "source": "Reuters"},
        {"headline": f"Analysis: What {query} means for markets", "date": "2026-08-19", "source": "Reuters"},
        {"headline": f"Update: {query} continues to drive investor interest", "date": "2026-08-18", "source": "Reuters"},
    ]
    results = mock_articles[:max_results]
    lines = [f"Found {len(results)} articles:"]
    for i, a in enumerate(results, 1):
        lines.append(f"  {i}. [{a['date']}] {a['headline']} ({a['source']})")
    return "\n".join(lines)


# =================================================================
# STEP 2: CREATE AGENT WITH TOOLS
# =================================================================
# Pass the tools list to create_react_agent. The agent will see these
# tools alongside any frontend actions (useCopilotAction) and can
# call whichever is appropriate.

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from copilotkit import CopilotKitMiddleware

TOOLS = [get_current_time, calculate_tip, search_articles]

agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.3),
    tools=TOOLS,
    prompt=(
        "You are a helpful assistant with access to tools. "
        "Use tools when they help answer the user's question. "
        "Always explain what you found after using a tool."
    ),
    middleware=[CopilotKitMiddleware()],
)


# =================================================================
# STEP 3: MOUNT ON FASTAPI
# =================================================================

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from copilotkit import LangGraphAGUIAgent
from ag_ui_langgraph import add_langgraph_fastapi_endpoint

app = FastAPI(title="Learn CopilotKit - Lesson 02")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(
        name="assistant",
        description="A helpful assistant with tools for time, tips, and article search",
        graph=agent,
    ),
    path="/copilotkit",
)


@app.get("/health")
def health():
    return {"status": "ok", "lesson": "02_backend_with_tools", "tools": [t.name for t in TOOLS]}


if __name__ == "__main__":
    print("\n  Lesson 02: Backend Tools")
    print("  ========================")
    print(f"  Tools registered: {[t.name for t in TOOLS]}")
    print("  Backend running at: http://localhost:8000")
    print("\n  Try asking:")
    print('    "What time is it?"')
    print('    "Calculate 20% tip on $120"')
    print('    "Search for Apple earnings news"\n')

    uvicorn.run(
        "02_backend_with_tools:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

    # -- Exercise ---------------------------------------------------------
    # 1. Add a tool that converts temperatures between Celsius and Fahrenheit
    # 2. Add a tool that generates a random headline (use random.choice)
    # 3. Watch the terminal — you'll see tool calls logged as the agent uses them
    # 4. Try asking a question that needs TWO tools — does the agent chain them?
