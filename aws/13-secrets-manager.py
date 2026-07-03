# ══════════════════════════════════════════════════════════════════
# AWS Deployment — Secrets Manager (Step 11)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 12-cloudfront-deep-dive.py  |  next: 14-cleanup-and-summary.py →

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
#
# ── Secrets Manager Key Concepts ────────────────────────────
#
#   ── Secret Structure ───────────────────────────────────────
#
#   A secret is a named container holding sensitive data.
#   It can store a JSON object (multiple key-value pairs)
#   or a plain string.
#
#   JSON format (most common — store multiple values):
#     Secret name: "book-store/production"
#     Secret value:
#       {
#         "DATABASE_URL": "postgresql://user:pass@host:5432/books",
#         "API_KEY": "sk-abc123",
#         "JWT_SECRET": "super-secret-key",
#         "REDIS_URL": "redis://cache.internal:6379"
#       }
#
#   Real example from the skills repo:
#     Secret name: "a207920-leon-skills"
#     Contains 15+ keys:
#       LEON_ORCHESTRATOR_API_KEY, LEON_ORCHESTRATOR_TENANT_ID,
#       SPHINX_AUTH_API_KEY, SPHINX_AUTH_PASSWORD, LSEG_API_KEY,
#       SEMANTIC_SEARCH_CLIENT_SECRET, AUTH_X_API_KEY, etc.
#
#   Naming conventions:
#     <project-id>/<service>/<env>  → a209485/assistant-backend/credentials
#     <project-id>-<service>        → a207920-leon-skills
#     <service>/<env>               → book-store/production
#
#   ── Retrieving Secrets ─────────────────────────────────────
#
#   Three ways to get secrets into your app:
#
#   1. ECS Container Injection (recommended for ECS):
#      Secrets are injected as environment variables at container start.
#      Your code reads them like normal env vars — no SDK needed.
#
#      Task Definition → Container → Environment → Secrets:
#        Name:      DATABASE_URL
#        ValueFrom: arn:aws:secretsmanager:eu-west-1:060725138335:
#                   secret:a207920-leon-skills:DATABASE_URL::
#
#      Format: arn:...:secret:<secret-name>:<json-key>::
#      The :: at the end means "latest version, no staging label"
#
#      In your Python code:
#        import os
#        db_url = os.environ["DATABASE_URL"]
#        # Already there — ECS injected it at startup
#
#      This is what the skills repo does. The CDK stack maps
#      each secret key to an environment variable.
#
#   2. Boto3 SDK (for Lambda or dynamic access):
#      Fetch secrets at runtime via API call.
#
#      import boto3, json
#
#      def get_secrets():
#          client = boto3.client("secretsmanager", region_name="eu-west-1")
#          response = client.get_secret_value(SecretId="book-store/production")
#          return json.loads(response["SecretString"])
#
#      secrets = get_secrets()
#      db_url = secrets["DATABASE_URL"]
#
#      IMPORTANT: Cache the result! Don't call GetSecretValue on every
#      request — it's slow (~50ms) and has rate limits (10,000/sec).
#      Lambda: load in module scope (runs once per cold start).
#      ECS: load once at startup, store in a global variable.
#
#   3. Docker Entrypoint Script (used by the backend repo):
#      The docker-entrypoint.sh script fetches secrets from AWS
#      and exports them as environment variables before starting the app.
#
#      # docker-entrypoint.sh
#      SECRET_JSON=$(aws secretsmanager get-secret-value \
#        --secret-id "a209485/assistant-backend/credentials" \
#        --query SecretString --output text)
#      export TR_API_KEY=$(echo $SECRET_JSON | jq -r '.TR_API_KEY')
#      export TR_CLIENT_SECRET=$(echo $SECRET_JSON | jq -r '.TR_CLIENT_SECRET')
#      exec uvicorn main:app --host 0.0.0.0 --port 8000
#
#   ── Versions & Staging Labels ──────────────────────────────
#
#   Every update to a secret creates a new VERSION (identified by UUID).
#   Staging labels mark which version is "current":
#
#     AWSCURRENT  → the active version (this is what GetSecretValue returns)
#     AWSPREVIOUS → the version before the current one (rollback target)
#     AWSPENDING  → the version being rotated into place
#
#   When you update a secret:
#     Old value gets label: AWSPREVIOUS
#     New value gets label: AWSCURRENT
#     You can fetch the old value: get_secret_value(VersionStage="AWSPREVIOUS")
#
#   ── Automatic Rotation ─────────────────────────────────────
#
#   Secrets Manager can automatically rotate secrets on a schedule.
#   A Lambda function generates the new value and updates the secret.
#
#   Common rotation targets:
#     RDS database passwords → built-in Lambda templates
#     API keys → custom Lambda that calls the API to regenerate
#     OAuth client secrets → custom Lambda
#
#   Rotation flow:
#     1. Schedule triggers (e.g., every 30 days)
#     2. createSecret  → Lambda generates new password, stores as AWSPENDING
#     3. setSecret     → Lambda updates the database with new password
#     4. testSecret    → Lambda tests connection with new password
#     5. finishSecret  → AWSPENDING becomes AWSCURRENT
#
#   Setup: Secrets Manager → secret → Rotation → Edit rotation
#     → Enable rotation
#     → Rotation interval: 30 days
#     → Lambda function: create new or select existing
#
#   For RDS, AWS provides pre-built rotation Lambda templates.
#   For custom secrets, you write the rotation Lambda yourself.
#
#   ── IAM Permissions ────────────────────────────────────────
#
#   Who can read which secrets is controlled by IAM policies.
#   Principle of least privilege: each service reads ONLY its secrets.
#
#   ECS Task Role policy (allows reading one specific secret):
#     {
#       "Effect": "Allow",
#       "Action": "secretsmanager:GetSecretValue",
#       "Resource": "arn:aws:secretsmanager:eu-west-1:060725138335:
#                    secret:a207920-leon-skills-*"
#     }
#
#   Note the wildcard (*) at the end — Secrets Manager appends a
#   random 6-character suffix to the ARN. Without the wildcard,
#   the policy won't match.
#
#   The ECS Execution Role also needs permission if you use
#   "secrets" in the task definition (to inject at container start).
#
#   ── Secrets Manager vs SSM Parameter Store ─────────────────
#
#   Both store configuration. Different features and pricing:
#
#     ┌──────────────────────┬───────────────────┬────────────────┐
#     │                      │ Secrets Manager   │ SSM Param Store│
#     ├──────────────────────┼───────────────────┼────────────────┤
#     │ Automatic rotation   │ ✅ Built-in       │ ❌ No          │
#     │ Cross-account share  │ ✅ Resource policy │ ❌ No          │
#     │ Versioning           │ ✅ Full history   │ ✅ (limited)   │
#     │ ECS injection        │ ✅ Direct         │ ✅ Direct      │
#     │ Max value size       │ 64 KB             │ 8 KB (adv: 8KB)│
#     │ Cost per secret/mo   │ $0.40             │ Free (standard)│
#     │ Cost per API call    │ $0.05/10K calls   │ Free (standard)│
#     │ Encryption           │ Always encrypted  │ Optional       │
#     │ Best for             │ Passwords, API keys│ Config values │
#     │                      │ DB credentials     │ Feature flags │
#     └──────────────────────┴───────────────────┴────────────────┘
#
#   Rule of thumb:
#     Secrets (passwords, API keys, tokens) → Secrets Manager
#     Configuration (URLs, feature flags, counts) → SSM Parameter Store
#     The skills repo uses Secrets Manager for all sensitive values
#     and environment variables in .env for non-sensitive config.
#
#   ── Cost ───────────────────────────────────────────────────
#
#   Per secret:    $0.40/month
#   Per API call:  $0.05 per 10,000 calls
#
#   Example:
#     3 secrets (skills, backend, database) × $0.40 = $1.20/month
#     100 ECS tasks starting/day × 30 days × 3 calls = 9,000 calls
#     9,000 calls = ~$0.045/month
#     Total: ~$1.25/month (very cheap)
#
#   Cost tip: Store MULTIPLE values in ONE secret (JSON format).
#   One secret with 15 keys costs $0.40/month.
#   15 separate secrets would cost $6.00/month.
#   That's why the skills repo stores all keys in one secret.
#
#   ── Common Gotchas ─────────────────────────────────────────
#
#   1. Deleted secrets are recoverable for 7-30 days (you choose).
#      Use recovery window = 0 only for test secrets.
#      Default: 30-day recovery window.
#
#   2. Secret ARN has a random suffix. Your IAM policy MUST use
#      a wildcard: secret:my-secret-* (not secret:my-secret).
#
#   3. ECS tasks DON'T automatically pick up secret changes.
#      You must redeploy the service (or force new deployment)
#      to get updated secret values.
#      aws ecs update-service --force-new-deployment
#
#   4. Lambda caches secrets in warm containers. If you rotate
#      a secret, warm Lambdas still have the OLD value until
#      they cold-start again. Add TTL-based cache invalidation.
#
#   5. Don't put secrets in CloudFormation/CDK outputs or logs.
#      Use dynamic references: {{resolve:secretsmanager:my-secret:SecretString:key}}
