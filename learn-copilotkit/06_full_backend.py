"""Lesson 06 -- Full Backend: Everything Together
==================================================

WHY THIS MATTERS:
  This is the capstone lesson — a complete backend that works with ALL 6
  frontend examples. It combines:

  1. System prompt (newsroom assistant persona)
  2. Backend tools (search, analyze, generate)
  3. CopilotKitMiddleware (frontend context, actions, interrupts)
  4. CORS (cross-origin access from the React dev server)

  This is a simplified version of what the Reuters production backend
  (copilotkit_rest.py + langgraph_mcp_orchestrator.py) does.

WHAT YOU'LL LEARN:
  1. How all the pieces from lessons 01-05 fit together
  2. Frontend actions (useCopilotAction) + backend tools work side by side
  3. The complete data flow: user message → agent → tools → response
  4. How this maps to the Reuters production architecture

Concepts:
  - Complete CopilotKit backend: system prompt + tools + middleware + CORS
  - Frontend actions run in the browser, backend tools run on the server
  - The LLM sees BOTH and chooses the right one for each task
  - In production: this is split across multiple MCP servers (skills)

Flow:
  +-------------------+                    +------------------+
  | React Frontend    |  POST /copilotkit  | FastAPI Backend   |
  |                   | =================> |                  |
  | useCopilotReadable|     messages +     | System Prompt    |
  |   (story context) |     context  +     | + Tools:         |
  |                   |     actions        |   search_articles|
  | useCopilotAction  |                    |   generate_draft |
  |   update_headline | <===SSE=========== |   analyze_text   |
  |   review_draft    |     tool calls +   |                  |
  |   search_related  |     text deltas    | CopilotKit       |
  |                   |                    | Middleware        |
  +-------------------+                    +------------------+
                                                    |
                                                    v
                                              OpenAI GPT-4o

  When the LLM calls "update_headline":
    → CopilotKit routes it to the FRONTEND handler (useCopilotAction)
    → The handler runs in the browser and updates React state

  When the LLM calls "search_articles":
    → CopilotKit routes it to the BACKEND handler (@tool)
    → The handler runs on the server and returns results

Run:  uv run python 06_full_backend.py

EXPECTED OUTPUT:
  INFO:     Uvicorn running on http://0.0.0.0:8000

  Works with ALL frontend examples:
    1-basic-chat.tsx     → basic chat
    2-page-context.tsx   → AI reads story context
    3-chat-actions.tsx   → AI calls frontend actions
    4-interrupts.tsx     → AI triggers renderAndWait cards
    5-generative-ui.tsx  → AI shows progress chips
    6-full-app.tsx       → all of the above combined

USED IN REUTERS:
  reuters-assistant_backend/src/routers/copilotkit_rest.py
    — Production CopilotKit REST endpoint with SSE streaming
  reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py
    — LangGraph StateGraph with DynamoDB checkpointing, interrupt support
  reuters-assistant_backend/src/services/mcp_protocol.py
    — MCP protocol for calling remote skill servers
  reuters-assistant_backend/src/app.py
    — FastAPI app with CORS, auth, routing, WebSocket progress
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
# STEP 1: DEFINE BACKEND TOOLS
# =================================================================
# These run on the server. The frontend also registers its own actions
# (useCopilotAction) — the LLM sees both sets and picks appropriately.

from langchain_core.tools import tool


@tool
async def search_articles(query: str, max_results: int = 5) -> str:
    """Search for news articles matching a query. Use when the user asks
    to find, search, or look up related stories.

    Args:
        query: Search keywords
        max_results: Maximum results to return
    """
    await asyncio.sleep(1.5)
    articles = [
        {"headline": f"Markets respond to {query} developments", "date": "2026-08-20"},
        {"headline": f"Analysis: {query} impact on global markets", "date": "2026-08-19"},
        {"headline": f"UPDATE: New data emerges on {query}", "date": "2026-08-18"},
    ]
    return json.dumps({
        "count": len(articles),
        "articles": articles[:max_results],
    })


@tool
async def generate_draft(topic: str, style: str = "spot") -> str:
    """Generate a news draft on a topic. Use when asked to write, draft,
    or create a story.

    Args:
        topic: What to write about
        style: Story style: 'spot' (short), 'feature' (long), 'buzz' (analysis)
    """
    await asyncio.sleep(2)
    templates = {
        "spot": f"{topic.upper()} - [City] - [brief factual lede about {topic}], sources said on [day].\n\nThe development comes as [context paragraph].\n\n(Reporting by [name]; Editing by [name])",
        "feature": f"FEATURE-{topic}\n\n[City] - In a development that could reshape [industry], {topic.lower()} has emerged as a key focus.\n\n[3-4 detailed paragraphs would follow]\n\n(Reporting by [name])",
        "buzz": f"BUZZ - {topic}\n\n** {topic} shows significant movement\n** Key data points: [metrics]\n** Analysts say: [consensus view]\n** Context: [background]\n\n(Reporting by [name])",
    }
    return templates.get(style, templates["spot"])


@tool
def analyze_text(text: str) -> str:
    """Analyze text for word count, readability, and style issues.

    Args:
        text: The text to analyze
    """
    words = len(text.split())
    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_words_per_sentence = words / sentences

    issues = []
    if avg_words_per_sentence > 25:
        issues.append(f"Long sentences (avg {avg_words_per_sentence:.0f} words — aim for <25)")
    if "!" in text:
        issues.append("Avoid exclamation marks in news copy")
    if words > 500:
        issues.append(f"Consider trimming — {words} words is long for a spot story")

    result = {
        "words": words,
        "sentences": sentences,
        "avg_words_per_sentence": round(avg_words_per_sentence, 1),
        "issues": issues if issues else ["No issues found — clean copy"],
    }
    return json.dumps(result)


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S (%A)")


# =================================================================
# STEP 2: SYSTEM PROMPT
# =================================================================
# This prompt shapes the agent for all 6 frontend examples.

SYSTEM_PROMPT = """You are a Reuters newsroom AI assistant.

CAPABILITIES:
- See the current story data (headline, body, RIC) via frontend context
- Search for related articles (search_articles tool)
- Generate news drafts (generate_draft tool)
- Analyze text quality (analyze_text tool)
- Update story fields via frontend actions (when available)

RULES:
- Be concise and professional — journalists are on deadline
- Reference the current story data when you can see it
- For major changes, generate a draft for review (don't just describe changes)
- When frontend actions are available (update_headline, review_and_apply_draft),
  use them to make actual edits to the story
- Use search_articles when asked to find related content
- Use analyze_text when asked about story quality or length

INTERACTION STYLE:
- Short, actionable responses
- Use bullet points for lists
- Reference specific data from the story context
- After using a tool, explain what you found or did"""


# =================================================================
# STEP 3: CREATE AGENT WITH ALL TOOLS + MIDDLEWARE
# =================================================================

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from copilotkit import CopilotKitMiddleware

TOOLS = [search_articles, generate_draft, analyze_text, get_current_time]

agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.3),
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
    middleware=[CopilotKitMiddleware()],
)


# =================================================================
# STEP 4: MOUNT ON FASTAPI WITH EVERYTHING
# =================================================================

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from copilotkit import LangGraphAGUIAgent
from ag_ui_langgraph import add_langgraph_fastapi_endpoint

app = FastAPI(title="Learn CopilotKit - Lesson 06 (Full Backend)")

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
        name="reuters_assistant",
        description="Full-featured newsroom assistant with search, drafting, and analysis tools",
        graph=agent,
    ),
    path="/copilotkit",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "lesson": "06_full_backend",
        "tools": [t.name for t in TOOLS],
        "works_with": [
            "1-basic-chat.tsx",
            "2-page-context.tsx",
            "3-chat-actions.tsx",
            "4-interrupts.tsx",
            "5-generative-ui.tsx",
            "6-full-app.tsx",
        ],
    }


if __name__ == "__main__":
    print("\n  Lesson 06: Full Backend (Capstone)")
    print("  ====================================")
    print(f"  Backend tools: {[t.name for t in TOOLS]}")
    print("  Frontend actions are registered by the React app (useCopilotAction)")
    print("  The LLM sees both sets and picks the right one for each task.")
    print("\n  Works with ALL 6 frontend examples!")
    print("  Start the frontend:  cd frontend && npm run dev")
    print("\n  Try each example:")
    print("    1-basic-chat    → just chat")
    print("    2-page-context  → AI sees story data")
    print("    3-chat-actions  → AI updates headline/body via frontend actions")
    print("    4-interrupts    → AI shows review card, waits for approval")
    print("    5-generative-ui → AI shows progress chips during tool calls")
    print("    6-full-app      → everything combined")
    print()

    uvicorn.run(
        "06_full_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

    # -- Exercise ---------------------------------------------------------
    # 1. Start this backend + the frontend, try each example
    # 2. In 6-full-app, try: "Rewrite the story in a more formal style"
    #    → Watch the review card appear (renderAndWait interrupt)
    # 3. Try: "Search for related Apple stories" → watch the search chip
    # 4. Add a new backend tool that the full-app example can use
    # 5. Compare this file with reuters-assistant_backend/src/app.py
    #    — What's different? (auth, DynamoDB, MCP, multi-tenant, etc.)
