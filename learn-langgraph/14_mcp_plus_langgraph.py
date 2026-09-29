"""Lesson 14 -- MCP + LangGraph: the production pattern
=======================================================

Lesson 06's tools were Python functions in the same file. Production tools
live in separate services and speak MCP. The graph does not change at all --
only where the tools come from. This is the bridge.

  ┌──── LangGraph (this file) ─────┐        ┌──── MCP server ("the skill") ──┐
  │                                │        │                               │
  │  at startup:                   │        │  validate_ric                 │
  │    list_tools() ───────────────┼───────►│  fetch_headlines              │
  │    wrap each as a              │◄───────┼─ name + description + schema  │
  │    StructuredTool              │        │  generate_news_buzz           │
  │         │                      │        │                               │
  │         ▼                      │        │                               │
  │  agent ◄─────────┐             │        │                               │
  │    │             │             │        │                               │
  │    ├─ tool_calls ► tools ──────┼───────►│  the tool actually runs here  │
  │    │               (calls MCP) │◄───────┼─ its result                   │
  │    └─ prose ► END              │        │                               │
  └────────────────────────────────┘        └───────────────────────────────┘

  1. DISCOVER      list_tools() at startup. The graph learns the tool names,
                   descriptions and schemas at RUNTIME -- nothing hardcoded.
  2. WRAP          each MCP tool becomes a StructuredTool whose coroutine
                   calls the MCP server. The model cannot tell the difference
                   from a local function.
  3. PASS THE SCHEMA  args_schema=<the MCP inputSchema>. Skip this and the
                   model is told the tool takes no arguments, then calls it
                   with none -- the single easiest way to break this bridge.
  4. LATE BINDING  `lambda _tn=tool_name, **kw:` pins THIS loop iteration's
                   name. Without the default, every wrapper would close over
                   the last tool in the list. (A default must precede **kw.)
  5. SAME LOOP     agent -> tools -> agent, exactly lesson 06. Only the tools
                   node changed.

  The result is that adding a tool means deploying a server, not editing this
  file.

** Requires .env with orchestrator credentials **

Run:  uv run python 14_mcp_plus_langgraph.py --local     (server in-process)
  or, two terminals:
      uv run python 14_mcp_plus_langgraph.py --server    (terminal 1, :8011)
      uv run python 14_mcp_plus_langgraph.py --agent      (terminal 2)

Maps to: langgraph_mcp_orchestrator.py -> does exactly this at startup;
mcp_server_registry.py -> caches the discovered definitions;
mcp_protocol.py -> the call itself
"""

import asyncio
import operator
import sys
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from fastmcp import Client, FastMCP
from fastmcp.client.transports import StreamableHttpTransport
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.graph import END, START, StateGraph

load_dotenv()


# -- The MCP server: a stand-in for a real skill ----------------------------

def create_skill_server() -> FastMCP:
    mcp = FastMCP("reuters-news-skill")

    @mcp.tool
    def validate_ric(ric: str) -> dict:
        """Validate a Reuters Instrument Code (RIC) and return instrument info."""
        known = {
            "AAPL.O": {"name": "Apple Inc", "exchange": "NASDAQ"},
            "MSFT.O": {"name": "Microsoft Corp", "exchange": "NASDAQ"},
        }
        info = known.get(ric)
        return {"valid": True, "ric": ric, **info} if info else {"valid": False, "ric": ric}

    @mcp.tool
    def fetch_headlines(ric: str, limit: int = 3) -> list[dict]:
        """Fetch recent news headlines for a given RIC."""
        return [{"id": f"HL{i+1}", "text": f"{ric} headline {i+1}"} for i in range(limit)]

    @mcp.tool
    def generate_news_buzz(ric: str, headline_ids: list[str]) -> dict:
        """Generate a news buzz draft from selected headlines."""
        return {"draft": f"BUZZ - {ric}: activity noted across {len(headline_ids)} headlines."}

    return mcp


# -- 1 + 2 + 3 + 4. The bridge: MCP tools -> LangChain tools ---------------

async def load_mcp_tools(client: Client) -> list[StructuredTool]:
    tools = []
    for mcp_tool in await client.list_tools():
        name = mcp_tool.name

        async def call(tool_name=name, **kwargs):
            result = await client.call_tool(tool_name, kwargs)
            return result.content[0].text if result.content else "No result"

        tools.append(StructuredTool.from_function(
            coroutine=lambda _tn=name, **kw: call(tool_name=_tn, **kw),   # 4.
            name=name,
            description=mcp_tool.description or "",
            args_schema=mcp_tool.input_schema or {},                      # 3.
        ))
    return tools


# -- 5. Lesson 06's loop, unchanged ----------------------------------------

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]


async def run_agent(client: Client, query: str) -> None:
    from llm_helper import get_llm

    tools = await load_mcp_tools(client)                  # 1.
    by_name = {t.name: t for t in tools}
    print(f"discovered {len(tools)} MCP tools: {list(by_name)}\n")

    llm = get_llm(model="gpt-4o", temperature=0).bind_tools(tools)

    async def agent(state: AgentState) -> dict:
        return {"messages": [await llm.ainvoke(state["messages"])]}

    async def call_tools(state: AgentState) -> dict:
        out = []
        for tc in state["messages"][-1].tool_calls:
            result = await by_name[tc["name"]].ainvoke(tc["args"])
            out.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        return {"messages": out}

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent)
    graph.add_node("tools", call_tools)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        lambda s: "tools" if getattr(s["messages"][-1], "tool_calls", None) else END,
        {"tools": "tools", END: END},
    )
    graph.add_edge("tools", "agent")
    app = graph.compile()

    result = await app.ainvoke({"messages": [
        SystemMessage(content="You are a Reuters news assistant. Use the tools."),
        HumanMessage(content=query),
    ]})

    for msg in result["messages"]:
        if getattr(msg, "tool_calls", None):
            for tc in msg.tool_calls:
                print(f"  [call] {tc['name']}({tc['args']})")
        elif isinstance(msg, ToolMessage):
            print(f"  [back] {msg.content[:90]}")
        elif isinstance(msg, AIMessage) and msg.content:
            print(f"\n  {msg.content[:220]}")


QUERY = "Generate a news buzz for Apple (AAPL.O). Validate the RIC first, then fetch headlines."


async def run_local():
    """Server in this process -- no ports, same MCP calls."""
    async with Client(create_skill_server()) as client:
        await run_agent(client, QUERY)


async def run_over_http():
    """Server in another terminal, reached by URL."""
    transport = StreamableHttpTransport(url="http://localhost:8011/mcp",
                                        headers={"Authorization": "Bearer demo"})
    async with Client(transport=transport, timeout=60) as client:
        await run_agent(client, QUERY)


if __name__ == "__main__":
    if "--server" in sys.argv:
        print("serving http://localhost:8011/mcp  (Ctrl+C to stop)")
        create_skill_server().run(transport="http", host="127.0.0.1", port=8011,
                                  show_banner=False, log_level="warning")
    elif "--agent" in sys.argv:
        asyncio.run(run_over_http())
    elif "--local" in sys.argv:
        asyncio.run(run_local())
    else:
        print(__doc__.split("Run:")[1].split("Maps to:")[0].strip())

# Exercises:
# 1. Delete args_schema= and rerun. The model calls the tools with no
#    arguments, because you told it they take none (point 3).
# 2. Remove `_tn=tool_name` from the lambda. Every wrapper now calls the last
#    discovered tool -- classic late binding (point 4).
# 3. Add a tool to create_skill_server(). The agent picks it up with no change
#    to the graph: that is what runtime discovery buys you.
# 4. Run --server and --agent in two terminals. Identical output, because the
#    transport is the only difference (learn-mcp lesson 02).
# 5. Add an interrupt() after generate_news_buzz so a human approves the draft
#    before it is returned (lesson 09 + this one).
