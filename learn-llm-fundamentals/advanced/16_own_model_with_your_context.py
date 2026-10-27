"""Lesson 16 -- Run "our own model" with OUR context: what's possible
=====================================================================

WHY THIS MATTERS:
  "Can we have our own model that knows our documents?" -- yes, in three
  very different ways. This lesson runs two of them on the same small
  company handbook so you can compare them for real:

    ┌───────────────────────────┬──────────────────────┬──────────────────┐
    │ A. existing open model    │ B. train our OWN     │ C. fine-tune an  │
    │    + our docs as CONTEXT  │    model from scratch│    open model    │
    ├───────────────────────────┼──────────────────────┼──────────────────┤
    │ Ollama + retrieval (RAG)  │ learns ONLY our text │ lesson 14        │
    │ minutes, any laptop       │ toy: seconds         │ hours, a GPU     │
    │ fluent + grounded  ✓      │ real: weeks of GPUs  │ style/format ✓   │
    │ update = edit the docs    │ parrots, can't reason│ facts: poorly    │
    └───────────────────────────┴──────────────────────┴──────────────────┘
       ▲ what you should do                       (parts 2-3)   (part 5)
         (parts 4-5)

WHAT YOU'LL LEARN:
  1. The three meanings of "our own model with our context"
  2. B for real: train a word-level language model ONLY on our handbook
     and generate from it -- watch it parrot, mix facts and fail on
     anything it hasn't seen
  3. Why a from-scratch model can't use "context" the way an LLM can
  4. A for real: retrieve the relevant handbook lines and build the exact
     grounded prompt for a local open model (sent to Ollama if it's running)
  5. Local context limits (num_ctx), keeping data private, and choosing

Concepts:
  - Context: the text you put in the prompt at question time (lesson 04)
  - Training data: the text baked into the weights (lesson 01 / 12 / 14)
  - Grounding: answering only from supplied context, with citations (lesson 10)
  - num_ctx: Ollama's context-window setting for a local model

PREREQUISITES: Lessons 01, 04, 10 and 15. Pure Python standard library.
Part 4 talks to a local model only if Ollama is running (lesson 15).

Level: ADVANCED
Run:  uv run python advanced/16_own_model_with_your_context.py
      uv run python advanced/16_own_model_with_your_context.py --model qwen2.5:0.5b --question "How many vacation days do I get?"
"""

import argparse
import json
import math
import random
import re
import urllib.error
import urllib.request
from collections import Counter, defaultdict

OLLAMA = "http://127.0.0.1:11434"

# OUR context: a tiny company handbook (stand-in for your own docs)
HANDBOOK = {
    "leave-1": "Full-time employees get 25 vacation days per year.",
    "leave-2": "Unused vacation days can be carried over up to 5 days into the next year.",
    "leave-3": "Sick leave does not reduce your vacation days.",
    "remote-1": "Employees may work remotely up to 3 days per week.",
    "remote-2": "Remote work from another country needs approval from HR.",
    "expense-1": "Travel expenses must be submitted within 30 days of the trip.",
    "expense-2": "Meals during business travel are reimbursed up to 50 dollars per day.",
    "laptop-1": "Every employee gets a new laptop every 3 years.",
    "laptop-2": "Lost laptops must be reported to IT within 24 hours.",
    "security-1": "Passwords must be at least 14 characters and changed every year.",
}

QUESTIONS = [
    "How many vacation days do I get?",
    "Can I carry over unused vacation days?",
    "How long do I have to submit travel expenses?",
    "Can I work from Spain for a month?",      # needs combining remote-1 + remote-2
    "What is the parental leave policy?",      # NOT in the handbook -> must say "don't know"
]


def header(title: str):
    print(f"\n######## {title} ########\n")


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+|[.,?]", text.lower())


# ============================================================================
# PART 1: Three meanings of "our own model with our context"
# ============================================================================
#   WHERE OUR KNOWLEDGE LIVES
#   A. in the PROMPT    question ─▶ retrieve our docs ─▶ [docs + question] ─▶ open model
#                       knowledge changes the moment the docs change
#   B. in the WEIGHTS   our docs ─▶ train from scratch ─▶ model that knows ONLY our docs
#                       no general language skill, no reasoning
#   C. in the WEIGHTS   open model + our examples ─▶ fine-tune ─▶ same model, our style
#      (adjusted)       good for tone/format, poor for facts that change (lesson 14)

def part1_options():
    header("PART 1 -- Three meanings of 'our own model with our context'")
    print(f"  our context: a handbook of {len(HANDBOOK)} lines, "
          f"{sum(len(words(t)) for t in HANDBOOK.values())} words\n")
    rows = [
        ("A. open model + context", "prompt", "minutes", "laptop (8B fits, lesson 15)", "edit docs"),
        ("B. train from scratch", "weights", "toy: secs / real: weeks", "real: GPU cluster", "retrain"),
        ("C. fine-tune open model", "weights", "hours", "1 GPU (LoRA, lesson 14)", "retrain"),
    ]
    print(f"  {'option':<26}{'knowledge in':<14}{'time':<24}{'hardware':<29}update")
    for r in rows:
        print(f"  {r[0]:<26}{r[1]:<14}{r[2]:<24}{r[3]:<29}{r[4]}")


# ============================================================================
# PART 2: B for real -- train our own model on ONLY our handbook
# ============================================================================
#   TRAIN = COUNT WHAT FOLLOWS WHAT (lesson 01, but with backoff)
#   "full time employees get 25 vacation days per year ."
#    context (2 words)          next-word counts
#    ("employees","get")   ──▶  {25: 1, a: 1}
#    ("vacation","days")   ──▶  {per: 1, can: 1, .: 1}
#   unseen 2-word context? ──▶ back off to 1-word context ──▶ then to word frequency
#   The model's whole "knowledge" = these tables, built from 10 sentences.

class OwnModel:
    """A word-level trigram language model with simple backoff, trained from scratch."""

    def __init__(self, texts: list[str]):
        self.tri: dict[tuple, Counter] = defaultdict(Counter)
        self.bi: dict[str, Counter] = defaultdict(Counter)
        self.uni: Counter = Counter()
        for t in texts:
            toks = ["<s>", "<s>"] + words(t) + ["</s>"]
            for a, b, c in zip(toks, toks[1:], toks[2:]):
                self.tri[(a, b)][c] += 1
                self.bi[b][c] += 1
                self.uni[c] += 1

    def next_dist(self, a: str, b: str) -> tuple[Counter, str]:
        if self.tri.get((a, b)):
            return self.tri[(a, b)], "trigram"
        if self.bi.get(b):
            return self.bi[b], "bigram (backoff)"
        return self.uni, "unigram (backoff)"

    def generate(self, prompt: str, rng: random.Random, max_words: int = 18) -> tuple[str, list[str]]:
        toks = ["<s>", "<s>"] + words(prompt)
        used = []
        for _ in range(max_words):
            dist, level = self.next_dist(toks[-2], toks[-1])
            choices, weights = zip(*dist.items())
            nxt = rng.choices(choices, weights=weights)[0]
            used.append(level)
            if nxt == "</s>":
                break
            toks.append(nxt)
        return " ".join(toks[2:]), used

    def perplexity(self, text: str) -> float:
        """How surprised the model is by `text` (lower = more familiar). Add-one smoothed."""
        toks = ["<s>", "<s>"] + words(text) + ["</s>"]
        vocab = len(self.uni) + 1
        logp = 0.0
        for a, b, c in zip(toks, toks[1:], toks[2:]):
            dist, _ = self.next_dist(a, b)
            logp += math.log((dist[c] + 1) / (sum(dist.values()) + vocab))
        return math.exp(-logp / (len(toks) - 2))


def part2_train_own(model: OwnModel):
    header("PART 2 -- B for real: train our OWN model on only the handbook")
    print(f"  trained in one pass: {len(model.tri)} trigram contexts, "
          f"{len(model.bi)} bigram contexts, vocab {len(model.uni)} words\n")
    rng = random.Random(16)
    real = {" ".join(words(t)) for t in HANDBOOK.values()}
    for prompt in ["employees get", "unused vacation", "lost laptops", "the weather today"]:
        out, levels = model.generate(prompt, rng)
        backoffs = sum(l != "trigram" for l in levels)
        verdict = ("copied a real handbook line" if any(out in r or r in out for r in real)
                   else "SPLICED -- this sentence is NOT in the handbook")
        print(f"  prompt {prompt!r:<20} -> {out!r}")
        print(f"  {'':<27}{verdict}; {backoffs} of {len(levels)} words needed backoff\n")
    print("  It either copies a handbook line or SPLICES two together at a shared\n"
          "  word ('days', 'must') into a fluent statement that is false -- the\n"
          "  same root cause as hallucination in lesson 01, at tiny scale.")
    print("\n  perplexity (how familiar the text looks; lower = closer to training data):")
    for t in ["Full-time employees get 25 vacation days per year.",
              "Full-time employees get 40 vacation days per year.",
              "The quarterly revenue grew by twelve percent."]:
        print(f"    {model.perplexity(t):>8.1f}  {t!r}")
    print("  It can tell 'sounds like our handbook' from 'doesn't' -- but '25' vs '40'\n"
          "  barely moves the score: it models WORDS, it doesn't know FACTS.")


# ============================================================================
# PART 3: Why a from-scratch model can't use "context"
# ============================================================================
#   A QUESTION IS JUST MORE WORDS TO CONTINUE
#   "how many vacation days do i get ?"  ──▶  last 2 words ("get","?")
#      seen in training?  no ──▶ backoff ──▶ continues with a random frequent word
#   An LLM was trained on trillions of Q&A-like texts, so "question ──▶ answer"
#   is a pattern it knows. Our model saw 10 statements and zero questions.

def part3_no_context(model: OwnModel):
    header("PART 3 -- Why our own tiny model can't answer questions")
    rng = random.Random(3)
    for q in QUESTIONS[:3]:
        out, levels = model.generate(q, rng, max_words=10)
        print(f"  Q: {q}")
        print(f"     model continues: {out[len(' '.join(words(q))):].strip()!r}   "
              f"(first step: {levels[0]})")
    print("\n  Putting the handbook in front of the question doesn't help either: the\n"
          "  model only looks at the last 2 words. 'Using context' needs attention\n"
          "  over the whole prompt (lesson 12) plus training on question->answer\n"
          "  data -- exactly what a real open model already has. So: don't build\n"
          "  the language skill yourself; BORROW it and supply your context (part 4).")


# ============================================================================
# PART 4: A for real -- open model + our context (local RAG)
# ============================================================================
#   ONE QUESTION, GROUNDED IN OUR DOCS, ON A LOCAL MODEL
#   question ─▶ score every handbook line (keyword overlap, lesson 10)
#            ─▶ top 3 lines + [ids] ─▶ prompt: "answer ONLY from these, cite [id],
#               else say you don't know" ─▶ Ollama on THIS machine ─▶ answer
#   Nothing leaves the laptop: the docs, the question and the model are all local.

STOP = {"the", "a", "an", "is", "are", "do", "i", "can", "my", "of", "to", "for", "how", "what",
        "many", "much", "long", "have", "get", "in", "be", "it", "from", "?", ".", ","}


def retrieve(question: str, k: int = 3) -> list[tuple[str, str, int]]:
    q = {w.rstrip("s") for w in words(question)} - STOP
    scored = []
    for doc_id, text in HANDBOOK.items():
        d = {w.rstrip("s") for w in words(text)} - STOP
        scored.append((doc_id, text, len(q & d)))
    scored.sort(key=lambda x: (-x[2], x[0]))
    return [s for s in scored[:k] if s[2] > 0]


def build_prompt(question: str, hits: list[tuple[str, str, int]]) -> list[dict]:
    context = "\n".join(f"[{doc_id}] {text}" for doc_id, text, _ in hits) or "(no matching documents)"
    system = ("You answer questions about the company handbook. Use ONLY the documents "
              "below. Cite the [id] of every document you use. If the answer is not in "
              "the documents, say exactly: I don't know based on the handbook.")
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"<documents>\n{context}\n</documents>\n\nQuestion: {question}"}]


def ask_ollama(model: str, messages: list[dict]) -> str | None:
    body = json.dumps({"model": model, "messages": messages, "stream": False,
                       "options": {"temperature": 0, "num_ctx": 4096}}).encode()
    req = urllib.request.Request(OLLAMA + "/api/chat", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())["message"]["content"].strip()
    except (urllib.error.URLError, OSError, KeyError):
        return None


def ollama_up() -> bool:
    try:
        urllib.request.urlopen(OLLAMA + "/api/tags", timeout=2)
        return True
    except (urllib.error.URLError, OSError):
        return False


def part4_local_rag(model: str, extra_question: str | None):
    header("PART 4 -- A for real: a local open model + our context")
    live = ollama_up()
    print(f"  Ollama at {OLLAMA}: {'running -> real answers below' if live else 'not running -> showing the exact prompts'}\n")
    qs = QUESTIONS + ([extra_question] if extra_question and extra_question not in QUESTIONS else [])
    for i, q in enumerate(qs):
        hits = retrieve(q)
        print(f"  Q: {q}")
        print(f"     retrieved: {[(h[0], h[2]) for h in hits] or 'nothing'}   (doc id, matching words)")
        messages = build_prompt(q, hits)
        if live:
            answer = ask_ollama(model, messages)
            print(f"     {model}: {answer if answer else '(call failed -- is the model pulled? ollama pull ' + model + ')'}")
        elif i == 0:
            print("     prompt sent to the model:")
            for m in messages:
                for line in m["content"].splitlines():
                    print(f"       {m['role']:>6} | {line}")
        print()
    print("  Note the last question: keyword search still returned 'leave-3' (it shares\n"
          "  the word 'leave'), but nothing about parental leave. Retrieval ALWAYS\n"
          "  returns something -- the prompt's 'say I don't know' rule is what stops a\n"
          "  made-up answer (lesson 10 part 9, lesson 11 grounding checks).\n")
    if not live:
        print("  To get real answers (lesson 15 has the details):")
        print(f"    winget install Ollama.Ollama   then   ollama pull {model}")
        print("    re-run this lesson -- part 4 will send these prompts to the local model.")
    print("\n  Why this wins: the open model already reads, reasons and phrases; we only\n"
          "  supply the facts. Change a policy -> edit one line -> the next answer\n"
          "  changes. No training run, and the 'parental leave' question gets an\n"
          "  honest 'I don't know' instead of a spliced guess (part 2).")


# ============================================================================
# PART 5: Local context limits, privacy, and choosing
# ============================================================================
#   HOW MUCH CONTEXT FITS LOCALLY?
#   model max context (config.json / model card)  e.g. 32k tokens
#        └─ Ollama uses options.num_ctx  ── set it, or long prompts get CUT
#   tokens = system + retrieved docs + question + answer  (lesson 04 budget)
#   bigger num_ctx = more RAM for the KV cache (lesson 15 part 2)

def part5_choose():
    header("PART 5 -- Local context limits, privacy, choosing")
    handbook_tokens = sum(len(t) for t in HANDBOOK.values()) // 4
    per_line = handbook_tokens / len(HANDBOOK)
    print(f"  whole handbook ~{handbook_tokens} tokens (chars / 4, lesson 01b) -> at this size\n"
          f"  you could skip retrieval and put ALL of it in the prompt.")
    for lines in (10, 500, 1_000, 100_000):
        tokens = round(per_line * lines)
        fits = "fits in num_ctx=8192" if tokens <= 8192 else "too big -> retrieve the top-k (lesson 10)"
        print(f"    {lines:>7,} policy lines ~{tokens:>9,} tokens  {fits}")
    print("\n  Checklist:")
    for c in ["Set num_ctx explicitly -- a local default can be smaller than the model's max",
              "Retrieve top-k chunks once the docs outgrow the window (lessons 04, 10)",
              "Keep 'answer only from documents + cite + say I don't know' in the system prompt",
              "Evaluate on YOUR questions, incl. unanswerable ones (lesson 11)",
              "Privacy: docs, prompts and answers stay on the machine -- no API involved",
              "Need a specific tone/format on top? fine-tune with LoRA (lesson 14, option C)"]:
        print("   [ ]", c)
    print("\n  Verdict: 'our own model with our context' = an open model you run (lesson\n"
          "  15) + your documents in the prompt. Train from scratch only to LEARN how\n"
          "  models work (parts 2-3, lessons 12, 14), not to ship.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5:0.5b", help="Ollama model tag (lesson 15)")
    ap.add_argument("--question", default=None, help="ask your own handbook question")
    args = ap.parse_args()
    own = OwnModel(list(HANDBOOK.values()))
    part1_options()
    part2_train_own(own)
    part3_no_context(own)
    part4_local_rag(args.model, args.question)
    part5_choose()


if __name__ == "__main__":
    main()

# Key takeaway: you rarely need your OWN model -- you need YOUR context in front
# of a good open model you run yourself. Training from scratch teaches how it
# works; it doesn't produce something you'd ship.
# Exercise: add a policy line to HANDBOOK ("Parental leave is 16 weeks."), re-run,
# and watch part 4 retrieve it while part 2's model would need retraining.
