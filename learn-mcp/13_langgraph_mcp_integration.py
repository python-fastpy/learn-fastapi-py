"""Lesson 13 -- LangGraph + MCP: the orchestrator as a graph
===========================================================

Lesson 12's loop was a while-loop with if-statements. LangGraph turns that
same loop into a GRAPH: each step is a node, each decision is an edge, and
the state travels between them. What you get for that is the ability to STOP
mid-run, save everything, and resume later -- which is how a human review
step works (lesson 06) without a process sitting there waiting.

  ┌──────────────────── the graph ────────────────────┐
  │                                                   │
  │  START                                            │      ┌ greeting-server ┐
  │    │                                              │ ───► │ greet, farewell │
  │    ▼                                              │      └─────────────────┘
  │  analyze        message -> a plan of tool calls   │      ┌ translate-server┐
  │    │                                              │ ───► │ translate       │
  │    ├── no tools needed ──────────────┐            │      └─────────────────┘
  │    ▼                                 │            │
  │  call_tools     run the plan over MCP│            │
  │    │                                 │            │
  │    ├── needs_approval? no ───────────┤            │
  │    ▼                                 │            │
  │  human_review   interrupt() -- the graph STOPS    │
  │    │            here; state is checkpointed and   │
  │    │            ainvoke() returns to you          │
  │    │                                 │            │
  │    ▼                                 ▼            │
  │  synthesize  ◄────────────────────────            │
  │    │            results -> one answer             │
  │    ▼                                              │
  │   END                                             │
  └───────────────────────────────────────────────────┘

  1. STATE      one TypedDict flows through every node. A node returns only
                the keys it changes. tool_results is Annotated with
                operator.add, so results accumulate instead of overwriting.
  2. NODES      plain functions. call_tools is where MCP lives -- the graph
                has no idea the tools are remote (lessons 11, 12).
  3. EDGES      add_edge is unconditional; add_conditional_edges calls your
                function and jumps to the node whose name it returns.
  4. INTERRUPT  interrupt(payload) stops the run. ainvoke returns with
                "__interrupt__" in the result, holding your payload for the
                UI. Nothing is blocked or held open.
  5. RESUME     ainvoke(Command(resume="approved"), same thread_id) picks up
                inside human_review -- interrupt() returns "approved" as its
                value and the run continues to synthesize.
  6. CHECKPOINT MemorySaver stores state per thread_id, which is what makes
                5 possible. Production swaps it for DynamoDB; the graph code
                does not change.

  The analysis here is keyword matching so the lesson runs with no .env.
  Replace analyze() with an LLM call (lesson 08) and the graph is unchanged.

Run:  uv run python 13_langgraph_mcp_integration.py

Maps to: langgraph_mcp_orchestrator.py (_build_graph, ExecutionState, the
interrupt block), mcp_protocol.py (tool calls inside a node)
"""

import asyncio
import operator
import re
from typing import Annotated, Literal, TypedDict

from fastmcp import Client, FastMCP
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

# -- The MCP side: two servers, discovered once at startup -------------------

greeting_server = FastMCP(name="greeting-server")
translate_server = FastMCP(name="translate-server")


@greeting_server.tool
def greet(name: str) -> dict:
    """Say hello to someone."""
    return {"message": f"Hello, {name}!"}


@greeting_server.tool
def farewell(name: str) -> dict:
    """Say goodbye to someone."""
    return {"message": f"Goodbye, {name}!"}


@translate_server.tool
def translate(text: str, language: str = "French") -> dict:
    """Translate text into another language (simulated)."""
    return {"message": f"[{language}] {text}"}


SERVERS = {s.name: s for s in (greeting_server, translate_server)}
ROUTES: dict[str, str] = {}                     # tool -> server, filled at startup


async def discover() -> None:
    for name, server in SERVERS.items():
        async with Client(server) as client:
            for tool in await client.list_tools():
                ROUTES[tool.name] = name


async def call_mcp(tool: str, args: dict) -> dict:
    async with Client(SERVERS[ROUTES[tool]]) as client:
        data = (await client.call_tool(tool, args)).data
        return {"tool": tool, "server": ROUTES[tool], "message": data["message"]}


# -- 1. STATE ----------------------------------------------------------------

class State(TypedDict):
    user_message: str
    plan: list[dict]
    needs_approval: bool
    tool_results: Annotated[list[dict], operator.add]     # accumulates
    approval: str
    response: str


# -- 2. NODES ----------------------------------------------------------------

def analyze(state: State) -> dict:
    """Message -> plan. Production asks the LLM; this matches keywords."""
    msg = state["user_message"].lower()
    # (?i: ...) makes only the keyword case-insensitive -- the name must stay
    # capitalised, or "Greet and" would hand us the name "and".
    name = re.search(r"\b(?i:greet|to|for)\s+([A-Z][a-z]+)", state["user_message"])
    name = name.group(1) if name else "World"

    plan = []
    if any(w in msg for w in ("greet", "hello")):
        plan.append({"tool": "greet", "args": {"name": name}})
    if any(w in msg for w in ("goodbye", "farewell", "bye")):
        plan.append({"tool": "farewell", "args": {"name": name}})
    if "translate" in msg:
        plan.append({"tool": "translate", "args": {"text": f"Hello, {name}!"}})

    # Two or more messages going out under our name? Have a human look first.
    return {"plan": plan, "needs_approval": len(plan) > 1}


async def call_tools(state: State) -> dict:
    """The only node that touches MCP."""
    results = []
    for step in state["plan"]:
        results.append(await call_mcp(step["tool"], step["args"]))
        print(f"      [mcp] {results[-1]['server']}/{results[-1]['tool']} ok")
    return {"tool_results": results}


def human_review(state: State) -> dict:
    """Stop the graph and ask. Resumes here with the caller's answer."""
    answer = interrupt({                                   # 4. INTERRUPT
        "type": "GREETING_REVIEW",
        "message": "Approve these before they go out?",
        "preview": [r["message"] for r in state["tool_results"]],
        "actions": ["approve", "reject"],
    })
    return {"approval": answer}                            # 5. value from Command(resume=...)


def synthesize(state: State) -> dict:
    """Results -> one answer."""
    if not state["tool_results"]:
        return {"response": f"No tool needed for {state['user_message']!r}."}
    lines = " / ".join(r["message"] for r in state["tool_results"])
    if state.get("approval") == "reject":
        return {"response": f"Discarded on review: {lines}"}
    return {"response": lines}


# -- 3. EDGES ----------------------------------------------------------------

def after_analyze(state: State) -> Literal["call_tools", "synthesize"]:
    return "call_tools" if state["plan"] else "synthesize"


def after_tools(state: State) -> Literal["human_review", "synthesize"]:
    return "human_review" if state["needs_approval"] else "synthesize"


def build():
    graph = StateGraph(State)
    graph.add_node("analyze", analyze)
    graph.add_node("call_tools", call_tools)
    graph.add_node("human_review", human_review)
    graph.add_node("synthesize", synthesize)

    graph.add_edge(START, "analyze")
    graph.add_conditional_edges("analyze", after_analyze)
    graph.add_conditional_edges("call_tools", after_tools)
    graph.add_edge("human_review", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile(checkpointer=MemorySaver())       # 6. CHECKPOINT


async def main():
    await discover()
    print("tool -> server:", ROUTES, "\n")
    app = build()

    # 1. No tool needed: analyze routes straight past call_tools.
    print("1. 'How are you?'")
    r = await app.ainvoke({"user_message": "How are you?"},
                          config={"configurable": {"thread_id": "t1"}})
    print(f"   path    : analyze -> synthesize")
    print(f"   response: {r['response']}\n")

    # 2. One tool, no approval needed.
    print("2. 'Greet Shubham'")
    r = await app.ainvoke({"user_message": "Greet Shubham"},
                          config={"configurable": {"thread_id": "t2"}})
    print(f"   path    : analyze -> call_tools -> synthesize")
    print(f"   response: {r['response']}\n")

    # 3. Two tools -> needs_approval -> the graph stops inside human_review.
    print("3. 'Greet Shubham and say goodbye'")
    config = {"configurable": {"thread_id": "t3"}}         # the resume handle
    r = await app.ainvoke({"user_message": "Greet Shubham and say goodbye"}, config=config)

    payload = r["__interrupt__"][0].value
    print(f"   PAUSED, nothing is blocked. The UI gets:")
    print(f"     type    : {payload['type']}")
    print(f"     preview : {payload['preview']}")
    print(f"     actions : {payload['actions']}")

    # Same thread_id -> resumes inside human_review, interrupt() returns this.
    r = await app.ainvoke(Command(resume="approve"), config=config)
    print(f"   resumed with 'approve' -> {r['approval']}")
    print(f"   response: {r['response']}")

    # The checkpoint kept every earlier step: results survived the pause.
    print(f"   tool_results still in state: {[x['tool'] for x in r['tool_results']]}")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Resume with "reject" instead and watch synthesize take the other path.
# 2. Print app.get_graph().draw_mermaid() and paste it into mermaid.live.
# 3. Add an "edit:<text>" answer that routes human_review BACK to call_tools
#    (add_conditional_edges) -- needs_approval is already False, so the
#    second pass falls through to synthesize instead of looping forever.
# 4. Run the plan with asyncio.gather in call_tools -- the graph does not
#    change, only the node.
# 5. Swap MemorySaver for SqliteSaver: test 3 can then resume after the
#    process restarts, which is what DynamoDB does in production.
