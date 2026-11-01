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

WHERE THE CONTEXT FITS IN -- not a step, but the TOKEN LIST that flows through the steps:

   CONTEXT = every token the model can see right now (prompt + answer so far).
   CONTEXT WINDOW = the MAX length of that list: 131,072 trained, 4,096 used by Ollama (num_ctx).

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                    │                            │                          │              │
             num_ctx SET HERE           CONTEXT IS BORN           CONTEXT IS READ          │
             (options, default          your prompt = 22 IDs      attention: each token    │
              4,096 -> memory for       (longer than num_ctx?     looks back at ALL the    │
              the KV cache)              -> cut, silently)        earlier ones (KV cache)  │
                                                                                           │
     you see ◀── 12 response ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax
                     │               │            │
              "context": [IDs]  CONTEXT FULL?  CONTEXT GROWS
              the whole list    drop the old   new token appended: 22 -> 23 -> 24 ...
              returned to you   tokens, keep   then back to 04 with the longer list
                                going ("context
                                shift") -> it forgets the start

   lesson   what it shows about the context
   01       num_ctx option; /api/ps "context_length": 4096
   03       the prompt's token count = how much of the window you use before the answer starts
   05       attention is the ONLY step that looks across tokens -- that's what "using context" means
   10       the window limit, the KV cache, and a live demo of a prompt being cut (PART 4)
   11       what happens when the window is full
   12       the "context" field: the token IDs of the whole exchange

ONE EXAMPLE, ALL THE WAY THROUGH (real llama3.2 values, the same prompt as 01b):

   step              what goes IN                     what comes OUT                     file
   ───────────────── ──────────────────────────────── ────────────────────────────────── ────────────────
   you type          keyboard                         "Complete the sentence with one word:
                                                       The capital of France is"
   01 request        your text                        JSON, HTTP POST to :11434          01_request.py
   02 template       messages [{role, content}]       ONE string with markers like       02_template.py
                                                      <|start_header_id|> and <|eot_id|>
   03 tokens         that string                      bytes -> BPE -> 22 IDs             03_tokens.py
                                                      [128000, 128006, 882, 128007, 271,
                                                       12833, 279, 11914, 449, 832, 3492,
                                                       25, 578, 6864, 315, 9822, 374,
                                                       128009, 128006, 78191, 128007, 271]
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

WHO DOES EACH STEP -- the same 12 steps, four different places they run:

   OLLAMA (this folder):

   ┌──────────────────┐    ┌──────────────────────────────────────────────────────────────┐
   │ YOUR CODE        │    │ OLLAMA SERVER (a program on your machine, port 11434)        │
   │                  │    │                                                              │
   │  you type        │───▶│  01 receive request, load the model file into memory         │
   │                  │    │  02 apply the chat template                                  │
   │                  │    │  03 tokenize (rules come FROM the model file)                │
   │                  │    │   ┌────────────────────────────────────────────────────────┐ │
   │                  │    │   │ THE MODEL (3.2 billion weights from Meta, in the GGUF) │ │
   │                  │    │   │  04 embedding table lookup                             │ │
   │                  │    │   │  05 28 layers                                          │ │
   │                  │    │   │  06 output table -> scores                             │ │
   │                  │    │   └────────────────────────────────────────────────────────┘ │
   │                  │    │  07 softmax   08 pick (uses YOUR temperature etc.)           │
   │                  │    │  09 ID -> text   10 loop   11 stop check                     │
   │  you see     ◀───│────│  12 send the response                                        │
   └──────────────────┘    └──────────────────────────────────────────────────────────────┘
   YOU SEE: the template (/api/show), token COUNTS, top probabilities (logprobs),
   the text, done_reason, timings. The weights are on YOUR disk -- this folder
   reads the token IDs, vectors and layer weights straight from the file.

   OPENAI (GPT models):

   ┌──────────────────┐    ┌──────────────────────────────────────────────────────────────┐
   │ YOUR CODE        │    │ OPENAI'S SERVERS (api.openai.com, in their data centres)     │
   │                  │    │                                                              │
   │  you type        │───▶│  01 receive request, check API key, limits, billing          │
   │ or: the ChatGPT  │    │  02 apply THEIR chat format (hidden from you)                │
   │     app          │    │  03 tokenize: tiktoken (e.g. o200k_base, a public library)   │
   │                  │    │   ┌────────────────────────────────────────────────────────┐ │
   │                  │    │   │ THE MODEL (GPT weights: private, not downloadable)     │ │
   │                  │    │   │  04-06 same idea: embed -> layers -> scores            │ │
   │                  │    │   │  (sizes and layer counts are not published)            │ │
   │                  │    │   └────────────────────────────────────────────────────────┘ │
   │                  │    │  07 softmax   08 pick (your temperature, top_p, seed)        │
   │                  │    │  09 ID -> text   10 loop   11 stop check (+ safety checks)   │
   │  you see     ◀───│────│  12 send the response (JSON, or an SSE stream) + usage       │
   └──────────────────┘    └──────────────────────────────────────────────────────────────┘
   YOU SEE: the text, usage token counts, finish_reason, optional top logprobs.
   HIDDEN: the template, the weights, the layers. Token IDs only if you run
   tiktoken yourself. You pay per token, counted on their side. (hedged)

   ANTHROPIC (Claude models):

   ┌──────────────────┐    ┌──────────────────────────────────────────────────────────────┐
   │ YOUR CODE        │    │ ANTHROPIC'S SERVERS (api.anthropic.com)                      │
   │                  │    │                                                              │
   │  you type        │───▶│  01 receive request, check x-api-key, limits, billing        │
   │ or: Claude.ai,   │    │  02 apply THEIR chat format (hidden); system = own field     │
   │     Claude Code  │    │  03 tokenize: Claude's own tokenizer (not published)         │
   │                  │    │   ┌────────────────────────────────────────────────────────┐ │
   │                  │    │   │ THE MODEL (Claude weights: private, not downloadable)  │ │
   │                  │    │   │  04-06 same idea: embed -> layers -> scores            │ │
   │                  │    │   │  (sizes and layer counts are not published)            │ │
   │                  │    │   └────────────────────────────────────────────────────────┘ │
   │                  │    │  07 softmax   08 pick (your temperature, top_p, top_k)       │
   │                  │    │  09 ID -> text   10 loop   11 stop check                     │
   │  you see     ◀───│────│  12 send the response (JSON, or SSE events) + usage          │
   └──────────────────┘    └──────────────────────────────────────────────────────────────┘
   YOU SEE: the text, usage input/output tokens, stop_reason. HIDDEN: the template,
   the tokenizer, token IDs, probabilities (no logprobs), the weights. A token COUNT
   is available from the token-counting endpoint. You pay per token. (hedged)

   HUGGING FACE transformers (on your machine, no server):

   ┌──────────────────┐    ┌──────────────────────────────────────────────────────────────┐
   │ YOU              │    │ YOUR PYTHON PROCESS (transformers library -- you run it)     │
   │                  │    │                                                              │
   │  you type        │───▶│  01 from_pretrained(): download from the Hub once            │
   │                  │    │     (~/.cache/huggingface), load weights into RAM / GPU      │
   │                  │    │  02 tokenizer.apply_chat_template(messages)                  │
   │                  │    │  03 tokenizer(text) -> input_ids         (tokenizer.json)    │
   │                  │    │   ┌────────────────────────────────────────────────────────┐ │
   │                  │    │   │ THE MODEL (the SAME Llama 3.2 weights -- public)       │ │
   │                  │    │   │  04-06 model(input_ids).logits -> all 128,256 scores   │ │
   │                  │    │   │  (safetensors, 16-bit: ~6.4 GB vs Ollama's 2.0 GB)     │ │
   │                  │    │   └────────────────────────────────────────────────────────┘ │
   │                  │    │  07-11 model.generate(): softmax, pick, loop, stop at EOS    │
   │                  │    │        (or write the loop yourself around model())           │
   │  you see     ◀───│────│  12 tokenizer.decode(output_ids) -> you print it             │
   └──────────────────┘    └──────────────────────────────────────────────────────────────┘
   YOU SEE: everything -- token IDs, vectors (output_hidden_states=True), every layer,
   all raw scores. Nothing is hidden, because it all runs in YOUR code. (Hugging Face
   also offers hosted inference APIs -- those work like the OpenAI / Anthropic boxes.)

   SIDE BY SIDE:

   question                 Ollama             OpenAI            Anthropic         HF transformers
   where does it run?       your machine       their servers     their servers     your machine
   the weights              downloaded (GGUF)  private           private           downloaded
                                                                                   (safetensors)
   the chat template        visible            hidden            hidden            visible
   token IDs                count only (03     only via          count only        visible
                            rebuilds them)     tiktoken
   probabilities            top logprobs       top logprobs      none              all raw scores
   cost                     free (your PC)     per token         per token         free (your PC)

   In ALL four, the MODEL is only steps 04-06: numbers in, scores out. Everything else --
   templates, tokenizing, picking, looping, stopping -- is done by the program around it.

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

   WHAT DOES "llama3.2" / "Llama 3.2 3B" MEAN?  -- every part of the name:

      Llama   3   .2   3B   Instruct   Q4_K_M
        │     │    │    │      │         └─ QUANTIZATION: each weight squeezed to ~4-5 bits
        │     │    │    │      │            (16-bit original ≈ 6.4 GB -> this file ≈ 2.0 GB)
        │     │    │    │      └─ fine-tuned to CHAT (answer, then stop) -- not the "base" model
        │     │    │    └─ SIZE: ~3 Billion PARAMETERS (exactly 3,212,749,888, rounded to "3B")
        │     │    └─ point release of generation 3 (September 2024)
        │     └─ GENERATION 3 (new training data, new 128,256 vocabulary vs Llama 2's 32,000)
        └─ the model FAMILY, made by Meta

   CAREFUL: "3.2" is the VERSION, "3B" is the SIZE. It is NOT "3.2 B parameters" --
   that the real count is also ~3.2 billion is a coincidence. llama3.2:1b is version 3.2 too.

   THE LLAMA 3 FAMILY (all share the same 128,256-token vocabulary -- 03_tokens.py):
      version     released    sizes (parameters)          note
      Llama 3     Apr 2024    8B, 70B                     8k context
      Llama 3.1   Jul 2024    8B, 70B, 405B               128k context
      Llama 3.2   Sep 2024    1B, 3B  (+ 11B, 90B vision)  128k context, small for laptops
      Llama 3.3   Dec 2024    70B                         better 70B

   OLLAMA NAMES -- "name:tag", the tag picks size / variant:
      llama3.2            = llama3.2:latest = llama3.2:3b   (3B, Instruct, Q4_K_M, 2.0 GB)
      llama3.2:1b         the 1B one        (same vocabulary, 16 layers instead of 28)
      llama3.1:70b        a different version AND size   (~40 GB)
      `ollama show llama3.2` prints: parameters 3.2B, quantization Q4_K_M, context 131072

   CONTEXT = how many TOKENS (prompt + answer) the model can look at at once.
      131,072 is what Meta TRAINED it for; Ollama only USES 4,096 unless you set num_ctx.
      Longer than that and old tokens are dropped -- the model forgets. Full story: 10_loop.py.

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
   the chat format (<|eot_id|> and    Meta, when they fine-tuned it      /api/show "template", GGUF
    the other markers)
   vocabulary (128,256 tokens)        Meta, built ONCE with BPE          GGUF tokenizer.ggml.tokens
   merge rules (280,147)              Meta, same BPE run                 GGUF tokenizer.ggml.merges
   bytes ('P' = 80)                   the UTF-8 standard (everywhere)    ../01c_utf8_bytes_table.py
   token IDs (" France" = 9822)       position in the vocabulary list    03_tokens.py
   the 3.2 B weights                  Meta, training on trillions of     GGUF tensors (~2 GB)
                                      tokens
   temperature, top_k, num_predict    YOU, in "options"                  your request
   timings, counts, done_reason       Ollama, while it runs              the response JSON

   "GGUF" = the model file Ollama downloaded:
      ~/.ollama/models/blobs/sha256-dde5aa3fc5ffc17176b5e8bdc82f587b24b2678c6c66101bf7da77af9f7ccdff
   gguf_reader.py in this folder reads it with plain Python.

IS ANY OF THIS OLLAMA-SPECIFIC?

   step               the idea                        Ollama-specific part
   01 request         every API has one               URL /api/chat, field names
   02 template        every chat model has one        Go template syntax; others hide it
   03-06              the model itself                nothing -- same in any program running llama3.2
   07 softmax         maths, same everywhere          what's exposed: "logprobs"
   08 pick            every API has sampling knobs    option names (num_predict, top_k, num_ctx)
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
   run the files in number order, from python 00_the_journey.py to python 12_response.py
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
