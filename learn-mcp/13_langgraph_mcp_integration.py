"""Lesson 13 -- LangGraph + MCP Integration (Capstone)
======================================================

WHY THIS MATTERS:
  This is the capstone lesson. The production backend uses LangGraph
  to orchestrate MCP tool calls -- it's a directed graph where each
  node is a step (analyze, call tools, interrupt for review, synthesize).
  LangGraph gives you checkpointing (save state, resume after interrupt),
  conditional routing (skip tools if not needed), and a clear execution
  flow. This lesson builds the same architecture with mock LLM calls
  so you can run it without credentials.

WHAT YOU'LL LEARN:
  1. Build a LangGraph StateGraph with nodes and conditional edges
  2. Call MCP tools from inside LangGraph nodes
  3. Use interrupt() to pause for human review + Command(resume=...) to continue
  4. Use MemorySaver to checkpoint state (production uses DynamoDB)
  5. See how all MCP lessons (01-12) combine into the final architecture

Concepts:
  - LangGraph StateGraph as the orchestrator
  - MCP servers (FastMCP) as the tool providers
  - Full loop: user message -> analyze -> call MCP tools -> synthesize
  - Human-in-the-loop interrupts via LangGraph interrupt() + MCP
  - MemorySaver checkpointer for interrupt/resume
  - Multi-server orchestration (greeting-server + translation-server)

Architecture (mirrors your production backend):
  +--------+     +------------------------+     +------------------+
  | User   | --> | LangGraph Orchestrator | --> | MCP Servers      |
  +--------+     |                        |     |                  |
                 | Nodes:                 |     | greeting-server: |
                 |  1. analyze            |     |   greet          |
                 |  2. route              |     |   farewell       |
                 |  3. call_mcp_tools     |     |                  |
                 |  4. maybe_interrupt    |     | translation:     |
                 |  5. synthesize         |     |   translate      |
                 +------------------------+     +------------------+
                        |        ^
                        v        |
                 +------------------------+
                 | MemorySaver            |
                 | (in-memory checkpoint) |
                 +------------------------+

  Maps to:
    langgraph_mcp_orchestrator.py -> the full StateGraph
    mcp_protocol.py              -> MCP client calls inside nodes
    mcp_server_registry.py       -> multi-server discovery

PREREQUISITES: Lesson 12 (orchestration), Lesson 10 (interrupts), Lesson 11 (multi-server)
  Also helpful: LangGraph basics (StateGraph, nodes, edges)

No real LLM needed -- uses mock analysis to keep it runnable without
credentials.  Swap mock_analyze() for LLM-based analysis to go live.

Run:  uv run python 13_langgraph_mcp_integration.py

EXPECTED OUTPUT:
  === MCP + LangGraph Orchestrator ===

  MCP Servers: ['greeting-server', 'translation-server']
  Discovered tools: ['greet', 'farewell', 'translate']
  Tool -> Server map: {'greet': 'greeting-server', ...}

  === Graph (Mermaid) ===
    %%{init: ...}%%
    graph TD; ...
    analyze --> route --> ...

  === Test 1: "Translate hello into French" ===
    [MCP] translation-server/translate -> OK
    Plan: {'strategy': 'single', 'tools': [...]}
    Response: [translation-server/translate] ...

  === Test 2: "Create a greeting and farewell for Alice" ===
    [MCP] greeting-server/greet -> OK
    [MCP] greeting-server/farewell -> OK
    [Paused] Graph PAUSED -- waiting for human review
    [Interrupt] type=GREETING_REVIEW
    [Interrupt] message=Please review the greeting below:
    [Step 3] User approves...
    Approval: approved
    Response: [greeting-server/greet] ... [greeting-server/farewell] ...

  === Test 3: "How are you?" ===
    Plan: {'strategy': 'none', 'tools': []}
    Response: I can help with that! ...

  === Test 4: "Greet Bob and translate it to Spanish" ===
    [MCP] greeting-server/greet -> OK
    [MCP] translation-server/translate -> OK
    [Paused for review -- auto-approving]
    Tools used: ['greet', 'translate']
    Servers hit: ['greeting-server', 'translation-server']
    Response: [greeting-server/greet] ... [translation-server/translate] ...
"""

import asyncio
import operator
from typing import TypedDict, Annotated, Literal

from pydantic import Field
from fastmcp import FastMCP, Client
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command


# ============================================================================
# PART 1: MCP Servers (same as lesson 12, representing production skills)
# ============================================================================
# In production these run on separate ECS containers behind an ALB.
# Here we use in-process FastMCP for simplicity.

greeting_server = FastMCP(name="greeting-server")
translation_server = FastMCP(name="translation-server")


@greeting_server.tool
async def greet(
    name: Annotated[str, Field(description="Name to greet")],
) -> dict:
    """Greet someone by name."""
    return {"message": f"Hello, {name}!"}


@greeting_server.tool
async def farewell(
    name: Annotated[str, Field(description="Name to say goodbye to")],
) -> dict:
    """Say goodbye to someone by name."""
    return {"message": f"Goodbye, {name}! Take care."}


@translation_server.tool
async def translate(
    text: Annotated[str, Field(description="Text to translate")],
    language: Annotated[str, Field(default="French", description="Target language")] = "French",
) -> dict:
    """Translate text into another language."""
    return {"original": text, "translated": f"[{language}] {text}", "language": language}


# ============================================================================
# PART 2: MCP Tool Registry
# ============================================================================
# Mirrors mcp_server_registry.py: discover tools from all servers,
# know which server owns each tool.

MCP_SERVERS = {
    "greeting-server": greeting_server,
    "translation-server": translation_server,
}

TOOL_OWNERSHIP: dict[str, str] = {}  # tool_name -> server_name (populated at startup)


async def discover_all_tools():
    """Connect to every MCP server, list its tools, build the registry."""
    for server_name, server in MCP_SERVERS.items():
        async with Client(server) as client:
            tools = await client.list_tools()
            for t in tools:
                TOOL_OWNERSHIP[t.name] = server_name


async def call_mcp_tool(tool_name: str, args: dict) -> dict:
    """Call a single MCP tool on the correct server.
    Mirrors mcp_protocol.py's one-shot client pattern."""
    server_name = TOOL_OWNERSHIP.get(tool_name)
    if not server_name:
        return {"error": f"Unknown tool: {tool_name}"}

    server = MCP_SERVERS[server_name]
    async with Client(server) as client:
        result = await client.call_tool(tool_name, args)
        return {"tool": tool_name, "server": server_name, "result": result}


# ============================================================================
# PART 3: LangGraph State
# ============================================================================
# This is the ExecutionState that flows through the graph.
# Production version lives in langgraph_mcp_orchestrator.py.

class OrchestratorState(TypedDict):
    user_message: str
    execution_plan: dict            # strategy + tool list
    tool_results: Annotated[list[dict], operator.add]
    needs_approval: bool            # triggers human-in-the-loop
    user_approval: str              # "approved" | "rejected" | "edit:..."
    response: str                   # final answer
    errors: Annotated[list[str], operator.add]


# ============================================================================
# PART 4: LangGraph Nodes
# ============================================================================
# Each node is an async function that reads/writes OrchestratorState.

# -- Node 1: Analyze --------------------------------------------------------
# In production the LLM decides which tools to call.
# Here we use keyword matching as a stand-in.

def analyze(state: OrchestratorState) -> dict:
    """Analyze user message and build an execution plan.
    Production: LLM call with tool schemas as context.
    Demo: keyword matching (same idea as fast_path_matcher.py)."""
    msg = state["user_message"].lower()

    tools_to_call = []
    needs_approval = False

    # Extract a name from the message (simple heuristic: last word)
    words = state["user_message"].split()
    name = words[-1].strip(".,!?") if words else "World"

    has_greet = any(w in msg for w in ["greet", "hello", "welcome"])
    has_farewell = any(w in msg for w in ["farewell", "goodbye", "bye"])

    if has_greet:
        tools_to_call.append({"tool": "greet", "args": {"name": name}})

    if has_farewell:
        tools_to_call.append({"tool": "farewell", "args": {"name": name}})

    # If both greet AND farewell are planned, require approval
    if has_greet and has_farewell:
        needs_approval = True

    if "translate" in msg:
        # Extract target language if mentioned
        text = state["user_message"]
        language = "French"
        for lang in ["Spanish", "French", "German", "Italian", "Japanese"]:
            if lang.lower() in msg:
                language = lang
                break
        # Extract the text to translate (simple: use the whole message)
        tools_to_call.append({"tool": "translate", "args": {"text": text, "language": language}})
        # Multi-server (greet + translate) also needs approval
        if has_greet or has_farewell:
            needs_approval = True

    strategy = "none"
    if len(tools_to_call) == 1:
        strategy = "single"
    elif len(tools_to_call) > 1:
        strategy = "sequential"

    return {
        "execution_plan": {"strategy": strategy, "tools": tools_to_call},
        "needs_approval": needs_approval,
    }


# -- Routing: should we call tools? -----------------------------------------
# Conditional edge after analyze node.

def route_after_analysis(state: OrchestratorState) -> Literal["call_tools", "synthesize"]:
    """Route to tool execution or skip to synthesis."""
    strategy = state["execution_plan"].get("strategy", "none")
    if strategy == "none":
        return "synthesize"
    return "call_tools"


# -- Node 2: Call MCP Tools -------------------------------------------------
# Executes tools from the plan by calling MCP servers.

async def call_tools(state: OrchestratorState) -> dict:
    """Execute each tool in the plan via MCP.
    Production calls real MCP servers over HTTP."""
    plan = state["execution_plan"]
    results = []
    errors = []

    for step in plan.get("tools", []):
        tool_name = step["tool"]
        args = step.get("args", {})

        try:
            result = await call_mcp_tool(tool_name, args)
            results.append(result)
            print(f"    [MCP] {result['server']}/{tool_name} -> OK")
        except Exception as e:
            errors.append(f"{tool_name}: {e}")
            print(f"    [MCP] {tool_name} -> ERROR: {e}")

    return {"tool_results": results, "errors": errors}


# -- Routing: does this need human approval? --------------------------------

def route_after_tools(state: OrchestratorState) -> Literal["human_review", "synthesize"]:
    """If the plan flagged needs_approval, pause for human review."""
    if state.get("needs_approval", False):
        return "human_review"
    return "synthesize"


# -- Node 3: Human-in-the-Loop ----------------------------------------------
# Uses LangGraph's interrupt() to pause and wait for user input.
# MemorySaver checkpoints state in memory so we can resume later.

def human_review(state: OrchestratorState) -> dict:
    """Pause execution for human review.
    The interrupt() call checkpoints state and returns control
    to the caller. When resumed, the user's response is available."""

    # Build a preview of what was produced
    greetings = [
        r for r in state.get("tool_results", [])
        if r.get("tool") in ("greet", "farewell")
    ]

    greeting_preview = "No greeting found."
    if greetings:
        previews = []
        for g in greetings:
            data = g.get("result", {})
            if isinstance(data, list) and data:
                content = data[0]
                if hasattr(content, "text"):
                    previews.append(content.text)
                else:
                    previews.append(str(content))
            elif isinstance(data, dict):
                previews.append(str(data))
        greeting_preview = " | ".join(previews)

    # interrupt() checkpoints the graph and returns to the caller.
    # When the caller resumes with a Command, the value becomes
    # the return from interrupt().
    user_response = interrupt({
        "type": "GREETING_REVIEW",
        "message": "Please review the greeting below:",
        "preview": greeting_preview,
        "actions": ["approve", "reject", "edit"],
    })

    return {"user_approval": user_response, "needs_approval": False}


# -- Routing: what did the human say? ---------------------------------------

def route_after_review(state: OrchestratorState) -> Literal["synthesize", "call_tools"]:
    """Route based on human review response."""
    approval = state.get("user_approval", "approved")
    if approval.startswith("edit:"):
        return "call_tools"  # re-execute with edits
    return "synthesize"


# -- Node 4: Synthesize -----------------------------------------------------
# Combines tool results into a final response.
# Production sends results to the LLM for natural-language synthesis.

def synthesize(state: OrchestratorState) -> dict:
    """Turn tool results into a user-facing response.
    Production: LLM call with results + original query as context.
    Demo: simple string formatting."""
    results = state.get("tool_results", [])
    approval = state.get("user_approval", "")

    if not results:
        return {"response": f"I can help with that! You asked: '{state['user_message']}'"}

    parts = []
    for r in results:
        tool = r.get("tool", "?")
        data = r.get("result", {})

        # Extract text from MCP TextContent list
        if isinstance(data, list):
            text_parts = []
            for item in data:
                if hasattr(item, "text"):
                    text_parts.append(item.text)
                else:
                    text_parts.append(str(item))
            data_str = " | ".join(text_parts)
        else:
            data_str = str(data)

        parts.append(f"[{r.get('server', '?')}/{tool}] {data_str[:120]}")

    if approval == "rejected":
        parts.append("(User rejected the greeting)")
    elif approval.startswith("edit:"):
        parts.append(f"(User requested edits: {approval[5:]})")

    errors = state.get("errors", [])
    if errors:
        parts.append(f"Warnings: {'; '.join(errors)}")

    return {"response": "\n".join(parts)}


# ============================================================================
# PART 5: Build the LangGraph
# ============================================================================
# Wire up nodes + edges. This is the equivalent of
# langgraph_mcp_orchestrator.py's _build_graph().

def build_orchestrator():
    """Build and compile the orchestrator graph.

    Graph:
      START -> analyze -> [route] -> call_tools -> [route] -> human_review
                 |                                               |
                 +-> synthesize <---------------------------------+
                        |
                       END

    With MemorySaver checkpointer for interrupt/resume.
    """
    graph = StateGraph(OrchestratorState)

    # Add nodes
    graph.add_node("analyze", analyze)
    graph.add_node("call_tools", call_tools)
    graph.add_node("human_review", human_review)
    graph.add_node("synthesize", synthesize)

    # Add edges
    graph.add_edge(START, "analyze")
    graph.add_conditional_edges("analyze", route_after_analysis)
    graph.add_conditional_edges("call_tools", route_after_tools)
    graph.add_conditional_edges("human_review", route_after_review)
    graph.add_edge("synthesize", END)

    # Compile with checkpointer (enables interrupt/resume)
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


# ============================================================================
# PART 6: Run the orchestrator
# ============================================================================

async def main():
    # -- Startup: discover tools from all MCP servers --
    await discover_all_tools()
    print("=== MCP + LangGraph Orchestrator ===\n")
    print(f"  MCP Servers: {list(MCP_SERVERS.keys())}")
    print(f"  Discovered tools: {list(TOOL_OWNERSHIP.keys())}")
    print(f"  Tool -> Server map: {TOOL_OWNERSHIP}")
    print()

    orchestrator = build_orchestrator()

    # Print the graph structure
    print("=== Graph (Mermaid) ===")
    print(orchestrator.get_graph().draw_mermaid())
    print()

    # -- Test 1: Translate (no approval needed) -----------------------------
    print("=" * 60)
    print("Test 1: Translate (no interrupt)")
    print("=" * 60 + "\n")

    config1 = {"configurable": {"thread_id": "session-001"}}
    result1 = await orchestrator.ainvoke(
        {"user_message": "Translate hello into French"},
        config=config1,
    )

    print(f"\n  Plan: {result1['execution_plan']}")
    print(f"  Response:\n    {result1['response']}")
    print()

    # -- Test 2: Greet + farewell (triggers interrupt for review) -----------
    print("=" * 60)
    print("Test 2: Greeting + farewell (with human-in-the-loop interrupt)")
    print("=" * 60 + "\n")

    config2 = {"configurable": {"thread_id": "session-002"}}

    # First invoke: runs until interrupt()
    print("  [Step 1] Sending message...")
    result2 = await orchestrator.ainvoke(
        {"user_message": "Create a greeting and farewell for Alice"},
        config=config2,
    )

    # After interrupt, the graph is paused. Check the state snapshot.
    snapshot = await orchestrator.aget_state(config2)
    is_interrupted = bool(snapshot.tasks and any(
        hasattr(t, "interrupts") and t.interrupts
        for t in snapshot.tasks
    ))

    if is_interrupted:
        print("  [Step 2] Graph PAUSED -- waiting for human review")

        # Extract what the interrupt is showing the user
        for task in snapshot.tasks:
            if hasattr(task, "interrupts") and task.interrupts:
                for intr in task.interrupts:
                    print(f"  [Interrupt] type={intr.value.get('type')}")
                    print(f"  [Interrupt] message={intr.value.get('message')}")
                    print(f"  [Interrupt] actions={intr.value.get('actions')}")
        print()

        # Resume with user's approval
        print("  [Step 3] User approves the greeting...")
        result2 = await orchestrator.ainvoke(
            Command(resume="approved"),
            config=config2,
        )

        print(f"\n  Approval: {result2.get('user_approval')}")
        print(f"  Response:\n    {result2['response']}")
    else:
        print(f"  Response:\n    {result2['response']}")
    print()

    # -- Test 3: Simple query (no tools) ------------------------------------
    print("=" * 60)
    print("Test 3: Simple query (no tools, LLM-only path)")
    print("=" * 60 + "\n")

    config3 = {"configurable": {"thread_id": "session-003"}}
    result3 = await orchestrator.ainvoke(
        {"user_message": "How are you?"},
        config=config3,
    )
    print(f"  Plan: {result3['execution_plan']}")
    print(f"  Response: {result3['response']}")
    print()

    # -- Test 4: Multi-server (greet + translate) ---------------------------
    print("=" * 60)
    print("Test 4: Multi-server (greeting-server + translation-server)")
    print("=" * 60 + "\n")

    config4 = {"configurable": {"thread_id": "session-004"}}
    result4 = await orchestrator.ainvoke(
        {"user_message": "Greet Bob and translate it to Spanish"},
        config=config4,
    )

    # This triggers interrupt because it combines greet + translate
    snapshot4 = await orchestrator.aget_state(config4)
    is_interrupted4 = bool(snapshot4.tasks and any(
        hasattr(t, "interrupts") and t.interrupts
        for t in snapshot4.tasks
    ))

    if is_interrupted4:
        print("  [Paused for review -- auto-approving]")
        result4 = await orchestrator.ainvoke(
            Command(resume="approved"),
            config=config4,
        )

    print(f"  Tools used: {[r['tool'] for r in result4.get('tool_results', [])]}")
    print(f"  Servers hit: {list(set(r['server'] for r in result4.get('tool_results', [])))}")
    print(f"  Response:\n    {result4['response']}")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # This lesson shows how LangGraph and MCP work together:
    #
    # LangGraph provides:
    #   - StateGraph: defines the orchestration flow (analyze -> tools -> synthesize)
    #   - Conditional edges: route based on analysis (which tools? need approval?)
    #   - Checkpointing: save state so interrupted flows can resume
    #   - interrupt(): pause execution for human input
    #   - Command(resume=...): resume from where we left off
    #
    # MCP (FastMCP) provides:
    #   - Tool definitions: @server.tool decorated functions
    #   - Tool discovery: client.list_tools() at startup
    #   - Tool execution: client.call_tool(name, args) during graph execution
    #   - Multi-server: each skill is a separate server with its own tools
    #   - Transport: HTTP in production, in-process here
    #
    # The integration pattern:
    #   1. STARTUP: discover tools from all MCP servers
    #   2. ANALYZE: LLM (or regex) determines which MCP tools to call
    #   3. EXECUTE: LangGraph node calls MCP tools via one-shot clients
    #   4. INTERRUPT: LangGraph pauses, checkpoints, waits for human input
    #   5. RESUME: human response flows back, graph continues
    #   6. SYNTHESIZE: LLM combines MCP tool results into a response
    #
    # How it maps to your production codebase:
    #   build_orchestrator()  -> langgraph_mcp_orchestrator.py:_build_graph()
    #   analyze()             -> chat.py:analyze_query_for_mcp_tools()
    #   call_mcp_tool()       -> mcp_protocol.py:call_tool()
    #   discover_all_tools()  -> mcp_server_registry.py:refresh_capabilities()
    #   human_review()        -> langgraph_mcp_orchestrator.py (interrupt block)
    #   MemorySaver           -> checkpointer (persists state for resume)
    #   MCP_SERVERS dict      -> mcp_server_registry.py:get_servers()
    #   OrchestratorState     -> langgraph_mcp_orchestrator.py:ExecutionState
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add LLM-based analysis: replace mock_analyze keywords with an
    #    LLM call using llm_helper.get_llm() (see lesson 07 for pattern)
    # 2. Add parallel tool execution: use asyncio.gather() in call_tools
    #    when the plan strategy is "parallel"
    # 3. Add workflow support: load workflow definitions from the MCP
    #    server (lesson 09) and use them to gate which tools are visible
    # 4. Add streaming: yield progress updates from call_tools using
    #    LangGraph's astream() instead of ainvoke()
    # 5. Swap MemorySaver for a SQLite or file-based checkpointer to
    #    persist state across process restarts
