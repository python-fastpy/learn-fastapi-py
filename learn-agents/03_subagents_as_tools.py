"""Lesson 03 -- Subagents: a whole agent, exposed as ONE tool
=================================================================

A SUBAGENT is a complete agent -- its own loop, its own tools, its own
decisions -- exposed to a PARENT agent as if it were a single callable
tool. The parent never sees what happened inside; it only sees the
subagent's final answer, exactly the way lesson 01's agent never saw
what happened inside `translate()` itself.

    SupervisorAgent                          TranslatorSubAgent
    (its own loop, lesson 01's shape)         (its OWN loop, OWN tools)
         │
         │  treats "translator" as if it           │
         │  were one ordinary tool ────────────────►│  runs its OWN decide()/tool
         │                                            │  loop internally -- could
         │                                            │  take 1 step or 5, the
         │                                            │  supervisor has no idea
         │◄───────────────────────────────────────────┤  returns ONLY the final
         │  (never sees the subagent's                   answer
         │   internal tool calls)

Why bother, instead of just importing `translate()` directly (lesson 01
did exactly that)? A subagent can make its OWN multi-step decisions --
here it decides WHICH language code a word like "french" maps to, and
could just as easily decide to look something up first. The parent
doesn't need to know any of that logic exists; it only needs to know
"ask the translator, get text back."

Run:  uv run python 03_subagents_as_tools.py
"""

from dataclasses import dataclass

from tools import greet, translate

LANGUAGE_WORDS = {"french": "fr", "german": "de", "spanish": "es", "english": "en"}


@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class FinalAnswer:
    text: str


class TranslatorSubAgent:
    """A complete, tiny agent. Its `run()` method is the ONLY thing the
    outside world ever calls -- everything else here is private to it."""

    name = "translator"

    def run(self, request: str) -> str:
        print(f"    [translator subagent] got request: {request!r}")
        text, language_word = request.rsplit(" into ", 1)
        language = LANGUAGE_WORDS.get(language_word.strip().lower(), "en")

        # its OWN tiny loop -- one step today, but it COULD take several
        decision = ToolCall("translate", {"text": text, "language": language})
        result = translate(**decision.arguments)
        print(f"    [translator subagent] internally called translate{decision.arguments} -> {result!r}")

        answer = FinalAnswer(result)
        print(f"    [translator subagent] returning -> {answer.text!r}")
        return answer.text


class SupervisorAgent:
    """The parent. `translator_subagent.run` sits in its tool catalog next
    to a PLAIN function (`greet`) -- from here, they look identical."""

    def __init__(self, translator_subagent: TranslatorSubAgent):
        self.tools = {"greet": greet, "translator": translator_subagent.run}

    def decide(self, messages: list[dict], request: str) -> ToolCall | FinalAnswer:
        done = [m["tool"] for m in messages if m.get("role") == "tool"]
        if "greet" not in done:
            name = request.split("greet", 1)[1].split(" and ", 1)[0].strip().title()
            return ToolCall("greet", {"name": name})
        if "translator" not in done:
            greeting = next(m["result"] for m in messages if m["tool"] == "greet")
            language_word = request.rsplit(" in ", 1)[1].strip()
            return ToolCall("translator", {"request": f"{greeting} into {language_word}"})
        return FinalAnswer(next(m["result"] for m in messages if m["tool"] == "translator"))

    def run(self, request: str) -> str:
        print(f"[supervisor] user: {request!r}")
        messages: list[dict] = []
        while True:
            decision = self.decide(messages, request)
            if isinstance(decision, FinalAnswer):
                print(f"[supervisor] final answer -> {decision.text!r}")
                return decision.text
            result = self.tools[decision.name](**decision.arguments)
            print(f"[supervisor] called {decision.name!r} -> {result!r}  (opaque -- just a tool to the supervisor)")
            messages.append({"role": "tool", "tool": decision.name, "result": result})


if __name__ == "__main__":
    supervisor = SupervisorAgent(TranslatorSubAgent())
    supervisor.run("greet Ada and say hello in french")

# Expected output:
#
# [supervisor] user: 'greet Ada and say hello in french'
# [supervisor] called 'greet' -> 'Hello, Ada!'  (opaque -- just a tool to the supervisor)
#     [translator subagent] got request: 'Hello, Ada! into french'
#     [translator subagent] internally called translate{'text': 'Hello, Ada!', 'language': 'fr'} -> 'Bonjour, Ada!'
#     [translator subagent] returning -> 'Bonjour, Ada!'
# [supervisor] called 'translator' -> 'Bonjour, Ada!'  (opaque -- just a tool to the supervisor)
# [supervisor] final answer -> 'Bonjour, Ada!'
#
# The indented [translator subagent] lines are its OWN internal loop --
# from the [supervisor] lines' point of view, calling "translator" looks
# exactly like calling "greet". That identical shape IS agent-as-tool.
