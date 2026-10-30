"""16 -- "Our own model" with our context  (simple version)
==========================================================

IN ONE LINE:
  Do NOT train your own model on your documents. Take a good open model
  and put the right documents into the PROMPT (this is RAG).

REAL USE CASE:
  HR asks: "Can we have a bot that knows our handbook?"

     question: "How many vacation days do I get?"
          │
          ▼  1. find matching handbook lines (search)
     [leave-1] Full-time employees get 25 vacation days per year.
          │
          ▼  2. build prompt: "answer ONLY from these lines, cite [id]"
     ┌──────────────────────┐
     │ open model (Ollama)  │   runs on your machine, data stays private
     └──────────────────────┘
          │
          ▼
     "You get 25 vacation days [leave-1]."

DECISION: "we want a model that knows our docs". Which way?

                       your company docs (handbook)
                                   │
              ┌────────────────────┴────────────────────┐
              ▼                                         ▼
   OPTION B: train a model                   OPTION A: give it your docs (RAG)
   from zero on ONLY the docs                good open model + search + prompt
              │                                         │
              ▼                                         ▼
   it learns "which word follows             it already knows language;
   which" (STEP 1)                           you add the facts per question
              │                                         │
              ▼                                         ▼
   mixes lines at shared words:              finds [leave-1] (STEP 2),
   "employees get 25 vacation days           builds a grounded prompt (STEP 3)
    per week"  ◀── FALSE                     answer cites [leave-1]  ✓
   cannot answer a question  ✗               policy changed? edit 1 line, done  ✓
                                             not in docs? "I don't know"  ✓

   Quick check before you choose:
   need FACTS from your docs?           ── yes ──▶ RAG (this lesson + lesson 10)
      │ no
      ▼
   need a fixed STYLE / FORMAT?         ── yes ──▶ fine-tune a good model (lesson 14)
      │ no
      ▼
   a good prompt is enough (lessons 04-05)
   Training from zero: almost never. It needs huge data and huge money.

THE RETRIEVAL FLOW, one real run (printed by STEP 2 and STEP 3):

   "How many vacation days do I get?"
        │  lowercase, drop "?", split into words
        ▼
   how many vacation days do i get
        │  remove SKIP words (how, many, do, i, get ...)
        ▼
   {days, vacation}
        │  count shared words with every handbook line
        ▼
   leave-1    2  (days, vacation)  ─┐
   leave-2    2  (days, vacation)  ─┤  sort: most shared first, then by id
   remote-1   1  (days)             │  keep top_k = 2
   expense-1  1  (days)             │
   laptop-1   0  -> dropped         │
        ┌───────────────────────────┘
        ▼
   hits = [leave-1, leave-2]  ──▶  build_prompt  ──▶  open model  ──▶ answer + [leave-1]

   "What is the parental leave policy?" ──▶ {leave, parental, policy}
        ──▶ 0 shared words everywhere ──▶ nothing ──▶ prompt says "(nothing found)"
        ──▶ the model must answer "I don't know based on the handbook."

WHAT AN ENGINEER MUST KNOW:
  1. A model trained from zero on only your docs just repeats and MIXES
     sentences. It cannot reason or answer questions.
  2. A real open model already knows language. You only add the facts.
  3. Change a policy -> edit one line -> the next answer is updated. No training.
  4. Always tell the model: "if it is not in the documents, say you don't know".

Run:  uv run python simple/16_own_model_with_your_context.py
"""

import random

HANDBOOK = {
    "leave-1": "full-time employees get 25 vacation days per year",
    "leave-2": "unused vacation days can be carried over up to 5 days",
    "remote-1": "employees may work remotely up to 3 days per week",
    "expense-1": "travel expenses must be submitted within 30 days",
    "laptop-1": "lost laptops must be reported to it within 24 hours",
}
SKIP = {"how", "many", "do", "i", "get", "can", "my", "the", "a", "is", "what", "to"}


# ----------------------------------------------------------------------------
# STEP 1: OPTION B -- train our OWN tiny model on only the handbook
# ----------------------------------------------------------------------------
#   5 handbook lines
#      │
#      ▼  train: write down which word follows which (like lesson 01)
#   notebook: "days" -> [per, can, <stop>, per, <stop>]     (from 4 different lines!)
#             "per"  -> [year, week]
#      │
#      ▼  generate from "employees" (seed 1), one word per loop:
#
#   ┌─▶ options = notebook[last word] ──▶ pick one at random
#   │      │
#   │   "<stop>"? ── yes ──▶ END
#   │      │ no
#   │   append it, max 15 words? ── yes ──▶ END
#   │      │ no
#   └──────┘
#
#   last word    options                          picked
#   ──────────   ──────────────────────────────   ────────
#   employees    get, may                         get        (leave-1)
#   get          25                               25         (leave-1)
#   25           vacation                         vacation   (leave-1)
#   vacation     days, days                       days       (leave-1)
#   days         per, can, <stop>, per, <stop>    per
#   per          year, week                       week       ◀── from remote-1! MIXED
#   week         <stop>                           <stop>
#
#   result: "employees get 25 vacation days per week"   sounds real, is FALSE
def train_own_model(texts):
    """Remember which word follows which word (like lesson 01)."""
    next_words = {}
    for text in texts:
        words = text.split() + ["<stop>"]
        for current, following in zip(words, words[1:]):
            next_words.setdefault(current, []).append(following)
    return next_words


def generate(model, start, seed):
    rng = random.Random(seed)
    words = start.split()
    for _ in range(15):
        options = model.get(words[-1], ["<stop>"])
        word = rng.choice(options)
        if word == "<stop>":
            break
        words.append(word)
    return " ".join(words)


# ----------------------------------------------------------------------------
# STEP 2: OPTION A -- find the right lines (retrieval)
# ----------------------------------------------------------------------------
#   question ──▶ q_words = {days, vacation}   (after SKIP words are removed)
#      │
#      ▼  for each handbook line:
#   ┌─▶ shared = q_words & words of the line
#   │      │
#   │   len(shared) > 0? ── no ──▶ skip it        (laptop-1: 0)
#   │      │ yes
#   │   keep (score, id, text)                    (leave-1: 2, leave-2: 2,
#   │      │                                       remote-1: 1, expense-1: 1)
#   └──────┘
#      │
#      ▼  sort by (-score, id): same score -> alphabetical id, so every run is the same
#   (2 leave-1) (2 leave-2) (1 expense-1) (1 remote-1)
#      │
#      ▼  keep the first top_k = 2
#   ['leave-1', 'leave-2']
def retrieve(question, top_k=2, show_scores=False):
    """Score each line by how many important words it shares with the question."""
    q_words = set(question.lower().strip("?").split()) - SKIP
    if show_scores:
        print(f"    important words: {sorted(q_words)}")
    scored = []
    for doc_id, text in HANDBOOK.items():
        overlap = len(q_words & set(text.split()))
        if show_scores:
            print(f"    {doc_id:<10} shares {overlap}  {sorted(q_words & set(text.split()))}")
        if overlap > 0:
            scored.append((overlap, doc_id, text))
    scored.sort(key=lambda s: (-s[0], s[1]))       # most shared words first, then by id
    return scored[:top_k]


# ----------------------------------------------------------------------------
# STEP 3: OPTION A -- build the grounded prompt for the open model
# ----------------------------------------------------------------------------
#   hits = [(2, 'leave-1', '...25 vacation days...'), (2, 'leave-2', '...carried over...')]
#      │
#      ▼  any hits? ── no ──▶ docs = "(nothing found)"  (model must say "I don't know")
#      │ yes
#      ▼  one line per hit: "[id] text"
#   ┌──────────────────────────────────────────────────────────────────┐
#   │ Answer ONLY from the documents. Cite the [id]. If the answer ... │  <- rules
#   │ <documents>                                                      │
#   │ [leave-1] full-time employees get 25 vacation days per year      │  <- facts
#   │ [leave-2] unused vacation days can be carried over up to 5 days  │
#   │ </documents>                                                     │
#   │ Question: How many vacation days do I get?                       │  <- question
#   └──────────────────────────────────────────────────────────────────┘
#      │
#      ▼  send as the user message to the open model (Ollama, lesson 15)
def build_prompt(question, hits):
    docs = "\n".join(f"[{doc_id}] {text}" for _, doc_id, text in hits) or "(nothing found)"
    return ("Answer ONLY from the documents. Cite the [id]. If the answer is not "
            "there, say: I don't know based on the handbook.\n\n"
            f"<documents>\n{docs}\n</documents>\n\nQuestion: {question}")


def main():
    print("STEP 1: our OWN model, trained only on the handbook")
    own = train_own_model(HANDBOOK.values())
    print(f"  notebook: after 'days' -> {own['days']}")
    print(f"            after 'per'  -> {own['per']}")
    for seed in range(4):
        text = generate(own, "employees", seed)
        real = any(text in line for line in HANDBOOK.values())   # is it inside one real line?
        print(f"   {'real line  ' if real else 'MIXED/FALSE'} | {text}")
    print("  It copies lines or MIXES them at a shared word (here: 'days').")
    print("  Mixed lines sound right but are false. And it cannot answer a question.")

    print("\nSTEP 2: retrieval -- find the lines that match the question")
    questions = ["How many vacation days do I get?", "What is the parental leave policy?"]
    for q in questions:
        print(f"  {q}")
        retrieve(q, show_scores=True)
    for q in questions:
        hits = retrieve(q)
        print(f"  {q:<36} -> {[doc_id for _, doc_id, _ in hits] or 'nothing'}")

    print("\nSTEP 3: the prompt we send to the open model")
    for line in build_prompt(questions[0], retrieve(questions[0])).splitlines():
        print("   |", line)
    print("  For the parental leave question nothing is found, so the rule")
    print("  'say I don't know' stops the model from inventing an answer.")


if __name__ == "__main__":
    main()

# HOW TO DO IT FOR REAL (needs Ollama running, see lesson 15):
#   send build_prompt(q, retrieve(q)) as the user message to
#   POST http://127.0.0.1:11434/api/chat  (same code as lesson 15), with
#   "options": {"temperature": 0, "num_ctx": 4096}   # num_ctx = context size

# Remember:
#   - "Our own model" = an open model you run + your docs in the prompt.
#   - Training from zero on your docs gives a parrot, not an assistant.
#   - Always allow "I don't know" in the prompt.
# Try: add "parental-1": "parental leave is 16 weeks" to HANDBOOK and run again.
