"""Lesson 01 -- What an LLM actually is: tokens in, next-token probabilities out
================================================================================

WHY THIS MATTERS:
  Every confusing thing about LLMs -- hallucinations, token limits, why
  they "forget", why the same prompt gives different answers -- follows
  from ONE fact:

      An LLM is a function that takes a sequence of tokens and returns a
      probability for every possible NEXT token. That's all it computes.

  Chatting, coding, tool calling and "reasoning" are all built by calling
  that function in a loop. This lesson builds a (tiny, honest) language
  model from scratch so you can watch each step happen.

WHAT YOU'LL LEARN:
  1. Tokenization -- text becomes integer IDs, and a token is NOT a word
  2. The model's one job: P(next token | all tokens so far)
  3. "Training" = adjusting the model so real text gets high probability
  4. Generation is a loop: predict -> pick one -> append -> repeat
  5. Why hallucination is built in: the model produces PLAUSIBLE
     continuations, not VERIFIED ones
  6. Why more context helps: a model that sees 2 words beats one that
     sees 1 -- and real models see hundreds of thousands

Concepts:
  - Token: a chunk of text (word, sub-word, or punctuation) with an int ID
  - Vocabulary: every token the model knows (real models: ~100k-200k)
  - Context window: the max tokens the model can look at in one call
  - Logits / probabilities: the model's score for each possible next token
  - Autoregressive: each new token is fed back in as input for the next

Flow:
   "The cat sat"                                       (your text)
        |  tokenizer
        v
   [464, 3797, 3332]                                   (token IDs)
        |  model (billions of learned numbers)
        v
   { " on": 0.61, " down": 0.22, " there": 0.05, ... } (one prob per vocab token)
        |  sampling (lesson 02: temperature / top_p)
        v
   " on"  --> append --> [464, 3797, 3332, 319] --> run the model again ...

TRAINING vs INFERENCE (two separate phases):
   TRAINING (once, offline)               INFERENCE (every API call)
   ┌──────────────────────────┐          ┌──────────────────────────────┐
   │ huge text corpus         │          │ your prompt tokens           │
   │   ▼                      │          │   ▼                          │
   │ count / adjust weights   │ weights  │ look up P(next | context)    │
   │ so real text gets high P ├─frozen──▶│   ▼                          │
   │ (here: NgramModel counts)│          │ sample 1 token, append, loop │
   └──────────────────────────┘          └──────────────────────────────┘
   Weights never change at inference -- only the context does.

PREREQUISITES: None. Pure Python, no packages, no credentials.

Run:  uv run python 01_what_is_an_llm.py      (or just: python 01_what_is_an_llm.py)
"""

import math
import random
from collections import Counter, defaultdict


# ============================================================================
# PART 1: Tokenization -- text is turned into integer IDs
# ============================================================================
# Models never see characters or words. A tokenizer splits text into
# pieces from a fixed vocabulary and maps each piece to an integer.
#
# Real tokenizers (BPE, SentencePiece) learn their vocabulary from data:
# common words get one token, rare words are split into pieces. The toy
# below uses greedy longest-match over a hand-written vocabulary -- the
# mechanism real tokenizers use at inference time is close to this.
#
# TEXT -> TOKENS -> IDS  (real output of part 1 for "The cat sat on the mat.")
#   "The cat sat on the mat."
#        │  tokenize()
#        ▼
#   tokens │ "The"  │ " cat" │ " sat" │ " on"  │ " the" │ " mat" │ "."
#        │  TOKEN_TO_ID (index in TOY_VOCAB)
#        ▼
#   ids    │ 9      │ 1      │ 2      │ 3      │ 0      │ 4      │ 23
#   6 words ──▶ 7 tokens   (the space rides on the FRONT of each word)

TOY_VOCAB = [
    # common whole words (with a leading space, like real tokenizers)
    " the", " cat", " sat", " on", " mat", " is", " not", " a", " and",
    "The", " dog", " un",
    # sub-word pieces
    "believ", "able", "happi", "ness", "token", "ization", " token",
    "ing", "s", "ed", "er",
    # punctuation / fallback single characters
    ".", ",", "!", "?", " ",
] + [chr(c) for c in range(ord("a"), ord("z") + 1)]

TOKEN_TO_ID = {tok: i for i, tok in enumerate(TOY_VOCAB)}

# GREEDY LONGEST-MATCH, STEP BY STEP: " unbelievable"
#   i=0  " unbelievable"  longest vocab prefix ──▶ " un"     (id 11)  i=3
#   i=3     "believable"  longest vocab prefix ──▶ "believ"  (id 12)  i=9
#   i=9           "able"  longest vocab prefix ──▶ "able"    (id 13)  i=13 end
#   no entry matches at i? ──▶ emit that 1 raw char (TOKEN_TO_ID gives -1)

def tokenize(text: str) -> list[str]:
    """Greedy longest-match: at each position take the longest vocab entry."""
    tokens, i = [], 0
    by_length = sorted(TOY_VOCAB, key=len, reverse=True)
    while i < len(text):
        for tok in by_length:
            if text.startswith(tok, i):
                tokens.append(tok)
                i += len(tok)
                break
        else:
            tokens.append(text[i])   # unknown char -> real tokenizers fall back to bytes
            i += 1
    return tokens


def part1_tokenization():
    print("######## PART 1 -- Tokenization ########\n")
    for text in ["The cat sat on the mat.", " unbelievable", " unhappiness",
                 " tokenization", "The dog is not a cat!"]:
        toks = tokenize(text)
        ids = [TOKEN_TO_ID.get(t, -1) for t in toks]
        words = len(text.split())
        print(f"  {text!r}")
        print(f"    tokens : {toks}")
        print(f"    ids    : {ids}")
        print(f"    {words} word(s) -> {len(toks)} tokens\n")

    print("  Takeaways:")
    print("   - A token is NOT a word. Rare words split into pieces; spaces are")
    print("     usually glued to the FRONT of the next word (' cat').")
    print("   - Rule of thumb for English: 1 token ~ 4 characters ~ 0.75 words.")
    print("     Code, JSON, numbers and non-English text use MORE tokens.")
    print("   - Everything is billed and limited in tokens: price, context")
    print("     window, max_tokens. That's why tokens matter to an engineer.")
    print("   - Why LLMs are bad at 'count the r's in strawberry': they see")
    print("     tokens like ['str', 'awberry'], not letters.\n")
    print("  Every case (spaces, capitals, numbers, code, emoji, other languages),")
    print("  with a real BPE tokenizer trained from scratch: 01b_tokens_in_depth.py\n")


# ============================================================================
# PART 2: The model -- P(next token | previous tokens)
# ============================================================================
# A real LLM is a transformer with billions of weights. But its INTERFACE
# is exactly this: give it the tokens so far, get back a probability for
# every token in the vocabulary.
#
# We'll build the simplest possible language model: count which word
# follows which in some training text. "Training" is just counting here;
# in a real LLM it's gradient descent over trillions of tokens -- but the
# goal is identical: make real text get high probability.
#
# THE NEXT-TOKEN TABLE = COUNTS ÷ TOTAL  (bigram, context "the", 10 examples)
#   context ("the",) ──▶ counts ──▶ P(next)
#     capital   4  ──▶ 0.40 ████████░░░░░░░░░░░░
#     cat       2  ──▶ 0.20 ████░░░░░░░░░░░░░░░░
#     mat       2  ──▶ 0.20 ████░░░░░░░░░░░░░░░░
#     dog       1  ──▶ 0.10 ██░░░░░░░░░░░░░░░░░░
#     rug       1  ──▶ 0.10 ██░░░░░░░░░░░░░░░░░░
#                       └─ sums to 1.00: ONE distribution, not one answer

TRAINING_TEXT = """
paris is the capital of france .
rome is the capital of italy .
berlin is the capital of germany .
the capital of france is paris .
the cat sat on the mat .
the dog sat on the rug .
the cat is on the mat .
paris is a beautiful city .
rome is a beautiful city .
"""


# TRAINING = COUNTING  (NgramModel.__init__, n=2)
#   "rome is the capital of italy ."
#     │  pad with <s> / </s>, slide a window of n words
#     ▼
#   <s>│rome rome│is is│the the│capital capital│of of│italy italy│. .│</s>
#     │  counts[context][next] += 1   (for every line of TRAINING_TEXT)
#     ▼
#   counts[("of",)]  = {france: 2, italy: 1, germany: 1}
#   counts[("the",)] = {capital: 4, cat: 2, mat: 2, dog: 1, rug: 1}
#   next_token_probs(): last n-1 tokens ──▶ counts ÷ total (unseen ──▶ </s>)
#   Real LLM: same goal, but gradient descent ADJUSTS weights instead of +1.
class NgramModel:
    """Predicts the next word from the previous `n-1` words by counting.

    n=2 (bigram) sees 1 previous word. n=3 (trigram) sees 2. A real LLM
    sees the whole context window -- that's the headline difference.
    """

    def __init__(self, text: str, n: int = 2):
        self.n = n
        self.counts: dict[tuple, Counter] = defaultdict(Counter)
        for line in text.strip().splitlines():
            words = ["<s>"] * (n - 1) + line.split() + ["</s>"]
            for i in range(n - 1, len(words)):
                context = tuple(words[i - n + 1:i])
                self.counts[context][words[i]] += 1

    def next_token_probs(self, tokens: list[str]) -> dict[str, float]:
        """THE core LLM operation: tokens so far -> distribution over next token."""
        padded = ["<s>"] * (self.n - 1) + tokens
        context = tuple(padded[len(padded) - self.n + 1:])
        counts = self.counts.get(context)
        if not counts:
            return {"</s>": 1.0}
        total = sum(counts.values())
        return {tok: c / total for tok, c in counts.most_common()}


def bar(p: float, width: int = 30) -> str:
    return "#" * round(p * width)


def part2_next_token():
    print("######## PART 2 -- The model predicts ONE next token ########\n")
    model = NgramModel(TRAINING_TEXT, n=2)

    for prompt in ["the", "the capital of", "paris is"]:
        probs = model.next_token_probs(prompt.split())
        print(f"  P(next | {prompt!r})")
        for tok, p in list(probs.items())[:5]:
            print(f"    {tok:<10} {p:5.2f}  {bar(p)}")
        print()

    print("  The model never outputs a sentence -- only this table of")
    print("  probabilities. A real LLM outputs one such table over its whole")
    print("  ~100k-token vocabulary, every single step.\n")


# ============================================================================
# PART 3: Generation -- call the model in a loop
# ============================================================================
# To produce text: predict, pick one token, append it, predict again.
# "Pick one" is where temperature and top_p come in (lesson 02). Here we
# use plain sampling in proportion to probability.
#
# THE GENERATE LOOP  (generate())
#   tokens = prompt.split()
#   ┌──▶ predict: probs = model.next_token_probs(tokens)
#   │      ▼
#   │    sample:  nxt = rng.choices(choices, weights=weights)
#   │      ▼
#   │    nxt == "</s>" ? ──yes──▶ STOP (model chose to end)
#   │      │ no
#   │      ▼
#   │    append:  tokens.append(nxt)
#   │      ▼
#   │    steps left (< max_tokens)? ──no──▶ STOP (cut off)
#   │      │ yes
#   └──────┘
#
# THE REAL RUN BELOW  (seed 3; every arrow = one full model call)
#   [rome is] ─1▶ the ─2▶ cat ─3▶ sat ─4▶ on ─5▶ the ─6▶ capital ─7▶ of
#             ─8▶ germany ─9▶ . ─10▶ </s> = STOP
#   step 8 had 3 options (france .50 / italy .25 / germany .25): dice -> germany

def generate(model: NgramModel, prompt: str, max_tokens: int = 12,
             rng: random.Random | None = None, verbose: bool = False) -> str:
    rng = rng or random.Random(0)
    tokens = prompt.split()
    for step in range(1, max_tokens + 1):
        probs = model.next_token_probs(tokens)
        choices, weights = zip(*probs.items())
        nxt = rng.choices(choices, weights=weights)[0]
        if verbose:
            top = ", ".join(f"{t}:{p:.2f}" for t, p in list(probs.items())[:3])
            print(f"    step {step:>2}: context={' '.join(tokens[-3:])!r:<28} "
                  f"top=[{top}]  -> picked {nxt!r}")
        if nxt == "</s>":            # end-of-sequence token = "I'm done"
            break
        tokens.append(nxt)
    return " ".join(tokens)


def part3_generation():
    print("######## PART 3 -- Generation is a loop ########\n")
    model = NgramModel(TRAINING_TEXT, n=2)
    print("  generate('rome is'):")
    out = generate(model, "rome is", rng=random.Random(3), verbose=True)
    print(f"\n  result: {out!r}\n")
    print("  Each step is a SEPARATE forward pass of the model. That's why")
    print("  output tokens are slower and pricier than input tokens: input is")
    print("  processed in one parallel pass, output is produced one at a time.\n")


# ============================================================================
# PART 4: Hallucination is built in
# ============================================================================
# The model was trained on TRUE sentences only. Watch it produce false ones.
# Each step is locally plausible ("of" -> "italy" is a real pattern), but
# nothing checks the whole sentence against reality.
#
# PLAUSIBLE PATHS vs THE TRUE PATH  (bigram, prompt "paris is the capital")
#   capital ─1.00▶ of ─┬─0.50▶ france ─┬─0.50▶ .  ──▶ TRUE (the only one)
#                      │               └─0.50▶ is ─▶ a / the / ... ──▶ FALSE
#                      ├─0.25▶ italy   ─1.00▶ .   ──▶ FALSE
#                      └─0.25▶ germany ─1.00▶ .   ──▶ FALSE
#   P(true) = 0.50 × 0.50 = 0.25 ──▶ ~50 of 200 expected (40 in the run below)
#   every single step is locally plausible; only the whole path is wrong

def part4_hallucination():
    print("######## PART 4 -- Why LLMs hallucinate ########\n")
    bigram = NgramModel(TRAINING_TEXT, n=2)
    seen = set(TRAINING_TEXT.split("\n"))
    results = Counter(generate(bigram, "paris is the capital", rng=random.Random(s))
                      for s in range(200))

    print("  Training data only ever says 'paris is the capital of france'.")
    print("  200 generations from 'paris is the capital' with a BIGRAM model:\n")
    for text, n in results.most_common(5):
        tag = "TRUE (in training data)" if text + " ." in seen or text in seen \
            else "FALSE -- hallucinated"
        print(f"    {n:>3}x  {text!r:<45} {tag}")

    print("\n  The model has no fact database. It only knows 'after \"of\", the")
    print("  words france / italy / germany are all likely'. Fluent + wrong")
    print("  is the natural failure mode of next-token prediction.\n")


# ============================================================================
# PART 5: More context = better predictions
# ============================================================================
# MORE CONTEXT = NARROWER DISTRIBUTION  (P(next) right after "...capital of")
#   prompt:  paris  is  the  capital  of  ▶ ?
#   2-gram sees                       [of]
#   4-gram sees           [the  capital  of]
#   6-gram sees [paris  is  the  capital  of]
#
#   model   france                     italy       germany     wrong/200
#   2-gram  ██████████░░░░░░░░░░ .50   █████ .25   █████ .25      111
#   4-gram  ██████████░░░░░░░░░░ .50   █████ .25   █████ .25      104
#   6-gram  ████████████████████ 1.00  ░ 0         ░ 0              0
#   only a window that reaches back to "paris" collapses it to the true answer

def part5_more_context():
    print("######## PART 5 -- More context, fewer mistakes ########\n")
    for n, label in [(2, "2-gram (sees 1 word) "), (4, "4-gram (sees 3 words)"),
                     (6, "6-gram (sees 5 words)")]:
        model = NgramModel(TRAINING_TEXT, n=n)
        outs = [generate(model, "paris is the capital", rng=random.Random(s))
                for s in range(200)]
        wrong = sum("italy" in o or "germany" in o for o in outs)
        print(f"  {label}: {wrong:>3}/200 generations wrong")

    print("\n  When it predicts the word after 'of', only the 6-gram can still see")
    print("  'paris' (5 words back) -- so only it gets the answer right. The")
    print("  4-gram sees 'is the capital of', which fits all three countries.")
    print("\n  Seeing far enough back is what fixes the answer. A real LLM")
    print("  uses ATTENTION to look back across its entire context window")
    print("  (hundreds of thousands of tokens) -- which is why putting the")
    print("  RIGHT information in the context is the #1 lever you control.")
    print("  That's context engineering (lesson 04).\n")


# ============================================================================
# Demo
# ============================================================================

def main():
    part1_tokenization()
    part2_next_token()
    part3_generation()
    part4_hallucination()
    part5_more_context()

    print("######## Summary ########\n")
    print("  text --tokenizer--> ids --model--> P(next) --sample--> 1 token")
    print("        ^                                                   |")
    print("        +-------------------- append, repeat ---------------+")
    print()
    print("  Everything else -- chat, tools, agents -- is this loop plus")
    print("  careful choices about WHAT tokens go in (the context).")


if __name__ == "__main__":
    main()

    # -- Key takeaway --------------------------------------------------------
    # An LLM is a next-token probability function called in a loop.
    #   - It knows only what was in training data + what's in the context now.
    #   - It has no memory between calls; the context IS its working memory.
    #   - It's fluent by construction and correct only when the context or
    #     training strongly supports the right answer.
    # A real LLM differs from our n-gram in SCALE and ARCHITECTURE (a
    # transformer with attention over the whole context, billions of
    # weights, trained on trillions of tokens, then instruction-tuned to be
    # a helpful assistant) -- not in its interface.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Add "madrid is the capital of spain ." to TRAINING_TEXT and re-run
    #    part 4 -- more training data spreads probability even thinner.
    # 2. Tokenize a JSON string like '{"a": 1}' and a sentence of the same
    #    length. Which uses more tokens?
    # 3. Give generate() a max_tokens=3 and see a truncated output -- the
    #    same thing as an API reply with stop_reason "max_tokens"/"length".
