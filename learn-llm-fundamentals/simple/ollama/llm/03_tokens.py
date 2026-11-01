r"""03 -- TOKENS: how your text becomes the numbers the model reads
=================================================================

CONCEPT IN ONE LINE:
  The tokenizer cuts text into pieces from a FIXED list of 128,256 and replaces each piece
  with its POSITION in that list (its ID). Here we build the REAL llama3.2 tokenizer in
  plain Python, straight from the model file, and check it against Ollama.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ [03 tokens] ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax

  IN:   one long string (your message wrapped in the template, lesson 02)
  OUT:  a list of IDs, e.g. 22 of them:
        [128000, 128006, 882, 128007, 271, 12833, 279, 11914, 449, 832, 3492, 25,
         578, 6864, 315, 9822, 374, 128009, 128006, 78191, 128007, 271]

FIRST: CHARACTERS vs TOKENS -- two different ways to count the same text

   text:     The capital of France is

   CHARACTERS -- just count them, spaces included (_ = space):

      T  h  e  _  c  a  p  i  t  a  l  _  o  f  _  F  r  a  n  c  e  _  i  s
      1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24

      piece      characters
      The            3
      space          1
      capital        7
      space          1
      of             2
      space          1
      France         6
      space          1
      is             2
      ─────────────────
      total         24          len("The capital of France is") == 24

   TOKENS -- the tokenizer cuts the same 24 characters into vocabulary pieces:

      tokens:   "The" | " capital" | " of" | " France" | " is"
      chars:      3   +     8      +   3   +     7     +   4    = 24 characters
      count:      1   +     1      +   1   +     1     +   1    =  5 tokens
      IDs:       791  |    6864    |  315  |    9822   |  374     -> [791, 6864, 315, 9822, 374]

   The 4 SPACES don't disappear: each one is glued to the FRONT of the next word
   (" capital" = space + 7 letters = 8). Every character lands in exactly one token, so the
   per-token character counts add back up to 24. 24 / 5 ≈ 4.8 characters per token --
   close to the usual rule of thumb for English, 1 token ≈ 4 characters.

   You can count characters by hand; you CAN'T count tokens by hand -- that depends on the
   model's vocabulary and merge rules, which is what the rest of this file is about.

WHAT HAPPENS -- 5 small steps:

   "<|start_header_id|>user<|end_header_id|>\n\nComplete the sentence with one word: The capital
    of France is<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
        │
        │ 1. SPECIAL SPLIT   cut out the special tokens first -- they are never split up
        ▼
   <|start_header_id|>   "user"   <|end_header_id|>
   "\n\nComplete the sentence with one word: The capital of France is"
   <|eot_id|>   <|start_header_id|>   "assistant"   <|end_header_id|>   "\n\n"
        │
        │ 2. PRE-SPLIT       a regex cuts normal text into word-sized chunks;
        ▼                    the SPACE stays glued to the FRONT of the word
   "\n\n"  "Complete"  " the"  " sentence"  " with"  " one"  " word"  ":"
   " The"  " capital"  " of"  " France"  " is"
        │
        │ 3. BYTES           each chunk -> UTF-8 bytes  (01c_utf8_bytes_table.py)
        ▼                    " capital" -> [32, 99, 97, 112, 105, 116, 97, 108]
        │ 4. BYTE -> CHAR    each byte -> one visible stand-in character (GPT-2 trick)
        ▼                    32 -> 'Ġ'   so   " capital" -> "Ġcapital" (8 symbols)
        │ 5. BPE MERGES      glue neighbouring symbols, best-ranked pair first,
        ▼                    until no merge rule applies
   "Ġcapital"  -> found in the vocabulary at position 6864  -> ID 6864

  REAL MERGE TRACE for " capital"  (rank = line number in the 280,147 merge rules;
  a LOWER rank = learned EARLIER = more common = applied FIRST):

     start          Ġ  c  a  p  i  t  a  l                 8 symbols
     rank     26    Ġc a  p  i  t  a  l                    Ġ + c       -> Ġc
     rank     29    Ġc a  p  it a  l                       i + t       -> it
     rank     32    Ġc a  p  it al                         a + l       -> al
     rank    205    Ġc ap it al                            a + p       -> ap
     rank  4,415    Ġcap  it al                            Ġc + ap     -> Ġcap
     rank  4,683    Ġcap  ital                             it + al     -> ital
     rank 17,793    Ġcapital                               Ġcap + ital -> Ġcapital   = ID 6864

  REAL MERGE TRACE for " France":
     start          Ġ  F  r  a  n  c  e
     rank     30    Ġ  F  r  an c  e                       a + n       -> an
     rank    141    Ġ  F  r  an ce                         c + e       -> ce
     rank    296    ĠF r  an ce                            Ġ + F       -> ĠF
     rank    808    ĠF r  ance                             an + ce     -> ance
     rank  6,626    ĠFr ance                               ĠF + r      -> ĠFr
     rank 26,043    ĠFrance                                ĠFr + ance  -> ĠFrance    = ID 9822

  Common words end as ONE token. Rare words run out of merge rules part-way:
     " Ouagadougou"  ->  "ĠOu" | "ag" | "ad" | "oug" | "ou"          5 tokens

  THE 22 TOKENS OF 01b's PROMPT (this file reproduces Ollama's count exactly):
      #   token                  ID       #   token                  ID
      1   <|begin_of_text|>      128000   12  ":"                    25
      2   <|start_header_id|>    128006   13  " The"                 578    (NOT 791)
      3   "user"                 882      14  " capital"             6864
      4   <|end_header_id|>      128007   15  " of"                  315
      5   "\n\n"                 271      16  " France"              9822
      6   "Complete"             12833    17  " is"                  374
      7   " the"                 279      18  <|eot_id|>             128009
      8   " sentence"            11914    19  <|start_header_id|>    128006
      9   " with"                449      20  "assistant"            78191
      10  " one"                 832      21  <|end_header_id|>      128007
      11  " word"                3492     22  "\n\n"                 271
      6 special + 16 text = 22 = "prompt_eval_count": 22

  SURPRISES (all real, from running this file):
     "2024"          -> [2366, 19]                 "202" + "4"   numbers go in groups of max 3 digits
     "12345"         -> [4513, 1774]               "123" + "45"  -> the model never "sees" 12,345
     "hello world"   -> [15339, 1917]              2 tokens
     "नमस्ते"         -> [61196, 88344, 79468, 100365, 35470]   5 tokens for ONE Hindi word
     "🙂"            -> [9468, 19044]              1 character = 4 bytes = 2 tokens

WHERE THIS COMES FROM:

   piece                  who made it                     where it lives
   the 128,256 tokens     Meta, ONCE, before training     GGUF key tokenizer.ggml.tokens
   the 280,147 merges     Meta, same BPE run              GGUF key tokenizer.ggml.merges
   which are "special"    Meta                            GGUF key tokenizer.ggml.token_type
                                                          (1 = normal x 128,000, 3 = control x 256)
   the pre-split regex    Meta (llama3 design)            GGUF key tokenizer.ggml.pre = "llama-bpe"
                                                          (only the NAME; the regex is in the code)
   running all of it      Ollama, inside /api/generate    you never see it -- only the COUNT,
                                                          "prompt_eval_count"
   an ID                  = POSITION in the token list:   tokens[6864] == "Ġcapital"

   Ollama's /api/show hides the lists (tokenizer.ggml.tokens: []), but they ARE in the
   model file -- gguf_reader.py reads them directly.

  Why more merges (280,147) than tokens (128,000)? Several merge paths can lead to the same
  token: "Ġ capital" (rank 17,792) and "Ġcap ital" (rank 17,793) both make "Ġcapital".

IS IT OLLAMA-SPECIFIC?  No -- the tokenizer belongs to the MODEL.

   who                tokenizer                                  can you see the IDs?
   the model itself   fixed at training; change it = retrain     -
   Ollama             runs the model's own tokenizer             count only (prompt_eval_count)
   OpenAI             tiktoken, e.g. o200k_base (~200k tokens)   yes, with the tiktoken library
   Anthropic          Claude's own tokenizer (not published)     count only (token-counting endpoint,
                                                                 usage.input_tokens)
   Hugging Face       tokenizer.json next to the weights         yes: tokenizer.encode(text)

   Same text, DIFFERENT model = different pieces, different IDs, different count.

COMMON CONFUSIONS:
   - token != word: " capital" is 1 token, " Ouagadougou" is 5, "." is 1
   - token != character: "🙂" is 1 character, 4 bytes, 2 tokens
   - ID != byte: 'P' is byte 80; "Paris" is ID 60704 (01c, last table)
   - "The" (791) and " The" (578) are DIFFERENT tokens -- the space is part of the token
   - the tokenizer is NOT learned during training of the weights -- it's fixed BEFORE

  NOTE: step 2 uses a standard-library approximation of llama3's regex (Python's `re`
  has no \p{L}). It matches the real one for normal text; rare scripts or odd punctuation
  might split slightly differently. Steps 1, 3, 4 and 5 are exact.

SEE IT VISUALLY:
   https://tiktokenizer.vercel.app/          colored tokens + IDs (pick a Llama 3 model)
   https://huggingface.co/learn/llm-course/chapter6/5   BPE explained step by step
"""

import re
import sys

import httpx

from gguf_reader import bytes_to_unicode, read_gguf

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"

# step 2: llama3's split rule, written for Python's `re` (letters = [^\W\d_], digits = \d)
PRE_SPLIT = re.compile(
    r"(?i:'s|'t|'re|'ve|'m|'ll|'d)"        # English endings: it's -> "it" "'s"
    r"|(?:(?![\r\n])[\W_])?[^\W\d_]+"      # a word, with ONE optional symbol/space in front
    r"|\d{1,3}"                            # numbers in groups of max 3 digits
    r"| ?(?:(?!\s)[\W_])+[\r\n]*"          # punctuation runs
    r"|\s*[\r\n]+"                         # newlines
    r"|\s+(?!\S)|\s+"                      # other whitespace
)


class Tokenizer:
    def __init__(self):
        meta, _tensors, _path = read_gguf()
        self.tokens = meta["tokenizer.ggml.tokens"]                     # ID -> string
        self.ids = {tok: i for i, tok in enumerate(self.tokens)}        # string -> ID
        self.ranks = {m: r for r, m in enumerate(meta["tokenizer.ggml.merges"])}
        self.special = {t for t, kind in zip(self.tokens, meta["tokenizer.ggml.token_type"])
                        if kind == 3}
        self.special_split = re.compile("(" + "|".join(map(re.escape, self.special)) + ")")
        self.byte_char = bytes_to_unicode()                             # 32 -> 'Ġ'

    def bpe(self, symbols, trace=False):
        parts = list(symbols)
        while len(parts) > 1:
            # the neighbouring pair with the LOWEST rank wins
            rank, i = min((self.ranks.get(parts[i] + " " + parts[i + 1], float("inf")), i)
                          for i in range(len(parts) - 1))
            if rank == float("inf"):
                break                                    # no rule left -> done
            parts[i:i + 2] = [parts[i] + parts[i + 1]]
            if trace:
                print(f"   rank {rank:>6,}  {parts}")
        return parts

    def encode(self, text):
        ids = []
        for chunk in self.special_split.split(text):                    # step 1
            if chunk in self.special:
                ids.append(self.ids[chunk])
                continue
            for piece in PRE_SPLIT.findall(chunk):                      # step 2
                symbols = "".join(self.byte_char[b] for b in piece.encode("utf-8"))  # 3 + 4
                ids += [self.ids[p] for p in self.bpe(symbols)]         # step 5
        return ids


def ollama_count(text):
    """How many tokens Ollama says it read (it adds <|begin_of_text|> itself, so +1)."""
    body = {"model": CHAT_MODEL, "prompt": text, "raw": True, "stream": False,
            "options": {"num_predict": 1}}
    r = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300)
    r.raise_for_status()
    return r.json()["prompt_eval_count"]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    tok = Tokenizer()
    print("vocabulary:", len(tok.tokens), "tokens,", len(tok.ranks), "merge rules,",
          len(tok.special), "special")
    # -> vocabulary: 128256 tokens, 280147 merge rules, 256 special

    print("\nSTEP 1: one sentence, piece by piece")
    text = "The capital of France is"
    for piece in PRE_SPLIT.findall(text):
        data = piece.encode("utf-8")
        symbols = "".join(tok.byte_char[b] for b in data)
        print(f"{piece!r:12} bytes {list(data)!s:42} -> {symbols!r:12} -> ID {tok.ids[symbols]}")
    print(tok.encode(text))
    # -> 'The'        bytes [84, 104, 101]                           -> 'The'        -> ID 791
    #    ' capital'   bytes [32, 99, 97, 112, 105, 116, 97, 108]     -> 'Ġcapital'   -> ID 6864
    #    ' of'        bytes [32, 111, 102]                           -> 'Ġof'        -> ID 315
    #    ' France'    bytes [32, 70, 114, 97, 110, 99, 101]          -> 'ĠFrance'    -> ID 9822
    #    ' is'        bytes [32, 105, 115]                           -> 'Ġis'        -> ID 374
    #    [791, 6864, 315, 9822, 374]

    print("\nSTEP 2: the BPE merges, live")
    for word in [" capital", " France", " Ouagadougou"]:
        symbols = "".join(tok.byte_char[b] for b in word.encode("utf-8"))
        print(f"{word!r}  starts as {list(symbols)}")
        tok.bpe(symbols, trace=True)
    # -> ' capital'  starts as ['Ġ', 'c', 'a', 'p', 'i', 't', 'a', 'l']
    #       rank     26  ['Ġc', 'a', 'p', 'i', 't', 'a', 'l']
    #       rank     29  ['Ġc', 'a', 'p', 'it', 'a', 'l']
    #       rank     32  ['Ġc', 'a', 'p', 'it', 'al']
    #       rank    205  ['Ġc', 'ap', 'it', 'al']
    #       rank  4,415  ['Ġcap', 'it', 'al']
    #       rank  4,683  ['Ġcap', 'ital']
    #       rank 17,793  ['Ġcapital']
    #    ' France'  starts as ['Ġ', 'F', 'r', 'a', 'n', 'c', 'e']
    #       rank     30  ['Ġ', 'F', 'r', 'an', 'c', 'e']
    #       rank    141  ['Ġ', 'F', 'r', 'an', 'ce']
    #       rank    296  ['ĠF', 'r', 'an', 'ce']
    #       rank    808  ['ĠF', 'r', 'ance']
    #       rank  6,626  ['ĠFr', 'ance']
    #       rank 26,043  ['ĠFrance']
    #    ' Ouagadougou'  starts as ['Ġ', 'O', 'u', 'a', 'g', 'a', 'd', 'o', 'u', 'g', 'o', 'u']
    #       rank     39  ['Ġ', 'O', 'u', 'a', 'g', 'a', 'd', 'ou', 'g', 'o', 'u']
    #       rank     39  ['Ġ', 'O', 'u', 'a', 'g', 'a', 'd', 'ou', 'g', 'ou']
    #       rank    109  ['Ġ', 'O', 'u', 'a', 'g', 'ad', 'ou', 'g', 'ou']
    #       rank    147  ['Ġ', 'O', 'u', 'ag', 'ad', 'ou', 'g', 'ou']
    #       rank    445  ['ĠO', 'u', 'ag', 'ad', 'ou', 'g', 'ou']
    #       rank 125,898  ['ĠO', 'u', 'ag', 'ad', 'oug', 'ou']
    #       rank 170,827  ['ĠOu', 'ag', 'ad', 'oug', 'ou']      <- no rule left: stuck at 5 pieces

    print("\nSTEP 3: 01b's full prompt -- do we match Ollama?")
    prompt = ("<|start_header_id|>user<|end_header_id|>\n\n"
              "Complete the sentence with one word: The capital of France is<|eot_id|>"
              "<|start_header_id|>assistant<|end_header_id|>\n\n")
    ids = tok.encode("<|begin_of_text|>" + prompt)       # Ollama adds this one itself
    print(len(ids), ids)
    print("Ollama prompt_eval_count:", ollama_count(prompt))
    # -> 22 [128000, 128006, 882, 128007, 271, 12833, 279, 11914, 449, 832, 3492, 25, 578,
    #        6864, 315, 9822, 374, 128009, 128006, 78191, 128007, 271]
    #    Ollama prompt_eval_count: 22

    print("\nSTEP 4: surprises -- ours vs Ollama (Ollama count includes +1 for BOS)")
    for text in ["hello world", "2024", "12345", "🙂", "नमस्ते", " Ouagadougou",
                 "It's 3:45pm!"]:
        ids = tok.encode(text)
        pieces = [tok.tokens[i] for i in ids]
        print(f"{text!r:16} {len(ids)} tokens  {ids}  {pieces}  Ollama: {ollama_count(text) - 1}")
    # -> 'hello world'    2 tokens  [15339, 1917]  ['hello', 'Ġworld']  Ollama: 2
    #    '2024'           2 tokens  [2366, 19]  ['202', '4']  Ollama: 2
    #    '12345'          2 tokens  [4513, 1774]  ['123', '45']  Ollama: 2
    #    '🙂'             2 tokens  [9468, 19044]  ['ðŁ', 'ĻĤ']  Ollama: 2
    #    'नमस्ते'          5 tokens  [61196, 88344, 79468, 100365, 35470]
    #                     ['à¤¨', 'à¤®', 'à¤¸', 'à¥įà¤¤', 'à¥ĩ']  Ollama: 5   <- raw bytes shown as stand-ins
    #    ' Ouagadougou'   5 tokens  [69327, 351, 329, 49404, 283]  ['ĠOu', 'ag', 'ad', 'oug', 'ou']  Ollama: 5
    #    "It's 3:45pm!"   8 tokens  [2181, 596, 220, 18, 25, 1774, 5298, 0]
    #                     ['It', "'s", 'Ġ', '3', ':', '45', 'pm', '!']  Ollama: 8
    #    every count matches Ollama

    print("\nSTEP 5: an ID is just a POSITION in the list")
    for i in [0, 791, 6864, 60704, 128000, 128009]:
        print(i, repr(tok.tokens[i]))
    # -> 0 '!'
    #    791 'The'
    #    6864 'Ġcapital'
    #    60704 'Paris'
    #    128000 '<|begin_of_text|>'
    #    128009 '<|eot_id|>'


if __name__ == "__main__":
    main()

# Try: tok.encode("ChatGPT") vs tok.encode(" ChatGPT") -- one space changes the pieces.
