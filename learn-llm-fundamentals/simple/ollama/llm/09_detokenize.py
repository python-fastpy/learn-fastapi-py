r"""09 -- DETOKENIZE: the picked ID turns back into text you can read
====================================================================

CONCEPT IN ONE LINE:
  The model only ever outputs an ID. To show it to you, the ID goes BACKWARDS through
  lesson 03: ID -> token string -> bytes -> UTF-8 text. Here we do it by hand with the
  real vocabulary and compare with what Ollama streams.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── [09 detokenize] ◀── 08 pick ◀── 07 softmax

  IN:   one ID picked in lesson 08, e.g. 60704
  OUT:  text for the "response" field, e.g. "Paris"

WHAT HAPPENS -- lesson 03 run in reverse:

   60704
     │  1. LOOK UP      tokens[60704]                          (the vocabulary list)
     ▼
   "Paris"                      the token string, written with stand-in characters
     │  2. CHAR -> BYTE  undo the GPT-2 trick:  'Ġ' -> 32,  'P' -> 80,  and so on for every symbol
     ▼
   [80, 97, 114, 105, 115]      the "bytes" field you saw in 01b STEP 3
     │  3. UTF-8 DECODE  bytes -> characters                    (01c_utf8_bytes_table.py)
     ▼
   "Paris"                      what appears on your screen

  A LONGER EXAMPLE -- [791, 6864, 315, 9822, 374]:

     ID      token string    bytes                                  text
     791     'The'           [84, 104, 101]                         "The"
     6864    'Ġcapital'      [32, 99, 97, 112, 105, 116, 97, 108]   " capital"     <- Ġ = space
     315     'Ġof'           [32, 111, 102]                         " of"
     9822    'ĠFrance'       [32, 70, 114, 97, 110, 99, 101]        " France"
     374     'Ġis'           [32, 105, 115]                         " is"
                                                     joined:  "The capital of France is"

  The spaces come back because they were INSIDE the tokens all along. Nothing adds
  spaces between tokens -- joining the bytes is enough.

  HALF CHARACTERS -- one token can hold an INCOMPLETE character:

     "🙂" = bytes [240, 159, 153, 130] = 2 tokens:
        9468   'ðŁ'   -> bytes [240, 159]         -> alone: not valid UTF-8 -> '�'
        19044  'ĻĤ'   -> bytes [153, 130]         -> alone: not valid UTF-8 -> '��'
        both together -> [240, 159, 153, 130]     -> '🙂'

     So a server can't just print each token as it comes. It keeps incomplete bytes
     back until the character is finished. REAL Ollama behaviour (STEP 4 below):
     asked for an emoji, the model wrote '😊' as 2 tokens ("eval_count": 3 = 2 + <end>)
     but Ollama sent ONE chunk with all 4 bytes -- the first half was held back.

     (and " 🙂" WITH a space in front is a single token, 28584 -- spaces change the pieces)

  SPECIAL TOKENS ARE NOT SHOWN:

     128009  <|eot_id|>   -> the model's <end> -- Ollama stops (lesson 11) and prints nothing:
                             the last chunk has "response": "" and "done_reason": "stop"
     128006  <|start_header_id|> etc. -- structure markers, never meant as visible text

WHERE THIS COMES FROM:

   piece                       who made it                    where it lives
   ID -> token string          Meta's vocabulary (lesson 03)  GGUF key tokenizer.ggml.tokens
   stand-in char -> byte       the GPT-2 byte map (fixed)     gguf_reader.bytes_to_unicode(), reversed
   bytes -> text               the UTF-8 standard             Python: bytes.decode("utf-8")
   holding back half chars     Ollama (the server)            inside /api/generate and /api/chat
   the "bytes" in logprobs     Ollama                         "logprobs": [{"token", "bytes"}]

IS IT OLLAMA-SPECIFIC?  No -- every model outputs IDs and every server decodes them.

   who                what you get back
   the model itself   one ID per step (it never produces text directly)
   Ollama             text in "response" (stream: one chunk per token, roughly);
                      token + bytes if "logprobs": true
   OpenAI             text; with logprobs: true, each token + its bytes (similar idea)
   Anthropic          text only (streamed as text deltas); no token IDs or bytes
   Hugging Face       IDs; you call tokenizer.decode(ids) yourself

COMMON CONFUSIONS:
   - a stream chunk is NOT always exactly one token: half characters get merged (😊 above)
   - "response": "" in the last chunk is the <end> token being hidden, not an error
   - decoding is exact and lossless: encode then decode gives back the same text
   - 'Ġ', 'Ċ', 'ðŁ' are NOT what the model "thinks" -- they're how the vocabulary file
     WRITES bytes; they disappear after step 2
   - mojibake (garbled text like "ðŸ™‚") = UTF-8 bytes decoded with the WRONG table
     (e.g. Windows-1252) -- a step-3 mistake, not a model mistake
"""

import json
import sys

import httpx

from gguf_reader import bytes_to_unicode, read_gguf

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


class Detokenizer:
    def __init__(self):
        meta, _tensors, _path = read_gguf()
        self.tokens = meta["tokenizer.ggml.tokens"]
        self.special = {i for i, kind in enumerate(meta["tokenizer.ggml.token_type"]) if kind == 3}
        self.char_byte = {c: b for b, c in bytes_to_unicode().items()}   # 'Ġ' -> 32

    def token_bytes(self, token_id):
        if token_id in self.special:
            return b""                                          # never shown as text
        return bytes(self.char_byte[c] for c in self.tokens[token_id])

    def decode(self, ids):
        data = b"".join(self.token_bytes(i) for i in ids)       # join BYTES, then decode once
        return data.decode("utf-8", errors="replace")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    d = Detokenizer()

    print("STEP 1: ID -> token string -> bytes -> text")
    ids = [791, 6864, 315, 9822, 374]
    for i in ids:
        data = d.token_bytes(i)
        print(f"{i:>6}  {d.tokens[i]!r:12} {list(data)!s:40} {data.decode('utf-8')!r}")
    print("joined:", repr(d.decode(ids)))
    # ->    791  'The'        [84, 104, 101]                           'The'
    #      6864  'Ġcapital'   [32, 99, 97, 112, 105, 116, 97, 108]     ' capital'
    #       315  'Ġof'        [32, 111, 102]                           ' of'
    #      9822  'ĠFrance'    [32, 70, 114, 97, 110, 99, 101]          ' France'
    #       374  'Ġis'        [32, 105, 115]                           ' is'
    #    joined: 'The capital of France is'

    print("\nSTEP 2: half characters")
    for i in [9468, 19044]:
        print(f"{i:>6}  {d.tokens[i]!r:8} {list(d.token_bytes(i))!s:12} alone -> {d.decode([i])!r}")
    print("both together ->", repr(d.decode([9468, 19044])))
    print("28584", repr(d.tokens[28584]), "->", repr(d.decode([28584])), "  <- space + emoji = 1 token")
    # ->   9468  'ðŁ'     [240, 159]   alone -> '�'
    #     19044  'ĻĤ'     [153, 130]   alone -> '��'
    #    both together -> '🙂'
    #    28584 'ĠðŁĻĤ' -> ' 🙂'   <- space + emoji = 1 token

    print("\nSTEP 3: special tokens disappear")
    print(repr(d.tokens[128009]), "->", repr(d.decode([60704, 13, 128009])))
    # -> '<|eot_id|>' -> 'Paris.'          <- 'Paris' + '.' + <end> (shown as nothing)

    print("\nSTEP 4: what Ollama streams -- one chunk per token, decoded for you")
    for ask in ["Complete the sentence with one word: The capital of France is",
                "Reply with only this emoji and nothing else: 🙂"]:
        prompt = ("<|start_header_id|>user<|end_header_id|>\n\n" + ask + "<|eot_id|>"
                  "<|start_header_id|>assistant<|end_header_id|>\n\n")
        body = {"model": CHAT_MODEL, "prompt": prompt, "raw": True, "stream": True,
                "logprobs": True, "options": {"temperature": 0, "num_predict": 10}}
        print("ask:", ask)
        with httpx.stream("POST", OLLAMA + "/api/generate", json=body, timeout=300) as r:
            for line in r.iter_lines():
                if not line:
                    continue
                chunk = json.loads(line)
                tokens = [(lp["token"], lp["bytes"]) for lp in chunk.get("logprobs", [])]
                print(f"   response={chunk['response']!r:10} logprobs={tokens}",
                      f"done_reason={chunk['done_reason']} eval_count={chunk['eval_count']}"
                      if chunk["done"] else "")
    # -> ask: Complete the sentence with one word: The capital of France is
    #       response='Paris'    logprobs=[('Paris', [80, 97, 114, 105, 115])]
    #       response='.'        logprobs=[('.', [46])]
    #       response=''         logprobs=[] done_reason=stop eval_count=3   <- <end>, hidden
    #    ask: Reply with only this emoji and nothing else: 🙂
    #       response='😊'       logprobs=[('😊', [240, 159, 152, 138])]     <- ONE chunk, but
    #       response=''         logprobs=[] done_reason=stop eval_count=3   <- 3 = 2 tokens + <end>


if __name__ == "__main__":
    main()

# Try: d.decode(range(1000, 1020)) -- 20 random tokens glued together, often half-words.
