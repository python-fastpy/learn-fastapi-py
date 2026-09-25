"""Lesson 06 -- Production LLM engineering: latency, cost, reliability, choices
==============================================================================

WHY THIS MATTERS:
  A prototype that works once in a notebook is not a product. In
  production every LLM call has a latency budget, a cost, a failure
  rate, and a model choice behind it -- and at scale those decide
  whether the feature ships. This lesson covers the engineering around
  the call, with simulations you can re-run and tweak.

WHAT YOU'LL LEARN:
  1. Latency: time-to-first-token vs tokens/sec, and why streaming matters
  2. Model selection and ROUTING: small model for easy calls, big for hard
  3. Response caching: when an identical request needs no LLM call at all
  4. Reliability: retries, fallbacks, timeouts -- measured success rates
  5. Batch vs real-time, and concurrency limits
  6. Prompting vs RAG vs fine-tuning: which one solves your problem
  7. Security and privacy checklist

Concepts:
  - TTFT: time to first token. Mostly input processing + queueing
  - TPS: output tokens per second. Output length drives total latency
  - Router: cheap logic (or a cheap model) that picks the model per request
  - Fallback: a second model/provider used when the first fails
  - Batch API: async bulk processing, typically ~50% cheaper, hours not seconds

PREREQUISITES: Lessons 01-05. Pure Python, no packages, no credentials.

Run:  uv run python 06_production_llm_engineering.py
"""

import hashlib
import json
import random
from collections import Counter


# ============================================================================
# PART 1: Latency
# ============================================================================

def latency(ttft_s: float, out_tokens: int, tps: float) -> float:
    return ttft_s + out_tokens / tps


def part1_latency():
    print("######## PART 1 -- Where the time goes ########\n")
    print("  total latency = TTFT (process input, queue) + output_tokens / tokens_per_sec\n")
    cases = [
        ("Classify a ticket (1 word out)", 0.4, 5, 80),
        ("Chat reply (150 tokens)", 0.5, 150, 80),
        ("Long answer (800 tokens)", 0.6, 800, 80),
        ("Same long answer, big model", 1.2, 800, 35),
        ("Reasoning model (2k thinking + 300 out)", 1.0, 2300, 80),
    ]
    print(f"  {'request':<42} {'TTFT':>5} {'out':>5} {'tok/s':>6} {'total':>7}  streamed: first text at")
    for label, ttft, out, tps in cases:
        total = latency(ttft, out, tps)
        first_visible = ttft if "Reasoning" not in label else latency(ttft, 2000, tps)
        print(f"  {label:<42} {ttft:>4.1f}s {out:>5} {tps:>6} {total:>6.1f}s  {first_visible:>5.1f}s")
    print("""
  Takeaways:
   - OUTPUT length dominates. Asking for "max 3 sentences" is a latency
     fix, not just a style choice.
   - STREAMING doesn't make the call faster, but the user sees text after
     TTFT instead of after the whole reply -- 10s feels like 0.6s.
   - Reasoning models spend tokens thinking BEFORE visible output; budget
     for it (or lower the effort setting) on latency-sensitive paths.
   - Input length mostly affects TTFT; prompt caching cuts it too.
""")


# ============================================================================
# PART 2: Model selection and routing
# ============================================================================

MODELS = {  # illustrative tiers -- plug in your provider's real numbers
    "small":  {"price_in": 0.25, "price_out": 1.25, "acc_easy": 0.95, "acc_hard": 0.55},
    "medium": {"price_in": 3.00, "price_out": 15.0, "acc_easy": 0.97, "acc_hard": 0.82},
    "large":  {"price_in": 5.00, "price_out": 25.0, "acc_easy": 0.98, "acc_hard": 0.92},
}


def call_cost(model: str, tin: int = 2000, tout: int = 300) -> float:
    m = MODELS[model]
    return (tin * m["price_in"] + tout * m["price_out"]) / 1e6


def route(request: dict) -> str:
    """A rule-based router. Real ones use request type, length, user tier,
    or a cheap classifier call. Start with rules -- they're debuggable."""
    return "large" if request["hard"] else "small"


def part2_routing():
    print("######## PART 2 -- Model choice and routing ########\n")
    rng = random.Random(7)
    requests = [{"hard": rng.random() < 0.2} for _ in range(10_000)]   # 20% hard

    def simulate(pick):
        cost = correct = 0.0
        for r in requests:
            m = pick(r)
            cost += call_cost(m)
            p = MODELS[m]["acc_hard" if r["hard"] else "acc_easy"]
            correct += rng.random() < p
        return cost, correct / len(requests)

    print("  10,000 requests, 20% of them hard:\n")
    print(f"    {'strategy':<32} {'cost':>8}  accuracy")
    for label, pick in [("all small", lambda r: "small"),
                        ("all medium", lambda r: "medium"),
                        ("all large", lambda r: "large"),
                        ("route easy->small, hard->large", route)]:
        cost, acc = simulate(pick)
        print(f"    {label:<32} ${cost:>7.2f}  {acc:.1%}")
    print("""
  Routing gets close to all-large accuracy at a fraction of the cost,
  because most traffic is easy. How to choose models in practice:
    1. Start with the most capable model to prove the task is POSSIBLE.
    2. Build an eval set (learn-ai-advanced 02).
    3. Try cheaper models / lower effort against it; keep what holds quality.
    4. Route only if the eval shows a clear easy/hard split.
  Judge cost per SOLVED task, not per call -- a cheap model that needs
  retries or human fixes isn't cheap.
""")


# ============================================================================
# PART 3: Response caching
# ============================================================================

def cache_key(model: str, messages: list[dict], temperature: float) -> str:
    """Hash of everything that affects the output. Normalize first:
    sort_keys + strip + lowercase so trivially different requests match."""
    norm = [{"role": m["role"], "content": " ".join(m["content"].lower().split())}
            for m in messages]
    blob = json.dumps({"model": model, "messages": norm, "t": temperature}, sort_keys=True)
    return hashlib.sha256(blob.encode()).hexdigest()


def part3_caching():
    print("######## PART 3 -- Response caching ########\n")
    faqs = [f"How do I {x}?" for x in
            ["reset my password", "add a teammate", "enable a region", "get an invoice",
             "rotate a deploy key", "cancel my plan", "change my email", "contact support"]]
    rng = random.Random(3)
    weights = [1 / (i + 1) for i in range(len(faqs))]   # a few questions dominate (Zipf)
    unique_tail = 0
    cache: dict[str, str] = {}
    hits = misses = 0
    for _ in range(5_000):
        if rng.random() < 0.35:                           # 35% are one-off questions
            q = f"Something unique #{unique_tail}"
            unique_tail += 1
        else:
            q = rng.choices(faqs, weights)[0]
            q = rng.choice([q, q.upper(), "  " + q + "  "])   # same question, messy input
        key = cache_key("small", [{"role": "user", "content": q}], 0.0)
        if key in cache:
            hits += 1
        else:
            misses += 1
            cache[key] = "<llm answer>"
    print(f"  5,000 support questions, exact-match cache after normalization:")
    print(f"    hits {hits:,}  misses {misses:,}  -> {hits / 5000:.0%} of LLM calls avoided\n")
    print("""  When a response cache is safe:
    - the answer doesn't depend on the user (no account data in context)
    - low temperature (you WANT the same answer every time)
    - you have a TTL / invalidation when the underlying docs change
  "Semantic" caching (match by embedding similarity) catches paraphrases
  but can serve a wrong answer to a subtly different question ("cancel my
  plan" vs "cancel my teammate's plan"). Use a high threshold and
  evaluate it. Different from PROMPT caching (lesson 04), which the
  provider does for you on a repeated prefix -- you still get a fresh answer.
""")


# ============================================================================
# PART 4: Reliability -- retries and fallbacks
# ============================================================================

def flaky_call(rng: random.Random, fail_rate: float) -> bool:
    return rng.random() >= fail_rate


def part4_reliability():
    print("######## PART 4 -- Retries and fallbacks ########\n")
    rng = random.Random(11)
    N = 20_000

    def run(fail_rate, retries, fallback_fail_rate=None):
        ok = 0
        for _ in range(N):
            success = any(flaky_call(rng, fail_rate) for _ in range(retries + 1))
            if not success and fallback_fail_rate is not None:
                success = flaky_call(rng, fallback_fail_rate)
            ok += success
        return ok / N

    print("  Primary fails 8% of calls (429 rate limits, 5xx, timeouts):\n")
    for label, kw in [("no retry", dict(retries=0)),
                      ("2 retries", dict(retries=2)),
                      ("2 retries + fallback model", dict(retries=2, fallback_fail_rate=0.05))]:
        print(f"    {label:<28} success {run(0.08, **kw):.3%}")
    print("""
  Retries assume failures are INDEPENDENT. During a real outage they're
  not -- every retry fails too -- which is why a fallback to a different
  model or provider matters. Production rules:
    - retry only retryable errors (429, 5xx, timeouts), never 400s
    - exponential backoff + jitter, honour retry-after headers
    - a timeout on EVERY call; streaming for long outputs
    - make tools idempotent -- a retried "send email" must not send twice
    - a circuit breaker stops hammering a provider that is down
  Implementations: learn-langgraph 12 (error handling), learn-mcp 06.
  Official SDKs already retry 429/5xx a couple of times by default.
""")


# ============================================================================
# PART 5: Batch vs real-time, and concurrency
# ============================================================================

def part5_batch():
    print("######## PART 5 -- Batch vs real-time ########\n")
    docs, cost_each = 50_000, 0.004
    print(f"  Classify {docs:,} documents at ${cost_each}/call:")
    print(f"    real-time API : ${docs * cost_each:>8,.0f}   results in minutes (if rate limits allow)")
    print(f"    batch API     : ${docs * cost_each * 0.5:>8,.0f}   results within hours, ~50% cheaper\n")
    print("""  Use batch for anything nobody is waiting on: nightly evals,
  back-filling embeddings or labels, bulk summarization.

  For real-time fan-out, cap concurrency (asyncio.Semaphore -- see
  python/10-async-await.py). Unbounded gather() over 10,000 calls will
  hit rate limits and turn into a retry storm.
""")


# ============================================================================
# PART 6: Prompting vs RAG vs fine-tuning
# ============================================================================

def part6_decision():
    print("######## PART 6 -- Prompting vs RAG vs fine-tuning ########\n")
    print("""  What's actually wrong?
        |
        |-- The model doesn't follow the format / tone / steps
        |      -> PROMPT ENGINEERING first (lesson 05): clearer spec, examples,
        |         structured outputs. Fine-tune only if that plateaus at high volume.
        |
        |-- The model doesn't KNOW the facts (your docs, recent data, private data)
        |      -> RAG / tools (lesson 04, learn-ai-advanced 01). Fine-tuning is a
        |         poor way to add facts: hard to update, still hallucinates them.
        |
        |-- It must take ACTIONS or use live data
        |      -> TOOLS / agents (learn-mini-claude, learn-mcp, learn-langgraph).
        |
        |-- It works, but it's too slow / expensive at scale on a NARROW task
        |      -> smaller model + better prompt; then fine-tune / distill a small
        |         model on outputs from a big one, validated by your eval set.
        |
        '-- You can't tell if it's working
               -> EVALS before anything else (learn-ai-advanced 02).

  | Approach     | Changes              | Cost to try | Updates         | Good for             |
  |--------------|----------------------|-------------|-----------------|----------------------|
  | Prompting    | the instructions     | minutes     | instant         | behaviour, format    |
  | RAG          | the context          | days        | re-index docs   | knowledge, citations |
  | Tools        | what it can DO       | days        | deploy code     | live data, actions   |
  | Fine-tuning  | the weights          | weeks + data| retrain         | narrow, high-volume  |
""")


# ============================================================================
# PART 7: Security and privacy
# ============================================================================

def part7_security():
    print("######## PART 7 -- Security and privacy checklist ########\n")
    print("""    [ ] No secrets in prompts (API keys, passwords) -- the model can repeat them
    [ ] PII redacted before logging (learn-ai-advanced 04) and minimised in context
    [ ] Know your provider's data retention / training policy for your tier
    [ ] Untrusted content (web, email, docs, tool output) treated as DATA
    [ ] Tools run with least privilege; destructive tools need confirmation
        (learn-mini-claude 02: sandbox + permission gate)
    [ ] Output validated before it's executed, rendered as HTML, or stored
    [ ] Per-user rate limits and spend caps -- an agent loop can burn money
    [ ] Every call logged with prompt version, model, tokens, cost, latency
""")


def main():
    part1_latency()
    part2_routing()
    part3_caching()
    part4_reliability()
    part5_batch()
    part6_decision()
    part7_security()


if __name__ == "__main__":
    main()

    # -- Key takeaway --------------------------------------------------------
    # Around every LLM call sits normal engineering: latency budgets,
    # caching, retries, fallbacks, concurrency limits, cost tracking, and
    # security. The model is one dependency. Treat it like a slow, costly,
    # occasionally-failing, occasionally-wrong external API -- because
    # that's what it is -- and measure everything with evals and traces.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Part 2: make 50% of requests hard. Is routing still worth it?
    # 2. Part 3: drop the normalization in cache_key (use raw content).
    #    How much does the hit rate fall?
    # 3. Part 4: simulate a 10-minute outage (fail_rate=1.0 for a block of
    #    calls). What do retries achieve? What does the fallback achieve?
