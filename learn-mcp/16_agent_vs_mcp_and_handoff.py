"""Lesson 16 -- Agent vs MCP, and two ways to hand off a job
============================================================

MCP has no judgment. greet() answers when called; it never decides that it
should be called. That decision is the AGENT -- a loop that picks the tool
and says when the task is done. Lessons 01-07 ran MCP with no agent at all.

  MCP layer -- callable, no judgment (lessons 01-04):
      greet(name)                 translate(text, language)
           ▲                               ▲
           │ called by                     │ called by
  Agent layer -- judgment: which tool, when to stop:
      GreetAgent                      TranslateAgent
           ▲                               ▲
           └───────────────┬───────────────┘
                           │ each is created per task and used as ONE
                           │ callable -- "agent-as-tool": the caller sees
                           │ the answer, never the tool calls inside
                    SupervisorAgent
                           ▲
                           │ "greet Shubham in French"
                          You

  Once the supervisor has specialists, there are two different things people
  mean by "hand it to another agent":

   3. DELEGATION                     4. CONTROL HANDOFF
      supervisor                        supervisor ─► greet-agent
        ├─ await greet-agent                          ─► translate-agent
        └─ await translate-agent                      ─► done
      returns the final answer          each step returns Handoff(next_agent)
                                        and a runner loop moves control on
      nested stack: the supervisor      flat stack: nobody is waiting; this
      is on the hook until both         is LangGraph's Command(goto=...)
      specialists come back             (lesson 13) by hand

  Delegation is simpler. Handoff is what you need once steps run long, pause
  for a human (lesson 06), or resume independently -- there is no stack frame
  left holding the job.

  The decision logic here is a plain `if` so the lesson needs no .env. Swap it
  for an LLM call and nothing else changes -- that is the point: the MCP tools
  below are identical either way.

Run:  uv run python 16_agent_vs_mcp_and_handoff.py

Maps to: langgraph_mcp_orchestrator.py (nodes as agents, edges as handoffs),
each skill in sphinx_leon-assistant-skills as one agent-as-tool
"""

import asyncio
import re
from dataclasses import dataclass, field

from fastmcp import Client, FastMCP

# -- The MCP layer: two tools, zero judgment ---------------------------------

tools_server = FastMCP(name="greeting-tools")


@tools_server.tool
def greet(name: str) -> dict:
    """Say hello to someone."""
    return {"greeting": f"Hello, {name}!"}


@tools_server.tool
def translate(text: str, language: str) -> dict:
    """Translate text into another language (simulated)."""
    return {"translated": f"[{language}] {text}"}


# -- The agent layer: a loop that decides ------------------------------------

class Agent:
    """A name, the tools it may call, and a run() that decides."""

    def __init__(self, name: str):
        self.name = name

    async def _call(self, tool: str, args: dict) -> dict:
        async with Client(tools_server) as client:
            return (await client.call_tool(tool, args)).data


class GreetAgent(Agent):
    def __init__(self):
        super().__init__("greet-agent")

    async def run(self, task: str) -> str:
        name = re.search(r"\b(?i:greet|to)\s+([A-Z][a-z]+)", task)   # keyword any case, name capitalised
        name = name.group(1) if name else "World"
        # The judgment: this task needs greet, with this argument, once.
        greeting = (await self._call("greet", {"name": name}))["greeting"]
        print(f"    [{self.name}] chose greet(name={name!r}) -> {greeting}")
        return greeting


class TranslateAgent(Agent):
    def __init__(self):
        super().__init__("translate-agent")

    async def run(self, text: str, task: str) -> str:
        language = re.search(r"\b(?:in|into)\s+([A-Z][a-z]+)", task)
        if not language:
            print(f"    [{self.name}] no language in the task -- nothing to do")
            return text                              # deciding NOT to call a tool
        result = (await self._call("translate", {"text": text, "language": language.group(1)}))
        print(f"    [{self.name}] chose translate(language={language.group(1)!r}) -> {result['translated']}")
        return result["translated"]


# -- 3. Delegation: the supervisor calls and waits ---------------------------

class SupervisorAgent:
    """Creates the specialist it needs per task, then awaits each one."""

    async def run(self, task: str) -> str:
        print(f"  [supervisor] task: {task!r}")
        greeting = await GreetAgent().run(task)               # created here, then WAIT
        final = await TranslateAgent().run(greeting, task)    # created here, then WAIT
        print("  [supervisor] still on the hook until both returned")
        return final


# -- 4. Control handoff: each step names who goes next -----------------------

@dataclass
class Handoff:
    next_agent: str | None                 # None == done
    context: dict = field(default_factory=dict)


async def supervisor_step(ctx: dict) -> Handoff:
    print(f"  [supervisor] task: {ctx['task']!r} -> HANDOFF to greet-agent, then steps aside")
    return Handoff("greet-agent", ctx)


async def greet_step(ctx: dict) -> Handoff:
    ctx["greeting"] = await GreetAgent().run(ctx["task"])
    print("      -> HANDOFF to translate-agent")
    return Handoff("translate-agent", ctx)


async def translate_step(ctx: dict) -> Handoff:
    ctx["final"] = await TranslateAgent().run(ctx["greeting"], ctx["task"])
    print("      -> HANDOFF to end (nobody left waiting)")
    return Handoff(None, ctx)


STEPS = {"supervisor": supervisor_step, "greet-agent": greet_step, "translate-agent": translate_step}


async def run_with_handoffs(task: str) -> str:
    """The runner loop. This is what a graph executor does with Command(goto=...)."""
    ctx, current = {"task": task}, "supervisor"
    while current:
        handoff = await STEPS[current](ctx)
        current, ctx = handoff.next_agent, handoff.context
    return ctx["final"]


async def main():
    task = "greet Shubham in French"

    print("1. MCP alone -- we decided, not the protocol")
    async with Client(tools_server) as client:
        r = await client.call_tool("greet", {"name": "Shubham"})
        print(f"    greet -> {r.data['greeting']}")
        print("    the tool had no say in being called\n")

    print("2. one agent deciding for itself")
    await GreetAgent().run(task)
    print("    same tool, unchanged -- the judgment moved above it\n")

    print("3. delegation -- supervisor waits for each specialist")
    print(f"    final: {await SupervisorAgent().run(task)}\n")

    print("4. control handoff -- supervisor steps aside")
    print(f"    final: {await run_with_handoffs(task)}")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Drop "in French" from the task. TranslateAgent decides to call nothing --
#    an agent choosing not to act is still a decision.
# 2. Let translate-agent hand back to "supervisor" for approval before
#    finishing, so the handoff graph has a loop rather than a line.
# 3. Replace the regexes with one llm_helper.get_llm() call that picks the
#    next agent by name (lesson 12 did this for workflows).
# 4. Put GreetAgent behind its own FastMCP server and reach it with MCP-to-MCP
#    (lesson 15) -- that is "agent as MCP server", callable by anyone.
