"""Lesson 13 -- What an Orchestrator Is
======================================

The capstone. An orchestrator is not one clever LLM call -- it is a graph
with four phases: work out what was asked, decide whether any tool is
needed, run them, then turn the raw results into an answer. Production does
exactly this for every user message.

  START
    │
    ▼
  analyze          the message -> a PLAN {strategy, tools, params}
    │
    │   route_after_analysis   (a conditional edge, lesson 03)
    ├── strategy == "none" ─────────────────────────┐
    ▼                                               │
  execute_tools    look each tool up in the         │
    │              registry, run it, collect        │
    │              results, ACCUMULATE errors       │
    │              instead of raising (lesson 04)   │
    ▼                                               ▼
  synthesize  ◄─────────────────────────────── (arrives directly)
    │              results -> one reply
    ▼
   END

  1. ANALYZE      message -> plan. Keyword matching here; in production an
                  LLM does it, with the tool list as context.
  2. STRATEGY     none | single | sequential | parallel. "none" is the one
                  people forget to build: most messages need no tool at all,
                  and routing past the tools is the cheapest thing you do.
  3. ROUTE        one conditional edge reading the plan. Lesson 03, unchanged.
  4. EXECUTE      a registry lookup per step. An unknown tool appends to
                  `errors` rather than raising, so a partly-failed run still
                  produces an answer.
  5. CHAIN        "sequential" means a later tool can consume an earlier
                  result -- translate reads what greet produced.
  6. SYNTHESIZE   raw tool output -> prose. An LLM in production; string
                  joining here, because the PHASE is the lesson, not the text.

  Only `analyze` decides anything. Every other node obeys the plan. That
  separation is what lets you swap keyword matching for an LLM, or local
  functions for MCP servers (lesson 14), without touching the graph.

Run:  uv run python 13_orchestrator.py      (no LLM needed)

Maps to: langgraph_mcp_orchestrator.py -> the same four phases;
chat.py -> analyze_query_for_mcp_tools(); mcp_protocol.py -> call_tool();
mcp_server_registry.py -> the registry below
"""

import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import END, START, StateGraph


class OrchestratorState(TypedDict):
    user_message: str
    execution_plan: dict
    tool_results: dict
    errors: Annotated[list[str], operator.add]     # accumulates (lesson 04)
    response: str


# In production these are MCP servers, discovered at runtime (lesson 14).
TOOL_REGISTRY = {
    "greet": lambda name: {"text": f"Hello, {name}!"},
    "farewell": lambda name: {"text": f"Goodbye, {name}!"},
    "translate": lambda text: {"text": f"[French] {text}"},
}


def analyze(state: OrchestratorState) -> dict:
    """1 + 2. Build the plan. An LLM's job in production."""
    msg = state["user_message"].lower()
    words = state["user_message"].split()
    name = next((w.strip(".,!?") for w in reversed(words)
                 if w[0].isupper() and w.strip(".,!?").isalpha()), "friend")

    tools = []
    if any(w in msg for w in ("greet", "hello", "welcome")):
        tools.append({"tool": "greet", "params": {"name": name}})
    if any(w in msg for w in ("goodbye", "farewell", "bye")):
        tools.append({"tool": "farewell", "params": {"name": name}})
    if "translate" in msg:
        tools.append({"tool": "translate", "params": {}})       # filled in by the chain
    if "everything" in msg:
        tools.append({"tool": "nonexistent", "params": {}})     # to show the error path

    strategy = "none" if not tools else ("single" if len(tools) == 1 else "sequential")
    return {"execution_plan": {"strategy": strategy, "tools": tools}}


def route_after_analysis(state: OrchestratorState) -> Literal["execute_tools", "synthesize"]:
    """3. The only branch in the graph."""
    return "synthesize" if state["execution_plan"]["strategy"] == "none" else "execute_tools"


def execute_tools(state: OrchestratorState) -> dict:
    """4 + 5. Run the plan. Collect, never raise."""
    results, errors = {}, []

    for step in state["execution_plan"]["tools"]:
        name, params = step["tool"], dict(step["params"])
        fn = TOOL_REGISTRY.get(name)
        if fn is None:
            errors.append(f"unknown tool: {name}")          # degraded, not dead
            continue
        if name == "translate" and "greet" in results:      # 5. the chain
            params["text"] = results["greet"]["text"]
        results[name] = fn(**params) if params else fn("nothing to translate")

    return {"tool_results": results, "errors": errors}


def synthesize(state: OrchestratorState) -> dict:
    """6. Raw results -> one reply."""
    results = state["tool_results"]
    if not results:
        return {"response": "I can greet people, say goodbye, and translate greetings."}

    reply = " | ".join(r["text"] for r in results.values())
    if state["errors"]:
        reply += f"   (partial: {'; '.join(state['errors'])})"
    return {"response": reply}


graph = StateGraph(OrchestratorState)
graph.add_node("analyze", analyze)
graph.add_node("execute_tools", execute_tools)
graph.add_node("synthesize", synthesize)

graph.add_edge(START, "analyze")
graph.add_conditional_edges("analyze", route_after_analysis)
graph.add_edge("execute_tools", "synthesize")
graph.add_edge("synthesize", END)

app = graph.compile()


if __name__ == "__main__":
    for message in (
        "Greet Shubham and say goodbye",          # two tools, sequential
        "Greet Shubham and translate it",         # the chain: translate reads greet
        "What can you help with?",                # strategy "none" -- skips the tools
        "Greet Shubham and do everything",        # one tool is missing: partial answer
    ):
        r = app.invoke({"user_message": message, "execution_plan": {}, "tool_results": {},
                        "errors": [], "response": ""})
        plan = r["execution_plan"]
        print(f"{message!r}")
        print(f"   plan     : {plan['strategy']} {[t['tool'] for t in plan['tools']]}")
        print(f"   response : {r['response']}\n")

    print("Four very different runs. One graph, and only `analyze` ever decided.")

# Exercises:
# 0. Ask "Hello, what can you help with?" instead. It routes to `greet`,
#    because "hello" is in the keyword list -- a greeting keyword inside a
#    question about capabilities. Keyword matching cannot tell those apart,
#    and that single failure is the whole argument for exercise 2.
# 1. Add a "parallel" strategy that runs independent tools with
#    asyncio.gather. Only execute_tools changes; the graph does not.
# 2. Replace analyze() with an LLM call that returns the plan as JSON
#    (llm_helper.get_llm + a schema). The other three nodes stay as they are.
# 3. Make a tool raise instead of being missing. Catch it, append to errors,
#    and confirm you still get a partial answer.
# 4. Point the registry at the MCP servers from lesson 14 -- that swap is the
#    whole distance between this file and production.
