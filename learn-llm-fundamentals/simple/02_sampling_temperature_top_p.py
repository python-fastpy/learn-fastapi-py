"""02 -- Sampling: temperature and top_p  (simple version)
=========================================================

IN ONE LINE:
  The model gives a score to every possible next word. Temperature and
  top_p decide how we PICK one word from those scores.

REAL USE CASE:
  Your FastAPI app has two endpoints. /extract must give the same JSON
  every time. /slogan should be creative. Same model, different settings:

     scores from model
          │
          ▼
     ┌────────────────┐   ÷ temperature   (low = safe, high = creative)
     │    softmax     │ ──▶ probabilities
     └────────────────┘
          │  top_p: keep only the top words that add up to p
          ▼
     pick one word at random (by its probability)

     /extract  ->  temperature=0      (always the top word)
     /slogan   ->  temperature=1.0, top_p=0.9

WHAT AN ENGINEER MUST KNOW:
  1. The model does not change. These settings only change how a word is picked.
  2. temperature 0 = always the most likely word. Use it for facts, JSON, code.
  3. Higher temperature = more random. Too high = nonsense.
  4. top_p cuts off the long tail of bad words. Change temperature OR top_p, not both.
  5. max_tokens and stop sequences decide when the loop ends.

Run:  uv run python simple/02_sampling_temperature_top_p.py
"""

import math
import random

# Made-up model scores ("logits") for the next word after "The weather today is".
SCORES = {"sunny": 3.2, "cloudy": 2.6, "rainy": 2.1, "cold": 1.5, "purple": -1.0}


# ----------------------------------------------------------------------------
# STEP 1: SOFTMAX = turn scores into probabilities (temperature goes here)
# ----------------------------------------------------------------------------
def softmax(scores, temperature):
    """Divide each score by temperature, then make them add up to 1."""
    if temperature == 0:                     # special case: just take the best word
        best = max(scores, key=scores.get)
        return {word: (1.0 if word == best else 0.0) for word in scores}
    powered = {word: math.exp(score / temperature) for word, score in scores.items()}
    total = sum(powered.values())
    return {word: value / total for word, value in powered.items()}


# ----------------------------------------------------------------------------
# STEP 2: TOP_P = keep the most likely words until they add up to p
# ----------------------------------------------------------------------------
def top_p_filter(probs, p):
    kept = {}
    running_total = 0.0
    for word in sorted(probs, key=probs.get, reverse=True):   # best word first
        kept[word] = probs[word]
        running_total += probs[word]
        if running_total >= p:               # we have enough, cut the rest
            break
    total = sum(kept.values())
    return {word: value / total for word, value in kept.items()}   # add up to 1 again


# ----------------------------------------------------------------------------
# STEP 3: PICK = choose one word at random, using the probabilities as weights
# ----------------------------------------------------------------------------
def pick(probs, rng):
    return rng.choices(list(probs), weights=list(probs.values()))[0]


def rounded(probs):
    """Round to 2 decimals so the output is easy to read."""
    return {word: round(value, 2) for word, value in probs.items()}


def main():
    print("STEP 1: scores -> probabilities, at different temperatures")
    for temperature in [0, 0.5, 1.0, 2.0]:
        print("  T =", temperature, ":", rounded(softmax(SCORES, temperature)))
    print("  Low T: the top word wins. High T: all words get closer.")

    print("\nSTEP 2: top_p = 0.9 cuts the unlikely words")
    probs = softmax(SCORES, 1.0)
    print("  before:", rounded(probs))
    print("  after: ", rounded(top_p_filter(probs, 0.9)))
    print("  'cold' and 'purple' are gone. They can never be picked now.")

    print("\nSTEP 3: pick 10 words with each setting")
    rng = random.Random(0)                   # fixed seed so the output is repeatable
    for temperature in [0, 1.0, 2.0]:
        probs = softmax(SCORES, temperature)
        words = [pick(probs, rng) for _ in range(10)]
        print("  T =", temperature, ":", " ".join(words))

    print("\nSTEP 4: what to set in your app")
    print("  JSON, extraction, code  -> temperature 0")
    print("  normal chat             -> temperature 0.7")
    print("  brainstorm, slogans     -> temperature 1.0, or top_p 0.9")
    # The real SDK call looks like this (we do not call it here):
    #   client.messages.create(
    #       model="claude-...", max_tokens=200, temperature=0,
    #       stop_sequences=["\n\n"], messages=[{"role": "user", "content": "..."}],
    #   )
    print("  max_tokens=200   -> stop after 200 tokens (answer may be cut!)")
    print("  stop_sequences   -> stop when the model writes this text")


if __name__ == "__main__":
    main()

# Remember:
#   - Settings change how a word is PICKED, not what the model knows.
#   - temperature 0 for exact tasks, higher for creative tasks.
#   - top_p removes the long tail of bad words.
# Try: add "banana": -2.5 to SCORES. At which temperature does it start to appear?
