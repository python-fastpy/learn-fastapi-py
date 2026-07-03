# ══════════════════════════════════════════════════════════════════
# AWS Deployment — ALB (Step 8)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 08-ecs-fargate.py  |  next: 10-cloudwatch.py →

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
#
# ── ALB Key Concepts ────────────────────────────────────────
#
#   ── Target Group ───────────────────────────────────────────
#
#   A pool of targets (containers, IPs, Lambdas) that the ALB
#   distributes traffic to. The ALB checks their health and
#   only sends traffic to healthy targets.
#
#   Target types:
#     ┌──────────────┬────────────────────────────────────────┐
#     │ IP addresses │ For Fargate tasks (awsvpc networking). │
#     │              │ ECS registers/deregisters IPs          │
#     │              │ automatically. This is what we use.    │
#     ├──────────────┼────────────────────────────────────────┤
#     │ Instance     │ For EC2 instances. Route by instance ID│
#     │              │ ALB routes to instance, then to port.  │
#     ├──────────────┼────────────────────────────────────────┤
#     │ Lambda       │ ALB can invoke Lambda directly.        │
#     │              │ No API Gateway needed. Simpler but     │
#     │              │ fewer features than API Gateway.       │
#     └──────────────┴────────────────────────────────────────┘
#
#   Practical example — the skills ALB has 3 target groups:
#
#     ┌─────────────────────────────────────────────────────┐
#     │ story-drafting-tg   (port 8004, IP type)            │
#     │   → 10.0.11.20 (task 1, healthy ✅)                 │
#     │   → 10.0.12.30 (task 2, healthy ✅)                 │
#     │                                                     │
#     │ urgent-drafting-tg  (port 8003, IP type)            │
#     │   → 10.0.11.45 (task 1, healthy ✅)                 │
#     │   → 10.0.12.55 (task 2, healthy ✅)                 │
#     │                                                     │
#     │ text-archive-tg     (port 8000, IP type)            │
#     │   → 10.0.11.70 (task 1, unhealthy ❌) ← no traffic │
#     │   → 10.0.12.80 (task 2, healthy ✅)   ← gets 100%  │
#     └─────────────────────────────────────────────────────┘
#
#   ── Health Checks ──────────────────────────────────────────
#
#   ALB periodically calls a health endpoint on each target.
#   If it fails N times, the target is marked unhealthy and
#   receives no more traffic. ECS service then replaces it.
#
#   Health check settings:
#     Path:            /health  (your health endpoint)
#     Protocol:        HTTP
#     Port:            traffic port (same port as app)
#     Interval:        30s (how often to check)
#     Timeout:         5s (max time for response)
#     Healthy count:   2 (consecutive passes to become healthy)
#     Unhealthy count: 3 (consecutive failures to become unhealthy)
#     Success codes:   200 (which HTTP codes = healthy)
#
#   Timeline of a failing target:
#     t=0s   ALB checks /health → 200 OK ✅
#     t=30s  ALB checks /health → 500 ❌ (failure 1)
#     t=60s  ALB checks /health → timeout ❌ (failure 2)
#     t=90s  ALB checks /health → 500 ❌ (failure 3)
#     t=90s  Target marked UNHEALTHY → traffic stops
#     t=91s  ECS notices unhealthy task → starts replacement
#     t=150s New task starts, passes 2 health checks → HEALTHY
#
#   Health check grace period (ECS):
#     New containers take time to start (import modules, warm up).
#     Grace period = ignore health check failures during startup.
#     Set to 120s for Python/FastAPI apps (cold start + imports).
#     Without grace period: ALB marks new task unhealthy before
#     it finishes starting → ECS replaces it → infinite loop!
#
#   ── Listener Rules ─────────────────────────────────────────
#
#   Rules on each listener (port) that determine routing.
#   Evaluated in priority order (lower number = higher priority).
#
#   Each rule has:
#     Condition:  path, host header, HTTP method, query string, source IP
#     Action:     forward, redirect, fixed response, authenticate
#
#   The skills ALB listener rules:
#
#     ┌──────────┬──────────────────────┬──────────────────────┐
#     │ Priority │ Condition            │ Action               │
#     ├──────────┼──────────────────────┼──────────────────────┤
#     │ 100      │ path = /story-*      │ forward → story-tg   │
#     │ 110      │ path = /urgent-*     │ forward → urgent-tg  │
#     │ 120      │ path = /text-archive*│ forward → archive-tg │
#     │ default  │ (everything else)    │ return 404           │
#     └──────────┴──────────────────────┴──────────────────────┘
#
#   Advanced conditions:
#     Host-based:    api.example.com → api-tg, www.example.com → web-tg
#     HTTP header:   X-Custom-Header = "special" → special-tg
#     Query string:  ?version=v2 → v2-tg
#     Source IP:      10.0.0.0/8 → internal-tg (VPN users)
#
#   Advanced actions:
#     Redirect:      HTTP → HTTPS (301), old URL → new URL
#     Fixed response: Return 200 {"status":"ok"} without any target
#     Authenticate:   OIDC or Cognito auth before forwarding
#
#   ── Sticky Sessions ───────────────────────────────────────
#
#   By default, ALB distributes each request independently
#   (round-robin). Sticky sessions pin a user to one target
#   for the duration of a session.
#
#   Types:
#     Duration-based:  ALB sets AWSALB cookie, lasts N seconds
#     Application-based: Your app sets a custom cookie, ALB reads it
#
#   When to use:
#     ❌ Stateless APIs (REST, FastAPI) → don't need stickiness
#     ✅ WebSocket connections → must stay on same target
#     ✅ In-memory sessions → user session stored in target's RAM
#     ✅ File uploads → multi-part upload to same target
#
#   Our book-store API is stateless → no sticky sessions needed.
#
#   ── Cross-Zone Load Balancing ──────────────────────────────
#
#   By default, ALB distributes traffic evenly across AZs,
#   then evenly among targets within each AZ.
#
#   With cross-zone (enabled by default for ALB):
#     AZ-a has 1 target, AZ-b has 3 targets
#     → Each target gets 25% of traffic (distributed evenly)
#
#   Without cross-zone:
#     AZ-a has 1 target, AZ-b has 3 targets
#     → AZ-a's target gets 50%, AZ-b targets share 50% (16.7% each)
#     → AZ-a's single target is overloaded!
#
#   ── ALB Access Logs ────────────────────────────────────────
#
#   Detailed logs of every request, written to S3 every 5 minutes.
#
#   Enable: EC2 → Load Balancers → your ALB → Attributes → Edit
#   → Access logs: Enabled → S3 bucket: your-alb-logs-bucket
#
#   Each log entry includes:
#     timestamp, client IP, target IP, request processing time,
#     target processing time, response time, status code,
#     request URL, user agent, SSL cipher, target group ARN
#
#   Useful for: debugging latency issues, identifying slow endpoints,
#   traffic analysis, security auditing.
#
#   ── Cost ───────────────────────────────────────────────────
#
#   ALB pricing:
#     Fixed:    $0.0225/hour = ~$16.20/month (even with 0 traffic)
#     LCU:     $0.008/LCU-hour (based on traffic volume)
#
#   LCU (Load Balancer Capacity Unit) — charged on the HIGHEST of:
#     - New connections/sec (25 per LCU)
#     - Active connections/min (3000 per LCU)
#     - Processed bytes/hour (1GB per LCU)
#     - Rule evaluations/sec (1000 per LCU)
#
#   For low-traffic APIs: ~$16-18/month total.
#   The fixed cost is the expensive part — the per-request cost
#   is negligible at low traffic.
