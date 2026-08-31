"""
Lesson 5: Human-in-the-Loop with MCP
======================================
Goal: Implement the full interrupt/resume cycle that powers
the Reuters AI Assistant's review workflows.

What you'll learn:
  - Returning interrupt payloads from tools
  - Continuation tokens for resuming
  - _meta injection for passing user responses back
  - The complete HITL lifecycle

Run:
  uv run python 05_hitl_interrupt.py

Production parallel:
  This is THE core pattern of the assistant:
  1. Skill generates a draft -> returns interrupt
  2. Backend checkpoints state (DynamoDB) -> sends interrupt to frontend
  3. User reviews in the UI (approve/refine/reject)
  4. Frontend sends interrupt_resolution -> backend resumes from checkpoint
  5. Backend calls tool again with _meta containing user response
  6. Skill continues from where it left off
"""

import asyncio
import json
import uuid
from fastmcp import FastMCP, Client

mcp = FastMCP("hitl-demo")

# Simulated session storage (in production: DynamoDB)
_sessions: dict[str, dict] = {}


@mcp.tool()
def draft_news_story(
    topic: str,
    style: str = "spot",
    _meta: dict | None = None,
) -> dict:
    """Draft a news story with human review.

    First call: generates a draft and returns an interrupt for review.
    Resume call: receives user's decision via _meta and finalizes.

    Args:
        topic: The news topic to write about
        style: Story style — "spot", "bulletin", or "buzz"
        _meta: Injected by the backend on resume. Contains session_id,
               continuation_token, and user_response.
    """

    # --- RESUME PATH: User responded to the interrupt ---
    if _meta and "user_response" in _meta:
        token = _meta.get("continuation_token")
        session = _sessions.get(token, {})
        user_response = _meta["user_response"]
        action = user_response.get("action")

        if action == "approve":
            final_draft = session.get("draft", "")
            del _sessions[token]  # cleanup
            return {
                "content": [{"type": "text", "text": final_draft}],
                "structuredContent": {
                    "status": "completed",
                    "draft": final_draft,
                    "action_taken": "approved",
                },
            }

        elif action == "refine":
            edits = user_response.get("edits", "")
            refined = f"{session.get('draft', '')}\n\n[REFINED with: {edits}]"
            _sessions[token]["draft"] = refined
            # Return another interrupt for re-review
            return {
                "content": [{"type": "text", "text": "Refined draft ready for review."}],
                "structuredContent": {
                    "status": "interrupted",
                    "interrupt": {
                        "type": "SPOT_STORY_REVIEW",
                        "message": "Review the refined draft",
                        "context": {"draft": refined, "revision": 2},
                        "actions": ["approve", "refine", "reject"],
                    },
                    "continuation_token": token,
                },
            }

        elif action == "reject":
            if token in _sessions:
                del _sessions[token]
            return {
                "content": [{"type": "text", "text": "Draft rejected."}],
                "structuredContent": {"status": "completed", "action_taken": "rejected"},
            }

    # --- INITIAL PATH: Generate draft and interrupt ---
    draft = f"[{style.upper()} STORY]\n\n{topic}\n\nDetails pending further reporting..."
    token = f"ct_{uuid.uuid4().hex[:12]}"

    # Save state for resume
    _sessions[token] = {
        "draft": draft,
        "topic": topic,
        "style": style,
        "revision": 1,
    }

    return {
        "content": [{"type": "text", "text": "Draft ready for your review."}],
        "structuredContent": {
            "status": "interrupted",
            "interrupt": {
                "type": "SPOT_STORY_REVIEW",
                "message": "Review the generated draft",
                "context": {
                    "draft": draft,
                    "topic": topic,
                    "style": style,
                    "word_count": len(draft.split()),
                },
                "actions": ["approve", "refine", "reject"],
            },
            "continuation_token": token,
        },
    }


async def demo():
    """Simulate the full HITL cycle."""
    client = Client(mcp)

    async with client:
        # === Step 1: Initial call — generates draft, returns interrupt ===
        print("=" * 60)
        print("STEP 1: Generate initial draft")
        print("=" * 60)
        result = await client.call_tool(
            "draft_news_story",
            {"topic": "Apple releases Vision Pro 2", "style": "spot"},
        )
        data = json.loads(result[0].text)
        sc = data["structuredContent"]
        token = sc["continuation_token"]

        print(f"Status: {sc['status']}")
        print(f"Interrupt type: {sc['interrupt']['type']}")
        print(f"Draft: {sc['interrupt']['context']['draft']}")
        print(f"Continuation token: {token}")
        print(f"Actions: {sc['interrupt']['actions']}")

        # === Step 2: User chooses "refine" with edits ===
        print("\n" + "=" * 60)
        print("STEP 2: User requests refinement")
        print("=" * 60)
        result = await client.call_tool(
            "draft_news_story",
            {
                "topic": "Apple releases Vision Pro 2",
                "style": "spot",
                "_meta": {
                    "continuation_token": token,
                    "user_response": {
                        "action": "refine",
                        "edits": "Add pricing information and availability date",
                    },
                },
            },
        )
        data = json.loads(result[0].text)
        sc = data["structuredContent"]

        print(f"Status: {sc['status']}")
        print(f"Refined draft: {sc['interrupt']['context']['draft']}")
        print(f"Revision: {sc['interrupt']['context']['revision']}")

        # === Step 3: User approves the refined draft ===
        print("\n" + "=" * 60)
        print("STEP 3: User approves")
        print("=" * 60)
        result = await client.call_tool(
            "draft_news_story",
            {
                "topic": "Apple releases Vision Pro 2",
                "style": "spot",
                "_meta": {
                    "continuation_token": token,
                    "user_response": {"action": "approve"},
                },
            },
        )
        data = json.loads(result[0].text)
        sc = data["structuredContent"]

        print(f"Status: {sc['status']}")
        print(f"Action: {sc['action_taken']}")
        print(f"Final draft: {data['content'][0]['text']}")


if __name__ == "__main__":
    asyncio.run(demo())


# ============================================================
# EXERCISES:
#
# 1. Add a "BUZZ_TYPE_SELECTION" interrupt that lets the user
#    choose between news buzz, earnings buzz, and preview buzz
# 2. Add a RIC_SELECTION interrupt (like NEWS_BUZZ.RIC_SELECTION)
#    that presents multiple RIC options
# 3. Implement a multi-step workflow: RIC selection -> headline
#    selection -> draft generation -> review
# ============================================================
