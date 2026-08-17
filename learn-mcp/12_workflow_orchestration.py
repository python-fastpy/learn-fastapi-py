"""Lesson 12 -- Workflow-Driven Orchestration
===============================================

WHY THIS MATTERS:
  This lesson combines everything from lessons 01-11 into a single
  orchestration loop -- the same pattern used by the production backend.
  When a user says "create a welcome message for Alice," the orchestrator:
    1. Discovers available workflows from the skill servers
    2. Picks the right workflow (fast-path regex or LLM fallback)
    3. Gates tools to only those listed in the workflow
    4. Calls tools in sequence
    5. Returns the result

  This is the highest-level pattern *before* LangGraph (lesson 13).

WHAT YOU'LL LEARN:
  1. The complete orchestration loop from user message to response
  2. Fast-path matching: skip the LLM for well-known patterns (~100ms)
  3. LLM-based workflow selection as fallback (~2-3s)
  4. Tool gating in action: hiding irrelevant tools from the agent
  5. How all the pieces from prior lessons fit together

Concepts:
  - Full orchestration loop: user intent -> workflow selection -> tool execution
  - Workflow discovery from MCP servers
  - LLM selects which workflow to run based on user message
  - Tool gating: only workflow-listed tools are available
  - Multi-step execution following workflow instructions

Flow:
  +-----------+     +--------------------+     +------------------+
  | User      | --> | Orchestrator       | --> | MCP Servers      |
  | "create a |     |                    |     |                  |
  |  welcome  |     | 1. Discover wfs    |     | greeting-server  |
  |  message  |     | 2. LLM selects wf  |     | translation-srv  |
  |  for      |     | 3. Load wf tools   |     +------------------+
  |  Alice"   |     | 4. LLM plans steps |
  +-----------+     | 5. Execute tools   |
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

PREREQUISITES: Lessons 09 (workflows), 11 (multi-server), 06 (client patterns)

** Requires .env for full LLM orchestration; runs in mock mode without it **

Run:  uv run python 12_workflow_orchestration.py

EXPECTED OUTPUT (mock mode -- no .env):
  === Workflow-Driven Orchestration Demo ===

  Setting up orchestrator...
    Registered 2 servers with 5 tools
    Loaded 3 workflows

  === Test 1: "Create a welcome message for Alice" ===
    Fast-path matched -> welcome-message
    Available tools (gated): ['greet', 'farewell']
    Calling greet({name: 'Alice'})...
    Calling farewell({name: 'Alice'})...
    Result: Welcome message for Alice (2 tool calls)

  === Test 2: "Translate a greeting into French for Bob" ===
    Fast-path matched -> translated-greeting
    Available tools (gated): ['greet', 'translate']
    Calling greet({name: 'Bob'})...
    Calling translate({text: 'Hello, Bob!', language: 'French'})...
    Result: Translated greeting for Bob (2 tool calls)

  === Test 3: "Create a greeting card for Bob" ===
    Fast-path matched -> greeting-card
    Available tools (gated): ['greet', 'format_card']
    Calling greet({name: 'Bob'})...
    Calling format_card({name: 'Bob', message: 'Hello, Bob!'})...
    Result: Greeting card for Bob (2 tool calls)

  === Test 4: "What's the weather today?" ===
    No workflow matched (no fast-path, no LLM match)
    Falling back to general response.
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

greeting_server = FastMCP(name="greeting-server")
translation_server = FastMCP(name="translation-server")


@greeting_server.tool
async def greet(
    name: Annotated[str, Field(description="Name of the person to greet")],
) -> dict:
    """Generate a friendly greeting for someone."""
    return {"message": f"Hello, {name}!", "word_count": 3}


@greeting_server.tool
async def farewell(
    name: Annotated[str, Field(description="Name of the person to say goodbye to")],
) -> dict:
    """Generate a farewell message for someone."""
    return {"message": f"Goodbye, {name}!", "word_count": 2}


@greeting_server.tool
async def format_card(
    name: Annotated[str, Field(description="Name for the card")],
    message: Annotated[str, Field(description="Message to display on the card")],
) -> dict:
    """Format a message as a decorative greeting card."""
    return {
        "card": f"=== Card for {name} ===\n{message}\n=======",
        "name": name,
    }


@translation_server.tool
async def translate(
    text: Annotated[str, Field(description="Text to translate")],
    language: Annotated[str, Field(default="French", description="Target language")] = "French",
) -> dict:
    """Translate text into another language."""
    return {"original": text, "translated": f"[{language}] {text}", "language": language}


@translation_server.tool
async def detect_language(
    text: Annotated[str, Field(description="Text to detect language of")],
) -> dict:
    """Detect the language of the given text."""
    return {"text": text, "detected": "en", "confidence": 0.95}


# ============================================================================
# Workflow definitions (inline, no temp files needed)
# ============================================================================

WORKFLOWS = [
    {
        "name": "welcome-message",
        "description": "Create a welcome message that greets and bids farewell to someone",
        "tools": ["greet", "farewell"],
        "trigger_patterns": [r"welcome.*message", r"say.*hello.*goodbye"],
        "content": (
            "1. Greet the person with greet\n"
            "2. Say farewell with farewell\n"
            "3. Present the combined welcome message"
        ),
    },
    {
        "name": "translated-greeting",
        "description": "Greet someone and translate the greeting into another language",
        "tools": ["greet", "translate"],
        "trigger_patterns": [r"translate.*greeting", r"greet.*in.*language"],
        "content": (
            "1. Generate a greeting with greet\n"
            "2. Translate the greeting with translate\n"
            "3. Present the translated greeting"
        ),
    },
    {
        "name": "greeting-card",
        "description": "Create a decorative greeting card for someone",
        "tools": ["greet", "format_card"],
        "trigger_patterns": [r"greeting.*card", r"create.*card"],
        "content": (
            "1. Generate a greeting with greet\n"
            "2. Format as a card with format_card\n"
            "3. Present the greeting card"
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
        # Extract name from messages like "create a welcome message for Alice"
        name_match = re.search(r"\bfor\s+([A-Z][a-z]+)", user_message)
        name = name_match.group(1) if name_match else "World"

        # Extract language from messages like "into French" or "in Spanish"
        lang_match = re.search(r"(?:into|in)\s+([A-Z][a-z]+)", user_message)
        language = lang_match.group(1) if lang_match else "French"

        arg_map = {
            "greet": {"name": name},
            "farewell": {"name": name},
            "format_card": {"name": name, "message": f"Hello, {name}!"},
            "translate": {"text": f"Hello, {name}!", "language": language},
            "detect_language": {"text": user_message},
        }
        return arg_map.get(tool_name, {"name": name})

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
    orch.register_server("greeting-server", greeting_server)
    orch.register_server("translation-server", translation_server)
    await orch.discover_tools()

    print("=== Workflow Orchestrator ===\n")
    print(f"  Servers: {list(orch._servers.keys())}")
    print(f"  All tools: {list(orch._all_tools.keys())}")
    print(f"  Workflows: {[wf['name'] for wf in orch._workflows]}")
    print()

    # -- Test 1: Welcome message (matches fast-path) --
    print("=" * 60)
    print("Test 1: 'Create a welcome message for Alice'")
    print("=" * 60 + "\n")

    r1 = await orch.handle_message("Create a welcome message for Alice")
    _print_result(r1)

    # -- Test 2: Translated greeting (matches fast-path) --
    print("=" * 60)
    print("Test 2: 'Translate a greeting into French for Bob'")
    print("=" * 60 + "\n")

    r2 = await orch.handle_message("Translate a greeting into French for Bob")
    _print_result(r2)

    # -- Test 3: Greeting card (matches fast-path) --
    print("=" * 60)
    print("Test 3: 'Create a greeting card for Bob'")
    print("=" * 60 + "\n")

    r3 = await orch.handle_message("Create a greeting card for Bob")
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
