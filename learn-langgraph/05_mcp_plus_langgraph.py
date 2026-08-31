"""
Lesson 11 (LangGraph 5): MCP + LangGraph — The Production Pattern
===================================================================
Goal: Build a LangGraph agent that discovers and calls MCP tools dynamically.
This is THE exact architecture used in the Reuters AI Assistant backend.

What you'll learn:
  - Loading MCP tools into LangGraph at runtime
  - The agent loop: LLM picks MCP tool -> execute via MCP client -> loop
  - Combining LangGraph state management with MCP tool execution

Run (two terminals):
  Terminal 1:  uv run python 05_mcp_plus_langgraph.py --server
  Terminal 2:  uv run python 05_mcp_plus_langgraph.py --agent

  OR run in-process (no server needed):
  uv run python 05_mcp_plus_langgraph.py --local

Production parallel:
  langgraph_mcp_orchestrator.py does exactly this:
  1. On startup, discovers tools from registered MCP servers
  2. Converts MCP tool schemas to LangChain tool definitions
  3. Binds them to the LLM
  4. Agent loop calls MCP tools via mcp_protocol.py
"""

import asyncio
import json
import os
import operator
import sys
from typing import TypedDict, Annotated

from dotenv import load_dotenv
from fastmcp import FastMCP, Client
from fastmcp.client.transports import StreamableHttpTransport
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolMessage, AIMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import StateGraph, START, END

load_dotenv()


# ===== MCP SERVER (the "skill") =====

def create_skill_server() -> FastMCP:
    mcp = FastMCP("reuters-news-skill")

    @mcp.tool()
    def validate_ric(ric: str) -> dict:
        """Validate a Reuters Instrument Code (RIC) and return instrument info."""
        known = {
            "AAPL.O": {"name": "Apple Inc", "exchange": "NASDAQ", "currency": "USD"},
            "MSFT.O": {"name": "Microsoft Corp", "exchange": "NASDAQ", "currency": "USD"},
            "TSLA.O": {"name": "Tesla Inc", "exchange": "NASDAQ", "currency": "USD"},
        }
        info = known.get(ric)
        if info:
            return {"valid": True, "ric": ric, **info}
        return {"valid": False, "ric": ric, "error": "Unknown RIC"}

    @mcp.tool()
    def fetch_headlines(ric: str, limit: int = 3) -> list[dict]:
        """Fetch recent news headlines for a given RIC."""
        return [
            {"id": f"HL{i+1}", "text": f"{ric} headline {i+1}: Market activity noted", "time": f"14:0{i}"}
            for i in range(limit)
        ]

    @mcp.tool()
    def generate_news_buzz(ric: str, headline_ids: list[str]) -> dict:
        """Generate a news buzz draft from selected headlines."""
        return {
            "draft": f"BUZZ - {ric}: Company sees significant activity based on {len(headline_ids)} headlines.",
            "word_count": 12,
            "status": "completed",
        }

    return mcp


# ===== MCP -> LANGCHAIN BRIDGE =====

async def load_mcp_tools_as_langchain(mcp_client: Client) -> list[StructuredTool]:
    """Discover MCP tools and wrap them as LangChain StructuredTools.

    This is the bridge between MCP and LangGraph. In production,
    mcp_server_registry.py caches these tool definitions.
    """
    mcp_tools = await mcp_client.list_tools()
    langchain_tools = []

    for mcp_tool in mcp_tools:
        tool_name = mcp_tool.name
        tool_desc = mcp_tool.description or ""
        schema = mcp_tool.inputSchema or {}

        async def _call_mcp(tool_name=tool_name, **kwargs):
            result = await mcp_client.call_tool(tool_name, kwargs)
            texts = [c.text for c in result if hasattr(c, "text")]
            return "\n".join(texts) if texts else "No result"

        # Build a StructuredTool that calls the MCP server
        lc_tool = StructuredTool.from_function(
            func=lambda **kw, _tn=tool_name: asyncio.get_event_loop().run_until_complete(
                _call_mcp(tool_name=_tn, **kw)
            ),
            coroutine=lambda **kw, _tn=tool_name: _call_mcp(tool_name=_tn, **kw),
            name=tool_name,
            description=tool_desc,
            args_schema=None,  # rely on the LLM to pass correct args
        )
        langchain_tools.append(lc_tool)

    return langchain_tools


# ===== LANGGRAPH AGENT =====

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]


async def build_and_run_agent(mcp_client: Client, query: str):
    """Build a LangGraph agent wired to MCP tools and run a query."""

    # Step 1: Discover MCP tools
    tools = await load_mcp_tools_as_langchain(mcp_client)
    tool_map = {t.name: t for t in tools}

    print(f"Discovered {len(tools)} MCP tools:")
    for t in tools:
        print(f"  - {t.name}: {t.description[:60]}...")
    print()

    # Step 2: Check for LLM credentials
    api_key = os.getenv("LEON_ORCHESTRATOR_API_KEY", "")

    if api_key:
        from langchain_openai import AzureChatOpenAI
        endpoint = os.getenv("ORCHESTRATOR_ENDPOINT", "https://llmorch-ha.int.thomsonreuters.com")
        llm = AzureChatOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-08-01-preview",
            model="gpt-4o",
            temperature=0,
        ).bind_tools(tools)
    else:
        llm = None

    if not llm:
        # Mock mode: simulate the agent loop without an LLM
        print("=== Mock Agent Loop (no LLM credentials) ===")
        print(f"Query: {query}\n")

        print("Step 1: Agent would call validate_ric(ric='AAPL.O')")
        r1 = await mcp_client.call_tool("validate_ric", {"ric": "AAPL.O"})
        print(f"  Result: {r1[0].text}\n")

        print("Step 2: Agent would call fetch_headlines(ric='AAPL.O')")
        r2 = await mcp_client.call_tool("fetch_headlines", {"ric": "AAPL.O", "limit": 3})
        print(f"  Result: {r2[0].text}\n")

        print("Step 3: Agent would call generate_news_buzz(ric='AAPL.O', headline_ids=['HL1','HL2'])")
        r3 = await mcp_client.call_tool("generate_news_buzz", {"ric": "AAPL.O", "headline_ids": ["HL1", "HL2"]})
        print(f"  Result: {r3[0].text}\n")

        print("This is exactly what the production orchestrator does,")
        print("but the LLM decides which tools to call and in what order.")
        return

    # Step 3: Build the agent graph
    async def call_llm(state: AgentState) -> dict:
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    async def call_tools(state: AgentState) -> dict:
        last_msg = state["messages"][-1]
        tool_messages = []
        for tc in last_msg.tool_calls:
            tool = tool_map[tc["name"]]
            result = await tool.ainvoke(tc["args"])
            tool_messages.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )
        return {"messages": tool_messages}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return "end"

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_llm)
    graph.add_node("tools", call_tools)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")
    app = graph.compile()

    # Step 4: Run
    print(f"Query: {query}\n")
    result = await app.ainvoke({
        "messages": [
            SystemMessage(content="You are a Reuters news assistant. Use the available MCP tools to help."),
            HumanMessage(content=query),
        ]
    })

    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"  [Tool Call] {tc['name']}({tc['args']})")
        elif isinstance(msg, ToolMessage):
            print(f"  [Tool Result] {msg.content[:100]}...")
        elif isinstance(msg, AIMessage) and msg.content:
            print(f"  [Assistant] {msg.content[:200]}...")


# ===== MAIN =====

async def run_local():
    """Run everything in-process (no HTTP server needed)."""
    server = create_skill_server()
    client = Client(server)
    async with client:
        await build_and_run_agent(
            client,
            "Generate a news buzz for Apple (AAPL.O). Validate the RIC first, then fetch headlines."
        )


async def run_with_http():
    """Connect to the HTTP server started in another terminal."""
    transport = StreamableHttpTransport(
        url="http://localhost:8011/mcp",
        headers={"Authorization": "Bearer demo", "X-Tenant-ID": "learn"},
    )
    client = Client(transport=transport, timeout=60)
    async with client:
        await build_and_run_agent(
            client,
            "Generate a news buzz for Apple (AAPL.O). Validate the RIC first, then fetch headlines."
        )


if __name__ == "__main__":
    if "--server" in sys.argv:
        server = create_skill_server()
        print("Starting MCP skill server on http://localhost:8011/mcp")
        server.run(transport="http", host="0.0.0.0", port=8011)
    elif "--agent" in sys.argv:
        asyncio.run(run_with_http())
    elif "--local" in sys.argv:
        asyncio.run(run_local())
    else:
        print("Usage:")
        print("  --local    Run in-process (no server needed)")
        print("  --server   Start the MCP skill server (terminal 1)")
        print("  --agent    Run the LangGraph agent against the server (terminal 2)")


# ============================================================
# EXERCISES:
#
# 1. Add interrupt() after generate_news_buzz to implement
#    human review (combine lessons 4-5 with this pattern)
# 2. Add a second MCP server (e.g., text archive search) and
#    have the agent discover tools from both
# 3. Add MemorySaver checkpointing and test interrupt/resume
# ============================================================
