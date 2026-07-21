"""Lesson 09 -- Workflow System
================================
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
       +-- select one ---> |  summarize-news   |
       |                   |  draft-story      |
       +-- read tools ---> +-------------------+
       |   from workflow   | Tools:            |
       +-- execute ------> |  search_articles  |
           tools           |  summarize_text   |
                           |  generate_headline|
                           +-------------------+

  Maps to:
    shared/workflows/loader.py (WorkflowDef, parse markdown)
    shared/workflows/routes.py (mount_workflows, REST endpoints)
    story-drafting/src/workflows/*.md (production workflow files)

No LLM needed -- demonstrates the workflow discovery system.

Run:  uv run python 09_workflows.py
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
    name: summarize-news
    description: Search for recent articles on a topic and generate a summary
    tools:
      - search_articles
      - summarize_text
    trigger_patterns:
      - "summarize.*news"
      - "what.*latest.*about"
    ---

    # Summarize News Workflow

    ## Steps

    1. Ask the user for the topic they want summarized
    2. Call `search_articles` with the topic to find recent articles
    3. Call `summarize_text` with the combined article content
    4. Present the summary to the user

    ## Notes

    - Default to searching for 5 articles unless user specifies otherwise
    - Use "bullet" style for summaries unless user requests otherwise
    """)

    wf2 = textwrap.dedent("""\
    ---
    name: draft-story
    description: Draft a news story from a topic or event description
    tools:
      - generate_headline
      - draft_story
    trigger_patterns:
      - "draft.*story"
      - "write.*article"
      - "create.*story"
    ---

    # Draft Story Workflow

    ## Steps

    1. Confirm the topic and style (spot, bulletin, urgent) with the user
    2. Call `generate_headline` to create a headline
    3. Call `draft_story` to generate the full story
    4. Present the draft for user review

    ## Notes

    - Default to "spot" style unless otherwise specified
    - Always show the draft for review before finalizing
    """)

    wf3 = textwrap.dedent("""\
    ---
    name: ric-resolution
    description: Validate and resolve RIC (Reuters Instrument Code) symbols
    tools:
      - validate_ric
      - search_rics
    trigger_patterns:
      - "validate.*ric"
      - "find.*ric"
      - "resolve.*instrument"
    ---

    # RIC Resolution Sub-Workflow

    ## Steps

    1. If user provides a specific RIC, call `validate_ric` to check it
    2. If the RIC is invalid or user wants alternatives, call `search_rics`
    3. Present matching RICs for user selection
    4. Return the confirmed RIC

    ## Notes

    - This is a reusable sub-workflow called by other workflows
    - Always confirm the final RIC with the user
    """)

    os.makedirs(directory, exist_ok=True)
    for filename, content in [
        ("summarize_news.md", wf1),
        ("draft_story.md", wf2),
        ("ric_resolution.md", wf3),
    ]:
        Path(os.path.join(directory, filename)).write_text(content, encoding="utf-8")


# ============================================================================
# Register tools referenced by workflows
# ============================================================================

@mcp.tool
async def search_articles(
    query: Annotated[str, Field(description="Search query")],
    limit: Annotated[int, Field(default=5, description="Max results")] = 5,
) -> dict:
    """Search for news articles."""
    return {
        "query": query,
        "articles": [{"title": f"{query} article #{i+1}"} for i in range(min(limit, 5))],
    }


@mcp.tool
async def summarize_text(
    text: Annotated[str, Field(description="Text to summarize")],
) -> dict:
    """Summarize text."""
    return {"summary": f"Summary of: {text[:50]}...", "word_count": len(text.split())}


@mcp.tool
async def generate_headline(
    event: Annotated[str, Field(description="Event description")],
) -> dict:
    """Generate a headline."""
    return {"headline": f"REUTERS: {event[:60]}"}


@mcp.tool
async def draft_story(
    topic: Annotated[str, Field(description="Story topic")],
) -> dict:
    """Draft a story."""
    return {"draft": f"Story about {topic}...", "style": "spot"}


@mcp.tool
async def validate_ric(
    ric: Annotated[str, Field(description="RIC to validate")],
) -> dict:
    """Validate a RIC."""
    return {"ric": ric, "valid": ric.endswith(".O") or ric.endswith(".L")}


@mcp.tool
async def search_rics(
    query: Annotated[str, Field(description="RIC search query")],
) -> dict:
    """Search for RICs."""
    return {"query": query, "results": [f"{query}.O", f"{query}.L", f"{query}.N"]}


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
    # 3. Add a "sub-workflow" reference (ric-resolution used by other workflows)
