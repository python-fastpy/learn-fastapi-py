# 02 — Stage 1: CRUD against a local JSON file

`Navigation: ← prev: 01-engineering-flow.md | next: 03-stage2-dynamodb.md →`

Get a working API in about two minutes. No AWS account, no credentials,
no Docker. Storage is a plain `books.json` file you can open in an editor.

---

## Why start here?

Because you learn one thing at a time. If you start with DynamoDB you're
debugging IAM permissions, region config, and `Decimal` conversion
*while* still figuring out your API shape. Starting with a file means
the only thing that can go wrong is your own code.

```
Stage 1 (here)              Stage 2 (next)
──────────────              ──────────────
books.json on disk    ──▶   DynamoDB table on AWS
no setup                     needs a table + permissions
open it in an editor         inspect via console/CLI
dev only                     production-ready
```

The API surface is identical in both. That's the point.

---

## Step 1 — Install

From the `project-book-store/` folder:

```bash
# Using uv (fast, recommended)
uv venv
uv pip install "fastapi==0.115.0" "uvicorn==0.30.6" \
               "pydantic==2.9.2" "pydantic-settings==2.5.2"

# Or plain pip
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux
pip install fastapi uvicorn pydantic pydantic-settings
```

Note `boto3` is **not** needed yet. `repository.py` only imports it
inside the `dynamodb` branch, so stage 1 runs without the AWS SDK
installed at all.

## Step 2 — Configure

```bash
cp .env.example .env      # copy .env.example .env   on Windows
```

The default is already what we want:

```
STORAGE=json
BOOKS_FILE=books.json
```

## Step 3 — Run

```bash
uvicorn main:app --reload
```

You should see:

```
[startup] storage=json env=local
INFO:     Uvicorn running on http://127.0.0.1:8000
```

That `[startup]` line comes from `main.py`'s lifespan handler — it's
confirming which backend got selected. Open
**http://localhost:8000/docs** for interactive Swagger UI that FastAPI
generates for free from the type hints.

---

## Step 4 — Exercise every endpoint

**Health check** (what AWS load balancers will poll later):

```bash
curl http://localhost:8000/health
# {"status":"ok","version":"1.0.0","storage":"json","env":"local"}
```

**List — empty at first:**

```bash
curl http://localhost:8000/books
# []
```

**Create** (note the `201` status and the server-assigned `id`):

```bash
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"title":"1984","author":"Orwell","price":9.99,"genre":"dystopia"}'
# {"title":"1984","author":"Orwell","price":9.99,"genre":"dystopia","id":"ff8286f4"}
```

**Look at the file** — this is the fun part of stage 1:

```bash
cat books.json
```
```json
{
  "ff8286f4": {
    "title": "1984",
    "author": "Orwell",
    "price": 9.99,
    "genre": "dystopia"
  }
}
```

**Get one** (use your own id):

```bash
curl http://localhost:8000/books/ff8286f4
```

**PATCH — partial update.** Only `price` is sent; everything else
survives:

```bash
curl -X PATCH http://localhost:8000/books/ff8286f4 \
  -H "Content-Type: application/json" \
  -d '{"price":14.99}'
# price is now 14.99, title/author/genre unchanged
```

**PUT — full replace.** Every field is required, and anything omitted is
*dropped*:

```bash
curl -X PUT http://localhost:8000/books/ff8286f4 \
  -H "Content-Type: application/json" \
  -d '{"title":"Dune","author":"Herbert","price":12.50}'
# genre is now null — it wasn't in the payload
```

> **PUT vs PATCH** is a classic interview question. PUT replaces the
> whole resource and is idempotent; PATCH merges a partial change. The
> implementation difference is `model_dump()` vs
> `model_dump(exclude_unset=True)` — see `repo_json.py`.

**Delete** (returns `204 No Content`, deliberately no body):

```bash
curl -i -X DELETE http://localhost:8000/books/ff8286f4
# HTTP/1.1 204 No Content
```

**Error paths** — worth checking explicitly:

```bash
curl -i http://localhost:8000/books/does-not-exist
# HTTP/1.1 404 Not Found   {"detail":"Book does-not-exist not found"}

curl -i -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" -d '{"title":"No author"}'
# HTTP/1.1 422 Unprocessable Entity  — Pydantic rejects it before your code runs

curl -i -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"title":"X","author":"Y","price":-5}'
# HTTP/1.1 422 — price has Field(gt=0)
```

## Step 5 — Run the tests

```bash
uv pip install "pytest==8.3.3" "httpx==0.27.2"
pytest test_books.py -v
```

All 14 should pass. They use a fake in-memory repository via
`dependency_overrides`, so they never touch `books.json` — meaning they
can't corrupt your data and don't need cleanup between tests.

---

## How the pieces fit

```
   HTTP request
        │
        ▼
   main.py                    endpoints — knows nothing about storage
        │  Depends(get_repository)
        ▼
   repository.py              picks an implementation from config
        │
        ▼
   repo_json.py               reads/writes books.json
        │
        ▼
   books.json
```

Read `repo_json.py` now — it's short, and two details are worth noticing:

**1. Atomic writes.** It writes to a temp file then `os.replace()`s it,
rather than opening `books.json` with `"w"`. Truncating the real file
first means a crash mid-write leaves you with a corrupted, half-written
file and no data. `os.replace` is atomic, so readers see either the
complete old file or the complete new one.

**2. `exclude_unset=True` in `patch()`.** Without it, unsent fields
arrive as `None` and would wipe existing values.

---

## Where this breaks (and why stage 2 exists)

This is genuinely fine for development and genuinely unusable in
production:

| Problem | What actually happens |
|---|---|
| **Lost updates** | Two simultaneous writes both read the file, both save their own copy — the second silently discards the first's change |
| **O(n) writes** | Adding one book to a 50,000-book file rewrites all 50,000 records |
| **No shared state** | On Lambda/Fargate you run many instances, each with its own local file and different data |
| **Ephemeral disk** | Lambda's filesystem is wiped when the execution environment recycles — your writes just vanish |
| **No queries** | "All books by Orwell" means loading everything into memory and filtering in Python |

DynamoDB fixes all five. The next doc migrates to it **without touching
`main.py`, `models.py`, or `test_books.py`.**

---

`Navigation: ← prev: 01-engineering-flow.md | next: 03-stage2-dynamodb.md →`
