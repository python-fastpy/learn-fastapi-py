"""Lesson 01 -- Hello CopilotKit: Your First AI Chat Backend
=============================================================

WHY THIS MATTERS:
  CopilotKit is the React framework that powers the Reuters AI Assistant
  chat UI. But the chat UI needs a backend to talk to. This lesson builds
  the simplest possible backend — a FastAPI server with a single CopilotKit
  endpoint that connects to an LLM.

  Once this is running, any CopilotKit React app can connect to it and
  start chatting with the AI.

WHAT YOU'LL LEARN:
  1. Create a FastAPI app with CopilotKit's LangGraph integration
  2. Use create_react_agent to build a simple chat agent
  3. Mount it at /copilotkit using add_langgraph_fastapi_endpoint
  4. Add CORS so the React frontend can connect from a different port

Concepts:
  - CopilotKit: React framework for AI chat UIs
  - AG-UI (Agent-GUI) protocol: how CopilotKit frontend talks to backends
  - LangGraphAGUIAgent: wraps a LangGraph agent for CopilotKit's protocol
  - add_langgraph_fastapi_endpoint: mounts the agent on a FastAPI route
  - CopilotKitMiddleware: enables frontend features (actions, context, etc.)
  - CORS: allows the React dev server (port 5173) to call the backend (port 8000)

Flow:
  +-------------------+      POST /copilotkit      +------------------+
  | React Frontend    | =========================> | FastAPI Backend   |
  | (port 5173)       |                            | (port 8000)      |
  | CopilotKit UI     | <======SSE================ |                  |
  +-------------------+      streamed response     | LangGraph Agent  |
                                                   |       |          |
                                                   |       v          |
                                                   |   OpenAI API     |
                                                   +------------------+

Run:  uv run python 01_hello_copilotkit.py

EXPECTED OUTPUT:
  INFO:     Uvicorn running on http://0.0.0.0:8000
  INFO:     Application startup complete.

  Then open the frontend (cd frontend && npm run dev) and chat!
  Or test with curl:
    curl http://localhost:8000/health

USED IN REUTERS:
  reuters-assistant_backend/src/routers/copilotkit_rest.py
    — The production CopilotKit endpoint that LEON connects to
  reuters-assistant_backend/src/app.py
    — FastAPI app factory with CORS, auth middleware, and routing
"""

import os
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# =================================================================
# STEP 1: LOAD ENVIRONMENT
# =================================================================
# We only need OPENAI_API_KEY — much simpler than the production
# backend which needs Azure AD, DynamoDB, and MCP server configs.

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("ERROR: Set OPENAI_API_KEY in your .env file")
    print("  cp .env.example .env  # then add your key")
    exit(1)


# =================================================================
# STEP 2: CREATE THE LANGGRAPH AGENT
# =================================================================
# create_react_agent builds a LangGraph graph that:
#   1. Takes user messages
#   2. Sends them to the LLM
#   3. Returns the response
#   4. Can call tools if any are provided (none here)
#
# CopilotKitMiddleware() enables the frontend to send:
#   - useCopilotReadable context (page data)
#   - useCopilotAction definitions (frontend tools)
#   - System instructions from CopilotChat

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from copilotkit import CopilotKitMiddleware

agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4o", temperature=0.3),
    tools=[],
    prompt="You are a helpful assistant. Be concise and friendly.",
    middleware=[CopilotKitMiddleware()],
)


# =================================================================
# STEP 3: CREATE THE FASTAPI APP
# =================================================================
# Add CORS so the React frontend (port 5173) can call us (port 8000).
# In production, Reuters uses specific allowed origins — we allow all
# for local development.

app = FastAPI(title="Learn CopilotKit - Lesson 01")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =================================================================
# STEP 4: MOUNT THE COPILOTKIT ENDPOINT
# =================================================================
# add_langgraph_fastapi_endpoint creates a POST route that:
#   1. Accepts CopilotKit's AG-UI protocol requests
#   2. Runs the LangGraph agent
#   3. Streams the response back as SSE events
#
# The frontend connects to this via:
#   <CopilotKit url="http://localhost:8000/copilotkit">

from copilotkit import LangGraphAGUIAgent
from ag_ui_langgraph import add_langgraph_fastapi_endpoint

add_langgraph_fastapi_endpoint(
    app=app,
    agent=LangGraphAGUIAgent(
        name="assistant",
        description="A helpful chat assistant",
        graph=agent,
    ),
    path="/copilotkit",
)


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "lesson": "01_hello_copilotkit"}


# =================================================================
# STEP 5: RUN THE SERVER
# =================================================================

if __name__ == "__main__":
    print("\n  Lesson 01: Hello CopilotKit")
    print("  ===========================")
    print("  Backend running at:  http://localhost:8000")
    print("  Health check:        http://localhost:8000/health")
    print("  CopilotKit endpoint: POST http://localhost:8000/copilotkit")
    print("\n  To use with the frontend:")
    print("    cd frontend && npm install && npm run dev")
    print("    Then open http://localhost:5173 and select 'Basic Chat'\n")

    uvicorn.run(
        "01_hello_copilotkit:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

    # -- Exercise ---------------------------------------------------------
    # 1. Start this server, then curl http://localhost:8000/health
    # 2. Change the system prompt to "You are a pirate" and restart
    # 3. Start the frontend and send a message — see it stream back
    # 4. Look at the terminal — you'll see each request come in
