"""Lesson 12 -- Inside the transformer: what the model actually computes
=======================================================================

WHY THIS MATTERS:
  Lesson 01 used an n-gram counter as a stand-in for "the model". Real
  LLMs keep the same interface (tokens in, next-token probabilities out)
  but compute it with a TRANSFORMER. Knowing what happens inside explains
  the engineering facts you meet every day:

      - why output tokens cost more and stream slowly    (KV cache)
      - why context windows have limits at all           (n^2 attention)
      - why facts in the middle of a long prompt get missed
      - what "7B parameters" actually counts

  This lesson builds every piece at toy scale, by hand, with real numbers.

WHAT YOU'LL LEARN:
  1. The full pipeline from token ids to logits to softmax
  2. Embeddings: tokens become vectors; similar tokens, similar vectors
  3. Self-attention by hand: QK^T / sqrt(d), causal mask, softmax, x V
  4. Multi-head attention: different heads look for different things
  5. Positional information: why word order needs to be injected
  6. Generation and the KV cache: work per token, measured
  7. Why context windows are limited: attention cost grows with n^2
  8. "Lost in the middle": attention favours the start and the end
  9. Scale: counting parameters, and the cross-entropy training objective

Concepts:
  - Embedding: a learned vector per token id (a row of a big table)
  - Query / Key / Value: what I'm looking for / what I offer / what I pass on
  - Causal mask: token i may only attend to tokens 0..i (no peeking ahead)
  - Residual stream: each block ADDS its result to the running vector
  - KV cache: stored keys/values of past tokens, reused every new step
  - Cross-entropy: -log P(correct next token), the loss training minimises

Flow:
   "the cat sat"
        |  tokenizer (lesson 01)
        v
   [1, 2, 4] --embedding lookup--> 3 vectors --+ position--> x
        |
        v   repeat N times (N = 2 here, 32+ in real models)
   +-- transformer block --------------------------------+
   |  x = x + Attention(norm(x))   tokens exchange info  |
   |  x = x + MLP(norm(x))         each token "thinks"   |
   +-----------------------------------------------------+
        |  last token's vector
        v
   unembedding --> logits (one per vocab token) --softmax--> P(next)
        |  sampling (lesson 02)
        v
   one token, appended, loop again

PREREQUISITES: Lessons 01-04. Pure Python, no packages, no credentials.

Level: ADVANCED

Run:  uv run python advanced/12_inside_the_transformer.py   (from learn-llm-fundamentals)
"""

import math
import random

# ============================================================================
# Tiny linear-algebra helpers (what numpy / a GPU does, at toy scale)
# ============================================================================
# MATVEC = ONE DOT PRODUCT PER OUTPUT ROW  (W is out x in)
#   W ┌ w00 w01 w02 ┐   x ┌ x0 ┐     ┌ w00*x0 + w01*x1 + w02*x2 ┐
#     └ w10 w11 w12 ┘     │ x1 │ ──▶ └ w10*x0 + w11*x1 + w12*x2 ┘
#                         └ x2 ┘     rows*cols multiplications (counted)

MULS = [0]  # global multiplication counter, used to MEASURE cost in part 6


def matvec(W, x):
    MULS[0] += len(W) * len(x)
    return [sum(w * xi for w, xi in zip(row, x)) for row in W]


def matmul(A, B):
    """Row-vector convention used in papers: (n x d) @ (d x m) -> (n x m)."""
    cols = list(zip(*B))
    return [[sum(a * b for a, b in zip(row, col)) for col in cols] for row in A]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def add(a, b):
    return [x + y for x, y in zip(a, b)]


def softmax(xs):
    m = max(xs)
    exps = [math.exp(x - m) for x in xs]   # exp(-inf) == 0.0 -> masked out
    total = sum(exps)
    return [e / total for e in exps]


def rmsnorm(x):
    rms = math.sqrt(sum(v * v for v in x) / len(x) + 1e-6)
    return [v / rms for v in x]


def cosine(a, b):
    return dot(a, b) / (math.sqrt(dot(a, a)) * math.sqrt(dot(b, b)))


def rand_matrix(rng, rows, cols):
    scale = 1 / math.sqrt(cols)
    return [[rng.gauss(0, scale) for _ in range(cols)] for _ in range(rows)]


def shade(w):
    """ASCII version of the shading ramp in the diagrams (░ ... █)."""
    return " .:+*#@"[min(6, round(w * 6))] * 2


def fmt(vec, n=4):
    return "[" + ", ".join(f"{v:+.2f}" for v in vec[:n]) + (", ...]" if len(vec) > n else "]")


# ============================================================================
# A real (tiny, untrained) decoder-only transformer
# ============================================================================
# ONE STEP FOR ONE TOKEN  (TinyTransformer.step)
#   tok_emb[id] + pos_emb[pos] ──▶ x
#   ┌─ for each layer ──────────────────────────────────────────────┐
#   │ h = norm(x) ─▶ q,k,v = Wq h, Wk h, Wv h ─▶ append k,v to cache│
#   │ w = softmax(q·K / sqrt(d)) over cached keys ─▶ a = w · V      │
#   │ x = x + Wo a                       (residual)                 │
#   │ x = x + W2 relu(W1 norm(x))        (MLP, residual)            │
#   └───────────────────────────────────────────────────────────────┘
#   logits = tok_emb · norm(x)   (unembedding, tied to the embedding table)

VOCAB = ["<s>", "the", "cat", "dog", "sat", "on", "mat", "rug", "ran", "a", ".", "and"]
TOK = {t: i for i, t in enumerate(VOCAB)}


class TinyTransformer:
    def __init__(self, d=16, n_layers=2, d_ff=64, max_len=32, seed=0):
        rng = random.Random(seed)
        self.d = d
        self.tok_emb = [[rng.gauss(0, 0.3) for _ in range(d)] for _ in VOCAB]
        self.pos_emb = [[rng.gauss(0, 0.1) for _ in range(d)] for _ in range(max_len)]
        self.layers = [{"Wq": rand_matrix(rng, d, d), "Wk": rand_matrix(rng, d, d),
                        "Wv": rand_matrix(rng, d, d), "Wo": rand_matrix(rng, d, d),
                        "W1": rand_matrix(rng, d_ff, d), "W2": rand_matrix(rng, d, d_ff)}
                       for _ in range(n_layers)]

    def n_params(self):
        mats = [self.tok_emb, self.pos_emb] + [m for L in self.layers for m in L.values()]
        return sum(len(m) * len(m[0]) for m in mats)

    def new_cache(self):
        return [{"K": [], "V": []} for _ in self.layers]

    def block(self, L, x, cache):
        h = rmsnorm(x)
        q, k, v = matvec(L["Wq"], h), matvec(L["Wk"], h), matvec(L["Wv"], h)
        cache["K"].append(k)
        cache["V"].append(v)
        t = len(cache["K"])                          # causal: only past + self exist
        w = softmax([dot(q, kk) / math.sqrt(self.d) for kk in cache["K"]])
        a = [sum(w[j] * cache["V"][j][i] for j in range(t)) for i in range(self.d)]
        MULS[0] += 2 * t * self.d                    # q.K scores + weighted sum of V
        x = add(x, matvec(L["Wo"], a))
        ff = [max(0.0, u) for u in matvec(L["W1"], rmsnorm(x))]
        return add(x, matvec(L["W2"], ff))

    def step(self, tok_id, pos, caches, want_logits=True, trace=None):
        x = add(self.tok_emb[tok_id], self.pos_emb[pos])
        if trace is not None:
            trace.append(("embedding + position", x))
        for n, (L, c) in enumerate(zip(self.layers, caches), 1):
            x = self.block(L, x, c)
            if trace is not None:
                trace.append((f"after block {n}", x))
        return matvec(self.tok_emb, rmsnorm(x)) if want_logits else None

    def forward(self, ids):
        """No cache: rebuild everything for the whole sequence, return last logits."""
        caches = self.new_cache()
        for pos, t in enumerate(ids):
            logits = self.step(t, pos, caches, want_logits=(pos == len(ids) - 1))
        return logits


# ============================================================================
# PART 1: The full pipeline -- ids to probabilities
# ============================================================================
# THE REAL RUN BELOW  (d=16, 2 blocks, 12-token vocab, last token "sat")
#   [1, 2, 4] ─▶ lookup ─▶ 3 x 16 ─▶ +pos ─▶ block 1 ─▶ block 2
#         ─▶ last vector (16) ─▶ unembed (12 x 16) ─▶ 12 logits ─▶ softmax
#   weights are RANDOM (untrained) ─▶ the probabilities are near-meaningless;
#   training (part 9) is what makes " on" win after "the cat sat".

def part1_pipeline():
    print("######## PART 1 -- The full pipeline ########\n")
    model = TinyTransformer()
    words = ["the", "cat", "sat"]
    ids = [TOK[w] for w in words]
    print(f"  tokens {words} -> ids {ids}")
    print(f"  embedding table: {len(VOCAB)} rows x {model.d} dims; "
          f"{len(model.layers)} transformer blocks\n")
    caches, trace, logits = model.new_cache(), [], None
    for pos, t in enumerate(ids):
        trace = [] if pos == len(ids) - 1 else None
        logits = model.step(t, pos, caches, trace=trace)
    print(f"  the vector for the LAST token ({words[-1]!r}) as it flows up:")
    for label, vec in trace:
        print(f"    {label:<22} {fmt(vec)}  |x|={math.sqrt(dot(vec, vec)):.2f}")
    probs = softmax(logits)
    print(f"\n  unembedding -> {len(logits)} logits -> softmax (lesson 02) -> P(next):")
    for i in sorted(range(len(VOCAB)), key=lambda i: -probs[i])[:5]:
        print(f"    {VOCAB[i]:<5} logit {logits[i]:+.2f}  p={probs[i]:.3f}  "
              f"{'#' * round(probs[i] * 40)}")
    print("\n  The weights are random, so these predictions are noise. The SHAPE")
    print("  of the computation is exactly what a 70B model does -- just wider")
    print("  vectors, more blocks, a 100k+ vocab, and trained weights.\n")


# ============================================================================
# PART 2: Embeddings -- a token id is just a row number
# ============================================================================
# LOOKUP = PICK A ROW                       SIMILAR MEANING = SIMILAR DIRECTION
#   id 2 ──▶ ┌──────────────────────┐            cat ─────▶
#            │ row 0  king   ...    │            kitten ───▶  cos ~ 1
#            │ row 1  queen  ...    │            apple  │
#            │ row 2  cat    ...  ◀─┤                   ▼     cos ~ 0
#            └──────────────────────┘
#   real models: ~100k rows x 4096+ dims, all LEARNED during training

EMBEDDINGS = {  # hand-made 4-d vectors. dims ~ [animal, royalty, food, young]
    "king":   [0.1, 0.9, 0.0, 0.1],
    "queen":  [0.1, 0.8, 0.1, 0.2],
    "cat":    [0.9, 0.0, 0.1, 0.2],
    "kitten": [0.8, 0.0, 0.1, 0.9],
    "dog":    [0.9, 0.1, 0.0, 0.2],
    "apple":  [0.0, 0.0, 0.9, 0.1],
    "banana": [0.1, 0.0, 0.9, 0.0],
}


def part2_embeddings():
    print("######## PART 2 -- Embeddings ########\n")
    names = list(EMBEDDINGS)
    table = [EMBEDDINGS[n] for n in names]
    for w in ["cat", "apple"]:
        print(f"  lookup {w!r}: id {names.index(w)} -> row {table[names.index(w)]}")
    print("\n  cosine similarity (1 = same direction, 0 = unrelated):")
    print("          " + "".join(f"{n:>8}" for n in names))
    for a in names:
        print(f"  {a:<8}" + "".join(f"{cosine(EMBEDDINGS[a], EMBEDDINGS[b]):>8.2f}" for b in names))
    for w in ["cat", "queen", "apple"]:
        best = max((n for n in names if n != w), key=lambda n: cosine(EMBEDDINGS[w], EMBEDDINGS[n]))
        print(f"  nearest to {w!r:<8} -> {best!r} ({cosine(EMBEDDINGS[w], EMBEDDINGS[best]):.2f})")
    print("\n  Nobody hand-labels the dimensions in a real model: training pushes")
    print("  tokens used in similar contexts toward similar vectors. This is the")
    print("  same idea as the retrieval embeddings in lesson 10.\n")


# ============================================================================
# PART 3: Self-attention, by hand
# ============================================================================
# 4 TOKENS, d=4.  Q = X Wq   K = X Wk   V = X Wv
#   scores = Q K^T / sqrt(d) ──▶ causal mask ──▶ softmax per row ──▶ x V
#   weights (real output below; row = query, col = key it reads)
#             the  cat  sat  on
#   the       ███   ─    ─    ─      only itself to look at
#   cat       ███  ░░    ─    ─      noun looks for its determiner
#   sat       ░░   ███  ░░    ─      verb looks for its subject
#   on        ░░   ░░   ███  ░░      preposition looks for the verb
#   ─ = masked (the future): every row sums to 1 over what it may see

ATT_TOKENS = ["the", "cat", "sat", "on"]
ATT_X = [[1, 0, 0, 0],   # dims = [determiner, noun, verb, preposition]
         [0, 1, 0, 0],
         [0, 0, 1, 0],
         [0, 0, 0, 1]]
# Wq: "what am I looking for?"  noun->determiner, verb->noun, prep->verb (strength 4)
ATT_WQ = [[0, 0, 0, 0],
          [4, 0, 0, 0],
          [0, 4, 0, 0],
          [0, 0, 4, 0]]
IDENTITY4 = [[1 if i == j else 0 for j in range(4)] for i in range(4)]


def causal_attention(Q, K, V):
    d = len(Q[0])
    scores = [[dot(q, k) / math.sqrt(d) for k in K] for q in Q]
    masked = [[s if j <= i else float("-inf") for j, s in enumerate(row)]
              for i, row in enumerate(scores)]
    weights = [softmax(row) for row in masked]
    return scores, weights, matmul(weights, V)


def part3_attention():
    print("######## PART 3 -- Self-attention by hand ########\n")
    Q, K, V = matmul(ATT_X, ATT_WQ), matmul(ATT_X, IDENTITY4), matmul(ATT_X, IDENTITY4)
    scores, weights, out = causal_attention(Q, K, V)
    print("  raw scores = Q K^T / sqrt(4)   (row = query token, col = key token)")
    for t, row in zip(ATT_TOKENS, scores):
        print(f"    {t:<5}" + "".join(f"{s:>7.2f}" for s in row))
    print("\n  after causal mask + softmax (each row sums to 1; '-' = future, hidden):")
    for i, (t, row) in enumerate(zip(ATT_TOKENS, weights)):
        cells = "".join(f"{w:>7.2f}" if j <= i else "      -" for j, w in enumerate(row))
        print(f"    {t:<5}{cells}   sum={sum(row):.2f}")
    print("\n  as a heat map (@@ = strong, .. = weak):")
    for i, (t, row) in enumerate(zip(ATT_TOKENS, weights)):
        print(f"    {t:<5} " + " ".join(shade(w) if j <= i else " -" for j, w in enumerate(row)))
    print("\n  what each token reads (V = identity, so output = mix of tokens):")
    for i, t in enumerate(ATT_TOKENS):
        j = max(range(i + 1), key=lambda j: weights[i][j])
        print(f"    {t:<4} attends most to {ATT_TOKENS[j]!r:<6} ({weights[i][j]:.2f})"
              f"  output={fmt(out[i])}")
    print("\n  The mask is why generation works left-to-right: during training")
    print("  token i can't cheat by looking at token i+1, the one it must predict.\n")


# ============================================================================
# PART 4: Multi-head attention -- several questions at once
# ============================================================================
#   x ──┬─▶ head 1: "who came just before me?"   ─▶ out1 (7 dims) ─┐
#       └─▶ head 2: "where did MY word appear?"  ─▶ out2 (7 dims) ─┴▶ concat
#                                                    (14) ─▶ Wo ─▶ back to d
#   head1 + head2 together = an "induction head": see "the" again, recall
#   what followed it last time ("cat"), predict it. Real models: 32-128 heads.

MH_TOKENS = ["the", "cat", "saw", "a", "dog", ".", "the", "cat", "ran"]


def multihead_inputs():
    words = sorted(set(MH_TOKENS), key=MH_TOKENS.index)
    W, T = len(words), len(MH_TOKENS)
    X = [[1.0 if c == words.index(tok) or c == W + p else 0.0 for c in range(W + T)]
         for p, tok in enumerate(MH_TOKENS)]   # [word one-hot | position one-hot]
    return words, X, W, T


def part4_multihead():
    print("######## PART 4 -- Multi-head attention ########\n")
    words, X, W, T = multihead_inputs()
    D = W + T
    big = 5 * math.sqrt(D)                      # strong enough to survive / sqrt(d)
    zeros = lambda: [[0.0] * D for _ in range(D)]
    wq1, wq2, wk_pos, wk_all = zeros(), zeros(), zeros(), zeros()
    for p in range(1, T):
        wq1[W + p][W + p - 1] = big            # position p asks for position p-1
    for c in range(D):
        wq2[c][c] = big if c < W else -big      # same word: +big, same position: -big
        wk_all[c][c] = 1.0
        if c >= W:
            wk_pos[c][c] = 1.0
    wv = [[1.0 if r == c and r < W else 0.0 for c in range(W)] for r in range(D)]
    V = matmul(X, wv)                          # value = the token's word identity
    heads = [causal_attention(matmul(X, wq1), matmul(X, wk_pos), V),
             causal_attention(matmul(X, wq2), matmul(X, wk_all), V)]
    print(f"  {T} tokens, d_model={D}, 2 heads, each head output = {W} dims\n")
    print(f"    {'pos':>3} {'token':<5}  head 1 (previous token)   head 2 (earlier copy of me)")
    for i, tok in enumerate(MH_TOKENS):
        cells = []
        for _, weights, _ in heads:
            j = max(range(i + 1), key=lambda j: weights[i][j])
            w = weights[i][j]
            cells.append(f"-> {MH_TOKENS[j]}@{j} ({w:.2f})" if w > 0.5 else f"spread (max {w:.2f})")
        print(f"    {i:>3} {tok:<5}  {cells[0]:<25} {cells[1]}")
    concat = heads[0][2][7] + heads[1][2][7]
    print(f"\n  token 7 ('cat'): concat(head1, head2) = {len(concat)} dims; "
          f"then Wo projects back to {D}")
    for name, (_, _, out) in zip(["head 1", "head 2"], heads):
        top = max(range(W), key=lambda c: out[6][c])
        print(f"  {name} output at pos 6 ('the') is {out[6][top]:.2f} x '{words[top]}'")
    print("\n  Neither head was told what to do in a real model -- training")
    print("  discovers useful heads like these (previous-token, induction,")
    print("  'find the subject', 'match the bracket') on its own.\n")


# ============================================================================
# PART 5: Positional information -- order must be injected
# ============================================================================
#   "dog bites man"  ─┐  attention without position sees a SET of tokens:
#   "man bites dog"  ─┘  {dog, bites, man} == {man, bites, dog}  ─▶ same output
#   fix: x = embedding(token) + PE(position)
#   PE(pos)[2i] = sin(pos / 10000^(2i/d))   PE(pos)[2i+1] = cos(same)
#   fast dims ▶ wiggle every token   slow dims ▶ drift over hundreds of tokens
#   together they give each position a unique, smoothly-varying fingerprint

def sinusoidal(pos, d=8):
    return [math.sin(pos / 10000 ** (2 * (i // 2) / d)) if i % 2 == 0
            else math.cos(pos / 10000 ** (2 * (i // 2) / d)) for i in range(d)]


def encode(words, emb, wq, wk, wv, use_position):
    X = [add(emb[w], sinusoidal(p)) if use_position else emb[w] for p, w in enumerate(words)]
    Q, K, V = matmul(X, wq), matmul(X, wk), matmul(X, wv)
    W = [softmax([dot(q, k) / math.sqrt(len(q)) for k in K]) for q in Q]  # no mask
    out = matmul(W, V)
    return {w: o for w, o in zip(words, out)}, [sum(c) / len(out) for c in zip(*out)]


def part5_position():
    print("######## PART 5 -- Positional information ########\n")
    rng = random.Random(5)
    emb = {w: [rng.gauss(0, 1) for _ in range(8)] for w in ["dog", "bites", "man"]}
    wq, wk, wv = (list(map(list, zip(*rand_matrix(rng, 8, 8)))) for _ in range(3))
    a, b = "dog bites man".split(), "man bites dog".split()
    for use_pos in (False, True):
        out_a, pooled_a = encode(a, emb, wq, wk, wv, use_pos)
        out_b, pooled_b = encode(b, emb, wq, wk, wv, use_pos)
        diff = max(abs(x - y) for x, y in zip(out_a["bites"], out_b["bites"]))
        print(f"  {'WITH' if use_pos else 'WITHOUT'} position:")
        print(f"    'bites' vector, max |difference| between sentences = {diff:.6f}")
        print(f"    whole-sentence vectors, cosine = {cosine(pooled_a, pooled_b):.6f}")
    print("\n  Without position, the two sentences are literally identical to the")
    print("  model (difference is 0 up to float rounding). Adding PE fixes it.\n")
    print("  sinusoidal PE (d=64): nearby positions look alike, far ones differ:")
    for k in [0, 1, 2, 4, 8, 16]:
        c = cosine(sinusoidal(10, 64), sinusoidal(10 + k, 64))
        print(f"    cos(PE(10), PE({10 + k:>2})) = {c:+.3f}  {'#' * max(0, round(c * 30))}")
    print("\n  Modern LLMs mostly use RoPE (rotate Q and K by a position-dependent")
    print("  angle) -- same goal: let attention know WHERE each token is.\n")


# ============================================================================
# PART 6: Generation and the KV cache -- measured
# ============================================================================
#   NO CACHE: step t recomputes all t tokens     WITH CACHE: only the new one
#   step 5   █████                                █
#   step 6   ██████                               █ (+ read 6 cached K,V)
#   step 20  ████████████████████                 █ (+ read 20 cached K,V)
#   total    ~ sum of 1..20 = O(n^2) token-passes ~ 20 token-passes = O(n)
#   Keys/values of past tokens never change (causal mask!) so caching is exact.

def generate(model, prompt_ids, total, use_cache):
    """Greedy generation; returns ids, logits per step, mults per step, total mults."""
    ids, all_logits, costs = list(prompt_ids), [], []
    caches = model.new_cache()
    MULS[0] = 0
    while len(ids) < total:
        before = MULS[0]
        if not use_cache:                       # rebuild the whole sequence every step
            logits = model.forward(ids)
        elif len(ids) == len(prompt_ids):       # prefill: the prompt, once
            for pos, t in enumerate(ids):
                logits = model.step(t, pos, caches, want_logits=(pos == len(ids) - 1))
        else:                                   # decode: only the newest token
            logits = model.step(ids[-1], len(ids) - 1, caches)
        costs.append(MULS[0] - before)
        all_logits.append(logits)
        ids.append(max(range(len(VOCAB)), key=lambda i: logits[i]))  # greedy (lesson 02)
    return ids, all_logits, costs, MULS[0]


def part6_kv_cache():
    print("######## PART 6 -- Generation and the KV cache ########\n")
    model = TinyTransformer()
    prompt = [TOK[w] for w in ["the", "cat", "sat", "on"]]
    ids_a, logits_a, steps_a, total_a = generate(model, prompt, 20, use_cache=False)
    ids_b, logits_b, steps_b, total_b = generate(model, prompt, 20, use_cache=True)
    diff = max(abs(x - y) for la, lb in zip(logits_a, logits_b) for x, y in zip(la, lb))
    print(f"  prompt 4 tokens, generate until 20 tokens (greedy, untrained model)")
    print(f"  output identical: {ids_a == ids_b}   max logit difference: {diff:.1e}\n")
    print(f"    {'new token #':>11}  {'mults, no cache':>16}  {'mults, KV cache':>16}")
    for k in [0, 1, 5, 10, len(steps_a) - 1]:
        note = "  (prefill: 4 prompt tokens)" if k == 0 else ""
        print(f"    {k + 5:>11}  {steps_a[k]:>16,}  {steps_b[k]:>16,}{note}")
    print(f"    {'TOTAL':>11}  {total_a:>16,}  {total_b:>16,}   "
          f"-> {total_a / total_b:.1f}x less work with the cache")
    print("\n  Why output tokens are slower and pricier than input tokens:")
    print("   - INPUT (prefill): all prompt tokens go through in ONE parallel pass")
    print(f"   - OUTPUT (decode): {len(ids_b) - len(prompt)} SEQUENTIAL passes here, one per token, each")
    print("     reading the whole KV cache from memory -- you can't parallelise")
    print("     token 12 before token 11 exists.\n")


# ============================================================================
# PART 7: Why context windows are limited -- n^2
# ============================================================================
#   every token attends to every earlier token ─▶ n x n score matrix
#   n=4  ████            n=8  ████████       2x the tokens
#        ████                 ████████   ─▶  4x the attention work
#        ████                 ...  (8 rows)
#   KV cache memory = 2 (K,V) x layers x kv_heads x head_dim x n x bytes

CFG_7B = dict(vocab=32000, d=4096, layers=32, heads=32, head_dim=128, d_ff=11008)


def kv_cache_bytes(n, cfg, kv_heads, bytes_per=2):
    return 2 * cfg["layers"] * kv_heads * cfg["head_dim"] * n * bytes_per


def part7_context_cost():
    print("######## PART 7 -- Why context windows are limited ########\n")
    c = CFG_7B
    weights = params_formula(**{k: c[k] for k in ("vocab", "d", "layers", "d_ff")}, gated=True)
    print(f"  7B-like config: {c['layers']} layers, {c['heads']} heads x {c['head_dim']} "
          f"dims, fp16 (2 bytes/value)\n")
    print(f"  {'n tokens':>9}  {'weight mults':>12}  {'attention mults':>15}  "
          f"{'attn/weights':>12}  {'KV cache MHA':>12}  {'KV cache GQA-8':>14}")
    for n in [1_000, 4_000, 32_000, 128_000, 1_000_000]:
        w_mults = weights * n                                # each weight used once per token
        a_mults = c["layers"] * c["heads"] * c["head_dim"] * n * n  # QK^T + AV, causal half each
        mha = kv_cache_bytes(n, c, kv_heads=c["heads"]) / 2**30
        gqa = kv_cache_bytes(n, c, kv_heads=8) / 2**30
        print(f"  {n:>9,}  {w_mults:>12.2e}  {a_mults:>15.2e}  {a_mults / w_mults:>11.2f}x"
              f"  {mha:>9.1f} GiB  {gqa:>11.1f} GiB")
    per_tok = kv_cache_bytes(1, c, c["heads"])
    crossover = weights / (c["layers"] * c["heads"] * c["head_dim"])
    print(f"\n  KV cache per token: {per_tok:,} bytes = {per_tok / 2**20:.2f} MiB (full multi-head)")
    print(f"  At short n, the weights dominate. Past ~{crossover / 1000:.0f}k tokens, attention work")
    print("  overtakes them and grows 4x per doubling, while the KV cache alone")
    print("  outgrows a GPU. Grouped-query attention (GQA: 8 shared K/V heads),")
    print("  sliding windows and other tricks push the limit -- they don't remove it.\n")


# ============================================================================
# PART 8: "Lost in the middle" -- simulated
# ============================================================================
#   accuracy by where the fact sits in a 20-chunk context (real run below)
#   start  (0-3)   ████████░░░░░░░░░░░░  41%  primacy: system prompt / first
#   middle (8-11)  ██░░░░░░░░░░░░░░░░░░  12%  gets the least attention
#   end    (16-19) ███████████░░░░░░░░░  56%  recency: next to the question
#   (simulation of the U-shape measured by Liu et al., 2023)

def position_bias(i, n):
    return 1.2 * math.exp(-i / 3) + 1.6 * math.exp(-(n - 1 - i) / 3)


def retrieval_accuracy(fact_pos, n=20, trials=400, rng=None):
    hits = 0
    for _ in range(trials):
        scores = [position_bias(i, n) + rng.gauss(0, 0.6) + (1.0 if i == fact_pos else 0.0)
                  for i in range(n)]
        hits += max(range(n), key=scores.__getitem__) == fact_pos
    return hits / trials


def part8_lost_in_middle():
    print("######## PART 8 -- Lost in the middle ########\n")
    rng, n = random.Random(8), 20
    acc = [retrieval_accuracy(p, n, rng=rng) for p in range(n)]
    print(f"  {n} context chunks, 1 holds the answer; 400 trials per position.")
    print("  score = position bias + noise + relevance; model 'uses' the top chunk.\n")
    for p, a in enumerate(acc):
        print(f"    chunk {p:>2}  {a:4.0%}  {'#' * round(a * 40)}")
    for name, rngs in [("start (0-3)", range(0, 4)), ("middle (8-11)", range(8, 12)),
                       ("end (16-19)", range(16, 20))]:
        print(f"  avg {name:<14} {sum(acc[i] for i in rngs) / 4:.0%}")
    print("\n  This is why lesson 04 orders the context: stable instructions at the")
    print("  START, the question LAST, and the most important documents at the")
    print("  edges -- never buried in the middle of a long dump.\n")


# ============================================================================
# PART 9: Scale -- what parameters are, and how they get trained
# ============================================================================
#   per layer:  attention  Wq Wk Wv Wo         = 4 x d x d
#               MLP        W1 W2 (+W3 gated)   = 2 (or 3) x d x d_ff
#   plus        embedding V x d  (+ unembedding V x d if not tied)
#   training:   loss = -log P(actual next token), averaged; nudge every
#               weight a tiny bit downhill; repeat for trillions of tokens

def params_formula(vocab, d, layers, d_ff, max_len=0, gated=False, tied=False, norms=False):
    per_layer = 4 * d * d + (3 if gated else 2) * d * d_ff + (2 * d if norms else 0)
    return vocab * d * (1 if tied else 2) + max_len * d + layers * per_layer + (d if norms else 0)


def part9_scale_and_training():
    print("######## PART 9 -- Scale and the training objective ########\n")
    model = TinyTransformer()
    toy = params_formula(len(VOCAB), 16, 2, 64, max_len=32, tied=True)
    print(f"  toy model: counted {model.n_params():,} numbers, formula says {toy:,} "
          f"-> match: {model.n_params() == toy}")
    c = CFG_7B
    big = params_formula(c["vocab"], c["d"], c["layers"], c["d_ff"], gated=True, norms=True)
    attn, mlp = 4 * c["d"] ** 2, 3 * c["d"] * c["d_ff"]
    print(f"  7B-like (d={c['d']}, {c['layers']} layers, d_ff={c['d_ff']}, vocab={c['vocab']}):")
    print(f"    attention per layer {attn:>13,}")
    print(f"    MLP per layer       {mlp:>13,}   ({mlp / (attn + mlp):.0%} of each block)")
    print(f"    embed + unembed     {2 * c['vocab'] * c['d']:>13,}")
    print(f"    TOTAL               {big:>13,}   = {big / 1e9:.2f}B parameters")
    print(f"    memory at fp16      {big * 2 / 2**30:>10.1f} GiB just to hold the weights\n")

    words = ["<s>", "the", "cat", "sat", "on", "the", "mat", "."]
    caches, losses = model.new_cache(), []
    for pos in range(len(words) - 1):
        probs = softmax(model.step(TOK[words[pos]], pos, caches))
        losses.append(-math.log(probs[TOK[words[pos + 1]]]))
    print("  training objective on 'the cat sat on the mat .' (untrained toy):")
    for pos, loss in enumerate(losses):
        print(f"    after {words[pos]!r:<6} target {words[pos + 1]!r:<6} "
              f"P={math.exp(-loss):.3f}  loss={loss:.2f}")
    print(f"    mean cross-entropy = {sum(losses) / len(losses):.2f}  "
          f"(uniform guessing = ln({len(VOCAB)}) = {math.log(len(VOCAB)):.2f})")
    print("    random weights are confidently WRONG -- worse than guessing. Training")
    print("    pushes this number down; good LLMs reach ~2 on a 100k+ vocab.")
    print("\n  loss for different P(correct token):")
    for p in [0.99, 0.9, 0.5, 0.1, 0.01]:
        print(f"    P={p:<5} loss={-math.log(p):.2f}  {'#' * round(-math.log(p) * 6)}")
    print("\n  Training = compute this loss on trillions of tokens and use gradients")
    print("  to nudge all the parameters so the loss goes down. Every ability the")
    print("  model has is whatever helped predict the next token.\n")


# ============================================================================
# Demo
# ============================================================================

def main():
    part1_pipeline()
    part2_embeddings()
    part3_attention()
    part4_multihead()
    part5_position()
    part6_kv_cache()
    part7_context_cost()
    part8_lost_in_middle()
    part9_scale_and_training()

    print("######## Summary ########\n")
    print("  ids -> embeddings + position -> [attention + MLP] x N -> logits -> softmax")
    print("  - attention lets every token read earlier tokens (causal mask)")
    print("  - the KV cache makes each new token cost O(n), not O(n^2)")
    print("  - attention is n^2 and the cache grows with n: context has a price")
    print("  - position bias means WHERE you put facts in the prompt matters")


if __name__ == "__main__":
    main()

    # -- Key takeaway --------------------------------------------------------
    # A transformer is embeddings + repeated (attention, MLP) blocks + an
    # unembedding. Attention is the only place tokens talk to each other,
    # and its cost and biases explain context limits, output pricing, and
    # why prompt ordering matters.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. In part 3, change ATT_WQ's strength from 4 to 1. How sharp is the
    #    attention now? (Lower contrast = "blurrier" focus.)
    # 2. In part 7, set kv_heads=1 (multi-query attention). How long a
    #    context fits in 24 GiB of KV cache?
    # 3. In part 8, raise the relevance from 1.0 to 2.0 -- a clearer, more
    #    relevant fact survives the middle better. Why does RAG help here?
