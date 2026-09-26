"""Lesson 16 -- Agent vs MCP, Agent-Creates-Agent, and Handoff Patterns
========================================================================

WHY THIS MATTERS:
  Lessons 01-15 taught MCP: how tools/resources/prompts are exposed and
  called over a standard protocol. But MCP itself has no brain -- it never
  decides *which* tool to call, *when* to stop, or *who* should handle a
  task. That decision loop is the "agent". Once a system needs more than
  one such loop, it runs into three questions this lesson answers:

    1. Where exactly is the line between "agent" and "MCP"?
    2. What does it mean for an agent to create another agent?
    3. How do you hand a job off to an agent instead of just calling it?

WHAT YOU'LL LEARN:
  1. Agent vs MCP -- which layer does what, and why MCP works with zero
     agents involved (lessons 01-07 never touched an LLM)
  2. Agent-as-tool -- wrapping a whole agent (loop + tools + memory) as one
     callable, the same shape as lesson 15's MCP-to-MCP, one level up
  3. Agent-creates-agent -- a supervisor that *instantiates* the right
     specialist at runtime based on the task, instead of a hardcoded
     pipeline of fixed tools
  4. Two ways to hand off a job:
       - Delegation (synchronous): parent calls child, waits, keeps control
         (nested call stack -- parent is still "on the hook")
       - Control handoff (routing): parent transfers the turn to the child
         and steps aside (flat call stack -- mirrors LangGraph's
         Command(goto=...) primitive from lesson 13)
  5. A map (not a full build) of where this leads: planner/executor,
     hierarchical supervisors, and shared-state ("blackboard") systems

Concepts:
  - MCP = protocol/interface layer: tools, resources, prompts. No memory,
    no judgment, no "next step" -- it just answers calls.
  - Agent = decision loop: an LLM (or deterministic policy, for this
    lesson) that decides which tool to call and when the task is done.
  - Agent-as-tool: an entire agent exposed as a single callable; the caller
    never sees its internal tool calls, only the final answer.
  - Delegation: caller awaits the callee's result before continuing.
  - Handoff: caller stops driving the conversation; the callee becomes the
    active agent going forward.
  - Supervisor: an agent whose only tools are "which specialist should
    handle this," not domain tools itself.

Flow:
  MCP layer (no judgment, just callable functions):
    +----------------+     +----------------+
    | search_web()   |     | draft_summary()|
    +----------------+     +----------------+
            ^                       ^
            | called by             | called by
            |                       |
  Agent layer (judgment: which tool, when to stop):
    +---------------+       +----------------+
    | ResearchAgent |       | WriterAgent    |
    +-------+-------+       +--------+-------+
            ^                        ^
            | agent-as-tool          | agent-as-tool
            | (delegation, waits)    | (delegation, waits)
            +-----------+------------+
                        |
              +---------+----------+
              | SupervisorAgent    |   <- decides which specialist to
              | (creates agents on |      CREATE for this task, then
              |  demand per task)  |      either delegates (waits) or
              +---------+----------+      hands off (steps aside)
                        ^
                        | task
                    +---+---+
                    | User  |
                    +-------+

  Maps to:
    langgraph_mcp_orchestrator.py       -- StateGraph nodes as agents,
                                            conditional edges as handoffs
    sphinx_leon-assistant-skills/*      -- each skill = one agent-as-tool,
                                            reachable via MCP-to-MCP (L15)
    LangGraph `Command(goto=..., update=...)` -- the real control-handoff
                                            primitive this lesson mimics

PREREQUISITES: Lesson 11 (multi-server routing), Lesson 12 (orchestration),
                Lesson 15 (MCP-to-MCP)

Run:  uv run python 16_agent_vs_mcp_and_handoff.py

EXPECTED OUTPUT:
  === Part 1: MCP alone (no agent, no judgment) ===
    search_web('quarterly earnings') -> 2 findings (deterministic, no LLM)

  === Part 2: A single agent driving MCP tools ===
    [research-agent] task: 'quarterly earnings' -> calls search_web -> returns findings

  === Part 3: Agent-as-tool (delegation -- supervisor waits) ===
    [supervisor] task: 'summarize quarterly earnings'
      -> creates ResearchAgent, delegates, WAITS for findings
      -> creates WriterAgent, delegates, WAITS for draft
    [supervisor] returns final draft (nested call stack, supervisor still "on the hook")

  === Part 4: Control handoff (supervisor steps aside) ===
    [supervisor] task: 'summarize quarterly earnings'
      -> HANDOFF to research-agent (supervisor exits, research-agent is now active)
    [research-agent] runs, then HANDOFF to writer-agent
    [writer-agent] runs, then HANDOFF to end (flat call stack, no one left "on the hook")
"""

import asyncio
import re
from dataclasses import dataclass, field
from typing import Annotated

from fastmcp import FastMCP, Client
from pydantic import Field


# ============================================================================
# PART 1: MCP layer -- pure tools, zero judgment
# ============================================================================
# These are ordinary MCP tools (same shape as lessons 01-04). Nothing here
# decides *when* to call them or *what* to do with the result -- that's the
# agent layer's job, added in Part 2.

tools_server = FastMCP(name="research-tools")


@tools_server.tool
async def search_web(
    query: Annotated[str, Field(description="Search query")],
) -> dict:
    """Look up information on a topic (simulated -- no real network call)."""
    fake_index = {
        "quarterly earnings": [
            "Revenue rose 15% year over year.",
            "Operating margin improved to 22%.",
        ],
        "product launch": [
            "New product ships in Q3.",
            "Early customer feedback is positive.",
        ],
    }
    findings = fake_index.get(query.lower(), [f"No indexed findings for '{query}'."])
    return {"query": query, "findings": findings}


@tools_server.tool
async def draft_summary(
    topic: Annotated[str, Field(description="Topic of the summary")],
    findings: Annotated[list[str], Field(description="Findings to summarize")],
) -> dict:
    """Turn findings into a short prose summary (simulated -- no LLM)."""
    body = " ".join(findings)
    return {"topic": topic, "draft": f"Summary of {topic}: {body}"}


# ============================================================================
# PART 2: Agent layer -- the decision loop MCP doesn't have
# ============================================================================
# An "agent" here is nothing more than: a name, a set of tools it's allowed
# to call, and a `run()` method that decides which tool(s) to call and when
# it's done. In production this decision is made by an LLM (lesson 08's
# create_react_agent); here it's a small deterministic policy so the lesson
# runs without an .env file. Swap `_decide()` for an LLM call and the shape
# doesn't change -- that's the point: MCP tools stay identical either way.

class Agent:
    """Minimal agent: wraps MCP tool calls with a decision loop."""

    def __init__(self, name: str, server: FastMCP):
        self.name = name
        self.server = server

    async def _call(self, tool: str, args: dict) -> dict:
        async with Client(self.server) as client:
            result = await client.call_tool(tool, args)
            for block in result.content:
                if hasattr(block, "text"):
                    import json
                    return json.loads(block.text)
        return {}


class ResearchAgent(Agent):
    """Decides to call search_web, then judges when it has enough findings."""

    def __init__(self):
        super().__init__("research-agent", tools_server)

    async def run(self, task: str) -> dict:
        topic = task.replace("summarize", "").strip()
        result = await self._call("search_web", {"query": topic})
        print(f"    [{self.name}] searched '{topic}' -> {len(result['findings'])} findings")
        return result


class WriterAgent(Agent):
    """Decides to call draft_summary once findings are available."""

    def __init__(self):
        super().__init__("writer-agent", tools_server)

    async def run(self, topic: str, findings: list[str]) -> dict:
        result = await self._call("draft_summary", {"topic": topic, "findings": findings})
        print(f"    [{self.name}] drafted: \"{result['draft']}\"")
        return result


# ============================================================================
# PART 3: Agent-as-tool + agent-creates-agent (delegation -- parent waits)
# ============================================================================
# The supervisor doesn't hardcode "always call ResearchAgent then
# WriterAgent" as fixed objects wired up front. It CREATES the specialist
# it needs, per task, the same way a tool call creates a fresh short-lived
# result -- this is "agent creating agent." Each specialist is used here as
# a single callable ("agent-as-tool"): the supervisor never sees that
# ResearchAgent internally called an MCP tool, only the dict it returned.

class SupervisorAgent:
    """Creates and delegates to specialist agents. Waits for each result
    before continuing -- a nested call stack, just like a normal function
    call. The supervisor is "on the hook" until the whole task completes."""

    async def run_delegation(self, task: str) -> str:
        print(f"  [supervisor] task: '{task}'")

        topic = re.sub(r"^summarize\s+", "", task, flags=re.IGNORECASE)

        # agent-creates-agent: spawned fresh for this task, not a singleton
        researcher = ResearchAgent()
        research_result = await researcher.run(task)  # delegate, WAIT

        writer = WriterAgent()
        draft_result = await writer.run(topic, research_result["findings"])  # delegate, WAIT

        print("  [supervisor] returns final draft (nested call stack)")
        return draft_result["draft"]


# ============================================================================
# PART 4: Control handoff -- parent steps aside instead of waiting
# ============================================================================
# This mirrors LangGraph's `Command(goto=<node>, update=<state>)` (lesson
# 13): instead of calling the next agent and waiting for a return value,
# the current agent returns a Handoff naming who goes next and what context
# they need. A small runner loop drives control from agent to agent. No one
# is "on the hook" waiting on a stack frame -- control genuinely moves.

@dataclass
class Handoff:
    next_agent: str | None      # None means "done"
    context: dict = field(default_factory=dict)


async def supervisor_step(context: dict) -> Handoff:
    print(f"  [supervisor] task: '{context['task']}'")
    print("    -> HANDOFF to research-agent (supervisor steps aside)")
    return Handoff(next_agent="research-agent", context=context)


async def research_step(context: dict) -> Handoff:
    researcher = ResearchAgent()
    result = await researcher.run(context["task"])
    context["topic"] = re.sub(r"^summarize\s+", "", context["task"], flags=re.IGNORECASE)
    context["findings"] = result["findings"]
    print("    -> HANDOFF to writer-agent")
    return Handoff(next_agent="writer-agent", context=context)


async def writer_step(context: dict) -> Handoff:
    writer = WriterAgent()
    result = await writer.run(context["topic"], context["findings"])
    context["draft"] = result["draft"]
    print("    -> HANDOFF to end (no one left on the hook)")
    return Handoff(next_agent=None, context=context)


AGENTS = {
    "supervisor": supervisor_step,
    "research-agent": research_step,
    "writer-agent": writer_step,
}


async def run_with_handoffs(task: str) -> str:
    """Drives control from agent to agent until a Handoff says `None`.
    This loop is the whole point: it's what LangGraph's graph executor
    does internally when a node returns Command(goto=...)."""
    context = {"task": task}
    current = "supervisor"
    while current is not None:
        step = AGENTS[current]
        handoff = await step(context)
        current = handoff.next_agent
        context = handoff.context
    return context["draft"]


# ============================================================================
# Demo
# ============================================================================

async def main():
    print("=== Part 1: MCP alone (no agent, no judgment) ===")
    async with Client(tools_server) as client:
        result = await client.call_tool("search_web", {"query": "quarterly earnings"})
        for block in result.content:
            if hasattr(block, "text"):
                import json
                data = json.loads(block.text)
                print(f"    search_web('quarterly earnings') -> {len(data['findings'])} findings")
                print("    (nothing decided this was worth calling -- we called it directly)")
    print()

    print("=== Part 2: A single agent driving MCP tools ===")
    researcher = ResearchAgent()
    await researcher.run("summarize quarterly earnings")
    print("    (the agent decided to call search_web -- MCP tool itself didn't change)")
    print()

    print("=== Part 3: Agent-as-tool + agent-creates-agent (delegation) ===")
    supervisor = SupervisorAgent()
    draft = await supervisor.run_delegation("summarize quarterly earnings")
    print(f"    final: \"{draft}\"")
    print()

    print("=== Part 4: Control handoff (supervisor steps aside) ===")
    draft2 = await run_with_handoffs("summarize quarterly earnings")
    print(f"    final: \"{draft2}\"")
    print()


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Agent vs MCP:
    #   MCP is the interface (tools/resources/prompts, callable by anyone).
    #   Agent is the judgment on top of it (which tool, when to stop, who
    #   should even handle this). Lessons 01-07 proved MCP works with zero
    #   agents. This lesson proves an agent doesn't require MCP either --
    #   what matters is the decision loop, MCP is just how it reaches tools.
    #
    # Agent-creates-agent:
    #   SupervisorAgent doesn't hold two fixed agent objects wired at
    #   startup. It creates ResearchAgent() / WriterAgent() fresh, per task,
    #   the same way you'd instantiate a class for a one-off job. This is
    #   what lets a supervisor handle tasks it wasn't specifically coded
    #   for -- it composes whichever specialists the task calls for.
    #
    # Handing a job to an agent -- two different things people mean by it:
    #   1. Delegation (Part 3): call it, wait, keep control. Simple, but the
    #      caller's stack frame is tied up for the whole sub-task.
    #   2. Handoff (Part 4): transfer the turn, step aside. Matches
    #      LangGraph's Command(goto=...) -- the graph executor, not any one
    #      agent, tracks "who's active now." Needed once agents run long,
    #      get interrupted (lessons 06, 10), or need to resume independently.
    #
    # Advanced techniques this generalizes into (see production mapping in
    # README.md for what maps where):
    #   - Planner/executor: one agent plans steps, a different one executes
    #     each step and reports back (delegation, but with a shared plan).
    #   - Hierarchical supervisors: a supervisor of supervisors -- each
    #     mid-level supervisor owns a domain and creates its own specialists.
    #   - Blackboard / shared state: agents don't call each other at all;
    #     they all read/write one shared state object (LangGraph's
    #     OrchestratorState from lesson 13 is a small version of this).
    #   - Agent-as-MCP-server: expose an entire agent behind an MCP server
    #     (combine this lesson with lesson 15) so ANY MCP client -- not just
    #     code in this repo -- can call it as one black-box tool.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a third specialist (FactCheckAgent) and have the supervisor
    #    decide, based on task text, whether to create it at all.
    # 2. Rewrite run_with_handoffs() so a step can hand off back to
    #    "supervisor" (a loop, not just a line) -- e.g. writer-agent hands
    #    back to supervisor for approval before finishing.
    # 3. Replace `_decide()`-style logic with an LLM call (llm_helper.get_llm)
    #    that picks the next agent by name -- same shape as lesson 12's
    #    LLM-based workflow selection.
    # 4. Wrap ResearchAgent in its own FastMCP server and call it via
    #    MCP-to-MCP (lesson 15) instead of an in-process Python call --
    #    that's "agent-as-MCP-server" made concrete.
