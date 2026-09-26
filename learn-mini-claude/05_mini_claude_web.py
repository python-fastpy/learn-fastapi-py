"""Lesson 05 -- The Web UI: mini Claude in a browser
=======================================================

WHY THIS MATTERS:
  Lesson 04 gave you a terminal REPL. This wraps the *same agent* in a
  FastAPI server with a plain HTML/CSS chat page -- no React, no build
  step, no npm. One `index.html`, one `style.css`, a little vanilla JS.

  The point is how little changes: `agent_core.agent_loop()` is imported
  unchanged. A UI is a presentation layer over the loop, not a different
  kind of program. Swapping the terminal for a browser means replacing
  two functions -- how you print, and how you approve.

WHAT YOU'LL LEARN:
  1. Wrapping an agent loop in an HTTP endpoint (POST /chat)
  2. Serving a static HTML/CSS front end from FastAPI
  3. Keeping conversation state server-side, keyed by session
  4. Handling permissions without a terminal -- a UI needs a *policy*,
     since there's no one to type "y" mid-request
  5. Reporting tool calls back to the browser so the user sees what the
     agent did, not just the final answer

Concepts:
  - Static files: FastAPI serves web/ directly; no bundler involved
  - Session state: conversation lives in a server-side dict keyed by
    session id. Restart the server and it's gone -- fine for a lesson,
    swap for Redis/DynamoDB in production (see fastapi/08-session.py)
  - Permission policy vs. prompt: the CLI asks a human in real time; the
    web UI decides up front (here: allow reads + writes, refuse shell).
    A production UI would stream an approval request to the browser and
    await the click -- that's learn-mcp lesson 06's interrupt pattern.
  - Event trace: on_event collects tool calls so the response can show
    them as chips under the reply

Flow:
  browser                     FastAPI                      agent_core
  -------                     -------                      ----------
  type message  --POST /chat-->  look up session
                                 append HumanMessage
                                 agent_loop(...)  ------->  model + tools
                                                            (MCP + builtin)
                                 collect events   <-------  tool results
  render reply  <--JSON--------  {reply, events}
  + tool chips

REQUIRES CREDENTIALS: same as lesson 04 -- needs .env for a real model.

Run:  uv run python 05_mini_claude_web.py
      then open http://127.0.0.1:8100

EXPECTED STARTUP:
  MCP 'notes': 3 tools attached
  mini-claude web -- 7 tools ready
  Open http://127.0.0.1:8100
"""

import os
import sys
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import agent_core
from agent_core import (
    Tool, Usage, agent_loop, build_registry, build_system_prompt, get_model,
)

load_dotenv()

WEB_DIR = agent_core.HERE / "web"

STATE: dict = {"registry": {}, "model": None}


# Build the tool registry inside the app's lifespan, NOT in a separate
# asyncio.run() before uvicorn starts.
#
# This bit me: stdio MCP servers keep a live subprocess session bound to
# the event loop that created it. asyncio.run() closes its loop when it
# returns, so every MCP connection built there is dead by the time
# uvicorn's loop handles the first request -- and the agent reports a
# vague "connection issue" instead of anything useful.
@asynccontextmanager
async def lifespan(app: FastAPI):
    STATE["registry"] = await build_registry()
    STATE["model"] = get_model("gpt-4-1")
    print(f"mini-claude web -- {len(STATE['registry'])} tools ready")
    print("Open http://127.0.0.1:8100")
    yield


app = FastAPI(title="mini-claude", lifespan=lifespan)

# Server-side conversation state: session_id -> message list.
# In-memory, so it resets when you restart. See fastapi/08-session.py for
# the Redis/JWT alternatives when you need it to survive a restart.
SESSIONS: dict[str, list] = {}

# Cumulative token usage per session, so the UI can show a running total.
SESSION_USAGE: dict[str, Usage] = {}


# ============================================================================
# The permission policy (the interesting difference from the CLI)
# ============================================================================
# The CLI can block on input() because a human is watching the terminal.
# An HTTP handler can't -- it has to answer *now*. So a web UI needs a
# policy decided in advance, not a prompt.
#
# This one allows file writes (sandboxed to _sandbox/ anyway) but refuses
# shell commands, since those are the hardest to undo. The grown-up
# version streams an approval request to the browser and waits for a
# click -- that's exactly the interrupt/resume pattern from learn-mcp
# lesson 06 and learn-langgraph lesson 09.

BLOCKED_IN_WEB_UI = {"run_command"}


def web_approve(tool: Tool, args: dict) -> bool:
    return tool.name not in BLOCKED_IN_WEB_UI


# ============================================================================
# API
# ============================================================================

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    # Per-session instructions from the UI's "Custom instructions" panel.
    # Only applied when the session is created -- see the note below.
    system_extra: str | None = None


@app.post("/chat")
async def chat(req: ChatRequest):
    from langchain_core.messages import HumanMessage, SystemMessage

    session_id = req.session_id or str(uuid.uuid4())
    if session_id not in SESSIONS:
        # The system prompt is message[0]. You can't retroactively change
        # instructions the model has already been answering under, so a
        # new prompt means a new session -- the UI sends session_id=null
        # after you hit Apply, which lands here.
        SESSIONS[session_id] = [
            SystemMessage(content=build_system_prompt(req.system_extra or ""))
        ]
        SESSION_USAGE[session_id] = Usage()

    messages = SESSIONS[session_id]
    messages.append(HumanMessage(content=req.message))

    # Collect tool activity so the browser can show what happened.
    events: list[dict] = []

    def on_event(kind: str, data):
        if kind == "tool_call":
            events.append({"type": "call", "name": data["name"], "args": data["args"]})
        elif kind == "tool_denied":
            events.append({"type": "denied", "name": data["name"], "args": data["args"]})
        elif kind == "tool_result":
            preview = str(data["result"])
            events.append({
                "type": "result",
                "name": data["name"],
                "preview": preview[:200] + ("..." if len(preview) > 200 else ""),
            })

    turn_usage = Usage()
    try:
        reply = await agent_loop(
            STATE["model"], STATE["registry"], messages,
            approve=web_approve, on_event=on_event, usage=turn_usage,
        )
    except Exception as e:
        reply = f"Error: {type(e).__name__}: {e}"
    finally:
        # A failed turn still cost tokens -- count it either way.
        SESSION_USAGE[session_id].merge(turn_usage)

    return {
        "session_id": session_id,
        "reply": reply,
        "events": events,
        "usage": turn_usage.as_dict(),
        "session_usage": SESSION_USAGE[session_id].as_dict(),
    }


@app.get("/tools")
async def tools():
    return {
        "tools": [
            {"name": t.name, "source": t.source,
             "read_only": t.read_only, "description": t.description[:80]}
            for t in sorted(STATE["registry"].values(), key=lambda t: (t.source, t.name))
        ]
    }


@app.post("/reset")
async def reset(req: ChatRequest):
    SESSIONS.pop(req.session_id or "", None)
    SESSION_USAGE.pop(req.session_id or "", None)
    return {"ok": True}


@app.get("/prompt")
async def prompt(session_id: str = ""):
    """What the agent is actually being told. Useful for confirming your
    AGENT.md or custom instructions really made it into the prompt."""
    active = None
    if session_id and session_id in SESSIONS:
        active = SESSIONS[session_id][0].content
    agent_md = agent_core.read_agent_md()
    return {
        "base": agent_core.BASE_SYSTEM_PROMPT,
        "agent_md": agent_md,
        "agent_md_loaded": bool(agent_md),
        # None until the session's first message creates it.
        "active_system_prompt": active,
    }


# While you're editing index.html/style.css, a cached copy in the browser
# looks exactly like "my change didn't work". Disable caching so a plain
# reload always picks up edits. Drop this in production.
_NO_CACHE = {"Cache-Control": "no-store, max-age=0"}


@app.middleware("http")
async def no_cache_static(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers.update(_NO_CACHE)
    return response


@app.get("/")
async def index():
    return FileResponse(WEB_DIR / "index.html", headers=_NO_CACHE)


app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


# ============================================================================
# Startup
# ============================================================================

if __name__ == "__main__":
    if not os.getenv("ORCHESTRATOR_ENDPOINT"):
        print("No .env found.")
        print("  The web UI needs a real model. Copy .env.example to .env and")
        print("  fill in the orchestrator credentials, then run it again.")
        sys.exit(1)

    import uvicorn

    # Registry + model are built in `lifespan` above, on uvicorn's own
    # event loop. See the comment there for why that matters.
    print("Starting mini-claude web...")
    uvicorn.run(app, host="127.0.0.1", port=8100, log_level="warning")

    # -- Key takeaway --------------------------------------------------------
    # The agent didn't change. `agent_core.agent_loop()` is imported here
    # exactly as the CLI imports it. What a UI actually adds is:
    #   1. TRANSPORT -- an HTTP endpoint instead of stdin/stdout
    #   2. STATE -- conversations keyed by session, because many users
    #      share one process (the CLI had exactly one conversation)
    #   3. A PERMISSION POLICY instead of a prompt -- the single real
    #      design problem. HTTP can't block on a human, so you either
    #      decide in advance (this lesson) or implement interrupt/resume
    #      (learn-mcp lesson 06) to ask the browser and wait.
    #   4. EVENT REPORTING -- the CLI printed tool calls as they happened;
    #      the UI has to collect and ship them with the response.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Stream the reply with SSE instead of one JSON blob, so text appears
    #    as it's generated (see fastapi/ and learn-langgraph lesson 10).
    # 2. Implement real approval: when the agent hits a blocked tool, return
    #    "needs_approval" and have the UI show Allow/Deny, then resume.
    # 3. Show the tool source (builtin vs mcp:notes) on each chip, so it's
    #    visible when an MCP server did the work.
    # 4. Persist SESSIONS to disk so a restart doesn't lose the conversation.
