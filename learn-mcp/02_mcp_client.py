"""
Lesson 2: MCP Client
=====================
Goal: Connect to an MCP server programmatically and call tools.

What you'll learn:
  - fastmcp.Client for calling MCP servers
  - The JSON-RPC handshake (initialize -> notifications/initialized)
  - list_tools() and call_tool()
  - Inspecting CallToolResult

Run:
  uv run python 02_mcp_client.py

  (No need to start the server separately — the client launches it
   via stdio transport automatically)

Production parallel:
  reuters-assistant_backend/src/services/mcp_protocol.py does exactly this
  with StreamableHttpTransport instead of stdio. Each tool call creates a
  one-shot client for tenant header isolation.
"""

import asyncio
from fastmcp import Client


async def main():
    # --- Step 1: Connect to the server ---
    # Passing a .py file starts it as a subprocess via stdio.
    # In production, you'd use StreamableHttpTransport with a URL.
    client = Client("01_hello_mcp_server.py")

    async with client:
        # The SDK automatically performs the 3-step handshake:
        #   1. POST initialize (capabilities exchange)
        #   2. Response with server capabilities
        #   3. POST notifications/initialized

        # --- Step 2: Discover available tools ---
        tools = await client.list_tools()
        print("=== Available Tools ===")
        for tool in tools:
            print(f"  {tool.name}: {tool.description}")
            if tool.inputSchema:
                props = tool.inputSchema.get("properties", {})
                for param, schema in props.items():
                    print(f"    - {param}: {schema.get('type', '?')}")
        print()

        # --- Step 3: Call tools ---
        print("=== Calling greet ===")
        result = await client.call_tool("greet", {"name": "Shubham"})
        print(f"  Result: {result}")
        # result is a list of Content blocks
        for content in result:
            print(f"  Content type: {content.type}, text: {content.text}")
        print()

        print("=== Calling add_numbers ===")
        result = await client.call_tool("add_numbers", {"a": 42, "b": 58})
        for content in result:
            print(f"  Result: {content.text}")
        print()

        print("=== Calling word_count ===")
        result = await client.call_tool(
            "word_count",
            {"text": "Reuters AI Assistant uses MCP for skill execution"},
        )
        for content in result:
            print(f"  Result: {content.text}")


if __name__ == "__main__":
    asyncio.run(main())


# ============================================================
# EXERCISES:
#
# 1. Try calling a tool with wrong parameter types — what error
#    do you get? How does MCP validate inputs?
# 2. Call a tool that doesn't exist — what's the error?
# 3. Print the raw tool.inputSchema to see the JSON Schema
#    that FastMCP auto-generated from your type hints
# ============================================================
