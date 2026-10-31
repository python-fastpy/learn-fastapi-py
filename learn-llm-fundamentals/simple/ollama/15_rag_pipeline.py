"""15 -- RAG pipeline: the full version a real app uses
======================================================

CONCEPT IN ONE LINE:
  Real documents are long. Cut them into CHUNKS, embed and SAVE them once, then for each
  question fetch the best chunks, answer WITH citations, and MEASURE retrieval quality.
                                                     (basics: lesson 14, details: simple/10)

   INDEXING (run once, or when docs change)
   ┌──────────┐   ┌───────────────┐   ┌──────────────┐   ┌──────────────────────┐
   │ handbook │──▶│ chunk         │──▶│ embed each   │──▶│ save index to disk   │
   │ (long)   │   │ ~2 sentences, │   │ chunk        │   │ .rag_index.json      │
   └──────────┘   │ 1 overlapping │   └──────────────┘   │ (a mini vector DB)   │
                  └───────────────┘                      └──────────────────────┘
   QUERY (every question)
   question ──▶ embed ──▶ score vs all chunks ──▶ best score too low? ── yes ──▶ "I don't know"
                                                       │ no                      (no LLM call)
                                                       ▼
                               top 3 chunks ──▶ prompt with [chunk ids] ──▶ answer + citations
   EVAL
   known question ──▶ is the RIGHT chunk in the top 3?  ──▶ hit rate (retrieval quality)

  WHY CHUNKS: a whole handbook does not fit the context window (lesson 05), and a
  small focused chunk gives a sharper embedding than one vector for everything.
"""

import hashlib
import json
import math
from pathlib import Path

from ollama_client import ask, embed

HANDBOOK = """
Acme Handbook. Acme sells smart lamps online. Our head office is in Berlin.
Refunds. You can return a product within 14 days of delivery. The product must be unused.
Refund money goes back to the original card. It takes 5 to 7 business days to arrive.
Shipping costs are not refunded. Damaged products are refunded in full, including shipping.
Shipping. We ship to all EU countries and the UK. Standard delivery takes 3 to 5 days.
Express delivery takes 1 day and costs 9 euros. Orders over 50 euros ship for free.
Warranty. All lamps have a 2 year warranty. The warranty covers electrical faults.
It does not cover water damage or broken glass caused by the customer.
Accounts. To reset your password, use the Forgot password link on the login page.
Accounts with no login for 3 years are deleted. We email you 30 days before deletion.
"""
INDEX_FILE = Path(__file__).with_name(".rag_index.json")
MIN_SCORE = 0.45          # below this the best chunk is "not related" -> don't guess. Tune it!
CHUNK_SIZE, OVERLAP = 2, 1   # sentences per chunk, sentences shared with the next chunk


# STEP 1: chunk -- 2 sentences per chunk, each chunk repeats 1 sentence of the previous one
def chunk(text, size=CHUNK_SIZE, overlap=OVERLAP):
    sentences = [s.strip() + "." for s in text.replace("\n", " ").split(".") if s.strip()]
    step = size - overlap
    return [" ".join(sentences[i:i + size]) for i in range(0, len(sentences) - overlap, step)]


# STEP 2: build or load the index (only re-embed when the handbook OR the chunk settings changed)
def load_index():
    version = hashlib.sha256(f"{HANDBOOK}|{CHUNK_SIZE}|{OVERLAP}".encode()).hexdigest()
    if INDEX_FILE.exists():
        saved = json.loads(INDEX_FILE.read_text())
        if saved["version"] == version:
            print(f"  loaded {len(saved['chunks'])} chunks from {INDEX_FILE.name} (no embedding needed)")
            return saved["chunks"]
    texts = chunk(HANDBOOK)
    # nomic-embed-text works best with a task prefix: "search_document:" / "search_query:"
    vectors = embed([f"search_document: {t}" for t in texts])
    chunks = [{"id": f"c{i}", "text": t, "vector": v} for i, (t, v) in enumerate(zip(texts, vectors))]
    INDEX_FILE.write_text(json.dumps({"version": version, "chunks": chunks}))
    print(f"  embedded {len(chunks)} chunks and saved them to {INDEX_FILE.name}")
    return chunks


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


# STEP 3: retrieve the top k chunks
def retrieve(chunks, question, k=3):
    q = embed(f"search_query: {question}")[0]
    scored = sorted(((cosine(q, c["vector"]), c) for c in chunks), key=lambda x: -x[0])
    return scored[:k]


# STEP 4: answer with citations, or refuse when nothing is related
def answer(chunks, question):
    top = retrieve(chunks, question)
    print(f"  Q: {question}")
    for score, c in top:
        print(f"     {score:.2f} [{c['id']}] {c['text'][:70]}")
    if top[0][0] < MIN_SCORE:
        print("  A: I don't know -- nothing in the handbook is related. (no LLM call, no cost)\n")
        return
    context = "\n".join(f"[{c['id']}] {c['text']}" for _, c in top)
    system = ("Answer ONLY from the handbook chunks below. After each fact, cite the chunk id like [c3]. "
              "If the chunks do not contain the answer, say \"I don't know.\"\n" + context)
    print("  A:", ask(question, system=system, options={"temperature": 0}), "\n")


# STEP 5: measure retrieval -- does the right chunk come back in the top 3?
def evaluate(chunks):
    tests = [("How long until my refund money arrives?", "5 to 7 business days"),
             ("Is shipping free?", "over 50 euros"),
             ("My lamp got wet, is that covered?", "water damage"),
             ("I forgot my password", "Forgot password")]
    hits = 0
    for question, must_contain in tests:
        found = any(must_contain in c["text"] for _, c in retrieve(chunks, question))
        hits += found
        print(f"  {'HIT ' if found else 'MISS'} {question}")
    print(f"  hit rate: {hits}/{len(tests)}  <- measure this BEFORE changing chunk size or model")


def main():
    print("STEP 1: chunking")
    for i, c in enumerate(chunk(HANDBOOK)[:3]):
        print(f"  c{i}: {c}")
    print(f"  ... {len(chunk(HANDBOOK))} chunks total (each shares 1 sentence with the next)\n")

    print("STEP 2: index")
    chunks = load_index()

    print("\nSTEP 3+4: ask questions")
    answer(chunks, "Do I get my shipping costs back if the lamp arrived broken?")
    answer(chunks, "What is the CEO's favourite food?")

    print("STEP 5: retrieval eval")
    evaluate(chunks)


if __name__ == "__main__":
    main()

# Try: set CHUNK_SIZE = 4 and re-run. The index rebuilds by itself (the settings are part
# of its version). Compare the hit rate and the answers with CHUNK_SIZE = 2.
