"""10 -- RAG and embeddings  (simple version)
===========================================

IN ONE LINE:
  RAG = find the few pieces of YOUR documents that match the question,
  put them in the prompt, and tell the model to answer only from them.

REAL USE CASE:
  Your FastAPI help bot must answer about YOUR product. The model was
  never trained on your docs, so you look them up first:

     question: "How do I get a refund?"
            │
            ▼  embed (text -> numbers)
     ┌────────────────┐  compare with every doc  ┌────────────────────┐
     │ question vector│ ───────────────────────▶ │ top 2 closest docs │
     └────────────────┘                          └────────────────────┘
                                                          │
            ┌─────────────────────────────────────────────┘
            ▼
     prompt = docs + question  ──▶  LLM  ──▶  answer with [doc ids]

WHERE RAG SITS IN A REAL APP:

  ┌──────────────┐  POST /ask    ┌─────────────────────────┐  HTTPS   ┌──────────────────┐
  │   Browser    │ ────────────▶ │  YOUR FASTAPI           │ ───────▶ │   LLM PROVIDER   │
  │ "How do I    │               │  1. embed question      │  prompt  │  answers ONLY    │
  │  get a       │               │  2. search vector store │  with    │  from the docs   │
  │  refund?"    │ ◀──────────── │  3. build prompt        │  docs    │  in the prompt   │
  └──────────────┘  answer +     └─────────────────────────┘ ◀─────── └──────────────────┘
                    [refunds]          │          ▲          answer
                                search │          │ top-k docs
                                       ▼          │
                                ┌─────────────────────────┐
                                │ VECTOR STORE (index)    │
                                │ filled ONCE at startup  │
                                └─────────────────────────┘

PIPELINE 1 -- INDEXING (done ONCE, before any question; STEP 1 in the code):

  ┌───────────────┐     ┌───────────────┐     ┌──────────────────────┐     ┌──────────────────┐
  │ your 4 docs   │ ──▶ │ chunks        │ ──▶ │ embed each chunk     │ ──▶ │ store vectors    │
  │ (DOCS dict)   │     │ here: 1 doc = │     │ (word counts here)   │     │ index = {id: vec}│
  │               │     │ 1 chunk       │     │                      │     │                  │
  └───────────────┘     └───────────────┘     └──────────────────────┘     └──────────────────┘
     real values printed by STEP 1:
       refunds  -> 9 words    invoices -> 6 words    sso -> 7 words    rollback -> 9 words
     Real apps split long docs into chunks of ~200-500 tokens first.

PIPELINE 2 -- QUERY (done for EVERY request; STEP 1 to 4 in the code):

  "How do I get a refund?"
        │
        ▼  embed (drop SKIP_WORDS: how, do, i, a)
  {'get': 1, 'refund': 1}                      |q| = 1.41
        │
        ▼  cosine with EVERY stored vector
  ┌──────────┬──────────────┬─────┬───────┬─────────────────────────┐
  │ doc      │ shared words │ dot │ |doc| │ cosine = dot/(|q|·|doc|)│
  ├──────────┼──────────────┼─────┼───────┼─────────────────────────┤
  │ refunds  │ get, refund  │  2  │ 3.00  │ 2 / (1.41 · 3.00) = 0.47│
  │ invoices │ (none)       │  0  │ 2.45  │ 0.0                     │
  │ sso      │ (none)       │  0  │ 2.65  │ 0.0                     │
  │ rollback │ (none)       │  0  │ 3.00  │ 0.0                     │
  └──────────┴──────────────┴─────┴───────┴─────────────────────────┘
  |doc| = sqrt(number of words), because every word count is 1. refunds: sqrt(9) = 3.00
        │
        ▼  drop score 0, sort high -> low, keep top k = 2
  [(0.47, 'refunds')]                          only 1 doc left, so k=2 gives 1
        │
        ▼  build prompt: rules + "[refunds] refunds are available ..." + question
        │
        ▼  LLM
  answer that cites [refunds]

  Note: "refunds" (in the doc) and "refund" (in the question) are DIFFERENT words
  for word counts. Only "refund" in "...to get a refund" matched. Real embeddings
  understand they mean the same thing.

WHAT AN ENGINEER MUST KNOW:
  1. An embedding turns text into a list of numbers. Similar meaning ->
     similar numbers. Real ones come from an embedding model API.
  2. Cosine similarity says how close two vectors are (1 = same, 0 = no match).
  3. Top-k = keep only the k best docs. Small k = short, cheap prompt.
  4. Tell the model: "answer only from these docs, cite the [id], and
     say 'I don't know' if the answer is not there".
  5. Index time (embed all docs) happens once. Query time happens per request.

Run:  uv run python simple/10_rag_and_embeddings.py
"""

import math

DOCS = {
    "refunds":  "refunds are available within 14 days. contact billing to get a refund",
    "invoices": "invoices are sent on the 1st of each month by email",
    "sso":      "sso login with saml is only on the enterprise plan",
    "rollback": "to undo a bad deploy run acme rollback to restore the old build",
}


# ----------------------------------------------------------------------------
# STEP 1: EMBED = turn text into numbers (here: count each word)
# ----------------------------------------------------------------------------
# A real embedding call looks like this (OpenAI-style SDK):
#   vector = client.embeddings.create(model="...", input=text).data[0].embedding
# A real vector has ~1000 numbers and knows "money back" is close to "refund".
# Our toy version only counts words, so it needs the SAME words.
#
#   "How do I get a refund?"
#      │
#      ▼  lower case, remove "?"
#   "how do i get a refund"
#      │
#      ▼  split into words
#   how   do   i   get   a   refund
#      │
#      ▼  drop SKIP_WORDS (how, do, i, a)
#   get   refund
#      │
#      ▼  count each word
#   {'get': 1, 'refund': 1}      <- this dict IS the vector
SKIP_WORDS = {"a", "the", "to", "do", "i", "how", "is", "are", "of", "on", "by"}   # too common to help


def embed(text):
    counts = {}
    for word in text.lower().replace("?", "").split():
        if word not in SKIP_WORDS:
            counts[word] = counts.get(word, 0) + 1
    return counts                        # {"refund": 1, "get": 1, ...}


# ----------------------------------------------------------------------------
# STEP 2: COSINE SIMILARITY = how close are two vectors?
# ----------------------------------------------------------------------------
#   a = question {'get': 1, 'refund': 1}
#   b = refunds  {'14': 1, 'available': 1, ..., 'get': 1, 'refund': 1, ...}   (9 words)
#      │
#      ▼  dot: for each word in a, multiply by its count in b, then add
#   get: 1 × 1 = 1     refund: 1 × 1 = 1     ──▶  dot = 2
#      │
#      ▼  length of each vector = sqrt(sum of counts squared)
#   |a| = sqrt(1 + 1) = 1.41     |b| = sqrt(9 × 1) = 3.00
#      │
#      ▼  a length is 0? ── yes ──▶ return 0.0  (empty text, avoid dividing by 0)
#      │ no
#      ▼
#   dot / (|a| × |b|) = 2 / (1.41 × 3.00) = 0.47
#
#   1.0 = same words in same amounts      0.0 = no word in common
def cosine(a, b):
    dot = sum(a[word] * b.get(word, 0) for word in a)       # shared words add up
    length_a = math.sqrt(sum(n * n for n in a.values()))
    length_b = math.sqrt(sum(n * n for n in b.values()))
    if length_a == 0 or length_b == 0:
        return 0.0
    return dot / (length_a * length_b)  # divide by length so long docs don't win


# ----------------------------------------------------------------------------
# STEP 3: TOP-K SEARCH = score every doc, keep the best k
# ----------------------------------------------------------------------------
#   q_vec = embed(question) = {'get': 1, 'refund': 1}
#      │
#      ▼
#   ┌─▶ next doc in index ──▶ score = cosine(q_vec, doc_vec)
#   │      │
#   │      ▼
#   │   score > 0? ── yes ──▶ scores.append((score, doc_id))   e.g. (0.47, 'refunds')
#   │      │ no                    │
#   │      ▼  skip it              │
#   │   more docs? ◀───────────────┘
#   │      │ yes
#   └──────┘
#          │ no
#          ▼
#   sort: highest score first; same score -> alphabetical by id
#          │
#          ▼
#   keep the first k  ──▶  [(0.47, 'refunds')]      (k=2, but only 1 doc scored > 0)
def search(question, index, k=2):
    q_vec = embed(question)
    scores = []
    for doc_id, doc_vec in index.items():
        score = round(cosine(q_vec, doc_vec), 2)
        if score > 0:                    # 0 = nothing in common, skip it
            scores.append((score, doc_id))
    scores.sort(key=lambda item: (-item[0], item[1]))   # highest first; tie -> alphabetical
    return scores[:k]


# ----------------------------------------------------------------------------
# STEP 4: BUILD THE PROMPT = put the found docs in, with their ids
# ----------------------------------------------------------------------------
#   top_docs = [(0.47, 'refunds')]       question = "How do I get a refund?"
#      │
#      ▼
#   ┌──────────────────────────────────────────────────────────────────────────────┐
#   │ Answer ONLY from the sources below. Cite the [id].            <- rules       │
#   │ If the answer is not in the sources, say 'I don't know'.      <- rules       │
#   │                                                                              │
#   │ [refunds] refunds are available within 14 days. contact ...   <- 1 line/doc  │
#   │                                                                              │
#   │ Question: How do I get a refund?                              <- the ask     │
#   └──────────────────────────────────────────────────────────────────────────────┘
#      │
#      ▼  send to the LLM as the user message
#   If top_docs is empty (like 'money back' -> []), only rules + question are sent,
#   so the model should say "I don't know".
def build_prompt(question, top_docs):
    lines = ["Answer ONLY from the sources below. Cite the [id].",
             "If the answer is not in the sources, say 'I don't know'.", ""]
    for score, doc_id in top_docs:
        lines.append("[" + doc_id + "] " + DOCS[doc_id])
    lines.append("")
    lines.append("Question: " + question)
    return "\n".join(lines)


def main():
    # Index time: embed every doc ONCE and keep the vectors (a vector database does this).
    index = {doc_id: embed(text) for doc_id, text in DOCS.items()}
    question = "How do I get a refund?"

    print("STEP 1: embed (word counts)")
    print("  index (done once), words per doc:")
    for doc_id, doc_vec in index.items():
        print("    " + doc_id.ljust(9), len(doc_vec), "words ->", sorted(doc_vec))
    print("  question ->", embed(question))

    print("\nSTEP 2: cosine similarity with each doc")
    q_vec = embed(question)
    for doc_id, doc_vec in index.items():
        shared = sorted(word for word in q_vec if word in doc_vec)
        dot = sum(q_vec[word] * doc_vec[word] for word in shared)
        len_q = math.sqrt(sum(n * n for n in q_vec.values()))
        len_d = math.sqrt(sum(n * n for n in doc_vec.values()))
        print("  " + doc_id.ljust(9), round(cosine(q_vec, doc_vec), 2),
              f"  shared={shared} dot={dot} |q|={len_q:.2f} |doc|={len_d:.2f}")

    print("\nSTEP 3: top-2 search (docs with score 0 are dropped)")
    top_docs = search(question, index, k=2)
    print("  ", top_docs)

    print("\nSTEP 4: the prompt we send to the LLM")
    prompt = build_prompt(question, top_docs)
    for line in prompt.split("\n"):
        print("  | " + line)
    # Then: client.messages.create(model="...", messages=[{"role": "user", "content": prompt}])

    print("\nSTEP 5: the weak spot of word counts")
    print("  'money back' ->", search("money back", index, k=1))
    print("  Nothing found: no shared words with 'refunds'. Real embeddings fix")
    print("  this, because they match MEANING, not exact words.")
    print("  With no docs, the prompt rule makes the model say 'I don't know'.")


if __name__ == "__main__":
    main()

# Remember:
#   - RAG = search your docs, put the best ones in the prompt, then ask.
#   - Embedding = text as numbers. Cosine = how close. Top-k = keep the best.
#   - Ask for citations and allow "I don't know".
# Try: add a doc about "pricing" and ask "what does the pro plan cost?".
