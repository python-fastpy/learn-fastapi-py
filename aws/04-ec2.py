# ══════════════════════════════════════════════════════════════════
# AWS Deployment — EC2 (Step 3)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 03-s3.py  |  next: 05-lambda.py →

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
#   ── AMI (Amazon Machine Image) ─────────────────────────────
#
#   A snapshot of an operating system + pre-installed software.
#   Like a "template" for creating servers.
#
#   Common AMIs:
#     Amazon Linux 2023  → lightweight, AWS-optimized, free
#     Ubuntu 22.04 LTS   → popular for Python/Node apps
#     Windows Server     → .NET apps, $$ (license cost built in)
#     Custom AMI         → your own pre-configured image
#
#   Practical example:
#     You launch an EC2 with Amazon Linux 2023 AMI.
#     It comes with: Python 3.9, dnf package manager, AWS CLI.
#     You then install Python 3.11, uv, your app, and create
#     a CUSTOM AMI from this configured instance. Next time you
#     can launch from YOUR AMI — app is already installed.
#
#     AWS Console: EC2 → Instances → select instance
#     → Actions → Image and templates → Create image
#     → Name: "book-store-api-v1" → Create
#
#   ── Instance Type ──────────────────────────────────────────
#
#   CPU + memory combo. The letter prefix tells you the family:
#
#     ┌────────┬──────────────────┬────────────────────────────┐
#     │ Family │ Optimized For    │ Example Use                │
#     ├────────┼──────────────────┼────────────────────────────┤
#     │ t3/t4g │ Burstable        │ Dev servers, light APIs    │
#     │ m6i    │ General purpose  │ Web servers, databases     │
#     │ c6i    │ Compute          │ ML inference, batch jobs   │
#     │ r6i    │ Memory           │ In-memory caches, Redis    │
#     │ g5     │ GPU              │ ML training, video render  │
#     │ i3     │ Storage I/O      │ High-throughput databases  │
#     └────────┴──────────────────┴────────────────────────────┘
#
#   Size suffixes (within a family):
#     t3.nano   → 2 vCPU, 0.5 GB   (~$3.80/month)
#     t3.micro  → 2 vCPU, 1 GB     (~$7.60/month) ← free tier
#     t3.small  → 2 vCPU, 2 GB     (~$15/month)
#     t3.medium → 2 vCPU, 4 GB     (~$30/month)
#     t3.large  → 2 vCPU, 8 GB     (~$60/month)
#     t3.xlarge → 4 vCPU, 16 GB    (~$121/month)
#
#   Burstable (t3) explained:
#     You earn CPU credits while idle (baseline: 20% CPU for t3.micro).
#     When your app spikes, it spends credits to burst to 100% CPU.
#     Credits run out → throttled to baseline (20%).
#     Use t3.unlimited to avoid throttling (pay for extra bursts).
#
#   ARM vs x86:
#     t4g (ARM/Graviton) is ~20% cheaper than t3 (x86) for same specs.
#     Python apps work on both. Use ARM unless you need x86-specific libs.
#
#   ── Key Pair ───────────────────────────────────────────────
#
#   An SSH key pair for logging into the instance remotely.
#   AWS stores the PUBLIC key. You download the PRIVATE key (.pem).
#
#   Flow:
#     1. Create key pair → download book-store-key.pem
#     2. Launch instance with this key pair
#     3. SSH in: ssh -i book-store-key.pem ec2-user@<public-ip>
#
#   IMPORTANT:
#     - You can ONLY download the .pem at creation time. Lose it = locked out.
#     - chmod 400 the file (read-only) or SSH refuses to use it.
#     - For Windows: use PuTTY and convert .pem → .ppk with PuTTYgen.
#     - Alternative: use EC2 Instance Connect (browser-based SSH, no key needed).
#
#   ── Elastic IP ─────────────────────────────────────────────
#
#   A static public IPv4 address that you OWN (persists across restarts).
#   Without it, the instance gets a NEW random public IP every time
#   it stops and starts.
#
#   Practical example:
#     Your DNS points books.example.com → 54.1.2.3 (Elastic IP).
#     You stop the instance for maintenance, start it again.
#     The Elastic IP stays at 54.1.2.3 — DNS still works.
#     Without Elastic IP, the IP changes and DNS breaks.
#
#   COST:
#     Attached to a RUNNING instance → FREE
#     NOT attached (or instance is stopped) → $0.005/hour (~$3.60/month)
#     AWS charges for UNUSED Elastic IPs to discourage hoarding.
#
#   Note: For production APIs, use a load balancer (ALB) instead
#   of Elastic IPs. ALB has its own DNS name that never changes.
#
#   ── EBS Volume (Elastic Block Store) ───────────────────────
#
#   Disk storage that attaches to EC2 instances. Like plugging
#   a hard drive into a server. Persists independently of the instance.
#
#   Volume types:
#     ┌──────────┬──────────┬─────────────┬──────────────────────┐
#     │ Type     │ IOPS     │ Cost/GB/mo  │ Use Case             │
#     ├──────────┼──────────┼─────────────┼──────────────────────┤
#     │ gp3      │ 3000     │ $0.08       │ General (default)    │
#     │ gp2      │ varies   │ $0.10       │ Legacy general       │
#     │ io2      │ 64,000   │ $0.125      │ Databases (high IO)  │
#     │ st1      │ 500      │ $0.045      │ Big data, logs       │
#     │ sc1      │ 250      │ $0.015      │ Archive, cold data   │
#     └──────────┴──────────┴─────────────┴──────────────────────┘
#
#   Key behaviors:
#     - EBS is in ONE AZ. Can't attach to instances in other AZs.
#     - You can snapshot an EBS volume → create a volume in another AZ.
#     - Root volume (OS) is deleted when instance terminates by default.
#       Change "Delete on termination" to No if you want to keep it.
#     - You can resize volumes live (no restart needed, then extend filesystem).
#
#   ── User Data ──────────────────────────────────────────────
#
#   A bash script that runs ONCE at first boot. Automate setup
#   so you don't have to SSH in and install things manually.
#
#   Example user data for our book-store API:
#
#     #!/bin/bash
#     dnf install python3.11 -y
#     curl -LsSf https://astral.sh/uv/install.sh | sh
#     source /root/.local/bin/env
#     mkdir -p /app && cd /app
#     # (In production, pull code from S3 or CodeDeploy)
#     echo 'ENV=production' > .env
#     # Start the app
#     uv run uvicorn main:app --host 0.0.0.0 --port 8000
#
#   View user data logs: /var/log/cloud-init-output.log
#   Debug: if your instance starts but the app isn't running,
#   check this log file — user data errors are silent.
#
#   ── Instance State ─────────────────────────────────────────
#
#   Running  → you're billed for compute + EBS + network
#   Stopped  → no compute charge, EBS still billed (~$0.08/GB/mo)
#   Terminated → everything deleted (unless "delete on termination" = No for EBS)
#
#   ┌──────────┐  stop   ┌──────────┐  start  ┌──────────┐
#   │ Running  │ ──────► │ Stopped  │ ──────► │ Running  │
#   │ ($$$)    │         │ (EBS $$) │         │ ($$$)    │
#   └────┬─────┘         └──────────┘         └──────────┘
#        │ terminate
#        ▼
#   ┌──────────┐
#   │Terminated│  ← gone forever (unless you made an AMI/snapshot)
#   │ (free)   │
#   └──────────┘
#
#   IMPORTANT: "Stop" preserves your data. "Terminate" destroys it.
#   Public IP changes on stop/start (use Elastic IP to keep it).
#
# ── IMPORTANT: Terminate When Done ──────────────────────────
#
#   EC2 → select instance → Instance state → Terminate instance
#   (Stopped instances still cost money for EBS storage)
