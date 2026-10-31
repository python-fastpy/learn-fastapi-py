"""12 -- Put it together: a real FastAPI support bot on a free local model
=========================================================================

CONCEPT IN ONE LINE:
  Everything from 01-11 inside one small web API -- the shape of a real LLM backend.

   Browser / curl
        │  POST /ask {"question": "..."}
        ▼
   ┌──────────────────────────── FastAPI (this file) ─────────────────────────────┐
   │ 1. input guard            block injection, empty or huge input   (lesson 16) │
   │ 2. RAG                    embed question, pick top 2 docs         (lesson 14) │
   │ 3. prompt                 rules + docs in tags + "I don't know"   (lesson 07) │
   │ 4. call Ollama            temperature 0, num_predict 200          (03, 04)    │
   │ 5. check done_reason      "length" -> mark answer as cut off      (lesson 04) │
   │ 6. return JSON            answer + sources + token usage          (lesson 02) │
   └──────────────────────────────────────────────────────────────────────────────┘
        │
        ▼
   {"answer": "...", "sources": ["refunds"], "input_tokens": 210, "output_tokens": 31}

RUN (fastapi + uvicorn are added just for this command, nothing is installed in the project):
   uv run --with fastapi --with uvicorn uvicorn 19_fastapi_app:app --app-dir simple/ollama --port 8019

TRY IT:
   open  http://localhost:8019/docs   (FastAPI's built-in test page)
   or    curl -X POST localhost:8019/ask -H "Content-Type: application/json" -d "{\"question\": \"How long do refunds take?\"}"
"""

import math

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

OLLAMA = "http://localhost:11434"
CHAT_MODEL = "llama3.2"
EMBED_MODEL = "nomic-embed-text"

DOCS = {
    "refunds":  "Refunds are paid back to the original card within 5 to 7 business days.",
    "shipping": "We ship to the EU and the UK. Delivery takes 3 to 5 days.",
    "password": "To reset your password, click 'Forgot password' on the login page.",
    "support":  "Our support team is available Monday to Friday, 9:00 to 17:00 CET.",
}
DOC_VECTORS = None                     # built on the first request (indexing)

app = FastAPI(title="Support bot on llama3.2")


class Question(BaseModel):
    question: str


def embed(texts):
    """Text(s) -> list of vectors, one raw POST to Ollama's /api/embed."""
    body = {"model": EMBED_MODEL, "input": texts}          # input = one string or a list of strings
    resp = httpx.post(OLLAMA + "/api/embed", json=body, timeout=300)   # json= sends body as JSON
    resp.raise_for_status()                                # 4xx/5xx -> exception (e.g. 404 = model not pulled)
    return resp.json()["embeddings"]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


@app.post("/ask")
def ask_endpoint(body: Question):
    global DOC_VECTORS
    q = body.question.strip()

    # 1. input guard
    if not q or len(q) > 500:
        raise HTTPException(400, "question must be 1-500 characters")
    if "ignore all" in q.lower() or "system prompt" in q.lower():
        raise HTTPException(400, "question blocked by input guard")

    # 2. RAG: index once, then find the 2 closest docs
    if DOC_VECTORS is None:
        DOC_VECTORS = dict(zip(DOCS, embed(list(DOCS.values()))))
    q_vec = embed(q)[0]
    ranked = sorted(DOCS, key=lambda n: cosine(q_vec, DOC_VECTORS[n]), reverse=True)
    sources = ranked[:2]

    # 3. prompt with facts in tags
    docs_text = "\n".join(f"<doc id='{n}'>{DOCS[n]}</doc>" for n in sources)
    system = ("You are a support bot. Answer in 1-2 sentences ONLY from the docs. "
              "If they do not contain the answer, say \"I don't know.\"\n" + docs_text)

    # 4. call the model
    payload = {
        "model": CHAT_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": q}],
        "stream": False,
        "options": {"temperature": 0, "num_predict": 200},
    }
    resp = httpx.post(OLLAMA + "/api/chat", json=payload, timeout=300)
    resp.raise_for_status()
    r = resp.json()

    # 5 + 6. check and return
    return {
        "answer": r["message"]["content"].strip(),
        "cut_off": r.get("done_reason") == "length",
        "sources": sources,
        "input_tokens": r.get("prompt_eval_count"),
        "output_tokens": r.get("eval_count"),
    }
