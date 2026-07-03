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
#   How to read it:
#     10.0.0.0/16  → 10.0.X.X can be anything
#                  → 2^(32-16) = 2^16 = 65,536 IPs
#                  → Range: 10.0.0.0 to 10.0.255.255
#
#     10.0.1.0/24  → 10.0.1.X can be anything
#                  → 2^(32-24) = 2^8 = 256 IPs
#                  → Range: 10.0.1.0 to 10.0.1.255
#
#     10.0.1.0/28  → 2^(32-28) = 2^4 = 16 IPs
#                  → Range: 10.0.1.0 to 10.0.1.15
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
#     Note: subnets CANNOT overlap. 10.0.1.0/24 and 10.0.2.0/24 are
#     separate ranges. AWS rejects overlapping CIDRs.
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
#   Public subnet = route table has 0.0.0.0/0 → Internet Gateway
#     → Resources here CAN have public IPs and be reached from internet
#     → Used for: ALB, NAT Gateway, bastion hosts
#
#   Private subnet = route table has 0.0.0.0/0 → NAT Gateway (or nothing)
#     → Resources here CANNOT be reached from internet directly
#     → Used for: ECS tasks, Lambda, databases (RDS), internal services
#
#   Practical example — what lives where:
#
#     Public subnet A (10.0.1.0/24, eu-west-1a):
#       ├─ ALB (10.0.1.50)          ← receives user traffic from internet
#       ├─ NAT Gateway (10.0.1.100) ← lets private subnet reach internet
#       └─ (Internet Gateway is VPC-level, not per-subnet)
#
#     Private subnet A (10.0.11.0/24, eu-west-1a):
#       ├─ ECS Task 1 (10.0.11.20)  ← runs your container
#       ├─ Lambda ENI  (10.0.11.35) ← Lambda gets a private IP here
#       └─ RDS instance (10.0.11.50) ← database, totally isolated
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
