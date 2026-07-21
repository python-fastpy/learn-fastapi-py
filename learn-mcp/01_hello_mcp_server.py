"""Lesson 01 -- Your First MCP Server
======================================
Concepts:
  - FastMCP: the server framework for building MCP-compliant tools
  - @mcp.tool: decorator to register a tool function
  - Annotated[type, Field(description="...")]: parameter metadata
  - Client(server): in-process client -- no HTTP needed for testing
  - Tools are async functions that return dicts

Flow:
  +--------+     +------------+     +--------+
  | Client | --> | MCP Server | --> | Tool   |
  +--------+     +------------+     +--------+
       |              |                  |
       |   list_tools()                  |
       |   call_tool("greet", {name})    |
       |              +--- greet() ------+
       |   <-- result dict               |
       +----------------------------------

  Maps to: story-drafting/src/main.py (FastMCP constructor + tool registration)

No LLM needed -- pure MCP protocol mechanics.

Run:  uv run python 01_hello_mcp_server.py
"""

import asyncio
from typing import Annotated
from pydantic import Field
from fastmcp import FastMCP, Client


# -- Step 1: Create a FastMCP server -------------------------------------------
# This is the same pattern as story-drafting/src/main.py:
#   mcp: FastMCP = FastMCP(name="story-drafting")

mcp = FastMCP(name="hello-mcp")


# -- Step 2: Register a tool with the @mcp.tool decorator ----------------------
# The decorator automatically extracts the function signature and docstring
# to build the MCP tool schema. Annotated + Field gives parameter descriptions.

@mcp.tool
async def greet(
    name: Annotated[str, Field(description="The person's name to greet")],
) -> dict:
    """Generate a personalized greeting."""
    return {
        "greeting": f"Hello, {name}! Welcome to MCP.",
        "server": "hello-mcp",
    }


# -- Step 3: Use an in-process Client to call the tool -------------------------
# FastMCP supports passing the server object directly to Client().
# No HTTP server needed -- great for testing and learning.

async def main():
    # Connect client directly to the server object (in-process transport)
    async with Client(mcp) as client:

        # Discover available tools
        tools = await client.list_tools()
        print("=== Available Tools ===")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
            if tool.inputSchema.get("properties"):
                for param, schema in tool.inputSchema["properties"].items():
                    print(f"      param '{param}': {schema.get('description', 'no description')}")
        print()

        # Call the tool
        result = await client.call_tool("greet", {"name": "Shubham"})
        print("=== Tool Result ===")
        print(f"  {result}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # FastMCP makes building MCP servers simple:
    #   1. Create: mcp = FastMCP(name="...")
    #   2. Register: @mcp.tool on async functions
    #   3. Test: Client(mcp) connects in-process
    #
    # The protocol handles schema generation, validation, and transport
    # automatically -- you just write Python functions.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a second tool `farewell(name: str) -> dict` that says goodbye
    # 2. Call both tools from the client
    # 3. Observe how list_tools() shows both tools
