"""Lesson 13 — What Is an Orchestrator?
=======================================
Concepts:
  - An orchestrator is a graph that coordinates multiple steps:
    analyze what the user wants → pick the right tool → execute → synthesize
  - This is exactly what your backend's langgraph_mcp_orchestrator.py does
  - We build a simplified version here: query analysis → tool routing →
    tool execution → response synthesis
  - Combines patterns from earlier lessons: conditional edges (03),
    tool calling (06), agent loop (07), interrupts (09), subgraphs (11)

Graph:
  +-------+     +---------+     +-------------+     +-------+     +------------+     +-----+
  | START | --> | analyze | --> | route_tools | --> | tools | --> | synthesize | --> | END |
  +-------+     +---------+     +-------------+     +-------+     +------------+     +-----+
                                      |                                   ^
                                      |  (no tools needed)                |
                                      +-----------------------------------+

  This mirrors the real orchestrator's flow:
    1. analyze   = query_analysis node    (what does the user want?)
    2. route     = conditional edge       (which tools, if any?)
    3. tools     = tool_execution node    (call MCP tools)
    4. synthesize = llm_synthesis node    (turn raw data into a response)

No LLM needed -- demonstrates the orchestration pattern with pure logic.

Run:  uv run python 13_orchestrator.py

Expected output:
  Test 1: Plan has greet + farewell tools → "Hello, Alice!" and "Goodbye, Alice!"
  Test 2: Plan has greet + translate tools → "Hello, Bob!" and "[French] Hello, Bob!"
  Test 3: No tools needed → general response
  Test 4: Plan has farewell tool → "Goodbye, Charlie!"
"""

import operator
from typing import TypedDict, Annotated, Literal


from langgraph.graph import StateGraph, START, END


# ── State ────────────────────────────────────────────────────────────
# Mirrors the real ExecutionState in langgraph_mcp_orchestrator.py,
# stripped down to the essentials.

class OrchestratorState(TypedDict):
    user_message: str
    execution_plan: dict          # which tools to call and why
    tool_results: dict            # tool_name -> result
    errors: Annotated[list[str], operator.add]
    response: str                 # final synthesized answer
    current_step: str             # tracks where we are


# ── Simulated tools (stand-ins for MCP tools) ───────────────────────
# In production these are MCP servers (story-drafting, text-archive, etc.)
# discovered at runtime via the skill registry.

TOOL_REGISTRY = {
    "greet": lambda name: {"greeting": f"Hello, {name}!", "name": name},
    "farewell": lambda name: {"farewell": f"Goodbye, {name}!", "name": name},
    "translate": lambda text: {"original": text, "translated": f"[French] {text}"},
}


# ── Node 1: Query Analysis ──────────────────────────────────────────
# The real orchestrator sends the user message to an LLM that decides
# which tools to call and in what order.  Here we use keyword matching
# as a stand-in.

def analyze(state: OrchestratorState) -> dict:
    """Analyze the user's message and build an execution plan."""
    msg = state["user_message"].lower()

    # Extract a name from the message (take last capitalized word from original)
    words = state["user_message"].split()
    name = next((w for w in reversed(words) if w[0].isupper() and w.isalpha()), "Friend")

    tools_needed = []
    if any(w in msg for w in ["greet", "hello", "welcome"]):
        tools_needed.append({"tool": "greet", "params": {"name": name}})
    if any(w in msg for w in ["goodbye", "farewell", "bye"]):
        tools_needed.append({"tool": "farewell", "params": {"name": name}})
    if "translate" in msg:
        tools_needed.append({"tool": "translate", "params": {"text": "placeholder"}})

    strategy = "sequential" if tools_needed else "none"

    return {
        "execution_plan": {
            "strategy": strategy,       # none | single | sequential | parallel
            "tools": tools_needed,
        },
        "current_step": "analyzed",
    }


# ── Routing: conditional edge ────────────────────────────────────────
# Decides whether to go to tool execution or skip straight to synthesis.
# The real orchestrator has four strategies: none, single, sequential,
# parallel.

def route_after_analysis(state: OrchestratorState) -> Literal["execute_tools", "synthesize"]:
    strategy = state["execution_plan"].get("strategy", "none")
    if strategy == "none":
        return "synthesize"
    return "execute_tools"


# ── Node 2: Tool Execution ──────────────────────────────────────────
# Runs each tool in the plan and collects results.
# The real orchestrator calls MCP servers over HTTP here.

def execute_tools(state: OrchestratorState) -> dict:
    """Execute all tools in the plan and collect results."""
    plan = state["execution_plan"]
    results = {}
    errors = []

    for step in plan.get("tools", []):
        tool_name = step["tool"]
        params = step.get("params", {})

        tool_fn = TOOL_REGISTRY.get(tool_name)
        if not tool_fn:
            errors.append(f"Unknown tool: {tool_name}")
            continue

        try:
            # For translate, chain with greet result if available
            if tool_name == "translate" and "greet" in results:
                results[tool_name] = tool_fn(results["greet"]["greeting"])
            else:
                first_param = next(iter(params.values()), "")
                results[tool_name] = tool_fn(first_param)
        except Exception as e:
            errors.append(f"{tool_name} failed: {e}")

    return {
        "tool_results": results,
        "errors": errors,
        "current_step": "tools_executed",
    }


# ── Node 3: Synthesis ───────────────────────────────────────────────
# Combines tool results into a coherent response.
# The real orchestrator sends tool results + the original query to an
# LLM for natural-language synthesis.

def synthesize(state: OrchestratorState) -> dict:
    """Synthesize tool results into a final response."""
    results = state.get("tool_results", {})

    if not results:
        return {
            "response": f"I can help with greetings, farewells, and translations! "
                        f"You asked: '{state['user_message']}'.",
            "current_step": "complete",
        }

    parts = []
    for tool_name, result in results.items():
        if tool_name == "greet":
            parts.append(result["greeting"])
        if tool_name == "farewell":
            parts.append(result["farewell"])
        if tool_name == "translate":
            parts.append(f"Translation: {result['translated']}")

    errors = state.get("errors", [])
    if errors:
        parts.append(f"(Warnings: {'; '.join(errors)})")

    return {
        "response": " | ".join(parts),
        "current_step": "complete",
    }


# ── Build the orchestrator graph ────────────────────────────────────

graph = StateGraph(OrchestratorState)

graph.add_node("analyze", analyze)
graph.add_node("execute_tools", execute_tools)
graph.add_node("synthesize", synthesize)

graph.add_edge(START, "analyze")
graph.add_conditional_edges("analyze", route_after_analysis)
graph.add_edge("execute_tools", "synthesize")
graph.add_edge("synthesize", END)

orchestrator = graph.compile()


# ── Run it ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Orchestrator Graph (Mermaid) ===")
    print(orchestrator.get_graph().draw_mermaid())
    print()

    # Test 1: Greet + farewell (two tools)
    print("=== Test 1: Greet and farewell ===\n")
    r1 = orchestrator.invoke({
        "user_message": "Greet Alice and say goodbye",
    })
    print(f"Plan:     {r1['execution_plan']}")
    print(f"Results:  {r1['tool_results']}")
    print(f"Response: {r1['response']}")
    print()

    # Test 2: Greet + translate (chained tools)
    print("=== Test 2: Translate a greeting ===\n")
    r2 = orchestrator.invoke({
        "user_message": "Translate a greeting for Bob",
    })
    print(f"Plan:     {r2['execution_plan']}")
    print(f"Results:  {r2['tool_results']}")
    print(f"Response: {r2['response']}")
    print()

    # Test 3: No tools needed
    print("=== Test 3: General query (no tools) ===\n")
    r3 = orchestrator.invoke({
        "user_message": "Hello, what can you help with?",
    })
    print(f"Plan:     {r3['execution_plan']}")
    print(f"Response: {r3['response']}")
    print()

    # Test 4: Farewell only
    print("=== Test 4: Farewell only ===\n")
    r4 = orchestrator.invoke({
        "user_message": "Say farewell to Charlie",
    })
    print(f"Plan:     {r4['execution_plan']}")
    print(f"Response: {r4['response']}")

    # ── Key takeaway ─────────────────────────────────────────────────
    # An orchestrator is a StateGraph that coordinates a multi-step
    # workflow:
    #
    #   1. ANALYZE  — understand what the user wants (query analysis)
    #   2. ROUTE    — decide which tools to call, if any (conditional edge)
    #   3. EXECUTE  — call the tools and collect results (tool execution)
    #   4. SYNTHESIZE — turn raw results into a coherent answer
    #
    # Your backend's langgraph_mcp_orchestrator.py does exactly this
    # but with real LLMs for analysis/synthesis, MCP servers as tools,
    # DynamoDB checkpointing for interrupts, and SSE streaming.
    #
    # The key insight: an orchestrator is NOT a single LLM call.
    # It's a graph that manages the lifecycle of a user request
    # across multiple steps, each of which may fail, retry, or
    # need human input.
    #
    # How it maps to your codebase:
    #   analyze        → chat.py:analyze_query_for_mcp_tools()
    #   route          → ExecutionStrategy enum (none/single/sequential/parallel)
    #   execute_tools  → mcp_protocol.py:call_tool()
    #   synthesize     → TR LLM Orchestrator call with tool results as context
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a "validate_params" node between analyze and execute_tools
    #    that checks if all required tool params are present
    # 2. If params are missing, route to a "request_params" node that
    #    returns what's needed (this is the parameter prompting pattern)
    # 3. Add a MemorySaver checkpointer so you can resume after the
    #    param request (combines this lesson with lesson 08 + 09)
