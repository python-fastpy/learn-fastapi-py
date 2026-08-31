"""
Lesson 4: Structured Content and Metadata
==========================================
Goal: Return rich structured data from MCP tools — the pattern used by
every Reuters skill for interrupt payloads and timing metadata.

What you'll learn:
  - Returning structuredContent from tools
  - Attaching _meta (out-of-band metadata like timing)
  - The difference between content (display) and structuredContent (machine-readable)

Run:
  uv run python 04_structured_content.py

Production parallel:
  Skills return structuredContent with status/interrupt/continuation_token.
  The _meta field carries skill_call_extras with per-step timing.
  See: mcp_protocol.py -> _call_tool_result_to_dict()
"""

import asyncio
import json
import time
from fastmcp import FastMCP, Client
from fastmcp.tools.tool import Tool

mcp = FastMCP("structured-content")


@mcp.tool()
def generate_buzz(ric: str, headline: str) -> dict:
    """Generate a news buzz draft for a given RIC and headline.

    Returns structured content with the draft and metadata.
    """
    start = time.time()

    # Simulate LLM generation
    draft = f"**{ric}** — {headline}\n\nMarket participants noted the development..."

    duration_ms = int((time.time() - start) * 1000)

    # This is what a real skill returns — the backend parses it:
    return {
        # Content blocks (what gets displayed)
        "content": [
            {"type": "text", "text": draft}
        ],
        # Structured content (machine-readable, for the orchestrator)
        "structuredContent": {
            "status": "completed",
            "draft": draft,
            "ric": ric,
            "word_count": len(draft.split()),
            "continuation_token": None,  # would be set if interrupted
        },
        # Metadata (out-of-band, not shown to user)
        "_meta": {
            "skill_call_extras": {
                "steps": [
                    {"name": "validate_ric", "duration_ms": 50},
                    {"name": "fetch_context", "duration_ms": 200},
                    {"name": "llm_generation", "duration_ms": duration_ms},
                ],
                "total_duration_ms": duration_ms + 250,
                "model_used": "gpt-4o",
            }
        },
    }


@mcp.tool()
def generate_with_review(ric: str, headline: str) -> dict:
    """Generate a buzz draft that requires human review before publishing.

    Returns an interrupt payload — the frontend renders a review UI.
    """
    draft = f"BUZZ — {ric}: {headline}. Sources said the move was expected."

    # This is the interrupt pattern — status: "interrupted" with an interrupt payload
    return {
        "content": [
            {"type": "text", "text": "Please review the generated buzz draft."}
        ],
        "structuredContent": {
            "status": "interrupted",
            "interrupt": {
                "type": "NEWS_BUZZ.REVIEW",
                "message": "Review the generated buzz before publishing",
                "context": {
                    "draft": draft,
                    "ric": ric,
                    "headline": headline,
                    "word_count": len(draft.split()),
                },
                "actions": ["approve", "refine", "reject"],
            },
            "continuation_token": "ct_demo_12345",
        },
        "_meta": {
            "skill_call_extras": {
                "steps": [{"name": "draft_generation", "duration_ms": 800}],
            }
        },
    }


async def demo():
    client = Client(mcp)

    async with client:
        # --- Call the simple generation tool ---
        print("=== generate_buzz ===")
        result = await client.call_tool(
            "generate_buzz",
            {"ric": "AAPL.O", "headline": "Apple announces new AI features"},
        )
        for content in result:
            # The raw result includes the full structured response
            data = json.loads(content.text)
            print(f"Status: {data['structuredContent']['status']}")
            print(f"Draft: {data['structuredContent']['draft'][:80]}...")
            print(f"Timing: {data['_meta']['skill_call_extras']['steps']}")
        print()

        # --- Call the interrupt tool ---
        print("=== generate_with_review ===")
        result = await client.call_tool(
            "generate_with_review",
            {"ric": "MSFT.O", "headline": "Microsoft beats earnings estimates"},
        )
        for content in result:
            data = json.loads(content.text)
            sc = data["structuredContent"]
            print(f"Status: {sc['status']}")
            print(f"Interrupt type: {sc['interrupt']['type']}")
            print(f"Actions: {sc['interrupt']['actions']}")
            print(f"Continuation token: {sc['continuation_token']}")
            print(f"Draft preview: {sc['interrupt']['context']['draft'][:60]}...")


if __name__ == "__main__":
    asyncio.run(demo())


# ============================================================
# EXERCISES:
#
# 1. Add a "refinement" interrupt type that includes the user's
#    edit suggestions in the context
# 2. Add multiple content blocks (text + an "image" placeholder)
# 3. Parse the _meta timing data and print a formatted summary
# ============================================================
