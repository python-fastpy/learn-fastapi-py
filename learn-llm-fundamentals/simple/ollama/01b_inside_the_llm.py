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
   6. softmax       scores -> probabilities that add up to 1                  (STEP 3: top_logprobs)
   7. pick          temperature 0 = always take the top one
   8. loop          append the picked token, run ALL of it again              (STEP 3: prompt_eval_count +1)
   9. stop          the model picks its special <end> token                   (STEP 3: "done_reason": "stop")

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

FULL PICTURE: ONE PREDICTION, TOP TO BOTTOM (steps 1-8)

  Follow the arrows. The right-hand column shows the SHAPE of the data at each stage --
  watch it go from text, to 22 x 3,072 numbers, to 128,256 scores, to ONE token.

   ┌────────────────────────────────────────────────────────────┐   DATA SHAPE
   │ INPUT     "Complete the sentence with one word:            │   a string
   │            The capital of France is"                       │
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ 1 TEMPLATE   wrap it in llama3.2's chat format             │   a longer string
   │   <|start_header_id|>user<|end_header_id|>\n\n             │
   │   Complete the sentence ... France is<|eot_id|>            │
   │   <|start_header_id|>assistant<|end_header_id|>\n\n        │
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ 2 TOKENIZE   cut into pieces, each piece -> its vocab ID   │   22 IDs
   │   <|begin_of_text|> <|start_header_id|> "user" ...         │   [128000, 128006,
   │   " capital" " of" " France" " is" <|eot_id|> ...          │    882, ... ]
   │   ... "assistant" <|end_header_id|> "\n\n"                 │
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ 3 EMBED      each ID -> its row of 3,072 numbers           │   22 x 3,072
   │              (a lookup in a learned table, see ZOOM A)     │
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ 4 28 LAYERS  attention + feed-forward, 28 times            │   22 x 3,072
   │              same shape out, but each vector now           │   (same shape,
   │              "knows" its context        (see ZOOM B)       │    richer meaning)
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼  keep only the LAST position ("\n\n" after assistant)
   ┌────────────────────────────────────────────────────────────┐
   │ 5 SCORES     last vector x output table [3,072 x 128,256]  │   128,256 scores
   │              = one score for EVERY vocab token (ZOOM C)    │
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ 6 SOFTMAX    scores -> probabilities that add up to 1      │   128,256 probs
   │              'Paris' 0.9997  'Par' 0.0002  'France' ...    │   (sum = 1)
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ 7 PICK       temperature 0 -> take the top one             │   1 token
   │              -> 'Paris'                                    │   'Paris'
   └─────────────────────────────┬──────────────────────────────┘
                                 ▼
   ┌────────────────────────────────────────────────────────────┐
   │ 8 LOOP       append 'Paris' to the tokens, go back to 3    │   23 tokens next run
   │              ... until it picks <|eot_id|> = STOP          │
   └────────────────────────────────────────────────────────────┘

   (the token split and IDs are approximate -- Ollama gives the COUNT, 22, not the pieces;
    128000 = <|begin_of_text|> and 128006 = <|start_header_id|> are the real IDs)

ZOOM A -- step 3, EMBED: a lookup table, no maths

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

ZOOM B -- step 4, the 28 LAYERS: what ONE layer does

   All 22 vectors go in side by side (only 6 drawn). Each column = one token.

      "The"   " capital"   " of"   " France"   " is"   ...  "\n\n"
        │         │          │         │         │            │
        ▼         ▼          ▼         ▼         ▼            ▼     22 x 3,072 in
   ┌──────────────────────────────────────────────────────────────────┐
   │ LAYER n                                                          │
   │                                                                  │
   │  (a) ATTENTION -- "which earlier tokens matter to me?"           │
   │      each token looks ONLY BACKWARDS (it can't see the future):  │
   │                                                                  │
   │        " is" ──▶ "The"  " capital"  " of"  " France"             │
   │                   0.05    0.40       0.05    0.50   <- weights   │
   │                           ▲▲▲                ▲▲▲                 │
   │        pulls in mostly " capital" + " France"                    │
   │        24 heads do this at once, each watching for something     │
   │        different (grammar, which noun, position, ...)            │
   │                          │                                       │
   │                          ▼  ADD to the vector (+)                │
   │                                                                  │
   │  (b) FEED-FORWARD -- "what do I know about this?"                │
   │      3,072 -> 8,192 -> 3,072 numbers, per token, on its own      │
   │      a memory lookup: training stored  capital + France = Paris  │
   │                          │                                       │
   │                          ▼  ADD to the vector (+)                │
   └──────────────────────────────────────────────────────────────────┘
        │         │          │         │         │            │
        ▼         ▼          ▼         ▼         ▼            ▼     22 x 3,072 out
                         (same shape, each vector a bit "smarter")

   Stack it 28 times -- same design, each layer has its OWN weights:

      embeddings ─▶ [L1] ─▶ [L2] ─▶ [L3] ─▶ ... ─▶ [L27] ─▶ [L28] ─▶ last vector
                    └─ spelling, ─┘ └──── meaning, ────┘   └─ the task, ─┘
                       grammar          relationships        the answer
   (the attention weights and the early/middle/late split are illustrative)

ZOOM C -- steps 5-7: from the last vector to ONE token

     last vector [3,072]         ("\n\n" after assistant -- through attention it has
           │                      gathered " capital" + " France" + " is")
           ▼
     x output table [3,072 x 128,256]
           │
           ▼
   ┌─────────────────────────┐        ┌───────────────────────────┐
   │ 5 SCORES (logits)       │        │ 6 PROBABILITIES (softmax) │
   │  token        score     │        │  token        probability │
   │  'Paris'      +24.1     │  ───▶  │  'Paris'       0.9997     │ ◀── 7 PICK (temperature 0:
   │  'Par'        +15.7     │        │  'Par'         0.0002     │       take the top one)
   │  ' Paris'     +14.1     │        │  ' Paris'      0.00005    │
   │  'France'     +12.7     │        │  'France'      0.00001    │
   │  'the'         +3.2     │        │  'the'         ~0         │
   │  'banana'      -6.5     │        │  'banana'      ~0         │
   │  ... 128,250 more       │        │  ... all add up to 1      │
   └─────────────────────────┘        └───────────────────────────┘
       any number, + or -                 0 to 1, sum = 1

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

SEE IT VISUALLY (interactive / 3D -- open in a browser):

   what you want to see                         link
   ───────────────────────────────────────────  ─────────────────────────────────────────────────
   THE WHOLE DIAGRAM ABOVE, IN 3D               https://bbycroft.net/llm
     fly through a small GPT: embedding table,  (LLM Visualization -- step through every
     each layer, attention, output, softmax      multiplication; same basic design as llama3.2, smaller)

   THE SAME FLOW, LIVE, WITH YOUR OWN TEXT      https://poloclub.github.io/transformer-explainer/
     type a sentence, watch GPT-2 run in your   (Transformer Explainer -- embeddings -> attention
     browser, see next-token probabilities       -> MLP -> probabilities; has a temperature slider)

   TOKENS (step 2)                              https://tiktokenizer.vercel.app/
     see your text split into colored tokens    (pick a model in the dropdown; token splits differ
     with their IDs                              per model -- llama3.2's own split may not be listed)

   EMBEDDINGS AS POINTS IN 3D (step 3)          https://projector.tensorflow.org/
     words as dots; similar meanings cluster    (Embedding Projector -- search "france", see neighbors)

   WHY IT WORKS -- animated explanations        https://www.3blue1brown.com/lessons/gpt
                                                https://www.3blue1brown.com/lessons/attention
                                                (3Blue1Brown, Deep Learning ch. 5 + 6 -- videos)

   READ IT AS PICTURES                          https://jalammar.github.io/illustrated-transformer/
                                                (The Illustrated Transformer -- classic diagram walkthrough)

  Most of these show GPT-2-sized models (12 layers, 768 numbers, 50k vocab). llama3.2 is the
  same basic design, bigger: 28 layers, 3,072 numbers, 128k vocab. The steps are the same;
  only small details differ (e.g. llama uses RoPE for word order, GPT-2 adds a position vector).

  Steps 3-5 happen inside the model and Ollama does not show them.
  Everything else we can see live.

  We use /api/generate with "raw": True -- WE write the chat template ourselves,
  so nothing is hidden, and "num_predict": 1 -- the model writes only ONE token per call.
"""

import json

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def main():
    print("STEP 1: everything Ollama knows about the model (/api/show)")
    resp = httpx.post(OLLAMA + "/api/show", json={"model": CHAT_MODEL}, timeout=60)
    # ^ the same endpoint in other APIs:
    #   API          | model details
    #   -------------+--------------------------------------
    #   Ollama       | POST /api/show  {"model": "llama3.2"}
    #   OpenAI       | (not available)
    #   Anthropic    | (not available)
    #   Hugging Face | the model's config.json
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

    # STEP 2: the chat template -- what the model REALLY reads.
    # The model was trained to continue text after "assistant<|end_header_id|>".
    # /api/chat builds this for you; with "raw": True we send it as-is.
    prompt = ("<|start_header_id|>user<|end_header_id|>\n\n"
              "Complete the sentence with one word: The capital of France is<|eot_id|>"
              "<|start_header_id|>assistant<|end_header_id|>\n\n")

    print("\nSTEP 3: the loop -- one call = one token")
    for run in range(1, 6):
        body = {
            "model": CHAT_MODEL,
            "prompt": prompt,
            "raw": True,                                    # no template added: we wrote it above
            "stream": False,
            "logprobs": True, "top_logprobs": 3,
            "options": {"temperature": 0, "num_predict": 1},   # ONE token only
            # ^ the same settings in other APIs:
            #   API          | raw prompt, no template | top choices                         | max output tokens | temperature
            #   -------------+-------------------------+-------------------------------------+-------------------+-----------------
            #   Ollama       | "raw": True             | "logprobs": True, "top_logprobs": 3 | "num_predict": 1  | "temperature": 0
            #   OpenAI       | POST /v1/completions    | "logprobs": true, "top_logprobs": 3 | "max_tokens": 1   | "temperature": 0
            #   Anthropic    | (not available)         | (not available)                     | "max_tokens": 1   | "temperature": 0
            #   Hugging Face | (default)               | output_scores=True                  | max_new_tokens=1  | do_sample=False
            #   Ollama puts num_predict + temperature inside "options"; the others put them at top level.
            #   OpenAI /v1/completions = the old (legacy) endpoint that takes a plain "prompt" string.
        }
        resp = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300)
        resp.raise_for_status()
        r = resp.json()
        print(f"--- run {run}")
        print(json.dumps(r, indent=2))
        if r["done_reason"] == "stop":                      # it picked <end> -- finished on its own
            break
        prompt += r["response"]                             # feed its own token back in

    # -> run 1   (real run; "bytes" lists shortened onto one line)   prompt sent:
    #   "<|start_header_id|>user<|end_header_id|>\n\nComplete the sentence with one word: The capital of France is<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n"
    # {
    #   "model": "llama3.2",
    #   "created_at": "2026-10-31T18:01:15.3489675Z",
    #   "response": "Paris",                         <- the ONE token it wrote
    #   "done": true,
    #   "done_reason": "length",                     <- stopped because num_predict: 1, not by choice
    #                                                   (OpenAI: finish_reason "length", Anthropic: stop_reason "max_tokens")
    #   "total_duration": 2923238500,                <- nanoseconds: 2.9 s ...
    #   "load_duration": 2730753400,                 <- ... 2.7 s of it = loading the model (first call only)
    #   "prompt_eval_count": 22,                     <- tokens IN: our template = 22 tokens
    #                                                   (OpenAI: usage.prompt_tokens, Anthropic: usage.input_tokens)
    #   "prompt_eval_cached_count": 0,               <- nothing cached yet (run the file again: 21,
    #                                                   the prompt is still cached from last time)
    #                                                   (OpenAI: usage.prompt_tokens_details.cached_tokens,
    #                                                    Anthropic: usage.cache_read_input_tokens)
    #   "prompt_eval_duration": 186357000,
    #   "eval_count": 1,                             <- tokens OUT
    #                                                   (OpenAI: usage.completion_tokens, Anthropic: usage.output_tokens)
    #   "eval_duration": 1000,
    #   "logprobs": [
    #     {"token": "Paris", "logprob": -0.0012, "bytes": [80, 97, 114, 105, 115],
    #      "top_logprobs": [                         <- probability = math.exp(logprob)
    #        {"token": "Paris",  "logprob": -0.0012, "bytes": [80, 97, 114, 105, 115]},    -> 0.9988
    #        {"token": "Par",    "logprob": -7.1457, "bytes": [80, 97, 114]},              -> 0.0008
    #        {"token": "France", "logprob": -9.8171, "bytes": [70, 114, 97, 110, 99, 101]} -> 0.0001
    #      ]}
    #   ]
    # }
    #
    # -> run 2   prompt is now (run 1's prompt + "Paris"):
    #   "<|start_header_id|>user<|end_header_id|>\n\nComplete the sentence with one word: The capital of France is<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\nParis"
    # {
    #   "model": "llama3.2",
    #   "created_at": "2026-10-31T18:01:18.0574438Z",
    #   "response": ".",
    #   "done": true,
    #   "done_reason": "length",
    #   "total_duration": 105278300,                 <- 0.1 s: model already loaded
    #   "load_duration": 5957900,
    #   "prompt_eval_count": 23,                     <- 22 + 'Paris' = 23: input grew by 1
    #   "prompt_eval_cached_count": 22,              <- KV cache: the first 22 reused from run 1
    #   "prompt_eval_duration": 82480000,
    #   "eval_count": 1,
    #   "eval_duration": 1000,
    #   "logprobs": [
    #     {"token": ".", "logprob": -0.3979, "bytes": [46],
    #      "top_logprobs": [
    #        {"token": ".", "logprob": -0.3979, "bytes": [46]},                            -> 0.67
    #        {"token": "",  "logprob": -1.1154},     <- no bytes = the <end> token          -> 0.33
    #        {"token": "!", "logprob": -7.6267, "bytes": [33]}                             -> 0.0005
    #      ]}
    #   ]
    # }
    #
    # -> run 3   prompt is now (run 2's prompt + "."):
    #   "<|start_header_id|>user<|end_header_id|>\n\nComplete the sentence with one word: The capital of France is<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\nParis."
    # {
    #   "model": "llama3.2",
    #   "created_at": "2026-10-31T18:01:20.7707029Z",
    #   "response": "",                              <- it picked <end>: nothing visible
    #   "done": true,
    #   "done_reason": "stop",                       <- the MODEL decided it was done
    #   "total_duration": 93742900,
    #   "load_duration": 9412400,
    #   "prompt_eval_count": 24,                     <- 23 + '.' = 24
    #   "prompt_eval_cached_count": 23,
    #   "prompt_eval_duration": 76571000,
    #   "eval_count": 1,
    #   "eval_duration": 1000
    # }                                              <- no "logprobs": Ollama hides them for <end>
    #
    # WHAT THIS MEANS:
    #   - prompt_eval_count 22 -> 23 -> 24: the token it just wrote becomes input.
    #   - prompt_eval_cached_count 0 -> 22 -> 23: earlier tokens are NOT re-read (KV cache).
    #   - done_reason "length": we allowed only 1 token.  "stop": it picked <end> itself.
    #   - In run 2 the "" choice IS that <end> token: ~67% "write ." vs ~33% "stop now".
    #   - /api/chat does this same loop for you, in one call, much faster.
    #   (the 4th decimal can wobble between runs, e.g. 0.6717 / 0.6881 -- GPU math noise, not randomness)


if __name__ == "__main__":
    main()

# Try: change temperature to 1 and run a few times -- run 2 sometimes stops right after 'Paris'.
# Compare with 01_next_token.py: there '.' had 0.99, here ~0.7. Same question, but /api/chat
# adds a system/date block to the template -- different text in = different probabilities.
