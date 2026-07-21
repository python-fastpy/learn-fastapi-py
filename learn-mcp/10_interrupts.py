"""Lesson 10 -- Human-in-the-Loop Interrupts
=============================================
Concepts:
  - SkillInterrupt: structured payload for pausing execution
  - InterruptPayload: typed payload with extra="forbid"
  - .block() builder: creates forwarded block for the client
  - Interrupt lifecycle: tool -> forwarded block -> client -> resume
  - Event types: how the frontend knows which UI to render

Flow:
  +--------+     +-----------+     +--------+     +-----------+
  | Client | --> | Orchestr. | --> | Tool   | --> | Interrupt |
  +--------+     +-----------+     +--------+     +-----------+
       |               |               |               |
       |  user msg     |  call_tool    |  draft story  |
       |               |               |               |
       |               |               |  <-- interrupt payload
       |               |  <-- forwarded block (event_type + draft)
       |  <-- SSE with interrupt data
       |
       |  User reviews draft, clicks "Approve" or "Refine"
       |
       |  resume msg --+
       |               |  resume tool  |
       |               +-------------->|  continue...
       +-------------------------------+

  Maps to:
    shared/interrupts/models.py (SkillInterrupt, InterruptPayload)
    story-drafting/src/interrupts/spot_story_review.py
    story-drafting/src/interrupts/news_buzz_ric_selection.py
    langgraph_mcp_orchestrator.py (interrupt() + checkpoint resume)

No LLM needed -- demonstrates the interrupt data model and lifecycle.

Run:  uv run python 10_interrupts.py
"""

import asyncio
import json
from typing import Annotated, Optional
from pydantic import BaseModel, Field
from fastmcp import FastMCP, Client


mcp = FastMCP(name="interrupt-demo")


# ============================================================================
# Interrupt models (mirrors shared/interrupts/models.py)
# ============================================================================

class InterruptPayload(BaseModel):
    """Base class for all interrupt payloads. extra='forbid' ensures
    no unexpected fields slip in."""
    model_config = {"extra": "forbid"}


class InterruptAction(BaseModel):
    """An action the user can take on an interrupt."""
    label: str
    value: str
    style: str = "default"  # default, primary, danger


class SkillInterrupt:
    """Base class for skill interrupts.

    Subclasses set:
      - type: str (class var) -- maps to frontend component
      - Payload: InterruptPayload subclass -- the structured data

    The .block() method builds the forwarded block format that
    the orchestrator sends to the frontend.
    """
    type: str = "GENERIC"

    def __init__(self, message: str, payload: InterruptPayload,
                 actions: list[InterruptAction] | None = None):
        self.message = message
        self.payload = payload
        self.actions = actions or []

    def block(self) -> list:
        """Build forwarded blocks for the interrupt.

        Returns a list suitable for ToolResult content:
        - First block: agent-visible summary
        - Second block (forwarded): full interrupt payload for the UI
        """
        interrupt_data = {
            "event_type": self.type,
            "message": self.message,
            "payload": self.payload.model_dump(),
            "actions": [a.model_dump() for a in self.actions],
        }

        return [
            {
                "type": "text",
                "text": f"[INTERRUPT] {self.type}: {self.message}",
                "_meta": {
                    "forwarded_blocks": [
                        {
                            "type": "text",
                            "text": json.dumps(interrupt_data),
                        }
                    ]
                },
            }
        ]


# ============================================================================
# Concrete interrupt types (mirrors production interrupts)
# ============================================================================

class StoryReviewPayload(InterruptPayload):
    """Payload for story review interrupts."""
    draft: str
    headline: str
    word_count: int
    style: str


class StoryReviewInterrupt(SkillInterrupt):
    """Interrupt for reviewing a drafted story."""
    type = "SPOT_STORY_REVIEW"


class RicSelectionPayload(InterruptPayload):
    """Payload for RIC selection interrupts."""
    query: str
    candidates: list[dict]


class RicSelectionInterrupt(SkillInterrupt):
    """Interrupt for selecting a RIC from candidates."""
    type = "NEWS_BUZZ.RIC_SELECTION"


class BuzzTypePayload(InterruptPayload):
    """Payload for buzz type selection."""
    available_types: list[str]


class BuzzTypeSelectionInterrupt(SkillInterrupt):
    """Interrupt for selecting buzz type."""
    type = "BUZZ_TYPE_SELECTION"


# ============================================================================
# Tools that trigger interrupts
# ============================================================================

@mcp.tool
async def draft_and_review(
    topic: Annotated[str, Field(description="Topic for the story")],
    style: Annotated[str, Field(default="spot", description="Story style")] = "spot",
) -> list:
    """Draft a story and return an interrupt for user review."""
    draft = (
        f"HEADLINE: {topic.title()} Developments - Reuters\n\n"
        f"LONDON (Reuters) - This is a {style} story about {topic}. "
        f"The story covers recent developments and market implications.\n\n"
        f"Industry analysts noted the significance of these changes."
    )

    payload = StoryReviewPayload(
        draft=draft,
        headline=draft.split("\n")[0],
        word_count=len(draft.split()),
        style=style,
    )

    interrupt = StoryReviewInterrupt(
        message=f"Please review the {style} story draft about '{topic}'",
        payload=payload,
        actions=[
            InterruptAction(label="Approve", value="approve", style="primary"),
            InterruptAction(label="Refine", value="refine", style="default"),
            InterruptAction(label="Reject", value="reject", style="danger"),
        ],
    )

    return interrupt.block()


@mcp.tool
async def select_ric(
    query: Annotated[str, Field(description="Company or instrument to search")],
) -> list:
    """Search for RICs and return an interrupt for user selection."""
    candidates = [
        {"ric": f"{query.upper()}.O", "name": f"{query} Inc (NASDAQ)", "exchange": "NASDAQ"},
        {"ric": f"{query.upper()}.N", "name": f"{query} Inc (NYSE)", "exchange": "NYSE"},
        {"ric": f"{query.upper()}.L", "name": f"{query} PLC (LSE)", "exchange": "LSE"},
    ]

    payload = RicSelectionPayload(query=query, candidates=candidates)

    interrupt = RicSelectionInterrupt(
        message=f"Multiple RICs found for '{query}'. Please select one:",
        payload=payload,
        actions=[
            InterruptAction(label=c["ric"], value=c["ric"])
            for c in candidates
        ],
    )

    return interrupt.block()


@mcp.tool
async def select_buzz_type() -> list:
    """Return an interrupt for buzz type selection."""
    payload = BuzzTypePayload(
        available_types=["preview_buzz", "news_buzz", "earnings_buzz"]
    )

    interrupt = BuzzTypeSelectionInterrupt(
        message="What type of buzz would you like to generate?",
        payload=payload,
        actions=[
            InterruptAction(label="Preview Buzz", value="preview_buzz"),
            InterruptAction(label="News Buzz", value="news_buzz"),
            InterruptAction(label="Earnings Buzz", value="earnings_buzz"),
        ],
    )

    return interrupt.block()


# ============================================================================
# Client demo: inspect interrupt payloads
# ============================================================================

async def main():
    async with Client(mcp) as client:
        print("=== Interrupt Demo ===\n")
        print("Interrupts pause execution and ask the user for input.")
        print("The frontend renders different UIs based on event_type.\n")

        # -- Story review interrupt --
        print("--- 1. Story Review Interrupt ---\n")
        r1 = await client.call_tool_mcp("draft_and_review", {
            "topic": "oil prices",
            "style": "spot",
        })
        _print_interrupt(r1)

        # -- RIC selection interrupt --
        print("--- 2. RIC Selection Interrupt ---\n")
        r2 = await client.call_tool_mcp("select_ric", {"query": "AAPL"})
        _print_interrupt(r2)

        # -- Buzz type selection interrupt --
        print("--- 3. Buzz Type Selection Interrupt ---\n")
        r3 = await client.call_tool_mcp("select_buzz_type", {})
        _print_interrupt(r3)

        # -- Interrupt lifecycle summary --
        print("=== Interrupt Lifecycle ===\n")
        print("  1. Tool builds SkillInterrupt with typed Payload")
        print("  2. .block() creates forwarded blocks")
        print("  3. Orchestrator detects interrupt, calls LangGraph interrupt()")
        print("  4. State checkpointed to DynamoDB")
        print("  5. Frontend receives event_type, renders appropriate UI")
        print("  6. User responds (approve/refine/select)")
        print("  7. Backend resumes from checkpoint with user's response")
        print("  8. Tool continues execution with the user's choice")


def _print_interrupt(result):
    """Extract and print interrupt data from a call_tool_mcp result."""
    for block in result.content:
        text = getattr(block, "text", None)
        if not text:
            continue

        # The tool returns a list of dicts, which FastMCP serializes as JSON text.
        # Parse and walk the structure to find the interrupt data.
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            print(f"  Raw: {text[:100]}...")
            continue

        # Could be a list of blocks or a single block
        blocks = parsed if isinstance(parsed, list) else [parsed]
        for item in blocks:
            if not isinstance(item, dict):
                continue

            # Print the agent-visible text
            agent_text = item.get("text", "")
            if "[INTERRUPT]" in agent_text:
                print(f"  Agent sees: {agent_text}")

            # Extract forwarded blocks from _meta
            fbs = item.get("_meta", {}).get("forwarded_blocks", [])
            for fb in fbs:
                fb_text = fb.get("text", "")
                try:
                    inner = json.loads(fb_text)
                    print(f"  Event type: {inner['event_type']}")
                    print(f"  Message: {inner['message']}")
                    print(f"  Actions: {[a['label'] for a in inner.get('actions', [])]}")
                    print(f"  Payload keys: {list(inner.get('payload', {}).keys())}")
                except (json.JSONDecodeError, KeyError):
                    print(f"  Forwarded: {fb_text[:100]}...")
    print()


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Interrupts are how skills pause for human input:
    #
    #   SkillInterrupt(type, message, payload, actions)
    #     |-- type: maps to frontend component (SPOT_STORY_REVIEW, etc.)
    #     |-- payload: typed data (draft text, RIC candidates, etc.)
    #     |-- actions: buttons the user can click
    #     |-- .block(): builds the forwarded block format
    #
    # Production event types include:
    #   SPOT_STORY_REVIEW, NEWS_BULLETIN_REVIEW, PREVIEW_BUZZ_REVIEW,
    #   URGENT_BUILDER_REVIEW, NEWS_BUZZ.RIC_SELECTION,
    #   NEWS_BUZZ.HEADLINE_SELECTION, BUZZ_TYPE_SELECTION, etc.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Create a HeadlineSelectionInterrupt with multiple headline options
    # 2. Simulate the "resume" side: process user's action choice
    # 3. Chain interrupts: RIC selection -> headline selection -> review
