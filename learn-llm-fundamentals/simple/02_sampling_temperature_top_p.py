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

WHERE SAMPLING SITS IN A REAL APP:

  ┌──────────────┐  POST /slogan ┌──────────────────┐  HTTPS   ┌─────────────────────────────┐
  │   Browser    │ ────────────▶ │  YOUR FASTAPI    │ ───────▶ │        LLM PROVIDER         │
  │ "a slogan    │               │  sets the knobs: │ prompt + │  model ──▶ scores (fixed)   │
  │  please"     │               │  temperature=1.0 │ settings │  SAMPLER uses your knobs:   │
  │              │ ◀──────────── │  top_p=0.9       │ ◀─────── │   softmax, top_p, pick      │
  └──────────────┘    slogan     │  max_tokens=200  │  answer  │  repeat for every token     │
                                 └──────────────────┘          └─────────────────────────────┘
  You never change the model. You only change how the sampler picks.

THE PIPELINE -- one pick of one next word:

  ┌──────────────┐  ÷ T   ┌──────────────┐  exp()  ┌──────────────┐  ÷ total  ┌──────────────┐
  │ scores       │ ─────▶ │ scaled       │ ──────▶ │ positive     │ ────────▶ │ probabilities│
  │ sunny 3.2 .. │        │ scores       │         │ numbers      │           │ add up to 1  │
  └──────────────┘        └──────────────┘         └──────────────┘           └──────┬───────┘
  STEP 1 = softmax (these 4 boxes)                                                   │
                                                                                     │
          ┌──────────────────────────────────────────────────────────────────────────┘
          ▼
  ┌──────────────────────┐          ┌──────────────────────┐
  │ top_p: keep the best │ ───────▶ │ pick: roll a random  │ ───▶ one word, e.g. "cloudy"
  │ words until sum >= p │          │ number, see where    │
  │ (STEP 2, optional)   │          │ it lands (STEP 3)    │
  └──────────────────────┘          └──────────────────────┘

ONE FULL RUN, step by step (the real numbers printed at T = 1.0):

   word      score   ÷ T=1.0   exp()     ÷ 51.01   running total   top_p 0.9   after top_p
   ───────   ─────   ───────   ───────   ───────   ─────────────   ─────────   ───────────
   sunny      3.2     3.2      24.53     0.48      0.48            keep        0.53
   cloudy     2.6     2.6      13.46     0.26      0.74            keep        0.29
   rainy      2.1     2.1       8.17     0.16      0.90  >= 0.9    keep, STOP  0.18
   cold       1.5     1.5       4.48     0.09                      cut         -
   purple    -1.0    -1.0       0.37     0.01                      cut         -
                               ──────    ────
                        total  51.01     1.00

   Then pick: the first 3 picks at T = 1.0 roll 0.91, 0.50, 0.28
   ──▶ cold, cloudy, sunny   (see STEP 3 for how a roll becomes a word)

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
#   scores = {sunny: 3.2, cloudy: 2.6, rainy: 2.1, cold: 1.5, purple: -1.0}
#      │
#      ▼
#   temperature == 0? ── yes ──▶ best word gets 1.0, all others 0.0   (sunny: 1.0)
#      │ no
#      ▼  divide every score by T, then exp() makes it positive
#
#      word        T = 0.5           T = 1.0           T = 2.0
#                  exp(score÷T)      exp(score÷T)      exp(score÷T)
#      sunny       601.85            24.53             4.95
#      cloudy      181.27            13.46             3.67
#      ...         ...               ...               ...
#      purple        0.14             0.37             0.61
#      total       870.02            51.01             14.2
#      │
#      ▼  divide each by the total, so they add up to 1
#      sunny       0.69              0.48              0.35
#      cloudy      0.21              0.26              0.26
#      ...         ...               ...               ...
#      purple      0.0               0.01              0.04
#
#   Small T makes big scores HUGE (601.85 vs 0.14): the top word wins.
#   Big T makes all scores close (4.95 vs 0.61): more words get a chance.
def softmax(scores, temperature, show_steps=False):
    """Divide each score by temperature, then make them add up to 1."""
    if temperature == 0:                     # special case: just take the best word
        best = max(scores, key=scores.get)
        return {word: (1.0 if word == best else 0.0) for word in scores}
    powered = {word: math.exp(score / temperature) for word, score in scores.items()}
    total = sum(powered.values())
    if show_steps:
        for word, score in scores.items():
            print(f"    {word:<7} score {score:>4}  ÷T {score / temperature:>5.2f}"
                  f"  exp {powered[word]:>6.2f}  ÷total -> {powered[word] / total:.2f}")
        print(f"    total of exp() = {total:.2f}")
    return {word: value / total for word, value in powered.items()}


# ----------------------------------------------------------------------------
# STEP 2: TOP_P = keep the most likely words until they add up to p
# ----------------------------------------------------------------------------
#   probs (T = 1.0) = {sunny 0.48, cloudy 0.26, rainy 0.16, cold 0.09, purple 0.01}
#      │
#      ▼  sort, best word first
#   ┌─▶ take the next word, add it to kept, add its prob to running_total
#   │      sunny  ──▶ running_total 0.48
#   │      cloudy ──▶ running_total 0.74
#   │      rainy  ──▶ running_total 0.90
#   │      │
#   │      ▼
#   │   running_total >= p (0.9)? ── yes ──▶ STOP (cold and purple are cut)
#   │      │ no
#   └──────┘
#      │
#      ▼  divide by the new total (0.90), so they add up to 1 again
#   {sunny 0.53, cloudy 0.29, rainy 0.18}
def top_p_filter(probs, p, show_steps=False):
    kept = {}
    running_total = 0.0
    for word in sorted(probs, key=probs.get, reverse=True):   # best word first
        kept[word] = probs[word]
        running_total += probs[word]
        if show_steps:
            print(f"    keep {word:<7} running total {running_total:.2f}")
        if running_total >= p:               # we have enough, cut the rest
            break
    total = sum(kept.values())
    return {word: value / total for word, value in kept.items()}   # add up to 1 again


# ----------------------------------------------------------------------------
# STEP 3: PICK = choose one word at random, using the probabilities as weights
# ----------------------------------------------------------------------------
#   Put the words on a line from 0 to 1. Each word gets a part as wide as its prob.
#
#   T = 1.0:
#   0        0.48       0.74     0.90   0.99 1
#   ├─ sunny ──┼─ cloudy ─┼─ rainy ─┼─cold─┼┤ purple
#
#   roll = rng.random()   (a random number between 0 and 1)
#      │
#      ▼
#   ┌─▶ next word: add its prob to running_total
#   │      │
#   │      ▼
#   │   roll < running_total? ── yes ──▶ this is the word, END
#   │      │ no
#   └──────┘
#
#   real rolls from this run (T = 1.0):
#      roll 0.91  ──▶ after sunny 0.48, cloudy 0.74, rainy 0.90 -- no;  cold 0.99 -- yes ──▶ cold
#      roll 0.50  ──▶ after sunny 0.48 -- no;  cloudy 0.74 -- yes                       ──▶ cloudy
#      roll 0.28  ──▶ sunny 0.48 -- yes                                                 ──▶ sunny
#   (This is exactly what rng.choices(words, weights=probs) does inside.)
def pick(probs, rng, show_steps=False):
    roll = rng.random() * sum(probs.values())       # a random point on the line
    running_total = 0.0
    for word, probability in probs.items():
        running_total += probability
        if roll < running_total:                     # the roll lands in this word's part
            break
    if show_steps:
        print(f"    roll {roll:.2f} -> lands in {word!r} (its part ends at {running_total:.2f})")
    return word


def rounded(probs):
    """Round to 2 decimals so the output is easy to read."""
    return {word: round(value, 2) for word, value in probs.items()}


def main():
    print("STEP 1: scores -> probabilities, at different temperatures")
    for temperature in [0, 0.5, 1.0, 2.0]:
        print("  T =", temperature, ":", rounded(softmax(SCORES, temperature)))
        if temperature > 0:                  # show the exp() numbers behind it
            powered = [math.exp(score / temperature) for score in SCORES.values()]
            print("          exp():", [round(value, 2) for value in powered],
                  "total", round(sum(powered), 2))
    print("  Low T: the top word wins. High T: all words get closer.")
    print("  softmax at T = 1.0, step by step:")
    softmax(SCORES, 1.0, show_steps=True)

    print("\nSTEP 2: top_p = 0.9 cuts the unlikely words")
    probs = softmax(SCORES, 1.0)
    print("  before:", rounded(probs))
    filtered = top_p_filter(probs, 0.9, show_steps=True)
    print("  after: ", rounded(filtered))
    print("  'cold' and 'purple' are gone. They can never be picked now.")

    print("\nSTEP 3: pick 10 words with each setting")
    rng = random.Random(0)                   # fixed seed so the output is repeatable
    for temperature in [0, 1.0, 2.0]:
        probs = softmax(SCORES, temperature)
        if temperature == 1.0:
            print("  T = 1.0 : the first 3 picks, explained:")
        words = [pick(probs, rng, show_steps=(temperature == 1.0 and n < 3)) for n in range(10)]
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
