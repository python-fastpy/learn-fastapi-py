"""Lesson 01 -- RAG: Chunking, Embeddings, and Retrieval
==========================================================

WHY THIS MATTERS:
  Every lesson in learn-langgraph and learn-mcp assumes the LLM already
  knows what it needs to know, or gets it via a tool call with structured
  args (search_web(query="...")). RAG (Retrieval-Augmented Generation) is
  the pattern for when the answer lives in *unstructured text* you own --
  PDFs, wiki pages, past articles -- too much to paste into a prompt, and
  not covered by any tool's fixed parameters. You retrieve the relevant
  slice first, then let the LLM answer using only that slice.

  This is the one core AI-app skill missing from the rest of this repo.

WHAT YOU'LL LEARN:
  1. Chunking: why you can't embed a whole document, and how chunk size /
     overlap trade off context vs. precision
  2. Embeddings: turning text into a vector so "similar meaning" becomes
     "close in space" -- and why fixed-size chunks matter for that
  3. Cosine similarity: the actual math behind "semantic search"
  4. A minimal vector store: add(), search() -- what Pinecone/pgvector/
     FAISS do underneath, minus the disk persistence and indexing tricks
  5. The full RAG loop: question -> embed -> retrieve top-k chunks ->
     stuff into the prompt -> LLM answers *grounded in retrieved text*

Concepts:
  - Chunking: splitting a document into overlapping windows small enough
    to embed meaningfully and retrieve precisely
  - Embedding: a fixed-length vector representing a text's meaning
  - Cosine similarity: cos(theta) between two vectors -- 1.0 = identical
    direction (meaning), 0.0 = unrelated, -1.0 = opposite
  - Vector store: a collection of (vector, text, metadata) you can search
    by "give me the k closest vectors to this query vector"
  - Top-k retrieval: taking only the k most relevant chunks, not everything
  - Grounding: telling the LLM "answer ONLY using this retrieved text" so
    it can't fall back on (possibly wrong) memorized knowledge
  - Retrieval failure modes: chunk boundary splits an answer in half,
    query wording doesn't match document wording, top-k too small

  ** EMBEDDING MODEL NOTE: This lesson's `embed()` is a deterministic,
  dependency-free stand-in (character n-gram hashing into a fixed vector)
  so the lesson runs with zero setup. It captures *some* signal (shared
  substrings pull vectors together) but nowhere near what a real embedding
  model captures (synonyms, paraphrase, word order). In production you'd
  call a real embedding model (OpenAI text-embedding-3, Azure
  text-embedding-ada-002, Bedrock Titan Embeddings) -- same interface
  (text in, fixed-length vector out), swap the function, nothing else in
  this file changes. The TR Orchestrator profile used elsewhere in this
  repo (llm_helper.py) only exposes chat models, not an embeddings
  deployment, which is why this lesson doesn't wire one up. **

Flow:
  Document                     Query: "What was Q2 revenue growth?"
     |                                     |
     v                                     v
  +--------+                        +-----------+
  | Chunk  |  (split + overlap)     |  Embed    |
  +---+----+                        +-----+-----+
      |                                   |
      v                                   |
  +--------+                              |
  | Embed  |  each chunk -> vector         |
  +---+----+                              |
      |                                   |
      v                                   v
  +----------------------------------------------+
  |            Vector Store (in-memory)          |
  |  search(query_vector, k=3) -> top-3 chunks    |
  +---------------------+------------------------+
                        |
                        v
              +-------------------+
              | Prompt:           |
              | "Using ONLY this  |
              |  text: <chunks>,  |
              |  answer: <query>" |
              +---------+---------+
                        |
                        v
                    LLM answer
              (grounded, or "I don't know"
               if chunks don't cover it)

  Maps to (production shape, not this repo's code):
    A skill's local knowledge base (e.g. style guides, past corrections)
    would follow this exact loop: chunk once at ingest time, embed once,
    store in a vector DB, then retrieve+ground per query at request time.

PREREQUISITES: None (pure Python + optional .env for the real LLM step)

Run:  uv run python 01_rag_embeddings_and_retrieval.py

EXPECTED OUTPUT (mock mode -- no .env needed):
  === Step 1: Chunking ===
    Document split into 3 chunks (size=220, overlap=40)

  === Step 2: Embedding chunks ===
    Embedded 3 chunks into 256-dim vectors

  === Step 3: Retrieval ===
    Query: 'What was Q2 revenue growth?'
    Top 2 chunks by cosine similarity:
      [0.23] "Acme Corp released its Q2 earnings report today. In Q2, revenue grew 1..."
      [0.15] "momentum in enterprise contracts. The CFO noted that headcount grew 8%..."

  === Step 4: Grounded answer (mock LLM -- no .env) ===
    Retrieved context handed to the LLM. Without .env, this lesson prints
    the grounding prompt instead of a live answer.

  === Failure mode demo ===
    Query: 'What color is the sky on Mars?'
    Every chunk scores 0.00 -- nothing in the document shares any content
    word with the query. Compare to the real match's 0.23: that gap is the
    signal a `min_score` threshold would use to say "don't even ask the LLM"
"""

import math
import os
import re
import zlib
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


# ============================================================================
# STEP 1: Chunking
# ============================================================================
# Why chunk at all? Two reasons:
#   1. Embedding models have an input size limit.
#   2. Even without that limit, embedding a whole 10-page doc into one
#      vector averages away everything -- you couldn't tell a query about
#      page 1 from a query about page 9. Smaller chunks = more precise
#      retrieval, at the cost of less context per chunk.
# Overlap prevents an answer from being split exactly across a chunk
# boundary (e.g. "revenue grew 15%" ending one chunk, "year over year"
# starting the next -- neither chunk alone answers the question well).

def chunk_text(text: str, size: int = 220, overlap: int = 40) -> list[str]:
    """Split text into overlapping windows of `size` characters."""
    text = re.sub(r"\s+", " ", text.strip())
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = end - overlap  # step back by `overlap` so windows overlap
    return chunks


# ============================================================================
# STEP 2: Embeddings (deterministic stand-in -- see docstring note)
# ============================================================================
# Real embedding models are trained neural nets. This is the "hash trick":
# every content word hashes into one of 64 buckets, and we count how often
# each bucket fires (weighted so rarer, more distinctive words count more
# than common ones). Texts that share topic words ("revenue", "quarter")
# land in the same buckets and end up with vectors pointing in similar
# directions -- crude compared to a real model (no synonyms, no word
# order, no paraphrase understanding), but enough to demonstrate
# retrieval mechanics without downloading one.

VECTOR_DIM = 256

_STOPWORDS = {
    "the", "a", "an", "in", "on", "at", "of", "to", "for", "and", "or",
    "is", "was", "were", "are", "be", "it", "its", "this", "that", "with",
    "as", "by", "from", "up", "also", "today",
}


def embed(text: str) -> list[float]:
    """Text -> fixed-length vector. Swap this for a real embedding model's
    API call in production; every other function in this file is agnostic
    to how the vector was produced."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    words = [w for w in words if w not in _STOPWORDS]
    vec = [0.0] * VECTOR_DIM
    for w in words:
        # zlib.crc32 (not the builtin hash()) -- Python randomizes str hash()
        # per-process for security, which would make bucket assignment (and
        # therefore every similarity score below) different on every run.
        bucket = zlib.crc32(w.encode()) % VECTOR_DIM
        # Weight rarer (longer) words more -- a cheap stand-in for the
        # inverse-document-frequency weighting real search systems use.
        vec[bucket] += 1.0 + len(w) / 10
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]  # unit-normalize so cosine sim = dot product


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """cos(theta) between two vectors. Both are already unit-normalized
    above, so this is just the dot product -- but written out in full so
    the formula is visible even if you skip the normalization step."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


# ============================================================================
# STEP 3: A minimal vector store
# ============================================================================
# This is what Pinecone / pgvector / FAISS give you, stripped of indexing
# (they use approximate nearest-neighbor structures so search doesn't have
# to be O(n) over every vector -- fine for a lesson with 4 chunks, not fine
# for a million).

@dataclass
class VectorStore:
    entries: list[tuple[list[float], str]] = field(default_factory=list)

    def add(self, text: str) -> None:
        self.entries.append((embed(text), text))

    def search(self, query: str, k: int = 2) -> list[tuple[float, str]]:
        """Return the top-k (score, text) pairs by cosine similarity."""
        query_vec = embed(query)
        scored = [(cosine_similarity(query_vec, vec), text) for vec, text in self.entries]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[:k]


# ============================================================================
# STEP 4: The grounded prompt (what actually goes to the LLM)
# ============================================================================

def build_grounded_prompt(query: str, retrieved_chunks: list[str]) -> str:
    context = "\n\n".join(f"[chunk {i+1}] {c}" for i, c in enumerate(retrieved_chunks))
    return (
        "Answer the question using ONLY the text in the chunks below. "
        "If the chunks don't contain the answer, say so -- do not use "
        "outside knowledge.\n\n"
        f"{context}\n\n"
        f"Question: {query}\n"
        "Answer:"
    )


# ============================================================================
# Demo
# ============================================================================

DOCUMENT = """
Acme Corp released its Q2 earnings report today. In Q2, revenue grew 15%
year over year, driven by strong demand in the cloud division. Operating
margin improved to 22%, up from 18% in the prior quarter. The company
also announced a new product line launching in Q3, targeting small and
medium businesses. Management raised full-year guidance, citing continued
momentum in enterprise contracts. The CFO noted that headcount grew 8%
in Q2, primarily in engineering and sales roles. Customer churn remained
flat at 4%, in line with historical averages.
"""


async def main():
    print("=== Step 1: Chunking ===")
    chunks = chunk_text(DOCUMENT, size=220, overlap=40)
    print(f"    Document split into {len(chunks)} chunks (size=220, overlap=40)")
    for i, c in enumerate(chunks):
        print(f"    [{i}] {c[:70]}...")
    print()

    print("=== Step 2: Embedding chunks ===")
    store = VectorStore()
    for c in chunks:
        store.add(c)
    print(f"    Embedded {len(chunks)} chunks into {VECTOR_DIM}-dim vectors")
    print()

    print("=== Step 3: Retrieval ===")
    query = "What was Q2 revenue growth?"
    print(f"    Query: '{query}'")
    results = store.search(query, k=2)
    print("    Top 2 chunks by cosine similarity:")
    for score, text in results:
        print(f"      [{score:.2f}] \"{text[:70]}...\"")
    print()

    print("=== Step 4: Grounded answer ===")
    retrieved_texts = [text for _, text in results]
    prompt = build_grounded_prompt(query, retrieved_texts)

    if os.getenv("ORCHESTRATOR_ENDPOINT"):
        from llm_helper import get_llm
        llm = get_llm(model="gpt-4o", temperature=0.0)
        response = await llm.ainvoke([{"role": "user", "content": prompt}])
        print(f"    LLM answer: {response.content}")
    else:
        print("    No .env -- printing the grounding prompt instead of calling an LLM:")
        print("    " + "-" * 60)
        for line in prompt.splitlines():
            print(f"    {line}")
        print("    " + "-" * 60)
    print()

    print("=== Failure mode demo: query with no matching chunk ===")
    bad_query = "What color is the sky on Mars?"
    bad_results = store.search(bad_query, k=2)
    print(f"    Query: '{bad_query}'")
    print("    Top matches (all low-confidence -- nothing in the doc covers this):")
    for score, text in bad_results:
        print(f"      [{score:.2f}] \"{text[:70]}...\"")
    print("    A grounded prompt built from these chunks should make the LLM say")
    print("    'not in the provided text' -- retrieval can't invent an answer that")
    print("    isn't there, which is the whole point: RAG can't hide a bad match,")
    print("    it just retrieves the closest thing and lets the LLM (or you) judge it.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

    # -- Key takeaway --------------------------------------------------------
    # RAG is three separable pieces, each independently swappable:
    #   1. CHUNKING   -- how you split source text (fixed-size here; production
    #      often splits on headings/paragraphs first, falling back to fixed-size)
    #   2. EMBEDDING   -- how you turn text into a vector (hash trick here;
    #      a real embedding model in production)
    #   3. VECTOR STORE -- how you index and search vectors (linear scan here;
    #      FAISS/Pinecone/pgvector with approximate nearest-neighbor in production)
    # The RAG *loop* (embed query -> retrieve -> ground the prompt) stays the
    # same regardless of which implementation you plug into each piece.
    #
    # -- Exercise -------------------------------------------------------------
    # 1. Change `size`/`overlap` in chunk_text() and see how retrieval quality
    #    changes for the "Q2 revenue growth" query.
    # 2. Add a second document about a different company and confirm the
    #    vector store retrieves chunks from the RIGHT document for each query.
    # 3. Add a `min_score` threshold to VectorStore.search() that returns
    #    nothing below it -- simulating "no confident match, don't even ask
    #    the LLM, just say I don't know."
    # 4. Combine with lesson 16 (agent-vs-mcp): wrap VectorStore.search() as
    #    an MCP tool (`@mcp.tool async def retrieve(query: str) -> list[str]`)
    #    so a LangGraph agent can call it like any other tool.
