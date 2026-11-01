"""01 -- See a REAL model guess the next token
==============================================

CONCEPT IN ONE LINE:
  An LLM only predicts the NEXT token, with a probability for each choice.
  A full answer = that prediction repeated in a loop.        (details: simple/01)

WHAT WE DO:
  Ask llama3.2 to continue "The capital of France is" and ask Ollama to show
  the top 5 candidates the model considered for EVERY token it wrote (logprobs).

   "The capital of France is"
          │
          ▼
   ┌──────────────┐    " Paris"   0.9x   ◀── picked (most likely)
   │  llama3.2    │ ─▶ " located" 0.0x
   └──────────────┘    " the"     0.0x
          │  add " Paris", run the model AGAIN
          ▼
   "The capital of France is Paris" ─▶ "." ─▶ ... ─▶ stop

  logprob = log(probability). We turn it back with exp(): exp(-0.05) = 0.95
"""

import math

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def main():
    prompt = "Complete the sentence with one word: The capital of France is"
    body = {
        "model": CHAT_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "logprobs": True, "top_logprobs": 5,        # show the model's top 5 choices
        "options": {"temperature": 0, "num_predict": 6},
        # ^ the same settings in other APIs:
        #   API          | top choices                         | max output tokens | temperature
        #   -------------+-------------------------------------+-------------------+-----------------
        #   Ollama       | "logprobs": True, "top_logprobs": 5 | "num_predict": 6  | "temperature": 0
        #   OpenAI       | "logprobs": true, "top_logprobs": 5 | "max_tokens": 6   | "temperature": 0
        #   Anthropic    | (not available)                     | "max_tokens": 6   | "temperature": 0
        #   Hugging Face | output_scores=True                  | max_new_tokens=6  | do_sample=False
        #   Ollama puts num_predict + temperature inside "options"; the others put them at top level.
    }
    resp = httpx.post(OLLAMA + "/api/chat", json=body, timeout=300)   # json= sends body as JSON
    # WHAT HAPPENS INSIDE THIS ONE CALL, TURN BY TURN (Ollama runs the loop, we just wait):
    #
    # TURN 0 -- prepare + read the prompt ("prefill")
    #   1. Template: Ollama wraps our text in llama3.2's chat format (roughly):
    #        <|start_header_id|>system<|end_header_id|> Cutting Knowledge Date: ...<|eot_id|>
    #        <|start_header_id|>user<|end_header_id|> Complete the sentence ... France is<|eot_id|>
    #        <|start_header_id|>assistant<|end_header_id|>
    #   2. Tokenize: that text -> 37 tokens                       (prompt_eval_count: 37)
    #   3. All 37 go through the 28 layers TOGETHER, in parallel, and their attention
    #      data is saved in the KV cache so they are never processed again.
    #      20 of them were already cached from our last call      (prompt_eval_cached_count: 20)
    #
    # TURN 1 -- reads ...assistant<|end_header_id|>           -> picks 'Paris'
    #   The LAST position's vector went through all 28 layers: attention pulled in
    #   " capital" + " France", feed-forward recalled "-> Paris".
    #   Last layer -> 128,256 scores -> softmax -> probabilities:
    #        'Paris' 0.9997   'Par' 0.0002   ' Paris' 0.00005   ' paris' ...   'France' ...
    #   temperature 0 = take the top one -> 'Paris'. Append it, add it to the cache.
    #
    # TURN 2 -- reads ...assistant<|end_header_id|>Paris      -> picks '.'
    #   Only the NEW token 'Paris' goes through the 28 layers; the other 37 come from
    #   the KV cache -- that's why each turn is fast.
    #        '.' 0.99   '' 0.01 (= <end>)   '!' 0.00   ',' 0.00
    #
    # TURN 3 -- reads ...assistant<|end_header_id|>Paris.     -> picks <|eot_id|> (<end>)
    #   The model picks its end-of-turn token -> generation STOPS  (done_reason: "stop")
    #   (hitting num_predict: 6 first would give done_reason: "length")
    #   <end> is not shown in content or logprobs -- that's why STEP 2 prints only 2 tokens.
    #
    # TURN 4 -- tokens back to text: 'Paris' + '.' -> "Paris."     (message.content)
    #   eval_count: 3 (= turns 1-3)   eval_duration 0.14 s (~0.05 s per token)   total 0.36 s
    #
    #   turn | tokens through the 28 layers | picked  | probability
    #   -----+------------------------------+---------+------------
    #    0   | 17 new (+20 cached), parallel| -       | -
    #    1   | 1                            | 'Paris' | 0.9997
    #    2   | 1                            | '.'     | 0.99
    #    3   | 1                            | <end>   | (not reported) -> stop
    #
    #   Reading the prompt = ONCE, in parallel.  Writing = ONE token per turn, in order.
    #   Stopping is just another token the model picks.
    #   (01b_inside_the_llm.py runs these same turns as separate calls, so you can watch each one.)
    resp.raise_for_status()
    r = resp.json()
    # -> the WHOLE response (real run, numbers rounded):
    # {
    #   "model": "llama3.2",
    #   "created_at": "2026-10-31T11:43:16.765081Z",
    #   "message": {"role": "assistant", "content": "Paris."},     <- the answer text
    #                                                                  (OpenAI: choices[0].message.content, Anthropic: content[0].text)
    #   "done": true,
    #   "done_reason": "stop",                                      <- model chose to stop ("length" = hit num_predict)
    #                                                                  (OpenAI: finish_reason "stop"/"length",
    #                                                                   Anthropic: stop_reason "end_turn"/"max_tokens")
    #   "logprobs": [                                               <- one entry per token it wrote
    #     {"token": "Paris", "logprob": -0.0003, "bytes": [80, 97, 114, 105, 115],
    #      "top_logprobs": [                                        <- the 5 best choices at that step
    #        {"token": "Paris",  "logprob": -0.0003, "bytes": [80, 97, 114, 105, 115]},
    #        {"token": "Par",    "logprob": -8.3978, "bytes": [80, 97, 114]},
    #        {"token": " Paris", "logprob": -9.9889, "bytes": [32, 80, 97, 114, 105, 115]},
    #        {"token": " paris", "logprob": -11.3931, "bytes": [32, 112, 97, 114, 105, 115]},
    #        {"token": "France", "logprob": -11.4433, "bytes": [70, 114, 97, 110, 99, 101]}]},
    #     {"token": ".", "logprob": -0.0056, "bytes": [46],
    #      "top_logprobs": [
    #        {"token": ".", "logprob": -0.0056, "bytes": [46]},
    #        {"token": "",  "logprob": -5.1833},
    #        {"token": "!", "logprob": -12.5340, "bytes": [33]},
    #        {"token": ",", "logprob": -13.2515, "bytes": [44]},
    #        {"token": "",  "logprob": -14.4763}]}
    #   ],
    #   "total_duration": 357036100,                                <- all times are in nanoseconds (0.36 s)
    #   "load_duration": 9208900,                                   <- loading the model into memory
    #   "prompt_eval_count": 37,                                    <- tokens IN (your prompt + chat template)
    #                                                                  (OpenAI: usage.prompt_tokens, Anthropic: usage.input_tokens)
    #   "prompt_eval_cached_count": 20,                             <- of those, reused from the last call
    #                                                                  (OpenAI: usage.prompt_tokens_details.cached_tokens,
    #                                                                   Anthropic: usage.cache_read_input_tokens)
    #   "prompt_eval_duration": 201598000,
    #   "eval_count": 3,                                            <- tokens OUT
    #                                                                  (OpenAI: usage.completion_tokens, Anthropic: usage.output_tokens)
    #   "eval_duration": 140305000
    # }
    # logprob -> probability: math.exp(logprob).  -0.0003 -> 1.00,  -8.40 -> 0.0002

    print("STEP 1: the answer")
    print("  ", repr(r["message"]["content"]))   # -> 'Paris.'

    print("\nSTEP 2: for each token the model wrote, the choices it had")
    for i, tok in enumerate(r.get("logprobs", []), 1):
        choices = ", ".join(f"{c['token']!r} {math.exp(c['logprob']):.2f}"
                            for c in tok.get("top_logprobs", []))
        print(f"  token {i}: picked {tok['token']!r:<12} choices: {choices}")
        # -> token 1: picked 'Paris'      choices: 'Paris' 1.00, 'Par' 0.00, ' Paris' 0.00, ' paris' 0.00, 'France' 0.00
        # -> token 2: picked '.'          choices: '.' 0.99, '' 0.01, '!' 0.00, ',' 0.00, '' 0.00
    if not r.get("logprobs"):
        print("  (your Ollama version has no logprobs -- update Ollama to see this part)")

    print("\nSTEP 3: what this means")
    print("  - Each line above = ONE run of the model. It never plans the whole sentence.")
    print("  - Tokens are pieces like ' Paris' (space included), not always whole words.")
    print(f"  - It wrote {r['eval_count']} tokens, so the model ran {r['eval_count']} times.")
    # -> It wrote 3 tokens, so the model ran 3 times.   (3 = 'Paris' + '.' + a hidden "end" token)


if __name__ == "__main__":
    main()

# Try: change the prompt to "My favourite colour is" -- the choices are much more spread out.
