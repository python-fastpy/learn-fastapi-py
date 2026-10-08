"""Lesson 10 -- Workflows: markdown files that gate the tools
=============================================================

This server has three greeting tools. For "say hello and goodbye to Shubham"
only two of them matter. A WORKFLOW is a markdown file that says which tools
a task needs, so the agent is shown those and nothing else.

  A workflow file = YAML frontmatter (the contract) + markdown (the steps):

    ---
    name: welcome-message                  <- unique id
    description: Say hello and goodbye     <- how the orchestrator picks it
    tools: [greet, farewell]               <- the gate: only these are shown
    trigger_patterns: ["welcome.*message"] <- regex fast-path for user intent
    ---
    # Steps
    1. Call `greet` ...                    <- instructions for the agent

  ┌──── ORCHESTRATOR ────┐                 ┌──── MCP SKILL SERVER ────┐
  │                      │  GET /workflows │ mount_workflows() serves │
  │ 1. discover ─────────┼───────────────► │   welcome-message        │
  │                      │ ◄───────────────┤   translated-greeting    │
  │                      │                 │                          │
  │ 2. match the user's  │                 │ tools/list:              │
  │    message to one    │                 │   greet                  │
  │    description       │                 │   farewell               │
  │                      │                 │   translate              │
  │ 3. show the agent    │   tools/call    │                          │
  │    ONLY wf.tools ────┼───────────────► │ only wf.tools are        │
  │                      │                 │ reachable this turn      │
  └──────────────────────┘                 └──────────────────────────┘

  Gating matters because an agent shown every tool picks wrong ones. With
  "welcome-message" selected, `translate` is not in its list, so it cannot
  call it -- no prompt engineering needed.

Run:  uv run python 10_workflows.py

Maps to: shared/workflows/loader.py (parse), shared/workflows/routes.py
(mount_workflows), story-drafting/src/workflows/*.md
"""

import asyncio
import tempfile
import textwrap
from pathlib import Path

from fastmcp import FastMCP, Client
from starlette.responses import JSONResponse

from greeting_tools import greet, farewell, translate
from workflow_def import WorkflowDef

mcp = FastMCP(name="workflow-greetings")


# -- The three tools the workflows choose between -----------------------------
# Imperative registration (same style as lesson 01's Style 2) -- these are
# plain functions shared with lessons 11 and 12, not redefined here.
mcp.tool(greet)
mcp.tool(farewell)
mcp.tool(translate)


# -- Workflow loader (simplified shared/workflows/loader.py) ------------------

def load_workflows(directory: str) -> list[WorkflowDef]:
    """Parse every *.md in a directory into a WorkflowDef."""
    return [
        WorkflowDef.from_markdown(f.read_text(encoding="utf-8"))
        for f in sorted(Path(directory).glob("*.md"))
    ]


def mount_workflows(server: FastMCP, workflows: list[WorkflowDef]) -> None:
    """Expose the workflows over REST, the way the orchestrator discovers them."""
    by_name = {wf.name: wf for wf in workflows}

    @server.custom_route("/workflows", methods=["GET"])
    async def list_workflows(request):
        return JSONResponse([{"name": w.name, "description": w.description} for w in workflows])

    @server.custom_route("/workflows/{name}", methods=["GET"])
    async def get_workflow(request):
        wf = by_name.get(request.path_params["name"])
        if not wf:
            return JSONResponse({"error": "not found"}, status_code=404)
        return JSONResponse(wf.__dict__)


# -- Two sample workflow files over the same three tools ----------------------

WORKFLOW_FILES = {
    "welcome_message.md": textwrap.dedent("""\
        ---
        name: welcome-message
        description: Say hello and goodbye to someone
        tools: [greet, farewell]
        trigger_patterns: ["welcome.*message", "hello.*goodbye"]
        ---

        # Welcome Message

        ## Steps
        1. Call `greet` with the name.
        2. Call `farewell` with the same name.
        3. Present both lines together.
        """),
    "translated_greeting.md": textwrap.dedent("""\
        ---
        name: translated-greeting
        description: Greet someone in another language
        tools: [greet, translate]
        trigger_patterns: ["translate.*greeting", "greet.*in.*language"]
        ---

        # Translated Greeting

        ## Steps
        1. Call `greet` with the name.
        2. Pass that greeting to `translate` with the target language.
        3. Show the original and the translation.
        """),
}


async def main():
    with tempfile.TemporaryDirectory() as tmpdir:
        for filename, text in WORKFLOW_FILES.items():
            (Path(tmpdir) / filename).write_text(text, encoding="utf-8")

        workflows = load_workflows(tmpdir)
        mount_workflows(mcp, workflows)     # served at GET /workflows over HTTP

        async with Client(mcp) as client:
            all_tools = {t.name for t in await client.list_tools()}
            print("server tools:", sorted(all_tools), "\n")

            for wf in workflows:
                print(f"workflow: {wf.name}")
                print(f"  description: {wf.description}")
                print(f"  triggers   : {wf.trigger_patterns}")
                print(f"  VISIBLE    : {sorted(set(wf.tools) & all_tools)}")
                print(f"  hidden     : {sorted(all_tools - set(wf.tools))}")
                print(f"  step 1     : {wf.content.splitlines()[3]}")
                print()

            # The gate is just set membership -- the agent is handed wf.tools.
            wf = next(w for w in workflows if w.name == "welcome-message")
            hidden = sorted(all_tools - set(wf.tools))
            r = await client.call_tool("greet", {"name": "Shubham"})
            print(f"'{wf.name}' calls greet ->", r.data["message"])
            print(f"'{wf.name}' cannot call {hidden[0]}: not in {wf.tools}")


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Add farewell_only.md with tools: [farewell]. It is discovered with no
#    code change -- that is the point of file-based workflows.
# 2. Match trigger_patterns with re.search against "send a welcome message"
#    to pick the workflow, instead of selecting it by name.
# 3. Serve the server over HTTP (lesson 01 --http) and curl GET /workflows.
