# ══════════════════════════════════════════════════════════════════
# AWS Deployment — RDS (Step 17)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 19-codedeploy-pipeline.py  |  next: 21-cognito.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 17: RDS — RELATIONAL DATABASE SERVICE      ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Managed relational databases. PostgreSQL, MySQL, MariaDB,
#       Oracle, SQL Server, or Aurora. AWS handles patching,
#       backups, failover. You just write SQL.
#
# REAL REPO: The book-store in-memory dict (books_db = {}) would
#            be replaced by RDS PostgreSQL in production. Many
#            enterprise Thomson Reuters services use RDS. The
#            backend uses DynamoDB (NoSQL) for sessions/checkpoints,
#            but relational data often goes to RDS.
#
# ── Supported Engines ───────────────────────────────────────
#
#   ┌──────────────┬───────────────────────────────────────────┐
#   │ Engine       │ Notes                                     │
#   ├──────────────┼───────────────────────────────────────────┤
#   │ PostgreSQL   │ Most popular for new projects. JSONB,     │
#   │              │ full-text search, extensions. Use this.   │
#   ├──────────────┼───────────────────────────────────────────┤
#   │ MySQL        │ Widely used. WordPress, legacy apps.      │
#   ├──────────────┼───────────────────────────────────────────┤
#   │ MariaDB      │ MySQL fork. Slightly faster in some cases.│
#   ├──────────────┼───────────────────────────────────────────┤
#   │ Oracle       │ Enterprise. Expensive licenses. Migration │
#   │              │ target: move to PostgreSQL when possible.  │
#   ├──────────────┼───────────────────────────────────────────┤
#   │ SQL Server   │ Microsoft. .NET shops use this.           │
#   ├──────────────┼───────────────────────────────────────────┤
#   │ Aurora       │ AWS-built. PostgreSQL/MySQL compatible.   │
#   │              │ 5x throughput, auto-scaling storage,      │
#   │              │ up to 15 read replicas. Premium price.    │
#   └──────────────┴───────────────────────────────────────────┘
#
#   Aurora is special:
#     - Wire-compatible with PostgreSQL or MySQL
#     - Storage auto-scales from 10 GB to 128 TB
#     - 6 copies of data across 3 AZs automatically
#     - Aurora Serverless v2: scales compute to zero
#     - Costs ~2x standard RDS but much more resilient
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console -> search "RDS" -> click it
#
#   2. Create DB Subnet Group first:
#      RDS -> Subnet groups -> "Create DB subnet group"
#      ┌──────────────────────────────────────────────────┐
#      │  Name:        book-store-db-subnets               │
#      │  Description: Private subnets for book-store DB   │
#      │  VPC:         book-store-vpc                      │
#      │                                                    │
#      │  Add subnets:                                     │
#      │    AZ: eu-west-1a  Subnet: private-subnet-1       │
#      │    AZ: eu-west-1b  Subnet: private-subnet-2       │
#      │    (must span at least 2 AZs)                     │
#      └──────────────────────────────────────────────────┘
#      -> Create
#
#   3. RDS -> Databases -> "Create database"
#      ┌──────────────────────────────────────────────────┐
#      │  Creation method: Standard create                 │
#      │  Engine:          PostgreSQL                      │
#      │  Version:         16.x (latest stable)            │
#      │                                                    │
#      │  Templates:       Free tier                       │
#      │    (or Production for Multi-AZ)                   │
#      │                                                    │
#      │  DB instance identifier: book-store-db            │
#      │  Master username:        bookadmin                │
#      │  Master password:        (use strong password)    │
#      │    -> Store in Secrets Manager: YES               │
#      │                                                    │
#      │  Instance class:                                  │
#      │    db.t3.micro (free tier — 1 vCPU, 1 GB RAM)    │
#      │    db.t3.medium (production — 2 vCPU, 4 GB RAM)  │
#      │                                                    │
#      │  Storage:                                         │
#      │    Type:      gp3 (General Purpose SSD)           │
#      │    Allocated: 20 GB                               │
#      │    Autoscaling: Enable (max 100 GB)               │
#      │                                                    │
#      │  Connectivity:                                    │
#      │    VPC:           book-store-vpc                   │
#      │    Subnet group:  book-store-db-subnets            │
#      │    Public access: NO (private subnets only!)      │
#      │    Security group: book-store-db-sg                │
#      │      -> Inbound: PostgreSQL (5432) from           │
#      │         book-store-app-sg (ECS security group)    │
#      │                                                    │
#      │  Multi-AZ: No (free tier) / Yes (production)      │
#      │                                                    │
#      │  Backup:                                          │
#      │    Retention: 7 days (up to 35 days)              │
#      │    Backup window: 03:00-04:00 UTC                 │
#      └──────────────────────────────────────────────────┘
#      -> Create database (takes 5-10 minutes)
#
# ── Key Concepts ────────────────────────────────────────────
#
#   ── DB Instance Classes ────────────────────────────────────
#
#   ┌──────────────┬──────────┬────────┬───────────────────┐
#   │ Class        │ vCPU     │ RAM    │ Use Case          │
#   ├──────────────┼──────────┼────────┼───────────────────┤
#   │ db.t3.micro  │ 2 (burst)│ 1 GB   │ Free tier / dev   │
#   │ db.t3.medium │ 2 (burst)│ 4 GB   │ Small production  │
#   │ db.r6g.large │ 2        │ 16 GB  │ Production        │
#   │ db.r6g.xlarge│ 4        │ 32 GB  │ Heavy workloads   │
#   │ db.r6g.4xl   │ 16       │ 128 GB │ Large databases   │
#   └──────────────┴──────────┴────────┴───────────────────┘
#
#   "t" = burstable (cheap, throttles under sustained load)
#   "r" = memory-optimized (consistent performance, production)
#   "m" = general purpose (balanced)
#
#   ── Multi-AZ Deployment ────────────────────────────────────
#
#   AWS maintains a STANDBY replica in a different AZ.
#   If the primary fails, AWS automatically fails over.
#
#   ┌────────────────────────────────────────────────────┐
#   │  VPC                                                │
#   │                                                      │
#   │  AZ-1a (Primary)         AZ-1b (Standby)           │
#   │  ┌──────────────┐       ┌──────────────┐           │
#   │  │ RDS Primary  │──────>│ RDS Standby  │           │
#   │  │ (read/write) │ sync  │ (not query-  │           │
#   │  │              │ repli │  able!)       │           │
#   │  └──────────────┘ cation└──────────────┘           │
#   │       ▲                        ▲                     │
#   │       │                  (takes over                 │
#   │   normal                  if primary                 │
#   │   traffic                 fails)                     │
#   └────────────────────────────────────────────────────┘
#
#   Failover takes 60-120 seconds. DNS endpoint stays the
#   same — your app reconnects automatically.
#
#   IMPORTANT: Multi-AZ standby is NOT a read replica.
#   You cannot run queries against it. It only exists
#   for automatic failover.
#
#   ── Read Replicas ──────────────────────────────────────────
#
#   Separate read-only copies for scaling read traffic.
#   Uses ASYNCHRONOUS replication (slight lag).
#
#   ┌──────────────┐      ┌──────────────┐
#   │ RDS Primary  │─────>│ Read Replica  │
#   │ (read/write) │async │ (read only)   │
#   └──────────────┘ repl └──────────────┘
#        ▲                      ▲
#        │                      │
#     writes              read-heavy queries
#     (INSERT/UPDATE)     (SELECT, reports)
#
#   Key facts:
#     - Up to 15 read replicas per primary (Aurora)
#     - Up to 5 read replicas per primary (standard RDS)
#     - Can be in a different region (cross-region replica)
#     - Can be promoted to standalone DB (disaster recovery)
#     - Async = reads might be slightly behind (ms to seconds)
#
#   ── Automated Backups ──────────────────────────────────────
#
#   RDS takes daily snapshots + continuous transaction logs.
#   You can restore to any point in time within the retention
#   window (1-35 days).
#
#   Point-in-time restore creates a NEW DB instance from the
#   backup. It does not overwrite the existing one.
#
#   Manual snapshots:
#     - Created on demand (or before risky changes)
#     - Persist indefinitely (until you delete them)
#     - Can be shared with other AWS accounts
#     - Can be copied to other regions
#
#   ── Connection from ECS ────────────────────────────────────
#
#   Your ECS tasks connect to RDS via the DB endpoint.
#   Store the connection string in Secrets Manager.
#
#   Security group rules:
#     book-store-db-sg (RDS):
#       Inbound: PostgreSQL (5432) from book-store-app-sg
#
#     book-store-app-sg (ECS):
#       Outbound: PostgreSQL (5432) to book-store-db-sg
#
#   Connection pattern (FastAPI + SQLAlchemy):
#
#     import os
#     from sqlalchemy import create_engine
#     from sqlalchemy.orm import sessionmaker
#
#     DATABASE_URL = os.environ["DATABASE_URL"]
#     # e.g., postgresql://bookadmin:pass@book-store-db.xxx.
#     #       eu-west-1.rds.amazonaws.com:5432/bookstore
#
#     engine = create_engine(DATABASE_URL, pool_size=5)
#     SessionLocal = sessionmaker(bind=engine)
#
#   The endpoint (hostname) looks like:
#     book-store-db.abc123xyz.eu-west-1.rds.amazonaws.com
#
#   ── Parameter Groups ───────────────────────────────────────
#
#   Engine-level configuration (like postgresql.conf).
#   Create a custom parameter group to tune settings:
#
#     max_connections:    100 (default) -> increase for ECS
#     shared_buffers:     25% of RAM
#     log_statement:      "all" (for debugging, not prod)
#     idle_in_transaction_session_timeout: 30000 (30s)
#
#   ── RDS Proxy ──────────────────────────────────────────────
#
#   Connection pooling managed by AWS. Essential for Lambda.
#
#   Problem: Lambda creates a new DB connection per invocation.
#   100 concurrent Lambdas = 100 connections. RDS max_connections
#   on db.t3.micro is only 87. Connections exhausted!
#
#   Solution: RDS Proxy sits between Lambda and RDS.
#   Lambda connects to the proxy. Proxy maintains a pool
#   of reusable connections to RDS.
#
#   ┌────────────┐     ┌───────────┐     ┌───────────┐
#   │  Lambda x  │────>│ RDS Proxy │────>│  RDS DB   │
#   │  100 calls │     │ (pool of  │     │ (only 10  │
#   │            │     │  10 conns)│     │  conns)   │
#   └────────────┘     └───────────┘     └───────────┘
#
#   RDS Proxy costs: ~$0.015/vCPU/hour of the DB instance.
#   For db.t3.medium (2 vCPU): ~$22/month.
#
# ── Cost ────────────────────────────────────────────────────
#
#   Free tier (first 12 months):
#     db.t3.micro: 750 hours/month (one instance, single-AZ)
#     20 GB storage, 20 GB backup
#
#   Production estimates (eu-west-1):
#     ┌──────────────┬────────────┬──────────────────────┐
#     │ Instance     │ Monthly    │ Notes                │
#     ├──────────────┼────────────┼──────────────────────┤
#     │ db.t3.micro  │ ~$13       │ Dev/test (1 vCPU)    │
#     │ db.t3.medium │ ~$50       │ Small prod (2 vCPU)  │
#     │ db.r6g.large │ ~$160      │ Production (2 vCPU)  │
#     │ + Multi-AZ   │ x2 compute│ Doubles compute cost │
#     │ + Storage    │ $0.115/GB  │ gp3, per month       │
#     │ + Backup     │ Free (up   │ Within retention     │
#     │              │  to DB sz) │  window              │
#     └──────────────┴────────────┴──────────────────────┘
#
#   Example production setup:
#     db.t3.medium Multi-AZ + 50 GB storage
#     = $50 x 2 + 50 x $0.115 = $105.75/month
#
# ── Common Gotchas ──────────────────────────────────────────
#
#   1. Multi-AZ is NOT a read replica. The standby is not
#      queryable. If you need read scaling, create explicit
#      read replicas separately.
#
#   2. Storage can ONLY grow, never shrink. If you allocate
#      100 GB and only use 5 GB, you still pay for 100 GB.
#      Start small with autoscaling enabled.
#
#   3. DB Subnet Group needs subnets in at least 2 AZs.
#      Even single-AZ deployments require this. RDS enforces
#      it for future Multi-AZ capability.
#
#   4. Lambda connection exhaustion: Without RDS Proxy,
#      concurrent Lambda invocations overwhelm the DB
#      connection limit. Always use RDS Proxy with Lambda.
#
#   5. Public access should be NO for production databases.
#      Connect via a bastion host or AWS Session Manager
#      if you need to run queries manually.
#
#   6. Restoring from backup creates a NEW instance.
#      It does not overwrite the existing database.
#      You must update your app's connection string to
#      point to the new instance.
#
#   7. Maintenance windows: AWS applies patches during your
#      configured window. For Multi-AZ, failover happens
#      automatically (brief downtime). For single-AZ,
#      the DB is unavailable during patching.
#
#   8. Encryption: Enable encryption at creation time.
#      You cannot encrypt an existing unencrypted DB.
#      (You can snapshot, copy with encryption, and restore.)
