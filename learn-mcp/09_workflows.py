"""Lesson 09 -- Workflow System
================================

WHY THIS MATTERS:
  A skill might have 10+ tools, but for a given task (e.g., "create a
  greeting card"), only 2 of them are relevant. Workflows solve this:
  they're markdown files that say "for this task, use these tools in
  this order." The orchestrator reads workflows at startup, picks the
  right one based on the user's message, and hides all other tools
  from the LLM agent. This keeps the agent focused and prevents it
  from calling tools that don't belong to the current task.

WHAT YOU'LL LEARN:
  1. Define workflows as markdown files with YAML frontmatter
  2. Parse and load workflows programmatically
  3. Mount REST endpoints so the orchestrator can discover workflows
  4. Understand tool gating -- only workflow-listed tools are visible

Concepts:
  - Workflows: markdown files with YAML frontmatter
  - Workflow fields: name, description, tools, trigger_patterns
  - mount_workflows(): auto-register REST endpoints
  - GET /workflows: list all workflows
  - GET /workflows/{name}: get specific workflow
  - Workflow-driven tool visibility (tools listed in workflow props)

Flow:
  +------------------+     +-------------------+
  | Orchestrator     | --> | MCP Skill Server  |
  | (backend agent)  |     |                   |
  +------------------+     | Endpoints:        |
       |                   |  GET /workflows   |
       |                   |  GET /workflows/X |
       +-- discover -----> |  POST /mcp (tools)|
       |   workflows       +-------------------+
       |                   | Workflows:        |
       +-- select one ---> |  welcome-message  |
       |                   |  translated-greet |
       +-- read tools ---> +-------------------+
       |   from workflow   | Tools:            |
       +-- execute ------> |  greet            |
           tools           |  farewell         |
                           |  translate        |
                           +-------------------+

  Maps to:
    shared/workflows/loader.py (WorkflowDef, parse markdown)
    shared/workflows/routes.py (mount_workflows, REST endpoints)
    story-drafting/src/workflows/*.md (production workflow files)

PREREQUISITES: Lesson 01 (tools), Lesson 04 (resources)

Run:  uv run python 09_workflows.py

EXPECTED OUTPUT:
  === Workflow Files Created ===

    greeting_card.md
    translated_greeting.md
    welcome_message.md

  === Server Tools (6) ===

    - greet: Return a greeting for the given name.
    - farewell: Return a farewell for the given name.
    - translate: Translate text into another language (simulated).
    - format_card: Format a message as a greeting card.
    - detect_mood: Detect the mood of a piece of text (simulated).
    - slow_greet: Greet someone after a short delay.

  === Workflows (3) ===

    Workflow: greeting-card
      Description: Create a formatted greeting card
      Tools: ['greet', 'format_card']
      Triggers: ['greeting.*card', 'create.*card']

    Workflow: translated-greeting
      Description: Translate a greeting into another language
      Tools: ['greet', 'translate']
      Triggers: ['translate.*greeting', 'greet.*in.*language']

    Workflow: welcome-message
      Description: Generate a full welcome message with greeting and farewell
      Tools: ['greet', 'farewell']
      Triggers: ['welcome.*message', 'say.*hello.*goodbye']

  === Workflow-Driven Tool Visibility ===

    Concept: tools listed in a workflow's 'tools' field are
    only loaded when that workflow is selected. This prevents
    the agent from seeing all tools upfront.

    If 'greeting-card' selected:
      Visible tools: ['format_card', 'greet']
      Hidden tools:  ['detect_mood', 'farewell', 'slow_greet', 'translate']

    If 'translated-greeting' selected:
      Visible tools: ['greet', 'translate']
      Hidden tools:  ['detect_mood', 'farewell', 'format_card', 'slow_greet']

    If 'welcome-message' selected:
      Visible tools: ['farewell', 'greet']
      Hidden tools:  ['detect_mood', 'format_card', 'slow_greet', 'translate']
"""

import asyncio
import os
import json
import tempfile
import textwrap
from typing import Annotated
from pathlib import Path
from pydantic import Field
from fastmcp import FastMCP, Client
import yaml
from starlette.responses import JSONResponse


mcp = FastMCP(name="workflow-demo")


# ============================================================================
# Workflow loader (simplified version of shared/workflows/loader.py)
# ============================================================================

class WorkflowDef:
    """A workflow definition parsed from a markdown file."""

    def __init__(self, name: str, description: str, tools: list[str],
                 trigger_patterns: list[str], content: str):
        self.name = name
        self.description = description
        self.tools = tools
        self.trigger_patterns = trigger_patterns
        self.content = content

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "trigger_patterns": self.trigger_patterns,
            "content": self.content,
        }

    @classmethod
    def from_markdown(cls, text: str) -> "WorkflowDef":
        """Parse a workflow markdown file with YAML frontmatter."""
        if not text.startswith("---"):
            raise ValueError("Workflow must start with YAML frontmatter (---)")

        _, frontmatter, content = text.split("---", 2)
        meta = yaml.safe_load(frontmatter)

        return cls(
            name=meta["name"],
            description=meta["description"],
            tools=meta.get("tools", []),
            trigger_patterns=meta.get("trigger_patterns", []),
            content=content.strip(),
        )


def load_workflows(directory: str) -> list[WorkflowDef]:
    """Load all workflow markdown files from a directory."""
    workflows = []
    for md_file in sorted(Path(directory).glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        try:
            wf = WorkflowDef.from_markdown(text)
            workflows.append(wf)
        except Exception as e:
            print(f"  Warning: failed to parse {md_file.name}: {e}")
    return workflows


def mount_workflows(server: FastMCP, workflow_dir: str):
    """Mount workflow REST endpoints on the MCP server.

    This mirrors shared/workflows/routes.py:
      GET /workflows -> list all workflows (name + description only)
      GET /workflows/{name} -> full workflow definition
    """
    workflows = load_workflows(workflow_dir)
    wf_by_name = {wf.name: wf for wf in workflows}

    @server.custom_route("/workflows", methods=["GET"])
    async def list_workflows(request):
        summaries = [
            {"name": wf.name, "description": wf.description}
            for wf in workflows
        ]
        return JSONResponse(summaries)

    @server.custom_route("/workflows/{name}", methods=["GET"])
    async def get_workflow(request):
        name = request.path_params["name"]
        wf = wf_by_name.get(name)
        if not wf:
            return JSONResponse({"error": f"Workflow '{name}' not found"}, status_code=404)
        return JSONResponse(wf.to_dict())


# ============================================================================
# Create sample workflow markdown files
# ============================================================================

def create_sample_workflows(directory: str):
    """Create sample workflow files matching production patterns."""

    wf1 = textwrap.dedent("""\
    ---
    name: welcome-message
    description: Generate a full welcome message with greeting and farewell
    tools:
      - greet
      - farewell
    trigger_patterns:
      - "welcome.*message"
      - "say.*hello.*goodbye"
    ---

    # Welcome Message Workflow

    ## Steps

    1. Ask the user for the person's name
    2. Call `greet` with the name to generate a hello message
    3. Call `farewell` with the name to generate a goodbye message
    4. Combine both into a full welcome message for the user

    ## Notes

    - Always greet before farewell -- order matters for politeness
    - Present both messages together as one cohesive welcome
    """)

    wf2 = textwrap.dedent("""\
    ---
    name: translated-greeting
    description: Translate a greeting into another language
    tools:
      - greet
      - translate
    trigger_patterns:
      - "translate.*greeting"
      - "greet.*in.*language"
    ---

    # Translated Greeting Workflow

    ## Steps

    1. Ask the user for the person's name and target language
    2. Call `greet` with the name to generate the greeting
    3. Call `translate` with the greeting text and target language
    4. Present both the original and translated greeting

    ## Notes

    - Default to Spanish if no language is specified
    - Always show the original alongside the translation
    """)

    wf3 = textwrap.dedent("""\
    ---
    name: greeting-card
    description: Create a formatted greeting card
    tools:
      - greet
      - format_card
    trigger_patterns:
      - "greeting.*card"
      - "create.*card"
    ---

    # Greeting Card Workflow

    ## Steps

    1. Ask the user for the recipient's name
    2. Call `greet` to generate the greeting message
    3. Call `format_card` with the name and greeting to create the card
    4. Present the formatted card to the user

    ## Notes

    - The card format uses a bordered text layout
    - Optionally allow the user to customize the message before formatting
    """)

    os.makedirs(directory, exist_ok=True)
    for filename, content in [
        ("welcome_message.md", wf1),
        ("translated_greeting.md", wf2),
        ("greeting_card.md", wf3),
    ]:
        Path(os.path.join(directory, filename)).write_text(content, encoding="utf-8")


# ============================================================================
# Register tools referenced by workflows
# ============================================================================

@mcp.tool
async def greet(
    name: Annotated[str, Field(description="Name of the person to greet")],
) -> dict:
    """Return a greeting for the given name."""
    return {"message": f"Hello, {name}!"}


@mcp.tool
async def farewell(
    name: Annotated[str, Field(description="Name of the person to bid farewell")],
) -> dict:
    """Return a farewell for the given name."""
    return {"message": f"Goodbye, {name}!"}


@mcp.tool
async def translate(
    text: Annotated[str, Field(description="Text to translate")],
    language: Annotated[str, Field(description="Target language")],
) -> dict:
    """Translate text into another language (simulated)."""
    return {"original": text, "translated": f"[{language}] {text}", "language": language}


@mcp.tool
async def format_card(
    name: Annotated[str, Field(description="Recipient name")],
    message: Annotated[str, Field(description="Card message")],
) -> dict:
    """Format a message as a greeting card."""
    card = f"=== Card for {name} ===\n{message}\n================="
    return {"card": card, "name": name}


@mcp.tool
async def detect_mood(
    text: Annotated[str, Field(description="Text to analyse for mood")],
) -> dict:
    """Detect the mood of a piece of text (simulated)."""
    return {"text": text, "mood": "happy"}


@mcp.tool
async def slow_greet(
    name: Annotated[str, Field(description="Name of the person to greet")],
    seconds: Annotated[float, Field(default=1.0, description="Seconds to wait")] = 1.0,
) -> dict:
    """Greet someone after a short delay."""
    await asyncio.sleep(seconds)
    return {"message": f"Hello, {name}!", "waited": seconds}


# ============================================================================
# Main: create workflows, mount them, demonstrate discovery
# ============================================================================

async def main():
    # Create temp workflow directory with sample files
    with tempfile.TemporaryDirectory() as tmpdir:
        create_sample_workflows(tmpdir)
        mount_workflows(mcp, tmpdir)

        print("=== Workflow Files Created ===\n")
        for f in sorted(Path(tmpdir).glob("*.md")):
            print(f"  {f.name}")
        print()

        # Use in-process client (no HTTP needed for workflow demo)
        async with Client(mcp) as client:
            # -- Discovery: what tools does this server have? --
            tools = await client.list_tools()
            print(f"=== Server Tools ({len(tools)}) ===\n")
            for t in tools:
                print(f"  - {t.name}: {t.description}")
            print()

        # -- Workflow discovery (via REST-like access) --
        # In production, the orchestrator calls GET /workflows
        # Here we demonstrate the workflow loader directly
        workflows = load_workflows(tmpdir)

        print(f"=== Workflows ({len(workflows)}) ===\n")
        for wf in workflows:
            print(f"  Workflow: {wf.name}")
            print(f"    Description: {wf.description}")
            print(f"    Tools: {wf.tools}")
            print(f"    Triggers: {wf.trigger_patterns}")
            print()

        # -- Workflow-driven tool visibility --
        print("=== Workflow-Driven Tool Visibility ===\n")
        print("  Concept: tools listed in a workflow's 'tools' field are")
        print("  only loaded when that workflow is selected. This prevents")
        print("  the agent from seeing all tools upfront.\n")

        for wf in workflows:
            all_tools = {t.name for t in tools}
            wf_tools = set(wf.tools)
            visible = wf_tools & all_tools
            hidden = all_tools - wf_tools

            print(f"  If '{wf.name}' selected:")
            print(f"    Visible tools: {sorted(visible)}")
            print(f"    Hidden tools:  {sorted(hidden)}")
            print()


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Workflows are markdown files with YAML frontmatter that define:
    #   - name: unique identifier
    #   - description: what the workflow does (used for routing)
    #   - tools: which MCP tools this workflow uses
    #   - trigger_patterns: regex patterns that match user intent
    #   - content: step-by-step instructions for the agent
    #
    # The orchestrator workflow:
    #   1. GET /workflows -> see available workflows
    #   2. Select workflow by matching user intent to descriptions
    #   3. Load only the tools listed in that workflow
    #   4. Execute the workflow steps
    #
    # This is the exact pattern from:
    #   shared/workflows/loader.py (parsing)
    #   shared/workflows/routes.py (REST endpoints)
    #   langgraph_mcp_orchestrator.py (workflow selection)
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a new workflow markdown file and verify it gets discovered
    # 2. Implement trigger_patterns matching with regex
    # 3. Add a "sub-workflow" reference (e.g., a reusable greeting step)
