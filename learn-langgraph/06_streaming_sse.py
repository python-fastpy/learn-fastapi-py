"""
Lesson 12 (LangGraph 6): Streaming with SSE
=============================================
Goal: Stream LangGraph execution events through a FastAPI SSE endpoint.

What you'll learn:
  - LangGraph's astream_events() for real-time streaming
  - FastAPI's StreamingResponse for SSE
  - The event format the frontend consumes
  - Progress tracking during graph execution

Run:
  uv run python 06_streaming_sse.py

  Then open: http://localhost:8012/docs  (Swagger UI)
  Or curl:   curl -N http://localhost:8012/api/v1/chat/stream?topic=Apple+earnings

Production parallel:
  The backend's /api/v1/chat endpoint (chat.py) streams LangGraph events
  as SSE to the frontend. Each event carries: node name, content delta,
  tool calls, interrupts, etc.
"""

import asyncio
import json
from typing import TypedDict

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from langgraph.graph import StateGraph, START, END


# --- Step 1: Build a simple graph to stream ---

class NewsState(TypedDict):
    topic: str
    research: str
    draft: str
    status: str


async def research_node(state: NewsState) -> dict:
    """Simulate slow research with progress."""
    await asyncio.sleep(0.5)  # simulate API call
    research = f"Key facts about {state['topic']}: significant market movement, analyst upgrades."
    return {"research": research, "status": "researching"}


async def draft_node(state: NewsState) -> dict:
    """Simulate draft generation."""
    await asyncio.sleep(0.8)  # simulate LLM call
    draft = f"REUTERS - {state['topic']}.\n\n{state['research']}\n\nReporting by AI Assistant."
    return {"draft": draft, "status": "drafted"}


async def review_node(state: NewsState) -> dict:
    """Simulate review."""
    await asyncio.sleep(0.3)
    return {"status": "reviewed"}


def build_graph():
    graph = StateGraph(NewsState)
    graph.add_node("research", research_node)
    graph.add_node("draft", draft_node)
    graph.add_node("review", review_node)
    graph.add_edge(START, "research")
    graph.add_edge("research", "draft")
    graph.add_edge("draft", "review")
    graph.add_edge("review", END)
    return graph.compile()


app_graph = build_graph()


# --- Step 2: FastAPI app with SSE streaming ---

api = FastAPI(title="LangGraph SSE Streaming Demo")


async def stream_graph_events(topic: str):
    """Generator that yields SSE events from graph execution.

    This is the pattern used in the backend's chat endpoint.
    Each event is formatted as: data: {json}\n\n
    """
    initial_state: NewsState = {
        "topic": topic,
        "research": "",
        "draft": "",
        "status": "starting",
    }

    # SSE format: each event is "data: ...\n\n"
    yield f"data: {json.dumps({'type': 'status', 'node': 'start', 'message': 'Starting graph execution'})}\n\n"

    # astream_events gives us fine-grained events
    async for event in app_graph.astream_events(initial_state, version="v2"):
        kind = event.get("event", "")
        name = event.get("name", "")

        if kind == "on_chain_start" and name in ("research", "draft", "review"):
            yield f"data: {json.dumps({'type': 'node_start', 'node': name})}\n\n"

        elif kind == "on_chain_end" and name in ("research", "draft", "review"):
            output = event.get("data", {}).get("output", {})
            yield f"data: {json.dumps({'type': 'node_end', 'node': name, 'output': output})}\n\n"

    # Send the final state
    final = await asyncio.to_thread(app_graph.invoke, initial_state)
    yield f"data: {json.dumps({'type': 'complete', 'draft': final['draft'], 'status': final['status']})}\n\n"
    yield "data: [DONE]\n\n"


@api.get("/api/v1/chat/stream")
async def stream_chat(topic: str = Query(default="Apple earnings report")):
    """Stream graph execution as Server-Sent Events.

    This mirrors the backend's /api/v1/chat endpoint.
    The frontend connects via EventSource and processes each event.
    """
    return StreamingResponse(
        stream_graph_events(topic),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )


@api.get("/api/v1/chat/sync")
async def sync_chat(topic: str = Query(default="Apple earnings report")):
    """Non-streaming version for comparison."""
    result = await asyncio.to_thread(
        app_graph.invoke,
        {"topic": topic, "research": "", "draft": "", "status": ""},
    )
    return {"draft": result["draft"], "status": result["status"]}


@api.get("/health")
async def health():
    return {"status": "ok"}


# --- Step 3: Run ---

if __name__ == "__main__":
    import uvicorn
    print("Starting SSE streaming server on http://localhost:8012")
    print("  Swagger UI: http://localhost:8012/docs")
    print("  SSE stream: curl -N 'http://localhost:8012/api/v1/chat/stream?topic=Apple+earnings'")
    print("  Sync call:  curl 'http://localhost:8012/api/v1/chat/sync?topic=Apple+earnings'")
    uvicorn.run(api, host="0.0.0.0", port=8012)


# ============================================================
# EXERCISES:
#
# 1. Add a POST /api/v1/chat endpoint that accepts JSON body
#    with {message, session_id} — closer to the real API
# 2. Add progress percentage to each event (e.g., node 1/3 = 33%)
# 3. Add an interrupt event that pauses the stream and waits
#    for a POST to /api/v1/chat/resume to continue
# 4. Connect to this SSE endpoint from JavaScript:
#    const es = new EventSource('/api/v1/chat/stream?topic=...')
#    es.onmessage = (e) => console.log(JSON.parse(e.data))
# ============================================================
