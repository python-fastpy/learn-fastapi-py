"""13 -- Reasoning and structured output  (simple version)
=========================================================

IN ONE LINE:
  Reasoning models "think" in hidden words before they answer (you pay for them).
  Structured output forces the answer into YOUR JSON shape.

REAL USE CASE:
  Your FastAPI endpoint asks the model to read a support ticket and return
  JSON that your code can save to a database:

     ticket text
          │
          ▼
     ┌───────────────────┐   hidden thinking  (billed as output tokens)
     │      MODEL        │ ─────────────────▶ ...
     └───────────────────┘   visible answer
          │                  {"category": "bug", "priority": 2}
          ▼
     json.loads ──▶ schema check ──▶ value check ──▶ save to DB
        (parses?)    (right keys?)    (makes sense?)

WHAT AN ENGINEER MUST KNOW:
  1. Thinking tokens are output tokens: more cost, more waiting. Use a
     reasoning model only for hard, multi-step tasks.
  2. "Please return JSON" in the prompt is only a request. It can break.
  3. Schema-constrained decoding is a guarantee: the model can only pick
     tokens that keep the JSON valid.
  4. Even valid JSON can have wrong VALUES. Always check them in code.
  5. Images also become tokens. Big images = many tokens. Resize and crop.

Run:  uv run python simple/13_reasoning_and_structured_output.py
"""

import json

PRICE_PER_1M_OUTPUT = 15.00     # example price in dollars


# ----------------------------------------------------------------------------
# STEP 1: THINKING COSTS MONEY (thinking + answer are both output tokens)
# ----------------------------------------------------------------------------
def cost_of_call(thinking_tokens, answer_tokens):
    total = thinking_tokens + answer_tokens
    return total, total * PRICE_PER_1M_OUTPUT / 1_000_000


# ----------------------------------------------------------------------------
# STEP 2: CHECK the model output (parse -> shape -> values)
# ----------------------------------------------------------------------------
CATEGORIES = ["bug", "feature", "question"]


def check_output(text):
    """Return 'OK' or the reason why we must reject (and maybe retry)."""
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return "REJECT: not valid JSON"
    if set(data) != {"category", "priority"}:
        return "REJECT: wrong keys"
    if data["category"] not in CATEGORIES:
        return "REJECT: unknown category"
    if not isinstance(data["priority"], int) or not 1 <= data["priority"] <= 5:
        return "REJECT: priority must be a number 1-5"
    return "OK"


# ----------------------------------------------------------------------------
# STEP 3: CONSTRAINED DECODING = block every token that breaks the format
# ----------------------------------------------------------------------------
# At each step: what the model WANTS (best first), and what the format ALLOWS.
STEPS = [
    (["Sure!", "{"],                 ["{"]),
    (['"category":'],                ['"category":']),
    (['"crash"', '"bug"'],           ['"bug"', '"feature"', '"question"']),
    ([","],                          [","]),
    (['"priority":'],                ['"priority":']),
    (['"high"', "2"],                ["1", "2", "3", "4", "5"]),
    (["}"],                          ["}"]),
]


def decode(constrained):
    out = []
    for wanted, allowed in STEPS:
        if constrained:
            # keep only allowed tokens, then take the model's best one
            pick = [t for t in wanted if t in allowed][0]
        else:
            pick = wanted[0]                  # just the model's favourite
        out.append(pick)
    return "".join(out)


def main():
    print("STEP 1: what thinking costs (1,000 calls)")
    for name, think in [("easy task, no thinking", 0), ("hard task, thinking", 3000)]:
        tokens, dollars = cost_of_call(think, 200)
        print(f"  {name:<24} {tokens:>5} output tokens/call  -> ${dollars * 1000:.2f}")
    print("  Same answer length, 16x the bill. Only think when the task needs it.")

    print("\nSTEP 2: check what the model returned")
    samples = [
        '{"category": "bug", "priority": 2}',
        'Sure! Here is the JSON: {"category": "bug", "priority": 2}',
        '{"category": "crash", "priority": 2}',
        '{"category": "bug", "priority": "high"}',
        '{"category": "bug", "prio',               # cut off by max_tokens
    ]
    for text in samples:
        print(f"  {text:<60} -> {check_output(text)}")

    print("\nSTEP 3: constrained decoding")
    for constrained in [False, True]:
        text = decode(constrained)
        label = "with constraint   " if constrained else "without constraint"
        print(f"  {label}: {text:<46} -> {check_output(text)}")
    print("  The model wanted 'Sure!', 'crash' and 'high'. The constraint blocked them.")
    print("  The shape is now guaranteed. The VALUES still need your own checks.")


if __name__ == "__main__":
    main()

# Remember:
#   - Thinking = hidden output tokens. You pay for them. Use for hard tasks only.
#   - Prompt "return JSON" < JSON mode < schema-constrained (a guarantee).
#   - Always validate values in code. Cut-off output (max_tokens) still breaks JSON.
# Try: add a sample with priority 9. Does check_output catch it?
