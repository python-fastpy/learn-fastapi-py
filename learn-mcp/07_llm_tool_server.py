"""Lesson 07 -- Tools That Call LLMs
=====================================
Concepts:
  - LLM as implementation detail inside MCP tools
  - get_llm() from llm_helper to connect to TR Orchestrator
  - Async LLM calls within tool functions
  - Prompt engineering inside tool logic
  - Returning generated content as structured dict

Flow:
  +--------+     +------------------+     +-------------------+
  | Client | --> | MCP Server       | --> | Tool              |
  +--------+     | "llm-tools"      |     |   summarize()     |
                 +------------------+     |   +-- get_llm() --|---> TR Orchestrator
                                          |   |               |     (Azure OpenAI)
                                          |   <-- LLM resp ---|
                                          |   return dict     |
                                          +-------------------+

  Maps to:
    story-drafting/src/tools/generate_spot_story.py (LLM inside tool)
    shared/llm/orchestrator.py (LLM client setup)

** Requires .env with TR Orchestrator credentials **

Run:  uv run python 07_llm_tool_server.py
"""

import asyncio
import os
from typing import Annotated, Optional
from pydantic import Field
from fastmcp import FastMCP, Client
from dotenv import load_dotenv

load_dotenv()


mcp = FastMCP(name="llm-tools")


def _has_env():
    """Check if LLM credentials are configured."""
    return bool(os.getenv("ORCHESTRATOR_ENDPOINT"))


# -- Tool 1: Summarize text using LLM -----------------------------------------

async def _summarize_text(
    text: Annotated[str, Field(description="Text to summarize")],
    style: Annotated[str, Field(default="concise", description="Style: concise, detailed, or bullet")] = "concise",
) -> dict:
    """Summarize text using an LLM. Demonstrates LLM-as-implementation-detail."""
    from llm_helper import get_llm

    llm = get_llm(model="gpt-4o", temperature=0.1)

    style_instructions = {
        "concise": "Summarize in 1-2 sentences.",
        "detailed": "Provide a detailed summary with key points.",
        "bullet": "Summarize as 3-5 bullet points.",
    }
    instruction = style_instructions.get(style, style_instructions["concise"])

    messages = [
        {"role": "system", "content": f"You are a Reuters news editor. {instruction}"},
        {"role": "user", "content": f"Summarize this text:\n\n{text}"},
    ]

    response = await llm.ainvoke(messages)

    return {
        "summary": response.content,
        "style": style,
        "input_length": len(text),
        "output_length": len(response.content),
    }

mcp.tool(name="summarize_text", meta={"display_name": "Summarize Text"})(_summarize_text)


# -- Tool 2: Generate headline from event description -------------------------

async def _generate_headline(
    event: Annotated[str, Field(description="Description of the news event")],
    max_length: Annotated[int, Field(default=80, description="Max headline length")] = 80,
) -> dict:
    """Generate a Reuters-style headline using LLM."""
    from llm_helper import get_llm

    llm = get_llm(model="gpt-4o", temperature=0.3)

    messages = [
        {
            "role": "system",
            "content": (
                f"You are a Reuters headline writer. Write a single headline, "
                f"max {max_length} characters. Start with the key fact. "
                f"No clickbait. No quotes around the headline. Just the headline text."
            ),
        },
        {"role": "user", "content": f"Write a headline for: {event}"},
    ]

    response = await llm.ainvoke(messages)
    headline = response.content.strip().strip('"').strip("'")

    return {
        "headline": headline,
        "length": len(headline),
        "within_limit": len(headline) <= max_length,
    }

mcp.tool(name="generate_headline", meta={"display_name": "Generate Headline"})(_generate_headline)


# -- Tool 3: Classify content (non-generative LLM use) ------------------------

async def _classify_content(
    text: Annotated[str, Field(description="Text to classify")],
) -> dict:
    """Classify news content by topic and sentiment using LLM."""
    from llm_helper import get_llm

    llm = get_llm(model="gpt-4o", temperature=0.0)

    messages = [
        {
            "role": "system",
            "content": (
                "Classify the following text. Respond with ONLY a JSON object "
                "(no markdown, no code fences) with these exact keys: "
                '"topic" (one of: markets, energy, politics, tech, other), '
                '"sentiment" (one of: positive, negative, neutral), '
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

mcp.tool(name="classify_content", meta={"display_name": "Classify Content"})(_classify_content)


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
        # Tool 1: Summarize
        print("--- summarize_text ---")
        r1 = await client.call_tool("summarize_text", {
            "text": (
                "Oil prices rose more than 2% on Monday after OPEC+ agreed to extend "
                "production cuts through the end of 2025. Brent crude futures settled at "
                "$78.50 a barrel, up $1.65. The decision came after weekend talks in Vienna "
                "where Saudi Arabia pushed for deeper cuts to support prices amid concerns "
                "about slowing Chinese demand."
            ),
            "style": "bullet",
        })
        print(f"  {r1}\n")

        # Tool 2: Generate headline
        print("--- generate_headline ---")
        r2 = await client.call_tool("generate_headline", {
            "event": "Federal Reserve raises interest rates by 25 basis points, signals pause in tightening cycle",
            "max_length": 80,
        })
        print(f"  {r2}\n")

        # Tool 3: Classify
        print("--- classify_content ---")
        r3 = await client.call_tool("classify_content", {
            "text": "Tesla stock surged 8% after the company reported record quarterly deliveries, beating analyst expectations.",
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
    #   Client sees: call_tool("summarize_text", {text: "..."})
    #   Tool does:   llm.ainvoke(prompt) internally
    #   Client gets: {summary: "...", style: "...", ...}
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a "translate" tool that translates text to a target language
    # 2. Add a "fact_check" tool that asks the LLM to verify claims
    # 3. Try different models (gpt-4-1, o4-mini) and compare outputs
