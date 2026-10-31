"""01b -- Look INSIDE the model: what happens between your text and its answer
============================================================================

CONCEPT IN ONE LINE:
  An LLM is a "predict the next token" function run in a LOOP.
  Here we run that loop BY HAND, one token per call, and watch it.

WHAT HAPPENS INSIDE, STEP BY STEP:

   text ─▶ template ─▶ tokens ─▶ vectors ─▶ 28 layers ─▶ 128k scores ─▶ probabilities ─▶ pick 1
                                   ▲                                                       │
                                   └────────────── append token, repeat until <end> ◀──────┘

   1. template      your message is wrapped in the model's chat format        (STEP 2 below)
   2. tokens        text -> word pieces -> IDs from a vocabulary of 128,256   (STEP 1: vocab_size)
   3. vectors       each ID -> a list of 3,072 numbers ("meaning")            (STEP 1: embedding_length)
   4. layers        28 transformer layers: attention + stored knowledge       (STEP 1: block_count)
   5. scores        last layer -> one score for EVERY token in the vocabulary
   6. softmax       scores -> probabilities that add up to 1                  (STEP 3: top3)
   7. pick          temperature 0 = always take the top one
   8. loop          append the picked token, run ALL of it again              (STEP 3: in= grows by 1)
   9. stop          the model picks its special <end> token                   (STEP 3: done_reason=stop)

WHAT IS A LAYER? (step 4)

  One processing stage. Every token's vector (3,072 numbers) goes through all 28 in order;
  each layer outputs a vector of the same size, a bit more "understood":

   " is" ─▶ [layer 1] ─▶ [layer 2] ─▶ ... ─▶ [layer 28] ─▶ "next token is probably Paris"
             tweak        tweak                 tweak

  Inside EVERY layer, two steps (each with its own learned weights):

   1. ATTENTION     "which earlier tokens matter to me?"
                    " is" looks back at:  "The"  " capital"  " of"  " France"
                                           low     HIGH       low     HIGH
                    24 heads do this 24 ways at once (grammar, which noun, position, ...)

   2. FEED-FORWARD  "what do I know about this?" -- a memory lookup where training
                    stored facts like  capital + France -> Paris

  Both steps ADD to the vector instead of replacing it, so understanding builds up.

  Why 28 and not 1? One layer = one round of "look around, then recall". Roughly:
     early  (1-8)     word pieces, spelling, grammar      "Par" + "is" = Paris
     middle (9-20)    meaning, relationships              "capital OF France"
     late   (21-28)   the task, the answer                "next word = a city: Paris"
  (a rough tendency the model learns by itself, not a strict rule)

  Almost all 3.2 BILLION parameters are the weights inside these 28 layers.
  Cost: EVERY generated token passes through ALL 28 layers.
        'Paris' + '.' + <end> = 3 tokens x 28 = 84 layer passes.
  Bigger models = more, wider layers (llama3.1 70B: 80 layers x 8,192) -> smarter, slower.

  Steps 3-5 happen inside the model and Ollama does not show them.
  Everything else we can see live.

  We use /api/generate with "raw": True -- WE write the chat template ourselves,
  so nothing is hidden, and "num_predict": 1 -- the model writes only ONE token per call.
"""

import math

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def main():
    print("STEP 1: the model's real size (from /api/show)")
    resp = httpx.post(OLLAMA + "/api/show", json={"model": CHAT_MODEL}, timeout=60)
    resp.raise_for_status()
    info = resp.json()["model_info"]
    arch = info["general.architecture"]                     # "llama" -> keys look like "llama.block_count"
    print(f"  parameters      {info['general.parameter_count']:>13,}   learned numbers (weights)")
    print(f"  vocab_size      {info[arch + '.vocab_size']:>13,}   different tokens it knows")
    print(f"  embedding       {info[arch + '.embedding_length']:>13,}   numbers per token (vector)")
    print(f"  layers          {info[arch + '.block_count']:>13,}   transformer blocks, stacked")
    print(f"  attention heads {info[arch + '.attention.head_count']:>13,}   attention runs this many ways at once")
    print(f"  context         {info[arch + '.context_length']:>13,}   max tokens it can read at once")
    # -> parameters      3,212,749,888   learned numbers (weights)
    # -> vocab_size            128,256   different tokens it knows
    # -> embedding               3,072   numbers per token (vector)
    # -> layers                     28   transformer blocks, stacked
    # -> attention heads            24   attention runs this many ways at once
    # -> context               131,072   max tokens it can read at once

    print("\nSTEP 2: the chat template -- what the model REALLY reads")
    prompt = ("<|start_header_id|>user<|end_header_id|>\n\n"
              "Complete the sentence with one word: The capital of France is<|eot_id|>"
              "<|start_header_id|>assistant<|end_header_id|>\n\n")
    print("  " + repr(prompt))
    # The model was trained to continue text after "assistant<|end_header_id|>".
    # /api/chat builds this for you; with "raw": True we send it as-is.

    print("\nSTEP 3: the loop -- one call = one token")
    for run in range(1, 6):
        body = {
            "model": CHAT_MODEL,
            "prompt": prompt,
            "raw": True,                                    # no template added: we wrote it above
            "stream": False,
            "logprobs": True, "top_logprobs": 3,
            "options": {"temperature": 0, "num_predict": 1},   # ONE token only
        }
        resp = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300)
        resp.raise_for_status()
        r = resp.json()

        top = (r.get("logprobs") or [{}])[0].get("top_logprobs", [])
        choices = ", ".join(f"{c['token']!r} {math.exp(c['logprob']):.4f}" for c in top)
        print(f"  run {run}: in={r['prompt_eval_count']:>3} tokens  picked {r['response']!r:<9}"
              f" done_reason={r['done_reason']:<7} top3: {choices}")
        if r["done_reason"] == "stop":                      # it picked <end> -- finished on its own
            break
        prompt += r["response"]                             # feed its own token back in
    # -> run 1: in= 22 tokens  picked 'Paris'   done_reason=length  top3: 'Paris' 0.9988, 'Par' 0.0008, 'France' 0.0001
    # -> run 2: in= 23 tokens  picked '.'       done_reason=length  top3: '.' 0.6717, '' 0.3278, '!' 0.0005
    # -> run 3: in= 24 tokens  picked ''        done_reason=stop    top3:
    # (the 4th decimal can wobble between runs, e.g. 0.6717 / 0.6881 -- GPU math noise, not randomness)

    print("\nSTEP 4: what this means")
    print("  - 'in=' grows by exactly 1 each run: the token it just wrote becomes input.")
    print("  - done_reason=length: it stopped because we allowed only 1 token (num_predict).")
    print("  - done_reason=stop:   it picked its <end> token -- the model decided it was done.")
    print("  - In run 2 the '' choice IS that <end> token: ~70% 'write .' vs ~30% 'stop now'.")
    print("  - /api/chat does this same loop for you, in one call, much faster (KV cache).")


if __name__ == "__main__":
    main()

# Try: change temperature to 1 and run a few times -- run 2 sometimes stops right after 'Paris'.
# Compare with 01_next_token.py: there '.' had 0.99, here ~0.7. Same question, but /api/chat
# adds a system/date block to the template -- different text in = different probabilities.
