# ══════════════════════════════════════════════════════════════════
# AWS Deployment — ECS + Fargate (Step 7)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 07-ecr.py  |  next: 09-alb.py →

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
# ── ECS + Fargate Key Concepts ──────────────────────────────
#
#   ── Cluster ────────────────────────────────────────────────
#
#   A logical grouping for your services and tasks. Like a
#   "project folder" — no compute resources by itself.
#
#   Cluster modes:
#     Fargate       → AWS manages the servers (serverless)
#     EC2           → you manage EC2 instances (more control, cheaper)
#     Both          → mix Fargate + EC2 instances in one cluster
#
#   The skills repo uses one cluster per environment:
#     dev-leon-skills-cluster   (dev/qa)
#     prod-leon-skills-cluster  (uat/prod)
#
#   Each cluster contains multiple services:
#     ├── story-drafting-service   (2 tasks)
#     ├── urgent-drafting-service  (2 tasks)
#     └── text-archive-service     (2 tasks)
#
#   ── Service ────────────────────────────────────────────────
#
#   The "manager" that ensures N tasks (containers) are always
#   running. If a task dies, the service replaces it automatically.
#
#   Key settings:
#     Desired count:   How many tasks to run (e.g., 2 for HA)
#     Min/Max:         Auto-scaling boundaries (e.g., 1-5)
#     Deployment:      Rolling update (replace one-by-one) or
#                      Blue/Green (deploy new, switch traffic)
#     Load balancer:   Routes traffic to healthy tasks
#     Health check:    Period to wait before marking task unhealthy
#
#   Service deployment strategies:
#
#     Rolling update (default):
#       Min healthy: 100%, Max: 200% (default)
#       → ECS starts new tasks FIRST, then stops old ones
#       → At peak: 4 tasks (2 old + 2 new) for desired count of 2
#       → Zero downtime — old tasks serve traffic until new ones pass health check
#
#       Timeline:
#         [Task1-old] [Task2-old]                        ← serving traffic
#         [Task1-old] [Task2-old] [Task1-new]            ← new task starting
#         [Task1-old] [Task2-old] [Task1-new] [Task2-new]← both new tasks healthy
#         [Task1-new] [Task2-new]                        ← old tasks stopped
#
#     Min 50%, Max 100% (faster, brief capacity dip):
#       → Stops 1 old task, starts 1 new task, repeat
#       → Uses fewer total resources but briefly runs at 50% capacity
#
#   ── Task Definition ────────────────────────────────────────
#
#   The "recipe" for running your container. Like a docker-compose
#   file but for AWS. Defines everything about HOW to run.
#
#   Key fields:
#     Image URI:       ECR image (060725138335.dkr.ecr.../story-drafting:v0.1.5)
#     CPU / Memory:    Resource allocation (0.25 vCPU / 0.5 GB minimum)
#     Port mappings:   Container port 8000 → host port 8000
#     Environment:     ENV=production, MCP_PORT=8004
#     Secrets:         Inject from Secrets Manager (see Step 11)
#     Log config:      awslogs driver → CloudWatch log group
#     Health check:    CMD ["curl", "-f", "http://localhost:8000/health"]
#     Stop timeout:    How long to wait for graceful shutdown (default 30s)
#
#   Task definitions are VERSIONED. Each change creates a new revision:
#     book-store-task:1  → original
#     book-store-task:2  → updated env vars
#     book-store-task:3  → new image version
#   The service points to the LATEST revision (or you specify one).
#
#   Fargate size options:
#     ┌──────────┬──────────────┬──────────────────────┐
#     │ CPU      │ Memory       │ Cost/month (eu-west-1)│
#     ├──────────┼──────────────┼──────────────────────┤
#     │ 0.25 vCPU│ 0.5-2 GB     │ ~$7-14               │
#     │ 0.5 vCPU │ 1-4 GB       │ ~$15-29              │
#     │ 1 vCPU   │ 2-8 GB       │ ~$29-58              │
#     │ 2 vCPU   │ 4-16 GB      │ ~$58-116             │
#     │ 4 vCPU   │ 8-30 GB      │ ~$116-232            │
#     │ 8 vCPU   │ 16-60 GB     │ ~$232-464            │
#     │ 16 vCPU  │ 32-120 GB    │ ~$464-930            │
#     └──────────┴──────────────┴──────────────────────┘
#     The skills use 0.5 vCPU / 1 GB for each drafting service.
#
#   ── Task ───────────────────────────────────────────────────
#
#   A running instance of a Task Definition = a running container.
#   Think of Task Definition as the recipe, Task as the cooked meal.
#
#   Each task gets:
#     - Its own private IP (e.g., 10.0.11.20) from the subnet
#     - Its own ENI (Elastic Network Interface) with security group
#     - Isolated filesystem (ephemeral — lost when task stops)
#     - Access to the IAM Task Role
#
#   Task lifecycle:
#     PROVISIONING → PENDING → RUNNING → STOPPING → STOPPED
#                                  ↑
#                         serving traffic here
#
#   Why tasks stop:
#     - Container crashes (exit code != 0) → service replaces it
#     - Health check fails → ALB marks unhealthy → service replaces
#     - Manual stop (ECS console or aws ecs stop-task)
#     - Deployment (new task definition revision)
#     - Spot interruption (if using Fargate Spot)
#
#   ── Fargate vs EC2 Launch Type ─────────────────────────────
#
#   Fargate (serverless):
#     ✅ No server management — AWS handles patching, scaling
#     ✅ Pay per task (per-second billing, minimum 1 minute)
#     ✅ Each task is isolated (own kernel)
#     ❌ More expensive than EC2 for steady workloads
#     ❌ Limited to 16 vCPU / 120 GB max per task
#     ❌ No GPU support
#
#   EC2 launch type:
#     ✅ Cheaper at scale (reserve instances → 40-60% savings)
#     ✅ GPU support for ML workloads
#     ✅ More instance types (up to 96 vCPU, 384 GB)
#     ❌ You manage the EC2 instances (patching, scaling, AMIs)
#     ❌ You handle capacity planning
#
#   Fargate Spot (save ~70%):
#     Like EC2 Spot Instances but for Fargate tasks.
#     AWS can reclaim your task with 30s warning.
#     Good for: batch processing, dev/test environments.
#     Bad for: production APIs (task might disappear mid-request).
#
#   ── Service Connect & Service Discovery ────────────────────
#
#   How services find each other within a cluster:
#
#   Service Discovery (Cloud Map):
#     Each service gets a DNS name within a private namespace.
#     story-drafting.skills.local → 10.0.11.20
#     Other services call this DNS name instead of IP.
#
#   Service Connect (newer, simpler):
#     Built-in load balancing between services in the same cluster.
#     ECS injects a sidecar proxy that handles routing.
#     No need to manage DNS or target groups for internal traffic.
#
#   For the skills repo: services communicate through the ALB
#   (external routing), not Service Connect (they're independent
#   services, not microservices that call each other).
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
