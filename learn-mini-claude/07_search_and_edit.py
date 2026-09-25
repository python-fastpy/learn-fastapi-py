"""Lesson 07 -- Search and Edit: tools that save tokens
========================================================

WHY THIS MATTERS:
  With only lesson 02's tools, the agent finds code the expensive way:
  list a directory, read every file, then rewrite a whole file to change
  one line. Every byte it reads goes into the conversation -- and every
  later turn RESENDS the conversation. Reading five files to change one
  number means paying for those five files on every turn that follows.

  Claude Code's answer is three tools: Glob (find files by name), Grep
  (find lines by content), and Edit (replace one exact string). Together
  they turn "read everything, rewrite everything" into "find the line,
  change the line".

WHAT YOU'LL LEARN:
  1. glob_files / grep / edit_file, built on lesson 02's sandbox
  2. Why edit_file refuses an `old` string that matches 0 or 2+ times --
     an ambiguous replace is how agents silently corrupt files
  3. That the refusal is a normal tool result: the model retries with
     more context, same as a denied permission (lesson 01's recovery)
  4. A sandbox gap specific to search: `Path.glob("../*")` happily walks
     OUT of the directory, so every match must be resolved and checked
  5. Measuring the difference: same task, two tool sets, token counts

Concepts:
  - Glob: pattern over file NAMES ("**/*.py")
  - Grep: regex over file CONTENTS -> "path:line: text"
  - Exact-match edit: old must appear exactly once, or nothing changes
  - Result caps: search output is capped (200 matches) because a search
    that returns the whole repo is just a slower read_file

Flow:
  task: "change the database timeout from 30 to 60"

  WITHOUT search               WITH search
  --------------               -----------
  list_files                   grep("DB_TIMEOUT")  -> config.py:4, db.py:6
  read_file x5  (everything)   edit_file("= 30" -> "= 60")
  write_file (whole file)        -> ERROR: appears 2 times
                                 (model adds context and retries)
                               edit_file("DB_TIMEOUT = 30" -> "... = 60")

  Maps to:
    Claude Code's Glob, Grep and Edit tools. Its Edit has the same
    exactly-once rule and the same "add more context" error.

PREREQUISITES: Lessons 01-02. Runs with no credentials (scripted model).

Run:  uv run python 07_search_and_edit.py

EXPECTED OUTPUT (abridged):
  === The sandbox hole in Path.glob ===
    WORKDIR.glob('../*.toml')      -> ['pyproject.toml']   <- outside the sandbox!
    glob_files('../*.toml')        -> []

  === Run A: lesson 02 tools only ===
    * list_files  {'subdir': 'search_demo/app'}
    * read_file  {'path': 'search_demo/app/api.py'}
    ...                                    (all five files)
    * write_file  {'path': 'search_demo/app/config.py', 'content': ...}
    4 LLM calls, ~7,180 tokens (estimated)

  === Run B: with glob / grep / edit_file ===
    * grep  {'pattern': 'DB_TIMEOUT', 'glob': 'search_demo/**/*.py'}
    * edit_file  {'path': ..., 'old': '= 30', 'new': '= 60'}
      -> {'error': "'old' text appears 2 times in ... -- include more
                    surrounding lines so it matches exactly once"}
    * edit_file  {'path': ..., 'old': 'DB_TIMEOUT = 30', 'new': 'DB_TIMEOUT = 60'}
    4 LLM calls, ~4,170 tokens (estimated)

  Run B used ~42% fewer tokens for the same change.

  (Run B's saving is net of its three extra tool specs, which are resent
  on every call too. On a real project with more and bigger files, the
  gap is far wider -- Run A's cost grows with the repo, Run B's doesn't.)
"""

import asyncio
import re
import textwrap

from langchain_core.messages import HumanMessage, SystemMessage

from agent_core import (
    WORKDIR, SandboxError, Tool, Usage, agent_loop, build_system_prompt,
    builtin_tools, safe_path,
)
from scripted_model import ScriptedModel, last_result, tool_results

DEMO_DIR = WORKDIR / "search_demo" / "app"


# ============================================================================
# STEP 1: Finding files -- and the sandbox hole in Path.glob
# ============================================================================
# Lesson 02's safe_path() checks ONE path the model gave you. A glob is
# different: the model gives you a pattern and the filesystem gives you
# the paths. `WORKDIR.glob("../*.toml")` returns files OUTSIDE WORKDIR --
# pathlib doesn't consider that its problem. So every match is resolved
# and checked, exactly like safe_path does for a single path.

SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
MAX_RESULTS = 200


def _iter_files(pattern: str):
    """Files under WORKDIR matching `pattern`, sandbox-checked."""
    for p in sorted(WORKDIR.glob(pattern)):
        resolved = p.resolve()
        if WORKDIR not in resolved.parents:
            continue  # "../x" or a symlink pointing out -- drop it silently
        if not p.is_file() or SKIP_DIRS & set(resolved.relative_to(WORKDIR).parts):
            continue
        yield resolved


async def glob_files(pattern: str) -> dict:
    """Find files by name pattern."""
    try:
        paths = [p.relative_to(WORKDIR).as_posix() for p in _iter_files(pattern)]
    except (ValueError, NotImplementedError) as e:  # e.g. an absolute pattern
        return {"error": f"bad pattern {pattern!r}: {e}"}
    return {"files": paths[:MAX_RESULTS], "count": len(paths),
            "truncated": len(paths) > MAX_RESULTS}


# ============================================================================
# STEP 2: Searching contents
# ============================================================================
# The output format is the design: "path:line: text". It's compact, and
# it tells the model exactly where to look next -- so it can go straight
# to edit_file without reading the file at all.

async def grep(pattern: str, glob: str = "**/*", ignore_case: bool = False) -> dict:
    """Search file contents with a regular expression."""
    try:
        rx = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
    except re.error as e:
        return {"error": f"bad regex {pattern!r}: {e}"}  # model can fix its regex
    matches: list[str] = []
    try:
        for p in _iter_files(glob):
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue  # binary or unreadable -- skip, don't fail the search
            rel = p.relative_to(WORKDIR).as_posix()
            for lineno, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    matches.append(f"{rel}:{lineno}: {line.strip()[:200]}")
                    if len(matches) >= MAX_RESULTS:
                        return {"matches": matches, "count": len(matches), "truncated": True}
    except (ValueError, NotImplementedError) as e:
        return {"error": f"bad glob {glob!r}: {e}"}
    return {"matches": matches, "count": len(matches), "truncated": False}


# ============================================================================
# STEP 3: Editing -- exactly once, or not at all
# ============================================================================
# write_file makes the model reproduce the WHOLE file to change one line:
# expensive, and every line it retypes is a chance to drop or mangle one.
# edit_file sends only the changed text. The exactly-once rule is what
# makes it safe: "replace '30' with '60'" in a file with two 30s would
# otherwise change a line nobody asked about.

async def edit_file(path: str, old: str, new: str) -> dict:
    """Replace one exact piece of text in a file."""
    try:
        target = safe_path(path)
        text = target.read_text(encoding="utf-8")
    except SandboxError as e:
        return {"error": str(e)}
    except FileNotFoundError:
        return {"error": f"no such file: {path}"}
    if not old:
        return {"error": "'old' must not be empty -- use write_file to create a file"}
    count = text.count(old)
    if count == 0:
        return {"error": f"'old' text not found in {path} -- read the file and copy it exactly"}
    if count > 1:
        return {"error": f"'old' text appears {count} times in {path} -- "
                         "include more surrounding lines so it matches exactly once"}
    target.write_text(text.replace(old, new, 1), encoding="utf-8")
    return {"edited": path, "removed_chars": len(old), "added_chars": len(new)}


def search_tools() -> dict[str, Tool]:
    """The three new tools, in the same Tool shape as everything else --
    so agent_core.agent_loop() runs them unchanged."""
    def obj(props, required):
        return {"type": "object", "properties": props, "required": required}

    return {
        "glob_files": Tool(
            "glob_files",
            "Find files by name pattern, e.g. '**/*.py'. Use this instead of "
            "listing directories one at a time.",
            obj({"pattern": {"type": "string", "description": "Glob relative to the working directory"}},
                ["pattern"]),
            glob_files, read_only=True, source="builtin"),
        "grep": Tool(
            "grep",
            "Search file contents with a regular expression. Returns 'path:line: text' "
            "for each match. Use this to find where something is defined or used "
            "instead of reading every file.",
            obj({"pattern": {"type": "string", "description": "Python regular expression"},
                 "glob": {"type": "string", "description": "Only search files matching this glob"},
                 "ignore_case": {"type": "boolean", "description": "Case-insensitive match"}},
                ["pattern"]),
            grep, read_only=True, source="builtin"),
        "edit_file": Tool(
            "edit_file",
            "Replace one exact piece of text in a file. `old` must appear exactly "
            "once -- include surrounding lines if needed. Prefer this over "
            "write_file for changes to an existing file.",
            obj({"path": {"type": "string", "description": "Relative file path"},
                 "old": {"type": "string", "description": "Exact text to replace, copied from the file"},
                 "new": {"type": "string", "description": "Replacement text"}},
                ["path", "old", "new"]),
            edit_file, read_only=False, source="builtin"),
    }


# ============================================================================
# Demo setup: a small project with one setting to change
# ============================================================================

def _filler(module: str, n: int) -> str:
    """Realistic-looking bulk, so reading a file costs what it would."""
    return "\n".join(textwrap.dedent(f'''
        def {module}_step_{i}(record: dict) -> dict:
            """Normalise field {i} of a {module} record before saving it."""
            value = record.get("field_{i}")
            if value is None:
                return record
            record["field_{i}"] = str(value).strip().lower()
            return record
        ''') for i in range(n))


def make_demo_project() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    files = {
        "config.py": '"""Settings for the app."""\n\nLOG_LEVEL = "INFO"\n'
                     'DB_TIMEOUT = 30\nRETRY_DELAY = 30\nMAX_RETRIES = 3\n',
        "db.py": '"""Database access."""\n\nfrom . import config\n\n\ndef connect(url):\n'
                 '    return open_connection(url, timeout=config.DB_TIMEOUT)\n' + _filler("db", 6),
        "api.py": '"""HTTP handlers."""\n' + _filler("api", 10),
        "emails.py": '"""Outgoing email."""\n' + _filler("email", 8),
        "reports.py": '"""Nightly reports."""\n' + _filler("report", 8),
    }
    for name, body in files.items():
        (DEMO_DIR / name).write_text(body, encoding="utf-8")


def on_event(kind: str, data) -> None:
    if kind == "tool_call":
        args = {k: (v if len(str(v)) < 40 else str(v)[:37] + "...") for k, v in data["args"].items()}
        print(f"    * {data['name']}  {args}")
    elif kind == "tool_result" and isinstance(data["result"], dict) and "error" in data["result"]:
        print(f"      -> {data['result']}")


def auto_approve(tool: Tool, args: dict) -> bool:
    return True  # scripted demo in the sandbox -- lesson 04 asks for real


# ============================================================================
# The two scripted runs
# ============================================================================
# Both scripts do what a real model plausibly does with each tool set.
# The loop is agent_core.agent_loop -- unchanged from lesson 04.

TASK = "Change the database timeout in search_demo/app from 30 to 60 seconds."
APP = "search_demo/app"


def _rewrite_config(messages):
    """Run A's model: find config.py among everything it read, retype it."""
    config = next(r["content"] for r in tool_results(messages) if "DB_TIMEOUT = 30" in r.get("content", ""))
    return [("write_file", {"path": f"{APP}/config.py",
                            "content": config.replace("DB_TIMEOUT = 30", "DB_TIMEOUT = 60")})]


RUN_A = [
    [("list_files", {"subdir": APP})],
    lambda msgs: [("read_file", {"path": f"{APP}/{name}"}) for name in last_result(msgs)["files"]],
    _rewrite_config,
    "Changed DB_TIMEOUT from 30 to 60 in search_demo/app/config.py.",
]

RUN_B = [
    [("grep", {"pattern": "DB_TIMEOUT", "glob": "search_demo/**/*.py"})],
    # First attempt is too short -- RETRY_DELAY is also 30.
    [("edit_file", {"path": f"{APP}/config.py", "old": "= 30", "new": "= 60"})],
    [("edit_file", {"path": f"{APP}/config.py", "old": "DB_TIMEOUT = 30", "new": "DB_TIMEOUT = 60"})],
    "Changed DB_TIMEOUT from 30 to 60 in search_demo/app/config.py (db.py reads it from there).",
]


async def run(label: str, registry: dict[str, Tool], script: list) -> Usage:
    make_demo_project()  # both runs start from the same files
    print(f"=== {label} ===")
    usage = Usage()
    messages = [SystemMessage(content=build_system_prompt()), HumanMessage(content=TASK)]
    answer = await agent_loop(ScriptedModel(script), registry, messages,
                              approve=auto_approve, on_event=on_event, usage=usage)
    print(f"    answer: {answer}")
    print(f"    {usage.llm_calls} LLM calls, ~{usage.total_tokens:,} tokens (estimated)")
    line = next(l for l in (DEMO_DIR / "config.py").read_text().splitlines() if "DB_TIMEOUT" in l)
    print(f"    config.py now says: {line}")
    print()
    return usage


async def main():
    WORKDIR.mkdir(exist_ok=True)

    print("=== The sandbox hole in Path.glob ===")
    naive = [p.name for p in WORKDIR.glob("../*.toml")]
    print(f"    WORKDIR.glob('../*.toml')      -> {naive}   <- outside the sandbox!")
    print(f"    glob_files('../*.toml')        -> {(await glob_files('../*.toml'))['files']}")
    print()

    a = await run("Run A: lesson 02 tools only", builtin_tools(), RUN_A)
    b = await run("Run B: with glob / grep / edit_file", {**builtin_tools(), **search_tools()}, RUN_B)

    saved = 1 - b.total_tokens / a.total_tokens
    print(f"  Run B used ~{saved:.0%} fewer tokens for the same change.")
    print("  And it never read api.py, emails.py or reports.py at all.")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Tool DESIGN is a cost lever, not just a capability one. Run A and
    # Run B made the same change with the same number of LLM calls; the
    # difference is how much text each tool put into the conversation --
    # and every later turn pays for that text again.
    #
    #   - grep returns "path:line: text", not files. Point, don't dump.
    #   - edit_file sends a diff, not a file. Less to pay for, less to mangle.
    #   - Both refuse ambiguity and say why, so the model can retry. The
    #     "appears 2 times" error above is the tool doing its job.
    #
    # And a search tool is a new sandbox surface: the model controls the
    # pattern, the filesystem picks the paths. Check every path that comes
    # back, not just the one that went in.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a `context` argument to grep that returns N lines around each
    #    match (Claude Code's Grep has -A/-B/-C). When does that beat a
    #    read_file?
    # 2. Make edit_file refuse unless the file was read_file'd earlier in
    #    this session (Claude Code does). Hint: the tool needs to see
    #    `messages`, or keep a set of read paths.
    # 3. Add `replace_all: bool` to edit_file for renames. What guardrail
    #    stops it rewriting 400 matches by accident?
    # 4. Add these tools to agent_core.builtin_tools() and try Run B's task
    #    in the lesson 04 CLI with a real model. Does it choose grep on its
    #    own? What does the tool description need to say for it to?
