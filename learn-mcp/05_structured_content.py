"""Lesson 05 -- Structured Content and Metadata: one tool result, three parts
============================================================================

A tool result can carry THREE separate things, each for a different reader:

  ┌──────────────────── one tool result ────────────────────┐
  │ content            "Hello, Shubham!"                    │ -> the LLM / chat UI reads this
  │                    human-readable text blocks           │
  │                                                         │
  │ structuredContent  {"status": "completed",              │ -> YOUR CODE reads this
  │                     "greeting": "Hello, Shubham!", ...} │    (the orchestrator) --
  │                    machine-readable JSON                │    no text parsing needed
  │                                                         │
  │ _meta              {"skill_call_extras":                │ -> logs / monitoring only
  │                      {"steps": [...timings...]}}        │    out-of-band: NOT shown to
  │                    out-of-band metadata                 │    the user or the LLM
  └─────────────────────────────────────────────────────────┘

  structuredContent.status tells the orchestrator what happened:
    "completed"   -> done, use the result
    "interrupted" -> paused for a human: an `interrupt` payload says WHAT to
                     ask (type, message, context, actions), and a
                     `continuation_token` says HOW to resume later

  Maps to production:
    Every Reuters skill returns structuredContent with status / interrupt /
    continuation_token, and _meta.skill_call_extras with per-step timing.
    The backend parses it in mcp_protocol.py -> _call_tool_result_to_dict().
    (Interrupts end to end: lesson 06. Hiding data from the LLM: lesson 09.)

Run:  uv run python 05_structured_content.py
"""

import asyncio
import time
from fastmcp import FastMCP, Client
from fastmcp.tools import ToolResult

mcp = FastMCP("structured-greetings")


# -- 0. The easy way: return a dict ------------------------------------------
# FastMCP fills in BOTH parts for you: content = the dict as JSON text,
# structuredContent = the dict itself. Fine when you don't need _meta.

@mcp.tool
def greet(name: str) -> dict:
    """Greet someone. Returns a plain dict."""
    return {"greeting": f"Hello, {name}!"}


# -- 1. Full control: set content, structuredContent and _meta yourself -------

@mcp.tool
def greet_with_timing(name: str) -> ToolResult:
    """Greet someone, with machine-readable status and timing metadata."""
    start = time.time()
    greeting = f"Hello, {name}! Welcome to MCP."
    took_ms = int((time.time() - start) * 1000)

    return ToolResult(
        content=greeting,                                   # for the LLM / user
        structured_content={                                # for your code
            "status": "completed",
            "greeting": greeting,
            "name": name,
            "word_count": len(greeting.split()),
            "continuation_token": None,                     # set only if interrupted
        },
        meta={                                              # out-of-band
            "skill_call_extras": {
                "steps": [
                    {"name": "validate_name", "duration_ms": 5},
                    {"name": "compose_greeting", "duration_ms": took_ms},
                ],
                "total_duration_ms": took_ms + 5,
            }
        },
    )


# -- 2. Interrupted: pause and ask a human before continuing ------------------

@mcp.tool
def greet_with_review(name: str) -> ToolResult:
    """Draft a greeting that a human must approve before it is sent."""
    draft = f"Dear {name}, welcome aboard! We're thrilled to have you."
    return ToolResult(
        content="Please review the greeting before it is sent.",
        structured_content={
            "status": "interrupted",
            "interrupt": {
                "type": "GREETING.REVIEW",                  # the UI picks a review screen by type
                "message": "Review the greeting before sending",
                "context": {"draft": draft, "name": name, "word_count": len(draft.split())},
                "actions": ["approve", "refine", "reject"],  # buttons the user can press
            },
            "continuation_token": "ct_demo_12345",          # sent back to resume this run
        },
        meta={"skill_call_extras": {"steps": [{"name": "draft_greeting", "duration_ms": 800}]}},
    )


# -- Client: read each part separately ----------------------------------------

async def demo():
    async with Client(mcp) as client:
        print("=== 0. greet (plain dict) ===")
        r = await client.call_tool("greet", {"name": "Shubham"})
        print(f"  content           : {r.content[0].text}")
        print(f"  structuredContent : {r.structured_content}")
        print(f"  _meta             : {r.meta}\n")

        print("=== 1. greet_with_timing (completed) ===")
        r = await client.call_tool("greet_with_timing", {"name": "Shubham"})
        print(f"  content           : {r.content[0].text}")
        print(f"  status            : {r.structured_content['status']}")
        print(f"  word_count        : {r.structured_content['word_count']}")
        print(f"  timing (_meta)    : {r.meta['skill_call_extras']['steps']}\n")

        print("=== 2. greet_with_review (interrupted) ===")
        r = await client.call_tool("greet_with_review", {"name": "Shubham"})
        sc = r.structured_content
        print(f"  content           : {r.content[0].text}")
        print(f"  status            : {sc['status']}")
        print(f"  interrupt type    : {sc['interrupt']['type']}")
        print(f"  actions           : {sc['interrupt']['actions']}")
        print(f"  continuation_token: {sc['continuation_token']}")
        print(f"  draft preview     : {sc['interrupt']['context']['draft']}")


if __name__ == "__main__":
    asyncio.run(demo())

    # -- Key takeaway --------------------------------------------------------
    #   content           -> what the LLM / user sees (text)
    #   structuredContent -> what your code reads (status, data, interrupt)
    #   _meta             -> side-channel data (timing, model used) -- never shown
    # Return a dict for simple tools; return ToolResult when you need _meta or
    # different text for the LLM than the data for your code.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a "refinement" interrupt type (GREETING.REFINE) that includes the
    #    user's edit suggestions in the context
    # 2. Return multiple content blocks (text + an image placeholder) --
    #    hint: content=[TextContent(...), ImageContent(...)] from mcp.types
    # 3. Parse the _meta timing data and print a formatted summary
    #    ("compose_greeting: 0ms, total: 5ms")
