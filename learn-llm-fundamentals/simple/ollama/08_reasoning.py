"""08 -- Reasoning: let the model "think" before it answers
==========================================================

CONCEPT IN ONE LINE:
  The model writes one token at a time and can't think silently. If it writes its
  steps first, the final answer is built on those steps -- so it is often more correct.
                                                               (details: simple/13)

   DIRECT                                   STEP BY STEP (chain of thought)
   question ──▶ "12"  (a guess)             question ──▶ "3 boxes x 4 = 12 apples,
                                                          minus 5 eaten = 7,
                                                          plus 2 bought = 9" ──▶ "9"

  THINKING MODELS (qwen3, deepseek-r1, gpt-oss) are trained to do this by themselves.
  Ollama returns the steps in message.thinking and the answer in message.content.
  COST: thinking tokens are output tokens -- you pay for them and wait for them.
"""

import json
import urllib.request

from ollama_client import OLLAMA, ask, post

PROBLEM = ("A shop has 3 boxes with 4 apples each. A customer eats 5 apples, "
           "then the shop buys 2 more apples. How many apples does the shop have now?")
THINKING_MODEL = "qwen3:1.7b"        # small thinking model, ~1.4 GB:  ollama pull qwen3:1.7b


def main():
    print(f"PROBLEM: {PROBLEM}   (correct answer: 9)\n")

    print("STEP 1: answer directly (no room to think)")
    print("  ", ask(PROBLEM + " Reply with the number only.", options={"temperature": 0, "num_predict": 5}))

    print("\nSTEP 2: ask for the steps first (chain of thought)")
    print("  ", ask(PROBLEM + " Think step by step, then give the final answer on the last line.",
                    options={"temperature": 0, "num_predict": 200}).replace("\n", "\n   "))

    print(f"\nSTEP 3: a real thinking model ({THINKING_MODEL})")
    with urllib.request.urlopen(OLLAMA + "/api/tags") as r:
        installed = [m["name"] for m in json.loads(r.read())["models"]]
    if THINKING_MODEL not in installed:
        print(f"   not installed -- to try it:  ollama pull {THINKING_MODEL}")
        return
    r = post("/api/chat", {"model": THINKING_MODEL, "think": True, "stream": False,
                           "messages": [{"role": "user", "content": PROBLEM}],
                           "options": {"temperature": 0}})
    thinking = r["message"].get("thinking", "")
    print(f"   thinking ({len(thinking)} chars): {thinking[:300]!r}...")
    print(f"   answer: {r['message']['content'].strip()}")
    print(f"   output tokens: {r['eval_count']}  <- the thinking is included, so it costs more")


if __name__ == "__main__":
    main()

# Remember: use step-by-step / thinking for maths, logic, planning. Skip it for simple
# lookups -- it only adds cost and delay there.
