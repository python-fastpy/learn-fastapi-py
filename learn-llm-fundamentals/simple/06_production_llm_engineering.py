"""06 -- Production LLM engineering  (simple version)
===================================================

IN ONE LINE:
  In production, an LLM call is a slow, costly, sometimes-failing network call.
  Treat it like one: stream it, route it, cache it, retry it.

REAL USE CASE:
  Your FastAPI endpoint POST /ask gets thousands of questions per day.

  ┌──────────────┐  POST /ask   ┌──────────────────────────────┐  HTTPS   ┌──────────────────────┐
  │   Browser    │ ───────────▶ │        YOUR FASTAPI          │ ───────▶ │    LLM PROVIDERS     │
  │ "How do I    │              │ cache -> router -> retry     │          │  small model (cheap) │
  │  reset my    │              │ -> fallback   (THIS LESSON)  │          │  big model (costly)  │
  │  password?"  │ ◀─────────── │ stream the answer back       │ ◀─────── │  backup model        │
  └──────────────┘   streamed   └──────────────────────────────┘  tokens  └──────────────────────┘
                     text
  All the "production" work is in YOUR code, between the user and the model.

ONE REQUEST, THE FULL PATH (in this file each part is its own STEP; a real app chains them):

     request: "How do I reset my password?"
        │
        ▼  normalize: lower case, single spaces                        (STEP 3)
     key = "how do i reset my password?"
        │
        ▼
     ┌───────────────┐  hit   ┌────────────────────────────────────┐
     │ key in cache? │ ─────▶ │ return the saved answer            │ ──▶ done ($0, instant)
     └───────────────┘        └────────────────────────────────────┘
        │ miss                  ▲
        │                       └── later "how do I reset my   PASSWORD?" gives the SAME key -> HIT
        ▼                                                              (STEP 2)
     ┌───────────────┐  more than 12 words, or has "explain"  ──▶ "big"   model  $0.02
     │    ROUTER     │
     └───────────────┘  else                                   ──▶ "small" model  $0.001
        │
        ▼                                                              (STEP 4)
     ┌─▶ call the main model (attempt 1, 2, 3)
     │      │
     │      ▼
     │   it worked? ── yes ─────────────────────────────────────┐
     │      │ no (429 rate limit / 500 / timeout)               │
     │      ▼                                                   │
     │   tries left? ── no ──▶ call the BACKUP model ───────────┤
     │      │ yes                                               │
     │      ▼                                                   │
     │   wait 1s, 2s, 4s ... (backoff)                          │
     └──────┘                                                   ▼
                                                             answer
                                                                │
                                                                ▼
                                       cache[key] = answer, then stream it to the user
                                       (first words after 0.5s, see STEP 1)

THE REAL RUN, step by step (the numbers the script prints):

   STEP 1  latency = 0.5s first token + tokens / 80 per second
           10 tokens -> 0.62 s     150 tokens -> 2.38 s     800 tokens -> 10.5 s

   STEP 2  question                                                   words  rule hit    model
           ────────────────────────────────────────────────────────   ─────  ─────────   ─────
           Reset password?                                               2   none        small
           Price of Pro plan?                                            4   none        small
           Is there an API?                                              4   none        small
           Explain why my monthly invoice is higher than last month     10   "explain"   big
           cost all-big: $0.08     cost routed: $0.023   (3 x 0.001 + 1 x 0.02)

   STEP 3  question                          key                            result
           ───────────────────────────────   ────────────────────────────   ─────
           'How do I reset my password?'     'how do i reset my password?'  MISS
           'how do I reset my   PASSWORD?'   'how do i reset my password?'  HIT   ◀── same key!
           'Do you have an API?'             'do you have an api?'          MISS

   STEP 4  request   attempt 1   attempt 2   attempt 3   answer from
           ───────   ─────────   ─────────   ─────────   ──────────────────────────
           1         429 fail    ok                      main-model (attempt 2)
           2         ok                                  main-model (attempt 1)
           3         429 fail    429 fail    429 fail    backup-model (fallback)
           4         ok                                  main-model (attempt 1)

WHAT AN ENGINEER MUST KNOW:
  1. Time = wait for first word + (output words / speed). Long answers are slow.
     Streaming shows the first words fast, so it FEELS fast.
  2. Most requests are easy. Send them to a small, cheap model.
  3. The same question again? Return the saved answer. No LLM call.
  4. Calls fail (429 rate limit, 500, timeout). Retry, then use a fallback.
  5. Never put secrets or private user data in prompts or logs.

Run:  uv run python simple/06_production_llm_engineering.py
"""

import random

# ----------------------------------------------------------------------------
# STEP 1: LATENCY = time to first token + time to write the answer
# ----------------------------------------------------------------------------
#   first_token_s = 0.5    output_tokens = 150    tokens_per_s = 80
#      │
#      ▼  time to write = 150 / 80
#   1.875 s
#      │
#      ▼  + 0.5 s wait for the first token
#   2.375 s  ──▶ printed as 2.38 s
#
#   timeline for 150 tokens:
#   0s        0.5s                                              2.38s
#   ├─ wait ──┼──────────── writing 150 tokens ──────────────────┤
#             ▲
#             └── with streaming, the user sees text HERE, not at the end
def total_seconds(first_token_s, output_tokens, tokens_per_s):
    return first_token_s + output_tokens / tokens_per_s


# ----------------------------------------------------------------------------
# STEP 2: ROUTING = cheap model for easy work, big model for hard work
# ----------------------------------------------------------------------------
#   "Explain why my monthly invoice is higher than last month"
#      │
#      ▼  count the words
#   10 words
#      │
#      ▼
#   more than 12 words? ── yes ──▶ "big"
#      │ no
#      ▼
#   has "explain"? ── yes ──▶ "big"   ◀── this question
#      │ no
#      ▼
#   "small"                           ◀── "Reset password?" (2 words)
#
#   cost: 3 small + 1 big = 3 x $0.001 + 1 x $0.02 = $0.023   (all-big: 4 x $0.02 = $0.08)
PRICE_PER_CALL = {"small": 0.001, "big": 0.02}      # example prices in dollars


def route(question):
    """Simple rules are fine to start. They are easy to debug."""
    if len(question.split()) > 12 or "explain" in question.lower():
        return "big"
    return "small"


# ----------------------------------------------------------------------------
# STEP 3: CACHING = same question -> same saved answer
# ----------------------------------------------------------------------------
#   "how do I reset my   PASSWORD?"
#      │
#      ▼  make_key: lower case + split on spaces + join with ONE space
#   "how do i reset my password?"
#      │
#      ▼
#   key in cache? ── yes ──▶ return cache[key]          "HIT (no LLM call)"   $0
#      │ no
#      ▼
#   answer = call the LLM   ──▶ "<answer to: how do i reset my password?>"
#      │
#      ▼
#   cache[key] = answer      (the next same question is a HIT)
#      │
#      ▼
#   return answer                                         "MISS (called the LLM)"
cache: dict[str, str] = {}                          # question -> saved answer


def make_key(question):
    return " ".join(question.lower().split())       # "  Hi THERE " -> "hi there"


def ask_with_cache(question):
    key = make_key(question)
    if key in cache:
        return cache[key], "HIT (no LLM call)"
    answer = "<answer to: " + key + ">"             # here you would call the LLM
    cache[key] = answer
    return answer, "MISS (called the LLM)"


# ----------------------------------------------------------------------------
# STEP 4: RETRY + FALLBACK = do not give up on the first error
# ----------------------------------------------------------------------------
#   attempt = 1
#      │
#      ▼
#   ┌─▶ fake_llm("main-model")
#   │      │
#   │      ▼
#   │   raised "429 rate limit"? ── no ──▶ return (answer, attempt)   request 1: attempt 2
#   │      │ yes                                                       request 2: attempt 1
#   │      ▼
#   │   print "attempt N failed"
#   │      │
#   │      ▼
#   │   attempt 3 done? ── yes ──▶ fake_llm("backup-model")
#   │      │ no                    return (answer, "fallback")         request 3: fallback
#   │      ▼
#   │   attempt += 1   (real code: wait 1s, 2s, 4s first)
#   └──────┘
#
# Real call with a timeout and SDK retries (Anthropic SDK):
#   client = anthropic.Anthropic(timeout=30, max_retries=2)
#   reply = client.messages.create(model=..., max_tokens=500, messages=[...])
def fake_llm(model, rng):
    """The main model fails 50% of the time, like a busy API.
    The backup model (other provider) works in this demo."""
    if model == "main-model" and rng.random() < 0.5:
        raise RuntimeError("429 rate limit")
    return "answer from " + model


def call_with_retry(rng, retries=2):
    for attempt in range(1, retries + 2):           # 1 try + 2 retries
        try:
            return fake_llm("main-model", rng), attempt
        except RuntimeError as error:
            print("     attempt", attempt, "failed:", error)
            # real code: wait 1s, 2s, 4s ... (exponential backoff) before next try
    return fake_llm("backup-model", rng), "fallback"


def main():
    print("STEP 1: latency (first token 0.5s, speed 80 tokens/s)")
    for tokens in [10, 150, 800]:
        seconds = round(total_seconds(0.5, tokens, 80), 2)
        print("  ", tokens, "output tokens ->", seconds, "s")
    print("   With streaming, the user sees text after 0.5s in every case.")

    print("\nSTEP 2: routing")
    questions = ["Reset password?", "Price of Pro plan?", "Is there an API?",
                 "Explain why my monthly invoice is higher than last month"]
    routed_cost = 0
    for q in questions:
        model = route(q)
        routed_cost += PRICE_PER_CALL[model]
        print("  ", model.ljust(5), "<-", str(len(q.split())).rjust(2), "words |", q)
    big_cost = PRICE_PER_CALL["big"] * len(questions)
    print("   cost all-big: $" + str(round(big_cost, 3)), "  cost routed: $" + str(round(routed_cost, 3)))

    print("\nSTEP 3: caching")
    for q in ["How do I reset my password?", "how do I reset my   PASSWORD?", "Do you have an API?"]:
        _answer, status = ask_with_cache(q)
        print("  ", status.ljust(22), "<-", repr(q).ljust(32), "key:", repr(make_key(q)))

    print("\nSTEP 4: retry, then fallback")
    rng = random.Random(1)
    for request in range(1, 5):
        print("   request", request)
        answer, attempt = call_with_retry(rng)
        print("     ->", answer, "(attempt:", str(attempt) + ")")


if __name__ == "__main__":
    main()

# Remember:
#   - Short answers are fast answers. Stream long ones.
#   - Route easy requests to a small model.
#   - Cache only answers that do not depend on the user.
#   - Retry only 429 / 5xx / timeouts, never 400 (bad request). Keep a fallback.
# Try: change the fail rate in fake_llm from 0.5 to 0.9 and see how often fallback is used.
