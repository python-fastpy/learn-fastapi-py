r"""04 -- VECTORS: each token ID becomes a list of 3,072 numbers
==============================================================

CONCEPT IN ONE LINE:
  An ID is just a position. The model looks up ROW number <ID> in a big learned table and
  from then on works with that row of 3,072 numbers -- the token's "meaning". Here we read
  REAL rows out of llama3.2's model file and compare them.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ [04 vectors] ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax

  IN:   22 IDs   [128000, 128006, 882, 128007, 271, 12833, 279, 11914, 449, 832, 3492, 25,
                  578, 6864, 315, 9822, 374, 128009, 128006, 78191, 128007, 271]
  OUT:  22 vectors x 3,072 numbers  -> the input of layer 1 (lesson 05)

WHAT HAPPENS -- a lookup, no maths:

  STEP 1 -- THE TABLE. Think of a giant spreadsheet stored in the model file
  (tensor "token_embd.weight"). Real values, first 5 columns shown:

                                 col 1    col 2    col 3    col 4    col 5   ...  col 3,072
                               ┌──────────────────────────────────────────────────────────┐
     row 0        "!"          │  0.0112   0.0097   0.0142   0.0239  -0.0045   ...         │
     row 1        '"'          │   ...                                                    │
      ...                      │                                                          │
     row 9822     " France"    │ -0.0272   0.0199  -0.0084  -0.0073   0.0010   ...         │
      ...                      │                                                          │
     row 128255   (reserved)   │ -0.0029   0.0022   0.0050  -0.0093   0.0165   ...         │
                               └──────────────────────────────────────────────────────────┘

     ROWS      128,256   one per token in the vocabulary (lesson 03) -- row number = token ID
     COLUMNS     3,072   the vector size -- the same for every token
     SIZE      128,256 x 3,072 = 394,002,432 numbers  (12.3% of all 3.2 B weights)
     WHO       the numbers were LEARNED in training (Meta); the row ORDER comes from the vocabulary

  STEP 2 -- THE LOOKUP. The ID is simply the row number:

     " France"  ──(03)──▶  ID 9822  ──(04)──▶  go to row 9822  ──▶  its 3,072 numbers:
        [-0.0272, 0.0199, -0.0084, -0.0073, 0.001, 0.0084, 0.0136, -0.0073, and 3,064 more]

     in Python:  vector = table[9822]     no multiplying, no adding -- just "read that row"

  STEP 3 -- THE WHOLE PROMPT. One lookup per ID, in order:

     #    token                 ID        row read          result
     1    <|begin_of_text|>     128000    row 128000   ->   3,072 numbers
     2    <|start_header_id|>   128006    row 128006   ->   3,072 numbers
     ...
     16   " France"             9822      row 9822     ->   3,072 numbers
     ...
     22   "\n\n"                271       row 271      ->   3,072 numbers
                                                            ─────────────────────
                                                            22 x 3,072 numbers -> layer 1 (05)

     The same ID twice gets the SAME row twice (128006 and 271 each appear 2x in the
     prompt). Here a token has no idea what is next to it -- that's added in 05.

  The numbers on their own mean nothing to a human. What matters is how rows COMPARE.
  Training moved the rows so that tokens used in similar places get similar rows.

  REAL SIMILARITIES from the file (cosine similarity: 1 = same direction, 0 = unrelated):

     " France"  vs " Germany"   0.475     countries
     " France"  vs " Italy"     0.463
     " France"  vs " Paris"     0.448     country <-> its capital
     " Paris"   vs " Berlin"    0.348     capitals
     " king"    vs " queen"     0.537
     " banana"  vs " apple"     0.274     fruits
     " France"  vs " banana"    0.052     unrelated -> near 0
     " France"  vs " the"      -0.054

  COSINE SIMILARITY -- a tiny worked example with 3 numbers instead of 3,072:

     a = [1, 2, 0]      b = [2, 3, 1]

     a·b    = 1*2 + 2*3 + 0*1             = 8         ("dot product": multiply pairs, add)
     |a|    = sqrt(1*1 + 2*2 + 0*0)       = sqrt(5)  = 2.236     (length of a)
     |b|    = sqrt(2*2 + 3*3 + 1*1)       = sqrt(14) = 3.742
     cosine = 8 / (2.236 * 3.742)         = 0.956     -> pointing almost the same way

     Same formula for the real rows, just 3,072 pairs instead of 3.

  HOW ONE ROW IS STORED (Q6_K, the format of this table in Ollama's download):

     3,072 numbers = 12 blocks of 256
     one block = 210 bytes:
        128 bytes  low 4 bits of each number    ┐
         64 bytes  high 2 bits of each number   ├─ 256 small integers, 6 bits each (-32..31)
         16 bytes  16 scales (one per 16 nums)  │
          2 bytes  one 16-bit block scale "d"   ┘
     number = d x scale x small_integer           (gguf_reader._dequantize_q6_k)
     one row = 12 x 210 = 2,520 bytes  (vs 3,072 x 2 = 6,144 bytes at 16-bit)

  RULES THAT SURPRISE PEOPLE:
     - SAME ID -> SAME ROW, in every sentence. " bank" (river) and " bank" (money) start
       identical; the LAYERS (05) add the context.
     - "France" (ID 50100) and " France" (ID 9822) are DIFFERENT rows -- the space matters
       (real cosine 0.859: training made them close, but not the same).
     - word ORDER is not in the row. llama3.2 adds position later, inside attention (RoPE).
     - the SAME table is used again at the very end (06_scores.py, "tied" embeddings).

WHERE THIS COMES FROM:

   piece                         who made it                    where it lives
   the 394 M numbers             Meta's TRAINING (learned)      GGUF tensor token_embd.weight,
                                                                shape (3072, 128256), type Q6_K
   3,072 (row length)            Meta's design choice           GGUF key llama.embedding_length
   128,256 (row count)           = vocabulary size (03)         GGUF key llama.vocab_size
   the lookup                    Ollama (llama.cpp engine)      inside /api/generate, invisible

IS IT OLLAMA-SPECIFIC?  No -- every LLM starts with an embedding lookup.

   who                what you can see
   the model itself   the table is part of the weights (different for every model)
   Ollama             nothing -- the rows are hidden; this file reads them from the .gguf
   OpenAI             nothing -- weights are private
   Anthropic          nothing -- weights are private
   Hugging Face       everything: model.get_input_embeddings().weight[9822]

   sizes differ:  GPT-2 50,257 x 768     llama3.2 128,256 x 3,072     llama3.1 70B 128,256 x 8,192

COMMON CONFUSIONS:
   - these are TOKEN embeddings (one row per token, no context). The /api/embed endpoint
     (lesson 14) is different: ONE vector for a WHOLE text, made by an embedding model after
     all its layers. The Ollama server used here refuses /api/embed for llama3.2 (it was
     started without embeddings support -- see STEP 4).
   - "embedding", "vector", "hidden state", "activation" -- all lists of numbers. The
     embedding is the FIRST one (before layer 1); the rest are what the layers produce.
   - the similarity numbers are modest (0.4-0.5) because a token row has to serve many
     uses at once; after the layers, contextual vectors separate meanings much more.

SEE IT VISUALLY:
   https://projector.tensorflow.org/        word vectors as 3D dots; search "france"
   https://bbycroft.net/llm                 the embedding table as the first block of a GPT
"""

import math
import sys

import httpx

from gguf_reader import embedding_row, read_gguf

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))                   # multiply pairs, add up
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    meta, tensors, path = read_gguf()
    ids = {tok: i for i, tok in enumerate(meta["tokenizer.ggml.tokens"])}

    def row(text):                                           # " France" -> its 3,072 numbers
        return embedding_row(ids[text.replace(" ", "Ġ")], tensors, path)

    print("STEP 1: the table in the model file")
    t = tensors["token_embd.weight"]
    print("token_embd.weight", t["shape"], t["type"], f"{t['shape'][0] * t['shape'][1]:,} numbers")
    # -> token_embd.weight (3072, 128256) Q6_K 394,002,432 numbers

    print("\nSTEP 2: one row = one token's vector")
    france = row(" France")
    print("ID", ids["ĠFrance"], "length", len(france))
    print("first 8:", [round(x, 4) for x in france[:8]])
    print("min", round(min(france), 4), "max", round(max(france), 4),
          "length (norm)", round(math.sqrt(sum(x * x for x in france)), 3))
    # -> ID 9822 length 3072
    #    first 8: [-0.0272, 0.0199, -0.0084, -0.0073, 0.001, 0.0084, 0.0136, -0.0073]
    #    min -0.0724 max 0.0637 length (norm) 1.023      <- small numbers, many of them

    print("\nSTEP 3: compare rows (cosine similarity)")
    pairs = [(" France", " Germany"), (" France", " Italy"), (" France", " Paris"),
             (" Paris", " Berlin"), (" king", " queen"), (" banana", " apple"),
             (" France", " banana"), (" France", " the")]
    for a, b in pairs:
        print(f"{a!r:11} vs {b!r:11} {cosine(row(a), row(b)):6.3f}")
    nospace = embedding_row(ids["France"], tensors, path)
    print(f"{'France'!r:11} vs {' France'!r:11} {cosine(nospace, france):6.3f}   <- different IDs, different rows")
    # -> ' France'   vs ' Germany'   0.475
    #    ' France'   vs ' Italy'     0.463
    #    ' France'   vs ' Paris'     0.448
    #    ' Paris'    vs ' Berlin'    0.348
    #    ' king'     vs ' queen'     0.537
    #    ' banana'   vs ' apple'     0.274
    #    ' France'   vs ' banana'    0.052
    #    ' France'   vs ' the'      -0.054
    #    'France'    vs ' France'    0.859   <- different IDs, different rows (similar, not equal)

    print("\nSTEP 4: /api/embed is a DIFFERENT thing (one vector per whole text)")
    body = {"model": CHAT_MODEL, "input": "The capital of France is"}
    r = httpx.post(OLLAMA + "/api/embed", json=body, timeout=300)
    if r.status_code == 200:
        vec = r.json()["embeddings"][0]
        print("one vector for the whole text, length", len(vec))
    else:
        print(r.status_code, r.json().get("error"))
    # -> 501 This server does not support embeddings. Start it with `--embeddings`
    #    (on a server with embeddings on you'd get one vector for the whole text;
    #     lesson 14 uses a dedicated embedding model, nomic-embed-text)


if __name__ == "__main__":
    main()

# Try: add (" Monday", " Tuesday") and (" cat", " dog") to the pairs list.
