"""04 -- Context engineering  (simple version)
============================================

IN ONE LINE:
  The model only knows what you send it in THIS call.
  Your job: send the RIGHT information, in the RIGHT order, and nothing else.

REAL USE CASE:
  A user asks your FastAPI support bot: "How do I reset my password?"
  You have 10 help docs and a long chat history. You can't send it all.

     help docs (10) ──SELECT the best 2──┐
     chat history  ──COMPRESS old turns──┤
                                         ▼
                              ┌─────────────────────┐
                              │ 1. system rules     │  <- same every call
                              │ 2. selected docs    │
                              │ 3. short history    │
                              │ 4. the question     │  <- always LAST
                              └─────────────────────┘
                                         │
                                         ▼
                                       MODEL

WHERE CONTEXT IS BUILT IN A REAL APP:

  ┌──────────────┐  POST /chat   ┌──────────────────────────────┐  HTTPS   ┌──────────────────────┐
  │   Browser    │ ────────────▶ │  YOUR FASTAPI                │ ───────▶ │    LLM PROVIDER      │
  │ "How do I    │   question    │  1. SELECT docs   (STEP 1)   │ ONE text │  reads ONLY this     │
  │  reset my    │               │  2. COMPRESS chat (STEP 2)   │ 67 tokens│  text. Knows nothing │
  │  password?"  │               │  3. BUILD context (STEP 3)   │          │  else about you.     │
  │              │ ◀──────────── │  4. CHECK it      (STEP 4)   │ ◀─────── │                      │
  └──────────────┘    answer     └──────────────────────────────┘  answer  └──────────────────────┘
                                    ▲                    ▲
                                    │                    │
                              help docs (DB)      chat history (DB)

THE PIPELINE -- from everything you have to what the model sees:

  ┌────────────────┐  SELECT   ┌────────────────┐
  │ 5 help docs    │ ────────▶ │ 1 doc          │ ──┐
  │ 73 tokens      │  STEP 1   │ 17 tokens      │   │
  └────────────────┘           └────────────────┘   │    BUILD     ┌────────────────┐  CHECK   ┌───────┐
                                                    ├───────────▶  │ final context  │ ───────▶ │ MODEL │
  ┌────────────────┐  COMPRESS ┌────────────────┐   │    STEP 3    │ 67 tokens      │  STEP 4  └───────┘
  │ 8 chat turns   │ ────────▶ │ 3 lines        │ ──┘              └────────────────┘
  │ 47 tokens      │  STEP 2   │ 25 tokens      │       + system rules + question
  └────────────────┘           └────────────────┘

ONE FULL RUN, step by step (the real numbers printed by the script):

   step        input                         what happens                       output
   ─────────   ───────────────────────────   ────────────────────────────────   ──────────────────────
   1 SELECT    5 docs, 73 tokens             count shared words with question   ['password'], 17 tokens
   2 COMPRESS  8 turns, 47 tokens            6 old turns ──▶ 1 summary line     3 lines, 25 tokens
   3 BUILD     rules + doc + history + q.    join in a fixed order              6 lines of text
   4 CHECK     the final context             is 'Settings > Security' in it?    True, 67 tokens

WHAT AN ENGINEER MUST KNOW:
  1. The API is stateless. You build the full context on EVERY call.
  2. The context window is a budget. Every token costs money and time.
  3. SELECT: send only the docs that match the question.
  4. COMPRESS: replace old chat turns with a short summary.
  5. ORDER: stable parts first (cheaper, cacheable), the question last.

Run:  uv run python simple/04_context_engineering.py
"""

# ----------------------------------------------------------------------------
# Our fake data
# ----------------------------------------------------------------------------
SYSTEM_RULES = "You are a support bot. Answer only from the docs. Be short."

HELP_DOCS = {
    "password": "To reset your password, open Settings > Security and click Reset.",
    "billing": "Invoices are sent on the 1st of each month to the account email.",
    "teams": "To add a teammate, open Settings > Team and click Invite.",
    "regions": "You can enable a new region from the Regions page.",
    "api_keys": "API keys can be rotated from Settings > Developer.",
}

CHAT_HISTORY = [
    "user: hi",
    "bot: hello, how can I help?",
    "user: my name is Sam",
    "bot: nice to meet you Sam",
    "user: I use the Pro plan",
    "bot: great, Pro has all features",
    "user: I can't log in",
    "bot: sorry to hear that",
]


def count_tokens(text):
    """Rough rule: 1 token is about 4 characters."""
    return len(text) // 4 + 1


# ----------------------------------------------------------------------------
# STEP 1: SELECT = keep only the docs that match the question
# ----------------------------------------------------------------------------
#   "How do I reset my password?"
#      │
#      ▼  lower case, remove "?", split into words
#   {how, do, i, reset, my, password}
#      │
#      ▼  remove SMALL_WORDS (how, do, i, my, ...)
#   question_words = {password, reset}
#      │
#      ▼
#   ┌─▶ next doc
#   │      │
#   │      ▼
#   │   shared = words in BOTH the doc and the question
#   │      password: {password, reset} ──▶ 2
#   │      billing:  {}                ──▶ 0
#   │      teams, regions, api_keys:   ──▶ 0
#   │      │
#   │      ▼
#   │   shared > 0? ── no ──▶ skip this doc
#   │      │ yes                  │
#   │      ▼                      │
#   │   scores.append((2, "password"))
#   │      │◀─────────────────────┘
#   │   more docs? ── no ──▶ sort: most shared first (same score -> A to Z)
#   │      │ yes                 │
#   └──────┘                     ▼  keep the top how_many=2
#                             ["password"]   (only 1 doc matched, so we get only 1)
SMALL_WORDS = {"how", "do", "i", "to", "the", "a", "my", "your", "and", "of"}


def select_docs(question, docs, how_many=2, show_steps=False):
    """Score each doc by how many words it shares with the question."""
    question_words = set(question.lower().replace("?", "").split()) - SMALL_WORDS
    if show_steps:
        print("    question words:", sorted(question_words))   # sorted: same order every run
    scores = []
    for name, text in docs.items():
        doc_words = set(text.lower().replace(".", "").replace(",", "").split())
        shared = len(question_words & doc_words)    # words in BOTH sets
        if show_steps:
            print("    " + name.ljust(9), "shares", sorted(question_words & doc_words), "->", shared)
        if shared > 0:                              # skip docs with no match
            scores.append((shared, name))
    scores.sort(key=lambda item: (-item[0], item[1]))  # best match first; tie -> A to Z
    return [name for shared, name in scores[:how_many]]


# ----------------------------------------------------------------------------
# STEP 2: COMPRESS = summarize old chat turns, keep the last few as-is
# ----------------------------------------------------------------------------
#   history (8 turns, 47 tokens)
#   ┌──────────────────────────────────┐
#   │ user: hi                         │ ┐
#   │ bot: hello, how can I help?      │ │
#   │ user: my name is Sam             │ │  old = history[:-2]  (6 turns)
#   │ bot: nice to meet you Sam        │ ├────────▶ summary: user is Sam, on the Pro plan (6 old turns)
#   │ user: I use the Pro plan         │ │          (a real app asks a small, cheap LLM for this)
#   │ bot: great, Pro has all features │ ┘
#   │ user: I can't log in             │ ┐  recent = history[-2:]  (keep as-is)
#   │ bot: sorry to hear that          │ ┘ ────────▶ user: I can't log in
#   └──────────────────────────────────┘             bot: sorry to hear that
#                                                      │
#                                                      ▼
#                                         [summary] + recent = 3 lines, 25 tokens
def compress_history(history, keep_last=2):
    old = history[:-keep_last]
    recent = history[-keep_last:]
    # A real app asks a small, cheap LLM to write this summary.
    summary = "summary: user is Sam, on the Pro plan (" + str(len(old)) + " old turns)"
    return [summary] + recent


# ----------------------------------------------------------------------------
# STEP 3: BUILD = put the parts together in a good order
# ----------------------------------------------------------------------------
#   parts = []
#      │
#      ▼  1. SYSTEM_RULES                 "You are a support bot. ..."    <- stable, FIRST
#      ▼  2. "DOC: " + each chosen doc    "DOC: To reset your password..."
#      ▼  3. the short history            summary + 2 recent turns
#      ▼  4. "QUESTION: " + question      "QUESTION: How do I reset..."   <- changes, LAST
#      │
#      ▼  "\n".join(parts)
#   one text, 6 lines, 67 tokens  ──▶  model
#
#   Why this order?  The top part is the same on every call, so the provider can
#   cache it (cheaper, faster). The question at the end is what the model reads last.
def build_context(question, doc_names, history):
    parts = [SYSTEM_RULES]                          # stable part goes FIRST
    for name in doc_names:
        parts.append("DOC: " + HELP_DOCS[name])
    parts.extend(history)
    parts.append("QUESTION: " + question)           # the question goes LAST
    return "\n".join(parts)


# ----------------------------------------------------------------------------
# STEP 4: CHECK = is the needed fact really in the context?
# ----------------------------------------------------------------------------
#   context
#      │
#      ▼
#   "Settings > Security" in context? ── no ──▶ fix SELECT first! (the model would guess)
#      │ yes (True)
#      ▼
#   size ok? (67 tokens) ── no ──▶ cut more history or fewer docs
#      │ yes
#      ▼
#   call the model
def main():
    question = "How do I reset my password?"

    print("STEP 1: select only the useful docs")
    all_docs_text = " ".join(HELP_DOCS.values())
    chosen = select_docs(question, HELP_DOCS, show_steps=True)
    chosen_text = " ".join(HELP_DOCS[name] for name in chosen)
    print("  all", len(HELP_DOCS), "docs :", count_tokens(all_docs_text), "tokens")
    print("  chosen    :", chosen, "->", count_tokens(chosen_text), "tokens")

    print("\nSTEP 2: compress the chat history")
    short_history = compress_history(CHAT_HISTORY)
    print("  before:", len(CHAT_HISTORY), "turns,", count_tokens(" ".join(CHAT_HISTORY)), "tokens")
    print("  after :", len(short_history), "turns,", count_tokens(" ".join(short_history)), "tokens")
    for line in short_history:
        print("    ", line)

    print("\nSTEP 3: build the final context (this is what the model sees)")
    context = build_context(question, chosen, short_history)
    print("  ---")
    for line in context.split("\n"):
        print("  " + line)
    print("  ---")
    print("  " + str(len(context.split("\n"))), "lines")

    print("\nSTEP 4: check the context before you call the model")
    has_fact = "Settings > Security" in context
    print("  contains the answer fact 'Settings > Security'?", has_fact)
    print("  total size:", count_tokens(context), "tokens")
    print("  If the fact is missing, the model can only guess (hallucinate).")


if __name__ == "__main__":
    main()

# Remember:
#   - You build the whole context on every call. The model remembers nothing.
#   - Less but relevant beats more but noisy.
#   - Stable parts first, the question last.
#   - Check that the needed facts are really in the context.
# Try: change the question to "How do I add a teammate?" and see which docs win.
