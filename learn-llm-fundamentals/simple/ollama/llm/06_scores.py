r"""06 -- SCORES: one number for EVERY token in the vocabulary
==========================================================

CONCEPT IN ONE LINE:
  The last token's final vector is compared with all 128,256 vocabulary rows (a dot product
  each); the result is 128,256 SCORES ("logits") -- high = "good next token".

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ [06 scores]
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax

  IN:   22 x 3,072 numbers from layer 28 -- but only the LAST position is used
        (the "\n\n" after assistant: through attention it has gathered the whole prompt)
  OUT:  128,256 scores, one per token ID

WHAT HAPPENS:

     last vector [3,072]          after blk.27
           │
           ▼
     output_norm (3,072 F32)      one more RMSNorm (same maths as 05)
           │
           ▼
     x token_embd [3,072 x 128,256]   <- the SAME table as step 04 ("tied" embeddings)
           │
           ▼
     128,256 scores

  ONE SCORE = ONE DOT PRODUCT: multiply position by position, add it all up.

     final vector    [ 0.12,  -0.40,   0.03,   0.25 ]   (+ 3,068 more numbers)
     row of 'Paris'  [ 0.30,  -0.20,   0.01,   0.18 ]   (+ 3,068 more, row 60704 of token_embd)
                       ─────────────────────────────
     score('Paris') = 0.12*0.30 + (-0.40)*(-0.20) + 0.03*0.01 + 0.25*0.18
                      and so on for all 3,072 pairs           (numbers illustrative)
     same direction  -> big positive score     unrelated -> ~0     opposite -> negative

  Done for all 128,256 rows:
     128,256 x 3,072 = 394,002,432 multiply-adds -- for EVERY generated token.

  WHY THE SAME TABLE TWICE ("tied embeddings"):
     step 04 (in):   ID 9822 -> row 9822 -> vector              "read a token"
     step 06 (out):  vector -> compare with every row -> ID     "write a token"
     llama3.2 uses ONE table for both. Proof: the file has token_embd.weight but NO
     output.weight tensor -- and the parameter count (3,212,749,888) only adds up with one.
     (Bigger models like llama3.1-8B have a separate output table.)

  THE NUMBERS FOR THE 01b PROMPT (real, from Ollama):

     token     logprob       score gap vs 'Paris'
     'Paris'   -0.0012          0.00
     'Par'     -7.1457         -7.14
     'France'  -9.8171         -9.82
     ' Paris'  -9.8229         -9.82
     'Berlin'  -11.0300       -11.03
     (128,251 more tokens, all lower)

  Ollama doesn't send raw scores, only logprobs (07). But softmax only cares about
  DIFFERENCES, so  score_A - score_B = logprob_A - logprob_B  exactly. We get the real
  GAPS, not the absolute values (adding 100 to every score changes nothing).

WHERE THIS COMES FROM:

  what                              who made it            where you find it
  the output table                  Meta's training        GGUF tensor token_embd.weight (tied)
  output_norm weights               Meta's training        GGUF tensor output_norm.weight (F32)
  the final vector                  computed per request   inside Ollama, never shown
  the 128,256 scores                computed per request   inside Ollama; you get only the top
                                                           ones, as logprobs

IS IT OLLAMA-SPECIFIC?

  the model itself   every LLM ends with "one score per vocab token" -- it's universal
  Ollama             "logprobs": true, "top_logprobs": N   (we got 20 here)
  OpenAI             logprobs + top_logprobs (Chat Completions, up to 20)
  Anthropic          no logprobs / scores in the API
  Hugging Face       the full raw scores: model(input_ids).logits, or
                     generate(input_ids, output_scores=True, return_dict_in_generate=True)

COMMON CONFUSIONS:

  - scores are NOT probabilities: they can be any number, + or -, and don't add up to 1.
    Softmax (07) turns them into probabilities.
  - "logit" = score. "logprob" = log of the probability AFTER softmax. Different numbers,
    same gaps.
  - the model scores ALL 128,256 tokens every time, even 'banana'. It never "searches".
  - only the LAST position's scores matter for generation; the other 21 positions'
    vectors are kept (KV cache, lesson 10) but their scores are not computed.

SEE IT VISUALLY:
   https://poloclub.github.io/transformer-explainer/   the bars at the end = these scores
"""

import math
import sys

import httpx

from gguf_reader import embedding_row, read_f32, read_gguf

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"

PROMPT = ("<|start_header_id|>user<|end_header_id|>\n\n"
          "Complete the sentence with one word: The capital of France is<|eot_id|>"
          "<|start_header_id|>assistant<|end_header_id|>\n\n")       # same as 01b STEP 2


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    meta, tensors, path = read_gguf()
    vocab = meta["tokenizer.ggml.tokens"]

    print("STEP 1: is there a separate output table?")
    for name in ["token_embd.weight", "output_norm.weight", "output.weight"]:
        t = tensors.get(name)
        print(f"  {name:20}", f"{t['shape']} {t['type']}" if t else "NOT IN FILE -> tied to token_embd")
    total = sum(math.prod(t["shape"]) for t in tensors.values())
    print(f"  total numbers in file: {total:,}")
    # -> STEP 1: is there a separate output table?
    #      token_embd.weight    (3072, 128256) Q6_K
    #      output_norm.weight   (3072,) F32
    #      output.weight        NOT IN FILE -> tied to token_embd
    #      total numbers in file: 3,212,749,888

    print("\nSTEP 2: scoring = dot products with real rows (mechanism demo)")
    # We can't run 28 layers in plain Python, so we use the real ' France' embedding as a
    # STAND-IN for "the final vector", put it through the real output_norm, and score it.
    norm = read_f32(tensors, path, "output_norm.weight")
    x = embedding_row(vocab.index("ĠFrance"), tensors, path)
    rms = math.sqrt(sum(v * v for v in x) / len(x) + 1e-5)
    final = [v / rms * w for v, w in zip(x, norm)]
    candidates = [" France", " French", " Paris", " Germany", " Italy", " Spain", " Belgium",
                  " Europe", " Lyon", " Berlin", " London", " country", " capital", " the",
                  " is", ".", " banana", " apple", " dog", " computer"]
    scores = []
    for word in candidates:
        tid = vocab.index(word.replace(" ", "Ġ"))              # vocab stores space as 'Ġ'
        scores.append((dot(final, embedding_row(tid, tensors, path)), word, tid))
    for s, word, tid in sorted(scores, reverse=True):
        print(f"  {word!r:12} ID {tid:>6}   score {s:7.3f}")
    print(f"  (real model: 128,256 rows x 3,072 = {128256 * 3072:,} multiply-adds per token)")
    # -> STEP 2: scoring = dot products with real rows (mechanism demo)
    #      ' France'    ID   9822   score  88.349     <- itself: same direction = biggest
    #      ' French'    ID   8753   score  55.242
    #      ' Paris'     ID  12366   score  39.789
    #      ' Spain'     ID  18157   score  39.540
    #      ' Italy'     ID  15704   score  39.189
    #      ' Germany'   ID  10057   score  38.900
    #      ' Europe'    ID   4606   score  34.101
    #      ' Belgium'   ID  34061   score  32.561
    #      ' Lyon'      ID  56301   score  20.595
    #      ' Berlin'    ID  20437   score  13.171
    #      ' London'    ID   7295   score  12.189
    #      ' country'   ID   3224   score   7.868
    #      ' apple'     ID  24149   score   5.469
    #      ' capital'   ID   6864   score   4.023
    #      ' banana'    ID  44196   score   3.789
    #      ' dog'       ID   5679   score   2.858
    #      ' computer'  ID   6500   score   1.386
    #      ' the'       ID    279   score  -3.307
    #      ' is'        ID    374   score  -4.729
    #      '.'          ID     13   score  -7.038
    #      (real model: 128,256 rows x 3,072 = 394,002,432 multiply-adds per token)
    # Real rows, real maths: France-related tokens score high, 'banana' ~0, grammar words
    # negative. But a raw ' France' vector scores ' France' first -- it says "France",
    # not "what comes NEXT". The 28 layers (05) are what turn the vector into
    # "next token = a capital city", so the real model ranks 'Paris' first (STEP 3).

    print("\nSTEP 3: the REAL score gaps for the 01b prompt, from Ollama's logprobs")
    body = {"model": CHAT_MODEL, "prompt": PROMPT, "raw": True, "stream": False,
            "logprobs": True, "top_logprobs": 20,
            "options": {"temperature": 0, "num_predict": 1}}
    r = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300).json()
    top = r["logprobs"][0]["top_logprobs"]
    best = top[0]["logprob"]
    for t in top:
        print(f"  {t['token']!r:10} logprob {t['logprob']:9.4f}   score gap {t['logprob'] - best:7.2f}")
    # -> STEP 3: the REAL score gaps for the 01b prompt, from Ollama's logprobs
    #      'Paris'    logprob   -0.0012   score gap    0.00
    #      'Par'      logprob   -7.1360   score gap   -7.13
    #      'France'   logprob   -9.6981   score gap   -9.70
    #      ' Paris'   logprob   -9.8432   score gap   -9.84
    #      'par'      logprob   -9.9892   score gap   -9.99
    #      'PAR'      logprob  -10.3009   score gap  -10.30
    #      ' paris'   logprob  -10.6985   score gap  -10.70
    #      'Berlin'   logprob  -10.8706   score gap  -10.87
    #      'London'   logprob  -11.5082   score gap  -11.51
    #      'French'   logprob  -11.7519   score gap  -11.75
    #      '"'        logprob  -11.8354   score gap  -11.83
    #      'Parm'     logprob  -11.9406   score gap  -11.94
    #      '.Par'     logprob  -12.0984   score gap  -12.10
    #      'P'        logprob  -12.3785   score gap  -12.38
    #      ' PAR'     logprob  -12.4612   score gap  -12.46
    #      'Tok'      logprob  -12.4755   score gap  -12.47
    #      '**'       logprob  -12.7175   score gap  -12.72
    #      'The'      logprob  -12.8154   score gap  -12.81
    #      '_par'     logprob  -12.9715   score gap  -12.97
    #      'B'        logprob  -12.9938   score gap  -12.99
    # (the last decimals wobble a little between runs -- CPU maths noise)
    # Notice: the runners-up are spellings of Paris ('Par', ' Paris', 'PAR') and other
    # capitals ('Berlin', 'London') -- the final vector points at "a capital city".


if __name__ == "__main__":
    main()

# Try: in STEP 2 replace "ĠFrance" with "ĠParis" -- the stand-in vector changes, so does the
#      ranking. Then ask Ollama a different question in STEP 3 and compare the gaps.
