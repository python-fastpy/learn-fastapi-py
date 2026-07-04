# ══════════════════════════════════════════════════════════════════
# AWS Deployment — VPC (Step 1)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 01-overview-and-app.py  |  next: 03-s3.py →

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
#   ── CIDR Block ──────────────────────────────────────────────
#
#   CIDR = Classless Inter-Domain Routing. A compact way to define
#   a range of IP addresses.
#
#   Format:  <base IP> / <prefix bits>
#            10.0.0.0/16 means "keep the first 16 bits fixed"
#
#   How to read it (shown in binary so you can see exactly which bits vary):
#
#     10.0.0.0/16  → first 16 bits are fixed, last 16 bits vary
#                  → 2^(32-16) = 2^16 = 65,536 IPs
#                  → Range: 10.0.0.0 to 10.0.255.255
#
#       10      .  0       .  0        .  0
#       00001010 . 00000000 . 00000000 . 00000000
#       ├──── fixed (16) ──┤  ├── vary (16) ──────┤
#                             ^^^^^^^^   ^^^^^^^^
#                             these 2 octets can be 0-255 each
#
#     10.0.1.0/24  → first 24 bits are fixed, last 8 bits vary
#                  → 2^(32-24) = 2^8 = 256 IPs
#                  → Range: 10.0.1.0 to 10.0.1.255
#
#       10      .  0       .  1        .  0
#       00001010 . 00000000 . 00000001 . 00000000
#       ├────── fixed (24) ───────────┤  ├vary(8)┤
#                                        ^^^^^^^^
#                                        last octet can be 0-255
#
#     10.0.1.0/28  → first 28 bits are fixed, last 4 bits vary
#                  → 2^(32-28) = 2^4 = 16 IPs
#                  → Range: 10.0.1.0 to 10.0.1.15
#
#       10      .  0       .  1        .  0
#       00001010 . 00000000 . 00000001 . 00000000
#       ├─────── fixed (28) ──────────────┤├v(4)┤
#                                          ^^^^
#                                          only last 4 bits of the
#                                          last octet vary (0-15)
#
#       Why 0 to 15?  The last octet has 8 bits: 0000|0000
#         /28 fixes the first 4 bits of that octet: 0000|????
#         The ???? part can be 0000 (0) to 1111 (15)
#         So: 10.0.1.0, 10.0.1.1, 10.0.1.2 ... 10.0.1.15
#
#   Common CIDR sizes:
#     /16 = 65,536 IPs  → VPC level (big network)
#     /20 = 4,096 IPs   → large subnet
#     /24 = 256 IPs     → typical subnet
#     /28 = 16 IPs      → smallest allowed in AWS
#
#   Practical example — our book-store VPC:
#     VPC:              10.0.0.0/16    (65,536 IPs — the whole space)
#     Public subnet A:  10.0.1.0/24   (256 IPs: 10.0.1.0 - 10.0.1.255)
#     Public subnet B:  10.0.2.0/24   (256 IPs: 10.0.2.0 - 10.0.2.255)
#     Private subnet A: 10.0.11.0/24  (256 IPs: 10.0.11.0 - 10.0.11.255)
#     Private subnet B: 10.0.12.0/24  (256 IPs: 10.0.12.0 - 10.0.12.255)
#
#     Why 1,2 for public and 11,12 for private?
#     These numbers are NOT fixed — you choose them. Any non-overlapping
#     range within 10.0.0.0/16 works. The gap (3-10) leaves room to add
#     more subnets later. Other common patterns:
#
#       Pattern 1 (what we use — gap between public/private):
#         Public:  10.0.1.0/24, 10.0.2.0/24
#         Private: 10.0.11.0/24, 10.0.12.0/24
#
#       Pattern 2 (sequential):
#         Public:  10.0.1.0/24, 10.0.2.0/24
#         Private: 10.0.3.0/24, 10.0.4.0/24
#
#       Pattern 3 (by AZ — 10.0.{AZ}{type}.0):
#         AZ-a public: 10.0.10.0/24   AZ-b public: 10.0.20.0/24
#         AZ-a private: 10.0.11.0/24  AZ-b private: 10.0.21.0/24
#
#       Pattern 4 (large subnets with /20):
#         Public:  10.0.0.0/20  (4,096 IPs)
#         Private: 10.0.16.0/20 (4,096 IPs)
#
#     The only rule: subnets CANNOT overlap and must be within the VPC CIDR.
#     AWS rejects overlapping CIDRs.
#
#     AWS reserves 5 IPs per subnet:
#       .0   = network address
#       .1   = VPC router
#       .2   = DNS server
#       .3   = reserved for future
#       .255 = broadcast (not used but reserved)
#     So a /24 subnet gives you 251 usable IPs, not 256.
#
#   Private IP ranges (RFC 1918 — never routed on public internet):
#     10.0.0.0/8       (10.x.x.x)     ← most VPCs use this
#     172.16.0.0/12    (172.16-31.x.x)
#     192.168.0.0/16   (192.168.x.x)  ← your home WiFi router
#
#   ── Subnet ─────────────────────────────────────────────────
#
#   A subnet is a slice of the VPC's IP range, placed in ONE
#   Availability Zone. A subnet is "public" or "private" based
#   on its route table — not a special setting.
#
#   ┌─────────────────────────────────────────────────────────────┐
#   │                  VPC: 10.0.0.0/16                           │
#   │                                                             │
#   │   ┌─── eu-west-1a ──────────┐  ┌─── eu-west-1b ──────────┐ │
#   │   │                         │  │                          │ │
#   │   │  PUBLIC 10.0.1.0/24     │  │  PUBLIC 10.0.2.0/24      │ │
#   │   │  ┌───────────────────┐  │  │  ┌────────────────────┐  │ │
#   │   │  │ ALB (10.0.1.50)   │  │  │  │ ALB (10.0.2.50)    │  │ │
#   │   │  │ NAT GW (10.0.1.100) │  │  │                    │  │ │
#   │   │  └───────┬───────────┘  │  │  └────────────────────┘  │ │
#   │   │          │ route:       │  │                          │ │
#   │   │          │ 0.0.0.0/0   │  │                          │ │
#   │   │          │ → IGW       │  │                          │ │
#   │   │          │ (internet)  │  │                          │ │
#   │   │  ........│............  │  │                          │ │
#   │   │  PRIVATE 10.0.11.0/24   │  │  PRIVATE 10.0.12.0/24   │ │
#   │   │  ┌───────────────────┐  │  │  ┌────────────────────┐  │ │
#   │   │  │ ECS (10.0.11.20)  │  │  │  │ ECS (10.0.12.20)   │  │ │
#   │   │  │ Lambda(10.0.11.35)│  │  │  │ RDS (10.0.12.50)   │  │ │
#   │   │  │ RDS (10.0.11.50)  │  │  │  │                    │  │ │
#   │   │  └───────────────────┘  │  │  └────────────────────┘  │ │
#   │   │     route: 0.0.0.0/0   │  │                          │ │
#   │   │     → NAT GW           │  │                          │ │
#   │   │     (outbound only)    │  │                          │ │
#   │   └─────────────────────────┘  └──────────────────────────┘ │
#   └─────────────────────────────────────────────────────────────┘
#
#   What makes a subnet public or private? Only the route table:
#
#     ┌─────────────────┬────────────────────┬─────────────────────┐
#     │                 │ Public Subnet       │ Private Subnet      │
#     ├─────────────────┼────────────────────┼─────────────────────┤
#     │ Route for       │ 0.0.0.0/0 → IGW   │ 0.0.0.0/0 → NAT GW │
#     │ 0.0.0.0/0       │ (internet gateway) │ (or no route)       │
#     ├─────────────────┼────────────────────┼─────────────────────┤
#     │ Inbound from    │ Yes (if SG allows) │ No (no direct path) │
#     │ internet?       │                    │                     │
#     ├─────────────────┼────────────────────┼─────────────────────┤
#     │ Outbound to     │ Yes (via IGW)      │ Yes (via NAT GW)    │
#     │ internet?       │                    │ No (if no NAT)      │
#     ├─────────────────┼────────────────────┼─────────────────────┤
#     │ Used for        │ ALB, NAT GW,       │ ECS tasks, Lambda,  │
#     │                 │ bastion hosts      │ RDS, internal svc   │
#     └─────────────────┴────────────────────┴─────────────────────┘
#
#   Example — a request flows through:
#
#     User (internet)
#       │
#       ▼
#     Internet Gateway (VPC level — not per subnet)
#       │
#       ▼
#     ALB in public subnet (10.0.1.50)
#       │  ALB forwards to healthy ECS tasks
#       ▼
#     ECS task in private subnet (10.0.11.20)
#       │  task needs to call external API
#       ▼
#     NAT Gateway in public subnet (10.0.1.100)
#       │  translates private IP → public IP
#       ▼
#     Internet (response comes back same path)
#
#   WHY separate? Security. Even if someone compromises the ALB,
#   they can't directly reach the containers or database. The
#   containers are on a completely different network segment with
#   no inbound internet route.
#
#   ── Availability Zone (AZ) ─────────────────────────────────
#
#   An AZ is a physically separate data center (or group of data
#   centers) within an AWS region. They have independent power,
#   cooling, and networking. Connected via low-latency fiber.
#
#   Region eu-west-1 (Ireland) has 3 AZs:
#     eu-west-1a  ← data center group A
#     eu-west-1b  ← data center group B (separate building/campus)
#     eu-west-1c  ← data center group C
#
#   WHY use multiple AZs?
#     If eu-west-1a loses power, your app keeps running in eu-west-1b.
#     This is why ALB requires subnets in at least 2 AZs.
#
#   Practical example — our setup uses 2 AZs:
#
#     eu-west-1a                    eu-west-1b
#     ┌──────────────────┐          ┌──────────────────┐
#     │ Public  10.0.1.0 │          │ Public  10.0.2.0 │
#     │   ALB node ────────────────── ALB node         │
#     │   NAT Gateway    │          │                  │
#     ├──────────────────┤          ├──────────────────┤
#     │ Private 10.0.11.0│          │ Private 10.0.12.0│
#     │   ECS Task 1     │          │   ECS Task 2     │
#     └──────────────────┘          └──────────────────┘
#
#     If eu-west-1a goes down:
#       - ALB stops sending traffic to Task 1 (health check fails)
#       - ALB sends ALL traffic to Task 2 in eu-west-1b
#       - Users never notice (ALB handles the switch automatically)
#
#   Note: AZ names are mapped differently per AWS account.
#   Your "eu-west-1a" might be a different physical data center
#   than someone else's "eu-west-1a". AWS does this to spread load.
#
#   ── Internet Gateway (IGW) ────────────────────────────────
#
#   The front door of your VPC. Connects it to the public internet.
#   Bidirectional — traffic flows both IN and OUT.
#
#   One per VPC. It's a managed AWS service (no maintenance, no cost,
#   no bandwidth limit). You just create it and attach it to the VPC.
#
#   HOW it works:
#     1. An EC2 instance in a public subnet has public IP 54.1.2.3
#     2. User sends request to 54.1.2.3
#     3. IGW receives it, translates public IP → private IP (NAT)
#     4. Forwards to the instance's private IP (10.0.1.50)
#     5. Response goes back through IGW → user
#
#   Practical example:
#     A user hits your ALB's public DNS name:
#       book-store-alb-123.eu-west-1.elb.amazonaws.com
#       → DNS resolves to public IP 54.1.2.3
#       → Request hits Internet Gateway
#       → IGW routes to ALB's private IP in public subnet
#       → ALB routes to ECS task in private subnet
#       → Response flows back: ECS → ALB → IGW → user
#
#   Without an IGW, nothing in your VPC can reach the internet
#   and nothing from the internet can reach your VPC. It's a
#   completely isolated network.
#
#   ── NAT Gateway ────────────────────────────────────────────
#
#   Network Address Translation gateway. Lets resources in PRIVATE
#   subnets make outbound calls to the internet, without being
#   reachable FROM the internet. One-way traffic only.
#
#   WHY needed?
#     Your ECS containers in private subnets need to:
#       - Pull Docker images from ECR (goes through internet)
#       - Call external APIs (LLM orchestrator, Sphinx auth, etc.)
#       - Download Python packages during build
#       - Send logs to external services
#     But they should NOT be directly reachable from the internet.
#
#   HOW it works:
#     1. ECS task (10.0.11.20) wants to call https://api.openai.com
#     2. Private subnet route table: 0.0.0.0/0 → NAT Gateway
#     3. Request goes to NAT Gateway in PUBLIC subnet (10.0.1.100)
#     4. NAT replaces source IP: 10.0.11.20 → NAT's public IP (52.x.x.x)
#     5. Request goes through Internet Gateway to api.openai.com
#     6. Response comes back to NAT's public IP
#     7. NAT translates back: 52.x.x.x → 10.0.11.20
#     8. Response delivered to ECS task
#
#     The external server only sees the NAT's public IP.
#     It can't initiate a connection TO 10.0.11.20 — it doesn't
#     know that address exists. One-way only.
#
#   Practical example from the real skills repo:
#     Story-drafting container (private subnet) calls:
#       - llmorch-ha.int.thomsonreuters.com (LLM orchestrator)
#       - api.sphinx-test.thomsonreuters.com (Sphinx auth)
#       - semantic-search.dev.82056.aws-int... (search API)
#     All go through NAT Gateway → Internet Gateway → internet.
#
#   COST WARNING:
#     NAT Gateway = $0.045/hour = ~$32/month (even if idle!)
#     Plus $0.045/GB of data processed.
#     It's often the MOST EXPENSIVE part of a small deployment.
#
#     Cost-saving options:
#       - "In 1 AZ" = 1 NAT ($32/mo). If that AZ goes down,
#         private subnets in the other AZ lose internet access.
#       - "1 per AZ" = 2 NATs ($64/mo). High availability.
#       - VPC endpoints (see below) = skip NAT for AWS services.
#
#   VPC Endpoints — avoid NAT for AWS services:
#     Instead of ECS → NAT → internet → ECR, you can create a
#     VPC endpoint so ECS → ECR directly (stays within AWS network).
#
#     Gateway endpoints (free):  S3, DynamoDB
#     Interface endpoints ($):   ECR, Secrets Manager, CloudWatch, etc.
#                                $0.01/hour + $0.01/GB
#
#     For small deployments NAT is simpler. For production with
#     high data transfer, VPC endpoints save money.
#
#   ── Route Table ────────────────────────────────────────────
#
#   A set of rules (routes) that determine where network traffic
#   goes. Each subnet is associated with exactly ONE route table.
#   Traffic is matched against routes — most specific match wins.
#
#   Route format:
#     Destination (CIDR)     Target
#     10.0.0.0/16            local        ← traffic within VPC
#     0.0.0.0/0              igw-abc123   ← everything else → internet
#
#   Practical example — our two route tables:
#
#   Public Route Table (attached to public subnets):
#     ┌──────────────────┬─────────────────┬──────────────────────┐
#     │ Destination      │ Target          │ What it means        │
#     ├──────────────────┼─────────────────┼──────────────────────┤
#     │ 10.0.0.0/16      │ local           │ VPC internal traffic │
#     │                  │                 │ stays in VPC         │
#     │ 0.0.0.0/0        │ igw-abc123      │ Everything else goes │
#     │                  │ (Internet GW)   │ to the internet      │
#     └──────────────────┴─────────────────┴──────────────────────┘
#
#   Private Route Table (attached to private subnets):
#     ┌──────────────────┬─────────────────┬──────────────────────┐
#     │ Destination      │ Target          │ What it means        │
#     ├──────────────────┼─────────────────┼──────────────────────┤
#     │ 10.0.0.0/16      │ local           │ VPC internal traffic │
#     │                  │                 │ stays in VPC         │
#     │ 0.0.0.0/0        │ nat-xyz789      │ Everything else goes │
#     │                  │ (NAT Gateway)   │ through NAT (1-way)  │
#     └──────────────────┴─────────────────┴──────────────────────┘
#
#   How routing works step-by-step:
#
#     Example 1: ECS task (10.0.11.20) → ALB (10.0.1.50)
#       Route table checks destination 10.0.1.50
#       Matches 10.0.0.0/16 → "local" → VPC internal routing
#       Traffic stays inside the VPC. Fast, free, no NAT needed.
#
#     Example 2: ECS task (10.0.11.20) → api.openai.com (104.18.7.23)
#       Route table checks destination 104.18.7.23
#       Does NOT match 10.0.0.0/16 (not a VPC address)
#       Matches 0.0.0.0/0 → NAT Gateway → Internet Gateway → internet
#
#     Example 3: User (1.2.3.4) → ALB public IP (54.1.2.3)
#       Hits Internet Gateway → routes to ALB in public subnet
#       ALB's public route table: 0.0.0.0/0 → igw (bidirectional)
#
#   Most specific route wins:
#     If you had routes for both 10.0.0.0/16 and 10.0.11.0/24,
#     traffic to 10.0.11.50 matches /24 (more specific) first.
#     This is how you can route specific subnets differently.
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
#
#      DNS hostnames: gives each instance a public DNS name
#        e.g., ec2-10-0-1-5.eu-west-1.compute.amazonaws.com
#        Without it, instances only get IP addresses, no names.
#
#      DNS resolution: lets resources in the VPC use AWS's
#        built-in DNS server (at 10.0.0.2) to resolve domain
#        names. Without it, your containers can't look up
#        hostnames like api.example.com or RDS endpoints.
#
#      Why both? RDS gives you a hostname endpoint like
#        book-store-db.abc123.eu-west-1.rds.amazonaws.com
#        Your ECS tasks need DNS resolution to convert that
#        hostname into an IP address they can connect to.
#        Most AWS services won't work inside the VPC without
#        these two settings enabled.
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
#
# ══════════════════════════════════════════════════════════════════
# APPENDIX: Understanding IP Addresses & Binary
# ══════════════════════════════════════════════════════════════════
#
# This section explains how binary and bits work — the foundation
# for understanding CIDR notation, subnets, and IP addresses above.
# Skip if you're already comfortable with binary math.
#
#
# ── Think of it like a light switch ──────────────────────────
#
#   You already know binary — you just don't know you know it.
#
#   A light switch has 2 states: OFF or ON.
#   In computers, we write that as: 0 or 1.
#   That's a "bit" — the smallest piece of information.
#
#     ┌─────────┐     ┌─────────┐
#     │  OFF    │     │   ON    │
#     │   0     │     │    1    │
#     └─────────┘     └─────────┘
#       1 switch = 1 bit = 2 possible states
#
#
# ── What happens with 2 switches? ───────────────────────────
#
#   Now imagine 2 light switches on a wall. How many combinations?
#
#     Switch A  │ Switch B  │ Pattern
#     ──────────┼───────────┼────────
#      OFF      │  OFF      │   00
#      OFF      │  ON       │   01
#      ON       │  OFF      │   10
#      ON       │  ON       │   11
#
#     2 switches = 2 bits = 4 combinations
#
#   But how do we turn these ON/OFF patterns into NUMBERS?
#
#   The trick: each switch position has a VALUE assigned to it.
#   The rightmost switch = 1, the next = 2, then 4, 8, 16...
#   (each position is DOUBLE the previous)
#
#     Think of it like money:
#       Decimal: you have a $10 bill and a $1 coin
#                $10 spot = tens place, $1 spot = ones place
#                Having both = $10 + $1 = $11
#
#       Binary:  you have a "2-slot" and a "1-slot"
#                Left spot = twos place, Right spot = ones place
#                Having both ON = 2 + 1 = 3
#
#     ┌─────────────────────────────┐
#     │  Position:    1       0     │
#     │  Value:       2       1     │
#     │                             │
#     │  Think of these as          │
#     │  "price tags" on each slot  │
#     └─────────────────────────────┘
#
#   To read a binary number:
#     1 = ON  → add that position's value
#     0 = OFF → skip it (add nothing)
#
#     Bits │ Calculation                    │ Value
#     ─────┼────────────────────────────────┼──────
#      00  │ 2 is OFF, 1 is OFF → 0 + 0   │  0
#      01  │ 2 is OFF, 1 is ON  → 0 + 1   │  1
#      10  │ 2 is ON,  1 is OFF → 2 + 0   │  2
#      11  │ 2 is ON,  1 is ON  → 2 + 1   │  3
#
#   That's it! Binary is just: check which positions are ON,
#   add up their values.
#
#
# ── 3 switches = 3 bits ─────────────────────────────────────
#
#   Add one more switch. Its value? Double the last one: 4.
#
#     Position:   2       1       0
#     Value:      4       2       1
#
#     Bits │ Calculation           │ Value
#     ─────┼───────────────────────┼──────
#     000  │ 0 + 0 + 0             │  0
#     001  │ 0 + 0 + 1             │  1
#     010  │ 0 + 2 + 0             │  2
#     011  │ 0 + 2 + 1             │  3
#     100  │ 4 + 0 + 0             │  4
#     101  │ 4 + 0 + 1             │  5
#     110  │ 4 + 2 + 0             │  6
#     111  │ 4 + 2 + 1             │  7
#
#     3 switches = 3 bits = 8 combinations (0 to 7)
#
#   See the pattern? Every time you add 1 switch, the number
#   of combinations DOUBLES:
#     1 switch → 2 combos
#     2 switches → 4 combos
#     3 switches → 8 combos
#
#
# ── 4 switches = 4 bits (a "nibble") ────────────────────────
#
#   One more switch. Value? Double again: 8.
#
#     Position:   3       2       1       0
#     Value:      8       4       2       1
#
#     Bits  │ Calculation          │ Value
#     ──────┼──────────────────────┼──────
#     0000  │ 0 + 0 + 0 + 0       │  0
#     0001  │ 0 + 0 + 0 + 1       │  1
#     0010  │ 0 + 0 + 2 + 0       │  2
#     0011  │ 0 + 0 + 2 + 1       │  3
#     0100  │ 0 + 4 + 0 + 0       │  4
#     0101  │ 0 + 4 + 0 + 1       │  5
#     0110  │ 0 + 4 + 2 + 0       │  6
#     0111  │ 0 + 4 + 2 + 1       │  7
#     1000  │ 8 + 0 + 0 + 0       │  8
#     1001  │ 8 + 0 + 0 + 1       │  9
#     1010  │ 8 + 0 + 2 + 0       │ 10
#     1011  │ 8 + 0 + 2 + 1       │ 11
#     1100  │ 8 + 4 + 0 + 0       │ 12
#     1101  │ 8 + 4 + 0 + 1       │ 13
#     1110  │ 8 + 4 + 2 + 0       │ 14
#     1111  │ 8 + 4 + 2 + 1       │ 15
#
#     4 switches = 4 bits = 16 combinations (0 to 15)
#
#     This is why CIDR /28 gives 16 IPs — the last 4 bits vary
#     from 0000 (0) to 1111 (15) = 16 possible addresses.
#
#
# ── 8 switches = 8 bits (one "octet") ───────────────────────
#
#   An IP address uses 8 bits for each of its 4 numbers.
#   That's 8 switches, with values doubling each time:
#
#     Position:   7      6     5     4     3    2    1    0
#     Value:     128    64    32    16     8    4    2    1
#
#   8 bits = 256 combinations (0 to 255).
#   That's why each number in an IP maxes out at 255!
#
#   All switches ON:  128 + 64 + 32 + 16 + 8 + 4 + 2 + 1 = 255
#   All switches OFF: 0 + 0 + 0 + 0 + 0 + 0 + 0 + 0 = 0
#
#
# ── How to convert a number to binary (the easy way) ────────
#
#   Think of it like making change with special coins.
#   You have coins worth: 128, 64, 32, 16, 8, 4, 2, 1
#   You need to make the exact amount using each coin AT MOST ONCE.
#
#   Start with the biggest coin. Can you use it? If yes, take it
#   and subtract. Move to the next smaller coin. Repeat.
#
#   Example: convert 10 to binary
#
#     You need to make 10 with coins: 128, 64, 32, 16, 8, 4, 2, 1
#
#     128-coin? No  (128 > 10, too big)          → 0
#      64-coin? No  (64 > 10, too big)           → 0
#      32-coin? No  (32 > 10, too big)           → 0
#      16-coin? No  (16 > 10, too big)           → 0
#       8-coin? YES (8 ≤ 10, take it!)           → 1   left: 10-8 = 2
#       4-coin? No  (4 > 2, too big)             → 0
#       2-coin? YES (2 ≤ 2, take it!)            → 1   left: 2-2 = 0
#       1-coin? No  (nothing left)               → 0
#
#     Result: 00001010 = 10  ✓
#     Check:  8 + 2 = 10 ✓
#
#   Example: convert 200 to binary
#
#     128-coin? YES (128 ≤ 200, take it!)        → 1   left: 200-128 = 72
#      64-coin? YES (64 ≤ 72, take it!)          → 1   left: 72-64 = 8
#      32-coin? No  (32 > 8)                     → 0
#      16-coin? No  (16 > 8)                     → 0
#       8-coin? YES (8 ≤ 8, take it!)            → 1   left: 8-8 = 0
#       4-coin? No  (nothing left)               → 0
#       2-coin? No                               → 0
#       1-coin? No                               → 0
#
#     Result: 11001000 = 200  ✓
#     Check:  128 + 64 + 8 = 200 ✓
#
#   Example: convert 255 to binary
#
#     128-coin? YES → 1   left: 255-128 = 127
#      64-coin? YES → 1   left: 127-64 = 63
#      32-coin? YES → 1   left: 63-32 = 31
#      16-coin? YES → 1   left: 31-16 = 15
#       8-coin? YES → 1   left: 15-8 = 7
#       4-coin? YES → 1   left: 7-4 = 3
#       2-coin? YES → 1   left: 3-2 = 1
#       1-coin? YES → 1   left: 1-1 = 0
#
#     Result: 11111111 = 255  ✓  (all switches ON!)
#
#
# ── Now you can read IP addresses in binary ──────────────────
#
#   An IP address = 4 groups of 8 switches = 32 switches total.
#
#   Example: 10.0.1.5
#
#     10       .  0        .  1        .  5
#     00001010 .  00000000 .  00000001 .  00000101
#     ├─8 bits─┤  ├─8 bits─┤  ├─8 bits─┤  ├─8 bits─┤
#                       Total = 32 bits
#
#     Let's verify each number:
#       10  = 00001010 → 8 + 2 = 10 ✓
#        0  = 00000000 → all OFF = 0 ✓
#        1  = 00000001 → 1 = 1 ✓
#        5  = 00000101 → 4 + 1 = 5 ✓
#
#
# ── Quick reference ──────────────────────────────────────────
#
#     Decimal │ Binary     │ Coins used
#     ────────┼────────────┼──────────────────────────────────
#       0     │ 00000000   │ none
#       1     │ 00000001   │ 1
#       5     │ 00000101   │ 4 + 1
#      10     │ 00001010   │ 8 + 2
#      15     │ 00001111   │ 8 + 4 + 2 + 1
#     128     │ 10000000   │ 128
#     192     │ 11000000   │ 128 + 64
#     255     │ 11111111   │ 128 + 64 + 32 + 16 + 8 + 4 + 2 + 1
#
#
# ── The doubling pattern ─────────────────────────────────────
#
#   Every time you add 1 more switch (bit), the number of
#   possible combinations DOUBLES:
#
#     Switches │ Combinations │ Range      │ Used in networking
#     ─────────┼──────────────┼────────────┼──────────────────
#      1       │      2       │ 0-1        │
#      2       │      4       │ 0-3        │
#      3       │      8       │ 0-7        │
#      4       │     16       │ 0-15       │ CIDR /28 (16 IPs)
#      5       │     32       │ 0-31       │
#      6       │     64       │ 0-63       │
#      7       │    128       │ 0-127      │
#      8       │    256       │ 0-255      │ CIDR /24 (256 IPs)
#     12       │  4,096       │ 0-4095     │ CIDR /20 (4,096 IPs)
#     16       │ 65,536       │ 0-65535    │ CIDR /16 (65,536 IPs)
#     32       │ 4 billion    │ 0-4.2B     │ All possible IPs
