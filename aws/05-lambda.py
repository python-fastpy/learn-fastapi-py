# ══════════════════════════════════════════════════════════════════
# AWS Deployment — Lambda (Step 4)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 04-ec2.py  |  next: 06-api-gateway.py →

# ╔══════════════════════════════════════════════════╗
# ║       STEP 4: LAMBDA — SERVERLESS               ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Run code without managing servers. Upload code, AWS handles
#       everything: provisioning, scaling, patching, availability.
#       Pay only when code runs (~$0.20 per 1M invocations).
#
# HOW:  Lambda receives an "event" (JSON), runs your function,
#       returns a response. Max runtime: 15 minutes.
#       Scales from 0 to thousands of instances automatically.
#
# REAL REPO: sphinx_story-service has 5 Lambda functions:
#            healthCheck, stories, assets, alerts, search
#            Each handles multiple routes via Middy router.
#
#   Event (JSON)                        Lambda Function
#   ┌────────────────┐                  ┌──────────────┐
#   │ httpMethod: GET│──── triggers ───►│ handler()    │
#   │ path: /health  │                  │   ↓          │
#   │ headers: {...} │                  │ return {     │
#   │ body: null     │                  │  statusCode, │
#   └────────────────┘                  │  body        │
#                                       │ }            │
#                                       └──────────────┘
#
# ── 4a. Create Lambda Handler File ──────────────────────────
#
#   Create lambda_handler.py in your project:
#
#     from mangum import Mangum
#     from main import app
#
#     # Mangum wraps FastAPI to handle Lambda's event format
#     # It translates API Gateway events ↔ ASGI (FastAPI's protocol)
#     handler = Mangum(app, lifespan="off")
#
#   Mangum converts this:
#     {"httpMethod":"GET","path":"/health",...}
#   Into a proper ASGI request that FastAPI understands.
#
# ── 4b. Package for Lambda ──────────────────────────────────
#
#   # Create deployment package with all dependencies
#   mkdir package
#   uv pip install -r pyproject.toml --target package/
#   cp main.py lambda_handler.py package/
#   cd package && zip -r ../deployment.zip . && cd ..
#
#   # Result: deployment.zip (~15MB) contains:
#   #   main.py, lambda_handler.py, fastapi/, uvicorn/, mangum/,
#   #   pydantic/, starlette/, and all sub-dependencies
#
# ── 4c. AWS Console Steps ───────────────────────────────────
#
#   1. AWS Console → search "Lambda" → click Lambda
#
#   2. Click "Create function" (orange button)
#
#   3. Fill in:
#      ┌──────────────────────────────────────────────────┐
#      │  ○ Author from scratch  (selected)                │
#      │                                                    │
#      │  Function name:  book-store-api                   │
#      │  Runtime:        Python 3.11                      │
#      │  Architecture:   arm64                            │
#      │    (cheaper + faster than x86 for Python)         │
#      │                                                    │
#      │  Permissions:                                     │
#      │    ○ Create a new role with basic Lambda perms    │
#      │                                                    │
#      │  Advanced settings:                               │
#      │    ✅ Enable VPC  (expand this section)           │
#      │    VPC:     book-store-vpc                        │
#      │    Subnets: Select BOTH private subnets           │
#      │    Security group: book-store-app-sg              │
#      └──────────────────────────────────────────────────┘
#
#   4. Click "Create function"
#
#   5. Upload code:
#      → Code tab → "Upload from" → ".zip file"
#      → Upload deployment.zip → Save
#
#   6. Change handler:
#      → Code tab → Runtime settings → "Edit"
#      → Handler: lambda_handler.handler
#      → Save
#
#   7. Configure timeout & memory:
#      → Configuration tab → General configuration → "Edit"
#      ┌──────────────────────────────────────────────────┐
#      │  Memory:   256 MB                                 │
#      │  Timeout:  30 seconds                             │
#      │  (FastAPI cold start needs ~3-5s, leave margin)   │
#      └──────────────────────────────────────────────────┘
#      → Save
#
#   8. Add environment variables (optional):
#      → Configuration → Environment variables → "Edit"
#      → Add: Key=ENV, Value=production
#      → Save
#
#   9. Test it:
#      → Test tab → Create test event:
#      ┌──────────────────────────────────────────────────┐
#      │  Event name:  health-check                        │
#      │  Template:    apigateway-aws-proxy                │
#      │  Event JSON:                                      │
#      │  {                                                │
#      │    "httpMethod": "GET",                           │
#      │    "path": "/health",                             │
#      │    "headers": {"Content-Type":"application/json"},│
#      │    "queryStringParameters": null,                 │
#      │    "body": null,                                  │
#      │    "requestContext": {}                            │
#      │  }                                                │
#      └──────────────────────────────────────────────────┘
#      → Click "Test"
#      → Should see: {"statusCode":200,"body":"{\"status\":\"ok\"...}"}
#
# ── Lambda Key Concepts ─────────────────────────────────────
#
#   ── Handler ────────────────────────────────────────────────
#
#   The entry point Lambda calls when a request arrives.
#   Format: filename.function_name (without .py extension).
#
#   "lambda_handler.handler" means:
#     → find file lambda_handler.py
#     → call function handler(event, context)
#
#   The function receives two arguments:
#     event   → the trigger data (API Gateway request, S3 event, etc.)
#     context → Lambda metadata (function name, memory, time remaining)
#
#   Practical example — what the event looks like from API Gateway:
#
#     {
#       "httpMethod": "POST",
#       "path": "/books",
#       "headers": {"Content-Type": "application/json", "Authorization": "Bearer ..."},
#       "body": "{\"title\":\"1984\",\"author\":\"Orwell\",\"price\":9.99}",
#       "queryStringParameters": null,
#       "pathParameters": null,
#       "requestContext": {"stage": "v1", "requestId": "abc-123"}
#     }
#
#   Mangum converts this into a proper ASGI request for FastAPI.
#   Without Mangum, you'd have to parse event manually.
#
#   ── Cold Start ─────────────────────────────────────────────
#
#   First invocation after idle period. Lambda must:
#     1. Download your deployment package (zip or container)
#     2. Start the Python runtime
#     3. Run module-level imports (fastapi, pydantic, etc.)
#     4. Call your handler function
#
#   Timeline:
#     Cold start:   ████████████████░░░░░░░░  3-5s (Python + FastAPI)
#     Warm call:    ██░░░░░░░░░░░░░░░░░░░░░░  50-100ms
#
#   Lambda keeps the container alive for ~5-15 minutes after the
#   last request. If no requests come in, container is destroyed.
#   Next request = cold start again.
#
#   Reducing cold starts:
#     - Use ARM64 (Graviton) — ~34% faster cold starts
#     - Minimize deployment package size (remove test files, unused deps)
#     - Use Layers for large dependencies
#     - Provisioned Concurrency — keeps N instances warm ($$$)
#       → Used in sphinx_story-service for latency-critical endpoints
#     - SnapStart (Java only) — caches initialized state
#
#   Provisioned Concurrency:
#     Lambda → Configuration → Provisioned concurrency → Add
#     → Version/Alias: prod, Concurrency: 5
#     → AWS keeps 5 warm instances. No cold starts for first 5 concurrent requests.
#     → Cost: ~$14/month per provisioned instance (256MB)
#
#   ── Concurrency ────────────────────────────────────────────
#
#   Each incoming request gets its OWN Lambda instance. If 100
#   requests arrive simultaneously, 100 instances spin up.
#
#   ┌─────────┐
#   │ Request1│ ──► Lambda Instance 1 (new or warm)
#   │ Request2│ ──► Lambda Instance 2 (new)
#   │ Request3│ ──► Lambda Instance 3 (new)
#   │ ...     │
#   │Request100──► Lambda Instance 100 (new)
#   └─────────┘
#
#   Limits:
#     Default:  1000 concurrent executions per region (across ALL functions)
#     Reserved: Carve out a guaranteed portion for one function
#               e.g., book-store-api gets 100 reserved → other functions share 900
#     Burst:    3000 in us-east-1, 1000 in most regions (initial burst)
#
#   If you hit the limit:
#     → Additional requests get THROTTLED (429 Too Many Requests)
#     → API Gateway retries throttled requests (with backoff)
#
#   ── Layers ─────────────────────────────────────────────────
#
#   Shared dependency packages that attach to Lambda functions.
#   Keeps your deployment zip small, speeds up deploys.
#
#   Without layers:
#     deployment.zip (15MB) = your code + ALL dependencies
#     Every deploy uploads 15MB even if only code changed.
#
#   With layers:
#     Layer (14MB) = fastapi, pydantic, uvicorn, mangum (rarely changes)
#     deployment.zip (100KB) = just your code (changes often)
#
#   Create a layer:
#     mkdir python && pip install fastapi mangum -t python/
#     zip -r fastapi-layer.zip python/
#     Lambda → Layers → Create layer → upload zip
#     Lambda → function → Layers → Add layer → select it
#
#   Max 5 layers per function. Total unzipped size: 250 MB.
#   Layers are versioned — update the layer, functions still use old version
#   until you explicitly point them to the new version.
#
#   ── Aliases & Versions ─────────────────────────────────────
#
#   Versions are immutable snapshots of your function.
#   Aliases are named pointers to versions (like git tags).
#
#     $LATEST → always the most recent code (mutable)
#     Version 1 → snapshot of code at time of publish (immutable)
#     Version 2 → newer snapshot
#     "prod" alias → points to Version 2
#     "staging" alias → points to $LATEST
#
#   Traffic shifting (canary deploys):
#     Alias "prod" → 90% to Version 2, 10% to Version 3
#     Monitor errors → if Version 3 is stable, shift to 100%
#     Lambda → Aliases → prod → Edit → Weighted alias → add Version 3 at 10%
#
#   ── Destinations ───────────────────────────────────────────
#
#   After your function finishes, Lambda can automatically send
#   the result somewhere. Useful for async pipelines.
#
#     Success → SQS queue, SNS topic, EventBridge, another Lambda
#     Failure → SQS queue (dead letter), SNS (alert), EventBridge
#
#   Unlike Dead Letter Queues (DLQ), destinations include the
#   full event, response, and error — better for debugging.
#
#   ── Pricing ────────────────────────────────────────────────
#
#   Two components:
#     Requests:   $0.20 per 1M invocations
#     Duration:   $0.0000166667 per GB-second
#
#   Example — 1000 requests/day, 256MB, avg 200ms:
#     Requests:   30,000/month × ($0.20/1M) = $0.006
#     Duration:   30,000 × 0.2s × 0.25GB = 1,500 GB-s
#                 1,500 × $0.0000166667 = $0.025
#     Total:      ~$0.03/month (practically free!)
#
#   Free tier (every month, forever):
#     1M requests + 400,000 GB-seconds
#     = ~3.2M invocations at 128MB with 1s duration
#
#   Cost comparison with ECS:
#     Lambda 1000 req/day:  ~$0.03/month
#     ECS Fargate 1 task:   ~$15/month + ALB $16 + NAT $32 = ~$63/month
#     Lambda wins massively for low-traffic APIs.
