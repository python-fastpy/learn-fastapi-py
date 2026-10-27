"""Lesson 14 -- Fine-tuning, end to end: data, training, overfitting, LoRA, evals
==============================================================================

WHY THIS MATTERS:
  Lesson 06 (PART 6) told you WHEN to reach for fine-tuning: last, after
  prompting, RAG and tools have plateaued on a narrow, high-volume task.
  This lesson is the HOW. Fine-tuning is just more gradient descent on
  your own examples, and every classic failure (bad data, leakage,
  overfitting, bad learning rate, forgetting) shows up at toy scale --
  so we build a tiny trainable model and fine-tune it for real.

Flow:
   base model (pretrained, answers in the wrong style)
        |  + your chat-format JSONL examples (cleaned, deduped, split)
        v
   training loop: predict -> loss -> gradient -> nudge weights -> repeat
        |  watch TRAIN and VALIDATION loss; stop when val stops improving
        v
   fine-tuned model (full weights or a small LoRA adapter)
        |  held-out eval: did the task improve? did general ability regress?
        v
   ship it -- or go back to prompting / RAG

WHAT YOU'LL LEARN:
  1. The three training stages: pretraining -> SFT -> preference tuning
  2. Fine-tuning data: chat JSONL, quality checks, dedup, train/val leakage
  3. A real (toy) fine-tune: loss per epoch, before/after outputs
  4. Overfitting and early stopping, from measured train/val curves
  5. Learning rate: too high / good / too slow -- measured
  6. Full fine-tuning vs LoRA: parameter counts, memory, swappable adapters
  7. Distillation (teacher labels data for a student) and DPO
  8. Evaluating a fine-tune: held-out set + catastrophic forgetting
  9. When NOT to fine-tune, and the practical tool path

Concepts:
  - SFT: supervised fine-tuning on (prompt, ideal response) pairs
  - Epoch: one pass over the training set
  - Validation set: examples never trained on, used to detect overfitting
  - Learning rate: how big each weight update is
  - LoRA: freeze W, learn a low-rank update A @ B (tiny, swappable)
  - DPO: learn from (chosen, rejected) pairs without a reward model

PREREQUISITES: Lessons 01-06. Pure Python, no packages, no credentials.

Level: ADVANCED

Run:  uv run python advanced/14_fine_tuning.py      (from learn-llm-fundamentals)
"""

import json
import math
import random
import re
import zlib
from collections import Counter

# ----------------------------------------------------------------------------
# The toy model used everywhere below
# ----------------------------------------------------------------------------
# A real LLM picks the next token from ~100k options. Our toy picks one
# whole REPLY from 5 options (think of each reply as one "token"). The
# model is a softmax classifier over bag-of-words features -- trained with
# the same cross-entropy loss and gradient descent a real SFT run uses.

SYSTEM = "You are Acme's support assistant. Be brief, polite and actionable."
REPLIES = [
    "lol idk, maybe google it? :)",                                  # 0
    "Sorry about that. I've started a refund (3-5 business days).",  # 1
    "Your order ships within 2 days. Tracking: [link]",              # 2
    "Reset it at Settings > Security > Reset password.",             # 3
    "I'm escalating this to a human agent now. Ticket created.",     # 4
]
NAMES = ["casual", "refund", "shipping", "password", "escalate"]
K = len(REPLIES)


def feats(text: str) -> list[str]:
    return ["<bias>"] + re.findall(r"[a-z']+", text.lower())


def softmax(z: list[float]) -> list[float]:
    e = [math.exp(v - max(z)) for v in z]
    return [v / sum(e) for v in e]


def logits(W: dict, f: list[str]) -> list[float]:
    """Sum the weight vector of every feature present (unknown words add 0)."""
    zero = [0.0] * K
    return [sum(W.get(t, zero)[k] for t in f) for k in range(K)]


def predict(W: dict, text: str) -> tuple[int, float]:
    p = softmax(logits(W, feats(text)))
    k = max(range(K), key=lambda i: p[i])
    return k, p[k]


def mean_loss(W: dict, data: list) -> float:
    return sum(-math.log(max(softmax(logits(W, f))[y], 1e-12))
               for f, y in data) / len(data)


def accuracy(W: dict, data: list) -> float:
    return sum(max(range(K), key=lambda i: logits(W, f)[i]) == y
               for f, y in data) / len(data)


def gd_step(W: dict, data: list, lr: float) -> None:
    """One full-batch gradient step. d(loss)/d(logit_k) = p_k - [k == y]."""
    grads: dict[str, list[float]] = {}
    for f, y in data:
        p = softmax(logits(W, f))
        for t in f:
            g = grads.setdefault(t, [0.0] * K)
            for k in range(K):
                g[k] += (p[k] - (k == y)) / len(data)
    for t, g in grads.items():
        w = W.setdefault(t, [0.0] * K)
        for k in range(K):
            w[k] -= lr * g[k]


def train(W: dict, data: list, lr: float, epochs: int) -> dict:
    for _ in range(epochs):
        gd_step(W, data, lr)
    return W


def bar(v: float, scale: float, width: int = 30) -> str:
    n = max(0, min(width, round(v / scale * width)))
    return "#" * n + "." * (width - n)


# "Pretraining" stand-in: casual internet chat, every reply casual. The
# resulting BASE model answers everything -- even support questions -- casually.
PRETRAIN = ["hey what's up", "tell me a joke", "lol that movie was great",
            "how is the weather today", "anyone know a good pizza place",
            "my cat is so funny", "what time is it", "i love this song",
            "where is the party tonight", "how do i cook pasta",
            "is it going to rain", "my order of fries was cold lol"]


def base_model() -> dict:
    return train({}, [(feats(t), 0) for t in PRETRAIN], lr=0.5, epochs=20)


# ============================================================================
# PART 1: What fine-tuning changes -- the three training stages
# ============================================================================
#  ┌────────────────┐    ┌────────────────────┐    ┌────────────────────┐
#  │ 1 PRETRAINING  │───▶│ 2 SFT              │───▶│ 3 PREFERENCE       │
#  │ next-token on  │    │ (prompt, ideal     │    │ (prompt, chosen,   │
#  │ ~10T tokens of │    │  reply) pairs,     │    │  rejected) pairs:  │
#  │ web/books/code │    │ 10k-1M examples    │    │ RLHF or DPO        │
#  └───────┬────────┘    └─────────┬──────────┘    └─────────┬──────────┘
#          ▼                       ▼                         ▼
#     BASE model             INSTRUCT/CHAT model        ALIGNED model
#     (autocompletes)        (follows format)           (preferred style)
#  YOUR fine-tune = more of stage 2 (and maybe 3) on a few hundred examples

def part1_stages():
    print("######## PART 1 -- What fine-tuning changes ########\n")
    print("""  | stage          | data                           | teaches             |
  |----------------|--------------------------------|---------------------|
  | 1 pretraining  | raw text, trillions of tokens  | knowledge, language |
  | 2 SFT          | (prompt, ideal reply), 10k-1M  | format, tone, task  |
  | 3 preference   | (prompt, chosen, rejected)     | style, helpfulness  |
  | YOUR fine-tune | 100s-10k of YOUR examples      | your narrow task    |""")
    k, p = predict(base_model(), "where is my order")
    print(f"\n  Toy BASE model ('pretrained' on {len(PRETRAIN)} casual chats):")
    print(f"    user: 'where is my order'  ->  {REPLIES[k]!r}  (p={p:.2f})")
    print("  Right language, wrong job. Fine-tuning changes the WEIGHTS so the")
    print("  default behaviour changes -- no instructions needed in the prompt.\n")


# ============================================================================
# PART 2: The data -- chat JSONL, quality checks, dedup, split, leakage
# ============================================================================
#  raw rows ──▶ schema ✓ ──▶ quality ✓ ──▶ dedup ✓ ──▶ shuffle+split ──▶ leak ✓
#     │            │             │            │            │              │
#     39       roles ok?    approved      normalised   75% train     val text
#              non-empty?   reply, not    text seen    25% val       never in
#                           too short     before?                    train
#  50 clean examples beat 500 noisy ones: the model copies what you show it

SUPPORT = {
    1: ["i want my money back", "please refund my order",
        "the item arrived broken, refund please", "can i get a refund for this",
        "charged twice, i need my money back", "return this and refund me",
        "refund the damaged blender", "how do i get my money back"],
    2: ["where is my order", "when will my package arrive",
        "has my parcel shipped yet", "tracking number for my order please",
        "my delivery is late", "how long does shipping take",
        "is my package on the way", "my order has not arrived, where is it"],
    3: ["i forgot my password", "how do i reset my password",
        "cannot log in to my account", "locked out of my account",
        "password reset link not working", "change my login password",
        "i can't sign in", "my account login fails"],
    4: ["i want to speak to a human", "this is unacceptable, get me a manager",
        "let me talk to a real person", "i will complain to a supervisor",
        "connect me to an agent now", "your bot is useless, human please",
        "i need a real human agent", "escalate this now"],
}
# Two MISLABELED rows that pass every check -- real datasets always have some.
NOISY = [("yo where is my parcel", 1), ("hey i forgot my password", 4)]


def chat_row(user: str, reply: str | None) -> dict:
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]
    if reply:
        msgs.append({"role": "assistant", "content": reply})
    return {"messages": msgs}


def raw_rows() -> list[dict]:
    rows = [chat_row(u, REPLIES[y]) for y, us in SUPPORT.items() for u in us]
    rows += [chat_row(u, REPLIES[y]) for u, y in NOISY]
    return rows + [chat_row("Where is my  ORDER?", REPLIES[2]),    # duplicate
                   chat_row("I forgot my password!", REPLIES[3]),  # duplicate
                   chat_row("can you refund me", REPLIES[0]),      # off-style
                   chat_row("ok", REPLIES[2]),                     # too short
                   chat_row("refund my shoes", None)]              # no reply


def user_of(row: dict) -> str:
    return row["messages"][1]["content"]


def norm(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9']+", text.lower()))


def check_row(row: dict) -> str | None:
    msgs = row["messages"]
    if [m["role"] for m in msgs] != ["system", "user", "assistant"] or \
            not all(m["content"].strip() for m in msgs):
        return "schema"
    if msgs[2]["content"] not in REPLIES[1:]:
        return "quality: reply not in style guide"
    if len(msgs[1]["content"].split()) < 2:
        return "quality: user text too short"
    return None


def clean_rows(verbose: bool = False) -> list[dict]:
    kept, seen = [], set()
    for row in raw_rows():
        why = check_row(row) or ("duplicate" if norm(user_of(row)) in seen else None)
        if why and verbose:
            print(f"    DROP {user_of(row)!r:<28} {why}")
        if not why:
            seen.add(norm(user_of(row)))
            kept.append(row)
    return kept


def split(rows: list, seed: int = 8) -> tuple[list, list]:
    rows = list(rows)
    random.Random(seed).shuffle(rows)
    n_val = len(rows) // 4
    return rows[n_val:], rows[:n_val]


def leaks(train_rows: list, val_rows: list) -> int:
    seen = {norm(user_of(r)) for r in train_rows}
    return sum(norm(user_of(r)) in seen for r in val_rows)


def dataset() -> tuple[list, list]:
    """(features, reply index) pairs for the cleaned train and val splits."""
    def to_xy(rows):
        return [(feats(user_of(r)), REPLIES.index(r["messages"][2]["content"]))
                for r in rows]
    tr, val = split(clean_rows())
    return to_xy(tr), to_xy(val)


def part2_data():
    print("######## PART 2 -- The data ########\n")
    raw = raw_rows()
    print("  One training example = one JSON line (OpenAI-style chat format):")
    print("    " + json.dumps(raw[0]))
    print(f"\n  Checks on {len(raw)} raw rows:")
    clean = clean_rows(verbose=True)
    tr, val = split(clean)
    print(f"\n  kept {len(clean)}/{len(raw)}  ->  train {len(tr)}, val {len(val)}")
    dirty = [r for r in raw if check_row(r) is None]
    leaky = sum(leaks(*split(dirty, seed=s)) > 0 for s in range(20))
    print(f"  leakage (val user text also in train) after dedup: {leaks(tr, val)} rows")
    print(f"  WITHOUT dedup, {leaky} of 20 random splits leak a duplicate into val")
    counts = Counter(NAMES[y] for _, y in dataset()[0])
    print("  train label balance: " + ", ".join(f"{n}={counts[n]}" for n in NAMES[1:]))
    print("\n  Leaked val rows make validation loss look better than reality. The 2")
    print("  mislabeled rows got through -- only human review catches those (PART 4).\n")


# ============================================================================
# PART 3: Training for real (toy)
# ============================================================================
#  ┌──▶ forward: p = softmax(W · features)
#  │      ▼
#  │    loss = -log p[correct reply]        (cross-entropy, as in real SFT)
#  │      ▼
#  │    gradient: dL/dlogit_k = p_k - 1[k = correct]
#  │      ▼
#  │    update: W -= learning_rate * gradient
#  └──────┘  one loop over all examples = one EPOCH

PROBES = ["where is my order", "i want a refund", "i forgot my password", "get me a human"]


def part3_training():
    print("######## PART 3 -- Fine-tuning for real (toy) ########\n")
    tr, val = dataset()
    before, W = base_model(), base_model()
    print(f"  {len(tr)} examples, full-batch gradient descent, lr=1.0\n")
    print("  epoch  train loss")
    start = mean_loss(W, tr)
    print(f"  {0:>5}  {start:5.3f}  {bar(start, start)}")
    for ep in range(1, 31):
        gd_step(W, tr, lr=1.0)
        if ep % 5 == 0:
            loss = mean_loss(W, tr)
            print(f"  {ep:>5}  {loss:5.3f}  {bar(loss, start)}")
    print(f"\n  val accuracy ({len(val)} rows): before {accuracy(before, val):.0%}"
          f"  ->  after {accuracy(W, val):.0%}\n")
    for q in PROBES:
        (kb, pb), (ka, pa) = predict(before, q), predict(W, q)
        print(f"  user: {q!r}")
        print(f"    before: {REPLIES[kb]!r} (p={pb:.2f})")
        print(f"    after : {REPLIES[ka]!r} (p={pa:.2f})")
    print("\n  No system prompt or examples at inference: behaviour is in the weights.\n")


# ============================================================================
# PART 4: Overfitting and early stopping
# ============================================================================
#  loss
#   │ ██ train ░░ val
#   │ ██░░
#   │   ██░░            val bottoms out ──▶ best checkpoint ✓
#   │     ██░░░░░░░░░░░░░░░░ ...then CREEPS UP (memorising noise) ✗
#   │       ██████████████████ train keeps falling toward 0
#   └──────────────────────────────▶ epochs
#  keep the checkpoint with the lowest VAL loss, not the last one

def part4_overfitting():
    print("######## PART 4 -- Overfitting and early stopping ########\n")
    tr_data, val = dataset()
    epochs, last, hist, best_ep = 2000, base_model(), [], 0
    best, best_val = base_model(), mean_loss(last, val)
    for ep in range(1, epochs + 1):
        gd_step(last, tr_data, lr=1.0)
        hist.append((ep, mean_loss(last, tr_data), mean_loss(last, val)))
        if hist[-1][2] < best_val:                   # checkpoint (deep copy)
            best_val, best_ep = hist[-1][2], ep
            best = {t: list(w) for t, w in last.items()}
    shown = [h for h in hist if h[0] in (1, 10, 30, best_ep, 200, 500, 1000, epochs)]
    lo, hi = min(h[2] for h in hist), max(h[2] for h in shown)
    print("  epoch  train  val    val loss (bar zoomed to min..max)")
    for ep, tr, va in shown:
        mark = "  <- lowest val (best)" if ep == best_ep else ""
        print(f"  {ep:>5}  {tr:5.3f}  {va:5.3f}  "
              f"{bar(va - lo + 0.02, hi - lo + 0.02, 24)}{mark}")
    print(f"\n  Train loss keeps falling to {hist[-1][1]:.3f} (memorised), but val")
    print(f"  loss bottoms out at epoch {best_ep} and then rises: the model grows MORE")
    print(f"  CONFIDENT on what it gets wrong. Early stopping keeps epoch {best_ep}.\n")
    for q in ["where is my parcel", "hey my password is lost"]:
        (kb, pb), (kl, pl) = predict(best, q), predict(last, q)
        print(f"  new input {q!r}")
        print(f"    epoch {best_ep:>4} (best): {NAMES[kb]:<9} p={pb:.2f}")
        print(f"    epoch {epochs} (last): {NAMES[kl]:<9} p={pl:.2f}")
    print("\n  Both should be shipping / password: the noisy rows taught 'parcel' ->")
    print("  refund and 'hey' -> escalate, and more epochs make it surer. Early")
    print("  stopping limits the damage; only fixing the data removes it.\n")


# ============================================================================
# PART 5: Learning rate and epochs
# ============================================================================
#  too high   loss ─╮╭╮╭─╮ ╭──  jumps over the minimum, bounces / blows up ✗
#  good       loss ─╲___________ fast, smooth, settles                   ✓
#  too low    loss ─────────╲___ barely moves in the same budget         ✗
#  same data, same 30 epochs -- only the step size differs

def part5_learning_rate():
    print("######## PART 5 -- Learning rate, measured ########\n")
    tr, val = dataset()
    start = mean_loss(base_model(), tr)
    print(f"  start train loss {start:.3f}; 30 epochs each\n")
    for lr in (300.0, 1.0, 0.02):
        W, losses = base_model(), []
        for _ in range(30):
            gd_step(W, tr, lr)
            losses.append(mean_loss(W, tr))
        ups = sum(b > a + 1e-9 for a, b in zip(losses, losses[1:]))
        verdict = ("GOOD" if losses[-1] < 0.5 * start else
                   "TOO SLOW (still > half the starting loss)")
        if ups >= 3 or max(losses) > start:
            verdict = f"UNSTABLE (loss rose {ups} times, peak {max(losses):.2f})"
        print(f"  lr={lr:<5}  epochs 1-6: " + " ".join(f"{x:.2f}" for x in losses[:6]))
        print(f"            final train {losses[-1]:.3f}  val {mean_loss(W, val):.3f}"
              f"  val acc {accuracy(W, val):.0%}  -> {verdict}\n")
    print("  Real LLM fine-tunes: LoRA ~1e-4 to 2e-4, full fine-tune ~1e-5,")
    print("  1-3 epochs, warmup + decay. Start from the library/provider default.\n")


# ============================================================================
# PART 6: Full fine-tuning vs LoRA
# ============================================================================
#   FULL: W (d x d) all trainable          LoRA: W frozen ░ + A @ B █
#   ┌───────────────┐                      ┌───────────────┐   ┌─┐
#   │███████████████│                      │░░░░░░░░░░░░░░░│ + │█│ A (d x r)
#   │███████████████│ d*d params           │░░░░░░░░░░░░░░░│   │█│ ┌───────┐
#   │███████████████│                      │░░░░░░░░░░░░░░░│   └─┘ │███████│
#   └───────────────┘                      └───────────────┘       └───────┘
#   one full copy per customer             base shared ──▶ B (r x d), swap a
#                                          few-MB adapter per customer

def lora_train(rank: int, epochs: int = 200, lr: float = 1.0) -> tuple[float, int]:
    """Freeze the base W0; learn only A (V x r) and B (r x K): W = W0 + A@B."""
    tr, val = dataset()
    W0, rng = base_model(), random.Random(42)
    vocab = sorted({t for f, _ in tr for t in f})
    A = {t: [rng.gauss(0, 0.3) for _ in range(rank)] for t in vocab}
    B = [[0.0] * K for _ in range(rank)]               # B = 0: starts as no-op

    def lg(f):
        z = logits(W0, f)
        for t, j, k in ((t, j, k) for t in f if t in A
                        for j in range(rank) for k in range(K)):
            z[k] += A[t][j] * B[j][k]
        return z

    for _ in range(epochs):              # chain rule through W0 + A@B
        gA = {t: [0.0] * rank for t in vocab}
        gB = [[0.0] * K for _ in range(rank)]
        for f, y in tr:
            p = softmax(lg(f))
            G = [(p[k] - (k == y)) / len(tr) for k in range(K)]   # dL/dlogits
            for t, j in ((t, j) for t in f for j in range(rank)):
                gA[t][j] += sum(G[k] * B[j][k] for k in range(K))
                for k in range(K):
                    gB[j][k] += A[t][j] * G[k]
        for t, j in ((t, j) for t in vocab for j in range(rank)):
            A[t][j] -= lr * gA[t][j]
        B = [[B[j][k] - lr * gB[j][k] for k in range(K)] for j in range(rank)]
    acc = sum(max(range(K), key=lambda i: lg(f)[i]) == y for f, y in val)
    return acc / len(val), len(vocab)


def part6_lora():
    print("######## PART 6 -- Full fine-tuning vs LoRA ########\n")
    d, ff, layers, vocab = 4096, 11008, 32, 32000
    mats = [(d, d)] * 4 + [(d, ff), (d, ff), (ff, d)]   # q k v o + MLP x3
    full = layers * sum(a * b for a, b in mats) + 2 * vocab * d
    print(f"  One {d}x{d} attention matrix: full = {d * d:,} trainable params")
    for r in (4, 8, 16):
        print(f"    LoRA r={r:<2}: r*(d+d) = {r * 2 * d:>9,}  "
              f"({r * 2 * d / (d * d):.2%} of full)")
    print(f"\n  7B-like config ({layers} layers, d={d}, MLP 11008, LoRA on all")
    print(f"  7 linear layers per block): total {full / 1e9:.2f}B params")
    for r in (4, 8, 16):
        lp = layers * sum(r * (a + b) for a, b in mats)
        print(f"    r={r:<2}: {lp / 1e6:5.1f}M trainable ({lp / full:.2%}), "
              f"adapter file {lp * 2 / 1e6:4.0f} MB in bf16")
    gb, lp16 = 1e9, layers * sum(16 * (a + b) for a, b in mats)
    print("\n  Training memory, rule of thumb (weights+grads+Adam, no activations):")
    print(f"    full FT  : 16 bytes x {full / gb:.2f}B params      = "
          f"{16 * full / gb:6.1f} GB")
    print(f"    LoRA r16 : 2 x base (frozen bf16) + 16 x adapter = "
          f"{(2 * full + 16 * lp16) / gb:6.1f} GB")
    print(f"    QLoRA r16: 0.5 x base (4-bit)   + 16 x adapter = "
          f"{(0.5 * full + 16 * lp16) / gb:6.1f} GB")
    print("\n  Toy model, base frozen, LoRA adapter trained (200 epochs):")
    for r in (1, 2, 4):
        acc, V = lora_train(r)
        print(f"    rank {r}: {r * (V + K):>3} trainable vs {V * K} full  "
              f"-> val acc {acc:.0%}")
    print("  Rank 1 can only push every word along ONE class direction; a few")
    print("  ranks are enough. Serving: keep one base model in memory and load")
    print("  customer A's or customer B's adapter per request (multi-LoRA).\n")


# ============================================================================
# PART 7: Distillation and preference tuning (DPO)
# ============================================================================
#  DISTILLATION                               DPO
#  unlabeled prompts                           prompt
#     ▼                                          ├─▶ chosen   ✓  push p UP
#  ┌─────────┐ labels ┌─────────┐               └─▶ rejected ✗  push p DOWN
#  │ TEACHER │──────▶│ STUDENT │ cheap, fast    loss = -log sigmoid(beta *
#  │ big, $$ │       │ small   │                  [(logp_c - ref_c) -
#  └─────────┘       └─────────┘                   (logp_r - ref_r)])

UNLABELED = ["my refund never came", "where's my parcel", "reset my login",
             "a human please", "money back for the broken lamp", "refund please",
             "package still not here", "password does not work", "talk to a person",
             "i demand a manager", "where is the delivery", "can't log into account"]
EVAL = [("i would like my money returned", 1), ("please refund the broken lamp", 1),
        ("when does my order arrive", 2), ("where is my package now", 2),
        ("reset password please", 3), ("i cannot log in", 3),
        ("get me a human now", 4), ("i want a manager", 4)]


def student_feats(text: str, buckets: int = 8) -> list[str]:
    """Tiny student: every word hashed into one of 8 buckets."""
    return ["<bias>"] + [f"h{zlib.crc32(w.encode()) % buckets}"
                         for w in feats(text)[1:]]


def part7_distill_dpo():
    print("######## PART 7 -- Distillation and DPO ########\n")
    teacher = train(base_model(), dataset()[0], lr=1.0, epochs=30)  # PART 3
    pool = [user_of(r) for r in clean_rows()] + UNLABELED
    sdata = [(student_feats(t), predict(teacher, t)[0]) for t in pool]
    student = train({}, sdata, lr=1.0, epochs=300)
    t_acc = accuracy(teacher, [(feats(t), y) for t, y in EVAL])
    s_acc = accuracy(student, [(student_feats(t), y) for t, y in EVAL])
    print(f"  teacher labeled {len(pool)} prompts; student trained on its labels")
    print(f"    teacher: {len(teacher) * K:>4} params, eval acc {t_acc:.0%}")
    print(f"    student: {len(student) * K:>4} params, eval acc {s_acc:.0%}")
    reqs, tok = 1_000_000, 60
    t_cost, s_cost = reqs * tok / 1e6 * 3.00, reqs * tok / 1e6 * 0.10
    print(f"  SIMULATED prices ($3.00 vs $0.10 per 1M tokens), {reqs:,} req x {tok} tok:")
    print(f"    teacher ${t_cost:,.0f}/month  vs  student ${s_cost:,.0f}/month")
    print(f"  Trade: some accuracy for {t_cost / s_cost:.0f}x cheaper, faster calls."
          " Gate on evals.\n")
    dpo()


def dpo():
    W, ref, beta = base_model(), base_model(), 1.0
    pairs = [(feats(SUPPORT[k][0]), k, 0) for k in range(1, K)]  # (x, chosen, rej)
    pair = {"prompt": SUPPORT[1][0], "chosen": REPLIES[1], "rejected": REPLIES[0]}
    print("  DPO on the BASE model, 4 pairs like:\n  " + json.dumps(pair))
    for step in range(41):
        loss, grads = 0.0, {}
        for f, c, r in pairs:
            lp = [math.log(p) for p in softmax(logits(W, f))]
            lref = [math.log(p) for p in softmax(logits(ref, f))]
            sig = 1 / (1 + math.exp(-beta * ((lp[c] - lref[c]) - (lp[r] - lref[r]))))
            loss -= math.log(sig) / len(pairs)
            for t in f:          # dL/dlogits = (sig - 1) * beta * (1[c] - 1[r])
                g = grads.setdefault(t, [0.0] * K)
                g[c] += (sig - 1) * beta / len(pairs)
                g[r] -= (sig - 1) * beta / len(pairs)
        if step % 10 == 0:
            pc = sum(softmax(logits(W, f))[c] for f, c, _ in pairs) / len(pairs)
            pr = sum(softmax(logits(W, f))[r] for f, _, r in pairs) / len(pairs)
            print(f"    step {step:>2}: DPO loss {loss:.3f}   mean P(chosen) {pc:.2f}"
                  f"   P(rejected) {pr:.2f}")
        for t, g in grads.items():
            W[t] = [w - 0.5 * gk for w, gk in zip(W.setdefault(t, [0.0] * K), g)]
    print("  DPO only asks chosen to beat rejected (vs the frozen reference); freed")
    print("  probability spreads to other replies too, so DPO runs AFTER SFT, not")
    print("  instead of it. No reward model, no RL loop: just a loss on pairs.\n")


# ============================================================================
# PART 8: Evaluating a fine-tune
# ============================================================================
#                    task eval (held out)     general eval (old skills)
#  base              ░░░░░░░░░░  low          ██████████  high
#  fine-tuned        ██████████  high  ✓      ███░░░░░░░  dropped ✗ forgetting
#  + replay mix      ██████████  high  ✓      █████████░  kept    ✓
#  always run BOTH; a fine-tune that wins one and loses the other is a regression

GENERAL = ["hey what's up tonight", "tell me a funny joke", "how is the weather",
           "i love pizza", "what a great movie lol", "my cat is funny"]


def part8_evaluate():
    print("######## PART 8 -- Evaluating a fine-tune ########\n")
    tr = dataset()[0]
    task = [(feats(t), y) for t, y in EVAL]
    general = [(feats(t), 0) for t in GENERAL]
    replay = [(feats(t), 0) for t in PRETRAIN[::2]]
    models = {"base": base_model(),
              "fine-tuned (support only)": train(base_model(), tr, 1.0, 100),
              f"fine-tuned + {len(replay)} replay rows":
                  train(base_model(), tr + replay, 1.0, 100)}
    print(f"  task eval = {len(task)} NEW support prompts; general eval = "
          f"{len(GENERAL)} chit-chat prompts")
    print("  (toy, measured: 'general ability' = the casual chat the base could do)\n")
    print(f"  {'model':<30} task acc   general acc")
    for name, m in models.items():
        print(f"  {name:<30} {accuracy(m, task):>7.0%}   {accuracy(m, general):>9.0%}")
    print("\n  Real models (illustrative, NOT measured here): a narrow full fine-tune")
    print("  can lose points on broad benchmarks; LoRA + replay data shrink that.")
    print("  Build the eval set BEFORE training, never train on it, and compare")
    print("  against the base model + best prompt (lesson 11: evals).\n")


# ============================================================================
# PART 9: When NOT to fine-tune -- and the practical path
# ============================================================================
#  facts change often?  ──yes──▶ RAG (weights can't be re-indexed nightly)
#        │ no
#  prompt + examples fix it? ──yes──▶ stop, ship the prompt
#        │ no
#  < ~100 good examples? ──yes──▶ collect data first (evals too)
#        │ no
#  narrow, high-volume, stable ──▶ fine-tune: LoRA on an open model,
#                                  or a provider fine-tuning API

def part9_when_not():
    print("######## PART 9 -- When NOT to fine-tune ########\n")
    print("""  Don't fine-tune when:
    - the FACTS change (prices, docs, policies) -> RAG; a fine-tune
      memorises a snapshot and still hallucinates (lesson 10)
    - a better prompt / few-shot examples / structured output fixes it
      (lesson 05) -- minutes, not weeks
    - you have too little data: PART 4 showed 2 bad rows out of 26
      bending the model; you need hundreds of reviewed examples
    - you have no eval set: you can't tell if it helped (lesson 11)

  Practical path when you DO fine-tune (names only -- nothing installed):
    open models   : Llama / Mistral / Qwen / Gemma weights
                    + Hugging Face transformers + peft (LoRA/QLoRA), TRL
                    (SFTTrainer, DPOTrainer), or Unsloth for faster LoRA
    provider APIs : upload chat JSONL, get a hosted fine-tuned model
                    (e.g. OpenAI fine-tuning, Amazon Bedrock, Google Vertex AI)
    run it locally: advanced/15 (running open models locally)
""")


# ============================================================================
# Demo
# ============================================================================

def main():
    part1_stages()
    part2_data()
    part3_training()
    part4_overfitting()
    part5_learning_rate()
    part6_lora()
    part7_distill_dpo()
    part8_evaluate()
    part9_when_not()

    print("######## Summary ########\n")
    print("  clean data -> split -> train -> watch val loss -> stop early")
    print("        -> eval task AND general ability -> ship adapter or go back")
    print("  Fine-tuning changes behaviour; RAG changes knowledge.")


if __name__ == "__main__":
    main()

    # -- Key takeaway --------------------------------------------------------
    # Fine-tuning is ordinary gradient descent on your examples. The model
    # copies your data -- including its mistakes -- so data quality, a clean
    # validation split, early stopping and a before/after eval matter more
    # than the training code. LoRA makes it cheap enough to try.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Delete the NOISY rows and re-run PART 4: does val loss still rise?
    # 2. Change split()'s seed: how much do val numbers move with only 8 rows?
    # 3. In PART 8 raise replay to all of PRETRAIN: what happens to task acc?
