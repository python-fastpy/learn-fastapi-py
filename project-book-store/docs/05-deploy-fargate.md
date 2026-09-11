# 05 — Deploy Path B: ECS Fargate + ALB (CloudFormation)

`Navigation: ← prev: 04-deploy-lambda.md | next: 06-operations-and-teardown.md →`

Deploy the *same application code* as a long-running container instead
of a function. No cold starts, no 15-minute limit — but you pay per
running hour instead of per request.

> **⚠ COST WARNING — read before deploying.** Unlike the Lambda path,
> this one is **not** free at idle. An ALB costs roughly **$16-18/month**
> just to exist, plus ~$9/month for two small Fargate tasks. Both bill
> by the hour whether or not anyone uses your API. Follow
> [doc 06](06-operations-and-teardown.md) to tear it down when you're
> finished, or you'll get a surprise bill.

---

## What we're building

```
   Internet
      │
      ▼
   ALB (Application Load Balancer)     public, port 80
      │   SG: allow :80 from anywhere
      │   health check: GET /health every 30s
      ▼
   Target Group ──▶ 2 × Fargate tasks
      │                SG: allow :8000 FROM THE ALB ONLY
      │                image pulled from ECR
      ▼
   DynamoDB: book-store-books-dev
```

## Lambda or Fargate?

| | Lambda (path A) | Fargate (path B) |
|---|---|---|
| Idle cost | ~$0 | ~$25/mo (ALB + tasks) |
| Cold starts | yes, ~1-3s | none |
| Max request | 15 min | unlimited |
| Websockets / SSE | awkward | natural |
| Background threads | die when frozen | fine |
| Scaling | instant, automatic | slower, you configure it |
| Deploy artifact | zip | Docker image |

Choose Fargate for steady traffic, long-running requests, websockets, or
when predictable latency matters more than idle cost. For this
tutorial's API, Lambda is honestly the better fit — path B exists
because you'll meet workloads where it isn't.

---

## Prerequisites

```bash
aws sts get-caller-identity    # credentials work
docker --version               # Docker running locally
```

---

## Step 1 — Understand the Dockerfile

Read `Dockerfile` in the project root. Four decisions in it matter:

**1. `python:3.11-slim`, not `alpine`.** Alpine uses musl instead of
glibc, so many Python packages can't use prebuilt wheels and compile
from source — slow builds and occasional runtime surprises.

**2. Dependencies copied and installed *before* app code.** Docker
caches layers. Because `pyproject.toml` is copied first, editing
`main.py` reuses the cached dependency layer instead of reinstalling
everything. Copy all files at once and every one-line edit costs a full
reinstall.

**3. Non-root user.** If the app is compromised, the attacker lands as
an unprivileged user rather than root inside the container.

**4. `--host 0.0.0.0`.** This is *the* classic mistake. uvicorn's
default (`127.0.0.1`) only accepts connections from inside the
container, so the ALB health check gets connection-refused, the task is
marked unhealthy, ECS kills it, and it restarts forever.

## Step 2 — Build and test locally FIRST

Never push an image you haven't run.

```bash
docker build -t book-store-api:v1 .

# Run with the JSON backend — no AWS needed for this check
docker run --rm -p 8000:8000 -e STORAGE=json book-store-api:v1
```

In another terminal:

```bash
curl http://localhost:8000/health
# {"status":"ok",...,"storage":"json","env":"local"}
```

If that works, the image is sound. Stop it with `Ctrl-C`.

## Step 3 — Push to ECR

ECR is AWS's private Docker registry. Fargate pulls from it.

```bash
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
REPO="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/book-store-api"

# 1. Create the repository (once)
aws ecr create-repository --repository-name book-store-api \
    --image-scanning-configuration scanOnPush=true

# 2. Log Docker in to ECR (token expires after 12h)
aws ecr get-login-password --region $REGION \
  | docker login --username AWS --password-stdin "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"

# 3. Tag and push
docker tag book-store-api:v1 "$REPO:v1"
docker push "$REPO:v1"
```

> **On Apple Silicon (M1/M2/M3):** Fargate here runs x86_64, so build
> with `docker build --platform linux/amd64 -t book-store-api:v1 .` or
> the task fails with an `exec format error`.

**Verify the push:**

```bash
aws ecr describe-images --repository-name book-store-api \
  --query 'imageDetails[].imageTags' --output table
```

> **Use explicit tags (`:v1`), never `:latest`.** With `:latest` you
> cannot tell which build is running, and CloudFormation sees no change
> to the `ContainerImage` parameter so it won't redeploy at all.

## Step 4 — Find your VPC and subnets

The template takes these as parameters rather than building a VPC (a
production VPC needs a NAT gateway, which costs ~$32/month even idle).

```bash
# Default VPC
VPC=$(aws ec2 describe-vpcs --filters Name=is-default,Values=true \
      --query 'Vpcs[0].VpcId' --output text)
echo $VPC

# Subnets in it
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC" \
  --query 'Subnets[].{Subnet:SubnetId,AZ:AvailabilityZone}' --output table
```

> **You need at least TWO subnets in DIFFERENT availability zones.** An
> ALB requires two AZs — this is not optional, and a single-subnet list
> is the most common first-deploy failure.

## Step 5 — Deploy the stack

```bash
aws cloudformation deploy \
  --template-file infra-fargate.yaml \
  --stack-name book-store-fargate-dev \
  --parameter-overrides \
      VpcId="$VPC" \
      SubnetIds="subnet-aaa,subnet-bbb" \
      ContainerImage="$REPO:v1" \
      Environment=dev \
  --capabilities CAPABILITY_NAMED_IAM
```

> `--capabilities CAPABILITY_NAMED_IAM` is **required** (named IAM roles
> again), and note `SubnetIds` is a comma-separated list inside one
> quoted string.

This takes **3-5 minutes** — longer than Lambda, because it waits for
the ALB to provision and for tasks to pass health checks.

```bash
aws cloudformation describe-stack-events --stack-name book-store-fargate-dev \
  --query 'StackEvents[0:8].[LogicalResourceId,ResourceStatus]' --output table
```

## Step 6 — Smoke test

```bash
ALB=$(aws cloudformation describe-stacks --stack-name book-store-fargate-dev \
      --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" --output text)
echo $ALB

curl "$ALB/health"
# {"status":"ok",...,"storage":"dynamodb","env":"dev"}
```

> If you get a **503** right after deploying, wait ~60s. Tasks must pass
> two consecutive health checks 30s apart before the ALB routes to them.

```bash
curl -X POST "$ALB/books" -H "Content-Type: application/json" \
  -d '{"title":"Neuromancer","author":"Gibson","price":11.99}'
curl "$ALB/books"
```

**Check that both tasks are healthy** — this is what redundancy looks
like:

```bash
aws ecs describe-services --cluster book-store-cluster-dev \
  --services book-store-service-dev \
  --query 'services[0].{desired:desiredCount,running:runningCount}'
# {"desired": 2, "running": 2}
```

## Step 7 — Logs

```bash
aws logs tail /ecs/book-store-dev --follow
```

Requests land on *either* task, so you'll see logs interleaved from
both — which is the visible proof you're load balanced.

---

## Two security groups, chained — the important bit

This pair is the whole network security model:

```
AlbSecurityGroup    :80   from  0.0.0.0/0          ← public front door
TaskSecurityGroup   :8000 from  AlbSecurityGroup   ← ALB only!
```

The task rule's source is the **ALB's security group**, not a CIDR. So
even though the containers sit in public subnets with public IPs, they
are unreachable from the internet — traffic must arrive via the load
balancer. Putting `0.0.0.0/0` there instead would expose the app
directly and let people bypass the ALB entirely.

## Two IAM roles, and why

Mixing these up is *the* classic ECS mistake:

| Role | Used by | For |
|---|---|---|
| `ExecutionRole` | the ECS **agent** | pulling the image from ECR, writing log streams |
| `TaskRole` | **your code** (boto3) | reading/writing the DynamoDB table |

Symptom of confusing them: the image pulls fine but every DynamoDB call
returns `AccessDenied` — or the task never starts with
`CannotPullContainerError`.

---

## Updating after a code change

```bash
docker build -t book-store-api:v2 .
docker tag book-store-api:v2 "$REPO:v2"
docker push "$REPO:v2"

aws cloudformation deploy \
  --template-file infra-fargate.yaml \
  --stack-name book-store-fargate-dev \
  --parameter-overrides VpcId="$VPC" SubnetIds="subnet-aaa,subnet-bbb" \
                        ContainerImage="$REPO:v2" \
  --capabilities CAPABILITY_NAMED_IAM
```

ECS does a **rolling deploy**: it starts v2 tasks, waits for them to
pass health checks, shifts traffic, *then* stops v1. The template's
`MinimumHealthyPercent: 100` / `MaximumPercent: 200` is what makes this
zero-downtime — it never drops below the desired count.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `CannotPullContainerError` | task can't reach ECR | needs `AssignPublicIp: ENABLED` in a public subnet (the template sets this), or VPC endpoints in a private one |
| Task starts then stops, repeatedly | health check failing | almost always uvicorn bound to `127.0.0.1` — must be `--host 0.0.0.0` |
| `exec format error` | built on ARM (Apple Silicon) | rebuild with `--platform linux/amd64` |
| 503 from the ALB | no healthy targets yet | wait 60s; then check `aws logs tail /ecs/book-store-dev` |
| Stack stuck `CREATE_IN_PROGRESS` ~15 min | tasks never pass health checks | check task logs; the stack will eventually roll back |
| `At least two subnets in two different AZs` | one subnet passed | pass two from different AZs |
| `AccessDenied` on DynamoDB | wrong role | app permissions belong on `TaskRole`, not `ExecutionRole` |
| Invalid CPU/memory combination | bad pairing | 256 CPU allows only 512/1024/2048 MB |

---

## What's missing for real production

Deliberately left out to keep the template readable:

- **HTTPS.** Listener is plain HTTP on :80. Real deployments add an ACM
  certificate, a :443 listener, and redirect 80 → 443.
- **A custom domain.** Route 53 alias record pointing at the ALB.
- **Auto-scaling.** Fixed `DesiredCount`; production adds an
  Application Auto Scaling target tracking CPU or request count.
- **Private subnets.** Tasks sit in public subnets with public IPs.
  More secure: private subnets + NAT gateway or VPC endpoints.

---

`Navigation: ← prev: 04-deploy-lambda.md | next: 06-operations-and-teardown.md →`
