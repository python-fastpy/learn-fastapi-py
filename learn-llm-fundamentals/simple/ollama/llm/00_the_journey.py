r"""00 -- The whole journey: from what you type to what you see
=============================================================

CONCEPT IN ONE LINE:
  Your text goes through 12 steps -- half in Ollama, half inside the model -- and comes back
  as ONE token at a time. Each file in this folder zooms into ONE step, in this order.

THE MAP (read left to right, then back along the bottom):

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax
                                                │
                                                └──▶ not finished? back to 04 with one more token

ONE EXAMPLE, ALL THE WAY THROUGH (real llama3.2 values, the same prompt as 01b):

   step              what goes IN                     what comes OUT                     file
   ───────────────── ──────────────────────────────── ────────────────────────────────── ────────────────
   you type          keyboard                         "...The capital of France is"
   01 request        your text                        JSON, HTTP POST to :11434          01_request.py
   02 template       messages [{role, content}]       ONE string with <|...|> markers    02_template.py
   03 tokens         that string                      bytes -> BPE -> 22 IDs             03_tokens.py
                                                      [128000, 128006, 882, ...]
   04 vectors        22 IDs                           22 x 3,072 numbers                 04_vectors.py
   05 layers         22 x 3,072                       22 x 3,072, 28 times over          05_layers.py
   06 scores         the LAST vector                  128,256 scores, one per token      06_scores.py
   07 softmax        128,256 scores                   128,256 probabilities (sum 1)      07_softmax.py
   08 pick           probabilities + temperature      ONE ID: 60704                      08_pick.py
   09 detokenize     60704                            bytes [80,97,114,105,115] "Paris"  09_detokenize.py
   10 loop           22 IDs + 60704                   23 IDs -> back to step 04          10_loop.py
   11 stop?          the picked ID                    <|eot_id|> = 128009 -> finished    11_stop.py
   12 response       all the text + timings           JSON back to your code             12_response.py
   you see           "Paris."

   For "Paris." the steps 04-11 run 3 times:   'Paris'   then   '.'   then   <end>

WHO DOES EACH STEP:

   ┌──────────────────┐    ┌──────────────────────────────────────────────────────────────┐
   │ YOUR CODE        │    │ OLLAMA SERVER (a program on your machine, port 11434)         │
   │                  │    │                                                              │
   │  you type        │───▶│  01 receive request, load the model file into memory          │
   │                  │    │  02 apply the chat template                                   │
   │                  │    │  03 tokenize (rules come FROM the model file)                 │
   │                  │    │   ┌────────────────────────────────────────────────────────┐ │
   │                  │    │   │ THE MODEL (3.2 billion weights from Meta, in the GGUF) │ │
   │                  │    │   │  04 embedding table lookup                             │ │
   │                  │    │   │  05 28 layers                                          │ │
   │                  │    │   │  06 output table -> scores                             │ │
   │                  │    │   └────────────────────────────────────────────────────────┘ │
   │                  │    │  07 softmax   08 pick (uses YOUR temperature etc.)            │
   │                  │    │  09 ID -> text   10 loop   11 stop check                      │
   │  you see     ◀───│────│  12 send the response                                         │
   └──────────────────┘    └──────────────────────────────────────────────────────────────┘

   The MODEL is only steps 04-06: numbers in, scores out. Everything else -- templates,
   tokenizing, picking, looping, stopping -- is done by the program running the model
   (Ollama here; OpenAI's / Anthropic's servers for their models; your code with HF).

WHAT IS "THE MODEL"?

   the model = ARCHITECTURE (the recipe) + WEIGHTS (the numbers)

      architecture "llama":  128,256 vocab -> 3,072 numbers per token -> 28 layers -> 128,256 scores
      weights:               3,212,749,888 learned numbers that fill in that recipe
                             (what one weight is and how training sets it: 05_layers.py)

   - same architecture + different weights = a DIFFERENT model
        (Llama-3.2 base and Llama-3.2 Instruct: same shape, different numbers)
   - it is NOT a program with rules or a database of facts: "Paris" isn't stored anywhere
     as text -- it comes out of multiplying the input by the weights
   - it is ONE function:  token IDs in -> scores for the next token out. It has no memory
     between calls -- a chat works because the app resends everything (01_request.py)
   - in Ollama, "llama3.2" = one GGUF file (weights + shape + vocabulary + Meta's template)
     plus Ollama's own template and stop words, listed in a manifest (01_request.py)

   LIFE OF A MODEL:
      pre-training    predict the next token over trillions     -> "base" model: continues
                      of tokens of text (Meta)                     any text, never stops
      fine-tuning     more training on chat examples, each      -> "Instruct" model: answers,
                      reply ending with <|eot_id|> (Meta)          then stops (02, 11)
                                                                   GGUF general.finetune = "Instruct"
      quantizing      16-bit weights squeezed to ~4-5 bits      -> the 2.0 GB GGUF (Q4_K_M)
                      and published on registry.ollama.ai          `ollama pull` downloads
      inference       YOU send text; weights are frozen         -> everything in this folder

WHERE EACH PIECE OF DATA COMES FROM:

   data                               comes from                         where you can see it
   ────────────────────────────────── ────────────────────────────────── ───────────────────────────
   the chat format (<|eot_id|> ...)   Meta, when they fine-tuned it      /api/show "template", GGUF
   vocabulary (128,256 tokens)        Meta, built ONCE with BPE          GGUF tokenizer.ggml.tokens
   merge rules (280,147)              Meta, same BPE run                 GGUF tokenizer.ggml.merges
   bytes ('P' = 80)                   the UTF-8 standard (everywhere)    ../01c_utf8_bytes_table.py
   token IDs (" France" = 9822)       position in the vocabulary list    03_tokens.py
   the 3.2 B weights                  Meta, training on trillions of     GGUF tensors (~2 GB)
                                      tokens
   temperature, top_k, num_predict    YOU, in "options"                  your request
   timings, counts, done_reason       Ollama, while it runs              the response JSON

   "GGUF" = the model file Ollama downloaded: ~/.ollama/models/blobs/sha256-dde5...
   gguf_reader.py in this folder reads it with plain Python.

IS ANY OF THIS OLLAMA-SPECIFIC?

   step               the idea                        Ollama-specific part
   01 request         every API has one               URL /api/chat, field names
   02 template        every chat model has one        Go template syntax; others hide it
   03-06              the model itself                nothing -- same in any program running llama3.2
   07 softmax         maths, same everywhere          what's exposed: "logprobs"
   08 pick            every API has sampling knobs    option names (num_predict, top_k ...)
   09-11              every API does them             done_reason values
   12 response        every API returns text + usage  JSON field names

   Swap llama3.2 for another model and steps 02-06 change (new template, vocabulary, weights).
   Swap Ollama for another server and only the field names in 01, 08, 12 change.

WHAT OLLAMA SHOWS YOU vs WHAT IS HIDDEN:

   visible in Ollama's API                      hidden (but this folder digs it out)
   the template (/api/show)                     the token IDs        -> 03 rebuilds them from the GGUF
   the token COUNT (prompt_eval_count)          the vectors          -> 04 reads real rows from the GGUF
   top probabilities ("logprobs")               the layers           -> 05 reads real layer weights
   the picked text, done_reason, timings        the raw scores       -> 06 recovers score GAPS

HOW TO USE THIS FOLDER:
   run the files in number order:   python 00_the_journey.py   python 01_request.py   ...
   each one is standalone; all need Ollama running with llama3.2 pulled (ollama pull llama3.2)
   02, 03, 04, 05, 06, 09, 10, 11 also read the model file directly via gguf_reader.py
"""

import json

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def main():
    # the 01b prompt, template written by hand (step 02) so nothing is hidden
    prompt = ("<|start_header_id|>user<|end_header_id|>\n\n"
              "Complete the sentence with one word: The capital of France is<|eot_id|>"
              "<|start_header_id|>assistant<|end_header_id|>\n\n")
    body = {
        "model": CHAT_MODEL,                                 # step 01: which model file to load
        "prompt": prompt,
        "raw": True,                                         # step 02 done by us, not Ollama
        "stream": False,
        "logprobs": True, "top_logprobs": 3,                 # step 07: show the probabilities
        "options": {"temperature": 0},                       # step 08: always take the top one
    }
    resp = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300)   # step 01: the request
    resp.raise_for_status()
    r = resp.json()                                          # step 12: the response

    print("THE JOURNEY, AS SEEN FROM OUTSIDE")
    print(f"03 tokens     prompt_eval_count = {r['prompt_eval_count']} tokens in")
    print(f"10 loop       eval_count        = {r['eval_count']} tokens out = {r['eval_count']} trips through steps 04-11")
    for i, lp in enumerate(r.get("logprobs", []), 1):
        top = ", ".join(f"{t['token']!r} {2.718281828 ** t['logprob']:.4f}" for t in lp["top_logprobs"])
        print(f"07 softmax    token {i}: {top}")
        print(f"08 pick       token {i}: {lp['token']!r}   09 detokenize: bytes {lp.get('bytes')}")
    print(f"11 stop       done_reason       = {r['done_reason']!r}")
    print(f"12 response   response          = {r['response']!r}")
    print(f"              total_duration    = {r['total_duration'] / 1e9:.2f} s "
          f"(load {r['load_duration'] / 1e9:.2f} s)")
    # -> THE JOURNEY, AS SEEN FROM OUTSIDE
    #    03 tokens     prompt_eval_count = 22 tokens in
    #    10 loop       eval_count        = 3 tokens out = 3 trips through steps 04-11
    #    07 softmax    token 1: 'Paris' 0.9988, 'Par' 0.0008, 'France' 0.0001
    #    08 pick       token 1: 'Paris'   09 detokenize: bytes [80, 97, 114, 105, 115]
    #    07 softmax    token 2: '.' 0.6881, '' 0.3114, '!' 0.0004
    #    08 pick       token 2: '.'   09 detokenize: bytes [46]
    #    11 stop       done_reason       = 'stop'
    #    12 response   response          = 'Paris.'
    #                  total_duration    = 0.14 s (load 0.01 s)
    #
    #    eval_count is 3 but only 2 logprobs entries: the 3rd pick was <end> (step 11) --
    #    counted, but not shown as text and no logprobs for it.
    #    '' in token 2's list IS that <end> token -- ~31% chance it would have stopped after 'Paris'.
    #    (load is tiny here because the model was already in memory -- first call: ~2-3 s)

    print("\nraw response JSON (what step 12 sends back):")
    r.pop("logprobs", None)
    print(json.dumps(r, indent=2))


if __name__ == "__main__":
    main()

# Next: python 01_request.py -- then follow the numbers.
