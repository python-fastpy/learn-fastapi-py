"""Lesson 13 — What Is an Orchestrator?
=======================================

WHY THIS MATTERS:
  This is the capstone lesson — everything comes together. An orchestrator is a
  graph that coordinates a multi-step workflow: understand the user's request,
  decide which tools to call, execute them, and synthesize the results into a
  response. This is EXACTLY what the production backend does for every user
  message.

  The production langgraph_mcp_orchestrator.py follows this same 4-step pattern,
  but with real LLMs for analysis/synthesis, MCP servers as tools, DynamoDB
  checkpointing, and SSE streaming.

WHAT YOU'LL LEARN:
  1. The orchestrator pattern: analyze -> route -> execute -> synthesize
  2. Query analysis: understanding what the user wants (tool selection)
  3. Execution strategies: none (no tools), single, sequential, parallel
  4. Tool execution: calling multiple tools and collecting results
  5. Response synthesis: combining tool results into a coherent answer

Concepts:
  - Orchestrator = StateGraph that coordinates a multi-step workflow.
        Not a single LLM call — it's a graph with distinct phases.
  - Query analysis: inspect the user's message and build an execution plan
        (which tools to call, in what order, with what parameters).
  - Execution strategy: none | single | sequential | parallel
        Determines how (or whether) tools are invoked.
  - Tool registry: a map of available tools (MCP servers in production).
        Discovered at runtime via mcp_server_registry.py in production.
  - Synthesis: combine raw tool outputs into a natural-language response.
        In production, an LLM does this; here we use string concatenation.
  - This combines patterns from: conditional edges (03), state reducers (04),
        tool calling (06).

Graph:
  +-------+     +---------+     +-------------+     +-------+     +------------+     +-----+
  | START | --> | analyze | --> | route_tools | --> | tools | --> | synthesize | --> | END |
  +-------+     +---------+     +-------------+     +-------+     +------------+     +-----+
                                      |                                   ^
                                      |  (no tools needed)                |
                                      +-----------------------------------+

  This mirrors the real orchestrator's flow:
    1. analyze    = query_analysis node    (what does the user want?)
    2. route      = conditional edge       (which tools, if any?)
    3. tools      = tool_execution node    (call MCP tools)
    4. synthesize = llm_synthesis node     (turn raw data into a response)

Graph trace:
  Test 1: "Greet Alice and say goodbye"
    analyze -> plan: {strategy: "sequential", tools: [greet, farewell]}
    route_after_analysis -> "execute_tools" (strategy != "none")
    execute_tools -> results: {greet: "Hello, Alice!", farewell: "Goodbye, Alice!"}
    synthesize -> "Hello, Alice! | Goodbye, Alice!"

  Test 3: "Hello, what can you help with?"
    analyze -> plan: {strategy: "none", tools: []}
    route_after_analysis -> "synthesize" (strategy == "none", skip tools)
    synthesize -> "I can help with greetings, farewells, and translations!..."

Maps to production:
  langgraph_mcp_orchestrator.py -> the production orchestrator (same 4 steps)
  chat.py                      -> analyze_query_for_mcp_tools()
  ExecutionStrategy enum       -> none | single | sequential | parallel
  mcp_protocol.py              -> call_tool() (tool execution)
  mcp_server_registry.py       -> TOOL_REGISTRY equivalent (discovers available tools)

PREREQUISITES: Lessons 03 (conditional edges), 04 (state reducers), 06 (tool calling)

EXPECTED OUTPUT:
  === Orchestrator Graph (Mermaid) ===
  (mermaid graph text)

  === Test 1: Greet and farewell ===
  Plan:     {'strategy': 'sequential', 'tools': [...]}
  Results:  {'greet': {'greeting': 'Hello, Alice!', ...}, 'farewell': {...}}
  Response: Hello, Alice! | Goodbye, Alice!

  === Test 2: Translate a greeting ===
  Plan:     {'strategy': 'sequential', 'tools': [...]}
  Results:  {'greet': {...}, 'translate': {...}}
  Response: Hello, Bob! | Translation: [French] Hello, Bob!

  === Test 3: General query (no tools) ===
  Plan:     {'strategy': 'none', 'tools': []}
  Response: I can help with greetings, farewells, and translations! ...

  === Test 4: Farewell only ===
  Plan:     {'strategy': 'sequential', 'tools': [...]}
  Response: Goodbye, Charlie!

No LLM needed -- demonstrates the orchestration pattern with pure logic.

Run:  uv run python 13_orchestrator.py
"""

import operator
from typing import TypedDict, Annotated, Literal


from langgraph.graph import StateGraph, START, END


# ── Step 1: State ────────────────────────────────────────────────────
# Mirrors the real ExecutionState in langgraph_mcp_orchestrator.py,
# stripped down to the essentials.  In production, this state also includes
# session_id, tenant_id, checkpoint data, and SSE streaming state.

class OrchestratorState(TypedDict):
    user_message: str                              # what the user typed
    execution_plan: dict                           # which tools to call and why
    tool_results: dict                             # tool_name -> result dict
    errors: Annotated[list[str], operator.add]     # accumulates errors across nodes
    response: str                                  # final synthesized answer
    current_step: str                              # tracks where we are in the flow


# ── Step 2: Simulated tools (stand-ins for MCP servers) ─────────────
# In production, these are MCP servers (story-drafting, text-archive, etc.)
# discovered at runtime via mcp_server_registry.py.  The registry maps tool
# names to callable endpoints.  Here we use simple lambdas as stand-ins.

TOOL_REGISTRY = {
    "greet": lambda name: {"greeting": f"Hello, {name}!", "name": name},
    "farewell": lambda name: {"farewell": f"Goodbye, {name}!", "name": name},
    "translate": lambda text: {"original": text, "translated": f"[French] {text}"},
}


# ── Step 3: Node 1 — Query Analysis ─────────────────────────────────
# The real orchestrator sends the user message to an LLM (via
# chat.py:analyze_query_for_mcp_tools()) that decides which tools to call
# and in what order.  Here we use keyword matching as a simple stand-in
# for the LLM.  The output is an execution plan: a strategy + list of tools.

def analyze(state: OrchestratorState) -> dict:
    """Analyze the user's message and build an execution plan.

    In production, this is an LLM call that inspects the user message,
    considers available MCP tools, and returns a structured plan.
    Here we simulate it with keyword matching.
    """
    msg = state["user_message"].lower()

    # Extract a name from the message (take last capitalized word from original)
    words = state["user_message"].split()
    name = next((w for w in reversed(words) if w[0].isupper() and w.isalpha()), "Friend")

    # Keyword matching as a stand-in for LLM tool selection
    tools_needed = []
    if any(w in msg for w in ["greet", "hello", "welcome"]):
        tools_needed.append({"tool": "greet", "params": {"name": name}})
    if any(w in msg for w in ["goodbye", "farewell", "bye"]):
        tools_needed.append({"tool": "farewell", "params": {"name": name}})
    if "translate" in msg:
        tools_needed.append({"tool": "translate", "params": {"text": "placeholder"}})

    # Determine execution strategy based on how many tools are needed
    # Production supports: none | single | sequential | parallel
    strategy = "sequential" if tools_needed else "none"

    return {
        "execution_plan": {
            "strategy": strategy,       # none | single | sequential | parallel
            "tools": tools_needed,
        },
        "current_step": "analyzed",
    }


# ── Step 4: Routing — conditional edge ──────────────────────────────
# Decides whether to go to tool execution or skip straight to synthesis.
# This is the same conditional edge pattern from Lesson 03, but now it
# inspects the execution plan from the analysis step.  The real
# orchestrator has four strategies: none, single, sequential, parallel.
# Strategy "none" means the user asked a general question — no tools needed.

def route_after_analysis(state: OrchestratorState) -> Literal["execute_tools", "synthesize"]:
    """Route based on execution strategy: tools needed vs. no tools."""
    strategy = state["execution_plan"].get("strategy", "none")
    if strategy == "none":
        return "synthesize"      # skip tools, go straight to response
    return "execute_tools"       # at least one tool to call


# ── Step 5: Node 2 — Tool Execution ─────────────────────────────────
# Runs each tool in the execution plan and collects results.
# The real orchestrator calls MCP servers over HTTP via mcp_protocol.py.
# Sequential strategy runs tools one after another (so later tools can
# use earlier results, like translate using the greet output).

def execute_tools(state: OrchestratorState) -> dict:
    """Execute all tools in the plan and collect results.

    In production, this iterates over the execution plan and calls each
    MCP tool via mcp_protocol.py:call_tool().  Results are collected into
    a dict keyed by tool name.  Errors are accumulated (not raised) so
    partial results can still be synthesized.
    """
    plan = state["execution_plan"]
    results = {}
    errors = []

    for step in plan.get("tools", []):
        tool_name = step["tool"]
        params = step.get("params", {})

        # Look up the tool in the registry (like mcp_server_registry.py)
        tool_fn = TOOL_REGISTRY.get(tool_name)
        if not tool_fn:
            errors.append(f"Unknown tool: {tool_name}")
            continue

        try:
            # For translate, chain with greet result if available —
            # this demonstrates sequential tool dependencies where one
            # tool's output feeds into the next tool's input
            if tool_name == "translate" and "greet" in results:
                results[tool_name] = tool_fn(results["greet"]["greeting"])
            else:
                first_param = next(iter(params.values()), "")
                results[tool_name] = tool_fn(first_param)
        except Exception as e:
            # Accumulate errors instead of crashing — partial results
            # are still useful for synthesis
            errors.append(f"{tool_name} failed: {e}")

    return {
        "tool_results": results,
        "errors": errors,
        "current_step": "tools_executed",
    }


# ── Step 6: Node 3 — Synthesis ──────────────────────────────────────
# Combines raw tool results into a coherent response for the user.
# The real orchestrator sends tool results + the original query to an
# LLM for natural-language synthesis.  Here we use string concatenation
# as a stand-in.  This is the final step before the response is streamed
# back to the frontend via SSE.

def synthesize(state: OrchestratorState) -> dict:
    """Synthesize tool results into a final response.

    In production, an LLM takes the raw tool outputs and the original
    user message, then generates a natural-language response.  Here we
    simply concatenate the relevant fields from each tool's output.
    """
    results = state.get("tool_results", {})

    # No tools were called — provide a general "what I can do" response
    if not results:
        return {
            "response": f"I can help with greetings, farewells, and translations! "
                        f"You asked: '{state['user_message']}'.",
            "current_step": "complete",
        }

    # Extract the user-facing text from each tool's result
    parts = []
    for tool_name, result in results.items():
        if tool_name == "greet":
            parts.append(result["greeting"])
        if tool_name == "farewell":
            parts.append(result["farewell"])
        if tool_name == "translate":
            parts.append(f"Translation: {result['translated']}")

    # Append any errors as warnings (partial results are still useful)
    errors = state.get("errors", [])
    if errors:
        parts.append(f"(Warnings: {'; '.join(errors)})")

    return {
        "response": " | ".join(parts),
        "current_step": "complete",
    }


# ── Step 7: Build the orchestrator graph ────────────────────────────
# Wire the four steps together: analyze -> route -> execute -> synthesize.
# The conditional edge after analyze decides whether tools are needed.

graph = StateGraph(OrchestratorState)

graph.add_node("analyze", analyze)
graph.add_node("execute_tools", execute_tools)
graph.add_node("synthesize", synthesize)

# START -> analyze (always)
graph.add_edge(START, "analyze")
# analyze -> execute_tools OR synthesize (conditional, based on strategy)
graph.add_conditional_edges("analyze", route_after_analysis)
# execute_tools -> synthesize (always, after tools finish)
graph.add_edge("execute_tools", "synthesize")
# synthesize -> END (always)
graph.add_edge("synthesize", END)

orchestrator = graph.compile()


# ── Run it ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Orchestrator Graph (Mermaid) ===")
    print(orchestrator.get_graph().draw_mermaid())
    print()

    # Test 1: Greet + farewell (two tools, sequential execution)
    # Trace: analyze -> route -> execute_tools(greet, farewell) -> synthesize
    print("=== Test 1: Greet and farewell ===\n")
    r1 = orchestrator.invoke({
        "user_message": "Greet Alice and say goodbye",
    })
    print(f"Plan:     {r1['execution_plan']}")
    print(f"Results:  {r1['tool_results']}")
    print(f"Response: {r1['response']}")
    print()

    # Test 2: Greet + translate (chained tools — translate uses greet's output)
    # Trace: analyze -> route -> execute_tools(greet, translate) -> synthesize
    print("=== Test 2: Translate a greeting ===\n")
    r2 = orchestrator.invoke({
        "user_message": "Translate a greeting for Bob",
    })
    print(f"Plan:     {r2['execution_plan']}")
    print(f"Results:  {r2['tool_results']}")
    print(f"Response: {r2['response']}")
    print()

    # Test 3: No tools needed — general question
    # Trace: analyze -> route -> synthesize (skips execute_tools entirely)
    print("=== Test 3: General query (no tools) ===\n")
    r3 = orchestrator.invoke({
        "user_message": "Hello, what can you help with?",
    })
    print(f"Plan:     {r3['execution_plan']}")
    print(f"Response: {r3['response']}")
    print()

    # Test 4: Farewell only (single tool)
    # Trace: analyze -> route -> execute_tools(farewell) -> synthesize
    print("=== Test 4: Farewell only ===\n")
    r4 = orchestrator.invoke({
        "user_message": "Say farewell to Charlie",
    })
    print(f"Plan:     {r4['execution_plan']}")
    print(f"Response: {r4['response']}")

    # ── Key takeaway ─────────────────────────────────────────────────
    # An orchestrator is NOT a single LLM call.  It's a StateGraph that
    # manages the entire lifecycle of a user request across multiple
    # distinct steps, each of which may fail, retry, or need human input.
    #
    # The 4-step pattern handles EVERYTHING — from simple greetings to
    # complex multi-tool workflows:
    #
    #   1. ANALYZE   — understand what the user wants (query analysis)
    #      Production: chat.py:analyze_query_for_mcp_tools()
    #      An LLM inspects the message and picks the right tools.
    #
    #   2. ROUTE     — decide the execution path (conditional edge)
    #      Production: ExecutionStrategy enum (none/single/sequential/parallel)
    #      If no tools needed, skip straight to synthesis.
    #
    #   3. EXECUTE   — call the tools and collect results (tool execution)
    #      Production: mcp_protocol.py:call_tool()
    #      Runs MCP tools over HTTP, with retry logic (Lesson 12).
    #
    #   4. SYNTHESIZE — turn raw results into a coherent answer
    #      Production: LLM call with tool results + original query as context.
    #      Streamed back to the frontend via SSE.
    #
    # The real langgraph_mcp_orchestrator.py adds:
    #   - DynamoDB checkpointing (for interrupt/resume, Lesson 09)
    #   - SSE streaming (partial results sent as they arrive)
    #   - MCP server discovery (mcp_server_registry.py)
    #   - Fast-path matching (bypass LLM for well-known patterns)
    #   - Human-in-the-loop interrupts (Lesson 09 + 10)
    #
    # But the CORE pattern is identical: analyze -> route -> execute -> synthesize.
    #
    # ── Exercise ─────────────────────────────────────────────────────
    # 1. Add a "validate_params" node between analyze and execute_tools
    #    that checks if all required tool params are present
    # 2. If params are missing, route to a "request_params" node that
    #    returns what's needed (this is the parameter prompting pattern)
    # 3. Add a MemorySaver checkpointer so you can resume after the
    #    param request (combines this lesson with lesson 08 + 09)
