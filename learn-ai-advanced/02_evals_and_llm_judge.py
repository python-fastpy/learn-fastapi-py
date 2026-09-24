"""Lesson 02 -- Evals: Golden Datasets, LLM-as-Judge, Regression Detection
============================================================================

WHY THIS MATTERS:
  Every other lesson in this repo tests *code paths* (does the tool get
  called, does the graph reach the right node). None of them test *answer
  quality* -- whether the LLM's actual output is correct. You can't
  `assert response == expected` on free-text output; wording varies every
  run even when the meaning is right. Evals are how you test quality
  anyway: a fixed set of question/expected-answer pairs (a "golden
  dataset"), a scoring method that tolerates wording differences, and a
  way to compare two versions of your system to catch regressions before
  users do.

  This is the generalized version of a pattern already used in this
  codebase: a quote-fidelity checker that verifies an LLM's draft against
  a source text isn't fundamentally different from an eval that verifies
  an LLM's answer against an expected answer. Same shape, different data.

WHAT YOU'LL LEARN:
  1. Golden datasets: a fixed set of (question, expected answer) pairs you
     re-run every time the prompt, model, or pipeline changes
  2. Why exact-match scoring fails on free text, and what keyword/fact
     coverage scoring gets you instead
  3. LLM-as-judge: using a second LLM call to grade "does this answer
     convey the same facts as the expected answer," with structured
     (Pydantic) output instead of free-text grading
  4. Regression detection: running the same dataset against two versions
     of a system and diffing the results
  5. Where this fits with lesson 01 (RAG): eval the answers a RAG pipeline
     produces, not just whether retrieval ran

Concepts:
  - Golden dataset: versioned, fixed test cases -- the eval equivalent of
    a unit test suite, except the assertions are about meaning, not values
  - Keyword/fact coverage: does the answer contain the required facts,
    regardless of exact phrasing -- cheap, deterministic, but brittle to
    paraphrasing ("15 percent" vs "15%")
  - LLM-as-judge: an LLM call whose only job is grading another LLM's
    output against an expected answer -- catches paraphrases keyword
    matching misses, at the cost of being probabilistic itself
  - Structured judge output: forcing the judge to return a typed verdict
    (score, pass/fail, reasoning) instead of free text you'd have to parse
  - Regression: same dataset, two system versions, different pass rate --
    tells you a prompt/model/pipeline change broke something specific

Flow:
  Golden Dataset                System Under Test (SUT)
  [{q, expected, facts}]              |
        |                             v
        |                    answer = sut.run(q)
        |                             |
        +--------------+--------------+
                       v
              +-------------------+
              | Scorer            |
              |  1. Keyword/fact  |  <- cheap, deterministic, first pass
              |     coverage      |
              |  2. LLM judge     |  <- catches paraphrases, costs a call
              |     (structured   |
              |      Verdict)     |
              +---------+---------+
                        v
              +-------------------+
              | Report            |
              |  pass rate,       |
              |  failing q_ids,   |
              |  per-question     |
              |  verdicts         |
              +---------+---------+
                        v
        Run again after a prompt/model change --
        diff against the previous report -> regression caught

  Maps to (production shape, not this repo's code):
    A quote-fidelity check (verify LLM draft against source text) is a
    one-question eval running at request time instead of a dataset
    running at test time -- same "compare output against ground truth"
    shape, different trigger.

PREREQUISITES: None (pure Python + optional .env for a real LLM judge)

Run:  uv run python 02_evals_and_llm_judge.py

EXPECTED OUTPUT (mock mode -- no .env needed):
  === Golden dataset ===
    3 questions loaded

  === Running SUT v1 (correct) against the dataset ===
    [q1] PASS -- keyword coverage 1/1
    [q2] PASS -- keyword coverage 1/1
    [q3] PASS -- keyword coverage 1/1
    Pass rate: 3/3 (100%)

  === Running SUT v2 (regressed -- drops key facts) against the dataset ===
    [q1] FAIL -- missing: '15%'
    [q2] PASS -- keyword coverage 1/1
    [q3] FAIL -- missing: '4%'
    Pass rate: 1/3 (33%)

  === Regression report: v1 -> v2 ===
    REGRESSED: q1 (was PASS, now FAIL)
    REGRESSED: q3 (was PASS, now FAIL)
    2 regression(s) found -- do not ship v2
"""

import asyncio
import os
from dataclasses import dataclass

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


# ============================================================================
# STEP 1: The golden dataset
# ============================================================================
# Each case has an expected answer (for an LLM judge to compare against)
# AND a list of required facts (for cheap keyword-coverage scoring).
# Keeping both lets you run the cheap check on every commit and save the
# LLM judge for cases the cheap check can't resolve confidently.

@dataclass
class EvalCase:
    id: str
    question: str
    expected_answer: str
    required_facts: list[str]  # substrings the answer must contain


GOLDEN_DATASET = [
    EvalCase(
        id="q1",
        question="What was Q2 revenue growth?",
        expected_answer="Revenue grew 15% year over year in Q2.",
        required_facts=["15%"],
    ),
    EvalCase(
        id="q2",
        question="What was the operating margin in Q2?",
        expected_answer="Operating margin improved to 22%.",
        required_facts=["22%"],
    ),
    EvalCase(
        id="q3",
        question="What is the customer churn rate?",
        expected_answer="Customer churn remained flat at 4%.",
        required_facts=["4%"],
    ),
]


# ============================================================================
# STEP 2: Two versions of a "system under test" (SUT)
# ============================================================================
# v1 answers correctly. v2 simulates a regression -- e.g. someone edited
# the system prompt and it now drops specific numbers in favor of vague
# language. In production these would be two prompt/model versions; here
# they're hardcoded so the lesson is deterministic without an LLM call.

def sut_v1(question: str) -> str:
    answers = {
        "What was Q2 revenue growth?": "Revenue grew 15% year over year in Q2.",
        "What was the operating margin in Q2?": "Operating margin improved to 22% in Q2.",
        "What is the customer churn rate?": "Customer churn remained flat at 4%.",
    }
    return answers.get(question, "I don't know.")


def sut_v2_regressed(question: str) -> str:
    """Simulates a regression: the numbers got dropped in favor of vague
    filler -- the kind of thing a prompt edit can silently introduce."""
    answers = {
        "What was Q2 revenue growth?": "Revenue grew nicely this quarter.",
        "What was the operating margin in Q2?": "Operating margin improved to 22% in Q2.",
        "What is the customer churn rate?": "Customer churn stayed about the same as usual.",
    }
    return answers.get(question, "I don't know.")


# ============================================================================
# STEP 3a: Cheap scorer -- keyword/fact coverage
# ============================================================================

@dataclass
class ScoreResult:
    case_id: str
    passed: bool
    detail: str


def score_keyword_coverage(case: EvalCase, answer: str) -> ScoreResult:
    missing = [fact for fact in case.required_facts if fact.lower() not in answer.lower()]
    if missing:
        return ScoreResult(case.id, False, f"missing: {', '.join(repr(m) for m in missing)}")
    return ScoreResult(case.id, True, f"keyword coverage {len(case.required_facts)}/{len(case.required_facts)}")


# ============================================================================
# STEP 3b: LLM-as-judge -- structured verdict, catches paraphrases
# ============================================================================
# Keyword coverage would falsely PASS "Revenue grew fifteen percent" (no
# literal "15%") and falsely FAIL "Revenue grew 15 pct." An LLM judge
# compares *meaning*, not substrings -- at the cost of being probabilistic
# and costing a call. Forcing structured (Pydantic) output means you get
# a typed verdict back, not a paragraph you have to regex.

class Verdict(BaseModel):
    passed: bool = Field(description="Does the answer convey the same facts as the expected answer?")
    reasoning: str = Field(description="One sentence explaining the verdict")


_NUMBER_WORDS = {
    "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
    "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18",
    "nineteen": "19", "twenty": "20", "twenty-two": "22",
}


def _normalize_spelled_out_numbers(text: str) -> str:
    """'fifteen percent' -> '15 percent'. A stand-in for what an LLM judge
    does for free (understanding that 'fifteen' and '15' mean the same
    number) -- without this, a paraphrased number looks like a missing fact
    to any substring-based check."""
    words = text.lower().replace("-", " ").split()
    return " ".join(_NUMBER_WORDS.get(w.strip(".,!?"), w) for w in words)


async def llm_judge(case: EvalCase, answer: str) -> Verdict:
    if os.getenv("ORCHESTRATOR_ENDPOINT"):
        from llm_helper import get_llm
        llm = get_llm(model="gpt-4o", temperature=0.0).with_structured_output(Verdict)
        return await llm.ainvoke([
            {
                "role": "system",
                "content": (
                    "You are grading an answer against an expected answer. "
                    "Judge whether the answer conveys the same facts, even if "
                    "worded differently. Ignore style, judge substance."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {case.question}\n"
                    f"Expected answer: {case.expected_answer}\n"
                    f"Actual answer: {answer}\n"
                ),
            },
        ])

    # Mock judge (no .env): normalize spelled-out numbers before checking,
    # so "fifteen percent" is recognized as the same fact as "15%" -- a
    # narrow stand-in for the semantic matching a real LLM judge does for
    # free, just enough to demonstrate the difference from a plain
    # substring check.
    normalized = _normalize_spelled_out_numbers(answer)
    missing = [
        fact for fact in case.required_facts
        if fact.lower() not in answer.lower() and fact.rstrip("%") not in normalized
    ]
    if missing:
        return Verdict(passed=False, reasoning=f"Missing required fact(s): {', '.join(missing)}")
    return Verdict(passed=True, reasoning="All required facts present (numbers normalized before comparing).")


# ============================================================================
# STEP 4: Run the dataset against a SUT, produce a report
# ============================================================================

@dataclass
class EvalReport:
    results: dict[str, bool]  # case_id -> passed

    @property
    def pass_rate(self) -> tuple[int, int]:
        passed = sum(1 for p in self.results.values() if p)
        return passed, len(self.results)


def run_keyword_eval(sut, dataset: list[EvalCase], label: str) -> EvalReport:
    print(f"=== Running {label} against the dataset ===")
    results = {}
    for case in dataset:
        answer = sut(case.question)
        result = score_keyword_coverage(case, answer)
        results[case.id] = result.passed
        status = "PASS" if result.passed else "FAIL"
        print(f"    [{case.id}] {status} -- {result.detail}")
    report = EvalReport(results)
    passed, total = report.pass_rate
    print(f"    Pass rate: {passed}/{total} ({round(100 * passed / total)}%)")
    print()
    return report


def diff_reports(before: EvalReport, after: EvalReport, before_label: str, after_label: str) -> int:
    print(f"=== Regression report: {before_label} -> {after_label} ===")
    regressions = 0
    for case_id, was_passed in before.results.items():
        now_passed = after.results[case_id]
        if was_passed and not now_passed:
            print(f"    REGRESSED: {case_id} (was PASS, now FAIL)")
            regressions += 1
        elif not was_passed and now_passed:
            print(f"    IMPROVED: {case_id} (was FAIL, now PASS)")
    if regressions:
        print(f"    {regressions} regression(s) found -- do not ship {after_label}")
    else:
        print(f"    No regressions -- {after_label} is safe to ship")
    return regressions


# ============================================================================
# Demo
# ============================================================================

async def main():
    print("=== Golden dataset ===")
    print(f"    {len(GOLDEN_DATASET)} questions loaded")
    print()

    report_v1 = run_keyword_eval(sut_v1, GOLDEN_DATASET, "SUT v1 (correct)")
    report_v2 = run_keyword_eval(sut_v2_regressed, GOLDEN_DATASET, "SUT v2 (regressed -- drops key facts)")

    diff_reports(report_v1, report_v2, "v1", "v2")
    print()

    print("=== LLM-as-judge catching a paraphrase keyword-coverage misses ===")
    paraphrase_case = GOLDEN_DATASET[0]
    paraphrase_answer = "Revenue increased by fifteen percent year over year."
    keyword_result = score_keyword_coverage(paraphrase_case, paraphrase_answer)
    judge_verdict = await llm_judge(paraphrase_case, paraphrase_answer)
    print(f"    Answer: \"{paraphrase_answer}\"")
    print(f"    Keyword coverage says: {'PASS' if keyword_result.passed else 'FAIL'} ({keyword_result.detail})")
    print(f"    LLM judge says: {'PASS' if judge_verdict.passed else 'FAIL'} ({judge_verdict.reasoning})")
    if not os.getenv("ORCHESTRATOR_ENDPOINT"):
        print("    (mock judge above normalizes spelled-out numbers -- set up .env for a real semantic judge call)")


if __name__ == "__main__":
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # Evals are a test suite for meaning, not values:
    #   1. GOLDEN DATASET -- fixed, versioned test cases (commit this to git)
    #   2. CHEAP SCORER FIRST -- keyword/fact coverage runs in milliseconds,
    #      no LLM call, catches the obvious regressions (dropped numbers,
    #      wrong entities)
    #   3. LLM JUDGE FOR NUANCE -- costs a call, catches paraphrases the
    #      cheap scorer would falsely fail (or falsely pass)
    #   4. DIFF REPORTS -- run the same dataset before/after a change, diff
    #      the pass/fail per case, not just the aggregate pass rate (a
    #      regression on q1 can hide behind an improvement on q3 if you
    #      only look at "3/3 -> 3/3")
    #
    # This is exactly the harness you'd want around lesson 01's RAG pipeline
    # (or any prompt) before changing chunk size, switching models, or
    # editing a system prompt -- run the same questions, compare reports.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a 4th EvalCase and a SUT that gets it subtly wrong (right
    #    number, wrong quarter) -- does keyword coverage catch it? Should it?
    # 2. Wire llm_judge() into run_keyword_eval() as a second pass: only
    #    call the LLM judge for cases the keyword scorer FAILs, to confirm
    #    it's a real miss and not a paraphrase false negative.
    # 3. Persist an EvalReport to a JSON file and write a small script that
    #    loads yesterday's report and diffs it against today's -- this is
    #    what CI would run on every PR that touches a prompt.
    # 4. Point sut_v1 at lesson 01's RAG pipeline (retrieve + grounded
    #    prompt) instead of a hardcoded dict, and eval the actual RAG output.
