# ══════════════════════════════════════════════════════════════════
# AWS Deployment — ECR (Step 6)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 06-api-gateway.py  |  next: 08-ecs-fargate.py →

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
#
# ── ECR Key Concepts ────────────────────────────────────────
#
#   ── Repository ─────────────────────────────────────────────
#
#   A collection of Docker images with the same name but different
#   tags (versions). Like a folder for one app's images.
#
#   One repo per service:
#     060725138335.dkr.ecr.eu-west-1.amazonaws.com/story-drafting
#     060725138335.dkr.ecr.eu-west-1.amazonaws.com/urgent-drafting
#     060725138335.dkr.ecr.eu-west-1.amazonaws.com/text-archive
#
#   Each repo holds multiple tagged images:
#     book-store-api:latest
#     book-store-api:v1
#     book-store-api:v0.1.5-a7f3b2c   ← production pattern (semver + git SHA)
#
#   The real skills repo uses this versioning format:
#     v0.1.5-a7f3b2c  → version 0.1.5, built from git commit a7f3b2c
#     Auto-incremented patch version + git SHA suffix.
#
#   ── Image Tags ─────────────────────────────────────────────
#
#   Tags are labels you put on images. Multiple tags can point
#   to the SAME image (like git tags pointing to a commit).
#
#   Common patterns:
#     :latest          → most recent build (mutable — changes often)
#     :v1, :v2         → simple versions
#     :v0.1.5-a7f3b2c  → semver + git SHA (production best practice)
#     :20260703-143022  → timestamp-based
#
#   Tag immutability:
#     Disabled (default) → you can overwrite :v1 with a new image
#     Enabled → once :v1 is pushed, it's permanent. Must use new tag.
#     Production tip: enable immutability to prevent accidental overwrites.
#
#   ── Image Scanning ─────────────────────────────────────────
#
#   ECR can scan images for known security vulnerabilities (CVEs)
#   in OS packages and application dependencies.
#
#   Two modes:
#     Basic scanning (free): Scans on push. Checks OS packages (rpm, deb).
#     Enhanced scanning ($): Continuous scanning. Also checks app-level
#       dependencies (pip packages, npm). Uses Amazon Inspector.
#
#   AWS Console: ECR → repo → click image tag → "Scan findings"
#   Shows: CVE ID, severity (CRITICAL/HIGH/MEDIUM/LOW), affected package.
#
#   Practical example:
#     You push book-store-api:v1. ECR scans it.
#     Finding: CVE-2024-1234 HIGH in openssl 1.1.1
#     Fix: update your Dockerfile base image to python:3.11-slim
#          (which has the patched openssl).
#
#   ── Lifecycle Policies ─────────────────────────────────────
#
#   Automatically clean up old images to save storage costs.
#   Without this, ECR fills up with hundreds of old images.
#
#   AWS Console: ECR → repo → "Lifecycle Policy" → Create rule
#
#   Common rules:
#     ┌──────────────────────────────────────────────────┐
#     │  Rule 1: Keep only last 10 tagged images          │
#     │    Match criteria: Tag status = Tagged             │
#     │    Count type: Image count more than 10            │
#     │    Action: Expire                                  │
#     │                                                    │
#     │  Rule 2: Delete untagged images after 1 day        │
#     │    Match criteria: Tag status = Untagged            │
#     │    Count type: Since image pushed, days > 1         │
#     │    Action: Expire                                  │
#     └──────────────────────────────────────────────────┘
#
#   ── Authentication ─────────────────────────────────────────
#
#   Docker must authenticate to ECR before pushing/pulling.
#   ECR auth tokens expire every 12 HOURS.
#
#   Command (generates temporary Docker login):
#     aws ecr get-login-password --region eu-west-1 | \
#       docker login --username AWS --password-stdin \
#       060725138335.dkr.ecr.eu-west-1.amazonaws.com
#
#   ECS tasks authenticate automatically using their Execution Role.
#   You don't need to run get-login-password for ECS — only for
#   local development and CI/CD pipelines.
#
#   ── Cross-Account & Cross-Region ───────────────────────────
#
#   By default, only the owning AWS account can push/pull.
#
#   Cross-account: Add a repository policy allowing another account:
#     ECR → repo → Permissions → Edit policy JSON
#     Grant ecr:GetDownloadUrlForLayer + ecr:BatchGetImage
#     to account 304853478528 (production account pulls from dev ECR).
#
#   Cross-region: ECR Replication automatically copies images
#   to another region. Useful when you deploy to both eu-west-1
#   and us-east-1 (like the skills repo in production).
#     ECR → Private registry → Replication → Add rule
#     → Destination: us-east-1
#
#   ── Cost ───────────────────────────────────────────────────
#
#   Storage:   $0.10/GB/month
#   Transfer:  Free within same region (ECR → ECS in eu-west-1)
#              $0.09/GB cross-region
#
#   Typical cost: 10 images × 200MB = 2GB → $0.20/month
#   Very cheap. The lifecycle policy matters more for cleanliness
#   than cost savings at small scale.
