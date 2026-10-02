"""Lesson 06 -- ReAct vs. Plan-and-Execute: when does the plan get decided?
==============================================================================

Lesson 01's loop IS a planning strategy, with a name: ReAct (Reason, Act,
observe, repeat). Decide ONE step, look at what it returned, let THAT
inform the next decision. Plan-and-Execute decides differently: produce
the WHOLE sequence of steps up front, then just run them -- only each
step's concrete ARGUMENTS get filled in as you go (from earlier steps'
results), not the sequence itself.

    REACT (lesson 01's shape)              PLAN-AND-EXECUTE
    decide step 1 -> observe               decide the FULL step sequence
    decide step 2 (informed by step 1)     execute step 1 -> fill in $step1
    decide step 3 (informed by step 2)     execute step 2 -> fill in $step2
    ...                                     execute step 3, using $step1/$step2
                                             (the SEQUENCE was fixed before
                                              any step ran)

    one model decision per step             one planning decision, total --
    (costs more, adapts better)             cheaper, but locked in early

THE CONCRETE TRADE-OFF, below: both approaches greet someone and translate
the greeting into their preferred language (looked up first). For Ada
(a known preference), both produce the same result. For Bob (unknown
preference), ReAct NOTICES the lookup came back empty and skips the
pointless translate step. Plan-and-Execute can't -- its 3-step plan was
already fixed before the lookup ever ran, so it runs all three regardless.

Run:  uv run python 06_planning_strategies.py
"""

from dataclasses import dataclass

from tools import greet, translate

PREFERENCES = {"Ada": "fr"}   # Bob is deliberately absent


# =================================================================== ReAct
@dataclass
class ToolCall:
    name: str
    arguments: dict


@dataclass
class FinalAnswer:
    text: str


def react_run(who: str) -> str:
    print(f"  [ReAct] greeting {who}")
    language = PREFERENCES.get(who)
    print(f"  [ReAct] lookup -> {language!r}")

    greeting = greet(who)
    print(f"  [ReAct] greet -> {greeting!r}")

    if language is None:
        print("  [ReAct] no preference found -- ADAPTING: skipping translate entirely")
        return greeting

    result = translate(greeting, language)
    print(f"  [ReAct] translate -> {result!r}")
    return result


# ========================================================= Plan-and-Execute
@dataclass
class Step:
    tool: str
    arguments: dict   # values may be literals, OR "$stepN" references to resolve later


TOOLS = {"lookup_preference": lambda who: PREFERENCES.get(who), "greet": greet, "translate": translate}


def make_plan(who: str) -> list[Step]:
    """Decided ONCE, before anything runs. Always 3 steps -- the plan
    cannot see what lookup_preference will return."""
    return [
        Step("lookup_preference", {"who": who}),
        Step("greet", {"name": who}),
        Step("translate", {"text": "$step2", "language": "$step1"}),
    ]


def plan_and_execute_run(who: str) -> str:
    plan = make_plan(who)
    print(f"  [Plan-and-Execute] fixed plan: {[s.tool for s in plan]}")
    results: dict[int, object] = {}

    for i, step in enumerate(plan, start=1):
        resolved_args = {
            k: (results[int(v[5:])] if isinstance(v, str) and v.startswith("$step") else v)
            for k, v in step.arguments.items()
        }
        results[i] = TOOLS[step.tool](**resolved_args)
        print(f"  [Plan-and-Execute] step {i} {step.tool}{resolved_args} -> {results[i]!r}")

    return results[len(plan)]


if __name__ == "__main__":
    print("=== Ada (a known preference) ===")
    print("ReAct            ->", react_run("Ada"))
    print("Plan-and-Execute ->", plan_and_execute_run("Ada"))

    print("\n=== Bob (no stored preference) ===")
    print("ReAct            ->", react_run("Bob"))
    print("Plan-and-Execute ->", plan_and_execute_run("Bob"))

# Expected output:
#
# === Ada (a known preference) ===
#   [ReAct] greeting Ada
#   [ReAct] lookup -> 'fr'
#   [ReAct] greet -> 'Hello, Ada!'
#   [ReAct] translate -> 'Bonjour, Ada!'
# ReAct            -> Bonjour, Ada!
#   [Plan-and-Execute] fixed plan: ['lookup_preference', 'greet', 'translate']
#   [Plan-and-Execute] step 1 lookup_preference{'who': 'Ada'} -> 'fr'
#   [Plan-and-Execute] step 2 greet{'name': 'Ada'} -> 'Hello, Ada!'
#   [Plan-and-Execute] step 3 translate{'text': 'Hello, Ada!', 'language': 'fr'} -> 'Bonjour, Ada!'
# Plan-and-Execute -> Bonjour, Ada!
#
# === Bob (no stored preference) ===
#   [ReAct] greeting Bob
#   [ReAct] lookup -> None
#   [ReAct] greet -> 'Hello, Bob!'
#   [ReAct] no preference found -- ADAPTING: skipping translate entirely
# ReAct            -> Hello, Bob!
#   [Plan-and-Execute] fixed plan: ['lookup_preference', 'greet', 'translate']
#   [Plan-and-Execute] step 1 lookup_preference{'who': 'Bob'} -> None
#   [Plan-and-Execute] step 2 greet{'name': 'Bob'} -> 'Hello, Bob!'
#   [Plan-and-Execute] step 3 translate{'text': 'Hello, Bob!', 'language': None} -> 'Hello, Bob!'
# Plan-and-Execute -> Hello, Bob!
#
# Same final text for Bob either way here (translate() defaults to English
# for an unknown language) -- but Plan-and-Execute still RAN step 3
# pointlessly, because its plan was committed before step 1's result
# existed. ReAct saw that result and skipped the step outright.
