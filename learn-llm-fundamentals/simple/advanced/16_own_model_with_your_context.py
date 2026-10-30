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

WHAT AN ENGINEER MUST KNOW:
  1. A model trained from zero on only your docs just repeats and MIXES
     sentences. It cannot reason or answer questions.
  2. A real open model already knows language. You only add the facts.
  3. Change a policy -> edit one line -> the next answer is updated. No training.
  4. Always tell the model: "if it is not in the documents, say you don't know".

Run:  uv run python simple/advanced/16_own_model_with_your_context.py
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
def retrieve(question, top_k=2):
    """Score each line by how many important words it shares with the question."""
    q_words = set(question.lower().strip("?").split()) - SKIP
    scored = []
    for doc_id, text in HANDBOOK.items():
        overlap = len(q_words & set(text.split()))
        if overlap > 0:
            scored.append((overlap, doc_id, text))
    scored.sort(key=lambda s: (-s[0], s[1]))       # most shared words first, then by id
    return scored[:top_k]


# ----------------------------------------------------------------------------
# STEP 3: OPTION A -- build the grounded prompt for the open model
# ----------------------------------------------------------------------------
def build_prompt(question, hits):
    docs = "\n".join(f"[{doc_id}] {text}" for _, doc_id, text in hits) or "(nothing found)"
    return ("Answer ONLY from the documents. Cite the [id]. If the answer is not "
            "there, say: I don't know based on the handbook.\n\n"
            f"<documents>\n{docs}\n</documents>\n\nQuestion: {question}")


def main():
    print("STEP 1: our OWN model, trained only on the handbook")
    own = train_own_model(HANDBOOK.values())
    for seed in range(4):
        text = generate(own, "employees", seed)
        real = any(text in line for line in HANDBOOK.values())   # is it inside one real line?
        print(f"   {'real line  ' if real else 'MIXED/FALSE'} | {text}")
    print("  It copies lines or MIXES them at a shared word (here: 'days').")
    print("  Mixed lines sound right but are false. And it cannot answer a question.")

    print("\nSTEP 2: retrieval -- find the lines that match the question")
    questions = ["How many vacation days do I get?", "What is the parental leave policy?"]
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
