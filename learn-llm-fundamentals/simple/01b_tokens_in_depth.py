"""01b -- Tokens  (simple version)
=================================

IN ONE LINE:
  An LLM never reads letters. It reads TOKENS: small pieces of text,
  each one turned into a number (an id).

REAL USE CASE:
  Your FastAPI app sends "Hello world!" to the model. You pay per token:

     "Hello world!"
          │  cut into chunks, then bytes:   H e l l o | _ w o r l d !
          ▼
     "Hello" | " world" | "!"        <- bytes glued into pieces (BPE)
          │  look up each piece's id
          ▼
     [812, 1043, 33]  ──▶  MODEL     (3 tokens = what you pay for)

WHERE THE TOKENIZER SITS IN A REAL APP:

  ┌──────────────┐  POST /chat   ┌──────────────────┐  HTTPS   ┌─────────────────────────────┐
  │   Browser    │ ────────────▶ │  YOUR FASTAPI    │ ───────▶ │        LLM PROVIDER         │
  │ "the cat is  │               │  sends text      │   text   │  TOKENIZER: text ──▶ ids    │
  │  running"    │               │  (not tokens)    │          │  MODEL:     ids  ──▶ ids    │
  │              │ ◀──────────── │  reads usage =   │ ◀─────── │  TOKENIZER: ids  ──▶ text   │
  └──────────────┘    answer     │  tokens = $$$    │  text +  │  counts tokens for the bill │
                                 └──────────────────┘  usage   └─────────────────────────────┘

TWO PHASES -- build the tokenizer once, then use it on every call:

  TRAINING (once)                                USING IT (every API call)
  ┌──────────────────────────────────────┐       ┌──────────────────────────────────────┐
  │ lots of text                         │       │ your text                            │
  │   │                                  │       │   │                                  │
  │   ▼                                  │       │   ▼                                  │
  │ cut into chunks, then single bytes   │       │ cut into chunks, then bytes (STEP 1) │
  │   (STEP 1)                           │ ────▶ │   │                                  │
  │   │                                  │ merge │   ▼                                  │
  │   ▼                                  │ list  │ apply the merges, in the same order  │
  │ count pairs, glue the most common,   │ is    │   │                                  │
  │ repeat 30 times  (STEP 2)            │ fixed │   ▼                                  │
  │   │                                  │ now   │ look up the id of each piece (STEP 3)│
  │   ▼                                  │       │   │                                  │
  │ merge list + vocab (286 pieces)      │       │   ▼                                  │
  └──────────────────────────────────────┘       │ ids ──▶ model                        │
                                                 └──────────────────────────────────────┘

ONE FULL ENCODE, step by step (the real run printed by STEP 3, "the cat is running"):

   chunk        start (1 byte each)       merges used (merge number)        pieces         ids
   ──────────   ───────────────────────   ───────────────────────────────   ────────────   ────────
   "the"        t h e                     1 h+e, 2 t+he                     the            257
   " cat"       _ c a t                   5 a+t, 25 _+c, 26 _c+at           _cat           281
   " is"        _ i s                     3 _+i, 7 _i+s                     _is            262
   " running"   _ r u n n i n g           9, 10, 11, 12, 27, 28             _runnin g      283, 103

   18 characters ──▶ 5 tokens: [257, 281, 262, 283, 103]
   Why "_runnin" + "g"?  Training saw "running." WITH a dot, so it learned
   "_running." (id 284), not "_running". Without the dot the last "g" stays alone.

WHAT AN ENGINEER MUST KNOW:
  1. Price, context window and max_tokens are all counted in tokens.
  2. English: about 1 token per 4 letters. Other languages often need MORE.
  3. Tokenizers learn common pieces from text (BPE = glue the most common pair).
  4. The model sees pieces, not letters. So "count the r's in strawberry" is hard.

Run:  uv run python simple/01b_tokens_in_depth.py
"""

from collections import Counter

# Real tokenizers learn from trillions of words. We use a few sentences.
TRAINING_TEXT = (
    "the cat sat on the mat. the cat is running. the dog is running. "
    "the runner is happy. hello world. hello there. the world is big. "
    "i like straw. i like a berry. i like strawberry jam. a straw berry."
)


# ----------------------------------------------------------------------------
# STEP 1: CHUNKS = cut text at spaces (the space stays with the next word)
# ----------------------------------------------------------------------------
#   "hello big world"
#      │
#      ▼  text.split(" ")
#   ["hello", "big", "world"]
#      │
#      ▼  put the space back in FRONT of every word except the first
#   ["hello", " big", " world"]
#      │
#      ▼  later (in STEP 2 and 3): every chunk becomes single bytes
#   " cat"  ──▶  [32, 99, 97, 116]  ──▶  pieces  _ c a t     (_ = space)
#
#   Pieces never cross a chunk border. So " cat" and " sat" are learned apart.
def split_into_chunks(text):
    """'hello big world' -> ['hello', ' big', ' world']"""
    words = text.split(" ")
    return [words[0]] + [" " + word for word in words[1:]]


# ----------------------------------------------------------------------------
# STEP 2: BPE = find the most common pair of pieces and glue it into one
# ----------------------------------------------------------------------------
#   merge_pair: glue ONE pair everywhere in one chunk
#
#   pieces = [t, h, e]       pair = (h, e)
#      │
#      ▼  walk left to right
#    t      ──▶ result = [t]
#    h      ──▶ (t, h) == pair? no  ──▶ result = [t, h]
#    e      ──▶ (h, e) == pair? YES ──▶ glue onto the last one ──▶ result = [t, he]
#      │
#      ▼
#   [t, he]
def merge_pair(pieces, pair):
    """Replace every (a, b) next to each other with one piece a+b."""
    result = []
    for piece in pieces:
        if result and (result[-1], piece) == pair:
            result[-1] = result[-1] + piece             # glue onto the piece before
        else:
            result.append(piece)
    return result


#   train: the BPE loop (real numbers from this run)
#
#   40 chunks, each cut into single bytes:  [t,h,e]  [_,c,a,t]  [_,s,a,t]  ...
#      │
#      ▼
#   ┌─▶ count every neighbour pair in every chunk
#   │      round 1:  h+e is in the, there, hello ... (9 times)
#   │      │
#   │      ▼
#   │   take the most common pair ──▶ (h, e), seen 9 times
#   │      │                          (same count? the pair seen first wins)
#   │      ▼
#   │   seen less than 2 times? ── yes ──▶ END (nothing common left to learn)
#   │      │ no
#   │      ▼
#   │   save it as merge 1, then glue it in all chunks:  [t,h,e] ──▶ [t,he]
#   │      │
#   │      ▼
#   │   done 30 merges? ── yes ──▶ END (we asked for number_of_merges=30)
#   │      │ no
#   └──────┘   round 2:  t+he 7  ──▶ merge 2 = "the"
#              round 3:  _+i  7  ──▶ merge 3 = "_i"   ...
def train(text, number_of_merges):
    """Start from single bytes. Glue the most common pair. Repeat."""
    # Every chunk starts as a list of 1-byte pieces: "cat" -> [b"c", b"a", b"t"]
    chunks = [[bytes([b]) for b in chunk.encode("utf-8")] for chunk in split_into_chunks(text)]
    merges = []
    counts = []                                          # how often each merge was seen
    for _ in range(number_of_merges):
        pair_counts = Counter()
        for pieces in chunks:
            for pair in zip(pieces, pieces[1:]):        # every neighbour pair
                pair_counts[pair] += 1
        best_pair, count = pair_counts.most_common(1)[0]
        if count < 2:                                    # nothing common left to learn
            break
        merges.append(best_pair)
        counts.append(count)
        chunks = [merge_pair(pieces, best_pair) for pieces in chunks]
    return merges, counts


# ----------------------------------------------------------------------------
# STEP 3: ENCODE = text -> pieces -> ids  (decode = ids -> text)
# ----------------------------------------------------------------------------
#   vocab (the id table):
#      id 0 .. 255    = the 256 single bytes     (id 103 = "g", id 116 = "t")
#      id 256 .. 285  = the 30 learned pieces    (id 256 = "he", id 257 = "the")
#
#   encode " running":
#   pieces = [_, r, u, n, n, i, n, g]
#      │
#      ▼
#   ┌─▶ next merge from the list (merge 1, 2, 3 ... 30, SAME order as training)
#   │      │
#   │      ▼
#   │   does this pair appear in the pieces? ── no ──▶ skip it
#   │      │ yes                                         │
#   │      ▼                                             │
#   │   glue it:  merge 9 (_+r)   ──▶ [_r, u, n, n, i, n, g]
#   │             merge 10 (_r+u) ──▶ [_ru, n, n, i, n, g]   ...
#   │      │◀────────────────────────────────────────────┘
#   │   more merges? ── no ──▶ pieces = [_runnin, g]
#   │      │ yes                   │
#   └──────┘                       ▼  vocab.index(piece)
#                               ids = [283, 103]
#
#   decode: ids ──▶ vocab[id] ──▶ join the bytes ──▶ .decode("utf-8") ──▶ text
def encode(text, merges, vocab, show_steps=False):
    """Cut into chunks, glue with the learned merges (in order), look up ids."""
    ids = []
    for chunk in split_into_chunks(text):
        pieces = [bytes([b]) for b in chunk.encode("utf-8")]
        if show_steps:
            print("    chunk", repr(show(chunk.encode("utf-8"))), "starts as", [show(p) for p in pieces])
        for number, pair in enumerate(merges, start=1):  # same order as training
            new_pieces = merge_pair(pieces, pair)
            if show_steps and new_pieces != pieces:
                print("      merge", number, "(" + show(pair[0]) + "+" + show(pair[1]) + ") ->",
                      [show(p) for p in new_pieces])
            pieces = new_pieces
        ids += [vocab.index(piece) for piece in pieces]
    return ids


def show(piece):                     # space shown as _ , a cut-up letter as a ?-box
    return piece.decode("utf-8", errors="replace").replace(" ", "_")


def main():
    print("STEP 1: cut text into chunks, then bytes")
    print("  ", split_into_chunks("hello big world"))
    print("   bytes of 'cat':", list("cat".encode("utf-8")))
    print("   training text:", len(split_into_chunks(TRAINING_TEXT)), "chunks")

    print("\nSTEP 2: learn pieces (BPE glues the most common pair)")
    merges, counts = train(TRAINING_TEXT, number_of_merges=30)
    for number, ((a, b), count) in enumerate(zip(merges[:8], counts), start=1):
        print("   merge", number, ":", show(a), "+", show(b), "->", show(a + b), "  (seen", count, "times)")
    # vocab: ids 0..255 are the single bytes, then one new id per merge
    vocab = [bytes([i]) for i in range(256)] + [a + b for a, b in merges]
    print("   vocab size:", len(vocab), "(256 bytes +", len(merges), "learned pieces)")

    print("\nSTEP 3: encode and decode")
    ids = encode("the cat is running", merges, vocab, show_steps=True)
    print("   pieces:", [show(vocab[i]) for i in ids])
    print("   ids:   ", ids)
    text_again = b"".join(vocab[i] for i in ids).decode("utf-8")   # decode
    print("   decode:", text_again)
    print("   (training saw 'running.' with a dot: learned piece",
          vocab.index(b" running."), "=", show(b" running.") + ")")

    print("\nSTEP 4: why token counts matter")
    for text in ["the cat is running", "le chat court", "बिल्ली दौड़ रही है"]:
        count = len(encode(text, merges, vocab))
        print("  ", len(text), "characters ->", count, "tokens :", text)
    print("   Languages the tokenizer saw less need more tokens = more money.")

    ids = encode("i like strawberry", merges, vocab)
    print("\n   'i like strawberry' pieces:", [show(vocab[i]) for i in ids])
    print(f"   The model sees {len(ids)} piece ids -- not the {len('i like strawberry')} letters.")
    print("   That is why 'how many r's in strawberry?' is hard for an LLM.")

    tokens_per_day = 1000 * 500                      # 1000 requests x 500 tokens
    cost = tokens_per_day * 3.00 / 1_000_000         # example price: $3 per 1M tokens
    print("\n   1000 requests x 500 tokens = $" + format(cost, ".2f") + " per day")


if __name__ == "__main__":
    main()

# Remember:
#   - Text -> chunks -> bytes -> glued pieces (tokens) -> ids -> model.
#   - You pay per token. Limits (context, max_tokens) are in tokens too.
#   - Non-English text and odd words usually need more tokens.
# Try: add "le chat court." 5 times to TRAINING_TEXT. Does French need fewer tokens?
