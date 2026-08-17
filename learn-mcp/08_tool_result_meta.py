"""Lesson 08 -- ToolResult & Forwarded Blocks
===============================================

WHY THIS MATTERS:
  When a tool generates a greeting card with creative text, the LLM
  agent doesn't need to see all of it in its context window -- that
  wastes tokens and confuses the agent. But the *frontend* needs the
  full card to display it to the user. Forwarded blocks solve this:
  the agent sees a short summary ("Greeting card created for Alice"),
  while the UI gets the full formatted card via _meta.forwarded_blocks.

  This is the key mechanism behind all story/buzz/bulletin drafts
  in the production system.

WHAT YOU'LL LEARN:
  1. Return rich results with content + metadata
  2. Use _meta.forwarded_blocks for UI-only payloads
  3. The difference between call_tool() and call_tool_mcp()
  4. The forwarded_tool_result() helper pattern

Concepts:
  - ToolResult: rich return type with content + metadata
  - _meta.forwarded_blocks: out-of-band payload for UI (not seen by agent)
  - call_tool_mcp() vs call_tool(): preserves MCP metadata
  - Agent-visible content vs UI-visible blocks

Flow:
  +--------+     +------------------+     +---------------------+
  | Client | --> | MCP Server       | --> | Tool                |
  +--------+     +------------------+     |   greet_card()      |
       |                                  |                     |
       |                                  | Returns:            |
       |         +-- agent text ------+   |  content: [{text}]  |
       |         |   (summary for     |   |  _meta:             |
       |         |    LLM context)    |   |   forwarded_blocks: |
       |         +--------------------+   |    [{full card}]    |
       |                                  +---------------------+
       |         +-- forwarded -------+
       |         |   (full card for   |
       |         |    UI rendering)   |
       |         +--------------------+

  Maps to:
    shared/forwarded.py (forwarded_tool_result helper)
    mcp_protocol.py (_call_tool_result_to_dict extracts forwarded blocks)
    story-drafting tools (return drafts via forwarded blocks)

PREREQUISITES: Lesson 07 (LLM tools), Lesson 04 (resources/primitives)

** Requires .env with TR Orchestrator credentials **

Run:  uv run python 08_tool_result_meta.py

EXPECTED OUTPUT (without .env -- mock mode):
  === 1. Simple Tool (greet) ===

    Result: [TextContent(... "message": "Hello, Alice!" ...)]

  === 2. Forwarded Blocks via call_tool (agent view only) ===

    Agent sees: [TextContent(... "Greeting card created for Bob" ...)]
    (Forwarded blocks are invisible to call_tool -- use call_tool_mcp to access them)

  === 3. Forwarded Blocks via call_tool_mcp (full result) ===

    Content blocks (agent-visible): 1
      [0] TextContent: {"summary": "Greeting card created for Bob", ...}

    Forwarded blocks (UI-only): 1
      event_type: GREETING_CARD_REVIEW
      word_count: <N>
      card preview: <first 200 chars of mock/LLM card text>...

EXPECTED OUTPUT (with .env -- real LLM card):
  Same structure, but greet_card returns a real LLM-generated greeting
  card instead of a mock placeholder.
"""

import asyncio
import json
import os
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client
from dotenv import load_dotenv

load_dotenv()


mcp = FastMCP(name="result-meta-demo")


def _has_env():
    return bool(os.getenv("ORCHESTRATOR_ENDPOINT"))


# ============================================================================
# Helper: forwarded_tool_result (mirrors shared/forwarded.py)
# ============================================================================

def forwarded_tool_result(agent_text: str, forwarded_data: dict) -> list:
    """Build a ToolResult with forwarded blocks.

    This is the pattern from shared/forwarded.py:
      - agent_text: what the LLM sees (summary/confirmation)
      - forwarded_data: what the UI sees (full draft, structured payload)

    The _meta.forwarded_blocks mechanism sends data to the frontend
    without polluting the agent's context window.
    """
    return [
        {
            "type": "text",
            "text": agent_text,
            "_meta": {
                "forwarded_blocks": [
                    {
                        "type": "text",
                        "text": json.dumps(forwarded_data),
                    }
                ]
            },
        }
    ]


# ============================================================================
# Tools that use forwarded blocks
# ============================================================================

async def _greet_card(
    name: Annotated[str, Field(description="Name of the person to create a greeting card for")],
    occasion: Annotated[str, Field(default="general", description="Occasion: general, birthday, farewell, congratulations")] = "general",
) -> list:
    """Generate a greeting card. Returns summary to agent + full card to UI."""
    if _has_env():
        from llm_helper import get_llm
        llm = get_llm(model="gpt-4o", temperature=0.7)
        messages = [
            {
                "role": "system",
                "content": (
                    f"You are a creative greeting card writer. Write a heartfelt {occasion} "
                    f"greeting card for {name}. Include a title line, a warm message (2-3 sentences), "
                    "and a closing. Keep it sincere and personal."
                ),
            },
            {"role": "user", "content": f"Write a {occasion} greeting card for: {name}"},
        ]
        response = await llm.ainvoke(messages)
        card_text = response.content
    else:
        card_text = (
            f"--- Greeting Card ---\n\n"
            f"Dear {name},\n\n"
            f"Wishing you all the best on this {occasion} occasion! "
            f"May your day be filled with joy and happiness.\n\n"
            f"With warm regards,\n"
            f"Your AI Assistant"
        )

    # Agent sees a short summary (saves context window)
    agent_summary = f"Greeting card created for {name}"

    # UI sees the full card (for rendering in the assistant panel)
    forwarded = {
        "event_type": "GREETING_CARD_REVIEW",
        "card_text": card_text,
        "metadata": {
            "name": name,
            "occasion": occasion,
            "word_count": len(card_text.split()),
        },
    }

    return forwarded_tool_result(agent_summary, forwarded)

mcp.tool(name="greet_card", meta={"display_name": "Greeting Card"})(_greet_card)


# -- Simple tool (no forwarded blocks, for comparison) -------------------------

@mcp.tool
async def greet(
    name: Annotated[str, Field(description="The person's name to greet")],
) -> dict:
    """Generate a greeting -- simple tool with no forwarded blocks."""
    return {"message": f"Hello, {name}!"}


# ============================================================================
# Client demo: call_tool vs call_tool_mcp
# ============================================================================

async def main():
    async with Client(mcp) as client:
        # -- 1. Simple tool (no meta) -----------------------------------------
        print("=== 1. Simple Tool (call_tool) ===\n")
        r1 = await client.call_tool("greet", {"name": "Alice"})
        print(f"  call_tool result: {r1}")
        print()

        # -- 2. Greeting card with forwarded blocks ---------------------------
        print("=== 2. Greeting Card (call_tool - agent sees summary only) ===\n")
        r2 = await client.call_tool("greet_card", {"name": "Bob", "occasion": "birthday"})
        print(f"  call_tool result (agent view):")
        print(f"    {r2}")
        print()

        # -- 3. call_tool_mcp preserves _meta ---------------------------------
        print("=== 3. Greeting Card (call_tool_mcp - preserves _meta) ===\n")
        r3 = await client.call_tool_mcp("greet_card", {"name": "Bob"})
        print(f"  call_tool_mcp result type: {type(r3).__name__}")
        print(f"  Content blocks: {len(r3.content)}")

        for i, block in enumerate(r3.content):
            block_type = getattr(block, "type", "unknown")
            print(f"\n  Block {i} (type={block_type}):")

            if hasattr(block, "text"):
                # Check for forwarded blocks in _meta
                meta = getattr(block, "meta", None)
                if meta and hasattr(meta, "forwarded_blocks") and meta.forwarded_blocks:
                    print(f"    Agent text: {block.text[:100]}...")
                    print(f"    Forwarded blocks: {len(meta.forwarded_blocks)}")
                    for j, fb in enumerate(meta.forwarded_blocks):
                        fb_text = getattr(fb, "text", str(fb))
                        try:
                            parsed = json.loads(fb_text)
                            print(f"      Block {j} event_type: {parsed.get('event_type')}")
                            print(f"      Block {j} word_count: {parsed.get('metadata', {}).get('word_count')}")
                            print(f"      Block {j} card preview: {parsed.get('card_text', '')[:200]}...")
                        except (json.JSONDecodeError, AttributeError):
                            print(f"      Block {j}: {str(fb_text)[:100]}...")
                else:
                    print(f"    Text: {block.text[:100]}...")
        print()


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Forwarded blocks solve the "agent context vs UI display" problem:
    #
    #   Agent sees:  "Greeting card created for Bob"
    #                (short, saves context window)
    #
    #   UI sees:     Full card text + event_type + metadata
    #                (rich, for rendering in the assistant panel)
    #
    # Production uses this for ALL story drafts:
    #   - generate_spot_story -> forwarded_tool_result(summary, full_draft)
    #   - generate_urgent     -> forwarded_tool_result(summary, full_draft)
    #   - generate_news_buzz  -> forwarded_tool_result(summary, full_draft)
    #
    # The backend's mcp_protocol.py extracts forwarded_blocks from _meta
    # and sends them to the frontend separately from the agent's context.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a "farewell_card" tool using the same forwarded pattern
    # 2. Include multiple forwarded blocks (e.g., card + metadata block)
    # 3. Compare call_tool() output vs call_tool_mcp() in detail
