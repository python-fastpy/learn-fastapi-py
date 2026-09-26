"""A workflow MCP server -- procedures the agent must follow, step by step.

The notes server (demo_mcp_server.py) adds *capability*: new things the
agent can do. This server adds *procedure*: a fixed order of operations
the agent works through, one step at a time, where the server decides
what comes next.

Why that matters: left alone, an agent improvises. Asked to "write a
script", it will happily write one and declare victory without ever
running it. A workflow makes "run it" a step the server hands out and
tracks -- the agent can't reach the end without passing through it.

  agent: start_workflow("new-script", target="fib.py")
  server:  -> run_id=wf-1, step 1/4: "Write the script to fib.py..."
  agent: (writes the file)
  agent: complete_step(run_id, "wrote fib.py")
  server:  -> step 2/4: "Run it with run_command..."
  agent: (runs it)
  agent: complete_step(run_id, "exit code 0")
  server:  -> step 3/4 ...
                                    ... until "workflow complete"

Workflows are markdown files in workflows/ with YAML frontmatter -- the
same shape as learn-mcp lesson 10 and the production shared/workflows/
loader. Add a .md file, restart, and it's available. No code change.

The difference from lesson 09: that lesson uses workflows to GATE tools
(hide what's irrelevant). This one uses them to SEQUENCE work (enforce an
order and keep state across calls). Both are real; they compose.

Run it directly to check it loads:
    uv run python workflow_mcp_server.py --list

Normally the agent launches it via .mcp.json:
    "workflow": { "command": "python", "args": ["workflow_mcp_server.py"] }
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated

import yaml
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

mcp = FastMCP(name="workflow")

WORKFLOW_DIR = Path(__file__).parent / "workflows"


# ============================================================================
# Loading workflow definitions
# ============================================================================

@dataclass
class WorkflowDef:
    name: str
    description: str
    steps: list[str]
    guidance: str  # the markdown body after the frontmatter


def _parse_workflow(path: Path) -> WorkflowDef | None:
    """Parse a markdown file with YAML frontmatter delimited by ---."""
    text = path.read_text(encoding="utf-8-sig")
    if not text.startswith("---"):
        return None
    # Split into: '', frontmatter, body
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None

    meta = yaml.safe_load(parts[1]) or {}
    steps = meta.get("steps") or []
    if not meta.get("name") or not steps:
        return None

    return WorkflowDef(
        name=meta["name"],
        description=meta.get("description", ""),
        steps=[str(s) for s in steps],
        guidance=parts[2].strip(),
    )


def workflow_files() -> list[Path]:
    """Every .md we'll look at: workflows/*.md, plus a single workflow.md
    next to this script if you'd rather keep one file at the root."""
    paths = sorted(WORKFLOW_DIR.glob("*.md")) if WORKFLOW_DIR.exists() else []
    root = Path(__file__).parent / "workflow.md"
    if root.exists():
        paths.append(root)
    return paths


def load_workflows() -> dict[str, WorkflowDef]:
    workflows = {}
    for path in workflow_files():
        wf = _parse_workflow(path)
        if wf:
            workflows[wf.name] = wf
    return workflows


WORKFLOWS = load_workflows()


# ============================================================================
# Run state -- this is what makes it a workflow and not just a document
# ============================================================================
# The server remembers where each run is. That's the whole mechanism: the
# agent can't skip ahead, because the server only ever hands it the
# current step.

@dataclass
class WorkflowRun:
    run_id: str
    workflow: str
    target: str
    index: int = 0                        # which step is current
    log: list[str] = field(default_factory=list)   # what the agent reported

    @property
    def done(self) -> bool:
        return self.index >= len(WORKFLOWS[self.workflow].steps)


RUNS: dict[str, WorkflowRun] = {}
_counter = 0


def _fill(text: str, target: str) -> str:
    return text.replace("<target>", target) if target else text


def _step_view(run: WorkflowRun) -> dict:
    wf = WORKFLOWS[run.workflow]
    total = len(wf.steps)
    if run.done:
        return {
            "run_id": run.run_id,
            "workflow": run.workflow,
            "status": "complete",
            "steps_completed": total,
            "log": run.log,
            "message": f"Workflow '{run.workflow}' complete ({total}/{total} steps).",
        }
    return {
        "run_id": run.run_id,
        "workflow": run.workflow,
        "status": "in_progress",
        "step_number": run.index + 1,
        "total_steps": total,
        "current_step": _fill(wf.steps[run.index], run.target),
        "next_action": "Do this step, then call complete_step with what you did.",
    }


# ============================================================================
# Tools
# ============================================================================

@mcp.tool
async def list_workflows() -> dict:
    """List the available workflows and what each one is for.

    Call this first if you are unsure which workflow fits the request.
    """
    return {
        "workflows": [
            {"name": wf.name, "description": wf.description, "steps": len(wf.steps)}
            for wf in WORKFLOWS.values()
        ]
    }


@mcp.tool
async def start_workflow(
    name: Annotated[str, Field(description="Workflow name, e.g. 'new-script'")],
    target: Annotated[str, Field(description="File the workflow acts on, e.g. 'fib.py'")] = "",
) -> dict:
    """Start a workflow and get its first step.

    Returns a run_id. Pass that run_id to complete_step as you finish each
    step. Follow the steps in the order given -- do not skip ahead.
    """
    global _counter
    if name not in WORKFLOWS:
        raise ToolError(
            f"Unknown workflow '{name}'. Available: {sorted(WORKFLOWS)}. "
            "Call list_workflows to see descriptions."
        )

    _counter += 1
    run = WorkflowRun(run_id=f"wf-{_counter}", workflow=name, target=target)
    RUNS[run.run_id] = run

    wf = WORKFLOWS[name]
    view = _step_view(run)
    view["description"] = wf.description
    if wf.guidance:
        view["guidance"] = _fill(wf.guidance, target)
    return view


@mcp.tool
async def complete_step(
    run_id: Annotated[str, Field(description="The run_id from start_workflow")],
    result: Annotated[str, Field(description="Briefly, what you actually did for this step")],
) -> dict:
    """Mark the current step done and receive the next one.

    Only call this after genuinely doing the step. If you could not do it,
    say so in `result` -- the record should reflect what happened.
    """
    run = RUNS.get(run_id)
    if run is None:
        raise ToolError(f"Unknown run_id '{run_id}'. Call start_workflow first.")
    if run.done:
        return _step_view(run)

    wf = WORKFLOWS[run.workflow]
    run.log.append(f"step {run.index + 1}/{len(wf.steps)}: {result}")
    run.index += 1
    return _step_view(run)


@mcp.tool
async def workflow_status(
    run_id: Annotated[str, Field(description="The run_id from start_workflow")],
) -> dict:
    """Check where a workflow run has got to, without advancing it."""
    run = RUNS.get(run_id)
    if run is None:
        raise ToolError(f"Unknown run_id '{run_id}'.")
    view = _step_view(run)
    view["log"] = run.log
    return view


if __name__ == "__main__":
    if "--list" in sys.argv:
        # Quick check that the .md files parse, without starting a server.
        if not WORKFLOWS:
            print(f"No workflows found in {WORKFLOW_DIR} (or ./workflow.md)")
            raise SystemExit(1)
        print(f"Loaded {len(WORKFLOWS)} workflow(s) from:")
        for p in workflow_files():
            print(f"    {p}")
        print()
        for wf in WORKFLOWS.values():
            print(f"  {wf.name} -- {wf.description}")
            for i, step in enumerate(wf.steps, 1):
                print(f"     {i}. {step}")
            print()
        raise SystemExit(0)

    mcp.run(show_banner=False)
