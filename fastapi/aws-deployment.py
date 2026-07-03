# ══════════════════════════════════════════════════════════════════
# AWS Deployment — Complete Guide (FastAPI on Every AWS Service)
# ══════════════════════════════════════════════════════════════════
# This file teaches every major AWS service by deploying ONE FastAPI app
# two ways: Lambda (serverless) and ECS Fargate (containers).
#
# Patterns are taken from real production repos:
#   - sphinx_story-service     (Lambda + API Gateway)
#   - sphinx_leon-assistant-skills  (ECS Fargate + ALB + Route53)
#
# No code to run here — this is a step-by-step AWS console walkthrough.
# ══════════════════════════════════════════════════════════════════

# ╔══════════════════════════════════════════════════╗
# ║           WHAT WE'RE BUILDING                    ║
# ╚══════════════════════════════════════════════════╝
#
#   User (browser / curl)
#     │
#     ▼
#   Route 53 (DNS: books.yourname.com)
#     │
#     ▼
#   CloudFront (CDN + HTTPS + caching)
#     │
#     ├──► API Gateway → Lambda        (serverless path)
#     │
#     └──► ALB (Load Balancer) → ECS Fargate  (container path)
#               │
#               ├──► S3 (file storage)
#               ├──► CloudWatch (logs & monitoring)
#               └──► Secrets Manager (API keys)
#
# We deploy the SAME FastAPI app both ways so you learn both patterns.


# ╔══════════════════════════════════════════════════╗
# ║          STEP 0: THE FASTAPI APP                 ║
# ╚══════════════════════════════════════════════════╝

# ── 0a. Create project folder ────────────────────────────────────
#   mkdir book-store-api && cd book-store-api

# ── 0b. main.py ──────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
import os

app = FastAPI(title="Book Store API", version="1.0.0")

books_db = {}  # in-memory (replace with DynamoDB/RDS in production)

class Book(BaseModel):
    title: str
    author: str
    price: float
    genre: Optional[str] = None

class BookPatch(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    price: Optional[float] = None
    genre: Optional[str] = None

class BookResponse(Book):
    id: str

@app.get("/health")
def health_check():
    """Every AWS service health-checks this endpoint."""
    return {"status": "ok", "version": "1.0.0", "env": os.getenv("ENV", "local")}

@app.get("/books", response_model=list[BookResponse])
def list_books():
    return [BookResponse(id=k, **v) for k, v in books_db.items()]

@app.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: str):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    return BookResponse(id=book_id, **books_db[book_id])

@app.post("/books", response_model=BookResponse, status_code=201)
def create_book(book: Book):
    book_id = str(uuid.uuid4())[:8]
    books_db[book_id] = book.model_dump()
    return BookResponse(id=book_id, **books_db[book_id])

@app.put("/books/{book_id}", response_model=BookResponse)
def update_book(book_id: str, book: Book):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    books_db[book_id] = book.model_dump()
    return BookResponse(id=book_id, **books_db[book_id])

@app.patch("/books/{book_id}", response_model=BookResponse)
def patch_book(book_id: str, book: BookPatch):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    stored = books_db[book_id]
    updates = book.model_dump(exclude_unset=True)
    stored.update(updates)
    books_db[book_id] = stored
    return BookResponse(id=book_id, **books_db[book_id])

@app.delete("/books/{book_id}")
def delete_book(book_id: str):
    if book_id not in books_db:
        raise HTTPException(status_code=404, detail="Book not found")
    del books_db[book_id]
    return {"message": "Book deleted"}


# ── 0c. pyproject.toml ──────────────────────────────────────────
#   [project]
#   name = "book-store-api"
#   version = "1.0.0"
#   requires-python = ">=3.11"
#   dependencies = [
#       "fastapi==0.115.0",
#       "uvicorn==0.30.0",
#       "mangum==0.19.0",
#   ]

# ── 0d. Test locally first ──────────────────────────────────────
#   uv sync
#   uv run uvicorn main:app --reload --port 8000
#   Open http://localhost:8000/docs  ← Swagger UI
#
#   curl http://localhost:8000/health
#   curl -X POST http://localhost:8000/books \
#        -H "Content-Type: application/json" \
#        -d '{"title":"1984","author":"Orwell","price":9.99}'


# ╔══════════════════════════════════════════════════╗
# ║         STEP 1: VPC — THE NETWORK               ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Virtual Private Cloud — your own isolated network inside AWS.
#       Everything (Lambda, ECS, ALB, RDS) runs inside a VPC.
#
# WHY:  Security. Public internet can only reach what you explicitly expose.
#       Internal services talk over private IPs — never exposed.
#
# ┌─────────────────── VPC (10.0.0.0/16) ──────────────────┐
# │                                                          │
# │  ┌─── AZ-a ────┐  ┌─── AZ-b ────┐                     │
# │  │ Public       │  │ Public       │                     │
# │  │ 10.0.1.0/24  │  │ 10.0.2.0/24  │  ← ALB lives here │
# │  ├──────────────┤  ├──────────────┤                     │
# │  │ Private      │  │ Private      │                     │
# │  │ 10.0.11.0/24 │  │ 10.0.12.0/24 │  ← ECS/Lambda here│
# │  └──────────────┘  └──────────────┘                     │
# │                                                          │
# │  Internet Gateway        NAT Gateway                     │
# │  (public→internet)       (private→internet, 1-way)       │
# └──────────────────────────────────────────────────────────┘
#
# ── VPC Concepts ─────────────────────────────────────────────
#
#   CIDR Block:  IP range for the whole VPC.  10.0.0.0/16 = 65,536 IPs.
#   Subnet:      Slice of the VPC. Each lives in ONE Availability Zone.
#                Public subnet = has route to Internet Gateway.
#                Private subnet = NO direct internet route (uses NAT).
#   AZ:          Availability Zone — physically separate data center.
#                ALB requires subnets in at least 2 AZs.
#   Internet GW: Connects public subnets to the internet (bidirectional).
#   NAT Gateway: Lets private subnets call OUT to internet (pull Docker
#                images, call external APIs) without being reachable FROM
#                internet. One-way only.
#   Route Table: Rules that decide where traffic goes.
#                Public RT:  0.0.0.0/0 → Internet Gateway
#                Private RT: 0.0.0.0/0 → NAT Gateway
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. Open AWS Console → search "VPC" → click VPC Dashboard
#
#   2. Click "Create VPC" (top-right orange button)
#
#   3. Select "VPC and more" (NOT "VPC only" — this auto-creates
#      subnets, route tables, internet gateway, NAT gateway for you)
#
#   4. Fill in:
#      ┌──────────────────────────────────────────────────┐
#      │  Name tag auto-generation: book-store             │
#      │  IPv4 CIDR block:         10.0.0.0/16            │
#      │  IPv6:                    No                      │
#      │  Tenancy:                 Default                 │
#      │  Number of AZs:           2                       │
#      │  Number of public subnets:  2                     │
#      │  Number of private subnets: 2                     │
#      │  NAT gateways:            In 1 AZ (saves money)  │
#      │  VPC endpoints:           None                    │
#      │  DNS hostnames:           Enable                  │
#      │  DNS resolution:          Enable                  │
#      └──────────────────────────────────────────────────┘
#      TIP: "In 1 AZ" for NAT saves ~$32/month vs per-AZ.
#           Use "1 per AZ" in production for high availability.
#
#   5. Review the preview diagram on the right — you'll see:
#      - 1 VPC
#      - 2 public subnets (one per AZ)
#      - 2 private subnets (one per AZ)
#      - 1 Internet Gateway
#      - 1 NAT Gateway
#      - Route tables auto-wired
#
#   6. Click "Create VPC" → wait ~2 minutes
#
#   7. Note down these IDs (you'll need them later):
#      - VPC ID:              vpc-0abc123...
#      - Public subnet IDs:   subnet-0pub1..., subnet-0pub2...
#      - Private subnet IDs:  subnet-0prv1..., subnet-0prv2...
#
# ── Security Groups ─────────────────────────────────────────
#
# Security Group = virtual firewall. Attached to each resource.
# Stateful: if you allow inbound, the response is auto-allowed out.
#
#   1. VPC → Security Groups → "Create security group"
#
#   2. ALB Security Group:
#      ┌──────────────────────────────────────────────────┐
#      │  Name:        book-store-alb-sg                   │
#      │  Description: Allow HTTP/HTTPS from internet      │
#      │  VPC:         book-store-vpc                      │
#      │                                                    │
#      │  Inbound rules:                                   │
#      │    Type        Port    Source                      │
#      │    HTTP        80      0.0.0.0/0 (anywhere)       │
#      │    HTTPS       443     0.0.0.0/0 (anywhere)       │
#      │                                                    │
#      │  Outbound rules:                                  │
#      │    All traffic   All    0.0.0.0/0                 │
#      └──────────────────────────────────────────────────┘
#
#   3. App Security Group:
#      ┌──────────────────────────────────────────────────┐
#      │  Name:        book-store-app-sg                   │
#      │  Description: Allow traffic only from ALB         │
#      │  VPC:         book-store-vpc                      │
#      │                                                    │
#      │  Inbound rules:                                   │
#      │    Type          Port    Source                    │
#      │    Custom TCP    8000    book-store-alb-sg         │
#      │                         ↑ select the ALB SG       │
#      │                         NOT an IP — a SG ref      │
#      │                                                    │
#      │  Outbound rules:                                  │
#      │    All traffic   All    0.0.0.0/0                 │
#      └──────────────────────────────────────────────────┘
#      WHY inbound from ALB SG only?
#        Containers only accept traffic FROM the load balancer.
#        Nobody can hit port 8000 directly — must go through ALB.
#        This is the pattern used in production.


# ╔══════════════════════════════════════════════════╗
# ║         STEP 2: S3 — FILE STORAGE               ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Simple Storage Service. Stores ANY file (images, PDFs, logs,
#       deployment artifacts, static websites). Unlimited storage.
#       Files are called "objects", folders are called "prefixes".
#
# COST: ~$0.023/GB/month. Almost free for small projects.
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console → search "S3" → click S3
#
#   2. Click "Create bucket" (orange button)
#
#   3. Fill in:
#      ┌──────────────────────────────────────────────────┐
#      │  Bucket name: book-store-covers-<your-acct-id>   │
#      │               (must be globally unique!)          │
#      │  AWS Region:  Same as your VPC (e.g. eu-west-1)  │
#      │                                                    │
#      │  Object Ownership: ACLs disabled (recommended)    │
#      │                                                    │
#      │  Block Public Access: ✅ Block ALL (on)           │
#      │  (We serve files via CloudFront, not direct S3)   │
#      │                                                    │
#      │  Bucket Versioning: ✅ Enable                     │
#      │  (Recover accidentally deleted/overwritten files)  │
#      │                                                    │
#      │  Encryption: SSE-S3 (default, free)               │
#      └──────────────────────────────────────────────────┘
#
#   4. Click "Create bucket"
#
#   5. Test: Click into the bucket → "Upload" → drag any image
#      → "Upload". You'll see it listed.
#
# ── Key S3 Concepts ─────────────────────────────────────────
#
#   Bucket:      Top-level container. Name is globally unique across ALL
#                AWS accounts. Like a drive letter.
#   Object:      A file. Identified by key (path): "covers/abc123.jpg"
#   Prefix:      Folder-like path: "covers/" — not a real folder, just
#                a naming convention. S3 is flat storage.
#   Versioning:  Keep every version of every object. Can recover deleted files.
#   Lifecycle:   Auto-move old objects to cheaper storage or delete them.
#   ACL vs Policy: Use bucket policies (JSON). ACLs are legacy.
#
#   Storage Classes:
#     Standard         → frequent access ($0.023/GB)
#     Infrequent (IA)  → rarely accessed ($0.0125/GB, retrieval fee)
#     Glacier          → archive, minutes-to-hours retrieval ($0.004/GB)
#     Glacier Deep     → long-term archive, 12-hour retrieval ($0.00099/GB)
#
# ── S3 Bucket Policy (allow CloudFront to read) ─────────────
#
#   Bucket → Permissions → Bucket policy → paste:
#
#   {
#     "Version": "2012-10-17",
#     "Statement": [{
#       "Sid": "AllowCloudFrontOAC",
#       "Effect": "Allow",
#       "Principal": {"Service": "cloudfront.amazonaws.com"},
#       "Action": "s3:GetObject",
#       "Resource": "arn:aws:s3:::book-store-covers-<acct-id>/*",
#       "Condition": {
#         "StringEquals": {
#           "AWS:SourceArn": "arn:aws:cloudfront::<acct-id>:distribution/<dist-id>"
#         }
#       }
#     }]
#   }
#   (You'll fill in <dist-id> after creating CloudFront in Step 10)


# ╔══════════════════════════════════════════════════╗
# ║       STEP 3: EC2 — VIRTUAL MACHINES             ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Elastic Compute Cloud. A virtual server you fully control.
#       You manage OS, patches, scaling, uptime — everything.
#
# WHY LEARN: EC2 underlies ECS (containers run ON EC2 or Fargate).
#            Understanding EC2 makes Lambda/ECS/Fargate make sense.
#
# WHY WE DON'T USE IT DIRECTLY:
#   - You must patch OS, handle failures, scale manually
#   - If the instance dies, your app dies (no auto-replacement)
#   - ECS Fargate and Lambda remove this burden
#   → Learn it, deploy to it once, then use Fargate/Lambda instead.
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console → search "EC2" → click EC2 Dashboard
#
#   2. Click "Launch instance" (orange button)
#
#   3. Fill in:
#      ┌──────────────────────────────────────────────────┐
#      │  Name:           book-store-ec2                   │
#      │                                                    │
#      │  AMI:            Amazon Linux 2023                │
#      │                  (free tier eligible)              │
#      │                                                    │
#      │  Instance type:  t3.micro (free tier)             │
#      │                                                    │
#      │  Key pair:       Click "Create new key pair"       │
#      │    Name:         book-store-key                    │
#      │    Type:         RSA                               │
#      │    Format:       .pem (Linux/Mac) or .ppk (PuTTY) │
#      │    → DOWNLOAD the .pem file! You can't get it     │
#      │      again. Store it safely.                       │
#      │                                                    │
#      │  Network settings → Edit:                         │
#      │    VPC:          book-store-vpc                    │
#      │    Subnet:       Public subnet (either AZ)        │
#      │    Auto-assign public IP: Enable                  │
#      │    Security group: Create new                     │
#      │      Allow SSH (22) from My IP                    │
#      │      Add rule: Custom TCP, port 8000, 0.0.0.0/0  │
#      │                                                    │
#      │  Storage:        8 GB gp3 (default, free tier)    │
#      └──────────────────────────────────────────────────┘
#
#   4. Click "Launch instance"
#
#   5. Wait for "Running" status → copy the Public IPv4 address
#
# ── SSH In & Deploy ─────────────────────────────────────────
#
#   # On your local machine:
#   chmod 400 book-store-key.pem   # (Linux/Mac — set read-only)
#   ssh -i book-store-key.pem ec2-user@<public-ip>
#
#   # On the EC2 instance:
#   sudo dnf install python3.11 -y
#   curl -LsSf https://astral.sh/uv/install.sh | sh   # install uv
#   source $HOME/.local/bin/env                        # add uv to PATH
#   mkdir app && cd app
#
#   # Create main.py and pyproject.toml (paste from Step 0 above)
#   uv sync
#
#   # Run the app
#   uv run uvicorn main:app --host 0.0.0.0 --port 8000
#
#   # Test from your local machine:
#   curl http://<public-ip>:8000/health
#   # → {"status":"ok","version":"1.0.0","env":"local"}
#
# ── EC2 Key Concepts ────────────────────────────────────────
#
#   AMI:             Amazon Machine Image — the OS template.
#                    Amazon Linux, Ubuntu, Windows, etc.
#   Instance Type:   CPU + memory combo. t3.micro = 2 vCPU, 1GB RAM.
#                    t=burstable, m=general, c=compute, r=memory, g=GPU.
#   Key Pair:        SSH key for remote access. Private key stays with you.
#   Elastic IP:      Static public IP. Without it, IP changes on restart.
#   EBS Volume:      Disk storage attached to EC2. Persists independently.
#   User Data:       Script that runs on first boot (automate setup).
#   Instance State:  Running (billed) → Stopped (no compute cost, EBS billed)
#                    → Terminated (deleted forever).
#
# ── IMPORTANT: Terminate When Done ──────────────────────────
#
#   EC2 → select instance → Instance state → Terminate instance
#   (Stopped instances still cost money for EBS storage)


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
#   Handler:       Entry point. format: filename.function_name
#                  "lambda_handler.handler" = lambda_handler.py → handler()
#   Cold Start:    First invocation after idle. Lambda must download code,
#                  start runtime, import modules. Takes 1-5s for Python.
#                  Subsequent calls reuse the warm container (~50ms).
#   Concurrency:   Each request gets its own Lambda instance.
#                  Default limit: 1000 concurrent executions per region.
#   Layers:        Shared code/dependencies packaged separately.
#                  Attach to multiple functions. Max 5 layers.
#   Aliases:       Named pointers to versions. $LATEST, prod, staging.
#   Destinations:  Send success/failure results to SQS, SNS, EventBridge.
#   Pricing:       $0.20 per 1M requests + $0.0000166667 per GB-second.
#                  Free tier: 1M requests + 400,000 GB-seconds/month.


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


# ╔══════════════════════════════════════════════════╗
# ║  STEP 6: ECR — CONTAINER REGISTRY               ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Elastic Container Registry. AWS's Docker Hub.
#       Stores your Docker images. ECS pulls from here.
#
#   You (laptop)           ECR                   ECS
#   ┌──────────┐  push   ┌──────────┐  pull   ┌──────────┐
#   │ docker   │────────►│ image:v1 │────────►│ container│
#   │ build    │         │ image:v2 │         │ running  │
#   └──────────┘         └──────────┘         └──────────┘
#
# ── 6a. Create Dockerfile ───────────────────────────────────
#
#   Create Dockerfile in your book-store-api/ folder:
#
#     FROM python:3.11-slim
#     COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
#     WORKDIR /app
#     COPY pyproject.toml uv.lock ./
#     RUN uv sync --frozen --no-dev
#     COPY main.py .
#     EXPOSE 8000
#     CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#
# ── 6b. Test Docker locally ─────────────────────────────────
#
#   docker build -t book-store-api .
#   docker run -p 8000:8000 book-store-api
#   curl http://localhost:8000/health
#
# ── 6c. AWS Console Steps ───────────────────────────────────
#
#   1. AWS Console → search "ECR" → click Elastic Container Registry
#
#   2. Click "Create repository"
#      ┌──────────────────────────────────────────────────┐
#      │  Visibility:      Private                         │
#      │  Repository name: book-store-api                  │
#      │  Tag immutability: Disabled (allow tag overwrite) │
#      │  Scan on push:    ✅ Enabled (vulnerability scan)│
#      │  Encryption:      AES-256 (default)               │
#      └──────────────────────────────────────────────────┘
#      → Create repository
#
#   3. Click into "book-store-api" → "View push commands" (button)
#      AWS shows you the exact commands. They look like:
#
#      # Authenticate Docker to ECR
#      aws ecr get-login-password --region <region> | \
#        docker login --username AWS --password-stdin \
#        <account-id>.dkr.ecr.<region>.amazonaws.com
#
#      # Build (arm64 for ECS Fargate — matches production)
#      docker build --platform linux/arm64 -t book-store-api .
#
#      # Tag
#      docker tag book-store-api:latest \
#        <account-id>.dkr.ecr.<region>.amazonaws.com/book-store-api:v1
#
#      # Push
#      docker push \
#        <account-id>.dkr.ecr.<region>.amazonaws.com/book-store-api:v1
#
#   4. Refresh the ECR page — you'll see image tag "v1" listed.


# ╔══════════════════════════════════════════════════╗
# ║  STEP 7: ECS + FARGATE — MANAGED CONTAINERS     ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Elastic Container Service runs Docker containers.
#       Fargate = serverless compute for containers.
#       No EC2 instances to manage. AWS handles the servers.
#
# REAL REPO: sphinx_leon-assistant-skills deploys each skill
#            (story-drafting, urgent-drafting, text-archive) as
#            Fargate tasks behind ALBs.
#
# ECS Hierarchy:
#   Cluster → Service → Task → Container
#
#   Cluster:   Logical grouping (like a "project")
#   Service:   Keeps N tasks running. Replaces unhealthy ones.
#              Connects to load balancer.
#   Task Def:  Blueprint: which image, how much CPU/RAM, env vars,
#              ports, IAM roles, logging config.
#   Task:      Running instance of a Task Definition (= running container).
#
# ── 7a. Create ECS Cluster ──────────────────────────────────
#
#   1. AWS Console → search "ECS" → click Elastic Container Service
#
#   2. Click "Create cluster"
#      ┌──────────────────────────────────────────────────┐
#      │  Cluster name: book-store-cluster                 │
#      │                                                    │
#      │  Infrastructure:                                  │
#      │    ✅ AWS Fargate (serverless)  ← select this     │
#      │    ☐ Amazon EC2 instances                         │
#      │                                                    │
#      │  Monitoring:                                      │
#      │    ✅ Use Container Insights (CloudWatch)         │
#      └──────────────────────────────────────────────────┘
#      → Create
#
# ── 7b. Create Task Definition ──────────────────────────────
#
#   1. ECS → Task definitions → "Create new task definition"
#
#   2. Step 1 — Task definition family:
#      ┌──────────────────────────────────────────────────┐
#      │  Task definition family: book-store-task          │
#      │                                                    │
#      │  Launch type: AWS Fargate                         │
#      │  OS:          Linux/ARM64                         │
#      │    (matches our Docker build --platform arm64)    │
#      │                                                    │
#      │  CPU:    0.5 vCPU                                 │
#      │  Memory: 1 GB                                     │
#      │                                                    │
#      │  Task role:      Create new (or ecsTaskRole)      │
#      │    → for app permissions (S3, Secrets, etc.)      │
#      │  Execution role: ecsTaskExecutionRole             │
#      │    → for ECS to pull image + write logs           │
#      └──────────────────────────────────────────────────┘
#
#   3. Step 2 — Container definition:
#      ┌──────────────────────────────────────────────────┐
#      │  Container name: book-store-container             │
#      │  Image URI:      <acct>.dkr.ecr.<region>.        │
#      │                  amazonaws.com/book-store-api:v1  │
#      │  Essential:      Yes                              │
#      │                                                    │
#      │  Port mappings:                                   │
#      │    Container port: 8000                           │
#      │    Protocol:       TCP                            │
#      │    App protocol:   HTTP                           │
#      │                                                    │
#      │  Environment variables:                           │
#      │    ENV = production                               │
#      │                                                    │
#      │  Log configuration:                               │
#      │    Log driver:     awslogs                        │
#      │    awslogs-group:  /ecs/book-store                │
#      │    awslogs-region: <your region>                  │
#      │    awslogs-stream-prefix: book-store              │
#      └──────────────────────────────────────────────────┘
#
#   4. Click "Create" → Task definition created.
#
#   TWO IAM ROLES explained:
#     Task Role       → What YOUR APP can access (S3, DynamoDB, Secrets)
#     Execution Role  → What ECS needs (pull ECR image, write CloudWatch)
#     These are separate because ECS (the platform) needs different
#     permissions than your application code.
#
# ── 7c. Create ECS Service ──────────────────────────────────
#
#   (Do Step 8 first to create the ALB, then come back here)
#
#   1. ECS → Clusters → book-store-cluster → "Create service"
#
#   2. Fill in:
#      ┌──────────────────────────────────────────────────┐
#      │  Launch type:      Fargate                        │
#      │  Platform version: LATEST                         │
#      │                                                    │
#      │  Task definition:                                 │
#      │    Family:   book-store-task                       │
#      │    Revision: LATEST                               │
#      │                                                    │
#      │  Service name:     book-store-service              │
#      │  Desired tasks:    2                               │
#      │    (2 containers for high availability)            │
#      │                                                    │
#      │  Networking:                                      │
#      │    VPC:            book-store-vpc                  │
#      │    Subnets:        Select PRIVATE subnets (both)  │
#      │    Security group: book-store-app-sg              │
#      │    Public IP:      DISABLED                       │
#      │      (containers are private — ALB is public)     │
#      │                                                    │
#      │  Load balancing:                                  │
#      │    Type:              Application Load Balancer   │
#      │    Load balancer:     book-store-alb (from Step 8)│
#      │    Target group:      book-store-tg               │
#      │    Container:         book-store-container : 8000 │
#      │    Health check grace: 120 seconds                │
#      │      (give container time to start up)            │
#      └──────────────────────────────────────────────────┘
#
#   3. Click "Create" → ECS pulls image, starts 2 tasks.
#
#   4. Check: ECS → your cluster → Tasks tab → should see
#      2 tasks with "RUNNING" status.


# ╔══════════════════════════════════════════════════╗
# ║   STEP 8: ALB — APPLICATION LOAD BALANCER        ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Distributes incoming traffic across multiple containers.
#       Health-checks each target. Removes unhealthy ones.
#       Layer 7 (HTTP) — can route based on URL path, headers, etc.
#
# REAL REPO: Skills use a shared ALB with path-based routing:
#   /story-drafting/*  → Story Drafting Target Group
#   /urgent-drafting/* → Urgent Drafting Target Group
#   /text-archive/*    → Text Archive Target Group
#
#   Client
#     │
#     ▼
#   ALB (public subnets)
#     │
#     ├── /books/*   → Target Group → ECS Task 1, Task 2
#     └── /search/*  → Target Group → ECS Task 3, Task 4
#
# ── Load Balancer Types ─────────────────────────────────────
#
#   ┌──────────────┬───────┬──────────────────────────────────┐
#   │ ALB          │ L7    │ HTTP routing, path-based, host-  │
#   │ (Application)│(HTTP) │ based. WebSocket support. Best   │
#   │              │       │ for web apps & APIs. USED HERE.  │
#   ├──────────────┼───────┼──────────────────────────────────┤
#   │ NLB          │ L4    │ TCP/UDP. Ultra-low latency.      │
#   │ (Network)    │(TCP)  │ Millions of req/sec. Static IP.  │
#   │              │       │ For gaming, IoT, gRPC.            │
#   ├──────────────┼───────┼──────────────────────────────────┤
#   │ GWLB         │ L3    │ Inline security appliances.      │
#   │ (Gateway)    │(IP)   │ Firewalls, IDS/IPS. Rare.        │
#   └──────────────┴───────┴──────────────────────────────────┘
#
# ── 8a. Create Target Group ─────────────────────────────────
#
#   1. EC2 → Target Groups → "Create target group"
#
#   2. Fill in:
#      ┌──────────────────────────────────────────────────┐
#      │  Target type: IP addresses                        │
#      │    (Fargate uses IPs — no EC2 instances)          │
#      │                                                    │
#      │  Target group name: book-store-tg                 │
#      │  Protocol:          HTTP                          │
#      │  Port:              8000                          │
#      │  VPC:               book-store-vpc                │
#      │  Protocol version:  HTTP1                         │
#      │                                                    │
#      │  Health check settings:                           │
#      │    Protocol:        HTTP                          │
#      │    Path:            /health                        │
#      │    Port:            traffic port                   │
#      │    Healthy threshold:   2                          │
#      │    Unhealthy threshold: 5                          │
#      │    Timeout:         30 seconds                    │
#      │    Interval:        60 seconds                    │
#      │    Success codes:   200                           │
#      └──────────────────────────────────────────────────┘
#      → Next → Do NOT register targets (ECS does it) → Create
#
# ── 8b. Create ALB ──────────────────────────────────────────
#
#   1. EC2 → Load Balancers → "Create Load Balancer"
#
#   2. Select "Application Load Balancer" → Create
#
#   3. Fill in:
#      ┌──────────────────────────────────────────────────┐
#      │  Load balancer name: book-store-alb               │
#      │  Scheme:            Internet-facing               │
#      │    (internal = only reachable from within VPC)    │
#      │    (internet-facing = reachable from internet)    │
#      │  IP address type:   IPv4                          │
#      │                                                    │
#      │  Network mapping:                                 │
#      │    VPC:     book-store-vpc                        │
#      │    Subnets: ✅ both PUBLIC subnets                │
#      │    (ALB lives in public subnets, routes to private│
#      │     containers)                                    │
#      │                                                    │
#      │  Security groups:                                 │
#      │    ✅ book-store-alb-sg  (HTTP 80 + HTTPS 443)   │
#      │    ✗ remove default SG                            │
#      │                                                    │
#      │  Listeners:                                       │
#      │    HTTP : 80 → Forward to: book-store-tg          │
#      │    (Add HTTPS:443 later with ACM certificate)     │
#      └──────────────────────────────────────────────────┘
#      → Create load balancer
#
#   4. Wait for state: "Active" (~2-3 minutes)
#
#   5. Copy the DNS name:
#      book-store-alb-123456789.eu-west-1.elb.amazonaws.com
#
#   6. Test (after ECS service is created and tasks are running):
#      curl http://book-store-alb-123456789.eu-west-1.elb.amazonaws.com/health
#
# ── 8c. Add HTTPS Listener (After ACM cert) ─────────────────
#
#   1. ALB → Listeners tab → "Add listener"
#      ┌──────────────────────────────────────────────────┐
#      │  Protocol: HTTPS                                  │
#      │  Port:     443                                    │
#      │  Default action: Forward to book-store-tg         │
#      │  Security policy: ELBSecurityPolicy-TLS13-1-2-... │
#      │  Certificate: Select from ACM (create in Step 10) │
#      └──────────────────────────────────────────────────┘
#
#   2. Edit HTTP:80 listener → Change action to Redirect:
#      ┌──────────────────────────────────────────────────┐
#      │  Redirect to: HTTPS : 443                        │
#      │  Status code: 301 (permanent)                     │
#      └──────────────────────────────────────────────────┘
#      This is the exact pattern from the production ALB:
#      HTTP → 301 redirect to HTTPS
#
# ── Path-Based Routing (Multiple Services) ──────────────────
#
#   To route different paths to different target groups:
#
#   ALB → HTTPS:443 listener → "Manage rules" → Add rule:
#      ┌──────────────────────────────────────────────────┐
#      │  Rule 1 (priority 100):                           │
#      │    IF path is /books or /books/*                  │
#      │    THEN forward to: books-target-group            │
#      │                                                    │
#      │  Rule 2 (priority 110):                           │
#      │    IF path is /search or /search/*                │
#      │    THEN forward to: search-target-group           │
#      │                                                    │
#      │  Default:                                         │
#      │    Return 404 {"error": "Not found"}              │
#      └──────────────────────────────────────────────────┘


# ╔══════════════════════════════════════════════════╗
# ║  STEP 9: CLOUDWATCH — LOGGING & MONITORING       ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Centralized logs, metrics, alarms, dashboards.
#       Everything in AWS sends data to CloudWatch.
#
# REAL REPO:
#   Lambda logs:  /aws/lambda/a207920-spx-ci-v6-euw1-story-stories-lambda
#                 Retention: 3 days (dev), 7 days (prod)
#   ECS logs:     /aws/ecs/dev-story-drafting-service
#                 Retention: 1 month
#
# ── What Gets Created Automatically ─────────────────────────
#
#   ┌───────────┬──────────────────────────┬────────────────┐
#   │ Source    │ Log Group                 │ Who Creates It │
#   ├───────────┼──────────────────────────┼────────────────┤
#   │ Lambda   │ /aws/lambda/book-store-api│ Lambda service │
#   │ ECS      │ /ecs/book-store           │ Task definition│
#   │ API GW   │ Enable in stage settings  │ You (manual)   │
#   │ ALB      │ Access logs → S3 bucket   │ You (manual)   │
#   └───────────┴──────────────────────────┴────────────────┘
#
# ── AWS Console Steps ───────────────────────────────────────
#
# 9a. View Logs:
#
#   1. AWS Console → search "CloudWatch" → click CloudWatch
#
#   2. Left sidebar → Logs → Log groups
#
#   3. Find /aws/lambda/book-store-api → click it
#      → Click any log stream → see your Lambda execution logs
#      → Every print() and exception traceback appears here
#
#   4. Find /ecs/book-store → click it
#      → See uvicorn startup logs, request logs, errors
#
# 9b. Set Log Retention:
#
#   1. Click on a log group → Actions → "Edit retention setting"
#      ┌──────────────────────────────────────────────────┐
#      │  Retention period: 1 month  (saves cost)         │
#      │  (default is "Never expire" — expensive!)         │
#      └──────────────────────────────────────────────────┘
#
# 9c. Create Alarm:
#
#   1. CloudWatch → Alarms → "Create alarm"
#
#   2. Select metric:
#      → AWS/Lambda → By Function Name
#      → book-store-api → Errors
#      → Select metric
#
#   3. Configure:
#      ┌──────────────────────────────────────────────────┐
#      │  Statistic:  Sum                                  │
#      │  Period:     5 minutes                            │
#      │  Threshold:  Static                               │
#      │  Condition:  Greater than or equal to 5           │
#      │                                                    │
#      │  → "5 or more errors in 5 minutes triggers alarm"│
#      └──────────────────────────────────────────────────┘
#
#   4. Notification:
#      → Create new SNS topic: book-store-errors
#      → Email: your-email@example.com
#      → You'll get a confirmation email — click confirm!
#
#   5. Name: book-store-high-error-rate → Create alarm
#
# 9d. Create Dashboard:
#
#   1. CloudWatch → Dashboards → "Create dashboard"
#      Name: book-store-dashboard
#
#   2. Add widgets:
#      → Add widget → Line → Select metrics:
#        AWS/Lambda → book-store-api → Invocations, Errors, Duration
#      → Add widget → Number → Select metrics:
#        AWS/ECS → book-store-service → CPUUtilization, MemoryUtilization
#
# ── ECS Auto-Scaling (based on CloudWatch metrics) ──────────
#
#   1. ECS → book-store-cluster → book-store-service
#   2. Click "Update service"
#   3. Scroll to "Service auto scaling"
#      ┌──────────────────────────────────────────────────┐
#      │  ✅ Use service auto scaling                      │
#      │  Minimum tasks: 1                                 │
#      │  Maximum tasks: 5                                 │
#      │  Desired tasks: 2                                 │
#      │                                                    │
#      │  Scaling policy:                                  │
#      │    Policy type: Target tracking                   │
#      │    Policy name: cpu-scaling                       │
#      │    ECS metric:  ECSServiceAverageCPUUtilization   │
#      │    Target value: 70  (scale out when CPU > 70%)   │
#      │    Scale-in cooldown:  60 seconds                 │
#      │    Scale-out cooldown: 60 seconds                 │
#      └──────────────────────────────────────────────────┘
#      → Update


# ╔══════════════════════════════════════════════════╗
# ║  STEP 10: ROUTE 53 + CLOUDFRONT + ACM            ║
# ╚══════════════════════════════════════════════════╝
#
# These three services work together to give you:
#   books.yourname.com → HTTPS → CDN → your app
#
# REAL REPO: Skills ALB gets a Route53 ALIAS record:
#   skills.leon-ci.8335.aws-int.thomsonreuters.com → ALB
#   EDGE API Gateway automatically gets CloudFront.
#
# ── Route 53 (DNS) ──────────────────────────────────────────
#
# WHAT: AWS's DNS service. Translates domain names → IP addresses.
#       Also does health checks and failover routing.
#
# DNS Record Types:
#   ┌────────┬────────────────────────────────────────────────┐
#   │ A      │ Domain → IPv4 address                          │
#   │        │ books.example.com → 1.2.3.4                    │
#   ├────────┼────────────────────────────────────────────────┤
#   │ AAAA   │ Domain → IPv6 address                          │
#   ├────────┼────────────────────────────────────────────────┤
#   │ CNAME  │ Domain → another domain name                   │
#   │        │ books.example.com → alb-123.amazonaws.com      │
#   │        │ CANNOT be used at zone apex (example.com)      │
#   ├────────┼────────────────────────────────────────────────┤
#   │ ALIAS  │ AWS-special: domain → AWS resource             │
#   │        │ books.example.com → ALB / CloudFront / S3      │
#   │        │ CAN be used at zone apex. No extra DNS lookup. │
#   │        │ FREE (no charge for ALIAS queries).             │
#   ├────────┼────────────────────────────────────────────────┤
#   │ MX     │ Email routing (not relevant here)              │
#   ├────────┼────────────────────────────────────────────────┤
#   │ TXT    │ Text records (SPF, domain verification)        │
#   └────────┴────────────────────────────────────────────────┘
#
# Hosted Zone Types:
#   Public  → accessible from internet (books.yourname.com)
#   Private → accessible only from within a VPC (internal DNS)
#             The repo uses private: skills.leon-ci.8335.aws-int...
#
# AWS Console Steps — Route 53:
#
#   Option A: You own a domain (or buy one in Route53 ~$12/year)
#
#   1. Route 53 → Hosted zones → "Create hosted zone"
#      ┌──────────────────────────────────────────────────┐
#      │  Domain name: yourname.com                        │
#      │  Type:        Public hosted zone                  │
#      └──────────────────────────────────────────────────┘
#      → Create
#
#   2. Note the 4 NS (name server) records.
#      If you bought domain elsewhere (GoDaddy, Namecheap),
#      go there and set custom name servers to these 4 values.
#
#   Option B: No domain (for learning)
#     Skip Route 53 — use ALB DNS name or API Gateway URL directly.
#     You can always add DNS later.
#
# ── ACM (Certificate Manager) ───────────────────────────────
#
# WHAT: Free SSL/TLS certificates for HTTPS. Auto-renews.
#       Required for HTTPS on ALB and CloudFront.
#
#   IMPORTANT: For CloudFront, certificate MUST be in us-east-1.
#              For ALB, certificate must be in same region as ALB.
#
# AWS Console Steps — ACM:
#
#   1. Switch region to us-east-1 (for CloudFront)
#      AWS Console → search "Certificate Manager" → ACM
#
#   2. Click "Request certificate"
#      ┌──────────────────────────────────────────────────┐
#      │  Certificate type: Public                         │
#      │                                                    │
#      │  Domain names:                                    │
#      │    books.yourname.com                             │
#      │    *.yourname.com      (wildcard — optional)      │
#      │                                                    │
#      │  Validation method:                               │
#      │    ○ DNS validation (recommended — automatic)     │
#      │      ACM gives you a CNAME record to add to       │
#      │      Route 53. It auto-validates.                  │
#      │    ○ Email validation                              │
#      │      AWS emails domain contacts. Manual.           │
#      └──────────────────────────────────────────────────┘
#      → Request
#
#   3. Click into the certificate → "Create records in Route 53"
#      → AWS auto-creates the validation CNAME records
#      → Status changes to "Issued" within ~5 minutes
#
#   4. Also request a certificate in YOUR ALB region (if different
#      from us-east-1) for ALB HTTPS listener.
#
# ── CloudFront (CDN) ────────────────────────────────────────
#
# WHAT: Content Delivery Network. 400+ edge locations worldwide.
#       Caches content close to users. Also provides HTTPS.
#
#   User (Tokyo) → Tokyo Edge → Origin (eu-west-1 ALB)
#                    ↑
#         cached response if available (static files)
#         or pass-through to origin (API calls)
#
# AWS Console Steps — CloudFront:
#
#   1. AWS Console → search "CloudFront" → CloudFront
#
#   2. Click "Create distribution"
#
#   3. Origin Settings:
#      ┌──────────────────────────────────────────────────┐
#      │  Origin domain:  book-store-alb-123.eu-west-1.   │
#      │                  elb.amazonaws.com               │
#      │                  (select your ALB from dropdown)  │
#      │                                                    │
#      │  Protocol:       HTTP only                        │
#      │    (CloudFront→ALB is internal, no need for HTTPS│
#      │     on that leg. HTTPS is client→CloudFront.)     │
#      │                                                    │
#      │  Origin path:    (leave empty)                    │
#      └──────────────────────────────────────────────────┘
#
#   4. Default Cache Behavior:
#      ┌──────────────────────────────────────────────────┐
#      │  Path pattern:          Default (*)               │
#      │  Viewer protocol:      Redirect HTTP to HTTPS    │
#      │                                                    │
#      │  Allowed HTTP methods:  GET, HEAD, OPTIONS,      │
#      │                         PUT, POST, PATCH, DELETE  │
#      │    (ALL methods — it's an API, not a static site) │
#      │                                                    │
#      │  Cache policy:         CachingDisabled            │
#      │    (API responses should NOT be cached)           │
#      │                                                    │
#      │  Origin request policy: AllViewer                 │
#      │    (forward all headers, cookies to origin)       │
#      └──────────────────────────────────────────────────┘
#
#   5. Add S3 Origin (for static files like book covers):
#      → Click "Add origin"
#      ┌──────────────────────────────────────────────────┐
#      │  Origin domain: book-store-covers-xxx.s3...      │
#      │                 (select your S3 bucket)           │
#      │                                                    │
#      │  Origin access: Origin access control settings   │
#      │                 (OAC — recommended)               │
#      │  → Create new OAC:                                │
#      │    Name: book-store-s3-oac                        │
#      │    Signing: Sign requests (recommended)           │
#      └──────────────────────────────────────────────────┘
#
#   6. Add S3 Behavior:
#      → Behaviors tab → Create behavior
#      ┌──────────────────────────────────────────────────┐
#      │  Path pattern:   /covers/*                        │
#      │  Origin:         S3 bucket origin                 │
#      │  Cache policy:   CachingOptimized                 │
#      │    (static files SHOULD be cached at edge)        │
#      └──────────────────────────────────────────────────┘
#
#   7. Settings:
#      ┌──────────────────────────────────────────────────┐
#      │  Alternate domain names (CNAMEs):                 │
#      │    books.yourname.com                             │
#      │                                                    │
#      │  Custom SSL certificate:                          │
#      │    Select your ACM cert from dropdown             │
#      │    (must be in us-east-1!)                         │
#      │                                                    │
#      │  Default root object: (leave empty for APIs)      │
#      │  Price class: Use all edge locations (or cheaper) │
#      └──────────────────────────────────────────────────┘
#      → Create distribution
#
#   8. Wait for Status: "Deployed" (~5-10 minutes)
#
#   9. Copy the distribution domain:
#      d1234abcdef.cloudfront.net
#
# ── Wire It All Together ────────────────────────────────────
#
#   Route 53 → Create/Update A record:
#      ┌──────────────────────────────────────────────────┐
#      │  Record name: books                               │
#      │  Record type: A                                   │
#      │  ✅ Alias: Yes                                    │
#      │  Route to: Alias to CloudFront distribution       │
#      │  → select your distribution                       │
#      └──────────────────────────────────────────────────┘
#
#   Final test:
#     curl https://books.yourname.com/health
#     curl https://books.yourname.com/books


# ╔══════════════════════════════════════════════════╗
# ║  CLOUDFRONT DEEP DIVE                            ║
# ╚══════════════════════════════════════════════════╝
#
# Step 10 showed how to create a CloudFront distribution.
# This section goes deeper into HOW CloudFront works and
# the advanced features you'll use in production.
#
# ── How CloudFront Works ─────────────────────────────────────
#
#   CloudFront has 3 tiers of infrastructure:
#
#   User (Tokyo)
#     │
#     ▼
#   Edge Location (400+ worldwide)        ← Layer 1: closest to user
#     │  Cache HIT? → return immediately (1-5ms)
#     │  Cache MISS? ↓
#     ▼
#   Regional Edge Cache (13 worldwide)    ← Layer 2: bigger cache, fewer locations
#     │  Cache HIT? → return, also cache at edge
#     │  Cache MISS? ↓
#     ▼
#   Origin (your ALB / S3 / API Gateway)  ← Layer 3: your actual server
#     │  Response flows back through all tiers,
#     │  getting cached at each level
#
#   Edge Location:          Small cache, many locations (low latency)
#   Regional Edge Cache:    Large cache, fewer locations (higher hit rate)
#   Origin:                 Your server (only hit on cache miss)
#
#   POP (Point of Presence): A physical facility containing
#   edge locations. Major cities have multiple POPs.
#
# ── Origins ──────────────────────────────────────────────────
#
#   An "origin" is where CloudFront fetches content when cache misses.
#   One distribution can have MULTIPLE origins.
#
#   ┌─────────────────┬────────────────────────────────────────┐
#   │ S3 Bucket       │ Static files (images, CSS, JS, HTML).  │
#   │                 │ Use OAC (Origin Access Control) so S3   │
#   │                 │ is private — only CloudFront can read.  │
#   │                 │ Replaces old OAI (Origin Access Identity)│
#   ├─────────────────┼────────────────────────────────────────┤
#   │ ALB / ELB       │ Dynamic API responses. CloudFront      │
#   │                 │ passes requests to your load balancer.  │
#   │                 │ ALB must be internet-facing (public     │
#   │                 │ subnets) for CloudFront to reach it.    │
#   ├─────────────────┼────────────────────────────────────────┤
#   │ API Gateway     │ Serverless API. EDGE type already HAS   │
#   │                 │ CloudFront built in. REGIONAL type lets  │
#   │                 │ you add your own CloudFront in front.    │
#   ├─────────────────┼────────────────────────────────────────┤
#   │ Custom HTTP     │ Any server with a public URL/IP.        │
#   │                 │ On-prem servers, other cloud providers.  │
#   ├─────────────────┼────────────────────────────────────────┤
#   │ MediaStore /    │ Video streaming origins.                │
#   │ MediaPackage    │                                         │
#   └─────────────────┴────────────────────────────────────────┘
#
#   OAC vs OAI:
#     OAI (old): CloudFront special identity → S3 bucket policy grants access.
#     OAC (new): CloudFront signs requests with SigV4 → S3 bucket policy
#                checks the signing. Supports S3 SSE-KMS, more regions.
#     → Always use OAC for new distributions.
#
# ── Behaviors (URL → Origin Routing) ────────────────────────
#
#   Behaviors map URL path patterns to origins + cache settings.
#   Think of them as routing rules. Evaluated top-to-bottom by priority.
#
#   ┌────────────────┬────────────────┬────────────────────────┐
#   │ Path Pattern   │ Origin         │ Cache Policy           │
#   ├────────────────┼────────────────┼────────────────────────┤
#   │ /api/*         │ ALB origin     │ CachingDisabled        │
#   │ /covers/*      │ S3 origin      │ CachingOptimized       │
#   │ /static/*      │ S3 origin      │ CachingOptimized       │
#   │ Default (*)    │ ALB origin     │ CachingDisabled        │
#   └────────────────┴────────────────┴────────────────────────┘
#
#   Each behavior controls:
#     - Which origin gets the request
#     - Whether to cache, and for how long
#     - Which headers/cookies/query strings to forward
#     - Viewer protocol (HTTP, HTTPS, or redirect HTTP→HTTPS)
#     - Allowed HTTP methods (GET only, or all methods)
#     - Whether to compress responses (gzip/brotli)
#     - CloudFront Functions / Lambda@Edge to run
#
#   Path patterns support wildcards:
#     /api/*         → matches /api/books, /api/books/123
#     /images/*.jpg  → matches /images/cat.jpg but NOT /images/cat.png
#     Default (*)    → catch-all, lowest priority
#
# ── Cache Policy vs Origin Request Policy ────────────────────
#
#   These two policies are the KEY to understanding CloudFront caching.
#   They're often confused, but they do very different things:
#
#   ┌───────────────────────────────────────────────────────────┐
#   │                    CACHE POLICY                           │
#   │  "What makes two requests THE SAME (cache key)?"          │
#   │                                                           │
#   │  Controls what goes into the CACHE KEY. If two requests   │
#   │  produce the same cache key, CloudFront serves the        │
#   │  cached response instead of asking the origin.            │
#   │                                                           │
#   │  Include in cache key:                                    │
#   │    Headers:        e.g., Accept-Language → separate       │
#   │                    cache entries per language              │
#   │    Cookies:        e.g., session_id → per-user cache      │
#   │    Query strings:  e.g., ?page=2 → separate cache         │
#   │    TTL:            How long to cache (min/max/default)     │
#   │                                                           │
#   │  MORE items in cache key = LOWER cache hit rate            │
#   │  FEWER items = HIGHER hit rate (but might serve wrong data)│
#   └───────────────────────────────────────────────────────────┘
#
#   ┌───────────────────────────────────────────────────────────┐
#   │                ORIGIN REQUEST POLICY                      │
#   │  "What extra data should I forward to the origin?"        │
#   │                                                           │
#   │  Some headers/cookies/query strings don't affect caching  │
#   │  but the origin still needs them. This policy forwards    │
#   │  them WITHOUT including them in the cache key.            │
#   │                                                           │
#   │  Common use: forward Authorization header (origin needs   │
#   │  it for auth) but DON'T include in cache key (same        │
#   │  content for all authorized users).                       │
#   └───────────────────────────────────────────────────────────┘
#
#   Example for a FastAPI API:
#
#     Cache Policy:     CachingDisabled
#       → API responses change per request, don't cache them
#
#     Origin Request Policy: AllViewer
#       → Forward ALL headers to ALB (Authorization, Content-Type, etc.)
#       → Origin needs these to process the request
#
#   Example for S3 static files:
#
#     Cache Policy:     CachingOptimized (TTL: 24 hours)
#       → Cache key: just the URL path (no headers/cookies/query)
#       → Same image served to everyone from edge cache
#
#     Origin Request Policy: None needed
#       → S3 doesn't need auth headers (OAC handles access)
#
#   AWS Managed Policies (pre-built — use these):
#
#   ┌──────────────────────────┬───────────────────────────────┐
#   │ CachingDisabled          │ TTL=0. Never cache. For APIs. │
#   │ CachingOptimized         │ TTL=24h. For static files.    │
#   │ CachingOptimizedForUncom │ Same + no compression.        │
#   │  pressedObjects          │ For already-compressed files.  │
#   │ Elemental-MediaPackage   │ For video streaming.          │
#   ├──────────────────────────┼───────────────────────────────┤
#   │ AllViewer                │ Forward all headers to origin. │
#   │ AllViewerExceptHostHeader│ Forward all except Host.       │
#   │ AllViewerAndCloudFront...│ Forward all + CF geo headers.  │
#   │ CORS-S3Origin            │ Forward CORS headers to S3.   │
#   │ UserAgentRefererHeaders  │ Forward User-Agent + Referer.  │
#   └──────────────────────────┴───────────────────────────────┘
#
# ── Cache Invalidation ───────────────────────────────────────
#
#   When you update content at the origin (new version of an image,
#   updated CSS), CloudFront still serves the old cached version
#   until the TTL expires. Invalidation forces CloudFront to
#   discard the cached copy.
#
#   AWS Console:
#     CloudFront → Distribution → Invalidations tab
#     → Create invalidation
#     → Enter paths:
#       /covers/abc123.jpg     ← single file
#       /covers/*              ← all files under /covers/
#       /*                     ← everything (nuclear option)
#
#   CLI:
#     aws cloudfront create-invalidation \
#       --distribution-id E1234ABCDEF \
#       --paths "/covers/*" "/static/main.css"
#
#   Cost: First 1000 paths/month FREE. Then $0.005 per path.
#         /covers/* counts as ONE path (wildcard = 1 path).
#
#   Better alternative: VERSION your files instead of invalidating.
#     /static/main-v2.css instead of /static/main.css
#     → New URL = automatic cache miss = no invalidation needed.
#     → This is what production build tools do (Webpack content hash).
#
# ── CloudFront Functions vs Lambda@Edge ──────────────────────
#
#   Both let you run code at the edge. Different use cases:
#
#   ┌──────────────────┬────────────────────┬──────────────────┐
#   │                  │ CloudFront         │ Lambda@Edge      │
#   │                  │ Functions          │                  │
#   ├──────────────────┼────────────────────┼──────────────────┤
#   │ Language         │ JavaScript (ES 5.1)│ Node.js, Python  │
#   │ Max runtime      │ 1 ms               │ 5s (viewer)      │
#   │                  │                    │ 30s (origin)     │
#   │ Max memory       │ 2 MB               │ 128-10240 MB     │
#   │ Network access   │ No                 │ Yes              │
#   │ File system      │ No                 │ Yes (/tmp 512MB) │
#   │ Runs at          │ Edge locations     │ Regional edge    │
#   │ Triggers         │ Viewer req/resp    │ Viewer + Origin  │
#   │                  │ only               │ req/resp (all 4) │
#   │ Cost             │ $0.10 / 1M inv     │ $0.60 / 1M inv   │
#   │ Scale            │ 10M+ req/sec       │ 10K req/sec      │
#   │ Deploy speed     │ Seconds            │ Minutes (global) │
#   └──────────────────┴────────────────────┴──────────────────┘
#
#   4 trigger points where you can run code:
#
#   Viewer Request  → before cache lookup  (modify/reject incoming req)
#   Origin Request  → on cache miss only   (modify request to origin)
#   Origin Response → on cache miss only   (modify response from origin)
#   Viewer Response → before returning     (modify response to user)
#
#   Client → [Viewer Req] → Cache → [Origin Req] → Origin
#                                                      ↓
#   Client ← [Viewer Resp] ← Cache ← [Origin Resp] ← Response
#
#   CloudFront Functions ONLY run at Viewer Request / Viewer Response.
#   Lambda@Edge runs at ALL FOUR points.
#
#   Use CloudFront Functions for:
#     - URL rewrites/redirects
#     - Header manipulation (add security headers)
#     - Simple A/B testing (route to different origins)
#     - Normalize cache keys (lowercase URLs, sort query params)
#     - JWT validation (basic token checks, no network calls)
#
#   Use Lambda@Edge for:
#     - Anything needing network access (auth API calls, DB lookups)
#     - Dynamic image resizing (resize on origin response)
#     - A/B testing with external config
#     - Server-side rendering at the edge
#     - Complex request routing
#
#   CloudFront Function example — add security headers:
#
#     function handler(event) {
#       var response = event.response;
#       var headers = response.headers;
#       headers['strict-transport-security'] =
#         { value: 'max-age=63072000; includeSubdomains; preload' };
#       headers['x-content-type-options'] = { value: 'nosniff' };
#       headers['x-frame-options'] = { value: 'DENY' };
#       headers['x-xss-protection'] = { value: '1; mode=block' };
#       return response;
#     }
#
#   CloudFront Function example — URL rewrite (SPA):
#
#     function handler(event) {
#       var request = event.request;
#       var uri = request.uri;
#       // If no file extension → serve index.html (SPA routing)
#       if (!uri.includes('.')) {
#         request.uri = '/index.html';
#       }
#       return request;
#     }
#
# ── Signed URLs & Signed Cookies ─────────────────────────────
#
#   Restrict access to content — only users with a valid signature
#   can fetch it. Used for premium content, private files, time-
#   limited downloads.
#
#   Signed URLs:
#     Each URL contains an expiration time + cryptographic signature.
#     Your backend generates the signed URL, gives it to the user.
#
#     https://d1234.cloudfront.net/premium/video.mp4
#       ?Expires=1720000000
#       &Signature=ABC123...
#       &Key-Pair-Id=K1234
#
#     → URL works until expiry. Can't be modified (signature breaks).
#     → Use for: individual file downloads, one-time links.
#
#   Signed Cookies:
#     Set a cookie with the signature. ALL requests with that cookie
#     are authorized. No URL changes needed.
#
#     Set-Cookie: CloudFront-Policy=ABC123...; Path=/premium/;
#     Set-Cookie: CloudFront-Signature=XYZ789...; Path=/premium/;
#     Set-Cookie: CloudFront-Key-Pair-Id=K1234; Path=/premium/;
#
#     → Use for: streaming (HLS/DASH with many segment files),
#       or when you don't want to modify URLs.
#
#   Setup:
#     1. CloudFront → Key management → Key groups
#        → Create a CloudFront key pair (RSA 2048)
#     2. Distribution → Behavior → "Restrict viewer access" = Yes
#        → Trusted key groups → select your key group
#     3. In your backend code, use the private key to sign URLs/cookies
#
#   Python signing example (boto3):
#
#     from datetime import datetime, timedelta
#     from botocore.signers import CloudFrontSigner
#     import rsa
#
#     def rsa_signer(message):
#         with open('private_key.pem', 'rb') as f:
#             private_key = rsa.PrivateKey.load_pkcs1(f.read())
#         return rsa.sign(message, private_key, 'SHA-1')
#
#     cf_signer = CloudFrontSigner('K1234KEYID', rsa_signer)
#     signed_url = cf_signer.generate_presigned_url(
#         'https://d1234.cloudfront.net/premium/video.mp4',
#         date_less_than=datetime.utcnow() + timedelta(hours=1)
#     )
#
# ── WAF (Web Application Firewall) Integration ──────────────
#
#   CloudFront integrates with AWS WAF to block malicious traffic
#   BEFORE it reaches your origin. WAF rules are evaluated at
#   every edge location.
#
#   AWS Console:
#     CloudFront → Distribution → General tab → "Edit"
#     → AWS WAF web ACL → select or create one
#
#   Common WAF rules:
#     - Rate limiting:   Block IPs exceeding 2000 req/5min
#     - Geo blocking:    Block traffic from specific countries
#     - SQL injection:   Block requests with SQL in query strings
#     - XSS protection:  Block requests with script tags
#     - IP allowlist:    Only allow known IP ranges
#     - Bot control:     Block known bad bots
#
#   AWS Managed Rule Groups (pre-built, free/paid):
#     AWSManagedRulesCommonRuleSet     → OWASP top 10 protection
#     AWSManagedRulesKnownBadInputs    → Log4j, etc.
#     AWSManagedRulesSQLiRuleSet       → SQL injection
#     AWSManagedRulesAmazonIpReputation → Known bad IPs
#     AWSManagedRulesBotControlRuleSet  → Bot detection ($10/month)
#
#   WAF Cost: $5/month per web ACL + $1/month per rule + $0.60/1M req
#
# ── Origin Failover (Origin Groups) ─────────────────────────
#
#   If your primary origin fails, CloudFront automatically
#   switches to a backup origin. No DNS changes needed.
#
#   Primary (ALB eu-west-1)
#     │
#     ├── 200 OK → return response
#     │
#     └── 500/502/503/504 → failover ──► Secondary (ALB us-east-1)
#
#   Setup:
#     1. Add both origins to the distribution
#     2. CloudFront → Origins tab → "Create origin group"
#        ┌──────────────────────────────────────────────────┐
#        │  Primary origin:   ALB eu-west-1                 │
#        │  Secondary origin: ALB us-east-1                 │
#        │                                                   │
#        │  Failover criteria (HTTP status codes):           │
#        │    ✅ 500  Internal Server Error                  │
#        │    ✅ 502  Bad Gateway                            │
#        │    ✅ 503  Service Unavailable                    │
#        │    ✅ 504  Gateway Timeout                        │
#        └──────────────────────────────────────────────────┘
#     3. In the behavior, select the origin GROUP instead of
#        a single origin.
#
#   Real-world: The skills repo deploys to eu-west-1 and us-east-1
#   for production. Origin groups could provide automatic failover
#   between the two regions.
#
# ── Custom Error Pages ───────────────────────────────────────
#
#   When the origin returns an error (404, 500, etc.), CloudFront
#   can return a custom error page instead of the raw error.
#
#   CloudFront → Distribution → Error pages tab → "Create custom error response"
#
#   ┌──────────────────────────────────────────────────┐
#   │  HTTP error code:     404                         │
#   │  Customize response:  Yes                         │
#   │  Response page path:  /errors/404.html            │
#   │  Response code:       404                         │
#   │  Error caching TTL:   60 seconds                  │
#   └──────────────────────────────────────────────────┘
#
#   For SPAs (React, Vue, Angular):
#     Map 403 and 404 → /index.html with response code 200
#     → CloudFront serves the SPA shell, client-side router handles it
#
#     ┌──────────────────────────────────────────────────┐
#     │  HTTP error code:     403                         │
#     │  Response page path:  /index.html                 │
#     │  Response code:       200                         │
#     │  Error caching TTL:   0                           │
#     │                                                    │
#     │  (Repeat for 404)                                  │
#     └──────────────────────────────────────────────────┘
#
# ── Price Classes ────────────────────────────────────────────
#
#   Control which edge locations CloudFront uses. Fewer locations
#   = lower cost but higher latency for distant users.
#
#   ┌──────────────────────┬───────────────────────────────────┐
#   │ Price Class All      │ All 400+ edge locations.          │
#   │ (default)            │ Best performance, highest cost.   │
#   ├──────────────────────┼───────────────────────────────────┤
#   │ Price Class 200      │ US, Canada, Europe, Asia, Middle  │
#   │                      │ East, Africa. Excludes South      │
#   │                      │ America, Australia.               │
#   ├──────────────────────┼───────────────────────────────────┤
#   │ Price Class 100      │ US, Canada, Europe only.          │
#   │ (cheapest)           │ Good for internal/regional apps.  │
#   └──────────────────────┴───────────────────────────────────┘
#
#   Data transfer pricing (per GB, varies by region):
#     US/Europe:    $0.085/GB (first 10TB)
#     Asia:         $0.114/GB
#     South America: $0.110/GB
#     → First 1TB/month is FREE (free tier)
#
# ── Logging & Monitoring ─────────────────────────────────────
#
#   Standard Logs (free):
#     S3 bucket receives log files every few minutes.
#     Each log line: timestamp, edge location, client IP, URI,
#     status code, bytes, cache hit/miss, time-to-first-byte.
#
#     Setup: Distribution → General → Settings → Edit
#     → Standard logging: On → S3 bucket: your-logs-bucket
#     → Prefix: cloudfront-logs/
#
#   Real-Time Logs (paid):
#     Stream to Kinesis Data Streams within seconds.
#     Can sample (e.g., 10% of requests) to save cost.
#     From Kinesis → Kinesis Firehose → S3/Elasticsearch/Splunk.
#
#   CloudWatch Metrics (automatic, free):
#     Requests, BytesDownloaded, BytesUploaded,
#     4xxErrorRate, 5xxErrorRate, TotalErrorRate,
#     CacheHitRate ← most important metric
#
#   Cache Hit Ratio goal:
#     90%+ for static sites
#     70-80% for mixed static/dynamic
#     0% for pure API (CachingDisabled) — expected and fine
#
# ── CloudFront for Different Architectures ───────────────────
#
#   1. Static Website (S3 + CloudFront):
#      ┌──────────────────────────────────────────────────┐
#      │  Origin:   S3 bucket (OAC access)                │
#      │  Cache:    CachingOptimized (24h TTL)            │
#      │  Compress: Yes (gzip + brotli)                    │
#      │  HTTPS:    Redirect HTTP → HTTPS                  │
#      │  Error:    404 → /index.html, 200 (for SPA)      │
#      │  Function: URL rewrite (/ → /index.html)          │
#      └──────────────────────────────────────────────────┘
#
#   2. API Only (ALB + CloudFront):
#      ┌──────────────────────────────────────────────────┐
#      │  Origin:   ALB (HTTP only, internal)              │
#      │  Cache:    CachingDisabled                        │
#      │  Methods:  ALL (GET, POST, PUT, DELETE, etc.)     │
#      │  Forward:  AllViewer (all headers to origin)       │
#      │  HTTPS:    Redirect HTTP → HTTPS                  │
#      │  WAF:      Enabled (rate limiting + bot control)  │
#      └──────────────────────────────────────────────────┘
#
#   3. Mixed (S3 static + ALB API — the book-store pattern):
#      ┌──────────────────────────────────────────────────┐
#      │  Behavior 1: /covers/*  → S3 (CachingOptimized)  │
#      │  Behavior 2: /static/*  → S3 (CachingOptimized)  │
#      │  Default:    /*         → ALB (CachingDisabled)   │
#      └──────────────────────────────────────────────────┘
#
#   4. Multi-Region Failover:
#      ┌──────────────────────────────────────────────────┐
#      │  Origin Group:                                    │
#      │    Primary:   ALB eu-west-1                       │
#      │    Secondary: ALB us-east-1                       │
#      │  Failover on: 500, 502, 503, 504                  │
#      └──────────────────────────────────────────────────┘
#
# ── HTTP/2 and HTTP/3 ────────────────────────────────────────
#
#   CloudFront supports HTTP/2 (enabled by default) and HTTP/3
#   (opt-in). These are between the viewer and CloudFront only —
#   CloudFront talks HTTP/1.1 to origins.
#
#   HTTP/2:  Multiplexing (multiple requests on one connection),
#            header compression, server push. ~30% faster.
#
#   HTTP/3:  Uses QUIC (UDP instead of TCP). Better on unstable
#            networks (mobile). 0-RTT connection establishment.
#            Enable: Distribution → General → Edit → HTTP/3: On
#
# ── Common Gotchas ───────────────────────────────────────────
#
#   1. ACM certificate MUST be in us-east-1 for CloudFront.
#      Your ALB cert can be in any region, but CloudFront
#      only reads certs from us-east-1.
#
#   2. ALB must be internet-facing. CloudFront can't reach
#      internal ALBs. (Use VPC origins for private ALBs —
#      newer feature, more complex setup.)
#
#   3. CloudFront→ALB uses HTTP by default. The TLS termination
#      happens at CloudFront (viewer→CF = HTTPS, CF→ALB = HTTP).
#      If you need end-to-end encryption, set origin protocol
#      to HTTPS and put an ACM cert on the ALB too.
#
#   4. Don't cache API responses unless you're sure they're
#      the same for all users. A cached authenticated response
#      served to the wrong user = security incident.
#
#   5. If your API is behind CloudFront with CachingDisabled,
#      CloudFront still adds latency (~5-15ms) vs direct ALB.
#      The benefit is WAF, HTTPS termination, and DDoS protection.
#
#   6. Max request body size through CloudFront: 20 GB.
#      But for file uploads, consider pre-signed S3 URLs instead
#      (client uploads directly to S3, bypasses CloudFront).
#
#   7. WebSocket connections work through CloudFront.
#      Set allowed methods to include GET, HEAD, OPTIONS.
#      CloudFront detects the Upgrade header and proxies the
#      WebSocket connection to the origin.
#
#   8. CloudFront Functions have a 1ms time limit and no network
#      access. If your function does anything slow, it'll fail.
#      Use Lambda@Edge for anything beyond simple rewrites.


# ╔══════════════════════════════════════════════════╗
# ║  STEP 11: SECRETS MANAGER                        ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Stores API keys, passwords, database credentials securely.
#       Injected into Lambda/ECS at runtime — never hardcoded in code.
#       Supports automatic rotation.
#
# REAL REPO: Skills inject 15+ secrets from Secrets Manager into
#            ECS containers: ORCHESTRATOR_ENDPOINT, API keys,
#            OAuth credentials, LLM endpoints.
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console → search "Secrets Manager" → click it
#
#   2. Click "Store a new secret"
#
#   3. Step 1:
#      ┌──────────────────────────────────────────────────┐
#      │  Secret type: Other type of secret                │
#      │                                                    │
#      │  Key/value pairs:                                 │
#      │    Key: DATABASE_URL                              │
#      │    Value: postgresql://user:pass@host:5432/books  │
#      │                                                    │
#      │    + Add row:                                     │
#      │    Key: API_KEY                                   │
#      │    Value: sk-your-secret-key-here                 │
#      │                                                    │
#      │    + Add row:                                     │
#      │    Key: JWT_SECRET                                │
#      │    Value: super-secret-jwt-key                    │
#      │                                                    │
#      │  Encryption key: aws/secretsmanager (default, free)│
#      └──────────────────────────────────────────────────┘
#      → Next
#
#   4. Step 2:
#      ┌──────────────────────────────────────────────────┐
#      │  Secret name: book-store/production               │
#      │  Description: Book Store API production secrets   │
#      │  Tags:                                            │
#      │    environment: production                        │
#      │    service: book-store                            │
#      └──────────────────────────────────────────────────┘
#      → Next → Next → Store
#
#   5. Grant ECS Task Role access:
#      → IAM → Roles → find your ECS task role
#      → Add permissions → Create inline policy:
#      ┌──────────────────────────────────────────────────┐
#      │  {                                                │
#      │    "Version": "2012-10-17",                       │
#      │    "Statement": [{                                │
#      │      "Effect": "Allow",                           │
#      │      "Action": "secretsmanager:GetSecretValue",   │
#      │      "Resource": "arn:aws:secretsmanager:<region> │
#      │        :<acct>:secret:book-store/production-*"    │
#      │    }]                                             │
#      │  }                                                │
#      └──────────────────────────────────────────────────┘
#
#   6. Use in ECS Task Definition:
#      → Edit task definition → Container → Environment
#      → Add environment variable:
#        Key:       DATABASE_URL
#        ValueFrom: arn:aws:secretsmanager:<region>:<acct>:
#                   secret:book-store/production:DATABASE_URL::
#      → ECS injects the secret value at container start
#
#   For Lambda: use boto3 in code:
#     import boto3, json
#     client = boto3.client("secretsmanager")
#     secret = json.loads(
#       client.get_secret_value(SecretId="book-store/production")
#       ["SecretString"]
#     )
#     db_url = secret["DATABASE_URL"]


# ╔══════════════════════════════════════════════════╗
# ║           CLEANUP (AVOID CHARGES)                ║
# ╚══════════════════════════════════════════════════╝
#
# Delete in this order (dependencies matter):
#
#   1. CloudFront  → Disable distribution → wait → Delete
#   2. Route 53    → Delete A record (keep hosted zone if you own domain)
#   3. ECS         → Delete service → Delete cluster
#   4. ALB         → Delete load balancer → Delete target group
#   5. ECR         → Delete repository (deletes all images)
#   6. Lambda      → Delete function
#   7. API Gateway → Delete API
#   8. CloudWatch  → Delete log groups, alarms, dashboard
#   9. S3          → Empty bucket → Delete bucket
#  10. Secrets Mgr → Delete secret (with 0-day recovery window)
#  11. EC2         → Terminate instance → Delete key pair
#  12. VPC         → Delete NAT Gateway (wait 5 min) → Delete VPC
#                    (auto-deletes subnets, route tables, IGW, SGs)
#
#   COST WARNING: NAT Gateway costs ~$0.045/hour ($32/month).
#   Delete it when not actively testing!


# ══════════════════════════════════════════════════════════════════
# CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
#
# SERVICE         │ WHAT IT DOES                     │ ANALOGY
# ────────────────┼──────────────────────────────────┼─────────────────
# VPC             │ Isolated network in AWS           │ Your office building
# Subnet          │ Network segment in 1 AZ           │ Floor in the building
# Internet GW     │ Connects VPC to internet          │ Front door
# NAT Gateway     │ Private→internet (one-way)        │ Mail room (sends, doesn't receive)
# Security Group  │ Firewall rules per resource       │ Badge reader on doors
# Route Table     │ Where traffic goes                │ Directory signs
# ────────────────┼──────────────────────────────────┼─────────────────
# EC2             │ Virtual machine (you manage)      │ Renting a full server room
# Lambda          │ Serverless function (AWS manages) │ Vending machine (pay per use)
# ECS             │ Container orchestration           │ Docker manager
# Fargate         │ Serverless containers             │ Docker without servers
# ECR             │ Container image registry          │ Docker Hub (private)
# ────────────────┼──────────────────────────────────┼─────────────────
# API Gateway     │ Managed API endpoint              │ Reception desk
#   EDGE          │ Via CloudFront globally            │ Global reception
#   REGIONAL      │ Direct to region                  │ Local reception
#   PRIVATE       │ VPC-only access                   │ Internal reception
# ALB             │ Load balancer (HTTP, Layer 7)     │ Receptionist routing to desks
# NLB             │ Load balancer (TCP, Layer 4)      │ Phone switchboard
# ────────────────┼──────────────────────────────────┼─────────────────
# S3              │ Unlimited file storage            │ Infinite filing cabinet
# CloudFront      │ CDN (cache at 400+ edge locs)     │ Local copies of popular files
# ACM             │ Free SSL certificates             │ HTTPS padlock
# Route 53        │ DNS (domain → IP)                 │ Phone book
# ────────────────┼──────────────────────────────────┼─────────────────
# CloudWatch      │ Logs + Metrics + Alarms           │ Security cameras + smoke alarms
# Secrets Manager │ Secure credential storage         │ Vault / safe
# IAM Role        │ Permissions for AWS services      │ Badge with access levels
# SSM Parameter   │ Config key-value store            │ Sticky notes on the wall
#
# PATTERN         │ SERVICES USED                     │ WHEN TO USE
# ────────────────┼──────────────────────────────────┼─────────────────
# Serverless API  │ API GW + Lambda + CloudWatch      │ Short requests, variable traffic
#                 │                                    │ Pay per invocation
# Container API   │ ALB + ECS Fargate + CloudWatch    │ Long-running, steady traffic
#                 │                                    │ WebSockets, custom runtimes
# Static + API    │ CloudFront + S3 + ALB/Lambda      │ Frontend (S3) + Backend (API)
# Full Production │ Route53 + CF + ALB + ECS + CW +   │ Production-grade deployment
#                 │ Secrets + S3 + VPC                 │
#
# ══════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════
# DETAILED REFERENCE — BUILD ORDER & ARCHITECTURE
# ══════════════════════════════════════════════════════════════════
#
# ── Recommended Build Order ──────────────────────────────────
#
#   Step │ Service              │ Depends On         │ Time
#   ─────┼──────────────────────┼────────────────────┼──────
#    1   │ VPC + Subnets + SGs  │ Nothing            │ 5 min
#    2   │ S3 Bucket            │ Nothing            │ 2 min
#    3   │ EC2 (learn, delete)  │ VPC                │ 10 min
#    4   │ Lambda               │ VPC, code zip      │ 10 min
#    5   │ API Gateway          │ Lambda             │ 5 min
#    6   │ ECR                  │ Docker installed   │ 10 min
#    7   │ ECS Cluster + Task   │ ECR, VPC           │ 10 min
#    8   │ ALB + Target Group   │ VPC                │ 5 min
#    7c  │ ECS Service          │ ECS Task, ALB      │ 5 min
#    9   │ CloudWatch           │ Lambda or ECS      │ 5 min
#   10a  │ ACM Certificate      │ Domain (optional)  │ 5 min
#   10b  │ CloudFront           │ ALB or S3, ACM     │ 10 min
#   10c  │ Route 53             │ CloudFront or ALB  │ 5 min
#   11   │ Secrets Manager      │ IAM role           │ 5 min
#
# ── Final Architecture Diagram ───────────────────────────────
#
#   ┌──────────────────────────────────────────────────────────┐
#   │                    YOUR AWS ACCOUNT                       │
#   │                                                          │
#   │  Route 53 (DNS)                                          │
#   │  └─ books.yourname.com → CloudFront                     │
#   │                                                          │
#   │  CloudFront (CDN + HTTPS)                                │
#   │  ├─ /covers/* → S3 bucket (cached at edge)              │
#   │  └─ /*        → ALB (pass-through, no cache)            │
#   │                                                          │
#   │  ACM (free SSL certificate for HTTPS)                    │
#   │                                                          │
#   │  ┌────────────── VPC ──────────────────────┐             │
#   │  │                                          │             │
#   │  │  Public Subnets (2 AZs)                  │             │
#   │  │  ├─ ALB (receives CloudFront traffic)    │             │
#   │  │  ├─ NAT Gateway (outbound for private)   │             │
#   │  │  └─ Internet Gateway                     │             │
#   │  │                                          │             │
#   │  │  Private Subnets (2 AZs)                 │             │
#   │  │  ├─ ECS Fargate Tasks (2 containers)     │             │
#   │  │  │    ├─ book-store-api:v1 (from ECR)    │             │
#   │  │  │    ├─ reads Secrets Manager            │             │
#   │  │  │    ├─ writes CloudWatch Logs           │             │
#   │  │  │    └─ reads/writes S3                  │             │
#   │  │  └─ Lambda (serverless path)              │             │
#   │  │       └─ triggered by API Gateway         │             │
#   │  │                                          │             │
#   │  └──────────────────────────────────────────┘             │
#   │                                                          │
#   │  API Gateway (EDGE) ── alternative serverless path       │
#   │  └─ ANY /{proxy+} → Lambda (book-store-api)              │
#   │                                                          │
#   │  CloudWatch                                              │
#   │  ├─ Log groups (Lambda, ECS, API Gateway)                │
#   │  ├─ Alarms (error rate, latency)                         │
#   │  └─ Dashboard (metrics visualization)                    │
#   │                                                          │
#   │  ECR (Elastic Container Registry)                        │
#   │  └─ book-store-api:v1 (Docker image)                     │
#   │                                                          │
#   │  S3 (Simple Storage Service)                             │
#   │  └─ book-store-covers-xxx/covers/{book_id}.jpg           │
#   │                                                          │
#   │  Secrets Manager                                         │
#   │  └─ book-store/production (DATABASE_URL, API_KEY, ...)   │
#   │                                                          │
#   │  IAM Roles                                               │
#   │  ├─ Lambda execution role (CloudWatch, VPC)              │
#   │  ├─ ECS task role (S3, Secrets Manager)                  │
#   │  └─ ECS execution role (ECR pull, CloudWatch)            │
#   └──────────────────────────────────────────────────────────┘
#
# ── Lambda vs ECS Fargate — When to Use Which ───────────────
#
#   ┌─────────────────┬──────────────────┬────────────────────┐
#   │                 │ Lambda           │ ECS Fargate        │
#   ├─────────────────┼──────────────────┼────────────────────┤
#   │ Max runtime     │ 15 minutes       │ Unlimited          │
#   │ Cold start      │ 1-5 seconds      │ None (always on)   │
#   │ Scaling         │ 0 to 1000+       │ Min 1 task         │
#   │ Cost model      │ Per invocation   │ Per second running │
#   │ Best for        │ APIs, events     │ Long processes,    │
#   │                 │ variable traffic │ steady traffic     │
#   │ Pricing (low    │ Nearly free      │ ~$15-30/month min  │
#   │  traffic)       │ (free tier)      │ (1 task always on) │
#   │ WebSockets      │ No (use APIGW)   │ Yes (native)       │
#   │ Custom runtime  │ Limited          │ Any Docker image   │
#   │ Memory max      │ 10 GB            │ 120 GB             │
#   │ vCPU max        │ 6 vCPU           │ 16 vCPU            │
#   │ Real repo       │ sphinx_story-svc │ sphinx_skills      │
#   └─────────────────┴──────────────────┴────────────────────┘
#
# ── Cost Estimation (Low Traffic API) ────────────────────────
#
#   Lambda path (1000 requests/day):
#     Lambda:      Free tier covers this entirely
#     API Gateway: ~$3.50/month (1M req = $3.50)
#     CloudWatch:  ~$0 (5GB logs free)
#     Total:       ~$3.50/month
#
#   ECS Fargate path (1 task, 0.5 vCPU, 1GB):
#     Fargate:     ~$15/month (always running)
#     ALB:         ~$16/month (fixed cost)
#     CloudWatch:  ~$0
#     NAT Gateway: ~$32/month (biggest cost!)
#     Total:       ~$63/month
#
#   → Lambda is cheaper for low/variable traffic
#   → ECS is better for steady traffic, long processes, WebSockets
#   → NAT Gateway is expensive — delete when not using!
