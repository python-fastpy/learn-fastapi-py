"""01 -- What is an LLM?  (simple version)
==========================================

IN ONE LINE:
  An LLM is a function: give it some words, it guesses the NEXT word.
  It does this again and again in a loop to write a whole answer.

REAL USE CASE:
  Your FastAPI chatbot sends "The capital of France is" to the model.
  The model does NOT look up an answer. It guesses one word at a time.

  ┌──────────────┐  POST /chat   ┌──────────────────┐  HTTPS   ┌─────────────────────────────┐
  │   Browser    │ ────────────▶ │  YOUR FASTAPI    │ ───────▶ │        LLM PROVIDER         │
  │ "capital of  │               │  builds prompt,  │          │                             │
  │  France?"    │ ◀──────────── │  returns JSON    │ ◀─────── │  loop:  predict 1 word      │
  └──────────────┘   "Paris"     └──────────────────┘  answer  │         pick 1 word         │
                                                               │         add it, repeat      │
                                                               └─────────────────────────────┘

TWO PHASES -- learn once, then use many times:

  TRAINING (once, before you ever call it)       USING IT (every API call)
  ┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
  │ lots of text                         │       │ your prompt                          │
  │   │                                  │       │   │                                  │
  │   ▼                                  │       │   ▼                                  │
  │ count: which word follows which?     │ ────▶ │ predict: P(next word)                │
  │   (STEP 1 in the code)               │ model │   (STEP 2)                           │
  │                                      │ is    │   │                                  │
  │ real LLM: adjusts billions of        │ fixed │   ▼                                  │
  │ numbers instead of counting          │ now   │ pick one, add it, repeat (STEP 3)    │
  └──────────────────────────────────────┘       └──────────────────────────────────────┘
  The model does NOT learn from your chats. Only the prompt changes per call.

ONE FULL GENERATION, step by step (the real run printed by STEP 3, seed 30):

   text so far              model looks at   choices it sees                 picked
   ─────────────────────    ──────────────   ─────────────────────────────   ────────
   paris is                 "is"             the 0.67, a 0.33                the
   paris is the             "the"            capital 0.33, cat 0.17, ...     capital
   paris is the capital     "capital"        of 1.00                         of
   ... capital of           "of"             france 0.50, italy 0.50         italy   ◀── WRONG!
   ... of italy             "italy"          <stop> 1.00                     <stop>  -> done

   Every single step looked fine. The whole sentence is false.
   That is HALLUCINATION: the model writes what is LIKELY, not what is TRUE.

WHAT AN ENGINEER MUST KNOW:
  1. The model only predicts the next word. A full answer = many calls in a loop.
  2. It learned which words usually follow which, from lots of text (training).
  3. It can sound right and still be wrong (hallucination).
  4. Giving it more context (more words to look at) makes its guesses better.

Run:  uv run python simple/01_what_is_an_llm.py
"""

import random

# ----------------------------------------------------------------------------
# STEP 1: TRAINING = learn which word comes after which
# ----------------------------------------------------------------------------
#   "paris is the capital of france"
#      │
#      ▼  look at every pair of neighbours
#   paris→is   is→the   the→capital   capital→of   of→france   france→<stop>
#      │
#      ▼  write each one down in a notebook (a dict)
#   next_words = {
#       "the": ["capital", "capital", "cat", "mat", "dog", "rug"],
#       "of":  ["france", "italy"],
#       ...
#   }
# A real LLM learns from trillions of words. We use 5 sentences.
TRAINING_TEXT = [
    "paris is the capital of france",
    "rome is the capital of italy",
    "paris is a city",
    "the cat sat on the mat",
    "the dog sat on the rug",
]


def train(sentences):
    """For every word, remember which words came right after it."""
    next_words = {}                         # "the" -> ["capital", "capital", "cat", ...]
    for sentence in sentences:
        words = sentence.split() + ["<stop>"]
        for current, following in zip(words, words[1:]):
            next_words.setdefault(current, []).append(following)
    return next_words


# ----------------------------------------------------------------------------
# STEP 2: PREDICT = how likely is each next word?
# ----------------------------------------------------------------------------
#   after "the" the notebook says:  capital capital cat mat dog rug   (6 words)
#
#      word      count    ÷ 6     probability
#      capital     2    ──────▶   0.33  ██████
#      cat         1    ──────▶   0.17  ███
#      dog         1    ──────▶   0.17  ███
#      mat         1    ──────▶   0.17  ███
#      rug         1    ──────▶   0.17  ███
#                                 ────
#                                 1.00   <- always adds up to 1
#
# A real LLM gives such a list for EVERY token it knows (~100,000 of them).
def predict(model, last_word):
    """Return {next_word: probability}. This is the ONLY thing an LLM computes."""
    seen = model.get(last_word, ["<stop>"])
    probs = {word: round(seen.count(word) / len(seen), 2) for word in set(seen)}
    # most likely first; same probability -> alphabetical, so every run prints the same
    return dict(sorted(probs.items(), key=lambda item: (-item[1], item[0])))


# ----------------------------------------------------------------------------
# STEP 3: GENERATE = predict, pick one, add it, repeat
# ----------------------------------------------------------------------------
#   words = ["paris", "is"]
#      │
#      ▼
#   ┌─▶ predict(last word) ──▶ {"the": 0.67, "a": 0.33}
#   │      │
#   │      ▼
#   │   pick one at random, weighted by probability  ──▶ "the"
#   │      │
#   │      ▼
#   │   is it "<stop>"? ── yes ──▶ END (stop_reason = "end_turn")
#   │      │ no
#   │      ▼
#   │   words.append("the")
#   │      │
#   │      ▼
#   │   reached max_words? ── yes ──▶ END (stop_reason = "max_tokens", cut off!)
#   │      │ no
#   └──────┘
def generate(model, prompt, max_words=10, seed=0, show_steps=False):
    rng = random.Random(seed)
    words = prompt.split()
    for _ in range(max_words):              # max_words is like the API's max_tokens
        probs = predict(model, words[-1])
        next_word = rng.choices(list(probs), weights=list(probs.values()))[0]
        if show_steps:
            print(f"    looks at {words[-1]!r:<10} choices {probs}  -> picked {next_word!r}")
        if next_word == "<stop>":           # the model decided it is done
            break
        words.append(next_word)
    return " ".join(words)


def main():
    model = train(TRAINING_TEXT)

    print("STEP 1: what the model learned")
    print("  after 'the' it saw:", model["the"])
    print("  after 'of'  it saw:", model["of"])

    print("\nSTEP 2: predict the next word")
    for word in ["the", "of"]:
        print(f"  after {word!r}: {predict(model, word)}")

    print("\nSTEP 3: generate text, one word per loop (seed 30)")
    result = generate(model, "paris is", seed=30, show_steps=True)
    print("  result:", result)
    print("\n  same prompt, other seeds (other random picks):")
    for seed in [4, 0, 10, 3]:
        print("   ", generate(model, "paris is", seed=seed))

    print("\nSTEP 4: notice the WRONG answer")
    print("  'paris is the capital of italy' sounds fine but is false.")
    print("  The model only looks at the LAST word ('of'), so it can't")
    print("  remember 'paris'. That is hallucination.")
    print("  Real LLMs look at the whole conversation (the context), which is")
    print("  why putting the right info in the prompt matters so much.")


if __name__ == "__main__":
    main()

# Remember:
#   - LLM = next-word predictor in a loop.
#   - It has no fact database; it repeats patterns it saw.
#   - Better context in the prompt = better answers.
# Try: add "berlin is the capital of germany" to TRAINING_TEXT and run again.
