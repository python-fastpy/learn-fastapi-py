"""02 -- Tokens: what you pay for and what fills the context window
===================================================================

CONCEPT IN ONE LINE:
  Every limit and every bill is counted in TOKENS, not characters or words.
                                                    (details: simple/01b, simple/01b_extra)

WHAT WE DO:
  Send the same short message in different forms and read the REAL token count
  the model used (prompt_eval_count in Ollama = input_tokens in paid APIs).

   your text ──▶ tokenizer ──▶ [ids] ──▶ model
                    │
                    └─▶ prompt_eval_count = how many tokens went IN
                        eval_count        = how many tokens came OUT

  NOTE: every chat message also gets hidden "template" tokens (role markers),
  so even a 1-word message costs ~25-30 tokens. We subtract that baseline.
"""

from ollama_client import chat

PRICE_PER_1M = 3.00          # example paid-API price per 1M input tokens


def count_tokens(text):
    """Input tokens for one user message (num_predict=1: we only want the count)."""
    r = chat([{"role": "user", "content": text}], options={"num_predict": 1})
    return r["prompt_eval_count"]


def main():
    base = count_tokens("")
    print(f"STEP 1: an EMPTY message already costs {base} tokens (the chat template)\n")

    print("STEP 2: same meaning, different token counts")
    samples = [
        ("English", "Where is my refund for order 1234?"),
        ("Hindi", "ऑर्डर 1234 का मेरा रिफंड कहाँ है?"),
        ("JSON", '{"question": "where is my refund", "order_id": 1234}'),
        ("typo", "Wher iz my refnd for ordr 1234?"),
        ("number", "1234567890123456789"),
    ]
    print(f"  {'kind':<9}{'chars':>6}{'tokens':>8}   text")
    for kind, text in samples:
        n = count_tokens(text) - base
        print(f"  {kind:<9}{len(text):>6}{n:>8}   {text}")

    print("\nSTEP 3: why an engineer cares")
    n = count_tokens(samples[0][1])
    daily = n * 100_000
    print(f"  one English question = {n} tokens (with template)")
    print(f"  100,000 questions/day = {daily:,} tokens = ${daily * PRICE_PER_1M / 1e6:.2f}/day")
    print("  The context window (e.g. 128k tokens) is filled by: system prompt + docs +")
    print("  history + question + answer. Long history -> old messages must be dropped.")


if __name__ == "__main__":
    main()

# Try: paste a long paragraph and compare chars / tokens. English is ~4 chars per token.
