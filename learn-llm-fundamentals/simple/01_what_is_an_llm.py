"""01 -- What is an LLM?  (simple version)
==========================================

IN ONE LINE:
  An LLM is a function: give it some words, it guesses the NEXT word.
  It does this again and again in a loop to write a whole answer.

REAL USE CASE:
  Your FastAPI chatbot sends "The capital of France is" to the model.
  The model does NOT look up an answer. It guesses one word at a time:

     "The capital of France is"
            │
            ▼
     ┌──────────────┐     " Paris"  0.90   <- most likely
     │    MODEL     │ ──▶ " a"      0.06
     └──────────────┘     " not"    0.04
            │
            ▼  pick one word, add it to the text
     "The capital of France is Paris"
            │
            ▼  ask the model AGAIN (loop) ... until it says "stop"

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
# A real LLM learns from trillions of words. We use 4 sentences.
TRAINING_TEXT = [
    "paris is the capital of france",
    "rome is the capital of italy",
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
def predict(model, last_word):
    """Return {next_word: probability}. This is the ONLY thing an LLM computes."""
    seen = model.get(last_word, ["<stop>"])
    probs = {word: round(seen.count(word) / len(seen), 2) for word in set(seen)}
    return dict(sorted(probs.items(), key=lambda item: -item[1]))   # most likely first


# ----------------------------------------------------------------------------
# STEP 3: GENERATE = predict, pick one, add it, repeat
# ----------------------------------------------------------------------------
def generate(model, prompt, max_words=10, seed=0):
    rng = random.Random(seed)
    words = prompt.split()
    for _ in range(max_words):              # max_words is like the API's max_tokens
        probs = predict(model, words[-1])
        next_word = rng.choices(list(probs), weights=list(probs.values()))[0]
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

    print("\nSTEP 3: generate text (a loop of predictions)")
    for seed in range(4):
        print("  ", generate(model, "paris is", seed=seed))

    print("\nSTEP 4: notice the WRONG answers")
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
