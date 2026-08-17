"""Lesson 10 -- Human-in-the-Loop Interrupts
=============================================

WHY THIS MATTERS:
  The AI generates a greeting — but what if the user wants to review
  it before sending? Interrupts let a tool *pause* and ask the human:
  "Here's the greeting. Approve, refine, or reject?" The entire
  execution state is saved (checkpointed), and when the user responds,
  execution resumes exactly where it left off. Any tool that needs
  human confirmation uses this pattern.

WHAT YOU'LL LEARN:
  1. Build structured interrupt payloads (what the frontend renders)
  2. Define actions the user can take (approve, refine, reject)
  3. Use the .block() builder to create forwarded blocks
  4. Understand the full lifecycle: tool -> interrupt -> checkpoint -> resume
  5. See how different event types drive different UIs
     (GREETING_REVIEW, LANGUAGE_SELECTION, STYLE_SELECTION)

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
       |  user msg     |  call_tool    |  greet user   |
       |               |               |               |
       |               |               |  <-- interrupt payload
       |               |  <-- forwarded block (event_type + greeting)
       |  <-- SSE with interrupt data
       |
       |  User reviews greeting, clicks "Approve" or "Refine"
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

PREREQUISITES: Lesson 08 (forwarded blocks -- interrupts build on the same _meta mechanism)

Run:  uv run python 10_interrupts.py

EXPECTED OUTPUT:
  === Interrupt Demo ===

  --- 1. Greeting Review Interrupt ---

    Agent sees: [INTERRUPT] GREETING_REVIEW: Please review the formal greeting for 'Alice'
    Event type: GREETING_REVIEW
    Message: Please review the formal greeting for 'Alice'
    Actions: ['Approve', 'Refine', 'Reject']
    Payload keys: ['greeting', 'name', 'style', 'word_count']

  --- 2. Language Selection Interrupt ---

    Agent sees: [INTERRUPT] LANGUAGE_SELECTION: Select a language for greeting 'Bob':
    Event type: LANGUAGE_SELECTION
    Message: Select a language for greeting 'Bob':
    Actions: ['English', 'Spanish', 'French']
    Payload keys: ['name', 'candidates']

  --- 3. Style Selection Interrupt ---

    Agent sees: [INTERRUPT] STYLE_SELECTION: What greeting style would you like?
    Event type: STYLE_SELECTION
    Message: What greeting style would you like?
    Actions: ['Formal', 'Casual', 'Warm']
    Payload keys: ['available_styles']

  === Interrupt Lifecycle ===
    1. Tool builds SkillInterrupt ...
    2. .block() creates forwarded blocks ...
    3. Orchestrator checkpoints state (DynamoDB) ...
    4. User responds (approve/refine/reject) ...
    5. Orchestrator resumes from checkpoint ...
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
# Concrete interrupt types
# ============================================================================

class GreetingReviewPayload(InterruptPayload):
    """Payload for greeting review interrupts."""
    greeting: str
    name: str
    style: str
    word_count: int


class GreetingReviewInterrupt(SkillInterrupt):
    """Interrupt for reviewing a generated greeting."""
    type = "GREETING_REVIEW"


class LanguageSelectionPayload(InterruptPayload):
    """Payload for language selection interrupts."""
    name: str
    candidates: list[dict]


class LanguageSelectionInterrupt(SkillInterrupt):
    """Interrupt for selecting a language for the greeting."""
    type = "LANGUAGE_SELECTION"


class StyleSelectionPayload(InterruptPayload):
    """Payload for style selection."""
    available_styles: list[str]


class StyleSelectionInterrupt(SkillInterrupt):
    """Interrupt for selecting greeting style."""
    type = "STYLE_SELECTION"


# ============================================================================
# Tools that trigger interrupts
# ============================================================================

@mcp.tool
async def greet_and_review(
    name: Annotated[str, Field(description="Name of the person to greet")],
    style: Annotated[str, Field(default="formal", description="Greeting style")] = "formal",
) -> list:
    """Generate a greeting and return an interrupt for user review."""
    greeting = {"formal": f"Dear {name}, pleased to meet you.", "casual": f"Hey {name}!", "warm": f"Welcome, {name}!"}.get(style, f"Hello, {name}!")

    payload = GreetingReviewPayload(
        greeting=greeting, name=name, style=style, word_count=len(greeting.split()),
    )

    interrupt = GreetingReviewInterrupt(
        message=f"Please review the {style} greeting for '{name}'",
        payload=payload,
        actions=[
            InterruptAction(label="Approve", value="approve", style="primary"),
            InterruptAction(label="Refine", value="refine", style="default"),
            InterruptAction(label="Reject", value="reject", style="danger"),
        ],
    )

    return interrupt.block()


@mcp.tool
async def select_language(
    name: Annotated[str, Field(description="Name of the person to greet")],
) -> list:
    """Present language options and return an interrupt for selection."""
    candidates = [
        {"code": "en", "label": "English"},
        {"code": "es", "label": "Spanish"},
        {"code": "fr", "label": "French"},
    ]

    payload = LanguageSelectionPayload(name=name, candidates=candidates)

    interrupt = LanguageSelectionInterrupt(
        message=f"Select a language for greeting '{name}':",
        payload=payload,
        actions=[
            InterruptAction(label=c["label"], value=c["code"])
            for c in candidates
        ],
    )

    return interrupt.block()


@mcp.tool
async def select_style() -> list:
    """Return an interrupt for greeting style selection."""
    payload = StyleSelectionPayload(
        available_styles=["formal", "casual", "warm"]
    )

    interrupt = StyleSelectionInterrupt(
        message="What greeting style would you like?",
        payload=payload,
        actions=[
            InterruptAction(label="Formal", value="formal"),
            InterruptAction(label="Casual", value="casual"),
            InterruptAction(label="Warm", value="warm"),
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

        # -- Greeting review interrupt --
        print("--- 1. Greeting Review Interrupt ---\n")
        r1 = await client.call_tool_mcp("greet_and_review", {
            "name": "Alice",
            "style": "formal",
        })
        _print_interrupt(r1)

        # -- Language selection interrupt --
        print("--- 2. Language Selection Interrupt ---\n")
        r2 = await client.call_tool_mcp("select_language", {"name": "Bob"})
        _print_interrupt(r2)

        # -- Style selection interrupt --
        print("--- 3. Style Selection Interrupt ---\n")
        r3 = await client.call_tool_mcp("select_style", {})
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
    # Interrupts are how tools pause for human input:
    #
    #   SkillInterrupt(type, message, payload, actions)
    #     |-- type: maps to frontend component (GREETING_REVIEW, etc.)
    #     |-- payload: typed data (greeting text, language candidates, etc.)
    #     |-- actions: buttons the user can click
    #     |-- .block(): builds the forwarded block format
    #
    # The pattern works for any review or selection flow:
    #   GREETING_REVIEW  -- approve/refine/reject a generated greeting
    #   LANGUAGE_SELECTION -- pick from language candidates
    #   STYLE_SELECTION  -- choose a greeting style
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Create a ToneSelectionInterrupt with options like "friendly", "professional"
    # 2. Simulate the "resume" side: process user's action choice
    # 3. Chain interrupts: style selection -> language selection -> review
