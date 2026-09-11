# Book Store API — from a JSON file to AWS

A complete, runnable FastAPI CRUD project that grows in three stages:

```
  STAGE 1                 STAGE 2                  STAGE 3
  JSON file       ──▶      DynamoDB        ──▶      Deployed on AWS
  (no AWS, 2 min)          (real database)          (CloudFormation)
```

**The point of this project:** `main.py` and `models.py` are written
**once** and never change. Only the storage implementation and the
environment change. That's what makes the migration a config change
instead of a rewrite — and it's the single most useful habit here.

This folder is self-contained. You don't need anything else in the repo.

---

## Read in this order

| Doc | What you'll do |
|---|---|
| [01-engineering-flow.md](docs/01-engineering-flow.md) | Understand the standard flow + the pre-deploy checklist. **Start here.** |
| [02-stage1-json-file.md](docs/02-stage1-json-file.md) | Get a working CRUD API in ~2 minutes, no AWS account |
| [03-stage2-dynamodb.md](docs/03-stage2-dynamodb.md) | Migrate to DynamoDB (offline first, then real AWS) |
| [04-deploy-lambda.md](docs/04-deploy-lambda.md) | Deploy serverlessly via CloudFormation — **free tier, start with this** |
| [05-deploy-fargate.md](docs/05-deploy-fargate.md) | Deploy as a container via CloudFormation — ⚠ ~$25/mo |
| [06-operations-and-teardown.md](docs/06-operations-and-teardown.md) | Logs, alarms, rollback, cost, **and how to delete it all** |

---

## 60-second start

```bash
cd project-book-store

uv venv
uv pip install "fastapi==0.115.0" "uvicorn==0.30.6" \
               "pydantic==2.9.2" "pydantic-settings==2.5.2"

cp .env.example .env          # copy .env.example .env  (Windows)
uvicorn main:app --reload
```

Then open **http://localhost:8000/docs**, or:

```bash
curl -X POST http://localhost:8000/books \
  -H "Content-Type: application/json" \
  -d '{"title":"1984","author":"Orwell","price":9.99}'

curl http://localhost:8000/books
cat books.json                # your data, on disk
```

Run the tests (no AWS needed):

```bash
uv pip install "pytest==8.3.3" "httpx==0.27.2"
pytest test_books.py -v       # 14 passed — API behaviour
```

Stage 2 adds offline tests for the DynamoDB layer (needs `boto3`, but
makes no AWS calls):

```bash
uv pip install "boto3==1.35.36"
pytest -v                     # 23 passed — both files
```

---

## Files

```
project-book-store/
│
├── README.md              this file
├── pyproject.toml         pinned dependencies
├── Dockerfile             for the Fargate path
├── .env.example           config template — copy to .env
│
├── models.py              Pydantic models        ← never changes
├── main.py                FastAPI endpoints      ← never changes
├── config.py              env-driven config (the STORAGE switch)
├── repository.py          ★ the storage interface — read this one
├── repo_json.py           stage 1: JSON file
├── repo_dynamo.py         stage 2: DynamoDB via boto3
├── lambda_handler.py      Mangum adapter (Lambda path only)
├── test_books.py          14 tests — API behaviour, no AWS required
├── test_repo_dynamo.py     9 tests — Decimal conversion + interface parity
│
├── infra-lambda.yaml      CloudFormation: DynamoDB + Lambda + API Gateway + IAM
├── infra-fargate.yaml     CloudFormation: DynamoDB + ECS + ALB + IAM
│
└── docs/                  the six walkthroughs above
```

`books.json` appears when you first run stage 1 (gitignored).

---

## How the swap works

```
   HTTP request
        │
        ▼
   main.py ───────────── knows only about BookRepository
        │  Depends(get_repository)
        ▼
   repository.py ─────── reads STORAGE from config, picks one:
        │
        ├── STORAGE=json ─────▶ repo_json.py ─────▶ books.json
        │
        └── STORAGE=dynamodb ─▶ repo_dynamo.py ───▶ DynamoDB table
```

Local development sets `STORAGE=json` in `.env`. Both CloudFormation
templates set `STORAGE=dynamodb` as an environment variable on the
deployed Lambda/container. Same code, both times.

---

## Which deploy path?

| | Lambda (doc 04) | Fargate (doc 05) |
|---|---|---|
| Idle cost | **~$0** | ~$25/mo (the ALB) |
| Cold starts | ~1-3s first request | none |
| Max request duration | 15 min | unlimited |
| Best for | spiky/low traffic, simple APIs | steady traffic, long jobs, websockets |

**Start with Lambda.** It's free at idle and a better fit for this API.
Do Fargate to learn containers, then tear it down.

---

## API

| Method | Path | Returns |
|---|---|---|
| `GET` | `/health` | 200 — liveness (what load balancers poll) |
| `GET` | `/books` | 200 — list all |
| `GET` | `/books/{id}` | 200, or 404 |
| `POST` | `/books` | **201** — created, with server-assigned `id` |
| `PUT` | `/books/{id}` | 200 — full replace, or 404 |
| `PATCH` | `/books/{id}` | 200 — partial merge, or 404 |
| `DELETE` | `/books/{id}` | **204** — no body, or 404 |

Invalid input returns **422** with per-field detail, courtesy of Pydantic.

---

## Verification status

What was actually checked when this project was written:

- ✅ All 9 `.py` files pass `python -m py_compile`
- ✅ `pytest` — **23/23 passing** (14 API behaviour + 9 DynamoDB-layer)
- ✅ Stage 1 run live with uvicorn: full create → list → get → patch →
  delete cycle verified, plus 404 and 422 paths, and `books.json`
  confirmed created/mutated/emptied on disk
- ✅ `repo_dynamo.py` imports cleanly with boto3, and its
  `Decimal`↔`float` conversion is covered by real tests (including
  proof that `Decimal(str(x))` avoids the binary-float noise that
  `Decimal(x)` introduces)
- ✅ Both CloudFormation templates pass real
  `aws cloudformation validate-template` — which is also how the
  required `--capabilities CAPABILITY_NAMED_IAM` flag was confirmed
- ⚠️ **Not executed:** actual AWS deployment (needs an account and
  incurs cost) and live DynamoDB reads/writes. The DynamoDB repository
  is verified by import, unit tests, and interface parity with the
  JSON one — but no request ever hit a real table. Use doc 03's
  DynamoDB Local option to exercise it end-to-end for free.

---

## ⚠ Cost reminder

The Lambda path is effectively free at tutorial scale. **The Fargate
path is not** — the load balancer alone is ~$16-18/month whether or not
anyone uses your API.

When you're finished:

```bash
aws cloudformation delete-stack --stack-name book-store-lambda-dev
aws cloudformation delete-stack --stack-name book-store-fargate-dev
```

Full teardown (including the S3 bucket and ECR images CloudFormation
doesn't own) is in
[06-operations-and-teardown.md](docs/06-operations-and-teardown.md).
