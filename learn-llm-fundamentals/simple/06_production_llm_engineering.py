"""06 -- Production LLM engineering  (simple version)
===================================================

IN ONE LINE:
  In production, an LLM call is a slow, costly, sometimes-failing network call.
  Treat it like one: stream it, route it, cache it, retry it.

REAL USE CASE:
  Your FastAPI endpoint POST /ask gets thousands of questions per day.

     request
        │
        ▼
     ┌────────┐  hit
     │ CACHE? │ ──────▶ return saved answer  ($0, instant)
     └────────┘
        │ miss
        ▼
     ┌────────┐  easy ─▶ small model (cheap)
     │ ROUTER │
     └────────┘  hard ─▶ big model (expensive)
        │
        ▼  failed? retry 2x, then try a backup model
     answer ──▶ save in cache ──▶ stream to the user

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
def total_seconds(first_token_s, output_tokens, tokens_per_s):
    return first_token_s + output_tokens / tokens_per_s


# ----------------------------------------------------------------------------
# STEP 2: ROUTING = cheap model for easy work, big model for hard work
# ----------------------------------------------------------------------------
PRICE_PER_CALL = {"small": 0.001, "big": 0.02}      # example prices in dollars


def route(question):
    """Simple rules are fine to start. They are easy to debug."""
    if len(question.split()) > 12 or "explain" in question.lower():
        return "big"
    return "small"


# ----------------------------------------------------------------------------
# STEP 3: CACHING = same question -> same saved answer
# ----------------------------------------------------------------------------
cache: dict[str, str] = {}                          # question -> saved answer


def ask_with_cache(question):
    key = " ".join(question.lower().split())        # "  Hi THERE " -> "hi there"
    if key in cache:
        return cache[key], "HIT (no LLM call)"
    answer = "<answer to: " + key + ">"             # here you would call the LLM
    cache[key] = answer
    return answer, "MISS (called the LLM)"


# ----------------------------------------------------------------------------
# STEP 4: RETRY + FALLBACK = do not give up on the first error
# ----------------------------------------------------------------------------
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
        print("  ", model.ljust(5), "<-", q)
    big_cost = PRICE_PER_CALL["big"] * len(questions)
    print("   cost all-big: $" + str(round(big_cost, 3)), "  cost routed: $" + str(round(routed_cost, 3)))

    print("\nSTEP 3: caching")
    for q in ["How do I reset my password?", "how do I reset my   PASSWORD?", "Do you have an API?"]:
        _answer, status = ask_with_cache(q)
        print("  ", status.ljust(22), "<-", repr(q))

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
