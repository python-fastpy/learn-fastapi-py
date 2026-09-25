"""A scripted stand-in for a real chat model -- used by lessons 07-11 and
test_agent_loop.py so they run with zero credentials.

It implements the only two methods `agent_core.agent_loop()` calls --
`bind_tools()` and `ainvoke()` -- and returns real LangChain `AIMessage`s.
So the lessons drive the REAL loop; only the model's "decisions" are fake.
Same idea as lesson 01's MockModel, but plug-compatible with agent_core.

A script is a list of turns. Each turn is one of:

    "some text"                        -> final answer; the loop ends
    [("tool_name", {args}), ...]       -> tool calls, all in one reply
    callable(messages) -> one of above -> decide from what's happened so far

    model = ScriptedModel([
        [("read_file", {"path": "notes.txt"})],
        lambda msgs: f"The file says: {last_result(msgs)['content']}",
    ])

Pass several scripts for a multi-message conversation -- the Nth script
answers the Nth user message:

    model = ScriptedModel(first_message_script, follow_up_script)

The position in the script is derived from the conversation itself (which
user message this is, and how many replies since it), not from a counter.
That makes one instance safe to share across conversations running at the
same time -- lesson 11's subagents rely on it.

Token counts are FAKE: roughly chars / 4, for the whole conversation plus
the tool specs, the way a real provider bills it. Good enough to compare
two approaches; not a real number.
"""

import copy
import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


class ScriptedModel:
    def __init__(self, *scripts: list):
        if not scripts:
            raise ValueError("ScriptedModel needs at least one script")
        self.scripts = scripts
        self.tool_specs: list[dict] = []

    def bind_tools(self, tools: list[dict]) -> "ScriptedModel":
        # Return a copy, like LangChain does -- binding must not mutate a
        # model that another conversation is also using.
        bound = copy.copy(self)
        bound.tool_specs = tools
        return bound

    async def ainvoke(self, messages: list) -> AIMessage:
        script_no, turn = _position(messages)
        script = self.scripts[min(script_no, len(self.scripts) - 1)]
        step: Any = script[turn] if turn < len(script) else "(end of script)"
        if callable(step):
            step = step(messages)

        usage = self._fake_usage(messages, step)
        if isinstance(step, str):
            return AIMessage(content=step, usage_metadata=usage)
        calls = [
            {"name": name, "args": args, "id": f"call_{script_no}_{turn}_{i}", "type": "tool_call"}
            for i, (name, args) in enumerate(step)
        ]
        return AIMessage(content="", tool_calls=calls, usage_metadata=usage)

    def _fake_usage(self, messages: list, step: Any) -> dict:
        sent = sum(len(str(m.content)) for m in messages) + len(json.dumps(self.tool_specs))
        inp, out = sent // 4, max(1, len(str(step)) // 4)
        return {"input_tokens": inp, "output_tokens": out, "total_tokens": inp + out}


def _position(messages: list) -> tuple[int, int]:
    """(which user message we're answering, how many replies since it)."""
    humans = sum(1 for m in messages if isinstance(m, HumanMessage))
    replies = 0
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            break
        if isinstance(m, AIMessage):
            replies += 1
    return max(0, humans - 1), replies


# ---------------------------------------------------------------------------
# Helpers for script callables
# ---------------------------------------------------------------------------

def tool_results(messages: list) -> list[Any]:
    """Every tool result since the last model reply, parsed from JSON."""
    out = []
    for m in reversed(messages):
        if not isinstance(m, ToolMessage):
            break
        try:
            out.append(json.loads(m.content))
        except json.JSONDecodeError:
            out.append(m.content)
    return list(reversed(out))


def last_result(messages: list) -> Any:
    """The most recent tool result, parsed from JSON."""
    results = tool_results(messages)
    return results[-1] if results else None


def user_prompt(messages: list) -> str:
    """The text of the most recent user message."""
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            return str(m.content)
    return ""
