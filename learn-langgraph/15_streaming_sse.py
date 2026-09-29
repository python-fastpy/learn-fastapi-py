"""Lesson 15 -- Streaming over HTTP with SSE
============================================

Lesson 10 streamed chunks inside one Python process. A browser is not in that
process. SSE (Server-Sent Events) is how the chunks get out: one long-lived
HTTP response, and the server writes events into it as they happen.

  ┌─ BROWSER ──────────┐        ┌─ FastAPI (this file) ─┐     ┌─ the graph ─┐
  │ new EventSource(   │  GET   │ StreamingResponse(    │     │ research    │
  │  "/api/v1/chat/    │ ─────► │   stream_events(),    │ ──► │   │         │
  │   stream?topic=x") │        │   media_type=         │     │   ▼         │
  │                    │        │   "text/event-stream")│     │ draft       │
  │ es.onmessage = ... │ ◄───── │                       │ ◄── │   │         │
  │   node_start       │  one   │ astream_events()      │     │   ▼         │
  │   node_end         │  TCP   │   yields as each node │     │ review      │
  │   complete         │  conn  │   starts and finishes │     └─────────────┘
  └────────────────────┘        └───────────────────────┘

  the wire format -- text, not JSON-RPC. Two newlines END each event:

      data: {"type": "node_start", "node": "research"}\\n\\n
      data: {"type": "node_end", "node": "research", ...}\\n\\n
      data: [DONE]\\n\\n

  1. astream_events()  finer-grained than lesson 10's stream(): you get
                       on_chain_start / on_chain_end per node, so a UI can
                       say "researching..." before the node finishes.
  2. StreamingResponse takes an async generator and keeps the response open.
                       media_type="text/event-stream" is what makes it SSE.
  3. THE FORMAT        every event is `data: <payload>\\n\\n`. Miss the blank
                       line and the browser buffers forever, waiting.
  4. X-Accel-Buffering: no  tells nginx not to buffer the stream. Without it
                       your events arrive in one lump at the end, and it
                       looks like streaming is broken when it is not.
  5. ONE RUN           the generator yields the final state from the LAST
                       event it saw. Calling invoke() again to "get the
                       result" would run the whole graph a SECOND time --
                       double the latency, double any side effect.

  EventSource only speaks GET, which is why this endpoint takes a query
  parameter. Real chat APIs POST a message and stream the reply, which needs
  fetch() with a ReadableStream on the client instead.

Run:  uv run python 15_streaming_sse.py           (no LLM needed)

  then, in another terminal:
      curl -N "http://localhost:8012/api/v1/chat/stream?topic=Apple+earnings"
      curl "http://localhost:8012/api/v1/chat/sync?topic=Apple+earnings"
  or open http://localhost:8012/docs

Maps to: chat.py -> the /api/v1/chat SSE endpoint the frontend consumes
"""

import asyncio
import json
from typing import TypedDict

from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from langgraph.graph import END, START, StateGraph


class NewsState(TypedDict):
    topic: str
    research: str
    draft: str
    status: str


async def research(state: NewsState) -> dict:
    await asyncio.sleep(0.5)                      # stands in for an API call
    return {"research": f"Key facts on {state['topic']}: market movement, upgrades.",
            "status": "researched"}


async def draft(state: NewsState) -> dict:
    await asyncio.sleep(0.8)                      # stands in for an LLM call
    return {"draft": f"REUTERS - {state['topic']}.\n\n{state['research']}",
            "status": "drafted"}


async def review(state: NewsState) -> dict:
    await asyncio.sleep(0.3)
    return {"status": "reviewed"}


def build():
    g = StateGraph(NewsState)
    g.add_node("research", research)
    g.add_node("draft", draft)
    g.add_node("review", review)
    g.add_edge(START, "research")
    g.add_edge("research", "draft")
    g.add_edge("draft", "review")
    g.add_edge("review", END)
    return g.compile()


graph = build()
NODES = ("research", "draft", "review")


def sse(payload: dict | str) -> str:
    """3. One event. The blank line is not optional."""
    return f"data: {json.dumps(payload) if isinstance(payload, dict) else payload}\n\n"


async def stream_events(topic: str):
    """1 + 5. Yield as the graph runs, and keep the final state as we go."""
    state: NewsState = {"topic": topic, "research": "", "draft": "", "status": "starting"}
    yield sse({"type": "status", "node": "start", "message": "graph starting"})

    final = state
    async for event in graph.astream_events(state, version="v2"):
        kind, name = event.get("event"), event.get("name")
        if name not in NODES:
            continue
        if kind == "on_chain_start":
            yield sse({"type": "node_start", "node": name})
        elif kind == "on_chain_end":
            output = event.get("data", {}).get("output") or {}
            final = {**final, **output}            # 5. accumulate, do not re-run
            yield sse({"type": "node_end", "node": name, "status": output.get("status")})

    yield sse({"type": "complete", "draft": final.get("draft", ""), "status": final.get("status")})
    yield sse("[DONE]")


api = FastAPI(title="LangGraph SSE demo")


@api.get("/api/v1/chat/stream")
async def stream_chat(topic: str = Query(default="Apple earnings report")):
    """2 + 4. An open response the generator writes into."""
    return StreamingResponse(
        stream_events(topic),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache",
                 "Connection": "keep-alive",
                 "X-Accel-Buffering": "no"},      # 4. or nginx buffers it all
    )


@api.get("/api/v1/chat/sync")
async def sync_chat(topic: str = Query(default="Apple earnings report")):
    """The same graph without streaming -- one wait, then everything."""
    result = await graph.ainvoke({"topic": topic, "research": "", "draft": "", "status": ""})
    return {"draft": result["draft"], "status": result["status"]}


@api.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    print("serving http://localhost:8012   (Ctrl+C to stop)")
    print('  curl -N "http://localhost:8012/api/v1/chat/stream?topic=Apple+earnings"')
    uvicorn.run(api, host="127.0.0.1", port=8012, log_level="warning")

# Exercises:
# 1. Add a print to each node and hit /sync, then /stream. Each prints ONCE
#    per request. Re-add an invoke() at the end of the generator and they
#    print twice -- the bug point 5 describes.
# 2. Drop one "\n" from sse(). curl shows nothing until the end: the browser
#    is waiting for an event boundary that never comes.
# 3. Add {"progress": "1/3"} to each node_end so a UI can draw a bar.
# 4. Emit an interrupt event mid-stream and a POST /resume that continues it
#    (lesson 09 over HTTP -- this is how production does review screens).
# 5. Consume it from a browser console:
#      const es = new EventSource("http://localhost:8012/api/v1/chat/stream?topic=x")
#      es.onmessage = (e) => console.log(e.data)
