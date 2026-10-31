"""05 -- Context window: the model's short-term memory has a size limit
=======================================================================

CONCEPT IN ONE LINE:
  The model can only see N tokens at once (the context window). Anything that does
  not fit is CUT OFF -- usually the oldest part -- and the model never sees it.
                                                               (details: simple/04)

   context window = num_ctx tokens (Ollama default is a few thousand; big models: 128k+)
   ┌───────────────────────────────── num_ctx ─────────────────────────────────┐
   │ system │ old history ......................... │ recent │ question │answer│
   └───────────────────────────────────────────────────────────────────────────┘
        ▲ too much text? the OLDEST tokens fall out first ──▶ "the model forgot"

  WHAT YOUR APP DOES ABOUT IT (pick one):
   1. TRIM       keep system prompt + the last few messages
   2. SUMMARIZE  replace old messages with a short summary (made by the model)
   3. RAG        don't send everything; fetch only the relevant parts (lessons 14-15)
"""

from ollama_client import ask, chat

FACT = "IMPORTANT: the customer's secret order code is 4417."
FILLER = "The customer talked about the weather, the traffic and lunch plans. " * 40


def ask_code(num_ctx):
    """Fact at the START, lots of text after it, question at the END."""
    messages = [{"role": "user", "content": FACT + "\n" + FILLER},
                {"role": "assistant", "content": "Noted."},
                {"role": "user", "content": "What is the customer's secret order code? Number only."}]
    r = chat(messages, options={"temperature": 0, "num_ctx": num_ctx, "num_predict": 10})
    return r["prompt_eval_count"], r["message"]["content"].strip()


def main():
    print("STEP 1: the same conversation with a BIG and a SMALL context window")
    for num_ctx in (4096, 256):
        used, answer = ask_code(num_ctx)
        print(f"  num_ctx={num_ctx:<5} tokens the model actually saw: {used:<5} answer: {answer!r}")
    print("  -> with 256 the start (where the code was) was cut off, so the model can't know it.")

    print("\nSTEP 2: fix it by SUMMARIZING the old part into a few tokens")
    summary = ask("Summarize this in one short sentence, keep any numbers:\n" + FACT + "\n" + FILLER,
                  options={"temperature": 0, "num_predict": 40})
    print(f"  summary: {summary!r}")
    messages = [{"role": "system", "content": "Earlier conversation summary: " + summary},
                {"role": "user", "content": "What is the customer's secret order code? Number only."}]
    r = chat(messages, options={"temperature": 0, "num_ctx": 256, "num_predict": 10})
    print(f"  num_ctx=256 with summary -> tokens: {r['prompt_eval_count']}, "
          f"answer: {r['message']['content'].strip()!r}")

    print("\nREMEMBER:")
    print("  - Count tokens before you send (prompt_eval_count tells you after).")
    print("  - Put the most important facts near the question, not far away at the start.")
    print("  - Bigger num_ctx = more memory (RAM) and slower. It is a trade-off.")


if __name__ == "__main__":
    main()

# Try: num_ctx=1024 -- find the size where the model starts to remember the code again.
