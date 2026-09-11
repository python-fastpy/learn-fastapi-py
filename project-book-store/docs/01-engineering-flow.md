# 01 — The Standard Engineering Flow

`Navigation: next: 02-stage1-json-file.md →`

How a real API actually gets from "idea" to "running on AWS", and what
you have to take care of at each step. Read this once before writing
code; come back to the checklist before each deploy.

---

## The flow

```
 1. REQUIREMENTS      what must it do, and how well?
        │
        ▼
 2. LOCAL DEV         build it with the simplest possible storage
        │             (a JSON file — no cloud account needed)
        ▼
 3. ABSTRACT          hide storage behind an interface, so swapping it
        │             later is a config change, not a rewrite
        ▼
 4. CONFIG            move every environment-specific value out of the
        │             code and into environment variables
        ▼
 5. TEST              prove the behaviour without touching real storage
        │
        ▼
 6. INFRASTRUCTURE    describe the cloud resources as CODE (CloudFormation),
        │             never by clicking in the console
        ▼
 7. DEPLOY            same code, real storage, real URL
        │
        ▼
 8. OBSERVE           logs, metrics, alarms — know when it breaks
        │
        └──────────▶ back to 1 (this is a loop, not a line)
```

Each stage in this project maps to that flow:

| Flow step | Where it lives here |
|---|---|
| 1. Requirements | this file, below |
| 2. Local dev | `repo_json.py` + [`02-stage1-json-file.md`](02-stage1-json-file.md) |
| 3. Abstract | `repository.py` — the `BookRepository` protocol |
| 4. Config | `config.py` + `.env.example` |
| 5. Test | `test_books.py` |
| 6. Infrastructure | `infra-lambda.yaml`, `infra-fargate.yaml` |
| 7. Deploy | [`04-deploy-lambda.md`](04-deploy-lambda.md), [`05-deploy-fargate.md`](05-deploy-fargate.md) |
| 8. Observe | [`06-operations-and-teardown.md`](06-operations-and-teardown.md) |

---

## 1. Requirements — do this before any code

Split them in two. Skipping the second half is the most common mistake,
and it's the half that actually decides your architecture.

**Functional** — what it does:
- Create, read, update (full + partial), delete a book
- List all books
- A health endpoint for load balancers to poll

**Non-functional** — how well it must do it:
- Read-heavy (people browse far more than they publish)
- Small dataset (thousands, not billions, of books)
- Eventual consistency is fine (a book appearing a second late is
  harmless — this is *not* a bank balance)
- Should cost ~nothing when idle

Those non-functional answers are why this project picks DynamoDB
on-demand billing and a single-table-free simple key design. Different
answers would give a different design — if the dataset were relational
and needed multi-row transactions, the right answer would be RDS, not
DynamoDB.

---

## 2-3. Local dev, then abstract

Build against the dumbest storage that works — here, a JSON file. You
get a working API in minutes with no AWS account, no credentials, no
Docker.

But put an **interface** between the endpoints and the storage from the
start. That is `repository.py`:

```
main.py  ──depends on──▶  BookRepository (interface)
                                 ▲
                   ┌─────────────┴─────────────┐
         JsonBookRepository            DynamoBookRepository
```

Without it, migrating to DynamoDB means editing every endpoint. With it,
migrating is one environment variable. This is the single highest-value
decision in the whole project.

> **Take care of:** don't let storage details leak upward. If `main.py`
> ever imports `json` or `boto3`, the abstraction has broken.

---

## 4. Config — never hardcode environment-specific values

Anything that differs between your laptop and AWS must come from the
environment: table names, regions, endpoints, feature flags.

```
Local:     STORAGE=json      BOOKS_FILE=books.json
Deployed:  STORAGE=dynamodb  TABLE_NAME=book-store-books-dev
```

Same code both times. `config.py` reads these once at startup and fails
fast on invalid values.

> **Take care of:**
> - **Secrets are not config.** API keys and passwords belong in AWS
>   Secrets Manager or SSM Parameter Store, fetched at startup — not in
>   `.env`, which is one `git add .` away from being public.
> - `.env` is for local convenience only. Nothing reads it in
>   production; the CloudFormation templates set real env vars instead.
> - **No credentials in code, ever.** boto3 finds them automatically
>   from the IAM role attached to your Lambda/ECS task.

---

## 5. Test — before you deploy, not after

`test_books.py` runs with no AWS account and no network, by swapping in
a fake repository:

```python
app.dependency_overrides[get_repository] = lambda: fake_repo
```

This is why step 3 mattered. The tests exercise the real HTTP layer
(status codes, validation, PATCH-vs-PUT semantics) against in-memory
storage, so they're fast enough to run on every save.

> **Take care of:** test the error paths, not just the happy path. 404
> on a missing id, 422 on invalid input, and PATCH leaving untouched
> fields alone are exactly the things that break silently.

---

## 6. Infrastructure as Code — the console is for looking, not building

You *could* click through the AWS console to create a table, a Lambda,
and an API Gateway. Don't. Six months later nobody remembers which
checkboxes were ticked, and staging doesn't match production.

Instead the whole environment is a CloudFormation template you commit
to git:

| Clicking in the console | CloudFormation |
|---|---|
| Not reproducible | Same stack every time |
| No history of what changed | Diffable in git |
| Manual teardown, easy to leak resources | `delete-stack` removes everything |
| Staging drifts from prod | Deploy the same file with different params |

> **Take care of:**
> - **Least privilege.** Grant exactly the actions needed on exactly the
>   resources needed. Both templates here scope DynamoDB permissions to
>   one table ARN, never `Resource: "*"`.
> - **Parameterise names.** `ProjectName`/`Environment` params let you
>   deploy dev and prod side by side from one file.
> - **Declare log groups explicitly** with a retention period.
>   Auto-created ones never expire and bill you forever.
> - **Know your `DeletionPolicy`.** These templates use `Delete` so
>   teardown is clean; real data wants `Retain`.

---

## 7. Deploy

Two paths, same application code:

```
                    ┌─ Lambda + API Gateway  (04-deploy-lambda.md)
   same main.py ────┤
                    └─ ECS Fargate + ALB     (05-deploy-fargate.md)
```

| | Lambda | Fargate |
|---|---|---|
| Cost at idle | ~$0 | pays per running hour |
| Cold starts | yes (~1-3s) | none |
| Max request duration | 15 min | unlimited |
| Scaling | automatic, instant | slower, you configure it |
| Best for | spiky/low traffic, simple APIs | steady traffic, long jobs, websockets |

> **Take care of:**
> - **Deploy order matters.** Storage before the thing that uses it.
>   CloudFormation figures most of this out from `!Ref` dependencies,
>   but use `DependsOn` where it can't.
> - **Verify each step before moving on.** Every deploy doc here tells
>   you what to `curl` and what you should see.
> - **Have a rollback path.** CloudFormation auto-rolls-back a failed
>   create. For a bad-but-successful deploy, keep the previous Lambda
>   version or container image tag so you can redeploy it.
> - **Never deploy straight to prod untested.** Deploy to `dev` first —
>   that's what the `Environment` parameter is for.

---

## 8. Observe

A deploy that you can't monitor isn't finished. Minimum viable
observability:

- **Logs** — CloudWatch, with a retention period set
- **A health endpoint** — `/health`, polled by the load balancer
- **Alarms** — tell you about errors before a user does

Covered in [`06-operations-and-teardown.md`](06-operations-and-teardown.md).

---

## The pre-deploy checklist

Run through this before every deploy:

- [ ] Tests pass locally (`pytest test_books.py`)
- [ ] No secrets in the code, in `.env`, or in the template
- [ ] No hardcoded table names, regions, or account IDs
- [ ] IAM scoped to specific actions on specific resources
- [ ] Log groups declared with retention
- [ ] Deployed to `dev` and smoke-tested before `prod`
- [ ] You know how to roll back
- [ ] You know how to tear it all down (so it stops costing money)

---

`Navigation: next: 02-stage1-json-file.md →`
