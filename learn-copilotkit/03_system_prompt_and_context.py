"""Lesson 03 -- System Prompts & Frontend Context
==================================================

WHY THIS MATTERS:
  In the Reuters AI Assistant, the chat knows what story you're editing.
  If you're on an Apple earnings story, the AI already knows the headline,
  slug, RIC, and body text. This happens through two mechanisms:

  1. System prompt: tells the agent its role and rules
  2. Frontend context: useCopilotReadable sends page data with every message

  This lesson shows how both work from the backend's perspective.

WHAT YOU'LL LEARN:
  1. System prompts shape agent behavior (tone, rules, capabilities)
  2. useCopilotReadable on the frontend sends context with each message
  3. CopilotKitMiddleware makes that context available to the agent
  4. The agent sees both the system prompt AND the frontend context

Concepts:
  - System prompt: persistent instructions to the LLM
  - Frontend context: dynamic data from useCopilotReadable
  - CopilotKitMiddleware: bridges frontend context into the agent
  - The LLM sees: system prompt + frontend context + user messages

Flow:
  Frontend (React):
    useCopilotReadable({
      description: "Current story",        <--- sent with every message
      value: { headline: "...", ric: "..." }
    })

  What the LLM sees:
    +--------------------------------------------------+
    | SYSTEM: You are a newsroom assistant...           |  <-- system prompt
    | SYSTEM: Current story: { headline: "...", ... }   |  <-- frontend context
    | USER: What story am I editing?                    |  <-- user message
    +--------------------------------------------------+

Run:  uv run python 03_system_prompt_and_context.py

EXPECTED OUTPUT:
  INFO:     Uvicorn running on http://0.0.0.0:8000

  Pair with frontend example 2-page-context.tsx:
    - Select a story in the dropdown
    - Ask "What story am I editing?" → AI describes the story it sees

USED IN REUTERS:
  lynx_leon/src/components/reuter-ai-assistant-v2/reuter-ai-assistant-v2-page-context.tsx
    — Sends story/alert data as externalContext to the AI
  reuters-assistant_backend/src/services/langgraph_mcp_orchestrator.py
    — System prompt includes user context, skill instructions, workflow steps
  @reuters/assistant-v2 → ReutersAssistantAI component
    — externalContext prop passes page data through CopilotKit's protocol
"""

import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: Set OPENAI_API_KEY in your .env file")
    exit(1)


# =================================================================
# STEP 1: DEFINE A RICH SYSTEM PROMPT
# =================================================================
# System prompts shape the agent's personality and rules.
# In production, Reuters builds the system prompt dynamically based on:
#   - The user's role and permissions
#   - Available skills/workflows
#   - Current page context type (story vs alert vs blank)
#
# Here we use a static prompt that mimics a newsroom assistant.

SYSTEM_PROMPT = """You are a newsroom assistant helping journalists edit stories.

RULES:
- Be concise and professional — journalists are on deadline
- When you can see a story (via context), reference it naturally
- If asked to edit, describe what you would change
- Never invent facts — only work with what's in the context
- For headlines, follow AP/Reuters style: short, active voice, present tense

CAPABILITIES:
- You can see the current story data (headline, body, RIC, slug)
- You can analyze story quality (tone, length, clarity)
- You can suggest edits to headlines and body text
- You can look up related information using available tools"""


# =================================================================
# STEP 2: ADD TOOLS THAT USE CONTEXT
# =================================================================
# These tools work with whatever story data the frontend sends.

from langchain_core.tools import tool


@tool
def analyze_headline(headline: str) -> str:
    """Analyze a headline for Reuters style compliance.

    Args:
        headline: The headline text to analyze
    """
    issues = []
    if len(headline) > 80:
        issues.append(f"Too long ({len(headline)} chars, max 80)")
    if headline.endswith("."):
        issues.append("Headlines don't end with periods")
    if headline == headline.upper():
        issues.append("Don't use ALL CAPS")
    if not headline[0].isupper():
        issues.append("Headline should start with capital letter")

    if not issues:
        return f"Headline looks good! ({len(headline)} chars)"
    return "Issues found:\n" + "\n".join(f"  - {i}" for i in issues)


@tool
def word_count(text: str) -> str:
    """Count words and characters in text.

    Args:
        text: The text to analyze
    """
    words = len(text.split())
    chars = len(text)
    sentences = text.count(".") + text.count("!") + text.count("?")
    return f"Words: {words} | Characters: {chars} | Sentences: {sentences}"


# =================================================================
# STEP 3: CREATE AGENT WITH SYSTEM PROMPT
# =================================================================
# The system prompt is passed to create_react_agent via the `prompt`
# parameter. CopilotKitMiddleware ensures that frontend context
# (from useCopilotReadable) is also injected into the conversation.

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from copilotkit import CopilotKitMiddleware

agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.3),
    tools=[analyze_headline, word_count],
    prompt=SYSTEM_PROMPT,
    middleware=[CopilotKitMiddleware()],
)


# =================================================================
# STEP 4: MOUNT ON FASTAPI
# =================================================================

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from copilotkit import LangGraphAGUIAgent
from ag_ui_langgraph import add_langgraph_fastapi_endpoint

app = FastAPI(title="Learn CopilotKit - Lesson 03")

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
        name="newsroom_assistant",
        description="A newsroom assistant that knows about the current story context",
        graph=agent,
    ),
    path="/copilotkit",
)


@app.get("/health")
def health():
    return {"status": "ok", "lesson": "03_system_prompt_and_context"}


if __name__ == "__main__":
    print("\n  Lesson 03: System Prompts & Frontend Context")
    print("  =============================================")
    print("  This backend expects to receive page context from the frontend.")
    print("  Pair with: frontend/src/examples/2-page-context.tsx")
    print("\n  Try asking:")
    print('    "What story am I editing?"     → AI reads the frontend context')
    print('    "Analyze the headline"         → AI calls analyze_headline tool')
    print('    "How long is the body?"        → AI calls word_count tool')
    print()

    uvicorn.run(
        "03_system_prompt_and_context:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

    # -- Exercise ---------------------------------------------------------
    # 1. Change the system prompt to make the AI respond in French
    # 2. Add a rule: "Never use the word 'very'" — test if it follows it
    # 3. Open 2-page-context.tsx in the frontend, switch stories, and ask
    #    "What story am I editing?" — notice the AI sees the new context
    # 4. Add a new tool: suggest_headline that generates 3 alternative headlines
