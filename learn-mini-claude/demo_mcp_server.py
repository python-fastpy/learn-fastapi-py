"""Demo MCP server -- something for your mini-Claude to attach to.

This is NOT a lesson. It's a tiny MCP server so `.mcp.json` points at
something real out of the box. It deliberately offers capabilities the
built-in file tools do NOT have (a persistent notes store), so when you
attach it in lesson 03 you can see genuinely new abilities appear in the
agent's tool list.

Run it directly to sanity-check it:
    uv run python demo_mcp_server.py
(It will sit waiting on stdin -- that's correct for a stdio MCP server.
 Press Ctrl+C. Normally the agent launches it for you.)

Built with FastMCP -- see learn-mcp lessons 01-06 for how this works.
"""

import json
from pathlib import Path
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP(name="notes")

NOTES_FILE = Path(__file__).parent / ".notes.json"


def _load() -> list[dict]:
    if NOTES_FILE.exists():
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    return []


def _save(notes: list[dict]) -> None:
    NOTES_FILE.write_text(json.dumps(notes, indent=2), encoding="utf-8")


@mcp.tool
async def save_note(
    text: Annotated[str, Field(description="The note text to save")],
    tag: Annotated[str, Field(description="A short tag to categorize the note")] = "general",
) -> dict:
    """Save a note to the persistent notes store."""
    notes = _load()
    note = {"id": len(notes) + 1, "text": text, "tag": tag}
    notes.append(note)
    _save(notes)
    return {"saved": note, "total_notes": len(notes)}


@mcp.tool
async def list_notes(
    tag: Annotated[str, Field(description="Filter by tag; empty means all notes")] = "",
) -> dict:
    """List saved notes, optionally filtered by tag."""
    notes = _load()
    if tag:
        notes = [n for n in notes if n["tag"] == tag]
    return {"count": len(notes), "notes": notes}


@mcp.tool
async def clear_notes() -> dict:
    """Delete all saved notes."""
    count = len(_load())
    _save([])
    return {"cleared": count}


if __name__ == "__main__":
    # stdio transport -- the agent launches this as a subprocess.
    # show_banner=False keeps FastMCP's startup art out of the parent's
    # terminal; with stdio the subprocess shares your console.
    mcp.run(show_banner=False)
