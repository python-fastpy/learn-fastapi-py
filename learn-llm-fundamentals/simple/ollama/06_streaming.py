"""05 -- Streaming: show words as soon as they are ready
========================================================

CONCEPT IN ONE LINE:
  The model writes one token at a time, so you can SHOW each token right away
  instead of waiting for the whole answer.                  (details: simple/06)

   WITHOUT streaming                         WITH streaming
   ─────────────────                         ──────────────
   user waits ......... 4 s ........ text    user sees words after ~0.3 s, then more and more

   Ollama sends one JSON line per token:
     {"message": {"content": "An"},  "done": false}
     {"message": {"content": " API"}, "done": false}
     ...
     {"done": true, "eval_count": 57, ...}      ◀ last line has the token counts

  In FastAPI you forward these pieces with StreamingResponse (see 19_fastapi_app.py).
"""

import json
import time
import urllib.request

from ollama_client import CHAT_MODEL, OLLAMA


def stream_chat(question):
    body = {"model": CHAT_MODEL, "stream": True, "options": {"temperature": 0},
            "messages": [{"role": "user", "content": question}]}
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    start, first = time.time(), None
    with urllib.request.urlopen(req) as resp:
        for line in resp:                            # one JSON object per line
            part = json.loads(line)
            if first is None:
                first = time.time() - start          # time to first token (TTFT)
            print(part["message"]["content"], end="", flush=True)
            if part["done"]:
                total = time.time() - start
                print(f"\n\n  first token after {first:.2f} s, full answer after {total:.2f} s, "
                      f"{part['eval_count']} tokens")


def main():
    print("STEP 1: watch the answer appear token by token\n")
    stream_chat("Explain what an API is, in 4 short sentences.")
    print("\nSTEP 2: why it matters")
    print("  Users judge speed by the FIRST word, not the last one.")
    print("  Streaming does not make the model faster -- it makes the app FEEL faster.")


if __name__ == "__main__":
    main()
