"""13 -- Reasoning and structured output  (simple version)
=========================================================

IN ONE LINE:
  Reasoning models "think" in hidden words before they answer (you pay for them).
  Structured output forces the answer into YOUR JSON shape.

REAL USE CASE:
  Your FastAPI endpoint asks the model to read a support ticket and return
  JSON that your code can save to a database:

  ┌──────────────┐ POST /ticket ┌─────────────────────┐  HTTPS   ┌──────────────────────────────┐
  │   Browser    │ ───────────▶ │  YOUR FASTAPI       │ ───────▶ │        LLM PROVIDER          │
  │ "app crashes │              │  1. build prompt    │          │  hidden thinking (billed!)   │
  │  on login"   │              │  2. CHECK the JSON  │ ◀─────── │  visible answer:             │
  │              │ ◀─────────── │  3. save to DB      │  answer  │  {"category": "bug",         │
  └──────────────┘  201 saved   └─────────────────────┘          │   "priority": 2}             │
                                    ▲ THIS LESSON                └──────────────────────────────┘
                                    │ = step 2, the check

THE CHECK PIPELINE (STEP 2 in the code). One fail = reject:

  model text
     │
     ▼
  ┌──────────────┐  no   ┌──────────────────────────────┐
  │ json.loads   │ ────▶ │ REJECT: not valid JSON       │
  │ parses?      │       └──────────────────────────────┘
  └──────────────┘
     │ yes
     ▼
  ┌──────────────┐  no   ┌──────────────────────────────┐
  │ keys exactly │ ────▶ │ REJECT: wrong keys           │
  │ cat + prio?  │       └──────────────────────────────┘
  └──────────────┘
     │ yes
     ▼
  ┌──────────────┐  no   ┌──────────────────────────────┐
  │ category in  │ ────▶ │ REJECT: unknown category     │
  │ the list?    │       └──────────────────────────────┘
  └──────────────┘
     │ yes
     ▼
  ┌──────────────┐  no   ┌───────────────────────────────────────┐
  │ priority int │ ────▶ │ REJECT: priority must be a number 1-5 │
  │ 1 to 5?      │       └───────────────────────────────────────┘
  └──────────────┘
     │ yes
     ▼
    OK ──▶ save to DB

ONE VALIDATE -> RETRY RUN, step by step (the real run printed by STEP 4):

   try   model returned                               check says                 next
   ───   ──────────────────────────────────────────   ────────────────────────   ─────────────────
    1    Sure! Here is the JSON: {"category": ...     REJECT: not valid JSON     retry, send error
    2    {"category": "crash", "priority": 2}         REJECT: unknown category   retry, send error
    3    {"category": "bug", "priority": 2}           OK                         save, stop

   3 calls = 3x the cost and 3x the wait. Constrained decoding (STEP 3)
   makes the FORMAT right the first time. Your VALUE checks still run.

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
#   easy task:  thinking     0  +  answer 200  =   200 output tokens
#   hard task:  thinking 3,000  +  answer 200  = 3,200 output tokens
#                  │
#                  ▼  x $15 per 1,000,000 tokens  x 1,000 calls
#   easy:   200 x 15 / 1,000,000 x 1,000  =  $3.00
#   hard: 3,200 x 15 / 1,000,000 x 1,000  = $48.00   <- 16x the bill, same answer
def cost_of_call(thinking_tokens, answer_tokens):
    total = thinking_tokens + answer_tokens
    return total, total * PRICE_PER_1M_OUTPUT / 1_000_000


# ----------------------------------------------------------------------------
# STEP 2: CHECK the model output (parse -> shape -> values)
# ----------------------------------------------------------------------------
#   text in                                       which check fails      result
#   ───────────────────────────────────────────   ────────────────────   ─────────────────────
#   {"category": "bug", "priority": 2}            (none)                 OK
#   Sure! Here is the JSON: {"category": ...      json.loads             not valid JSON
#   {"category": "crash", "priority": 2}          category list          unknown category
#   {"category": "bug", "priority": "high"}       priority 1-5           priority must be ...
#   {"category": "bug", "prio                     json.loads             not valid JSON
#                                                  (cut off by max_tokens!)
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
#   step  model WANTS (best first)   format ALLOWS               no constraint   with constraint
#   ────  ────────────────────────   ─────────────────────────   ─────────────   ───────────────
#    1    Sure!  {                   {                           Sure!   ✗       {
#    2    "category":                "category":                 "category":     "category":
#    3    "crash"  "bug"             "bug" "feature" "question"  "crash" ✗       "bug"
#    4    ,                          ,                           ,               ,
#    5    "priority":                "priority":                 "priority":     "priority":
#    6    "high"  2                  1 2 3 4 5                   "high"  ✗       2
#    7    }                          }                           }               }
#
#   for each step:
#      │
#      ▼
#   constrained? ── no ──▶ take wanted[0] (the favourite, even if it breaks JSON)
#      │ yes
#      ▼
#   drop every wanted token that is NOT allowed ──▶ take the best one left
#
#   no constraint : Sure!"category":"crash","priority":"high"}  -> REJECT: not valid JSON
#   constraint    : {"category":"bug","priority":2}             -> OK
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


# ----------------------------------------------------------------------------
# STEP 4: VALIDATE -> RETRY loop (what your FastAPI code does without constraints)
# ----------------------------------------------------------------------------
#   attempt = 1
#      │
#      ▼
#   ┌─▶ call the model ──▶ text
#   │      │
#   │      ▼
#   │   check_output(text) == "OK"? ── yes ──▶ return json.loads(text)  (save to DB)
#   │      │ no
#   │      ▼
#   │   attempt == max_tries? ── yes ──▶ give up, return None  (your API sends 502)
#   │      │ no
#   │      ▼
#   │   add the error to the prompt: "Your last answer was rejected: unknown category"
#   │   attempt = attempt + 1
#   └──────┘
#
#   real run:  try 1 not valid JSON ──▶ try 2 unknown category ──▶ try 3 OK
#              result {'category': 'bug', 'priority': 2}
def ask_with_retry(model_replies, max_tries=3):
    """model_replies = what a fake model returns on try 1, 2, 3 (a real app calls the API)."""
    for attempt, text in enumerate(model_replies[:max_tries], start=1):
        verdict = check_output(text)
        print(f"  try {attempt}: {text:<58} -> {verdict}")
        if verdict == "OK":
            return json.loads(text)
        # real app: put the verdict into the next prompt so the model can fix it
    return None


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

    print("\nSTEP 4: validate -> retry (no constraint, max 3 tries)")
    result = ask_with_retry([samples[1], samples[2], samples[0]])
    print(f"  result: {result}  (3 calls = 3x cost and wait)")


if __name__ == "__main__":
    main()

# Remember:
#   - Thinking = hidden output tokens. You pay for them. Use for hard tasks only.
#   - Prompt "return JSON" < JSON mode < schema-constrained (a guarantee).
#   - Always validate values in code. Cut-off output (max_tokens) still breaks JSON.
#   - Without constraints: validate, then retry with the error. Limit the tries.
# Try: add a sample with priority 9. Does check_output catch it?
