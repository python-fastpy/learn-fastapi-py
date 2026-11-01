r"""10 -- LOOP: append the picked token and run the model AGAIN
===========================================================

CONCEPT IN ONE LINE:
  One model run = ONE new token. A whole answer is that run repeated in a LOOP:
  pick a token, glue it to the end of the input, run again -- until it stops (11).

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── 11 stop? ◀── [10 loop] ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax

WHAT HAPPENS -- the real loop for "Count from 1 to 5, separated by spaces." (PART 1):

   step   input tokens            model run (03-08)        picked     input grows to
    1     22 (the template)  ─▶  28 layers ─▶ pick  ─▶     '1'        22 + 1 = 23
    2     23                 ─▶  28 layers ─▶ pick  ─▶     ' '        24
    3     24                 ─▶  28 layers ─▶ pick  ─▶     '2'        25
    4     25                 ─▶  28 layers ─▶ pick  ─▶     ' '        26
    5     26                 ─▶  28 layers ─▶ pick  ─▶     '3'        27
    6     27                 ─▶  28 layers ─▶ pick  ─▶     ' '        28
    7     28                 ─▶  28 layers ─▶ pick  ─▶     '4'        29
    8     29                 ─▶  28 layers ─▶ pick  ─▶     ' '        30
    9     30                 ─▶  28 layers ─▶ pick  ─▶     '5'        31
   10     31                 ─▶  28 layers ─▶ pick  ─▶     <end>      STOP (11)

   ┌──────────────────────────────────────────────────────────────┐
   │  tokens ─▶ MODEL ─▶ probabilities ─▶ pick ─▶ new token        │
   │    ▲                                            │             │
   │    └──────────── append it to the tokens ◀──────┘             │
   └──────────────────────────────────────────────────────────────┘
   "1 2 3 4 5" = 9 visible tokens + <end> = 10 model runs = "eval_count": 10

THE KV CACHE -- why step 10 is not 10x slower than step 1:

   Inside attention (05), every token makes a KEY and a VALUE vector ("what I am", "what I
   carry"). Old tokens' keys/values never change, so the server KEEPS them in memory:

      run 1:   compute K,V for tokens 1-22         -> keep them        (expensive: 22 tokens)
      run 2:   reuse K,V 1-22, compute ONLY #23    -> keep it          (cheap: 1 token)
      run 3:   reuse K,V 1-23, compute ONLY #24    -> keep it          (and so on, every run)

   You can SEE it: "prompt_eval_cached_count" = tokens whose K,V were reused (PART 1: 22, 23,
   24, 25, 26, 27, 28, 29, 30 -- each = all but the newest). Once in a while the cache misses (seen in one run:
   0 cached, ~2.3 s) and everything is computed again -- same answer, just slower.

PREFILL vs DECODE -- the two speeds in every response (PART 3):

   PREFILL  read the whole prompt         all tokens at once, in parallel   ~140-150 tok/s here
            "prompt_eval_count", "prompt_eval_duration"
   DECODE   write the answer              ONE token per run, must wait for  ~20-25 tok/s here
            "eval_count", "eval_duration" the previous one (it's a loop!)
   (numbers from this laptop, CPU only -- /api/ps "size_vram": 0. A GPU is much faster.)

   That's why long answers are slow but long prompts are fairly quick, and why APIs charge
   output tokens more than input tokens.

THE CONTEXT WINDOW -- how long the loop can run:

   prompt + everything generated must fit in the context window:
      the MODEL can handle    131,072 tokens    (GGUF: llama.context_length -- set by Meta)
      Ollama ACTUALLY uses      4,096 tokens    (/api/ps "context_length" -- Ollama's default
                                                 here; change with options "num_ctx")
   Bigger num_ctx = more memory for the KV cache.

   When it doesn't fit (PART 4, num_ctx 128):
      - a too-long PROMPT is silently CUT: 618 tokens in -> "prompt_eval_count": 66
      - a too-long ANSWER keeps going: Ollama drops old tokens to make room ("context shift")
        -- the model just forgets the start. 300 tokens generated with num_ctx 128.
   Neither raises an error -- check prompt_eval_count if answers ignore your instructions.

WHERE THIS COMES FROM:
   the loop          Ollama's server (llama.cpp runner, /api/ps "runner": "llamacpp") -- not
                     the model; the model only ever does ONE step
   the KV cache      Ollama's server memory; reused across calls with the same prompt start
   context_length    131,072 = trained limit, from the GGUF (Meta); num_ctx = Ollama setting
   the counters      Ollama's response JSON (12)

IS IT OLLAMA-SPECIFIC?
   who                 the loop                          you see the steps?   KV cache
   the model itself    no -- one step: tokens -> probs   --                    --
   Ollama              server-side, /api/generate        stream: 1 chunk per   yes, shows
                       ("num_predict": 1 = do 1 step)    token                 cached count
   OpenAI              server-side                       stream: chunks        yes ("cached
                                                                               tokens", hedged)
   Anthropic           server-side                       stream: text deltas   prompt caching
                                                                               (opt-in, hedged)
   Hugging Face        model.generate() loops in Python  streamer / your own   past_key_values
                       on your machine                   loop with model()
   Every LLM works this way -- even the biggest hosted ones generate one token per step.

COMMON CONFUSIONS:
   - "the model writes the whole answer at once"  -> no, one token per run (PART 1).
   - "in a manual loop, prompt_eval_count = my prompt"  -> it's the prompt + the answer so
     far: it grows by 1 every step (PART 1).
   - "131,072 context in the model card = what I get"  -> Ollama uses num_ctx (4,096 here).

SEE IT VISUALLY:
   https://bbycroft.net/llm   (one full step through the model -- the loop repeats it)
"""

import json
import sys
import time

import httpx

from gguf_reader import read_gguf

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def chat_prompt(text):
    return ("<|start_header_id|>user<|end_header_id|>\n\n" + text + "<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n")


def generate(prompt, **options):
    body = {"model": CHAT_MODEL, "prompt": prompt, "raw": True, "stream": False, "options": options}
    resp = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300)
    resp.raise_for_status()
    return resp.json()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    prompt = chat_prompt("Count from 1 to 5, separated by spaces.")

    print("PART 1: the loop BY HAND -- one call = one token")
    text = prompt
    for step in range(1, 20):
        r = generate(text, temperature=0, num_predict=1)
        print(f"   step {step:2}  picked {r['response']!r:5}  input {r['prompt_eval_count']}  "
              f"cached {r.get('prompt_eval_cached_count', 0):2}  {r['total_duration'] / 1e6:5.0f} ms  "
              f"{r['done_reason']}")
        if r["done_reason"] == "stop":                       # it picked <end>
            break
        text += r["response"]                                # THE LOOP: append, run again
    # ->    step  1  picked '1'    input 22  cached  5    173 ms  length
    #       step  2  picked ' '    input 23  cached 22     59 ms  length   <- 22 reused, 1 new
    #       step  3  picked '2'    input 24  cached 23     54 ms  length
    #       step  4  picked ' '    input 25  cached 24     56 ms  length
    #       step  5  picked '3'    input 26  cached 25     53 ms  length
    #       step  6  picked ' '    input 27  cached 26     55 ms  length
    #       step  7  picked '4'    input 28  cached 27     69 ms  length
    #       step  8  picked ' '    input 29  cached 28     66 ms  length
    #       step  9  picked '5'    input 30  cached 29     59 ms  length
    #       step 10  picked ''     input 31  cached 30     51 ms  stop     <- <end>, nothing visible
    # (cached counts vary run to run -- they depend on what the server still has in memory;
    #  in an earlier run step 3 showed "cached 0" and took 2350 ms: a cache miss)

    print("\nPART 2: the SAME loop, done by Ollama in one call")
    r = generate(prompt, temperature=0)
    print("  ", repr(r["response"]), "eval_count", r["eval_count"], r["done_reason"])
    # ->    '1 2 3 4 5' eval_count 10 stop        <- 10 runs inside the server, 1 HTTP call

    print("\nPART 3: streaming -- watch each loop step arrive")
    body = {"model": CHAT_MODEL, "prompt": chat_prompt("Write two sentences about the sea."),
            "raw": True, "stream": True, "options": {"temperature": 0}}
    start, arrivals = time.time(), []
    with httpx.stream("POST", OLLAMA + "/api/generate", json=body, timeout=300) as resp:
        for line in resp.iter_lines():                       # one JSON line per token
            chunk = json.loads(line)
            arrivals.append((time.time() - start, chunk["response"]))
            if chunk["done"]:
                last = chunk
    for t, tok in arrivals:
        print(f"   {t:6.3f} s  {tok!r}")
    print(f"   ({len(arrivals)} chunks in total)")
    prefill = last["prompt_eval_count"] / (last["prompt_eval_duration"] / 1e9)
    decode = last["eval_count"] / (last["eval_duration"] / 1e9)
    print(f"   prefill {last['prompt_eval_count']} tokens at {prefill:.0f} tok/s | "
          f"decode {last['eval_count']} tokens at {decode:.1f} tok/s")
    # ->     2.639 s  'The'           <- connecting + prefill (see note below)
    #        2.681 s  ' sea'          <- then ~45 ms per token: one loop step each
    #        2.725 s  ' is'
    #        2.768 s  ' a'
    #        2.812 s  ' vast'
    #        2.856 s  ' and'
    #        2.901 s  ' mysterious'
    #        2.982 s  ' body'
    #        3.031 s  ' of'
    #        3.074 s  ' salt'
    #        3.117 s  'water'
    #        3.159 s  ' that'
    #        3.204 s  ' covers'
    #        3.251 s  ' over'
    #        3.296 s  ' '
    #        3.341 s  '70'
    #        3.388 s  '%'
    #        3.433 s  ' of'
    #        3.481 s  ' the'
    #        3.531 s  ' Earth'
    #        3.579 s  "'s"
    #        3.626 s  ' surface'
    #        3.676 s  '.'
    #        3.728 s  ' Its'
    #        3.779 s  ' waves'
    #        3.821 s  ' and'
    #        3.865 s  ' t'
    #        3.912 s  'ides'
    #        3.957 s  ' have'
    #        4.002 s  ' shaped'
    #        4.047 s  ' the'
    #        4.092 s  ' coast'
    #        4.138 s  'lines'
    #        4.186 s  ' and'
    #        4.234 s  ' influenced'
    #        4.283 s  ' the'
    #        4.339 s  ' lives'
    #        4.388 s  ' of'
    #        4.450 s  ' countless'
    #        4.510 s  ' people'
    #        4.571 s  ' throughout'
    #        4.629 s  ' history'
    #        4.688 s  '.'
    #        4.742 s  ''              <- the <end> token: counted, nothing visible
    #       (44 chunks in total)
    #       prefill 17 tokens at 119 tok/s | decode 44 tokens at 20.9 tok/s
    # NOTE: prefill itself took ~0.14 s. Most of the 2.6 s is the Windows "localhost"
    #       connection delay (01_request.py, COMMON CONFUSIONS), not the model.

    print("\nPART 4: the context window")
    meta, _, _ = read_gguf()
    running = httpx.get(OLLAMA + "/api/ps").json()["models"]
    print("   model can handle (GGUF llama.context_length):", meta["llama.context_length"])
    print("   Ollama is using  (/api/ps context_length):   ",
          [m.get("context_length") for m in running if m["name"].startswith(CHAT_MODEL)])
    long = chat_prompt("The quick brown fox jumps over the lazy dog. " * 60 + "How many times did the fox jump?")
    full = generate(long, temperature=0, num_predict=1)
    cut = generate(long, temperature=0, num_predict=1, num_ctx=128)
    print("   long prompt, default num_ctx -> prompt_eval_count", full["prompt_eval_count"])
    print("   long prompt, num_ctx 128     -> prompt_eval_count", cut["prompt_eval_count"], "(silently cut!)")
    # ->    model can handle (GGUF llama.context_length): 131072
    #       Ollama is using  (/api/ps context_length):    [4096]
    #       long prompt, default num_ctx -> prompt_eval_count 618
    #       long prompt, num_ctx 128     -> prompt_eval_count 66 (silently cut!)
    # (/api/ps shows the model only while it's loaded; asking with num_ctx 128 reloads it
    #  with that size, so the next call with the default may take a moment longer)


if __name__ == "__main__":
    main()

# Try: in PART 3 add "num_predict": 300 and "num_ctx": 128 -- it still writes 300 tokens
#      (context shift), but the early tokens -- your question -- have been dropped by then.
