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
def split_into_chunks(text):
    """'hello big world' -> ['hello', ' big', ' world']"""
    words = text.split(" ")
    return [words[0]] + [" " + word for word in words[1:]]


# ----------------------------------------------------------------------------
# STEP 2: BPE = find the most common pair of pieces and glue it into one
# ----------------------------------------------------------------------------
def merge_pair(pieces, pair):
    """Replace every (a, b) next to each other with one piece a+b."""
    result = []
    for piece in pieces:
        if result and (result[-1], piece) == pair:
            result[-1] = result[-1] + piece             # glue onto the piece before
        else:
            result.append(piece)
    return result


def train(text, number_of_merges):
    """Start from single bytes. Glue the most common pair. Repeat."""
    # Every chunk starts as a list of 1-byte pieces: "cat" -> [b"c", b"a", b"t"]
    chunks = [[bytes([b]) for b in chunk.encode("utf-8")] for chunk in split_into_chunks(text)]
    merges = []
    for _ in range(number_of_merges):
        pair_counts = Counter()
        for pieces in chunks:
            for pair in zip(pieces, pieces[1:]):        # every neighbour pair
                pair_counts[pair] += 1
        best_pair, count = pair_counts.most_common(1)[0]
        if count < 2:                                    # nothing common left to learn
            break
        merges.append(best_pair)
        chunks = [merge_pair(pieces, best_pair) for pieces in chunks]
    return merges


# ----------------------------------------------------------------------------
# STEP 3: ENCODE = text -> pieces -> ids  (decode = ids -> text)
# ----------------------------------------------------------------------------
def encode(text, merges, vocab):
    """Cut into chunks, glue with the learned merges (in order), look up ids."""
    ids = []
    for chunk in split_into_chunks(text):
        pieces = [bytes([b]) for b in chunk.encode("utf-8")]
        for pair in merges:                              # same order as training
            pieces = merge_pair(pieces, pair)
        ids += [vocab.index(piece) for piece in pieces]
    return ids


def show(piece):                     # space shown as _ , a cut-up letter as a ?-box
    return piece.decode("utf-8", errors="replace").replace(" ", "_")


def main():
    print("STEP 1: cut text into chunks, then bytes")
    print("  ", split_into_chunks("hello big world"))
    print("   bytes of 'cat':", list("cat".encode("utf-8")))

    print("\nSTEP 2: learn pieces (BPE glues the most common pair)")
    merges = train(TRAINING_TEXT, number_of_merges=30)
    for number, (a, b) in enumerate(merges[:8], start=1):
        print("   merge", number, ":", show(a), "+", show(b), "->", show(a + b))
    # vocab: ids 0..255 are the single bytes, then one new id per merge
    vocab = [bytes([i]) for i in range(256)] + [a + b for a, b in merges]
    print("   vocab size:", len(vocab), "(256 bytes +", len(merges), "learned pieces)")

    print("\nSTEP 3: encode and decode")
    ids = encode("the cat is running", merges, vocab)
    print("   pieces:", [show(vocab[i]) for i in ids])
    print("   ids:   ", ids)
    text_again = b"".join(vocab[i] for i in ids).decode("utf-8")   # decode
    print("   decode:", text_again)

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
