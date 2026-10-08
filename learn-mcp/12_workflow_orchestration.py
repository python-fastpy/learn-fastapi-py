"""Lesson 12 -- The Orchestration Loop: user message to tool calls
==================================================================

Lessons 10 and 11 built the parts: workflows gate tools, a registry routes
them. This is the loop that runs them, for one greeting request.

  "Create a welcome message for Shubham"
              │
              ▼
  ┌───────────────── ORCHESTRATOR ─────────────────┐
  │ 1. DISCOVER   tools from every server (11)     │      ┌─ greeting-server ─┐
  │               workflows from their files (10)  │ ───► │ greet, farewell   │
  │                                                │      └───────────────────┘
  │ 2. SELECT     a) fast path: regex on the       │      ┌─ translate-server ┐
  │                  message        ~1ms           │ ───► │ translate         │
  │               b) miss? ask the LLM  ~2s        │      └───────────────────┘
  │                  (costs a call, so try a       │
  │                   regex first)                 │
  │                                                │
  │ 3. GATE       tools = wf.tools ONLY            │
  │                                                │
  │ 4. EXECUTE    call them in the workflow's      │
  │               order, collect the results       │
  │                                                │
  │ 5. no workflow matched -> plain chat, no tools │
  └────────────────────────────────────────────────┘

  Step 2 is the whole trick: a regex costs nothing and handles the phrasings
  you have seen before; the LLM handles everything else. Production calls
  these the fast path and the selector.

  In production the LLM also does step 4 -- picking the next tool from the
  workflow text and the results so far. Here step 4 just walks wf.tools in
  order, so the loop stays readable.

** .env gives you real LLM selection in test 2; without it that test simply
   reports no match. Tests 1 and 3 never need it. **

Run:  uv run python 12_workflow_orchestration.py

Maps to: langgraph_mcp_orchestrator.py (the loop), fast_path_matcher.py
(step 2a), mcp_protocol.py (step 4)
"""

import asyncio
import os
import re

from dotenv import load_dotenv
from fastmcp import FastMCP, Client

from greeting_tools import greet, farewell, translate
from workflow_def import WorkflowDef

load_dotenv()

# -- The servers (lesson 11) --------------------------------------------------
# Same shared functions as lessons 10 and 11 -- no local redefinitions.

greeting_server = FastMCP(name="greeting-server")
greeting_server.tool(greet)
greeting_server.tool(farewell)

translate_server = FastMCP(name="translate-server")
translate_server.tool(translate)


# -- The workflows (lesson 10's WorkflowDef, these as plain literals) --------

WORKFLOWS = [
    WorkflowDef(
        name="welcome-message",
        description="Say hello and goodbye to someone",
        tools=["greet", "farewell"],
        trigger_patterns=[r"welcome.*message", r"hello.*goodbye"],
    ),
    WorkflowDef(
        name="translated-greeting",
        description="Greet someone in another language",
        tools=["greet", "translate"],
        trigger_patterns=[r"translate.*greeting", r"greet.*in.*language"],
    ),
]


class Orchestrator:
    """The loop. Simplified langgraph_mcp_orchestrator.py."""

    def __init__(self, workflows: list[WorkflowDef]):
        self.workflows = workflows
        self.servers: dict[str, FastMCP] = {}
        self.routes: dict[str, str] = {}           # tool -> server

    # 1. DISCOVER
    async def discover(self, *servers: FastMCP) -> None:
        for server in servers:
            self.servers[server.name] = server
            async with Client(server) as client:
                for tool in await client.list_tools():
                    self.routes[tool.name] = server.name

    # 2a. SELECT -- fast path
    def match_pattern(self, message: str) -> WorkflowDef | None:
        for wf in self.workflows:
            if any(re.search(p, message.lower()) for p in wf.trigger_patterns):
                return wf
        return None

    # 2b. SELECT -- LLM fallback
    async def match_llm(self, message: str) -> WorkflowDef | None:
        if not os.getenv("ORCHESTRATOR_ENDPOINT"):
            return None
        from llm_helper import get_llm

        catalogue = "\n".join(f"- {wf.name}: {wf.description}" for wf in self.workflows)
        reply = await get_llm(model="gpt-4o", temperature=0.0).ainvoke([
            {"role": "system", "content": "Reply with ONE workflow name from the list, "
                                          f"or 'none'.\n\n{catalogue}"},
            {"role": "user", "content": message},
        ])
        choice = reply.content.strip().lower()
        return next((wf for wf in self.workflows if wf.name == choice), None)

    # 3. GATE
    def gate(self, wf: WorkflowDef) -> list[str]:
        return [t for t in wf.tools if t in self.routes]

    # 4. EXECUTE
    async def call(self, tool: str, args: dict) -> dict:
        async with Client(self.servers[self.routes[tool]]) as client:
            return (await client.call_tool(tool, args)).data

    async def handle(self, message: str) -> dict:
        wf = self.match_pattern(message)
        how = "fast-path"
        if not wf:
            wf, how = await self.match_llm(message), "llm"
        if not wf:
            return {"status": "no_workflow", "how": "none matched -> plain chat"}

        gated = self.gate(wf)
        name, language = _extract(message)
        steps = []
        for tool in gated:                          # production: the LLM picks the order
            args = {"greet": {"name": name},
                    "farewell": {"name": name},
                    "translate": {"text": f"Hello, {name}!", "language": language}}[tool]
            steps.append((tool, await self.call(tool, args)))

        return {
            "status": "completed",
            "workflow": wf.name,
            "how": how,
            "gated": gated,
            "hidden": sorted(set(self.routes) - set(gated)),
            "steps": steps,
        }


def _extract(message: str) -> tuple[str, str]:
    """Pull name and language out of the message. Production lets the LLM do this."""
    name = re.search(r"\b(?:for|to)\s+([A-Z][a-z]+)", message)
    language = re.search(r"\b(?:in|into)\s+([A-Z][a-z]+)", message)
    return (name.group(1) if name else "World",
            language.group(1) if language else "French")


async def main():
    orch = Orchestrator(WORKFLOWS)
    await orch.discover(greeting_server, translate_server)     # 1. DISCOVER

    print("tools    :", sorted(orch.routes))
    print("workflows:", [wf.name for wf in orch.workflows])

    for message in (
        "Create a welcome message for Shubham",      # 2a. regex hit
        "Say something nice to Shubham in German",   # 2b. no regex -> LLM
        "What is the weather today?",                # 5.  nothing matches
    ):
        print(f"\n--- {message!r}")
        r = await orch.handle(message)
        print(f"  selected by : {r['how']}")
        if r["status"] == "no_workflow":
            continue
        print(f"  workflow    : {r['workflow']}")
        print(f"  gated tools : {r['gated']}   (hidden: {r['hidden']})")
        for tool, data in r["steps"]:
            print(f"    {tool:<10} -> {list(data.values())[0]}")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Time both selection paths (time.perf_counter) -- how much does the regex
#    actually save?
# 2. Message 2 has no regex. Add a trigger_pattern that catches it, and watch
#    the LLM call disappear.
# 3. Let the LLM choose the tool ORDER too, instead of walking wf.tools.
# 4. Pause mid-workflow for approval before farewell runs (lesson 06).
