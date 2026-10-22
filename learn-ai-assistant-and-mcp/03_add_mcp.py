"""Step 3 -- Add MCP: now it works like Claude Code
=======================================================

Step 2's assistant had TOOL_SCHEMAS hand-written at the top of the file,
and called reading_list.add_book(...) directly -- it had to know Python
import paths for the app. This step removes BOTH of those. The assistant
now:

    1. connects to reading_list_mcp_server.py (a SEPARATE process, over
       stdio -- exactly like Claude Code launching an MCP server from
       your .mcp.json)
    2. asks it "what tools do you have?" at RUNTIME -- client.list_tools()
    3. builds the schemas the model sees FROM that discovery, not from
       anything hand-written
    4. when the model calls a tool, sends it to the SERVER over MCP --
       client.call_tool(name, arguments) -- instead of calling a Python
       function directly

    step 2                                   step 3 (this file)
    TOOL_SCHEMAS = [...]  <- hand-written     tools = await client.list_tools()
    TOOLS["add_book"](**args)                 await client.call_tool(name, args)
    (assistant imports reading_list.py)       (assistant imports NOTHING app-specific)

THIS is "just like Claude Code": the assistant's code has zero knowledge
of what the server does. Point it at a DIFFERENT MCP server (a weather
server, a database server, learn-fastmcp-server's target_server.py,
anything) and this file does not change at all -- only which server you
launch does. That's exactly what Claude Code's .mcp.json does: name a
server, and every tool it offers shows up with no code change on the
assistant/host side. (learn-mini-claude goes further with this same idea
-- a real .mcp.json config file, multiple servers at once, a CLI and a
web UI. Read that project next if you want to go deeper than this file.)

Run:  uv run python 03_add_mcp.py
"""

import json
import os

from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport

load_dotenv()


def mcp_tool_to_openai_schema(tool) -> dict:
    """The only piece of 'translation' needed: MCP's tool shape is already
    JSON Schema, so this is just renaming fields into the OpenAI shape."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


async def run_assistant(request: str, max_steps: int = 6) -> str:
    from llm_client import call_llm   # deferred so --help works without a live connection

    async with Client(PythonStdioTransport("reading_list_mcp_server.py", args=["--stdio"])) as client:
        # 1 + 2 + 3: discover tools, build schemas -- no hardcoded list anywhere
        mcp_tools = await client.list_tools()
        tool_schemas = [mcp_tool_to_openai_schema(t) for t in mcp_tools]
        print(f"discovered {len(mcp_tools)} tools from the server: {[t.name for t in mcp_tools]}\n")

        print(f"you: {request!r}")
        messages: list[dict] = [{"role": "user", "content": request}]

        for _ in range(max_steps):
            message = call_llm(messages, tools=tool_schemas)

            if not message.get("tool_calls"):
                print(f"assistant: {message['content']}")
                return message["content"]

            messages.append(message)
            for call in message["tool_calls"]:
                name = call["function"]["name"]
                arguments = json.loads(call["function"]["arguments"])
                # 4: call the SERVER over MCP, not a Python function
                result = (await client.call_tool(name, arguments)).data
                print(f"  [mcp call] {name}({arguments}) -> {result}")
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})

    raise RuntimeError(f"no final answer after {max_steps} steps")


if __name__ == "__main__":
    import asyncio

    if not os.getenv("LEON_ORCHESTRATOR_API_KEY"):
        print("No .env found -- copy .env.example to .env and fill in credentials to run this.")
    else:
        asyncio.run(run_assistant(
            "Add 'Dune' by Frank Herbert and 'Klara and the Sun' by Kazuo Ishiguro, "
            "mark Dune as reading, then show me the full list."
        ))

# Example output (wording varies -- the model is not deterministic -- but
# the "discovered 4 tools" line and the tool-call sequence should match):
#
# discovered 4 tools from the server: ['add_book', 'list_books', 'mark_status', 'remove_book']
#
# you: "Add 'Dune' by Frank Herbert and 'Klara and the Sun' by Kazuo Ishiguro, mark Dune as reading, then show me the full list."
#   [mcp call] add_book({'title': 'Dune', 'author': 'Frank Herbert'}) -> {'id': 1, ...}
#   [mcp call] add_book({'title': 'Klara and the Sun', 'author': 'Kazuo Ishiguro'}) -> {'id': 2, ...}
#   [mcp call] mark_status({'book_id': 1, 'status': 'reading'}) -> {'id': 1, ..., 'status': 'reading'}
#   [mcp call] list_books({}) -> [{'id': 1, ..., 'status': 'reading'}, {'id': 2, ...}]
# assistant: Done! Here's your reading list: ...
