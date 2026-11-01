r"""05 -- LAYERS: 28 rounds of "look around, then recall"
=====================================================

CONCEPT IN ONE LINE:
  Each token's 3,072 numbers go through 28 identical-looking LAYERS; each layer reads the
  vectors, ADDS a correction, and passes them on -- same shape out, richer meaning.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ [05 layers] ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax

  IN:   22 tokens x 3,072 numbers   (from 04: one embedding row per token)
  OUT:  22 tokens x 3,072 numbers   (same shape -- 06 uses only the LAST one)

WHAT HAPPENS -- ONE LAYER, TENSOR BY TENSOR (real names from the model file):

     x  (one token's 3,072 numbers)
     │
     ├──────────────────────────────┐   keep a copy of x for the ADD
     ▼                              │
   blk.N.attn_norm    (3,072)        │   1. RMSNorm: rescale x so its size is ~1, then
     │                              │      multiply by 3,072 learned weights
     ▼                              │
   blk.N.attn_q  (3,072 x 3,072)     │   2. make 3 new vectors from x:
   blk.N.attn_k  (3,072 x 1,024)     │      Q "what am I looking for?"   24 heads x 128
   blk.N.attn_v  (3,072 x 1,024)     │      K "what do I contain?"        8 heads x 128
     │                              │      V "what do I pass on?"        8 heads x 128
     ▼                              │
   ATTENTION (no weights of its own) │   3. each token compares its Q with the K of every
     │                              │      EARLIER token (causal: never the future),
     │                              │      softmax -> weights, takes a weighted mix of V
     ▼                              │
   blk.N.attn_output (3,072 x 3,072) │   4. mix the 24 heads' results back into 3,072
     │                              │
     ▼                              │
    (+) ◀────────────────────────────┘   5. ADD to the copy: x = x + attention_result
     │
     ├──────────────────────────────┐
     ▼                              │
   blk.N.ffn_norm     (3,072)        │   6. RMSNorm again
     ▼                              │
   blk.N.ffn_gate (3,072 x 8,192)    │   7. widen to 8,192 numbers, twice:
   blk.N.ffn_up   (3,072 x 8,192)    │      gate -> SiLU (a soft on/off switch)
     │                              │      up   -> the content;   multiply them together
     ▼                              │
   blk.N.ffn_down (8,192 x 3,072)    │   8. shrink back to 3,072
     ▼                              │
    (+) ◀────────────────────────────┘   9. ADD again: x = x + feed_forward_result
     │
     ▼
     x  for the next layer   (blk.0 -> blk.1 -> ... -> blk.27)

  This "keep x, ADD a correction" path is called the RESIDUAL STREAM. Nothing is replaced,
  each layer only writes on top -- that's why 28 layers can build up understanding.

THE PIECES, IN PLAIN WORDS:

  RMSNorm         divide the vector by its average size (root-mean-square), then scale each
                  of the 3,072 numbers by its own learned weight. Keeps numbers from blowing
                  up or shrinking away over 28 layers.
                     rms = sqrt( (x1² + x2² + ... + x3072²) / 3072 + 0.00001 )
                     out_i = x_i / rms * weight_i

  ATTENTION       " is" asks: which earlier tokens matter to me?
                     score(" is", t) = Q(" is") · K(t) / sqrt(128)     for every earlier t
                     softmax(scores) -> weights that add up to 1
                     result = sum of weight_t x V(t)
                  24 heads do this in parallel, each with its own 128-number slice, so each
                  head can watch for something different (grammar, which noun, position...).
  GQA             grouped-query attention: 24 Q heads but only 8 K/V heads -- every 3 Q heads
                  share one K/V head. Smaller attn_k / attn_v (1,024 wide, not 3,072) and a
                  3x smaller KV cache (lesson 10).
  CAUSAL          token 5 can only look at tokens 1-5. That's what lets the model generate
                  left to right, and lets earlier results be cached.
  RoPE            word ORDER is added inside attention by rotating Q and K by an angle that
                  depends on the position (rope_freqs.weight, rope.freq_base = 500,000).
  FEED-FORWARD    per token, on its own: 3,072 -> 8,192 -> 3,072. The "memory lookup" where
                  training stored facts like  capital + France -> Paris.
  SiLU            silu(x) = x / (1 + e^-x):  negative -> ~0 (off),  positive -> ~x (on)

WHAT IS A WEIGHT? (every tensor above is a box of them)

  A weight (also called a PARAMETER) is one learned number that gets MULTIPLIED with the
  input. That's all -- there are no rules or facts written anywhere in the model.

  THE SMALLEST EXAMPLE -- 2 inputs, 1 output:

     input:    x1 = 1.0     x2 = 0.5
     weights:  w1 = 0.8     w2 = -0.3

     output = x1 * w1  +  x2 * w2
            = 1.0 * 0.8  +  0.5 * (-0.3)
            = 0.8 - 0.15
            = 0.65

     w1 =  0.8    "input 1 matters a lot, and pushes the output UP"
     w2 = -0.3    "input 2 matters a little, and pushes the output DOWN"
     w  ≈  0      "ignore this input"
  Same input, different weights -> different output. That's why the weights ARE the knowledge.

  SCALED UP: attn_q turns 3,072 numbers into 3,072 new numbers. EVERY output number is the
  sum above, with all 3,072 inputs, each times its own weight:

     3,072 inputs  x  3,072 outputs  =  9,437,184 weights  =  the attn_q row in the table below
     one weight = "how much does input number i affect output number j"

  HOW WEIGHTS GET THEIR VALUES -- TRAINING (done once, by Meta, before you download):
     1. start with random numbers
     2. take real text, hide the next token:   "The capital of France is" -> ?
     3. let the model predict; measure how wrong it was ("error")
     4. nudge EVERY weight a tiny bit in the direction that lowers the error
        (the maths that finds that direction for all weights at once = BACKPROPAGATION)
     5. repeat over trillions of tokens

     The same thing on the 2-input example (real numbers -- main() STEP 0 computes them),
     wanted output 1.0, each step: weight -= 0.1 x 2 x error x its input
        start    w = [0.8,    -0.3   ]   output 0.65     error -0.35
        step 1   w = [0.87,   -0.265 ]   output 0.7375
        step 2   w = [0.9225, -0.2388]   output 0.8031
        ...
        step 8   w = [1.052,  -0.174 ]   output 0.965    <- creeping towards 1.0
     llama3.2 did this with 3.2 BILLION weights at once. No single weight "contains" Paris --
     the fact is spread over millions of them.

  After training the weights are FROZEN. Running the model (every lesson here) = INFERENCE:
  the weights are only read, never changed. Your prompts don't teach it anything.

  WHY THE NUMBER OF WEIGHTS MATTERS:
     file size   3.2 B x 2 bytes (16-bit) ≈ 6.4 GB;  Ollama's ~4-5 bits each (Q4_K/Q6_K) ≈ 2.0 GB
     memory      ALL of them must be loaded to run (01_request.py: load_duration)
     speed       every generated token is multiplied through almost all of them (STEP 5)
     quality     more weights = more it can store   (llama3.1 70B >> llama3.2 3B)

  WEIGHTS vs THE OTHER NUMBERS IN THIS FOLDER:
     number     what it is                                 changes?
     weight     learned number in the model file           only in training, then frozen
     vector     the 3,072 numbers for YOUR token right     new for every prompt
                now (also called "activations")
     ID         a token's position in the vocabulary (03)  never   (" France" = 9822)
     byte       a character's number (01c)                 never   ('P' = 80)

PARAMETER COUNT, FROM THE REAL SHAPES (main() recomputes this from the file):

     tensor          shape              numbers
     attn_norm       3,072                    3,072
     attn_q          3,072 x 3,072        9,437,184
     attn_k          3,072 x 1,024        3,145,728
     attn_v          3,072 x 1,024        3,145,728
     attn_output     3,072 x 3,072        9,437,184
     ffn_norm        3,072                    3,072
     ffn_gate        3,072 x 8,192       25,165,824
     ffn_up          3,072 x 8,192       25,165,824
     ffn_down        8,192 x 3,072       25,165,824
                                       ─────────────
     one layer                          100,669,440      x 28 = 2,818,744,320  (87.7%)

  Feed-forward = 75% of a layer: most of the "knowledge" lives there.

  THE WHOLE MODEL:
     embedding table (04)     128,256 x 3,072       394,002,432   12.3%
     28 layers                28 x 100,669,440    2,818,744,320   87.7%
     output_norm (06)         3,072                       3,072
     rope_freqs               64                             64
                                                  ─────────────
     total = general.parameter_count              3,212,749,888   exact match

  COST: every new token passes through ALL 28 layers, one after another (layer 5 needs
  layer 4's output). ~2.8 billion weights read per token -> ~40-50 ms per token on this PC.

WHERE THIS COMES FROM:

  what                            who made it                where you find it
  the DESIGN (28 layers, GQA,     Meta (Llama 3 paper)       GGUF metadata: llama.block_count,
   RMSNorm, SiLU, RoPE)                                      llama.attention.head_count(_kv),
                                                             llama.feed_forward_length
  the WEIGHTS in each tensor      Meta's training run        GGUF tensors blk.0.* ... blk.27.*
  the 4-bit packing (Q4_K/Q6_K)   the GGUF converter         tensor "type" in the tensor table
  running the maths               Ollama's engine (ggml /    on your CPU/GPU, per request
                                  llama.cpp family)

IS IT OLLAMA-SPECIFIC?

  the model itself   28 layers is part of llama3.2-3B -- the same in every program
  Ollama             runs them; shows the shape in /api/show (llama.block_count = 28)
  OpenAI             layers exist but are secret -- no layer count is published for GPT models
  Anthropic          same: not published, not visible through the API
  Hugging Face       config.json: num_hidden_layers 28, hidden_size 3072,
                     intermediate_size 8192, num_attention_heads 24, num_key_value_heads 8;
                     with output_hidden_states=True you can even get each layer's output

COMMON CONFUSIONS:

  - "layer" here = one transformer BLOCK (GGUF calls it block_count). Not the same as the
    "layers" in an Ollama download (those are files: model, template, license, params).
  - all 28 layers have the same DESIGN but different WEIGHTS -- they are not copies.
  - layers don't change the shape: 3,072 in, 3,072 out. Only the meaning changes.
  - attention has no weights of its own -- its "weights" (0.05, 0.40, ...) are computed
    fresh for every prompt. The learned weights are Q, K, V, O.

SEE IT VISUALLY:
   https://bbycroft.net/llm                          step through every layer in 3D
   https://poloclub.github.io/transformer-explainer/ attention + MLP, live in the browser
   https://www.3blue1brown.com/lessons/attention     attention explained with animation
"""

import math
import sys

import httpx

from gguf_reader import embedding_row, read_f32, read_gguf

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def rms_norm(x, weight, eps=1e-5):
    rms = math.sqrt(sum(v * v for v in x) / len(x) + eps)
    return [v / rms * w for v, w in zip(x, weight)], rms


def softmax(scores):
    top = max(scores)
    exps = [math.exp(s - top) for s in scores]
    return [e / sum(exps) for e in exps]


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    print("STEP 0: what a weight does, and how training nudges it (2 inputs, 1 output)")
    x, w, wanted = [1.0, 0.5], [0.8, -0.3], 1.0
    out = sum(xi * wi for xi, wi in zip(x, w))                  # multiply, add up
    print(f"  output = 1.0*0.8 + 0.5*(-0.3) = {out}")
    for step in range(1, 9):
        error = sum(xi * wi for xi, wi in zip(x, w)) - wanted
        w = [wi - 0.1 * 2 * error * xi for xi, wi in zip(x, w)]  # the nudge (gradient descent)
        if step in (1, 2, 8):
            print(f"  step {step}  w = {[round(v, 4) for v in w]}"
                  f"  output {sum(xi * wi for xi, wi in zip(x, w)):.4f}")
    # -> STEP 0: what a weight does, and how training nudges it (2 inputs, 1 output)
    #      output = 1.0*0.8 + 0.5*(-0.3) = 0.65
    #      step 1  w = [0.87, -0.265]  output 0.7375
    #      step 2  w = [0.9225, -0.2388]  output 0.8031
    #      step 8  w = [1.052, -0.174]  output 0.9650      <- towards the wanted 1.0

    meta, tensors, path = read_gguf()

    print("\nSTEP 1: the real tensors of layer 0 (blk.0.*) in the model file")
    total_layer = 0
    for name, t in tensors.items():
        if name.startswith("blk.0."):
            n = math.prod(t["shape"])
            total_layer += n
            print(f"  {name:26} {str(t['shape']):16} {t['type']:5} {n:>12,}")
    print(f"  one layer = {total_layer:,} numbers")
    layers = sorted({int(n.split('.')[1]) for n in tensors if n.startswith("blk.")})
    print(f"  layers in file: blk.{layers[0]} ... blk.{layers[-1]} = {len(layers)}"
          f"   (llama.block_count = {meta['llama.block_count']})")
    print(f"  28 x {total_layer:,} = {28 * total_layer:,}")
    # -> STEP 1: the real tensors of layer 0 (blk.0.*) in the model file
    #      blk.0.attn_norm.weight     (3072,)          F32          3,072
    #      blk.0.ffn_down.weight      (8192, 3072)     Q6_K    25,165,824
    #      blk.0.ffn_gate.weight      (3072, 8192)     Q4_K    25,165,824
    #      blk.0.ffn_up.weight        (3072, 8192)     Q4_K    25,165,824
    #      blk.0.ffn_norm.weight      (3072,)          F32          3,072
    #      blk.0.attn_k.weight        (3072, 1024)     Q4_K     3,145,728
    #      blk.0.attn_output.weight   (3072, 3072)     Q4_K     9,437,184
    #      blk.0.attn_q.weight        (3072, 3072)     Q4_K     9,437,184
    #      blk.0.attn_v.weight        (3072, 1024)     Q6_K     3,145,728
    #      one layer = 100,669,440 numbers
    #      layers in file: blk.0 ... blk.27 = 28   (llama.block_count = 28)
    #      28 x 100,669,440 = 2,818,744,320
    # (file order is how the converter wrote them, not the order they run in)

    print("\nSTEP 2: the FIRST thing layer 0 does -- real RMSNorm on the real ' France' row")
    france_id = meta["tokenizer.ggml.tokens"].index("ĠFrance")          # 'Ġ' = space
    x = embedding_row(france_id, tensors, path)                          # lesson 04
    w = read_f32(tensors, path, "blk.0.attn_norm.weight")
    y, rms = rms_norm(x, w, meta["llama.attention.layer_norm_rms_epsilon"])
    print(f"  ' France' = ID {france_id}")
    print("  before   x[:6] =", [round(v, 4) for v in x[:6]])
    print("  weights  w[:6] =", [round(v, 4) for v in w[:6]])
    print(f"  rms = sqrt(mean(x²) + eps) = {rms:.5f}")
    print("  after    y[:6] =", [round(v, 4) for v in y[:6]], "  (y = x / rms * w)")
    # -> STEP 2: the FIRST thing layer 0 does -- real RMSNorm on the real ' France' row
    #      ' France' = ID 9822
    #      before   x[:6] = [-0.0272, 0.0199, -0.0084, -0.0073, 0.001, 0.0084]
    #      weights  w[:6] = [0.0645, 0.0977, 0.3945, 0.0635, -0.0065, -0.064]
    #      rms = sqrt(mean(x²) + eps) = 0.01873
    #      after    y[:6] = [-0.0936, 0.1036, -0.1762, -0.0248, -0.0004, -0.0286]   (y = x / rms * w)
    # Each of the 3,072 positions has its OWN learned weight: position 2 is boosted (0.39),
    # position 4 almost switched off (-0.0065).
    # That's real: same numbers Ollama computes first for ' France'. The next steps
    # (attn_q, ...) are 4-bit packed matrices -- too slow to unpack in plain Python.

    print("\nSTEP 3: attention, on a TOY example (4 tokens x 4 numbers, illustrative)")
    words = ["The", " capital", " of", " France"]
    q = [1.0, 0.0, 1.0, 0.0]                       # Q of " France": "looking for a place-word"
    k = [[0.1, 0.2, 0.0, 0.1],                     # K of each token: "what I contain"
         [0.9, 0.1, 0.8, 0.0],                     #   " capital" matches the question well
         [0.0, 0.3, 0.1, 0.2],
         [0.5, 0.0, 0.4, 0.1]]
    v = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]   # V: what each passes on
    scores = [sum(a * b for a, b in zip(q, kt)) / math.sqrt(4) for kt in k]   # Q·K / sqrt(size)
    weights = softmax(scores)
    mixed = [sum(weights[t] * v[t][d] for t in range(4)) for d in range(4)]
    for word, s, wt in zip(words, scores, weights):
        print(f"  ' France' -> {word!r:11} score {s:5.2f}   weight {wt:.2f}")
    print("  result = weighted mix of V:", [round(m, 2) for m in mixed])
    print("  causal mask: ' of' may look at", words[:3], "-- never at ' France' (the future)")
    # -> STEP 3: attention, on a TOY example (4 tokens x 4 numbers, illustrative)
    #      ' France' -> 'The'       score  0.05   weight 0.17
    #      ' France' -> ' capital'  score  0.85   weight 0.39     <- pays most attention here
    #      ' France' -> ' of'       score  0.05   weight 0.17
    #      ' France' -> ' France'   score  0.45   weight 0.26
    #      result = weighted mix of V: [0.17, 0.39, 0.17, 0.26]
    #      causal mask: ' of' may look at ['The', ' capital', ' of'] -- never at ' France' (the future)

    print("\nSTEP 4: SiLU, the on/off switch in the feed-forward part")
    for val in [-4, -1, 0, 1, 4]:
        print(f"  silu({val:>2}) = {val / (1 + math.exp(-val)):6.3f}")
    # -> silu(-4) = -0.072   silu(-1) = -0.269   silu( 0) =  0.000
    #    silu( 1) =  0.731   silu( 4) =  3.928         negative -> ~0, positive -> ~itself

    print("\nSTEP 5: live -- every generated token goes through all 28 layers")
    body = {"model": CHAT_MODEL, "prompt": "Write two sentences about Paris.", "stream": False,
            "options": {"temperature": 0, "num_predict": 40}}
    r = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300).json()
    ms = r["eval_duration"] / r["eval_count"] / 1e6
    print(f"  {r['eval_count']} tokens in {r['eval_duration'] / 1e9:.2f} s"
          f" = {ms:.0f} ms per token = {ms / 28:.1f} ms per layer pass")
    print(f"  = {r['eval_count'] * 28:,} layer passes for this answer")
    # -> STEP 5: live -- every generated token goes through all 28 layers
    #      40 tokens in 1.94 s = 49 ms per token = 1.7 ms per layer pass
    #      = 1,120 layer passes for this answer
    # (your numbers depend on your CPU/GPU; ms-per-layer is a rough average)


if __name__ == "__main__":
    main()

# Try: change "blk.0." to "blk.27." in STEP 1 -- same names and shapes, different weights.
#      In STEP 2 use blk.27.attn_norm.weight: the same x comes out scaled differently.
