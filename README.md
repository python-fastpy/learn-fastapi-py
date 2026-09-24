# Python & FastAPI Learning Reference

A hands-on learning repo with condensed Python and FastAPI examples. Each file covers a topic end-to-end with runnable code, a cheat sheet, and a detailed reference section with beginner-friendly curl examples and arrow diagrams.

**Live Site:** [https://python-fastpy.github.io/learn-fastapi-py/](https://python-fastpy.github.io/learn-fastapi-py/)

---

## Quick Start with uv

[uv](https://docs.astral.sh/uv/) is a fast Python package manager (replaces pip, venv, pyenv). Install it first:

```bash
# Install uv
# Windows (PowerShell):
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
# Mac/Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Set Up a Project

```bash
# Create a new project (creates pyproject.toml + .venv automatically)
uv init my-project
cd my-project

# Or init in current directory
uv init
```

### Install & Run Python

```bash
# Install a specific Python version
uv python install 3.12

# Run a script (uv auto-creates .venv if needed)
uv run python script.py

# Run FastAPI dev server
uv run fastapi dev main.py
```

### Manage Dependencies

```bash
# Add a package (adds to pyproject.toml + installs)
uv add fastapi
uv add uvicorn
uv add pydantic

# Add multiple at once
uv add httpx pytest boto3

# Add dev-only dependency (not needed in production)
uv add --dev pytest ruff mypy

# Remove a package
uv remove httpx

# Sync — install everything from pyproject.toml (like npm install)
uv sync

# See what's installed
uv pip list
```

### How It Works

```
  uv init
    → creates pyproject.toml     (like package.json — lists your dependencies)
    → creates .venv/             (isolated Python environment — like node_modules)
    → creates uv.lock            (exact versions — like package-lock.json)

  uv add fastapi
    → adds "fastapi" to pyproject.toml [dependencies]
    → installs it into .venv/
    → updates uv.lock with exact version

  uv run python app.py
    → runs using .venv Python (no need to activate venv manually)
```

### pyproject.toml (what it looks like)

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "pydantic>=2.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.5.0",
]
```

### uv vs pip Comparison

| Task | pip (old way) | uv (new way) |
|------|--------------|--------------|
| Create venv | `python -m venv .venv` | `uv init` (auto) |
| Activate venv | `.venv\Scripts\activate` | not needed — `uv run` handles it |
| Install package | `pip install fastapi` | `uv add fastapi` |
| Install from file | `pip install -r requirements.txt` | `uv sync` |
| Run script | `python app.py` | `uv run python app.py` |
| Lock versions | `pip freeze > requirements.txt` | automatic (`uv.lock`) |

---

## Flow-to-Learning Map

See [flow_to_learning_map.txt](../reuters-ai_assistant/reuters-assistant_backend/flow_to_learning_map.txt) — maps every step of the production orchestrator flow (HTTP POST → MCP discovery → tool execution → interrupt → response) to the specific learning file that covers it. Covers all steps from both `flow_to_build_mcp_tools.txt` and `flow_after_build_mcp_tools.txt`.

---

## What's Inside

### FastAPI (`fastapi/`)

| File | Topics |
|------|--------|
| `01-crud.py` | Raw-dict CRUD, Body/Query/Path/Header/Cookie/Form/File params (no Pydantic yet) |
| `02-pydantic.py` | BaseModel, Field validation, validators, nested models, response_model, model_dump, BaseSettings (env config) |
| `03-routes.py` | APIRouter, Annotated style, response types, Depends intro, exception handlers, BackgroundTasks |
| `04-headers-auth-request-anatomy.py` | HTTP request/response anatomy, auth headers, API keys, OAuth2PasswordBearer, security headers |
| `05-async-await.py` | async/await, gather, create_task, Semaphore, Lock, Event, Queue, shield, httpx |
| `06-middleware-cors-caching.py` | CORS, GZip, custom middleware, Cache-Control, ETag, rate limiting |
| `07-lifespan.py` | Startup/shutdown, app.state, DI over shared resources, background jobs, testing lifespan |
| `08-session.py` | Cookie/Redis/JWT session strategies + comparison table (full lifespan deep-dive: see `07-lifespan.py`) |
| `09-testing-with-pytest.py` | TestClient, dependency overrides, async testing (httpx+ASGITransport), validation-error assertions |

### Book Store Project (`project-book-store/`)

A self-contained, **runnable** end-to-end project: build a FastAPI CRUD
API against a local JSON file, migrate it to DynamoDB, then deploy to
AWS via CloudFormation (both Lambda and ECS Fargate paths). Start at
[`project-book-store/README.md`](project-book-store/README.md).

| File | Topics |
|------|--------|
| `repository.py` | The storage interface (`BookRepository` protocol) that makes the migration a config change |
| `repo_json.py` | Stage 1 — JSON-file persistence, atomic writes, why it's dev-only |
| `repo_dynamo.py` | Stage 2 — boto3 DynamoDB, `Decimal` conversion, `ConditionExpression`, Scan pagination |
| `main.py` / `models.py` | FastAPI endpoints + Pydantic models — identical across both stages |
| `config.py` | `BaseSettings` env config; the `STORAGE=json\|dynamodb` switch |
| `test_books.py` / `test_repo_dynamo.py` | 23 tests — API behaviour via `dependency_overrides`, plus `Decimal` conversion and interface parity. No AWS needed |
| `infra-lambda.yaml` | CloudFormation: DynamoDB + Lambda (Mangum) + API Gateway + least-privilege IAM |
| `infra-fargate.yaml` | CloudFormation: DynamoDB + ECS Fargate + ALB + chained security groups + IAM |
| `docs/01-engineering-flow.md` | The standard flow: requirements → local → abstract → config → test → IaC → deploy → observe |
| `docs/02-stage1-json-file.md` | Walkthrough: working CRUD API in ~2 minutes |
| `docs/03-stage2-dynamodb.md` | Walkthrough: migrate to DynamoDB (DynamoDB Local, then real AWS) |
| `docs/04-deploy-lambda.md` | Walkthrough: serverless deploy, packaging gotchas, cold starts |
| `docs/05-deploy-fargate.md` | Walkthrough: Docker → ECR → ECS, two IAM roles, rolling deploys |
| `docs/06-operations-and-teardown.md` | Logs, alarms, rollback, cost comparison, CI/CD outline, full teardown |

### AI Advanced (`learn-ai-advanced/`)

The AI-app skills not covered by `learn-langgraph`/`learn-mcp`/`learn-copilotkit`:
retrieval, quality testing, observability, and defense against untrusted content.
All 4 lessons run with zero setup (deterministic mocks); `.env` upgrades 3 of
them to a real LLM call for comparison. Start at
[`learn-ai-advanced/README.md`](learn-ai-advanced/README.md).

| File | Topics |
|------|--------|
| `01_rag_embeddings_and_retrieval.py` | Chunking, embeddings, cosine similarity, a minimal vector store, grounded prompts |
| `02_evals_and_llm_judge.py` | Golden datasets, keyword/fact coverage, LLM-as-judge, regression diffing |
| `03_observability_and_tracing.py` | Spans, trace trees, latency waterfalls, token/cost tracking, critical path |
| `04_guardrails_and_prompt_injection.py` | Output validation + retry, PII redaction, direct/indirect prompt injection, data/instruction separation |

### Python (`python/`)

| File | Topics |
|------|--------|
| `data-types.py` | Numbers, strings, lists, dicts, sets, tuples, type conversions |
| `functions.py` | Args, kwargs, closures, generators, lambda, decorators |
| `oops.py` | Classes, inheritance, MRO, dunder methods, ABC, dataclasses |
| `decorators.py` | Function/class decorators, chaining, functools.wraps |
| `annotations.py` | Type hints, Optional, Union, TypeVar, Protocol, generics |
| `typeddict.py` | TypedDict, NotRequired, Required, nested, inheritance, JSON patterns |
| `exception-handling.py` | try/except, custom exceptions, context managers, ExceptionGroup |
| `async-await.py` | asyncio, gather, create_task, Semaphore, Lock, Event, Queue, TaskGroup |
| `file-handling.py` | File I/O, CSV, JSON, pathlib, tempfile, shutil |

### DSA (`DSA/`)

| File | Topics |
|------|--------|
| `01-big-o-complexity.js` | Big-O/Omega/Theta, complexity chart, nested loops, amortized analysis |
| `02-arrays-objects-sets-maps.js` | Array, Object, Set, Map, master Big-O table, when-to-use decision tree |
| `03-searching-algorithms.js` | Linear, binary (iterative/recursive), jump, interpolation, two-pointer, sliding window |
| `04-sorting-algorithms.js` | Bubble, selection, insertion, quick, merge, counting sort, TimSort internals |
| `05-stacks.js` | Stack variants (array/object/closure/WeakMap/linked-list), MinStack, balanced parens, infix-to-postfix, monotonic stack |
| `06-queues.js` | Queue, QueueObj (O(1)), CircularQueue |
| `07-linked-lists.js` | Singly/doubly linked list, stack/queue via linked list |
| `08-hash-tables.js` | Hash table with chaining, collision handling |
| `09-trees-and-tries.js` | Binary search tree (insert/search/traversals/delete), Trie |
| `10-heaps-and-priority-queue.js` | MinHeap, PriorityQueue |
| `11-graphs.js` | Adjacency list, BFS, DFS (recursive + iterative) |
| `12-lru-cache.js` | LRU cache via Map |
| `13-coding-problems-basic.js` | Reverse number/string, palindrome, fibonacci, factorial, primes, anagrams, dedupe, flatten, shuffle |
| `14-coding-problems-intermediate.js` | Two/Three Sum, valid parentheses, Kadane's, sliding window, two-pointer, MinStack, daily temperatures |
| `15-coding-problems-advanced.js` | Climbing stairs, coin change, house robber (DP), merge intervals, product except self |

### System Design (`system-design/`)

Plain Markdown, ELI5 analogy first then real technical depth (same
non-code style as `github/*.md`) — not wired into the HTML viewer.

| File | Topics |
|------|--------|
| `01-what-is-system-design.md` | Functional vs non-functional requirements, back-of-envelope estimation, interview flow |
| `02-scalability.md` | Vertical vs horizontal scaling, statelessness |
| `03-load-balancing.md` | Routing algorithms, L4 vs L7, health checks |
| `04-caching.md` | Cache layers, cache-aside/write-through/write-back, invalidation, LRU eviction |
| `05-databases-sql-vs-nosql.md` | ACID, key-value/document/column/graph stores, when to use which |
| `06-database-scaling.md` | Replication (leader/follower), sharding, indexing |
| `07-cap-theorem-and-consistency.md` | CAP theorem, strong vs eventual consistency, read-your-writes |
| `08-message-queues-and-async.md` | Pub-sub vs point-to-point, delivery guarantees, event-driven design |
| `09-microservices-vs-monolith.md` | Trade-offs, API Gateway responsibilities |
| `10-rate-limiting.md` | Token/leaky bucket, fixed vs sliding window, where state lives |
| `11-cdn-and-proxies.md` | CDN edge caching, forward vs reverse proxy, geo-routing |
| `12-consistent-hashing.md` | The ring, virtual nodes, minimal remapping on scale change |
| `13-availability-and-failover.md` | SLA/SLO/SLI, nines, active-passive vs active-active, circuit breakers |
| `14-monitoring-and-observability.md` | Metrics/logs/traces, alerting, health checks |
| `15-case-study-url-shortener.md` | End-to-end: ID generation, read-path caching |
| `16-case-study-rate-limiter.md` | End-to-end: distributed rate limiter, fail-open vs fail-closed |
| `17-case-study-chat-app.md` | End-to-end: WebSockets, delivery/ordering, presence |
| `18-case-study-news-feed.md` | End-to-end: fan-out-on-write vs fan-out-on-read, celebrity problem |

### Each `fastapi/`/`python/` file has 3 sections:

1. **Content** - Runnable code examples with explanations
2. **Cheat Sheet** - Quick-reference summary of all concepts
3. **Detailed Reference** - Beginner examples with curl commands and arrow diagrams showing data flow

`DSA/` files are plain runnable scripts (`node <file>.js`) ordered from
beginner to advanced concepts, each with inline ASCII diagrams, Big-O
notes, and INTERVIEW/GOTCHA callouts instead of the 3-section split above.

---

## HTML Viewer

An interactive browser-based viewer with:
- Sidebar navigation by folder/file
- Split view: Content on left, Cheat Sheet + Reference on right
- Syntax highlighting, resizable panels
- Search and keyboard shortcuts (`/` to search, `Esc` to clear)

---

## Local Setup

```bash
# Clone the repo
git clone https://github.com/python-fastpy/learn-fastapi-py.git
cd learn-fastapi-py

# Build the viewer data
python viewer/build.py

# Open in browser
# Windows:
start viewer/index.html
# Mac:
open viewer/index.html
# Linux:
xdg-open viewer/index.html
```

After editing any `.py` file, re-run `python viewer/build.py` to update the viewer.

---

## GitHub Pages Deployment

The site auto-deploys on every push to `main` via GitHub Actions.

### One-time setup (if not already done):

1. Go to your repo on GitHub: **Settings > Pages**
2. Under **Source**, select **GitHub Actions**
3. Push to `main` — the workflow runs automatically:
   - Checks out code
   - Runs `python viewer/build.py` to generate `data.js`
   - Deploys the `viewer/` folder to GitHub Pages
4. Site goes live at: `https://python-fastpy.github.io/learn-fastapi-py/`

### Workflow file

The deploy workflow is at [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). It triggers on:
- Every push to `main`
- Manual trigger via **Actions > Deploy to GitHub Pages > Run workflow**

### After deployment

Any changes you push to `main` (new files, updated examples) will automatically rebuild and redeploy the site within ~1-2 minutes.

---

## Project Structure

```
learn-fastapi-py/
├── fastapi/                    # FastAPI learning files
│   ├── 01-crud.py
│   ├── 02-pydantic.py
│   ├── 03-routes.py
│   ├── 04-headers-auth-request-anatomy.py
│   ├── 05-async-await.py
│   ├── 06-middleware-cors-caching.py
│   ├── 07-lifespan.py
│   ├── 08-session.py
│   └── 09-testing-with-pytest.py
├── project-book-store/         # Runnable end-to-end project (JSON -> DynamoDB -> AWS)
│   ├── README.md               # START HERE for this project
│   ├── pyproject.toml
│   ├── Dockerfile              # for the Fargate deploy path
│   ├── .env.example
│   ├── models.py               # never changes across stages
│   ├── main.py                 # never changes across stages
│   ├── config.py               # the STORAGE=json|dynamodb switch
│   ├── repository.py           # the storage interface
│   ├── repo_json.py            # stage 1
│   ├── repo_dynamo.py          # stage 2
│   ├── lambda_handler.py       # Mangum adapter
│   ├── test_books.py           # 14 tests, no AWS required
│   ├── test_repo_dynamo.py     # 9 tests, no AWS calls made
│   ├── infra-lambda.yaml       # CloudFormation: Lambda path
│   ├── infra-fargate.yaml      # CloudFormation: Fargate path
│   └── docs/                   # 6 numbered walkthroughs
├── learn-ai-advanced/           # RAG, evals, observability, guardrails (4 lessons, no setup needed)
│   ├── 01_rag_embeddings_and_retrieval.py
│   ├── 02_evals_and_llm_judge.py
│   ├── 03_observability_and_tracing.py
│   ├── 04_guardrails_and_prompt_injection.py
│   ├── llm_helper.py
│   └── README.md
├── python/                     # Python learning files
│   ├── data-types.py
│   ├── functions.py
│   ├── oops.py
│   ├── decorators.py
│   ├── annotations.py
│   ├── typeddict.py
│   ├── async-await.py
│   ├── exception-handling.py
│   └── file-handling.py
├── DSA/                        # Data structures & algorithms (JS, node-runnable)
│   ├── 01-big-o-complexity.js
│   ├── 02-arrays-objects-sets-maps.js
│   ├── 03-searching-algorithms.js
│   ├── 04-sorting-algorithms.js
│   ├── 05-stacks.js
│   ├── 06-queues.js
│   ├── 07-linked-lists.js
│   ├── 08-hash-tables.js
│   ├── 09-trees-and-tries.js
│   ├── 10-heaps-and-priority-queue.js
│   ├── 11-graphs.js
│   ├── 12-lru-cache.js
│   ├── 13-coding-problems-basic.js
│   ├── 14-coding-problems-intermediate.js
│   └── 15-coding-problems-advanced.js
├── system-design/               # System design (Markdown, ELI5 + technical depth)
│   ├── 01-what-is-system-design.md
│   ├── 02-scalability.md
│   ├── 03-load-balancing.md
│   ├── 04-caching.md
│   ├── 05-databases-sql-vs-nosql.md
│   ├── 06-database-scaling.md
│   ├── 07-cap-theorem-and-consistency.md
│   ├── 08-message-queues-and-async.md
│   ├── 09-microservices-vs-monolith.md
│   ├── 10-rate-limiting.md
│   ├── 11-cdn-and-proxies.md
│   ├── 12-consistent-hashing.md
│   ├── 13-availability-and-failover.md
│   ├── 14-monitoring-and-observability.md
│   ├── 15-case-study-url-shortener.md
│   ├── 16-case-study-rate-limiter.md
│   ├── 17-case-study-chat-app.md
│   └── 18-case-study-news-feed.md
├── viewer/                     # HTML viewer
│   ├── index.html              # Main viewer page
│   ├── build.py                # Parses .py files → data.js
│   └── data.js                 # Generated (do not edit manually)
├── .github/workflows/
│   └── deploy.yml              # GitHub Pages auto-deploy
├── .gitignore
└── README.md
```
