"""Lesson 08 -- A Tool That Calls an LLM
=======================================

An MCP tool is just a function, so it can call an LLM. The LLM is an
IMPLEMENTATION DETAIL: the client calls "greet" and gets a greeting back.
Nothing in the request or the result says a model was involved.

  ┌───── MCP CLIENT ─────┐               ┌──── MCP SERVER "llm-greetings" ─────┐
  │ call_tool("greet",   │  tools/call   │ greet(name, occasion) runs:         │
  │  {"name": "Shubham", │ ────────────► │                                     │
  │   "occasion":        │               │ 1. llm = get_llm("gpt-4o", 0.7)     │
  │      "birthday"})    │               │ 2. build messages from the args     │
  │                      │               │ 3. await llm.ainvoke(messages) ─────┼──► TR Orchestrator
  │                      │               │                    ◄────────────────┼─── (Azure OpenAI)
  │ {"greeting": "Happy  │ ◄──────────── │ 4. return {"greeting": ...} -- a    │
  │   birthday, ..."}    │               │    plain dict, same as lesson 01    │
  └──────────────────────┘               └─────────────────────────────────────┘

  1. get_llm() INSIDE the tool, not at import time -- the server then starts
     without credentials and only this one tool fails.
  2. The prompt is built from the tool's own arguments.
  3. await llm.ainvoke(...) -- async, so the server still serves other calls
     while the model is thinking.
  4. Return a plain dict. The client sees an ordinary MCP result (lesson 01).

  temperature: 0.0 = repeatable (classifying), 0.7 = creative (writing).

** Requires .env with TR Orchestrator credentials (see llm_helper.py).
   Without it, this lesson prints the tool schema and stops. **

Run:  uv run python 08_llm_tool_server.py

Maps to: story-drafting/src/tools/generate_spot_story.py (LLM inside a tool)
"""

import asyncio
import os
from dotenv import load_dotenv
from fastmcp import FastMCP, Client

load_dotenv()

mcp = FastMCP(name="llm-greetings")


@mcp.tool
async def greet(name: str, occasion: str = "general") -> dict:
    """Write a short creative greeting. occasion: general, birthday, farewell."""
    from llm_helper import get_llm                      # 1. imported here, not at module level

    llm = get_llm(model="gpt-4o", temperature=0.7)      #    0.7 -> creative
    messages = [                                        # 2. prompt built from the arguments
        {"role": "system", "content": "You write greetings. 1-2 sentences, warm, no preamble."},
        {"role": "user", "content": f"Write a {occasion} greeting for {name}."},
    ]
    response = await llm.ainvoke(messages)              # 3. the only new line vs lesson 01

    return {"greeting": response.content, "name": name, "occasion": occasion}   # 4. plain dict


async def main():
    async with Client(mcp) as client:
        if not os.getenv("ORCHESTRATOR_ENDPOINT"):
            t = (await client.list_tools())[0]
            print("No .env -- showing the schema only. Copy .env.example to .env for real calls.\n")
            print(f"  tool  : {t.name}")
            print(f"  desc  : {t.description}")
            print(f"  params: {list(t.inputSchema['properties'])}")
            return

        # The client call looks identical to lesson 01 -- the LLM is invisible here.
        r = await client.call_tool("greet", {"name": "Shubham", "occasion": "birthday"})
        print("greet ->", r.data["greeting"])


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Set temperature=0.0 and call twice -- is the greeting identical?
# 2. Swap gpt-4o for o4-mini (see MODELS in llm_helper.py). Faster? Different?
# 3. raise ToolError("name cannot be empty") for a blank name (lesson 01) --
#    the LLM sees that error text and can retry with a real name.
