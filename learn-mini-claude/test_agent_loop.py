"""Tests for agent_core.agent_loop -- no LLM, no tokens, no credentials.

    uv run pytest test_agent_loop.py -v

Why this exists: test_workflow.py tests the workflow SERVER. Nothing
tested the loop itself -- the part every lesson, the CLI and the web UI
depend on. A model is non-deterministic, so you can't test the loop by
asking a real one to misbehave on cue. ScriptedModel (scripted_model.py)
misbehaves exactly when told to: calls a tool that doesn't exist, calls
one that raises, never stops calling tools.

Each test pins down one promise the README makes about the loop:
  - text ends the loop; tool calls continue it
  - every tool call gets a result with the matching tool_call_id
  - read-only tools never reach approve(); writes always do
  - a denial, an unknown tool, or a crashing tool is a RESULT, not a crash
  - max_turns stops a model that never finishes
  - usage counts every LLM call
  - safe_path() holds against `..`, absolute paths and prefix tricks

Run by file name: `uv run pytest` alone also collects test_workflow.py,
which is a script with its own runner, not a pytest suite.
"""

import asyncio
import json

import pytest
from langchain_core.messages import HumanMessage, ToolMessage

import agent_core
from agent_core import SandboxError, Tool, Usage, agent_loop, safe_path
from scripted_model import ScriptedModel, last_result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_tool(name: str, fn, read_only: bool = True) -> Tool:
    return Tool(name, f"test tool {name}", {"type": "object", "properties": {}},
                fn, read_only=read_only, source="test")


class Recorder:
    """Collects on_event calls and counts tool executions."""

    def __init__(self):
        self.events: list[tuple[str, object]] = []
        self.ran: list[str] = []

    def on_event(self, kind, data):
        self.events.append((kind, data))

    def kinds(self) -> list[str]:
        return [k for k, _ in self.events]

    def tool(self, name: str, result=None, read_only: bool = True) -> Tool:
        async def fn(**kwargs):
            self.ran.append(name)
            return result if result is not None else {"ok": name, "args": kwargs}
        return make_tool(name, fn, read_only)


def never_approve(tool, args):
    raise AssertionError(f"approve() should not be called for {tool.name}")


def run(model, registry, *, approve=never_approve, on_event=None, max_turns=12, usage=None):
    messages = [HumanMessage(content="test")]
    kwargs = {"approve": approve, "max_turns": max_turns, "usage": usage}
    if on_event:
        kwargs["on_event"] = on_event
    answer = asyncio.run(agent_loop(model, registry, messages, **kwargs))
    return answer, messages


def tool_messages(messages) -> list[ToolMessage]:
    return [m for m in messages if isinstance(m, ToolMessage)]


# ---------------------------------------------------------------------------
# The loop's basic contract
# ---------------------------------------------------------------------------

def test_text_reply_ends_the_loop():
    answer, messages = run(ScriptedModel(["hello"]), {})
    assert answer == "hello"
    assert len(messages) == 2  # the human message + one AI reply


def test_tool_result_goes_back_with_matching_id():
    rec = Recorder()
    seen = {}

    def check(msgs):
        seen["result"] = last_result(msgs)
        return "done"

    answer, messages = run(ScriptedModel([[("echo", {"x": 1})], check]),
                           {"echo": rec.tool("echo")})
    call_id = messages[1].tool_calls[0]["id"]
    [tm] = tool_messages(messages)
    assert tm.tool_call_id == call_id
    assert seen["result"] == {"ok": "echo", "args": {"x": 1}}  # the model saw it
    assert answer == "done"


def test_several_calls_in_one_reply_all_answered_in_order():
    rec = Recorder()
    registry = {n: rec.tool(n) for n in ("a", "b", "c")}
    _, messages = run(ScriptedModel([[("a", {}), ("b", {}), ("c", {})], "done"]), registry)
    ids = [c["id"] for c in messages[1].tool_calls]
    assert [tm.tool_call_id for tm in tool_messages(messages)] == ids
    assert rec.ran == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# The permission gate
# ---------------------------------------------------------------------------

def test_read_only_tools_skip_approve():
    rec = Recorder()
    run(ScriptedModel([[("look", {})], "done"]), {"look": rec.tool("look")},
        approve=never_approve)
    assert rec.ran == ["look"]


def test_write_tools_always_ask():
    rec = Recorder()
    asked = []

    def approve(tool, args):
        asked.append(tool.name)
        return True

    run(ScriptedModel([[("save", {})], "done"]),
        {"save": rec.tool("save", read_only=False)}, approve=approve)
    assert asked == ["save"]
    assert rec.ran == ["save"]


def test_denied_tool_is_not_run_and_the_model_is_told():
    rec = Recorder()
    _, messages = run(ScriptedModel([[("save", {})], "ok, I won't"]),
                      {"save": rec.tool("save", read_only=False)},
                      approve=lambda t, a: False, on_event=rec.on_event)
    assert rec.ran == []
    assert json.loads(tool_messages(messages)[0].content) == {"error": "permission denied by user"}
    assert "tool_denied" in rec.kinds()
    assert "tool_call" not in rec.kinds()


# ---------------------------------------------------------------------------
# Failures are results, not crashes
# ---------------------------------------------------------------------------

def test_unknown_tool_is_reported_and_the_loop_continues():
    answer, messages = run(ScriptedModel([[("nope", {})], "recovered"]), {})
    assert json.loads(tool_messages(messages)[0].content) == {"error": "unknown tool: nope"}
    assert answer == "recovered"


def test_tool_that_raises_becomes_an_error_result():
    async def boom(**kwargs):
        raise ValueError("disk on fire")

    answer, messages = run(ScriptedModel([[("boom", {})], "recovered"]),
                           {"boom": make_tool("boom", boom)})
    result = json.loads(tool_messages(messages)[0].content)
    assert result == {"error": "ValueError: disk on fire"}
    assert answer == "recovered"


def test_huge_result_is_truncated():
    rec = Recorder()
    big = rec.tool("big", result={"data": "x" * 50_000})
    _, messages = run(ScriptedModel([[("big", {})], "done"]), {"big": big})
    assert len(tool_messages(messages)[0].content) == 8000


# ---------------------------------------------------------------------------
# Limits and accounting
# ---------------------------------------------------------------------------

def test_max_turns_stops_a_model_that_never_finishes():
    rec = Recorder()
    forever = ScriptedModel([[("look", {})]] * 100)
    answer, _ = run(forever, {"look": rec.tool("look")}, max_turns=3)
    assert answer.startswith("Stopped")
    assert len(rec.ran) == 3


def test_usage_counts_every_llm_call():
    rec = Recorder()
    usage = Usage()
    run(ScriptedModel([[("look", {})], [("look", {})], "done"]),
        {"look": rec.tool("look")}, usage=usage)
    assert usage.llm_calls == 3
    assert usage.input_tokens > 0 and usage.output_tokens > 0


# ---------------------------------------------------------------------------
# The sandbox
# ---------------------------------------------------------------------------

@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    root = (tmp_path / "box").resolve()
    root.mkdir()
    monkeypatch.setattr(agent_core, "WORKDIR", root)
    return root


@pytest.mark.parametrize("path", [
    "../outside.txt",
    "sub/../../outside.txt",
    "/etc/passwd",
    "C:/Windows/win.ini",
])
def test_safe_path_rejects_escapes(sandbox, path):
    with pytest.raises(SandboxError):
        safe_path(path)


def test_safe_path_rejects_sibling_with_same_prefix(sandbox):
    # "box-evil" starts with "box" -- a string-prefix check would allow it.
    (sandbox.parent / "box-evil").mkdir()
    with pytest.raises(SandboxError):
        safe_path("../box-evil/x.txt")


def test_safe_path_allows_inside(sandbox):
    assert safe_path("a/b.txt") == sandbox / "a" / "b.txt"
    assert safe_path(".") == sandbox


def test_read_file_escape_is_an_error_result_not_an_exception(sandbox):
    result = asyncio.run(agent_core.read_file("../secret.txt"))
    assert "escapes the sandbox" in result["error"]
