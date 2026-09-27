"""Lesson 09 -- Forwarded Blocks: data the LLM never sees
=========================================================

One greet result, two readers:

  1. AGENT TEXT      "Greeting card ready for Shubham (18 words)"  -> the LLM
  2. FORWARDED BLOCK the full card + metadata, as JSON             -> the UI

The agent doesn't need the whole card to decide what to do next, and every
token it reads costs context window. So the card rides along out-of-band in
the content block's _meta, and the backend routes it to the frontend instead
of into the conversation.

  ┌──────── MCP SERVER "forwarded-greetings" ────────┐
  │ greet("Shubham") returns ONE text block:         │
  │                                                  │
  │   text   "Greeting card ready for Shubham ..."   │
  │   _meta  {"forwarded_blocks":                    │
  │             [ {"type":"text","text":"{card...}"} │
  │           ]}                                     │
  └──────────────────────┬───────────────────────────┘
                         │  tools/call result
              ┌──────────┴───────────┐
              ▼                      ▼
        block.text              block.meta["forwarded_blocks"]
     into the LLM's             to the frontend, NOT to the LLM
     context window             (full card, event_type, word_count)
              │                      │
              ▼                      ▼
     agent decides the         UI renders the card for
     next tool call            the user to review

  The split is the BACKEND's choice, not a transport feature: one result
  arrives, and the backend decides which part becomes agent context.
  (call_tool and call_tool_mcp both preserve _meta -- they differ only in
  error handling: call_tool raises, call_tool_mcp returns is_error instead.)

Run:  uv run python 09_tool_result_meta.py

Maps to: shared/forwarded.py (forwarded_tool_result), mcp_protocol.py
(_call_tool_result_to_dict pulls forwarded blocks out of _meta)
"""

import asyncio
import json
from fastmcp import FastMCP, Client
from fastmcp.tools import ToolResult
from mcp.types import TextContent

mcp = FastMCP(name="forwarded-greetings")


def forwarded_tool_result(agent_text: str, payload: dict) -> ToolResult:
    """Short text for the agent + an out-of-band payload for the UI.

    Mirrors shared/forwarded.py. The _meta must sit on the CONTENT BLOCK
    (TextContent(_meta=...)), not on the ToolResult -- result-level meta is
    where per-call logging/timing goes instead (lesson 05).
    """
    return ToolResult(
        content=[
            TextContent(
                type="text",
                text=agent_text,
                _meta={"forwarded_blocks": [{"type": "text", "text": json.dumps(payload)}]},
            )
        ]
    )


@mcp.tool
def greet(name: str) -> ToolResult:
    """Write a greeting card. The agent gets a summary, the UI gets the card."""
    card = (
        f"Dear {name},\n\n"
        f"Welcome aboard! We are delighted to have you with us.\n\n"
        f"Warmly,\nThe Team"
    )
    words = len(card.split())

    return forwarded_tool_result(
        f"Greeting card ready for {name} ({words} words)",      # 1. the agent reads this
        {                                                        # 2. the UI reads this
            "event_type": "GREETING_CARD_REVIEW",                #    which screen to render
            "card_text": card,
            "metadata": {"name": name, "word_count": words},
        },
    )


async def main():
    async with Client(mcp) as client:
        r = await client.call_tool("greet", {"name": "Shubham"})
        block = r.content[0]

        # 1. AGENT VIEW -- the only part that would enter the LLM's context
        print("1. agent text        :", block.text)

        # 2. UI VIEW -- block.meta is a plain dict; forwarded_blocks is a list
        blocks = block.meta["forwarded_blocks"]
        payload = json.loads(blocks[0]["text"])
        print("2. forwarded blocks  :", len(blocks))
        print("   event_type        :", payload["event_type"])
        print("   word_count        :", payload["metadata"]["word_count"])
        print("   card_text         :", payload["card_text"].replace("\n", " ")[:48], "...")

        # 3. The saving: the agent read one short line instead of the whole card
        print(f"\n3. agent read {len(block.text)} chars; the UI got {len(blocks[0]['text'])} chars.")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Add a second forwarded block (e.g. the metadata as its own block) and
#    print both.
# 2. Move the payload to ToolResult(meta=...) instead. Read it with r.meta --
#    which reader does that serve? (lesson 05)
# 3. Call with call_tool_mcp and print m.content[0].meta -- same _meta. Then
#    make greet raise and compare how call_tool and call_tool_mcp report it.
