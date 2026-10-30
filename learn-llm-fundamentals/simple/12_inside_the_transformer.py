"""12 -- Inside the transformer  (simple version)
===============================================

IN ONE LINE:
  Each word looks at the earlier words and decides how much each one matters.
  This is called ATTENTION. It is the heart of every modern LLM.

REAL USE CASE:
  You send a long prompt. For every new word it writes, the model compares
  that word with ALL the words before it. More words = more work.

     "the cat sat"
          │  each word -> a list of numbers (an embedding)
          ▼
     ┌───────────────────────────────┐
     │ ATTENTION for the word "sat"  │
     │  1. score   = dot product     │   "how related is each earlier word?"
     │  2. weights = softmax(scores) │   "turn scores into % that sum to 1"
     │  3. output  = weighted sum    │   "mix the words by those %"
     └───────────────────────────────┘
          │  repeat in many layers, then predict the next word
          ▼
     " on"

WHERE ATTENTION SITS IN A REAL APP:

  ┌──────────────┐  POST /chat   ┌──────────────────┐  HTTPS   ┌──────────────────────────────────┐
  │   Browser    │ ────────────▶ │  YOUR FASTAPI    │ ───────▶ │          LLM PROVIDER            │
  │ "the cat     │               │  sends prompt,   │          │ for each new token:              │
  │  sat"        │ ◀──────────── │  pays per token  │ ◀─────── │   embed -> [ATTENTION -> MLP]    │
  └──────────────┘    " on"      └──────────────────┘  answer  │          x many layers           │
                                                               │   -> predict next token          │
                                                               │ KV cache keeps old work in GPU   │
                                                               └──────────────────────────────────┘
  Long prompt = more attention work = slower first token and a bigger bill.

ATTENTION FOR "sat", AS A WORKED GRID (real numbers printed by STEP 1 to 3):

  query of "sat" = [0.0, 2.0]   ("who is doing the action?")

   word   vector       1. score = query · vector      2. exp(score)   weight = exp / 11.11
   ────   ──────────   ────────────────────────────   ─────────────   ────────────────────
   the    [1.0, 0.0]   0.0×1.0 + 2.0×0.0 = 0.00       1.00            0.09  ###
   cat    [0.0, 1.0]   0.0×0.0 + 2.0×1.0 = 2.00       7.39            0.67  ####################
   sat    [1.0, 0.5]   0.0×1.0 + 2.0×0.5 = 1.00       2.72            0.24  #######
                                                      ─────           ────
                                                total 11.11      sum  1.00

   3. weighted sum = weight × vector, then add the rows:

   the    0.09 × [1.0, 0.0] = [0.09, 0.0 ]
   cat    0.67 × [0.0, 1.0] = [0.0 , 0.67]
   sat    0.24 × [1.0, 0.5] = [0.24, 0.12]
                              ────────────
   new vector for "sat"     = [0.33, 0.79]   <- mostly "cat" now. "sat" knows WHO sat.

CAUSAL MASK -- each word only sees itself and the words BEFORE it:

                  looks at:  the     cat     sat
   "the"                     yes     -       -
   "cat"                     yes     yes     -
   "sat"                     yes     yes     yes
   "-" = future word, hidden. The model cannot cheat by reading ahead.

   Real run for "cat": query [1.0, 1.0] over ['the', 'cat'] only
     scores [1.0, 1.0]  ──▶  softmax  ──▶  weights [0.5, 0.5]   ("sat" gets nothing)

WHAT AN ENGINEER MUST KNOW:
  1. A word can only look BACK, never forward (the "causal mask").
  2. The model saves old work in a "KV cache", so each new word is cheaper.
  3. Output words are made one by one -> they are slower and cost more.
  4. Attention work grows with (number of words) squared -> context limits.
  5. Facts in the MIDDLE of a long prompt get less attention. Put key info
     at the start or the end.

Run:  uv run python simple/12_inside_the_transformer.py
"""

import math

# Tiny embeddings with 2 numbers each: [is_a_thing, is_an_action].
# Real models use thousands of numbers per word, learned in training.
WORDS = ["the", "cat", "sat"]
VECTORS = {
    "the": [1.0, 0.0],
    "cat": [0.0, 1.0],
    "sat": [1.0, 0.5],
}
# The "question" the word "sat" asks: "who is doing the action?"
QUERY_FOR_SAT = [0.0, 2.0]


# ----------------------------------------------------------------------------
# STEP 1: SCORE = dot product (how well does each word match my question?)
# ----------------------------------------------------------------------------
#   a = [0.0, 2.0]  (query of "sat")      b = [0.0, 1.0]  (vector of "cat")
#        │    │                                │    │
#        ▼    ▼  multiply pair by pair         │    │
#     0.0×0.0 = 0.0  ◀─────────────────────────┘    │
#     2.0×1.0 = 2.0  ◀──────────────────────────────┘
#        │
#        ▼  add up
#     0.0 + 2.0 = 2.00   <- high: "cat" answers the question well
#
#   same for "the" [1.0, 0.0] -> 0.00 (no match)   and "sat" [1.0, 0.5] -> 1.00
def dot(a, b):
    """Multiply pair by pair, then add up. Big number = good match."""
    return sum(x * y for x, y in zip(a, b))


# ----------------------------------------------------------------------------
# STEP 2: SOFTMAX = turn scores into percentages that add up to 1
# ----------------------------------------------------------------------------
#   scores        [0.00, 2.00, 1.00]          (the, cat, sat)
#      │
#      ▼  exp(each)  -> always positive, big scores grow MUCH bigger
#   exps          [1.00, 7.39, 2.72]
#      │
#      ▼  total = 1.00 + 7.39 + 2.72 = 11.11
#      │
#      ▼  divide each by the total
#   weights       [0.09, 0.67, 0.24]          sum = 1.00
#
#   Score 2 vs 1 is only "2x", but weight 0.67 vs 0.24 is almost 3x.
#   Softmax makes the best match stand out.
def softmax(scores):
    exps = [math.exp(s) for s in scores]     # exp makes every number positive
    total = sum(exps)
    return [e / total for e in exps]


# ----------------------------------------------------------------------------
# STEP 3: WEIGHTED SUM = mix the word vectors using those percentages
# ----------------------------------------------------------------------------
#   query [0.0, 2.0] + words ["the", "cat", "sat"]
#      │
#      ▼  STEP 1 for each word
#   scores  = [0.00, 2.00, 1.00]
#      │
#      ▼  STEP 2
#   weights = [0.09, 0.67, 0.24]
#      │
#      ▼  output = [0.0, 0.0], then for each word:
#   ┌─▶ output += weight × vector       the: + [0.09, 0.0 ]
#   │      │                            cat: + [0.0 , 0.67]
#   │      ▼                            sat: + [0.24, 0.12]
#   │   more words? ── yes ──┐
#   └────────────────────────┘
#          │ no
#          ▼
#   output = [0.33, 0.79]     return (scores, weights, output)
#
#   The words list decides what a word may see. Passing only ["the", "cat"]
#   for "cat" IS the causal mask: "sat" is not in the list, so it gets no weight.
def attention(query, words):
    scores = [dot(query, VECTORS[w]) for w in words]
    weights = softmax(scores)
    output = [0.0, 0.0]
    for weight, w in zip(weights, words):
        for i in range(2):
            output[i] += weight * VECTORS[w][i]
    return scores, weights, output


# ----------------------------------------------------------------------------
# STEP 4: COST = why long prompts are slow and context has a limit
# ----------------------------------------------------------------------------
#   writing word t = 1, 2, 3, ... n:
#
#   ┌─▶ use_cache? ── yes ──▶ work += t (only the new word looks at t words) ─┐
#   │      │ no                                                               │
#   │      ▼                                                                  │
#   │   work += t × t                    (redo all t words from zero)         │
#   │      │ ◀────────────────────────────────────────────────────────────────┘
#   │      ▼
#   │   t < n? ── yes ──┐  (t = t + 1)
#   └───────────────────┘
#          │ no
#          ▼  return work
#
#   n = 10:   KV cache 1+2+...+10 = 55        no cache 1+4+...+100 = 385
#   n = 100:  KV cache 5,050                  no cache 338,350
#   n = 1000: KV cache 500,500                no cache 333,833,500
def attention_work(n_words, use_cache):
    """Count how many word-to-word comparisons are needed to write n_words."""
    work = 0
    for t in range(1, n_words + 1):
        if use_cache:
            work += t                 # only the NEW word looks at the t old words
        else:
            work += t * t             # all t words are computed again from zero
    return work


def main():
    print("STEP 1: dot product scores for the word 'sat'")
    scores, weights, output = attention(QUERY_FOR_SAT, WORDS)
    for w, s in zip(WORDS, scores):
        print(f"  {QUERY_FOR_SAT} . {VECTORS[w]} = {s:.2f}   ({w})")

    print("\nSTEP 2: softmax -> attention weights (they sum to 1)")
    exps = [math.exp(s) for s in scores]
    print("  exp(score):", "  ".join(f"{w}={e:.2f}" for w, e in zip(WORDS, exps)),
          f"  total={sum(exps):.2f}")
    for w, p in zip(WORDS, weights):
        print(f"  {w:<4} {p:.2f}  {'#' * round(p * 30)}")
    print(f"  sum = {sum(weights):.2f}.  'sat' looks most at 'cat' (the one who sat).")

    print("\nSTEP 3: weighted sum -> the new vector for 'sat'")
    for w, p in zip(WORDS, weights):
        part = [round(p * x, 2) for x in VECTORS[w]]
        print(f"  {p:.2f} x {VECTORS[w]} = {part}   ({w})")
    print(f"  output = {[round(x, 2) for x in output]}")
    print("  'sat' now carries information about 'cat'. That is how words share meaning.")
    print("  Causal mask: 'cat' may look at 'the', but NOT at 'sat' (the future).")
    # 'cat' asks a neutral question [1, 1]; it only gets the words up to itself
    s_cat, w_cat, _ = attention([1.0, 1.0], ["the", "cat"])
    print(f"  scores  for 'cat' over ['the', 'cat'] = {s_cat}")
    print(f"  weights for 'cat' over ['the', 'cat'] = {[round(x, 2) for x in w_cat]}")

    print("\nSTEP 4: cost of writing N words (comparisons)")
    print(f"  {'N words':>8} {'no cache':>14} {'KV cache':>12}")
    for n in [10, 100, 1000]:
        print(f"  {n:>8} {attention_work(n, False):>14,} {attention_work(n, True):>12,}")
    print("  10x more words -> about 100x more work with the cache (n squared),")
    print("  and much more without it. This is why context windows have a limit.")


if __name__ == "__main__":
    main()

# Remember:
#   - Attention = dot product -> softmax -> weighted sum. That is all.
#   - Words only look back. The KV cache saves old work.
#   - Long prompts cost more (n squared). Put important facts at the start or end.
# Try: change QUERY_FOR_SAT to [2.0, 0.0]. Which word does 'sat' look at now?
