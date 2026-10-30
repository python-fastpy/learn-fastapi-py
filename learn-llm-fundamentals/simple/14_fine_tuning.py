"""14 -- Fine-tuning  (simple version)
=====================================

IN ONE LINE:
  Fine-tuning = keep training an existing model on YOUR examples,
  so its default behaviour changes (no long prompt needed).

REAL USE CASE:
  Your support bot answers in the wrong style. You collect a few hundred
  good (question, ideal answer) pairs and train on them:

     your examples (chat JSONL)
          │  clean: remove bad rows and duplicates
          ▼
     split ──▶ TRAIN (75%)          VALIDATION (25%, never trained on)
          ▼
     [ TRAINING LOOP: predict -> loss -> nudge weights -> repeat ]
          │  stop when validation stops getting better
          ▼
     fine-tuned model (or a small LoRA "adapter" file)

WHERE IT SITS IN A REAL APP (training is offline, once; the app only USES the result):

  OFFLINE (once, on a GPU box or provider)         ONLINE (every request)
  ┌──────────────────────────────────────┐        ┌──────────────┐ POST /chat ┌──────────────────┐
  │ JSONL ──▶ clean ──▶ train loop       │        │   Browser    │ ─────────▶ │  YOUR FASTAPI    │
  │                        │             │        └──────────────┘            └──────────────────┘
  │                        ▼             │                                             │
  │          base model + LoRA adapter   │                                             ▼
  └──────────────────────────────────────┘                                    ┌──────────────────┐
                 │                                                            │ base model +     │
                 └──────────────── deploy the adapter file ─────────────────▶ │ YOUR adapter     │
                                                                              └──────────────────┘
  The app code does not change. Only the model name / adapter changes.

THE TRAINING LOOP (STEP 2 in the code), for every example, every epoch:

  ┌───────────────┐    ┌───────────────┐    ┌──────────────────┐    ┌───────────────────┐
  │ 1. FORWARD    │    │ 2. LOSS       │    │ 3. GRADIENT      │    │ 4. UPDATE         │
  │ text ──▶      │──▶ │ -log(p of the │──▶ │ probs - target   │──▶ │ score -= 0.5 x    │
  │ probs per     │    │ right reply)  │    │ (which way is    │    │ gradient          │
  │ reply         │    │ low = good    │    │  "more right"?)  │    │ (a small nudge)   │
  └───────────────┘    └───────────────┘    └──────────────────┘    └───────────────────┘
          ▲                                                                   │
          └──────────────────────── next example / next epoch ◀───────────────┘

ONE TRAINING RUN, step by step (the real run printed by STEP 2, 6 rows, learning rate 0.5):

   epoch   avg loss   bar                            p("order ships") for "where is my package"
   ─────   ────────   ────────────────────────────   ─────────────────────────────────────────
   start      -       -                              0.33   (3 replies, a pure guess)
     1      1.29      ##########################
     2      0.43      #########
     3      0.20      ####
     4      0.13      ###
     5      0.10      ##
     6      0.08      ##
     7      0.07      #
     8      0.06      #                              0.96   ◀── right reply, and sure

   Loss falls fast, then flattens. On real data you also watch VALIDATION loss.
   If train loss still falls but validation loss goes UP: stop. That is overfitting.

WHAT AN ENGINEER MUST KNOW:
  1. Try prompting and RAG first. Fine-tune last, for a narrow, stable task.
  2. The model copies your data, mistakes included. 50 clean rows beat 500 bad ones.
  3. Keep a validation set. If train loss goes down but validation goes up,
     the model is memorising (overfitting). Stop early.
  4. Fine-tuning teaches style and format. It is bad at teaching facts
     that change. Use RAG for facts.
  5. LoRA trains a tiny extra matrix instead of all weights: cheap and swappable.

Run:  uv run python simple/14_fine_tuning.py
"""

import json
import math

REPLIES = ["refund started", "order ships in 2 days", "reset at Settings > Security"]

# ----------------------------------------------------------------------------
# STEP 1: THE DATA = one chat example per line (JSONL), cleaned
# ----------------------------------------------------------------------------
#   RAW: 8 rows
#      │
#      ▼  for each row: fewer than 2 words? ── yes ──▶ DROP  ("ok")
#      │ no
#      ▼  lowercase it. Seen this text before? ── yes ──▶ DROP  ("Where is my ORDER"
#      │ no                                                     = "where is my order")
#      ▼
#   keep (text, label)  ──▶  6 rows
#      │
#      ▼  turn each row into one JSONL line
#   {"messages": [{"role": "user", "content": "i want my money back"},
#                 {"role": "assistant", "content": "refund started"}]}
RAW = [
    ("i want my money back", 0), ("please refund my order", 0),
    ("where is my order", 1), ("when will my package arrive", 1),
    ("i forgot my password", 2), ("cannot log in to my account", 2),
    ("Where is my ORDER", 1),        # duplicate (only case is different)
    ("ok", 1),                       # too short to be useful
]


def clean(rows):
    kept, seen = [], set()
    for text, label in rows:
        key = text.lower()
        if len(text.split()) < 2 or key in seen:     # drop short rows and duplicates
            continue
        seen.add(key)
        kept.append((key, label))
    return kept


# ----------------------------------------------------------------------------
# STEP 2: THE MODEL = one score per (word, reply). Training nudges the scores.
# ----------------------------------------------------------------------------
#   FIRST example of epoch 1 (the real trace printed by STEP 2):
#
#   "i want my money back"   correct reply = 0 ("refund started")
#      │
#      ▼  1. FORWARD: add word scores (all 0 at start), softmax
#   probs = [0.33, 0.33, 0.33]
#      │
#      ▼  2. LOSS = -log(probs[correct]) = -log(0.33)
#   loss = 1.10                          (perfect would be 0.00)
#      │
#      ▼  3. GRADIENT = probs - target    target = [1, 0, 0]
#   gradient = [-0.67, 0.33, 0.33]
#      │
#      ▼  4. UPDATE every word in the text:  score -= 0.5 x gradient
#   score["money"] = [0.33, -0.17, -0.17]   (reply 0 goes UP, the others go DOWN)
#
#   one epoch = do this for all 6 rows:
#   ┌─▶ next row ──▶ forward ──▶ loss ──▶ gradient ──▶ update
#   │      │
#   │   last row? ── yes ──▶ return the average loss of this epoch
#   │      │ no
#   └──────┘
def predict(weights, text):
    """Add up the scores of all words, then softmax -> probability per reply."""
    scores = [sum(weights.get(w, [0, 0, 0])[k] for w in text.split()) for k in range(3)]
    exps = [math.exp(s) for s in scores]
    return [e / sum(exps) for e in exps]


def train_one_epoch(weights, data, learning_rate=0.5, trace=False):
    """One pass over the data. This is real gradient descent, at tiny size."""
    total_loss = 0.0
    for i, (text, correct) in enumerate(data):
        probs = predict(weights, text)
        total_loss += -math.log(probs[correct])          # loss: low when right & sure
        for w in text.split():
            row = weights.setdefault(w, [0.0, 0.0, 0.0])
            for k in range(3):
                target = 1.0 if k == correct else 0.0
                row[k] -= learning_rate * (probs[k] - target)   # nudge toward target
        if trace and i == 0:                             # show the 4 parts once
            word = text.split()[3]
            print(f"  first example {text!r}  (correct = {correct}, {REPLIES[correct]!r})")
            print(f"    1. forward : probs {[round(p, 2) for p in probs]}")
            print(f"    2. loss    : -log({probs[correct]:.2f}) = {-math.log(probs[correct]):.2f}")
            grad = [round(p - (1.0 if k == correct else 0.0), 2) for k, p in enumerate(probs)]
            print(f"    3. gradient: probs - target = {grad}")
            print(f"    4. update  : score[{word!r}] = {[round(x, 2) for x in weights[word]]}")
    return total_loss / len(data)


# ----------------------------------------------------------------------------
# STEP 3: LoRA = train a small add-on instead of the whole matrix
# ----------------------------------------------------------------------------
#   FULL FINE-TUNE                          LoRA (rank 8)
#   change every number of W                W stays FROZEN, train A and B only
#
#        4096                                 4096            8          4096
#   ┌────────────┐                       ┌────────────┐     ┌──┐     ┌────────────┐ 8
#   │            │                       │            │     │  │     └────────────┘
#   │  W  (all   │ 4096                  │  W frozen  │  +  │A │  x        B
#   │  trained)  │                       │            │     │  │ 4096
#   └────────────┘                       └────────────┘     └──┘
#   4096 x 4096 = 16,777,216 numbers     4096x8 + 8x4096 = 65,536 numbers (0.39%)
#                                        rank 16: 131,072 numbers (0.78%)
#
#   The adapter (A, B) is a small file. Keep ONE base model, swap adapters per task.
def lora_params(d, rank):
    """Full matrix: d*d numbers. LoRA: two thin matrices, d*rank + rank*d."""
    return d * d, 2 * d * rank


def main():
    print("STEP 1: the data")
    data = clean(RAW)
    print("  one JSONL line looks like:")
    row = {"messages": [{"role": "user", "content": data[0][0]},
                        {"role": "assistant", "content": REPLIES[data[0][1]]}]}
    print("   ", json.dumps(row))
    print(f"  raw rows {len(RAW)} -> after cleaning {len(data)} (1 duplicate, 1 too short)")
    print("  (a real run also keeps 25% aside as validation; 6 rows is too few here)")

    print("\nSTEP 2: training (loss should go down)")
    weights = {}
    question = "where is my package"
    before = predict(weights, question)
    for epoch in range(1, 9):
        loss = train_one_epoch(weights, data, trace=(epoch == 1))
        print(f"  epoch {epoch}: loss {loss:.2f}  {'#' * round(loss * 20)}")
    after = predict(weights, question)
    print(f"  question: {question!r}  (not in the training data)")
    print(f"    before: {REPLIES[before.index(max(before))]!r}  p={max(before):.2f}  (just a guess)")
    print(f"    after : {REPLIES[after.index(max(after))]!r}  p={max(after):.2f}")

    print("\nSTEP 3: full fine-tune vs LoRA (one 4096 x 4096 matrix)")
    for rank in [8, 16]:
        full, lora = lora_params(4096, rank)
        print(f"  rank {rank:>2}: full {full:,} numbers, LoRA {lora:,} ({lora / full:.2%})")
    print("  LoRA is under 1% of the size. Keep one base model, swap small adapters.")


if __name__ == "__main__":
    main()

# Remember:
#   - Fine-tuning = more training on your examples. Data quality is everything.
#   - Always keep a validation set and stop when it stops improving.
#   - Fine-tune for style/format; use RAG for facts. LoRA makes it cheap.
# HOW TO DO IT FOR REAL (names only): Hugging Face transformers + peft (LoRA)
#   + trl (SFTTrainer), or a provider fine-tuning API (upload chat JSONL).
# Try: add a wrong row ("where is my parcel", 0) to RAW. What does the model say now?
