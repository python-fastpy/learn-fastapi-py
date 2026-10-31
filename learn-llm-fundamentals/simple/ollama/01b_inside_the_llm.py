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

FULL PICTURE: TEXT -> TEMPLATE -> TOKENS -> 28 LAYERS -> 128k SCORES (steps 1-7)

   TEXT           "Complete the sentence with one word: The capital of France is"
                                                          │
   TEMPLATE       wrap it in llama3.2's chat format (STEP 2 prints this):
                                                          ▼
        <|start_header_id|>user<|end_header_id|>\n\n
        Complete the sentence with one word: The capital of France is<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>\n\n
                                                          │
   TOKENS         split into pieces, each piece -> an ID from the 128,256 vocabulary
                                                          ▼
        <|begin_of_text|> <|start_header_id|> "user" <|end_header_id|> "\n\n"
        "Complete" " the" " sentence" " with" " one" " word" ":" " The"
        " capital" " of" " France" " is" <|eot_id|>
        <|start_header_id|> "assistant" <|end_header_id|> "\n\n"
                                                          = 22 tokens  (STEP 3: run 1 in= 22)
        (the split shown is approximate -- Ollama gives the COUNT, not the pieces)
                                                          │
   Below, only the 5 tokens that matter for the answer are drawn;
   in reality all 22 go through the layers side by side.  ▼

   EMBEDDING      each token ID -> look up its row in a learned table (no maths, just a lookup)

                          3,072 columns (numbers)
                        ┌──────────────────────────────────────┐
     ID 0      "!"      │  0.012  -0.341   0.077  ...   0.210  │
     ...                │                 ...                  │
     ID 9822   " France"│  0.231  -0.874   0.112  ...   0.045  │  <- one row = one token's embedding
     ...                │                 ...                  │
     ID 128255          │  ...                                 │
                        └──────────────────────────────────────┘
                          128,256 rows (one per vocabulary token)
     size: 128,256 x 3,072 = 394 million numbers  (~12% of the 3.2 B parameters)

     " France" -> ID 9822 -> row 9822 -> [0.231, -0.874, 0.112, ..., 0.045]

     Training moves the rows so SIMILAR MEANINGS = SIMILAR NUMBERS:
        " France" ●───● " Germany"        countries close together
                    ● " Italy"
        " Paris"  ●───● " Berlin"         capitals close together
        " banana" ●                       far from both
     (IDs, numbers and the picture are illustrative -- Ollama doesn't expose the table)

     The row is the token's meaning ON ITS OWN -- " is" gets the same row in every sentence.
     Context comes later, from the layers. Word ORDER is added inside attention (RoPE).
     Not the same as lesson 14's embeddings: those are ONE vector for a WHOLE text.

   Input tokens:   "The"  " capital"  " of"  " France"  " is"   ... "\n\n"
                     │        │         │        │        │
                  [3,072]  [3,072]   [3,072]  [3,072]  [3,072]    <- each token = its 3,072-number row
                     │        │         │        │        │
   ┌─────────────────┴────────┴─────────┴────────┴────────┴──────────────┐
   │  LAYER 1                                                            │
   │   ATTENTION (24 heads): each token looks at the tokens before it    │
   │       " is" ──looks at──▶ " capital" (HIGH)   " France" (HIGH)      │
   │   FEED-FORWARD (8,192 wide): "memory lookup" of learned facts       │
   │   output: still 3,072 numbers per token, slightly "smarter"         │
   └─────────────────────────────────────────────────────────────────────┘
                     │        │         │        │        │
   ┌─────────────────┴────────┴─────────┴────────┴────────┴──────────────┐
   │  LAYER 2        same structure, its OWN weights                     │
   └─────────────────────────────────────────────────────────────────────┘
                    ...      ...       ...      ...      ...     (layers 3 ... 27)
   ┌─────────────────┴────────┴─────────┴────────┴────────┴──────────────┐
   │  LAYER 28       same structure, its OWN weights                     │
   └─────────────────────────────────────────────────────────────────────┘
                                                          │
              only the LAST token's vector ("\n\n" after   │ assistant) is used to predict --
              through attention it has gathered " capital" │ + " France" + " is"
                                                          ▼
                                                      [3,072]   <- "what does the assistant say first?"
                                                          │
   OUTPUT LAYER   3,072 numbers x weight table [3,072 x 128,256]
                                                          ▼
   128,256 SCORES (logits) -- one for EVERY token in the vocabulary:
        token        score
        ────────────────────
        'Paris'      +24.1   ◀── highest
        'Par'        +15.7
        ' Paris'     +14.1
        'France'     +12.7
        'the'         +3.2
        'banana'      -6.5
        ... 128,250 more ...
                                                          │
   SOFTMAX        scores -> probabilities (all positive, add up to 1)
                                                          ▼
        'Paris' 0.9997   'Par' 0.0002   ' Paris' 0.00005   'France' 0.00001   ...
                                                          │
   PICK           temperature 0 -> take the top one       ▼
                                                       'Paris'

  Score GAP -> probability gap:  'Paris' +24.1 vs 'Par' +15.7 = 8.4 apart
                                 -> e^8.4 ≈ 4,400x more likely
  (Ollama does not return the raw scores: the numbers above are made up so their GAPS
   match the real probabilities. The probabilities themselves are real.)

     piece                    llama3.2     /api/show field (STEP 1)
     vector per token         3,072        embedding_length
     layers                   28           block_count
     attention heads          24           attention.head_count
     feed-forward width       8,192        feed_forward_length
     scores per prediction    128,256      vocab_size

  Steps 3-5 happen inside the model and Ollama does not show them.
  Everything else we can see live.

  We use /api/generate with "raw": True -- WE write the chat template ourselves,
  so nothing is hidden, and "num_predict": 1 -- the model writes only ONE token per call.
"""

import json
import math

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def main():
    print("STEP 1: everything Ollama knows about the model (/api/show)")
    resp = httpx.post(OLLAMA + "/api/show", json={"model": CHAT_MODEL}, timeout=60)
    resp.raise_for_status()
    show = resp.json()
    show.pop("license", None)                        # 14 KB of legal text -- not useful here
    print(json.dumps(show, indent=2))
    # -> {
    # "thinking": {"values": [false], "default": false},  <- can it "think" first? no (lesson 08)
    # "modelfile": "# Modelfile generated by \"ollama show\"\n...FROM C:\\Users\\...\\.ollama\\models\\blobs\\sha256-dde5...
    #               TEMPLATE ...  PARAMETER ...  LICENSE ...",    <- recipe for this model (~16 KB, lesson 18)
    # "parameters": "stop \"<|start_header_id|>\"\nstop \"<|end_header_id|>\"\nstop \"<|eot_id|>\"",
    #                                                     <- stop generating when it writes one of these
    # "template": "<|start_header_id|>system<|end_header_id|>\n\nCutting Knowledge Date: December 2023\n\n
    #              {{ if .System }}{{ .System }} ... {{ range $i, $_ := .Messages }} ...",
    #                                                     <- how /api/chat turns messages into text (STEP 2)
    # "template_source": "go_template",
    # "details": {"parent_model": "", "format": "gguf", "family": "llama", "families": ["llama"],
    #             "parameter_size": "3.2B",
    #             "quantization_level": "Q4_K_M"},        <- weights squeezed to ~4 bits each -> ~2 GB file
    # "capabilities": ["completion", "tools"],            <- can chat + call tools (lesson 10)
    # "modified_at": "2026-10-31T16:39:49.1145141+05:30",
    # "model_info": {                                     <- the model's SHAPE (printed order may differ):
    #   "general.architecture": "llama",
    #   "general.basename": "Llama-3.2",
    #   "general.file_type": 15,
    #   "general.finetune": "Instruct",                   <- tuned to follow chat instructions
    #   "general.languages": ["en", "de", "fr", "it", "pt", "hi", "es", "th"],
    #   "general.parameter_count": 3212749888,            <- 3.2 BILLION learned numbers (weights)
    #   "general.quantization_version": 2,
    #   "general.size_label": "3B",
    #   "general.tags": ["facebook", "meta", "pytorch", "llama", "llama-3", "text-generation"],
    #   "general.type": "model",
    #   "llama.attention.head_count": 24,                 <- attention runs 24 ways at once
    #   "llama.attention.head_count_kv": 8,               <- heads share 8 key/value sets (smaller KV cache)
    #   "llama.attention.key_length": 128,
    #   "llama.attention.layer_norm_rms_epsilon": 1e-05,
    #   "llama.attention.value_length": 128,
    #   "llama.block_count": 28,                          <- 28 LAYERS, stacked
    #   "llama.context_length": 131072,                   <- max tokens it can read at once
    #   "llama.embedding_length": 3072,                   <- numbers per token (the vector)
    #   "llama.feed_forward_length": 8192,                <- size of the "memory lookup" inside each layer
    #   "llama.rope.dimension_count": 128,                <- RoPE = how the model knows token ORDER
    #   "llama.rope.freq_base": 500000,
    #   "llama.vocab_size": 128256,                       <- different tokens it knows
    #   "tokenizer.ggml.bos_token_id": 128000,            <- <|begin_of_text|>, added at the start of every call
    #   "tokenizer.ggml.eos_token_id": 128009,            <- <|eot_id|>, the <end> token it picks to stop
    #   "tokenizer.ggml.merges": [],                      <- (empty: Ollama leaves out the big lists)
    #   "tokenizer.ggml.model": "gpt2",                   <- BPE tokenizer, same family as GPT-2
    #   "tokenizer.ggml.pre": "llama-bpe",
    #   "tokenizer.ggml.token_type": [],
    #   "tokenizer.ggml.tokens": []
    # }}
    # 24 heads x 128 (key_length) = 3,072 = embedding_length -- the heads split the vector between them.

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
