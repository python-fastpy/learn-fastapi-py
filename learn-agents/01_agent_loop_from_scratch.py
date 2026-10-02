"""Lesson 01 -- The agent loop, built from scratch, no framework
====================================================================

An agent is: A MODEL that decides + TOOLS it can call + A LOOP that keeps
going until the model says it's done. That's the whole definition. Every
framework (LangGraph, the OpenAI/Claude Agent SDKs, CrewAI, ...) is some
version of this loop with extra features bolted on. This lesson builds the
loop itself, so nothing about it is hidden behind a framework.

    user message
         │
         ▼
    ┌─────────────────────── THE AGENT LOOP ───────────────────────┐
    │  while True:                                                 │
    │      decision = decide(messages, tools)   <- the ONE line a  │
    │                                               real model call │
    │                                               would replace   │
    │      if decision is FINAL ANSWER:                             │
    │          return it, stop looping                              │
    │      if decision is a TOOL CALL:                               │
    │          result = tools[decision.name](**decision.arguments) │
    │          messages.append(a message holding `result`)          │
    │          # loop again -- the model sees the result and        │
    │          # decides what happens next, informed by it          │
    └────────────────────────────────────────────────────────────────┘

`decide()` below is a deterministic stand-in for a real LLM call --
swapping in `anthropic.Anthropic().messages.create(messages=messages,
tools=tools)` is a one-line change exactly where `decide()` is called;
nothing else in the loop changes. Keeping it fake here means this lesson
needs no API key and produces the same output every run.

Run:  uv run python 01_agent_loop_from_scratch.py
"""

from dataclasses import dataclass

from tools import TOOLS


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class FinalAnswer:
    text: str


def decide(messages: list[dict], request: str) -> ToolCall | FinalAnswer:
    """Stands in for one real LLM call. Looks at what's happened so far and
    picks the next tool call, or decides it's done. A real model reads the
    full `messages` history and the tool SCHEMAS; this one just pattern-matches
    the original request against which tools have already run."""
    done_tools = [m["tool"] for m in messages if m.get("role") == "tool"]

    if "greet" in request and "greet" not in done_tools:
        name = request.split("greet", 1)[1].split(" in ")[0].strip().title()
        return ToolCall("greet", {"name": name})

    if " in " in request and "translate" not in done_tools and "greet" in done_tools:
        language_word = request.rsplit(" in ", 1)[1].strip().lower()
        lang_code = {"french": "fr", "german": "de", "spanish": "es"}.get(language_word, "en")
        greeting = next(m["result"] for m in messages if m.get("tool") == "greet")
        return ToolCall("translate", {"text": greeting, "language": lang_code})

    # nothing left to do -- answer with whatever the last tool produced
    last_result = messages[-1]["result"] if messages and messages[-1].get("role") == "tool" else request
    return FinalAnswer(last_result)


def run_agent(request: str) -> str:
    print(f"user: {request!r}")
    messages: list[dict] = [{"role": "user", "content": request}]

    while True:
        decision = decide(messages, request)

        if isinstance(decision, FinalAnswer):
            print(f"agent: final answer -> {decision.text!r}")
            return decision.text

        result = TOOLS[decision.name](**decision.arguments)
        print(f"agent: called {decision.name}({decision.arguments}) -> {result!r}")
        messages.append({"role": "tool", "tool": decision.name, "result": result})
        # loop again -- decide() will see this tool result in `messages` next time


if __name__ == "__main__":
    run_agent("greet Ada in French")

# Expected output:
#
# user: 'greet Ada in French'
# agent: called greet({'name': 'Ada'}) -> 'Hello, Ada!'
# agent: called translate({'text': 'Hello, Ada!', 'language': 'fr'}) -> 'Bonjour, Ada!'
# agent: final answer -> 'Bonjour, Ada!'
#
# Three iterations of the SAME while loop: two tool calls, then a final
# answer. Nothing paused or threaded -- decide() just looks at a growing
# `messages` list each time and returns a different decision because the
# list is different.
