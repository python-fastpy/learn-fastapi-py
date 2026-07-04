# ══════════════════════════════════════════════════════════════════
# AWS Deployment — Overview & FastAPI App (Step 0)
# ══════════════════════════════════════════════════════════════════
# Navigation:  next: 02-vpc.py →
#
# ── Table of Contents ────────────────────────────────────────────
#   01-overview-and-app.py      — Architecture diagram + FastAPI app
#   02-vpc.py                   — VPC, subnets, AZs, IGW, NAT, security groups
#   03-s3.py                    — S3 buckets, policies, storage classes
#   04-ec2.py                   — EC2 instances, AMI, EBS, user data
#   05-lambda.py                — Lambda, cold starts, concurrency, layers
#   06-api-gateway.py           — API Gateway types, authorizers, REST vs HTTP
#   07-ecr.py                   — ECR, lifecycle policies, scanning, auth
#   08-ecs-fargate.py           — ECS + Fargate, clusters, services, task defs
#   09-alb.py                   — ALB, target groups, health checks, listeners
#   10-cloudwatch.py            — CloudWatch logs, metrics, alarms, dashboards
#   11-route53-cloudfront-acm.py — DNS, CDN basics, SSL certificates
#   12-cloudfront-deep-dive.py  — CloudFront origins, behaviors, caching, WAF
#   13-secrets-manager.py       — Secrets Manager, retrieval, rotation, vs SSM
#   14-cleanup-and-summary.py   — Cleanup commands, build order, cost comparison
#   15-dynamodb.py              — DynamoDB tables, keys, GSI/LSI, query vs scan
#   16-sns.py                   — SNS topics, subscriptions, CloudWatch → email
#   17-sqs.py                   — SQS queues, DLQ, FIFO, Lambda triggers
#   18-waf.py                   — WAF web ACLs, managed rules, rate limiting
#   19-codedeploy-pipeline.py   — CodeBuild + CodePipeline + CodeDeploy, CI/CD
#   20-rds.py                   — RDS managed databases, Multi-AZ, Aurora
#   21-cognito.py               — Cognito user pools, JWT, API GW integration
#   22-ssm-parameter-store.py   — SSM Parameter Store, hierarchies, vs Secrets Mgr
#   23-iam.py                   — IAM users, groups, roles, policies, least privilege
# ─────────────────────────────────────────────────────────────────

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
