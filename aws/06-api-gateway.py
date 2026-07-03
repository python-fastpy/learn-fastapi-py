# ══════════════════════════════════════════════════════════════════
# AWS Deployment — API Gateway (Step 5)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 05-lambda.py  |  next: 07-ecr.py →

# ╔══════════════════════════════════════════════════╗
# ║   STEP 5: API GATEWAY — FRONT DOOR FOR LAMBDA   ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Managed HTTP endpoint that sits in front of Lambda.
#       Handles routing, auth, throttling, CORS, caching.
#       Clients call API Gateway URL → API Gateway invokes Lambda.
#
#   Client                 API Gateway              Lambda
#   ┌──────┐   HTTPS      ┌───────────┐  invoke   ┌──────────┐
#   │ curl │──────────────►│  Routes   │──────────►│ handler()│
#   │      │◄──────────────│  Auth     │◄──────────│ return   │
#   └──────┘   response   │  CORS     │  response └──────────┘
#                          │  Throttle │
#                          └───────────┘
#
# ── API Gateway Types ───────────────────────────────────────
#
#   ┌─────────────┬────────────────────────────────────────────┐
#   │ REST API    │ Full-featured: caching, WAF, request       │
#   │             │ validation, usage plans, API keys.          │
#   │             │ Used by sphinx_story-service.               │
#   ├─────────────┼────────────────────────────────────────────┤
#   │ HTTP API    │ Simpler, 70% cheaper, lower latency.       │
#   │             │ Good for most apps. Missing: caching,       │
#   │             │ request validation, usage plans.             │
#   ├─────────────┼────────────────────────────────────────────┤
#   │ WebSocket   │ Real-time bidirectional: chat, live feeds. │
#   │ API         │ Not used in these repos.                    │
#   └─────────────┴────────────────────────────────────────────┘
#
# ── REST API Endpoint Types ─────────────────────────────────
#
#   ┌──────────────┬───────────────────────────────────────────┐
#   │ EDGE         │ Routes through CloudFront edge locations. │
#   │ (default)    │ Best for global users.                     │
#   │              │ sphinx_story-service uses this in eu-west-1│
#   ├──────────────┼───────────────────────────────────────────┤
#   │ REGIONAL     │ Direct to region. No built-in CloudFront. │
#   │              │ Use when you add your own CDN, or all     │
#   │              │ users are in one region.                    │
#   │              │ sphinx_story-service uses this in us-east-1│
#   ├──────────────┼───────────────────────────────────────────┤
#   │ PRIVATE      │ Only accessible from within a VPC.        │
#   │              │ For internal microservice-to-microservice. │
#   └──────────────┴───────────────────────────────────────────┘
#
# ── Option A: HTTP API (Simpler — Start Here) ───────────────
#
#   1. AWS Console → search "API Gateway" → click API Gateway
#
#   2. Click "Create API"
#
#   3. Find "HTTP API" section → click "Build"
#
#   4. Add integration:
#      ┌──────────────────────────────────────────────────┐
#      │  Integration type: Lambda                         │
#      │  AWS Region:       your region                    │
#      │  Lambda function:  book-store-api                 │
#      │  API name:         book-store-http-api            │
#      └──────────────────────────────────────────────────┘
#      → Next
#
#   5. Configure routes:
#      ┌──────────────────────────────────────────────────┐
#      │  Method: ANY                                      │
#      │  Resource path: /{proxy+}                         │
#      │  Integration target: book-store-api               │
#      │                                                    │
#      │  /{proxy+} is a catch-all — ANY method, ANY path  │
#      │  goes to Lambda. FastAPI handles routing inside.   │
#      └──────────────────────────────────────────────────┘
#      → Next
#
#   6. Stages:
#      ┌──────────────────────────────────────────────────┐
#      │  Stage name: $default                             │
#      │  Auto-deploy: ✅ enabled                          │
#      └──────────────────────────────────────────────────┘
#      → Next → Create
#
#   7. Copy the "Invoke URL":
#      https://<api-id>.execute-api.<region>.amazonaws.com
#
#   8. Test:
#      curl https://<api-id>.execute-api.<region>.amazonaws.com/health
#      curl -X POST https://<api-id>.execute-api.<region>.amazonaws.com/books \
#           -H "Content-Type: application/json" \
#           -d '{"title":"1984","author":"Orwell","price":9.99}'
#
# ── Option B: REST API (Full Featured) ──────────────────────
#
#   1. API Gateway → "Create API"
#
#   2. Find "REST API" section → "Build" (NOT "REST API Private")
#
#   3. Settings:
#      ┌──────────────────────────────────────────────────┐
#      │  ○ New API                                        │
#      │  API name:     book-store-rest-api                │
#      │  Description:  Book Store REST API                │
#      │  API endpoint type: EDGE                          │
#      │                                                    │
#      │  EDGE = requests route through CloudFront edge    │
#      │  locations. Client in Tokyo → Tokyo edge →        │
#      │  eu-west-1 Lambda. Reduces latency.               │
#      └──────────────────────────────────────────────────┘
#      → Create API
#
#   4. Create a proxy resource (catch-all):
#      → Actions → Create Resource
#      ┌──────────────────────────────────────────────────┐
#      │  ✅ Configure as proxy resource                   │
#      │  Resource path: /{proxy+}                         │
#      │  ✅ Enable API Gateway CORS                       │
#      └──────────────────────────────────────────────────┘
#      → Create Resource
#
#   5. Setup Lambda integration:
#      → ANY method appears → click it
#      ┌──────────────────────────────────────────────────┐
#      │  Integration type: Lambda Function Proxy          │
#      │  ✅ Use Lambda Proxy integration                  │
#      │  Lambda Region: your region                       │
#      │  Lambda Function: book-store-api                  │
#      └──────────────────────────────────────────────────┘
#      → Save → OK (grant API Gateway permission to invoke Lambda)
#
#   6. Deploy the API:
#      → Actions → Deploy API
#      ┌──────────────────────────────────────────────────┐
#      │  Deployment stage: [New Stage]                    │
#      │  Stage name: v1                                   │
#      └──────────────────────────────────────────────────┘
#      → Deploy
#
#   7. Copy the Invoke URL:
#      https://<api-id>.execute-api.<region>.amazonaws.com/v1
#
#   8. Test:
#      curl https://<api-id>.execute-api.<region>.amazonaws.com/v1/health
#
# ── Authorizers (How Auth Works) ─────────────────────────────
#
#   sphinx_story-service uses TOKEN authorizer:
#     authorizer:
#       type: TOKEN
#       authorizerId: ww0429
#
#   This means a separate Lambda validates the JWT token before
#   your function runs. Types:
#
#   ┌───────────────┬──────────────────────────────────────┐
#   │ TOKEN         │ Lambda receives the token, validates  │
#   │ (Lambda)      │ it, returns an IAM policy. Cached.    │
#   ├───────────────┼──────────────────────────────────────┤
#   │ REQUEST       │ Lambda receives full request (headers,│
#   │ (Lambda)      │ query params). More context.           │
#   ├───────────────┼──────────────────────────────────────┤
#   │ COGNITO       │ AWS Cognito User Pool validates JWT.  │
#   │               │ No Lambda needed. Simplest.            │
#   ├───────────────┼──────────────────────────────────────┤
#   │ IAM           │ AWS Signature V4. For service-to-     │
#   │               │ service calls. No user tokens.         │
#   └───────────────┴──────────────────────────────────────┘
#
# ── Shared API Gateway (Advanced) ───────────────────────────
#
#   In production, multiple services share ONE API Gateway:
#
#     API Gateway (g4tcha4jva)
#       ├─ /v6/stories/*  → stories Lambda
#       ├─ /v6/assets/*   → assets Lambda
#       ├─ /v6/alerts/*   → alerts Lambda
#       └─ /v6/search/*   → search Lambda
#
#   Each service references the SAME gateway by ID:
#     apiGateway:
#       restApiId: g4tcha4jva
#       restApiRootResourceId: ahxjdtil2b
#
#   Benefits:
#     - One URL for everything (api.sphinx-test.thomsonreuters.com)
#     - Shared authorizer (one JWT validation for all services)
#     - Lower cost (fewer API Gateways)
