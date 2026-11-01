r"""12 -- RESPONSE: what you actually get back, and every number in it
=====================================================================

CONCEPT IN ONE LINE:
  The answer comes back as JSON -- either ONE object at the end (stream: false) or one small
  object PER TOKEN as it's generated (stream: true) -- plus stats that tell you exactly
  how many tokens went in, came out, and how long each step took.

WHERE YOU ARE IN THE JOURNEY:

     you type ─▶ 01 request ─▶ 02 template ─▶ 03 tokens ─▶ 04 vectors ─▶ 05 layers ─▶ 06 scores
                                                                                          │
     you see ◀── [12 response] ◀── 11 stop? ◀── 10 loop ◀── 09 detokenize ◀── 08 pick ◀── 07 softmax

WHAT HAPPENS:

   Inside, the model produced token IDs one at a time (08-10) and Ollama turned each into
   text (09). This step is just DELIVERY -- how that text reaches your program.

   stream: false  ->  wait, then ONE JSON                  stream: true  ->  one JSON line PER TOKEN
   ──────────────────────────────────────                  ─────────────────────────────────────────
   {                                                       {"message":{"content":"Blue"},  "done":false}
     "message": {"role": "assistant",                      {"message":{"content":","},     "done":false}
                 "content": "Blue, green, yellow"},        {"message":{"content":" green"},"done":false}
     "done": true,                                         {"message":{"content":","},     "done":false}
     "done_reason": "stop",                                {"message":{"content":" yellow"},"done":false}
     "total_duration": 319995400,                          {"message":{"content":""},      "done":true,
     "load_duration": 6550100,                               "done_reason":"stop",
     "prompt_eval_count": 33,                                + the same 7 stats fields as on the left}
     "prompt_eval_cached_count": 20,
     "prompt_eval_duration": 111707000,                    (only the LAST line carries the stats)
     "eval_count": 6,
     "eval_duration": 198481000
   }

   Streaming format = NDJSON ("newline-delimited JSON", content-type application/x-ndjson):
   each line is a complete JSON object. Read line by line, append "content", stop at done:true.
   Chunks arrived ~40 ms apart here = the time for ONE trip through all 28 layers (05).

   THE FINAL OBJECT (real, from main() below, /api/chat):
   {
     "model": "llama3.2",
     "created_at": "2026-11-01T07:00:47.3494031Z",   <- when this chunk was made (UTC)
     "message": {"role": "assistant",                 <- /api/chat: a message, ready to append
                 "content": ""},                         to your history for the next turn
     "done": true,                                    <- last object
     "done_reason": "stop",                           <- WHY it ended (11_stop.py):
                                                         "stop"   = model picked <|eot_id|>
                                                                    or a stop string matched
                                                         "length" = hit num_predict / limit
     "total_duration":       319995400,               <- ALL durations are NANOSECONDS
     "load_duration":          6550100,                  (1 s = 1,000,000,000 ns)
     "prompt_eval_count":           33,
     "prompt_eval_cached_count":    20,
     "prompt_eval_duration": 111707000,
     "eval_count":                   6,
     "eval_duration":        198481000
   }

   EVERY STATS FIELD:
     field                     unit     meaning                                    see
     total_duration            ns       whole request inside Ollama                -
     load_duration             ns       loading the model file into memory         01_request
     prompt_eval_count         tokens   tokens IN: template + your messages        02, 03
     prompt_eval_cached_count  tokens   of those, reused from the KV cache         10_loop
     prompt_eval_duration      ns       time to process the tokens IN              05
     eval_count                tokens   tokens OUT (including the <|eot_id|>)      08-11
     eval_duration             ns       time to generate the tokens OUT            10_loop

   NUMBERS YOU CAN WORK OUT (from the object above):
     output speed      eval_count / eval_duration     = 6 / 0.198 s      ≈ 30 tokens/s
     per token         eval_duration / eval_count     = 0.198 s / 6      ≈ 33 ms
     tokens actually   prompt_eval_count - cached     = 33 - 20          = 13 new tokens
       processed in
     other             total - load - prompt - eval   = 0.320 - 0.007 - 0.112 - 0.198
                                                      ≈ 0.003 s  (templating, tokenizing,
                                                                  bookkeeping)

   WHY eval_count = 6 BUT ONLY 5 TEXT CHUNKS?
     "Blue" "," " green" "," " yellow" = 5 visible tokens, then the model picked <|eot_id|>
     (the 6th). It's counted and costs time, but it's never shown -- the last chunk's
     content is "" (11_stop.py).

   /api/generate vs /api/chat -- same model, different envelope:
     /api/chat       "message": {"role": "assistant", "content": "Hello."}
     /api/generate   "response": "Hello."
                     + (non-raw, non-stream) "context": the token IDs of the whole exchange
                       (32 IDs here, all listed in STEP 4 below); old way to continue a chat,
                       now deprecated

WHERE THIS COMES FROM:
   - the TEXT                -> the model's picked token IDs, turned back into text (09)
   - done_reason             -> Ollama: did the model pick its end token, or did a limit hit?
   - counts + durations      -> Ollama's runner measures them while it works
   - the JSON / NDJSON shape -> Ollama's API design (other providers use other shapes)

IS IT OLLAMA-SPECIFIC?
   The STATS IDEAS are universal (tokens in / out, why it stopped). The NAMES and the
   envelope are not. Field names below are hedged -- check each provider's docs.

   meaning           Ollama /api/chat         OpenAI chat completions        Anthropic messages
   the text          message.content          choices[0].message.content     content[0].text
   why it stopped    done_reason              choices[0].finish_reason       stop_reason
                     "stop" / "length"        "stop" / "length" /            "end_turn" / "max_tokens"
                                              "tool_calls" /                 / "stop_sequence" /
                                              "content_filter"               "tool_use" / "pause_turn"
                                                                             / "refusal"
                                              (both hedged -- newer values may exist, see the docs)
   tokens in         prompt_eval_count        usage.prompt_tokens            usage.input_tokens
   tokens out        eval_count               usage.completion_tokens        usage.output_tokens
   timings           yes, in ns               no                             no
   streaming format  NDJSON lines             Server-Sent Events             Server-Sent Events
                                              ("data: {json}" lines)         (typed events)
   Hugging Face transformers: model.generate() returns token IDs; you call
   tokenizer.decode() yourself and count/measure everything yourself.

COMMON CONFUSIONS:
   - "Streaming is faster."  The total time is about the same -- you just see the FIRST
     token sooner (time to first token), which FEELS much faster in a chat app.
   - "Durations are milliseconds."  They're NANOSECONDS. 319995400 = 0.32 s.
   - "One chunk = one word."  One chunk = one TOKEN: "," and " green" are separate chunks.
   - "prompt_eval_count = my message length."  It includes the whole template (02) and the
     whole conversation history, every call.
   - "Billing tokens = what I see."  Hidden tokens count too: the template, and the end token.
"""

import json
import time

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"


def main():
    messages = [{"role": "user", "content": "Name 3 colours, comma separated."}]

    print("STEP 1: stream: false -- one JSON object at the end")
    r = httpx.post(OLLAMA + "/api/chat", json={
        "model": CHAT_MODEL, "messages": messages, "stream": False,
        "options": {"temperature": 0},
    }, timeout=300).json()
    print(json.dumps(r, indent=2))
    # -> {
    #      "model": "llama3.2",
    #      "created_at": "2026-11-01T07:01:49.5162383Z",
    #      "message": {"role": "assistant", "content": "Blue, green, yellow"},
    #      "done": true,
    #      "done_reason": "stop",
    #      "total_duration": 4498680600,      <- 4.5 s in total, and
    #      "load_duration": 3925580900,       <- 3.9 s of that was loading: model wasn't in memory
    #      "prompt_eval_count": 33,
    #      "prompt_eval_cached_count": 0,     <- nothing cached after a fresh load
    #      "prompt_eval_duration": 331440000,
    #      "eval_count": 6,
    #      "eval_duration": 235645000
    #    }

    print("\nSTEP 2: stream: true -- one NDJSON line per token, with arrival times")
    text = ""
    t0 = time.perf_counter()
    first = None
    with httpx.stream("POST", OLLAMA + "/api/chat", json={
        "model": CHAT_MODEL, "messages": messages, "stream": True,
        "options": {"temperature": 0},
    }, timeout=300) as resp:
        print("content-type:", resp.headers.get("content-type"))
        for line in resp.iter_lines():
            chunk = json.loads(line)                     # each line = one complete JSON object
            now = time.perf_counter() - t0
            first = first or now
            piece = chunk["message"]["content"]
            text += piece
            print(f"   +{now:6.3f} s  {piece!r:10}  done={chunk['done']}")
            if chunk["done"]:
                final = chunk
    # -> content-type: application/x-ndjson
    #       + 2.605 s  'Blue'      done=False      <- ~2.5 s of this is the Windows "localhost"
    #       + 2.644 s  ','         done=False         delay (01_request.py), not the model
    #       + 2.685 s  ' green'    done=False
    #       + 2.726 s  ','         done=False      <- ~40 ms between tokens = one pass
    #       + 2.770 s  ' yellow'   done=False         through all 28 layers
    #       + 2.811 s  ''          done=True       <- the <|eot_id|>: counted, never shown

    print(f"\nassembled text: {text!r}   time to first token: {first:.3f} s")
    # -> assembled text: 'Blue, green, yellow'   time to first token: 2.605 s

    print("\nSTEP 3: the stats on the last chunk, worked out")
    ns = 1e9
    print(f"   tokens in : {final['prompt_eval_count']}"
          f"  (cached {final.get('prompt_eval_cached_count', 0)})")
    print(f"   tokens out: {final['eval_count']}")
    print(f"   load      : {final['load_duration'] / ns:.3f} s")
    print(f"   prompt    : {final['prompt_eval_duration'] / ns:.3f} s")
    print(f"   generate  : {final['eval_duration'] / ns:.3f} s"
          f"  = {final['eval_count'] / (final['eval_duration'] / ns):.1f} tokens/s")
    print(f"   total     : {final['total_duration'] / ns:.3f} s")
    # -> tokens in : 33  (cached 32)
    #    tokens out: 6
    #    load      : 0.005 s
    #    prompt    : 0.048 s
    #    generate  : 0.209 s  = 28.7 tokens/s
    #    total     : 0.265 s
    #    (cached 32: STEP 1 sent the same prompt a moment ago -- 10_loop.py explains the cache)

    print("\nSTEP 4: /api/generate -- same model, different envelope")
    g = httpx.post(OLLAMA + "/api/generate", json={
        "model": CHAT_MODEL, "prompt": "Say hi in one word.", "stream": False,
        "options": {"temperature": 0},
    }, timeout=300).json()
    print("   keys:", list(g))
    print("   response:", repr(g["response"]))
    if "context" in g:
        print(f"   context: {len(g['context'])} token IDs = {g['context']}")
    # -> keys: ['model', 'created_at', 'response', 'done', 'done_reason', 'context',
    #           'total_duration', 'load_duration', 'prompt_eval_count', 'prompt_eval_cached_count',
    #           'prompt_eval_duration', 'eval_count', 'eval_duration']
    #    response: 'Hello.'
    #    context: 32 token IDs = [128006, 9125, 128007, 271, 38766, 1303, 33025, 2696, 25, 6790,
    #             220, 2366, 18, 271, 128009, 128006, 882, 128007, 271, 46864, 15960, 304, 832,
    #             3492, 13, 128009, 128006, 78191, 128007, 271, 9906, 13]
    #    the same 32 IDs as tokens (looked up in the vocabulary, 03_tokens.py):
    #       <|start_header_id|> system <|end_header_id|> \n\n
    #       Cut ting " Knowledge" " Date" : " December" " " 202 3 \n\n <|eot_id|>
    #       <|start_header_id|> user <|end_header_id|> \n\n
    #       Say " hi" " in" " one" " word" . <|eot_id|>
    #       <|start_header_id|> assistant <|end_header_id|> \n\n
    #       Hello .
    #    = the templated prompt + the answer, as IDs


if __name__ == "__main__":
    main()

# Try: set "options": {"num_predict": 3} -- done_reason becomes "length" and eval_count is 3.
