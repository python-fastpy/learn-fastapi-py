"""Lesson 02 -- Sampling: temperature, top_k, top_p, penalties, stop, max_tokens
=================================================================================

WHY THIS MATTERS:
  Lesson 01 ended with the model producing a probability table for the
  next token. SAMPLING is how ONE token gets picked from that table.
  Every "creativity" knob in an LLM API acts at this single step:

      logits --temperature--> softmax --top_k--> --top_p--> pick one token
                                                                  |
                penalties adjust logits of already-used tokens <--+
                stop / max_tokens decide when the loop ends

  The model's weights never change between calls. These settings only
  change how the next token is CHOSEN from what the model already
  predicted. That's the source of most confusion, so this lesson runs
  every case with real numbers.

WHAT YOU'LL LEARN:
  1. Logits -> softmax: how raw scores become probabilities
  2. Temperature: every value from 0 (greedy) to 2 (chaos), measured
  3. top_k: keep only the k most likely tokens
  4. top_p (nucleus): keep the smallest set whose probability sums to p
  5. How they COMBINE, and in what order (temperature first!)
  6. Seeds and determinism -- and why temperature 0 isn't a guarantee
  7. Frequency / presence penalties: fighting repetition
  8. max_tokens and stop sequences: how generation ends
  9. What to actually set for each kind of task

Concepts:
  - Logit: the raw, unnormalized score the model gives each token
  - Softmax: turns logits into probabilities that sum to 1
  - Temperature T: divide logits by T before softmax. T<1 sharpens, T>1 flattens
  - Greedy decoding: always pick the top token (what T=0 means)
  - Nucleus: the set of tokens top_p keeps

PREREQUISITES: Lesson 01. Pure Python, no packages, no credentials.

Run:  uv run python 02_sampling_temperature_top_p.py
"""

import math
import random
from collections import Counter

# The model's raw scores for the next token after "The weather today is".
# These are made up but shaped like real logits: a few plausible tokens,
# then a long tail of nonsense with low scores.
LOGITS = {
    " sunny": 3.2,
    " cloudy": 2.6,
    " rainy": 2.1,
    " cold": 1.5,
    " perfect": 0.9,
    " purple": -1.0,
    " banana": -2.5,
}


# ============================================================================
# The sampling pipeline -- each function is one real API knob
# ============================================================================

def softmax(logits: dict[str, float], temperature: float = 1.0) -> dict[str, float]:
    """Logits -> probabilities. Temperature divides the logits first.

    temperature == 0 is special-cased as greedy: all probability on the
    top token (dividing by 0 is undefined; APIs treat it as argmax).
    """
    if temperature == 0:
        best = max(logits, key=logits.get)
        return {t: (1.0 if t == best else 0.0) for t in logits}
    scaled = {t: v / temperature for t, v in logits.items()}
    m = max(scaled.values())                      # subtract max for numeric stability
    exps = {t: math.exp(v - m) for t, v in scaled.items()}
    total = sum(exps.values())
    return {t: e / total for t, e in sorted(exps.items(), key=lambda kv: -kv[1])}


def top_k_filter(probs: dict[str, float], k: int | None) -> dict[str, float]:
    """Keep the k most likely tokens, renormalize. k=None means no filter."""
    if k is None:
        return probs
    kept = dict(sorted(probs.items(), key=lambda kv: -kv[1])[:k])
    total = sum(kept.values())
    return {t: p / total for t, p in kept.items()}


def top_p_filter(probs: dict[str, float], p: float | None) -> dict[str, float]:
    """Nucleus sampling: keep the smallest top set whose mass reaches p."""
    if p is None or p >= 1.0:
        return probs
    kept, cumulative = {}, 0.0
    for tok, prob in sorted(probs.items(), key=lambda kv: -kv[1]):
        kept[tok] = prob
        cumulative += prob
        if cumulative >= p:
            break
    total = sum(kept.values())
    return {t: q / total for t, q in kept.items()}


def sampling_distribution(logits, temperature=1.0, top_k=None, top_p=None):
    """The order most inference engines use: temperature -> top_k -> top_p."""
    probs = softmax(logits, temperature)
    probs = top_k_filter(probs, top_k)
    probs = top_p_filter(probs, top_p)
    return probs


def sample(probs: dict[str, float], rng: random.Random) -> str:
    toks, weights = zip(*probs.items())
    return rng.choices(toks, weights=weights)[0]


def show(probs: dict[str, float], all_tokens=LOGITS):
    for tok in all_tokens:
        p = probs.get(tok, 0.0)
        mark = "" if tok in probs else "   (removed)"
        print(f"      {tok:<10} {p:6.1%}  {'#' * round(p * 40)}{mark}")


# ============================================================================
# PART 1: Logits -> softmax
# ============================================================================

def part1_softmax():
    print("######## PART 1 -- Logits become probabilities ########\n")
    print("  Prompt: 'The weather today is'   raw logits from the model:")
    for tok, v in LOGITS.items():
        print(f"      {tok:<10} {v:+.1f}")
    print("\n  softmax (temperature 1.0) -> probabilities that sum to 100%:")
    show(softmax(LOGITS, 1.0))
    print("\n  Note ' banana' is NOT zero. With plain sampling it WILL be")
    print("  picked occasionally -- that's what top_k / top_p exist to stop.\n")


# ============================================================================
# PART 2: Temperature -- every case
# ============================================================================

def part2_temperature():
    print("######## PART 2 -- Temperature sweep ########\n")
    print("  temperature divides every logit before softmax:")
    print("    T < 1  -> gaps between logits grow  -> top token dominates")
    print("    T = 1  -> the model's own distribution, unchanged")
    print("    T > 1  -> gaps shrink               -> long tail gets picked\n")

    rows = []
    for T in [0, 0.2, 0.5, 0.7, 1.0, 1.5, 2.0]:
        probs = softmax(LOGITS, T)
        rng = random.Random(42)
        counts = Counter(sample(probs, rng) for _ in range(1000))
        rows.append((T, probs, counts))

    header = "  T    " + "".join(f"{t.strip():>9}" for t in LOGITS) + "   | 1000 samples: distinct / nonsense"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for T, probs, counts in rows:
        cells = "".join(f"{probs[t]:>8.1%} " for t in LOGITS)
        nonsense = counts[" purple"] + counts[" banana"]
        print(f"  {T:<4} {cells}  |  {len(counts)} distinct, {nonsense:>3} nonsense")

    print("""
  Reading the table:
    T=0    greedy. ' sunny' every time. Deterministic, can get repetitive.
    T=0.2  near-greedy. Tiny variation. Good for facts, code, extraction.
    T=0.7  common default for chat. Varied but sensible.
    T=1.0  the raw model distribution. Creative writing.
    T=1.5+ the tail wakes up -- ' purple' and ' banana' start appearing.
           Over many tokens this compounds into incoherent text.
""")


# ============================================================================
# PART 3: top_k
# ============================================================================

def part3_top_k():
    print("######## PART 3 -- top_k: keep the k best tokens ########\n")
    for k in [1, 2, 3, None]:
        print(f"  top_k = {k}   (temperature 1.0)")
        show(sampling_distribution(LOGITS, 1.0, top_k=k))
        print()
    print("  top_k=1 is greedy (same as T=0). The weakness of top_k: k is")
    print("  FIXED. When the model is confident, k=3 still keeps 2 weak tokens;")
    print("  when it's unsure between 10 good options, k=3 cuts 7 good ones.")
    print("  top_p adapts to the shape instead -- next part.\n")


# ============================================================================
# PART 4: top_p (nucleus sampling)
# ============================================================================

def part4_top_p():
    print("######## PART 4 -- top_p: keep the top X% of probability mass ########\n")
    base = softmax(LOGITS, 1.0)
    cumulative = 0.0
    print("  Cumulative probability, most likely first (T=1.0):")
    for tok, p in base.items():
        cumulative += p
        print(f"      {tok:<10} {p:6.1%}   running total {cumulative:6.1%}")
    print()
    for p in [0.5, 0.8, 0.9, 0.95, 1.0]:
        kept = sampling_distribution(LOGITS, 1.0, top_p=p)
        print(f"  top_p = {p:<4} -> keeps {len(kept)} token(s): {', '.join(t.strip() for t in kept)}")

    # The adaptive part: same top_p, differently shaped distributions.
    confident = {" Paris": 6.0, " Lyon": 1.0, " Nice": 0.5, " Rome": 0.0}
    unsure = {" red": 1.0, " blue": 0.95, " green": 0.9, " black": 0.85, " white": 0.8}
    print("\n  Same top_p=0.9 on two different prompts:")
    for label, lg in [("'The capital of France is' (confident)", confident),
                      ("'My favourite colour is'  (unsure)   ", unsure)]:
        kept = sampling_distribution(lg, 1.0, top_p=0.9)
        print(f"    {label} -> keeps {len(kept)}: {', '.join(t.strip() for t in kept)}")
    print("\n  top_p shrinks to 1 option when the model is sure and widens when")
    print("  it isn't. That's why top_p is usually preferred over top_k.\n")


# ============================================================================
# PART 5: Combining them -- order matters
# ============================================================================

def part5_combinations():
    print("######## PART 5 -- Combining temperature + top_p + top_k ########\n")
    print("  Pipeline: logits / T -> softmax -> top_k -> top_p -> renormalize -> sample\n")
    cases = [
        ("T=0.7, top_p=1.0           (temperature only)", dict(temperature=0.7)),
        ("T=1.0, top_p=0.9           (top_p only)", dict(temperature=1.0, top_p=0.9)),
        ("T=1.5, top_p=0.9           (hot + nucleus)", dict(temperature=1.5, top_p=0.9)),
        ("T=0.5, top_p=0.9           (cool + nucleus)", dict(temperature=0.5, top_p=0.9)),
        ("T=1.0, top_k=3, top_p=0.9  (all three)", dict(temperature=1.0, top_k=3, top_p=0.9)),
        ("T=0,   top_p=0.9           (T=0 wins)", dict(temperature=0, top_p=0.9)),
    ]
    for label, kw in cases:
        probs = sampling_distribution(LOGITS, **kw)
        kept = ", ".join(f"{t.strip()} {p:.0%}" for t, p in probs.items() if p > 0)
        print(f"  {label}\n      -> {kept}\n")
    print("  Key interaction: temperature runs FIRST. A high T flattens the")
    print("  distribution, so the SAME top_p=0.9 lets in more tokens (compare")
    print("  T=1.5 vs T=0.5 above). Tuning both at once makes the effect hard")
    print("  to reason about -- common advice: change one, leave the other at")
    print("  its default. Some APIs (e.g. several Claude models) only allow one.\n")


# ============================================================================
# PART 6: Seeds and determinism
# ============================================================================

def part6_determinism():
    print("######## PART 6 -- Seeds and determinism ########\n")
    probs = softmax(LOGITS, 1.0)
    run = lambda seed: "".join(sample(probs, random.Random(seed * 100 + i))[1]
                               for i in range(12))
    print(f"  T=1.0, seed=7  -> {run(7)}   (first letter of each pick)")
    print(f"  T=1.0, seed=7  -> {run(7)}   same seed, same picks")
    print(f"  T=1.0, seed=8  -> {run(8)}   different seed, different picks")
    greedy = softmax(LOGITS, 0)
    print(f"  T=0            -> {''.join(sample(greedy, random.Random(i))[1] for i in range(12))}"
          f"   no randomness left at all")
    print("""
  In this simulation T=0 is perfectly deterministic. Real APIs are NOT
  fully deterministic even at temperature 0: GPU floating-point order,
  request batching and model updates can change a near-tie. Some APIs
  offer a `seed` parameter for best-effort reproducibility. For tests,
  don't assert on exact wording -- assert on structure or facts
  (learn-ai-advanced lesson 02, evals).
""")


# ============================================================================
# PART 7: Frequency and presence penalties
# ============================================================================
# These edit the LOGITS of tokens that already appeared in the output:
#   presence_penalty : flat subtraction if the token appeared at all
#   frequency_penalty: subtraction * how many times it appeared
# (OpenAI-style; range roughly -2..2. Not every provider offers them.)

LOOP_LOGITS = {  # a model that loves repeating itself
    "very": {"very": 2.0, "good": 1.5, "nice": 1.2, ".": 0.3},
    "good": {".": 2.0, "and": 1.0},
    "nice": {".": 2.0, "and": 1.0},
    "and": {"very": 1.8, "good": 1.0, "nice": 1.0},
}


def generate_with_penalties(freq: float, pres: float, steps: int = 10) -> str:
    out = ["very"]
    for _ in range(steps):
        logits = dict(LOOP_LOGITS.get(out[-1], {".": 1.0}))
        used = Counter(out)
        for tok in logits:
            if used[tok]:
                logits[tok] -= pres + freq * used[tok]
        nxt = max(logits, key=logits.get)          # greedy, so only penalties change the output
        out.append(nxt)
        if nxt == ".":
            break
    return " ".join(out)


def part7_penalties():
    print("######## PART 7 -- Repetition penalties ########\n")
    for freq, pres in [(0, 0), (0, 0.6), (0.4, 0), (0.8, 0.5)]:
        print(f"  frequency={freq:<3} presence={pres:<3} -> {generate_with_penalties(freq, pres)!r}")
    print("\n  No penalty: greedy decoding loops on 'very'. Penalties push the")
    print("  model toward tokens it hasn't used. Too high and it avoids words")
    print("  it NEEDS to repeat (variable names in code, a person's name).\n")


# ============================================================================
# PART 8: How generation stops -- max_tokens and stop sequences
# ============================================================================

def part8_stopping():
    print("######## PART 8 -- max_tokens and stop sequences ########\n")
    full = ["Step", " 1", ":", " boil", " water", ".", "\n", "Step", " 2", ":",
            " add", " pasta", ".", "\n", "Step", " 3", ":", " drain", ".", "<eos>"]

    def run(max_tokens=None, stop=None):
        text, n = "", 0
        for tok in full:
            if tok == "<eos>":
                return text, "end_turn / stop (model chose to end)"
            if max_tokens is not None and n >= max_tokens:
                return text, "max_tokens / length (cut off!)"
            candidate = text + tok
            if stop:
                for s in stop:
                    if s in candidate:
                        return candidate[:candidate.index(s)], f"stop_sequence {s!r}"
            text, n = candidate, n + 1
        return text, "?"

    for label, kw in [("no limits", {}), ("max_tokens=8", {"max_tokens": 8}),
                      ('stop=["Step 3"]', {"stop": ["Step 3"]})]:
        text, reason = run(**kw)
        print(f"  {label:<18} stop_reason = {reason}")
        print(f"      {text!r}\n")
    print("  max_tokens caps OUTPUT only (not input). Hitting it truncates")
    print("  mid-thought -- ALWAYS check the stop reason; a cut-off JSON object")
    print("  won't parse. Stop sequences are removed from the returned text.\n")


# ============================================================================
# PART 9: What to set, by task
# ============================================================================

def part9_recommendations():
    print("######## PART 9 -- Settings by task ########\n")
    print("""  | Task                              | temperature | top_p  | Why                                   |
  |-----------------------------------|-------------|--------|---------------------------------------|
  | Extraction, classification, JSON  | 0 - 0.2     | 1.0    | One right answer; variety = bugs      |
  | Code generation                   | 0 - 0.3     | 1.0    | Syntax punishes creative tokens       |
  | RAG / factual Q&A                 | 0 - 0.3     | 1.0    | Stick to the retrieved text           |
  | Agents / tool calling             | 0 - 0.3     | 1.0    | Reliable tool names & arguments       |
  | General chat / assistant          | 0.5 - 0.8   | 1.0    | Natural, not robotic                  |
  | Brainstorming, creative writing   | 0.8 - 1.2   | 0.9-1  | Variety IS the goal                   |
  | Many diverse candidates (then     | 0.9 - 1.2   | 0.95   | Explore, then pick the best with a    |
  |   pick the best)                  |             |        |   judge or a test                     |

  Provider notes (check your model's docs -- these change):
    - OpenAI chat models: temperature 0-2, top_p 0-1, plus frequency/
      presence penalties and `seed`. Reasoning models (o-series) don't
      accept custom temperature/top_p.
    - Claude: temperature 0-1 on models that accept sampling params.
      The newest Claude models (Opus 4.7+, Opus 5.x, Sonnet 5, Fable 5.x)
      REJECT temperature/top_p/top_k -- you steer them with the prompt
      and `effort` instead.
    - Reasoning / thinking models in general sample internally; the
      knob you get is "how much to think", not "how random".
""")


def main():
    part1_softmax()
    part2_temperature()
    part3_top_k()
    part4_top_p()
    part5_combinations()
    part6_determinism()
    part7_penalties()
    part8_stopping()
    part9_recommendations()


if __name__ == "__main__":
    main()

    # -- Key takeaway --------------------------------------------------------
    # The model computes ONE probability table per token. Sampling settings
    # only choose from that table:
    #   temperature -> reshape it (sharper / flatter)
    #   top_k/top_p -> cut off the tail
    #   penalties   -> push down tokens already used
    #   stop / max  -> end the loop
    # None of them make the model smarter or add knowledge. If answers are
    # WRONG, fix the context (lesson 04). If they're too random or too
    # repetitive, fix the sampling.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add a logit " sunny-ish": 3.19 (a near-tie with ' sunny') and run
    #    part 2 again -- this is why T=0 can still flip between runs on real
    #    hardware.
    # 2. Implement min_p sampling: keep tokens with p >= min_p * p(top).
    #    Compare with top_p at T=1.5.
    # 3. In part 8, set max_tokens=3 on a JSON output and try json.loads().
