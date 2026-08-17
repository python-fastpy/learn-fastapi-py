"""Lesson 07 -- Tools That Call LLMs
=====================================

WHY THIS MATTERS:
  An MCP tool doesn't have to be a simple function. In production,
  generate_spot_story calls GPT-4o to actually *write* the story.
  The LLM is an implementation detail -- the client just calls
  "generate_spot_story" and gets back a draft. It doesn't know or
  care that an LLM was involved. This pattern is the core of every
  drafting skill.

WHAT YOU'LL LEARN:
  1. Call an LLM from inside a tool using get_llm()
  2. Construct prompts within tool logic
  3. Return LLM-generated content as structured data
  4. Handle the case where credentials aren't available (mock fallback)

Concepts:
  - LLM as implementation detail inside MCP tools
  - get_llm() from llm_helper to connect to TR Orchestrator
  - Async LLM calls within tool functions
  - Prompt engineering inside tool logic

Flow:
  +--------+     +------------------+     +-------------------+
  | Client | --> | MCP Server       | --> | Tool              |
  +--------+     | "llm-tools"      |     |   creative_greet()|
                 +------------------+     |   +-- get_llm() --|---> TR Orchestrator
                                          |   |               |     (Azure OpenAI)
                                          |   <-- LLM resp ---|
                                          |   return dict     |
                                          +-------------------+

  Maps to:
    story-drafting/src/tools/generate_spot_story.py (LLM inside tool)
    shared/llm/orchestrator.py (LLM client setup)

PREREQUISITES: Lesson 01 (tools), llm_helper.py (credentials)

** Requires .env with TR Orchestrator credentials **

Run:  uv run python 07_llm_tool_server.py

EXPECTED OUTPUT (without .env -- schema-only mode):
  === LLM Tools Demo (NO .env - showing tool schemas only) ===

  Tool: creative_greet
    Description: Generate a creative, personalized greeting using an LLM. ...
    Parameters: ['name', 'occasion']

  Tool: farewell_poem
    Description: Generate a short farewell poem using an LLM. ...
    Parameters: ['name']

  Tool: detect_mood
    Description: Detect the mood/sentiment of text using an LLM. ...
    Parameters: ['text']

  To run with real LLM calls, create a .env file from .env.example

EXPECTED OUTPUT (with .env -- real LLM calls):
  === LLM Tools Demo (with real LLM calls) ===

  --- creative_greet ---
    [TextContent(... greeting: <LLM-generated creative greeting for Alice's birthday> ...)]

  --- farewell_poem ---
    [TextContent(... poem: <LLM-generated 2-4 line farewell poem for Bob> ...)]

  --- detect_mood ---
    [TextContent(... mood: 'excited', confidence: 0.95 ...)]
"""

import asyncio
import os
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client
from dotenv import load_dotenv

load_dotenv()


mcp = FastMCP(name="llm-tools")


def _has_env():
    """Check if LLM credentials are configured."""
    return bool(os.getenv("ORCHESTRATOR_ENDPOINT"))


# -- Tool 1: Creative greeting using LLM ------------------------------------

async def _creative_greet(
    name: Annotated[str, Field(description="Name of the person to greet")],
    occasion: Annotated[str, Field(default="general", description="Occasion: general, birthday, promotion, farewell, holiday")] = "general",
) -> dict:
    """Generate a creative, personalized greeting using an LLM. Demonstrates LLM-as-implementation-detail."""
    from llm_helper import get_llm

    llm = get_llm(model="gpt-4o", temperature=0.7)

    messages = [
        {
            "role": "system",
            "content": (
                f"You are a greeting writer. Write a short, creative greeting "
                f"for {name} for the occasion: {occasion}. Keep it to 1-2 sentences."
            ),
        },
        {"role": "user", "content": f"Write a creative greeting for {name}."},
    ]

    response = await llm.ainvoke(messages)

    return {
        "greeting": response.content,
        "name": name,
        "occasion": occasion,
    }

mcp.tool(name="creative_greet", meta={"display_name": "Creative Greet"})(_creative_greet)


# -- Tool 2: Farewell poem using LLM ----------------------------------------

async def _farewell_poem(
    name: Annotated[str, Field(description="Name of the person to say farewell to")],
) -> dict:
    """Generate a short farewell poem using an LLM."""
    from llm_helper import get_llm

    llm = get_llm(model="gpt-4o", temperature=0.8)

    messages = [
        {
            "role": "system",
            "content": (
                f"Write a short farewell poem (2-4 lines) for {name}. "
                f"Keep it warm and brief."
            ),
        },
        {"role": "user", "content": f"Write a farewell poem for {name}."},
    ]

    response = await llm.ainvoke(messages)

    return {
        "poem": response.content,
        "name": name,
    }

mcp.tool(name="farewell_poem", meta={"display_name": "Farewell Poem"})(_farewell_poem)


# -- Tool 3: Detect mood (non-generative LLM use) ---------------------------

async def _detect_mood(
    text: Annotated[str, Field(description="Text to analyze for mood/sentiment")],
) -> dict:
    """Detect the mood/sentiment of text using an LLM."""
    from llm_helper import get_llm

    llm = get_llm(model="gpt-4o", temperature=0.0)

    messages = [
        {
            "role": "system",
            "content": (
                "Classify the mood of the following text. Respond with ONLY a JSON object "
                "(no markdown, no code fences) with these exact keys: "
                '"mood" (one of: happy, sad, neutral, excited), '
                '"confidence" (float 0-1).'
            ),
        },
        {"role": "user", "content": text},
    ]

    response = await llm.ainvoke(messages)

    import json
    try:
        classification = json.loads(response.content)
    except json.JSONDecodeError:
        classification = {"raw": response.content, "parse_error": True}

    return {"text_preview": text[:100], "classification": classification}

mcp.tool(name="detect_mood", meta={"display_name": "Detect Mood"})(_detect_mood)


# ============================================================================
# CLIENT DEMO
# ============================================================================

async def main():
    if not _has_env():
        print("=== LLM Tools Demo (NO .env - showing tool schemas only) ===\n")
        async with Client(mcp) as client:
            tools = await client.list_tools()
            for t in tools:
                print(f"Tool: {t.name}")
                print(f"  Description: {t.description}")
                print(f"  Parameters: {list(t.inputSchema.get('properties', {}).keys())}")
                print()
        print("To run with real LLM calls, create a .env file from .env.example")
        return

    print("=== LLM Tools Demo (with real LLM calls) ===\n")

    async with Client(mcp) as client:
        # Tool 1: Creative greeting
        print("--- creative_greet ---")
        r1 = await client.call_tool("creative_greet", {
            "name": "Alice",
            "occasion": "birthday",
        })
        print(f"  {r1}\n")

        # Tool 2: Farewell poem
        print("--- farewell_poem ---")
        r2 = await client.call_tool("farewell_poem", {
            "name": "Bob",
        })
        print(f"  {r2}\n")

        # Tool 3: Detect mood
        print("--- detect_mood ---")
        r3 = await client.call_tool("detect_mood", {
            "text": "I just got promoted! This is the best day ever!",
        })
        print(f"  {r3}\n")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # LLM calls are an IMPLEMENTATION DETAIL inside MCP tools.
    # The client doesn't know or care that the tool uses an LLM.
    # This is the exact pattern in your production skills:
    #
    #   generate_spot_story -> calls LLM to draft story
    #   generate_urgent     -> calls LLM to draft urgent
    #   generate_news_buzz  -> calls Gemini to draft buzz
    #
    # The MCP boundary keeps it clean:
    #   Client sees: call_tool("creative_greet", {name: "Alice", occasion: "birthday"})
    #   Tool does:   llm.ainvoke(prompt) internally
    #   Client gets: {greeting: "...", name: "Alice", occasion: "birthday"}
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a "greeting_card" tool that generates a full greeting card with
    #    a title, body, and sign-off using the LLM
    # 2. Add a "roast" tool that generates a playful, friendly roast greeting
    # 3. Try different models (gpt-4-1, o4-mini) and compare outputs
