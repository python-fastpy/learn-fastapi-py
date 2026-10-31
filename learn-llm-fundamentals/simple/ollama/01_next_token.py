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
    }
    resp = httpx.post(OLLAMA + "/api/chat", json=body, timeout=300)   # json= sends body as JSON
    resp.raise_for_status()
    r = resp.json()

    print("STEP 1: the answer")
    print("  ", repr(r["message"]["content"]))

    print("\nSTEP 2: for each token the model wrote, the choices it had")
    for i, tok in enumerate(r.get("logprobs", []), 1):
        choices = ", ".join(f"{c['token']!r} {math.exp(c['logprob']):.2f}"
                            for c in tok.get("top_logprobs", []))
        print(f"  token {i}: picked {tok['token']!r:<12} choices: {choices}")
    if not r.get("logprobs"):
        print("  (your Ollama version has no logprobs -- update Ollama to see this part)")

    print("\nSTEP 3: what this means")
    print("  - Each line above = ONE run of the model. It never plans the whole sentence.")
    print("  - Tokens are pieces like ' Paris' (space included), not always whole words.")
    print(f"  - It wrote {r['eval_count']} tokens, so the model ran {r['eval_count']} times.")


if __name__ == "__main__":
    main()

# Try: change the prompt to "My favourite colour is" -- the choices are much more spread out.
