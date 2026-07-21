"""Lesson 12 -- Workflow-Driven Orchestration
===============================================
Concepts:
  - Full orchestration loop: user intent -> workflow selection -> tool execution
  - Workflow discovery from MCP servers
  - LLM selects which workflow to run based on user message
  - Tool gating: only workflow-listed tools are available
  - Multi-step execution following workflow instructions
  - Combining all lessons: server, client, workflows, LLM, interrupts

Flow:
  +-----------+     +--------------------+     +------------------+
  | User      | --> | Orchestrator       | --> | MCP Servers      |
  | "draft a  |     |                    |     |                  |
  |  story    |     | 1. Discover wfs    |     | story-drafting   |
  |  about    |     | 2. LLM selects wf  |     | text-archive     |
  |  oil"     |     | 3. Load wf tools   |     +------------------+
  +-----------+     | 4. LLM plans steps |
                    | 5. Execute tools   |
                    | 6. Return result   |
                    +--------------------+
                         |         ^
                         v         |
                    +--------------------+
                    | LLM (TR Orch.)     |
                    | - Select workflow  |
                    | - Plan tool calls  |
                    | - Process results  |
                    +--------------------+

  Maps to:
    langgraph_mcp_orchestrator.py (full orchestration loop)
    fast_path_matcher.py (regex shortcut for known patterns)
    mcp_protocol.py (tool execution)

** Requires .env for full LLM orchestration; runs in mock mode without it **

Run:  uv run python 12_workflow_orchestration.py
"""

import asyncio
import json
import os
import re
import tempfile
import textwrap
from typing import Annotated
from pathlib import Path
from pydantic import Field
from fastmcp import FastMCP, Client
from dotenv import load_dotenv
import yaml

load_dotenv()


# ============================================================================
# MCP Servers (simplified versions of production servers)
# ============================================================================

story_server = FastMCP(name="story-drafting")
archive_server = FastMCP(name="text-archive")


@story_server.tool
async def draft_story(
    topic: Annotated[str, Field(description="Topic for the story")],
    style: Annotated[str, Field(default="spot", description="Style: spot, bulletin")] = "spot",
) -> dict:
    """Draft a news story about a given topic."""
    return {
        "draft": (
            f"HEADLINE: {topic.title()} - Reuters\n\n"
            f"(Reuters) - This is a {style} story about {topic}. "
            f"Markets reacted positively to the latest developments."
        ),
        "style": style,
        "word_count": 25,
    }


@story_server.tool
async def generate_headline(
    event: Annotated[str, Field(description="Event to generate headline for")],
) -> dict:
    """Generate a Reuters-style headline."""
    return {"headline": f"{event.upper()[:60]} - REUTERS"}


@story_server.tool
async def search_rics(
    query: Annotated[str, Field(description="Company or instrument name")],
) -> dict:
    """Search for Reuters Instrument Codes."""
    return {"query": query, "results": [f"{query.upper()}.O", f"{query.upper()}.L"]}


@archive_server.tool
async def search_archive(
    query: Annotated[str, Field(description="Search query")],
    limit: Annotated[int, Field(default=5, description="Max results")] = 5,
) -> dict:
    """Search the Reuters Text Archive."""
    return {
        "query": query,
        "results": [
            {"title": f"Archive: {query} #{i+1}", "date": f"2024-12-{20-i}"}
            for i in range(min(limit, 3))
        ],
    }


# ============================================================================
# Workflow definitions (inline, no temp files needed)
# ============================================================================

WORKFLOWS = [
    {
        "name": "draft-story",
        "description": "Draft a news story from a topic or event description",
        "tools": ["generate_headline", "draft_story"],
        "trigger_patterns": [r"draft.*story", r"write.*article", r"create.*story"],
        "content": (
            "1. Generate a headline with generate_headline\n"
            "2. Draft the full story with draft_story\n"
            "3. Present the draft for review"
        ),
    },
    {
        "name": "search-and-summarize",
        "description": "Search the text archive for articles and summarize findings",
        "tools": ["search_archive"],
        "trigger_patterns": [r"search.*archive", r"find.*articles", r"look.*up"],
        "content": (
            "1. Search the archive with search_archive\n"
            "2. Summarize the key findings\n"
            "3. Present results to the user"
        ),
    },
    {
        "name": "ric-resolution",
        "description": "Find and validate Reuters Instrument Codes for a company",
        "tools": ["search_rics"],
        "trigger_patterns": [r"find.*ric", r"validate.*ric", r"instrument.*code"],
        "content": (
            "1. Search for RICs matching the query\n"
            "2. Present candidates to the user\n"
            "3. Confirm the selected RIC"
        ),
    },
]


# ============================================================================
# Orchestrator
# ============================================================================

class WorkflowOrchestrator:
    """Simplified version of langgraph_mcp_orchestrator.py.

    Demonstrates the full orchestration loop:
      1. Discover workflows from servers
      2. Select workflow based on user intent
      3. Gate tools to workflow-listed tools only
      4. Execute workflow steps by calling tools
    """

    def __init__(self):
        self._servers: dict[str, FastMCP] = {}
        self._all_tools: dict[str, str] = {}  # tool_name -> server_name
        self._workflows = WORKFLOWS

    def register_server(self, name: str, server: FastMCP):
        self._servers[name] = server

    async def discover_tools(self):
        """Discover tools from all registered servers."""
        for name, server in self._servers.items():
            async with Client(server) as client:
                tools = await client.list_tools()
                for t in tools:
                    self._all_tools[t.name] = name

    def select_workflow_by_pattern(self, user_message: str) -> dict | None:
        """Fast-path: select workflow by regex pattern matching.
        Maps to fast_path_matcher.py."""
        msg_lower = user_message.lower()
        for wf in self._workflows:
            for pattern in wf.get("trigger_patterns", []):
                if re.search(pattern, msg_lower):
                    return wf
        return None

    async def select_workflow_by_llm(self, user_message: str) -> dict | None:
        """LLM-based workflow selection. Uses the LLM to pick the best
        workflow based on the user's message and workflow descriptions."""
        try:
            from llm_helper import get_llm
            llm = get_llm(model="gpt-4o", temperature=0.0)
        except Exception:
            return None

        wf_descriptions = "\n".join(
            f"- {wf['name']}: {wf['description']}"
            for wf in self._workflows
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a workflow selector. Given a user message and available "
                    "workflows, respond with ONLY the workflow name that best matches. "
                    "If none match, respond with 'none'.\n\n"
                    f"Available workflows:\n{wf_descriptions}"
                ),
            },
            {"role": "user", "content": user_message},
        ]

        response = await llm.ainvoke(messages)
        selected_name = response.content.strip().lower()

        for wf in self._workflows:
            if wf["name"] == selected_name:
                return wf
        return None

    def get_gated_tools(self, workflow: dict) -> list[str]:
        """Get only the tools listed in the workflow.
        Maps to workflow-driven tool visibility in the orchestrator."""
        return [t for t in workflow.get("tools", []) if t in self._all_tools]

    async def call_tool(self, tool_name: str, args: dict) -> dict:
        """Call a tool on the appropriate server."""
        server_name = self._all_tools.get(tool_name)
        if not server_name:
            return {"error": f"Unknown tool: {tool_name}"}

        server = self._servers[server_name]
        async with Client(server) as client:
            result = await client.call_tool(tool_name, args)
            return {"tool": tool_name, "server": server_name, "result": result}

    async def execute_workflow(self, workflow: dict, user_message: str) -> list[dict]:
        """Execute a workflow by calling its tools in sequence.

        In production, the LLM drives this loop (deciding which tool
        to call next based on workflow instructions + prior results).
        Here we demonstrate the sequential execution pattern.
        """
        results = []
        gated_tools = self.get_gated_tools(workflow)

        for tool_name in gated_tools:
            # Build simple args from user message
            args = self._build_args(tool_name, user_message)
            result = await self.call_tool(tool_name, args)
            results.append(result)

        return results

    def _build_args(self, tool_name: str, user_message: str) -> dict:
        """Build tool arguments from user message (simplified).
        In production, the LLM extracts parameters from context."""
        topic = user_message.split("about")[-1].strip() if "about" in user_message else user_message

        arg_map = {
            "draft_story": {"topic": topic, "style": "spot"},
            "generate_headline": {"event": topic},
            "search_archive": {"query": topic, "limit": 3},
            "search_rics": {"query": topic},
        }
        return arg_map.get(tool_name, {"query": topic})

    async def handle_message(self, user_message: str) -> dict:
        """Full orchestration loop for a user message."""

        # Step 1: Try fast-path (regex matching)
        workflow = self.select_workflow_by_pattern(user_message)
        selection_method = "fast-path"

        # Step 2: Fall back to LLM selection if no regex match
        if not workflow and os.getenv("ORCHESTRATOR_ENDPOINT"):
            workflow = await self.select_workflow_by_llm(user_message)
            selection_method = "llm"

        if not workflow:
            return {
                "status": "no_workflow",
                "message": "No matching workflow found. Falling back to general chat.",
            }

        # Step 3: Gate tools
        gated = self.get_gated_tools(workflow)

        # Step 4: Execute workflow
        results = await self.execute_workflow(workflow, user_message)

        return {
            "status": "completed",
            "workflow": workflow["name"],
            "selection_method": selection_method,
            "gated_tools": gated,
            "all_tools_available": list(self._all_tools.keys()),
            "tools_hidden": [t for t in self._all_tools if t not in gated],
            "steps": len(results),
            "results": results,
        }


# ============================================================================
# Demo
# ============================================================================

async def main():
    # -- Setup orchestrator --
    orch = WorkflowOrchestrator()
    orch.register_server("story-drafting", story_server)
    orch.register_server("text-archive", archive_server)
    await orch.discover_tools()

    print("=== Workflow Orchestrator ===\n")
    print(f"  Servers: {list(orch._servers.keys())}")
    print(f"  All tools: {list(orch._all_tools.keys())}")
    print(f"  Workflows: {[wf['name'] for wf in orch._workflows]}")
    print()

    # -- Test 1: Draft story (matches fast-path) --
    print("=" * 60)
    print("Test 1: 'Draft a story about oil prices'")
    print("=" * 60 + "\n")

    r1 = await orch.handle_message("Draft a story about oil prices")
    _print_result(r1)

    # -- Test 2: Search archive (matches fast-path) --
    print("=" * 60)
    print("Test 2: 'Search the archive for OPEC articles'")
    print("=" * 60 + "\n")

    r2 = await orch.handle_message("Search the archive for OPEC articles")
    _print_result(r2)

    # -- Test 3: RIC resolution (matches fast-path) --
    print("=" * 60)
    print("Test 3: 'Find the RIC for Apple'")
    print("=" * 60 + "\n")

    r3 = await orch.handle_message("Find the RIC for Apple")
    _print_result(r3)

    # -- Test 4: No match --
    print("=" * 60)
    print("Test 4: 'What is the weather today?'")
    print("=" * 60 + "\n")

    r4 = await orch.handle_message("What is the weather today?")
    _print_result(r4)


def _print_result(result: dict):
    if result["status"] == "no_workflow":
        print(f"  Status: {result['status']}")
        print(f"  Message: {result['message']}")
    else:
        print(f"  Status: {result['status']}")
        print(f"  Workflow: {result['workflow']}")
        print(f"  Selection: {result['selection_method']}")
        print(f"  Gated tools: {result['gated_tools']}")
        print(f"  Hidden tools: {result['tools_hidden']}")
        print(f"  Steps executed: {result['steps']}")
        for step in result["results"]:
            print(f"    [{step['server']}] {step['tool']}: {str(step['result'])[:80]}")
    print()


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # This lesson ties everything together into the full orchestration loop:
    #
    # 1. DISCOVER: list tools from all MCP servers (lesson 11)
    # 2. DISCOVER: list workflows from servers (lesson 09)
    # 3. SELECT: match user intent to workflow
    #    - Fast-path: regex patterns (fast_path_matcher.py)
    #    - LLM: ask the model to select (langgraph_mcp_orchestrator.py)
    # 4. GATE: restrict available tools to workflow's tool list
    # 5. EXECUTE: call tools following workflow instructions
    # 6. RESPOND: return results to the user
    #
    # Production adds:
    #   - LangGraph StateGraph for execution flow
    #   - DynamoDB checkpointing for interrupt/resume
    #   - SSE streaming for real-time responses
    #   - Human-in-the-loop interrupts (lesson 10)
    #   - Forwarded blocks for UI payloads (lesson 08)
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add LLM-driven step planning (LLM decides tool call order)
    # 2. Add interrupt support mid-workflow (pause for user approval)
    # 3. Add parallel tool execution for independent steps
    # 4. Add workflow chaining (one workflow triggers another)
