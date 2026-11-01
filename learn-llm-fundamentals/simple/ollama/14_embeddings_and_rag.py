"""10 -- RAG: answer questions from YOUR documents
==================================================

CONCEPT IN ONE LINE:
  Turn documents into vectors (embeddings), find the ones closest to the question,
  and put them in the prompt.                                  (details: simple/10)

   INDEXING (once)                          QUERY (every question)
   ───────────────                          ─────────────────────
   docs ──▶ embed ──▶ vectors ──▶ store     question ──▶ embed ──▶ vector
                                               │
                                               ▼
                                    compare with every stored vector (cosine similarity)
                                               │
                                               ▼
                                    top 2 docs ──▶ prompt: "answer from these docs" ──▶ LLM

  WHY EMBEDDINGS: "money back" and "refund" share no words, but their vectors are
  close because they MEAN the same. Word matching (simple/10) cannot do that.
"""

import math

import httpx

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"
EMBED_MODEL = "nomic-embed-text"

DOCS = {
    "refunds":  "Refunds are paid back to the original card within 5 to 7 business days.",
    "shipping": "We ship to the EU and the UK. Delivery takes 3 to 5 days.",
    "password": "To reset your password, click 'Forgot password' on the login page.",
    "support":  "Our support team is available Monday to Friday, 9:00 to 17:00 CET.",
}


def embed(texts):
    """Text(s) -> list of vectors (each vector = a list of numbers)."""
    body = {"model": EMBED_MODEL, "input": texts}          # input = one string or a list of strings
    resp = httpx.post(OLLAMA + "/api/embed", json=body, timeout=300)   # json= sends body as JSON
    # ^ the same call in other APIs:
    #   API          | endpoint                 | sent            | vectors in reply
    #   -------------+--------------------------+-----------------+------------------------------------
    #   Ollama       | POST /api/embed          | "input": texts  | r["embeddings"]
    #   OpenAI       | POST /v1/embeddings      | "input": texts  | [d["embedding"] for d in r["data"]]
    #   Anthropic    | (not available)          | (not available) | (not available)
    #   Hugging Face | SentenceTransformer(...) | .encode(texts)  | the return value
    #   Anthropic has no embeddings API -- they point to Voyage AI.
    resp.raise_for_status()                                # 4xx/5xx -> exception (e.g. 404 = model not pulled)
    return resp.json()["embeddings"]


def cosine(a, b):
    """1.0 = same meaning direction, 0 = unrelated."""
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


def main():
    print("STEP 1: INDEXING -- embed every doc once")
    names = list(DOCS)
    vectors = embed([DOCS[n] for n in names])
    print(f"  {len(vectors)} docs -> vectors of {len(vectors[0])} numbers each")
    print(f"  first 5 numbers of 'refunds': {[round(x, 3) for x in vectors[0][:5]]}")

    question = "How long until I get my money back?"
    print(f"\nSTEP 2: QUERY -- {question!r}")
    q_vec = embed(question)[0]
    scores = sorted(((cosine(q_vec, v), n) for n, v in zip(names, vectors)), reverse=True)
    for score, name in scores:
        print(f"  {name:<9} similarity {score:.2f}  {'█' * int(score * 30)}")
    print(f"  -> {scores[0][1]!r} is closest. (With nomic-embed-text this should be 'refunds',")
    print("     although the question never says 'refund' -- the vectors match on MEANING.)")

    print("\nSTEP 3: put the top 2 docs in the prompt and ask the LLM")
    top = [n for _, n in scores[:2]]
    context = "\n".join(f"[{n}] {DOCS[n]}" for n in top)
    system = ("Answer ONLY from the docs below and cite the doc id like [refunds]. "
              "If the docs do not answer it, say \"I don't know.\"\n" + context)
    print("  docs used:", top)
    body = {
        "model": CHAT_MODEL,
        "messages": [{"role": "system", "content": system},     # the docs go in the system message
                     {"role": "user", "content": question}],
        "stream": False,
        "options": {"temperature": 0},
        # ^ the same settings in other APIs:
        #   API          | system message          | stream          | temperature
        #   -------------+-------------------------+-----------------+------------------------
        #   Ollama       | {"role": "system", ...} | "stream": False | "temperature": 0
        #   OpenAI       | {"role": "system", ...} | "stream": false | "temperature": 0  (0-2)
        #   Anthropic    | "system": system        | "stream": false | "temperature": 0  (0-1)
        #   Hugging Face | -                       | -               | do_sample=False
        #   Ollama wraps temperature in "options"; Anthropic puts "system" at top level, not in messages.
    }
    resp = httpx.post(OLLAMA + "/api/chat", json=body, timeout=300)
    # ^ the same call in other APIs:
    #   API       | endpoint
    #   ----------+--------------------------
    #   Ollama    | POST /api/chat
    #   OpenAI    | POST /v1/chat/completions
    #   Anthropic | POST /v1/messages
    resp.raise_for_status()
    answer = resp.json()["message"]["content"].strip()
    # ^ the same field in other APIs:
    #   API       | reply text
    #   ----------+--------------------------------------
    #   Ollama    | r["message"]["content"]
    #   OpenAI    | r["choices"][0]["message"]["content"]
    #   Anthropic | r["content"][0]["text"]
    print("  answer   :", answer)


if __name__ == "__main__":
    main()

# Try: ask "Can I pay with PayPal?" -- nothing in DOCS covers it, so it should say I don't know.
