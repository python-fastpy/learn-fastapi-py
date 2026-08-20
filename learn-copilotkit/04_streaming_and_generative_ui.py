"""Lesson 04 -- Streaming & Generative UI: Live Progress in the Chat
=====================================================================

WHY THIS MATTERS:
  When the AI calls a tool that takes time (generating a story, searching
  an archive), the user needs to see progress. CopilotKit has two mechanisms:

  1. render — shows live status chips (inProgress → executing → complete)
  2. renderAndWait — shows a card and PAUSES until the user responds

  Both are frontend features, but the backend drives them. This lesson
  shows the backend side: tools with deliberate delays so you can see
  the render lifecycle in action.

WHAT YOU'LL LEARN:
  1. How backend tool execution triggers frontend render states
  2. The render lifecycle: inProgress → executing → complete
  3. Tools that return structured data for rich UI display
  4. How CopilotKit streams tool calls and results as SSE events

Concepts:
  - SSE (Server-Sent Events): how CopilotKit streams responses
  - Tool execution lifecycle:
      1. LLM decides to call a tool → frontend sees "inProgress"
      2. Backend handler runs     → frontend sees "executing"
      3. Handler returns          → frontend sees "complete" with result
  - render (frontend): shows UI during tool execution, does NOT pause
  - renderAndWait (frontend): shows UI and PAUSES until user responds

Flow:
  User: "Search for Apple news"
       |
       v
  [LLM calls search_articles]
       |
  SSE: tool_call_start ──────> Frontend: render({status: "inProgress"})
       |                              Shows: "Searching..."
  [Backend handler runs]
       |
  SSE: tool_call_result ─────> Frontend: render({status: "complete"})
       |                              Shows: "Found 3 articles"
       v
  [LLM formats response]
  SSE: text_delta ───────────> Frontend: streaming text appears

Run:  uv run python 04_streaming_and_generative_ui.py

EXPECTED OUTPUT:
  INFO:     Uvicorn running on http://0.0.0.0:8000

  Pair with: frontend/src/examples/5-generative-ui.tsx
  The frontend shows color-coded status chips as tools run:
    Yellow (inProgress) → Blue (executing) → Green (complete)

USED IN REUTERS:
  @reuters/assistant-v2 → components/mcp/mcp-execution-summary.tsx
    — Shows which MCP servers were called during a response
  @reuters/assistant-v2 → components/skill-calls/skill-call-chip.tsx
    — Live status chip per tool call (loading → done)
  @reuters/assistant-v2 → hooks/useSkillCalls.ts
    — Tracks skill execution state for UI rendering
  @reuters/assistant-v2 → ProgressTracker.tsx
    — Step-by-step progress display for multi-step workflows
"""

import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: Set OPENAI_API_KEY in your .env file")
    exit(1)


# =================================================================
# STEP 1: TOOLS WITH DELIBERATE DELAYS
# =================================================================
# These tools simulate real-world latency so you can see the
# render lifecycle in the frontend. In production, the delays
# come from actual API calls (Reuters Text Archive, RMA, LLM).

from langchain_core.tools import tool


@tool
async def search_archive(query: str, date_range: str = "week") -> str:
    """Search the news archive for articles matching a query.

    Args:
        query: Search keywords
        date_range: How far back to search: 'today', 'week', 'month', 'year'
    """
    # Simulate API latency — this is where the frontend shows "Searching..."
    await asyncio.sleep(2)

    articles = [
        {"headline": f"Markets rally on {query} developments", "date": "2026-08-20"},
        {"headline": f"Analysts weigh in on {query} outlook", "date": "2026-08-19"},
        {"headline": f"{query}: A deep dive into recent trends", "date": "2026-08-18"},
    ]

    return json.dumps({
        "count": len(articles),
        "query": query,
        "date_range": date_range,
        "articles": articles,
    })


@tool
async def generate_summary(topic: str) -> str:
    """Generate a news summary for a given topic.

    Args:
        topic: The topic to summarize
    """
    # Simulate multi-step generation — longer delay
    await asyncio.sleep(3)

    return json.dumps({
        "topic": topic,
        "summary": f"Key developments in {topic}: Markets showed strong movement "
                   f"as investors reacted to new data. Analysts remain cautiously "
                   f"optimistic about near-term prospects.",
        "generated_at": datetime.now().isoformat(),
    })


@tool
async def fact_check(claim: str) -> str:
    """Check a factual claim against known data.

    Args:
        claim: The claim to verify
    """
    await asyncio.sleep(1.5)

    return json.dumps({
        "claim": claim,
        "verdict": "Plausible",
        "confidence": 0.78,
        "note": "This is a mock fact-checker for demonstration purposes.",
    })


# =================================================================
# STEP 2: CREATE AGENT
# =================================================================

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from copilotkit import CopilotKitMiddleware

TOOLS = [search_archive, generate_summary, fact_check]

agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.3),
    tools=TOOLS,
    prompt=(
        "You are a research assistant. Use your tools to help users find "
        "and analyze news. Always use the appropriate tool when asked to "
        "search, summarize, or fact-check. Explain your findings clearly."
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

app = FastAPI(title="Learn CopilotKit - Lesson 04")

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
        name="research_assistant",
        description="Research assistant with search, summary, and fact-check tools",
        graph=agent,
    ),
    path="/copilotkit",
)


@app.get("/health")
def health():
    return {"status": "ok", "lesson": "04_streaming_and_generative_ui", "tools": [t.name for t in TOOLS]}


if __name__ == "__main__":
    print("\n  Lesson 04: Streaming & Generative UI")
    print("  =====================================")
    print(f"  Tools: {[t.name for t in TOOLS]}")
    print("  Each tool has a deliberate delay so you can see the render lifecycle.")
    print("\n  Pair with: frontend/src/examples/5-generative-ui.tsx")
    print("\n  Try asking:")
    print('    "Search the archive for Apple earnings"  → 2s delay, shows search chip')
    print('    "Summarize the Tesla situation"          → 3s delay, shows generation progress')
    print('    "Fact-check: Apple revenue exceeded $90B"→ 1.5s delay, shows verdict\n')

    uvicorn.run(
        "04_streaming_and_generative_ui:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

    # -- Exercise ---------------------------------------------------------
    # 1. Change the delay in search_archive to 5s — watch the chip stay yellow longer
    # 2. Add a tool that returns a list of images (as URLs) — can the frontend display them?
    # 3. Make generate_summary return partial results (simulate multi-step generation)
    # 4. Open 5-generative-ui.tsx and watch the color transitions
