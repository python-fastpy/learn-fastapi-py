# 04 — Deploy Path A: Lambda + API Gateway (CloudFormation)

`Navigation: ← prev: 03-stage2-dynamodb.md | next: 05-deploy-fargate.md →`

Deploy the app serverlessly. One CloudFormation stack creates the
DynamoDB table, the Lambda function, the HTTP API in front of it, IAM
roles, and a log group.

**Cost:** everything here fits in the AWS free tier for tutorial-level
traffic, and an idle stack costs essentially $0. Tear it down anyway
when you're done — [doc 06](06-operations-and-teardown.md).

---

## What we're building

```
   Internet
      │
      ▼
   API Gateway (HTTP API)        public HTTPS URL
      │   $default route: ANY /{proxy+}
      │   sends EVERY path+method to one Lambda;
      │   FastAPI routes internally
      ▼
   Lambda: book-store-api-dev    lambda_handler.handler (Mangum)
      │   env: STORAGE=dynamodb
      ▼
   DynamoDB: book-store-books-dev
```

## Why Mangum is needed

FastAPI speaks ASGI. Lambda speaks "here's a JSON event dict, return a
JSON response dict". They don't understand each other:

```
API Gateway ──▶ handler(event, context)      ← event is a dict describing
                        │                       the HTTP request
                        ▼
                 Mangum translates
                        │
                        ▼
              FastAPI's normal ASGI app       ← your @app.get runs
                        │
                 Mangum translates back
                        ▼
        {"statusCode": 200, "body": "...", ...}
```

`lambda_handler.py` is the whole adapter — three lines. `main.py` is
untouched; the same `app` object serves uvicorn locally and Lambda here.

---

## Prerequisites

```bash
aws --version                  # AWS CLI v2
aws sts get-caller-identity    # confirms credentials work
```

If that second command fails, run `aws configure` first.

---

## Step 1 — Build the deployment package

Lambda needs your code *and* its dependencies in one zip. Lambda's
Python runtime includes `boto3` already, but not `fastapi`, `pydantic`,
`pydantic-settings`, or `mangum`.

```bash
# from project-book-store/
rm -rf build && mkdir build

# Dependencies. --target installs INTO the folder rather than a venv.
pip install \
  --target build \
  --platform manylinux2014_x86_64 \
  --implementation cp \
  --python-version 3.11 \
  --only-binary=:all: \
  "fastapi==0.115.0" "pydantic==2.9.2" \
  "pydantic-settings==2.5.2" "mangum==0.19.0"

# Application code (flat, no subfolder)
cp models.py config.py repository.py repo_json.py repo_dynamo.py \
   main.py lambda_handler.py build/
```

> **Why all those `--platform` flags?** Lambda runs Linux x86_64. If you
> build on Windows or macOS without them, pip installs *your* platform's
> compiled wheels — `pydantic-core` is a native binary — and the
> function fails at import with
> `No module named 'pydantic_core._pydantic_core'`. This is the single
> most common Lambda packaging failure.

```bash
cd build && zip -r ../function.zip . -x '*.pyc' '__pycache__/*' && cd ..
```

On Windows PowerShell, instead of `zip`:

```powershell
Compress-Archive -Path build\* -DestinationPath function.zip -Force
```

**Verify** the zip has the right shape — `lambda_handler.py` must be at
the *root*, not nested in a folder:

```bash
unzip -l function.zip | head -20
```

## Step 2 — Upload the zip to S3

CloudFormation can't take a zip from your disk; Lambda code with
dependencies must come from S3.

```bash
# Bucket names are GLOBALLY unique — add your account id
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
BUCKET="book-store-deploy-$ACCOUNT"

aws s3 mb "s3://$BUCKET"
aws s3 cp function.zip "s3://$BUCKET/book-store/function.zip"
```

## Step 3 — Deploy the stack

```bash
aws cloudformation deploy \
  --template-file infra-lambda.yaml \
  --stack-name book-store-lambda-dev \
  --parameter-overrides \
      CodeS3Bucket="$BUCKET" \
      CodeS3Key=book-store/function.zip \
      Environment=dev \
  --capabilities CAPABILITY_NAMED_IAM
```

> **`--capabilities CAPABILITY_NAMED_IAM` is REQUIRED.** The template
> creates IAM roles with explicit names, and CloudFormation refuses to
> create named IAM resources unless you explicitly acknowledge it —
> because creating roles is a privilege-escalation-shaped action.
> Without this flag the deploy fails immediately with
> `InsufficientCapabilitiesException`.

Takes ~1-2 minutes. Watch progress:

```bash
aws cloudformation describe-stack-events \
  --stack-name book-store-lambda-dev \
  --query 'StackEvents[0:5].[LogicalResourceId,ResourceStatus]' \
  --output table
```

## Step 4 — Get your URL

```bash
aws cloudformation describe-stacks \
  --stack-name book-store-lambda-dev \
  --query 'Stacks[0].Outputs' --output table
```

```
ApiUrl           https://abc123.execute-api.us-east-1.amazonaws.com
HealthCheckUrl   https://abc123.execute-api.us-east-1.amazonaws.com/health
SwaggerDocsUrl   https://abc123.execute-api.us-east-1.amazonaws.com/docs
TableName        book-store-books-dev
FunctionName     book-store-api-dev
```

This is why templates declare `Outputs` — no hunting through the console.

## Step 5 — Smoke test

Always health-check first. It's the cheapest signal and doesn't touch
storage, so it isolates "is the app running" from "can it reach the DB".

```bash
API=$(aws cloudformation describe-stacks --stack-name book-store-lambda-dev \
      --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)

curl "$API/health"
# {"status":"ok","version":"1.0.0","storage":"dynamodb","env":"dev"}
```

Note `"storage":"dynamodb"` — the same code that ran against a JSON file
locally is now on DynamoDB, purely because the template set
`STORAGE=dynamodb`.

Now the real thing:

```bash
curl -X POST "$API/books" -H "Content-Type: application/json" \
  -d '{"title":"Dune","author":"Herbert","price":12.50,"genre":"scifi"}'

curl "$API/books"
```

Confirm it really landed in DynamoDB:

```bash
aws dynamodb scan --table-name book-store-books-dev \
  --query 'Items[].{id:book_id.S,title:title.S}' --output table
```

And open `$API/docs` in a browser — Swagger UI, live, on AWS.

## Step 6 — Read the logs

```bash
aws logs tail /aws/lambda/book-store-api-dev --follow
```

`--follow` streams live; hit an endpoint in another terminal and watch
requests arrive. Each cold start logs `INIT_START`, and every invocation
ends with a `REPORT` line showing `Duration`, `Billed Duration`, and
`Max Memory Used` — that last one tells you whether your `LambdaMemoryMB`
is sensible.

---

## Updating after a code change

CloudFormation only updates the function if the S3 object *key* changes
— it doesn't notice new bytes at the same key. Version your keys:

```bash
# rebuild, then:
aws s3 cp function.zip "s3://$BUCKET/book-store/function-v2.zip"

aws cloudformation deploy \
  --template-file infra-lambda.yaml \
  --stack-name book-store-lambda-dev \
  --parameter-overrides CodeS3Bucket="$BUCKET" \
                        CodeS3Key=book-store/function-v2.zip \
  --capabilities CAPABILITY_NAMED_IAM
```

(Real pipelines use the git commit SHA as the key. `aws cloudformation
package` and AWS SAM automate this.)

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `InsufficientCapabilitiesException` | missing IAM ack | add `--capabilities CAPABILITY_NAMED_IAM` |
| `No module named 'pydantic_core._pydantic_core'` | wheels built for the wrong OS | rebuild with the `--platform manylinux2014_x86_64` flags in step 1 |
| `Unable to import module 'lambda_handler'` | zip has a nested folder, or wrong `Handler` | `lambda_handler.py` must be at the zip root; handler is `lambda_handler.handler` |
| 500 on every route, `AccessDenied` in logs | IAM can't reach the table | check the stack created `ExecutionRole`; the table ARN is scoped in `AccessBooksTableOnly` |
| `{"message":"Not Found"}` from API Gateway | route didn't match | the template's `$default` route should catch everything — check `ApiRoute` exists |
| First request slow (~1-3s), rest fast | cold start | expected; raise `LambdaMemoryMB` (more memory = more CPU) or use provisioned concurrency |
| `Task timed out after 30.00 seconds` | genuinely slow work | Lambda's a poor fit for long jobs — see path B |

---

## The cold start trade-off

```
Request 1 (cold):  [ init runtime | import fastapi/pydantic | your code ]  ~1-3s
Request 2 (warm):  [ your code ]                                            ~10ms
```

Lambda freezes the container between invocations and reuses it, so only
the first request after idle pays the init cost. `lambda_handler.py`
uses `Mangum(app, lifespan="off")` specifically so lifespan events don't
re-run on every invocation; the repository is built once per warm
container and cached.

If consistent low latency matters more than idle cost, that's the
argument for **path B (Fargate)** — no cold starts, but you pay per
running hour.

---

`Navigation: ← prev: 03-stage2-dynamodb.md | next: 05-deploy-fargate.md →`
