r"""11 -- STOP: every way the loop ends
=====================================

CONCEPT IN ONE LINE:
  The loop (10) has no idea what "finished" means. It ends when the MODEL picks a special
  <end> token -- or when a RULE outside the model cuts it off.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── 12 response ◀── [11 stop?] ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax

  CONTEXT HERE: a FULL context is NOT a stop reason in Ollama -- old tokens are dropped
  and it keeps going (check (5) below). Map of the context in all steps: 00_the_journey.py.

WHAT HAPPENS -- after EVERY picked token the server checks, in effect:

   picked token
        │
        ├─ is it an end token (<|eot_id|>)?              -> STOP   done_reason "stop"    (1)
        ├─ does the text now contain a stop string?      -> STOP   done_reason "stop"    (2)(4)
        ├─ reached num_predict tokens?                   -> STOP   done_reason "length"  (3)
        ├─ context window full?                          -> make room, CONTINUE           (5)
        ├─ did the client hang up?                       -> STOP   (nobody to send to)    (6)
        └─ otherwise                                     -> back to 10 loop, next token

THE 6 WAYS, ONE BY ONE:

  (1) THE MODEL PICKS ITS END TOKEN -- the normal, "natural" stop
      The end token is just another vocabulary entry with an ID. 01b STEP 3 run 2 showed it competing:
          '.'      0.6717
          <end>    0.3278     <- shown as '' -- the end token has no visible text
      Here it is, from the GGUF file (PART 1):
          tokenizer.ggml.eos_token_id = 128009  ->  <|eot_id|>   "end of turn"
      The special tokens (token_type 3 in the GGUF), minus 248 unused "reserved" slots:
          128000  <|begin_of_text|>          put at the very start of every input
          128001  <|end_of_text|>            end of a whole document (base-model training)
          128004  <|finetune_right_pad_id|>  padding used during fine-tuning
          128006  <|start_header_id|>        \  wrap a role name:
          128007  <|end_header_id|>          /  <|start_header_id|>user<|end_header_id|>
          128008  <|eom_id|>                 "end of message" -- pause for a tool result
          128009  <|eot_id|>                 "end of turn" -- the assistant is done   <- STOP
          128010  <|python_tag|>             starts a built-in tool call (code)

  (2) OLLAMA'S STOP LIST -- a safety net from the model's Modelfile (PART 2):
          /api/show "parameters":   stop "<|start_header_id|>"
                                    stop "<|end_header_id|>"
                                    stop "<|eot_id|>"
      If the model ever starts writing a NEW turn header instead of ending, Ollama cuts it.

  (3) num_predict -- a hard limit on output tokens (PART 4)
          num_predict 4  ->  'Here is the count'   done_reason "length"
      Cut mid-sentence: the model was NOT finished. (01b uses num_predict 1 on purpose.)
      Other APIs call this max_tokens / max_new_tokens.

  (4) YOUR OWN STOP STRINGS -- options "stop": ["5"] (PART 5)
          stop ["5"]  ->  'Here is the count from 1 to 10, separated by commas:\n\n1, 2, 3, 4, '
                          done_reason "stop"
      The stop string itself is NOT included. Note: done_reason is "stop" for both (1) and
      (4) -- Ollama doesn't tell you which one happened.

  (5) CONTEXT WINDOW FULL -- doesn't stop on its own in Ollama: old tokens are dropped
      ("context shift") and generation continues until (1)-(4) happen. See 10 loop PART 4.

  (6) THE CLIENT DISCONNECTS -- you close the stream early (PART 6). The server notices and
      stops computing. You never receive the final "done": true chunk with the stats.

HOW DID THE MODEL LEARN TO STOP?
   Nobody programmed "stop after answering". During fine-tuning (Meta, "Instruct" version) it
   saw huge numbers of chat examples where every assistant reply ENDS with <|eot_id|>:
      <|start_header_id|>assistant<|end_header_id|>\n\nParis.<|eot_id|>
   So after a complete answer, <|eot_id|> becomes a likely next token -- and it gets picked
   (08) like any other token. That's why it is a probability (0.33 after 'Paris'), not a rule.
   A base model (no chat fine-tuning) would happily keep writing.

WHERE THIS COMES FROM:
   end token ID 128009      GGUF tokenizer.ggml.eos_token_id (Meta's tokenizer)
   special token list       GGUF tokenizer.ggml.tokens + token_type 3
   knowing WHEN to end      the weights (Meta's fine-tuning)
   stop list                Ollama's Modelfile for llama3.2 (/api/show "parameters")
   num_predict, stop        YOU (your request "options")
   done_reason              Ollama's server, in the last response chunk (12)

IS IT OLLAMA-SPECIFIC?
   who                 end token              limit             stop strings     "why did it end"
   the model itself    <|eot_id|> 128009      --                --               -- (just a token)
   Ollama              eos + Modelfile stop   num_predict       options "stop"   done_reason:
                                                                                 stop / length
   OpenAI              (hidden)               max_tokens /      "stop"           finish_reason:
                                              max_completion_                    stop / length /
                                              tokens (hedged)                    tool_calls /
                                                                                 content_filter
   Anthropic           (hidden)               max_tokens        stop_sequences   stop_reason:
                                              (required)                         end_turn /
                                                                                 max_tokens /
                                                                                 stop_sequence /
                                                                                 tool_use /
                                                                                 pause_turn /
                                                                                 refusal
                                                                                 (hedged -- newer
                                                                                 values may exist,
                                                                                 see the docs)
   Hugging Face        eos_token_id in        max_new_tokens    stop_strings     you check the
                       generation_config                        (newer versions, output yourself
                                                                hedged)
   Different models have different end tokens (GPT-2: <|endoftext|>, others: </s>) -- the
   API hides that and gives you one word: stop / end_turn / length.

COMMON CONFUSIONS:
   - "done_reason: length" = the answer is CUT, not complete -> raise num_predict.
   - "done": true appears on EVERY final chunk -- read done_reason to know WHY.
   - Stop strings match TEXT, not tokens, and are checked as the text grows.
"""

import json
import math
import sys

import httpx

from gguf_reader import read_gguf

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def chat_prompt(text):
    return ("<|start_header_id|>user<|end_header_id|>\n\n" + text + "<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n")


def generate(prompt, top_logprobs=0, **options):
    body = {"model": CHAT_MODEL, "prompt": prompt, "raw": True, "stream": False,
            "logprobs": top_logprobs > 0, "top_logprobs": top_logprobs, "options": options}
    resp = httpx.post(OLLAMA + "/api/generate", json=body, timeout=300)
    resp.raise_for_status()
    return resp.json()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    count = chat_prompt("Count from 1 to 10, separated by commas.")

    print("PART 1: the end token, read from llama3.2's GGUF file")
    meta, _, _ = read_gguf()
    tokens, types = meta["tokenizer.ggml.tokens"], meta["tokenizer.ggml.token_type"]
    print("   bos_token_id", meta["tokenizer.ggml.bos_token_id"],
          "| eos_token_id", meta["tokenizer.ggml.eos_token_id"], "=", tokens[meta["tokenizer.ggml.eos_token_id"]])
    special = [(i, t) for i, (t, ty) in enumerate(zip(tokens, types)) if ty == 3]
    named = [(i, t) for i, t in special if "reserved" not in t]
    print(f"   {len(special)} special tokens, {len(special) - len(named)} of them 'reserved' (unused):")
    for i, t in named:
        print(f"      {i}  {t}")
    # ->    bos_token_id 128000 | eos_token_id 128009 = <|eot_id|>
    #       256 special tokens, 248 of them 'reserved' (unused):
    #          128000  <|begin_of_text|>
    #          128001  <|end_of_text|>
    #          128004  <|finetune_right_pad_id|>
    #          128006  <|start_header_id|>
    #          128007  <|end_header_id|>
    #          128008  <|eom_id|>
    #          128009  <|eot_id|>
    #          128010  <|python_tag|>

    print("\nPART 2: Ollama's stop list for this model (/api/show 'parameters')")
    show = httpx.post(OLLAMA + "/api/show", json={"model": CHAT_MODEL}, timeout=60).json()
    for line in show.get("parameters", "").splitlines():
        print("  ", " ".join(line.split()))
    # ->    stop "<|start_header_id|>"
    #       stop "<|end_header_id|>"
    #       stop "<|eot_id|>"

    print("\n(1) the model picks <end> -- 01b's prompt after 'Paris'")
    p = chat_prompt("Complete the sentence with one word: The capital of France is") + "Paris"
    r = generate(p, top_logprobs=3, temperature=0, num_predict=1)
    for t in r["logprobs"][0]["top_logprobs"]:
        print(f"   {t['token'] or '<end>'!r:10} {math.exp(t['logprob']):.4f}")
    r = generate(count, temperature=0)
    print("   natural end:", repr(r["response"][-12:]), "| done_reason", r["done_reason"],
          "| eval_count", r["eval_count"])
    # ->    '.'        0.7014
    #       '<end>'    0.2982
    #       '!'        0.0004
    #       (wobbles run to run: 01b STEP 3 got 0.6717 / 0.3278 -- CPU maths noise)
    #       natural end: ' 7, 8, 9, 10' | done_reason stop | eval_count 44

    print("\n(3) num_predict 4 -- cut off by the limit")
    r = generate(count, temperature=0, num_predict=4)
    print("  ", repr(r["response"]), "| done_reason", r["done_reason"], "| eval_count", r["eval_count"])
    # ->    'Here is the count' | done_reason length | eval_count 4

    print("\n(4) your own stop string: stop ['5']")
    r = generate(count, temperature=0, stop=["5"])
    print("  ", repr(r["response"]), "| done_reason", r["done_reason"])
    # ->    'Here is the count from 1 to 10, separated by commas:\n\n1, 2, 3, 4, ' | done_reason stop
    #       ('5' itself is not in the text)

    print("\n(6) the client hangs up after 5 tokens")
    body = {"model": CHAT_MODEL, "prompt": count, "raw": True, "stream": True, "options": {"temperature": 0}}
    received = []
    with httpx.stream("POST", OLLAMA + "/api/generate", json=body, timeout=300) as resp:
        for line in resp.iter_lines():
            chunk = json.loads(line)
            received.append(chunk["response"])
            if len(received) == 5:
                break                                        # leaving 'with' closes the connection
    print("   got", repr("".join(received)), "-- no final chunk, no done_reason, no stats")
    # ->    got 'Here is the count from' -- no final chunk, no done_reason, no stats


if __name__ == "__main__":
    main()

# Try: stop ["\n"] on a question with a multi-line answer -- you get only the first line.
#      Then num_predict 1000 on "Write a long story" and compare eval_count with done_reason.
