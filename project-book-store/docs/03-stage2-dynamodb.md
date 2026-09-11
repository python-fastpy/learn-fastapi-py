# 03 — Stage 2: Migrate to DynamoDB

`Navigation: ← prev: 02-stage1-json-file.md | next: 04-deploy-lambda.md →`

Swap the JSON file for a real database. You can do this entirely
offline first (DynamoDB Local, no AWS account), then against real AWS.

**The headline: `main.py`, `models.py`, and `test_books.py` do not
change. At all.** Only the environment changes.

---

## What DynamoDB is, briefly

A managed NoSQL key-value store. You give it a key, it gives you an
item, in single-digit milliseconds, at any scale. What you give up
versus SQL: joins, multi-row transactions by default, and ad-hoc
queries on arbitrary columns.

| | JSON file | DynamoDB |
|---|---|---|
| Concurrent writes | lost updates | atomic, server-side |
| Write cost | rewrites whole file | touches one item |
| Shared across instances | no | yes |
| Queryable | no | by key, or via indexes |
| Costs money | no | yes (tiny; ~$0 idle) |
| Needs permissions | no | yes (IAM) |

---

## Table design

Deliberately the simplest thing that works:

```
Table: book-store-books
Partition key: book_id (String)      ← no sort key

┌──────────────┬───────┬─────────┬───────┬──────────┐
│ book_id (PK) │ title │ author  │ price │ genre    │
├──────────────┼───────┼─────────┼───────┼──────────┤
│ a1b2c3d4     │ 1984  │ Orwell  │ 9.99  │ dystopia │
│ e5f6a7b8     │ Dune  │ Herbert │ 12.50 │ (absent) │
└──────────────┴───────┴─────────┴───────┴──────────┘
```

**Why no sort key?** Every access here is "give me the book with this
exact id". A sort key earns its complexity only when you store multiple
related items under one partition (a book *and* its reviews) or query
ranges.

**Only the key is declared.** DynamoDB is schemaless for everything
else — `title`/`author`/`price`/`genre` appear nowhere in the template.
The `Dune` row simply has no `genre` attribute rather than a NULL column.

> **Note on advanced design:** you may see "single-table design" with
> generic `PK`/`SK` attributes holding values like `BOOK#001` /
> `METADATA`. That's a powerful pattern for modelling multiple entity
> types and relationships in one table, and it's what
> `../aws/15c-dynamodb.yaml` in this repo demonstrates. It's also a lot
> to absorb at once. This project stays with a simple partition key on
> purpose; graduate to single-table when you actually have
> relationships to model.

---

## Option A — DynamoDB Local (no AWS account)

Fastest way to try stage 2. Runs DynamoDB in a Docker container on your
machine.

**1. Start it:**

```bash
docker run -d -p 8001:8000 --name dynamodb-local amazon/dynamodb-local
```

(Host port `8001` because our API already uses `8000`.)

**2. Install boto3 and create the table:**

```bash
uv pip install "boto3==1.35.36"

aws dynamodb create-table \
  --table-name book-store-books \
  --attribute-definitions AttributeName=book_id,AttributeType=S \
  --key-schema AttributeName=book_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --endpoint-url http://localhost:8001 \
  --region us-east-1
```

DynamoDB Local ignores credentials, but the AWS CLI still insists they
exist. If you have none configured:

```bash
export AWS_ACCESS_KEY_ID=fake AWS_SECRET_ACCESS_KEY=fake   # bash
$env:AWS_ACCESS_KEY_ID="fake"; $env:AWS_SECRET_ACCESS_KEY="fake"  # PowerShell
```

**3. Point the app at it** — edit `.env`:

```
STORAGE=dynamodb
TABLE_NAME=book-store-books
AWS_REGION=us-east-1
DYNAMODB_ENDPOINT_URL=http://localhost:8001
```

**4. Restart and verify the switch:**

```bash
uvicorn main:app --reload
# [startup] storage=dynamodb env=local     ← different backend!
```

```bash
curl http://localhost:8000/health
# {"status":"ok",...,"storage":"dynamodb","env":"local"}
```

**5. Run the exact same curl commands from stage 1.** Identical
responses, but now `books.json` is never touched — the data lives in
DynamoDB. Confirm:

```bash
aws dynamodb scan --table-name book-store-books \
  --endpoint-url http://localhost:8001 --region us-east-1
```

---

## Option B — Real AWS

**1. Credentials:**

```bash
aws configure          # needs an IAM user with DynamoDB permissions
aws sts get-caller-identity   # verify it works
```

**2. Create the table:** the same `create-table` command as above,
minus `--endpoint-url`. Or just skip ahead — the CloudFormation
templates in the next docs create it for you, which is the better habit.

**3. `.env`** — same as Option A but with `DYNAMODB_ENDPOINT_URL=`
(empty), so boto3 talks to real AWS.

> **Cost:** on-demand billing means an idle table costs essentially
> nothing, and this tutorial's traffic falls inside the AWS free tier.
> Still, tear it down when done — see doc 06.

---

## What changed in the code

Only one new file: `repo_dynamo.py`. Same six methods, same signatures.
Three things in it are worth understanding, because they're the things
that actually bite people.

### 1. The `Decimal` gotcha

DynamoDB has no float type. Hand boto3 a `float` and it raises
`TypeError: Float types are not supported`.

```python
Decimal(9.99)       # 9.99000000000000021316...  ← binary float noise
Decimal(str(9.99))  # 9.99                        ← what you meant
```

`_to_dynamo()` converts on the way in, `_from_dynamo()` converts back on
the way out. Doing it at the repository boundary means `models.py` and
the JSON responses never see a `Decimal` (which `json.dumps` can't
serialise anyway).

### 2. `ConditionExpression` — how "not found" works

The JSON version could just check `if book_id not in data`. DynamoDB
operations don't fail on missing keys by default:

- `put_item` **silently overwrites** an existing item
- `delete_item` on a missing key **succeeds** (it's idempotent)

So each method states its expectation explicitly:

| Method | Condition | Why |
|---|---|---|
| `create` | `attribute_not_exists(book_id)` | never clobber an existing book on an id collision |
| `replace` | `attribute_exists(book_id)` | PUT must not *create* — otherwise we'd return 200 for a nonexistent id |
| `patch` | `attribute_exists(book_id)` | same |
| `delete` | `attribute_exists(book_id)` | so we can tell "deleted" from "wasn't there" and return 404 |

When the condition fails, DynamoDB raises `ConditionalCheckFailedException`,
which we catch and turn into `None`/`False` → the endpoint returns 404.

### 3. `Scan` vs `Query`, and pagination

`list_all()` uses **Scan**, which reads every item in the table.

```
Scan  — reads the WHOLE table.     Cost grows with total table size.
Query — reads ONE partition.       Cost grows with matches returned.
```

Scan is fine for a demo table and is the operation to be most suspicious
of in real systems. If "list all books" needed to scale you'd
restructure so it becomes a Query (e.g. partition by genre), or add a
Global Secondary Index.

Also: **Scan returns at most 1 MB per call.** A naive implementation
silently returns partial data. `list_all()` loops on
`LastEvaluatedKey` to page through everything — an easy bug to ship.

### 4. One client, not one per request

```python
# In main.py's lifespan — created ONCE at startup:
app.state.repository = build_repository(settings)
```

Creating a boto3 resource per request re-resolves credentials and opens
new TLS connections every time. It's a real, common performance bug.
`get_repository` in `repository.py` reuses the single instance (and
caches one on first use if the lifespan didn't run, which is the case
under Lambda — see doc 04).

---

## Verify the migration properly

The strongest check that the abstraction held: **the test suite is
unchanged and still passes.**

```bash
pytest test_books.py -v     # 14 passed
```

Those tests inject a fake repository, so they pass regardless of
backend — which is exactly the point. They pin the *contract* that
`repo_json.py` and `repo_dynamo.py` both have to satisfy.

To test against DynamoDB itself without real AWS, look at
[`moto`](https://docs.getmoto.org/), which mocks AWS services in-process.

---

## Gotchas worth knowing

1. **Reserved words.** `name`, `status`, `size`, `year`, `value` and
   ~570 others can't be used bare in expressions. `patch()` routes
   *every* attribute through an `#alias` placeholder so you never have
   to remember the list.
2. **Eventual consistency.** Reads may return slightly stale data by
   default. Pass `ConsistentRead=True` to `get_item` when you must read
   your own write immediately — it costs double the read units.
3. **400 KB max item size.** Store large blobs in S3 and keep the URL in
   DynamoDB.
4. **No `SELECT * WHERE price < 10`.** Non-key filtering happens
   *after* the read, so you pay to read everything and then discard.
   Design your keys around your access patterns, not the other way round.

---

`Navigation: ← prev: 02-stage1-json-file.md | next: 04-deploy-lambda.md →`
