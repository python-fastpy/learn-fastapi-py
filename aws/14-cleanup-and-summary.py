# ══════════════════════════════════════════════════════════════════
# AWS Deployment — Cleanup & Summary
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 13-secrets-manager.py  |  next: 15-dynamodb.py →

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
