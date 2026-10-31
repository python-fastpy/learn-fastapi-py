"""17 -- Production: timeouts, retries, fallback, cache, logging
===============================================================

CONCEPT IN ONE LINE:
  LLM calls are slow, sometimes fail, and cost money. Wrap every call so your app
  stays fast, keeps working, and you can see what it costs.      (details: simple/06)

   request
     │
     ▼
   cache hit? ── yes ──▶ return saved answer        (0 tokens, ~0 ms)
     │ no
     ▼
   try main model ── error / timeout ──▶ wait, retry (1 s, 2 s ...)
     │ ok                                   │ still failing
     │                                      ▼
     │                              fallback model ── ok ──▶ answer
     ▼
   log: model, tokens in/out, latency, tokens/second  ──▶ save in cache ──▶ answer
"""

import json
import time
import urllib.error
import urllib.request

from ollama_client import CHAT_MODEL, OLLAMA

CACHE = {}


def call_model(model, question, timeout=60):
    """One raw call that RAISES on errors (the shared helper exits instead)."""
    body = {"model": model, "stream": False, "options": {"temperature": 0, "num_predict": 60},
            "messages": [{"role": "user", "content": question}]}
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def with_retry(model, question, tries=3):
    for attempt in range(1, tries + 1):
        try:
            return call_model(model, question)
        except urllib.error.HTTPError as e:
            if e.code < 500:                                # 4xx = OUR mistake (e.g. 404 no such model)
                raise RuntimeError(f"{model}: HTTP {e.code}, not retrying") from e   # retry won't help
            error = f"HTTP {e.code} server error"           # 5xx = server problem, may pass
        except (urllib.error.URLError, TimeoutError) as e:  # network / timeout = temporary
            error = str(e)[:50]
        wait = 2 ** (attempt - 1)                           # 1 s, 2 s, 4 s: "exponential backoff"
        print(f"    {model}: attempt {attempt} failed ({error})"
              + (f", retry in {wait} s" if attempt < tries else ""))
        if attempt < tries:
            time.sleep(wait)
    raise RuntimeError(f"{model} failed {tries} times")


def answer(question, models=(CHAT_MODEL,)):
    key = " ".join(question.lower().split())                # same question, other spacing = same key
    if key in CACHE:
        print("    cache HIT -> 0 tokens, instant")
        return CACHE[key]
    for model in models:                                    # main model first, then fallbacks
        try:
            r = with_retry(model, question, tries=2)
        except RuntimeError as e:
            print(f"    {e} -> trying the next model")
            continue
        secs = r["total_duration"] / 1e9                    # Ollama reports nanoseconds
        log = {"model": model, "in": r["prompt_eval_count"], "out": r["eval_count"],
               "latency_s": round(secs, 2), "tok_per_s": round(r["eval_count"] / (r["eval_duration"] / 1e9), 1)}
        print("    log:", json.dumps(log))                  # in a real app: send to your logging system
        CACHE[key] = r["message"]["content"].strip()
        return CACHE[key]
    return "Sorry, the assistant is not available right now."  # never show a stack trace to users


def main():
    q = "What is an HTTP status code? One sentence."

    print("STEP 1: normal call (logged)")
    t = time.time()
    print("   ", answer(q), f"({time.time() - t:.2f} s)")

    print("\nSTEP 2: same question again, different spacing -> cache")
    t = time.time()
    print("   ", answer("  what is an HTTP   status code?  One sentence. "), f"({time.time() - t:.3f} s)")

    print("\nSTEP 3: main model is broken -> retry, then fall back to a working model")
    print("   ", answer("Name one HTTP method.", models=("model-that-does-not-exist", CHAT_MODEL)))


if __name__ == "__main__":
    main()

# Remember: set a timeout on EVERY call, retry only temporary errors, log tokens per request
# (that's your bill), and cache answers that don't need to be fresh.
