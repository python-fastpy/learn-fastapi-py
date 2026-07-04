# ══════════════════════════════════════════════════════════════════
# AWS Deployment — IAM (Step 20)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 22-ssm-parameter-store.py

# ╔══════════════════════════════════════════════════╗
# ║  STEP 20: IAM — IDENTITY & ACCESS MANAGEMENT    ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Controls WHO can do WHAT in your AWS account.
#       Every API call to AWS is checked by IAM:
#       "Is this user/service allowed to do this action?"
#
#       Without IAM, anyone with account access could
#       delete databases, read secrets, or spin up expensive
#       resources. IAM is the lock on every door.
#
# REAL REPO: Every AWS service in the skills repo needs IAM
#            permissions. ECS tasks have execution roles to
#            pull images from ECR and read secrets. Lambda
#            functions have roles to write logs and access
#            DynamoDB. The deploy.sh scripts use IAM roles
#            assumed via cloud-tool (human-role/a207920-PowerUser2).
#
# ── The 4 IAM Building Blocks ──────────────────────────────
#
#   ┌──────────────────────────────────────────────────────────┐
#   │                                                          │
#   │  USER              GROUP             ROLE                │
#   │  (person)          (team)            (service/app)       │
#   │                                                          │
#   │  ┌──────────┐     ┌──────────┐     ┌──────────┐        │
#   │  │ Alice    │     │ Devs     │     │ ECS Task │        │
#   │  │ Bob      │     │ Ops      │     │ Lambda   │        │
#   │  │ Charlie  │     │ Admins   │     │ EC2      │        │
#   │  └──────────┘     └──────────┘     └──────────┘        │
#   │       │                │                │                │
#   │       └────────────────┼────────────────┘                │
#   │                        │                                 │
#   │                        ▼                                 │
#   │               ┌──────────────┐                           │
#   │               │   POLICY     │                           │
#   │               │ (permissions)│                           │
#   │               └──────────────┘                           │
#   │                                                          │
#   │  "Alice CAN read S3 buckets"                            │
#   │  "ECS task CAN pull from ECR and read secrets"          │
#   │  "Lambda CAN write to DynamoDB"                         │
#   └──────────────────────────────────────────────────────────┘
#
#   USER:   A person (or machine) with a username + credentials.
#           Has long-term credentials (password + access keys).
#           Best practice: use as few IAM users as possible.
#
#   GROUP:  A collection of users. Attach policies to the group,
#           all members inherit them. Much easier than per-user.
#           e.g., "Developers" group gets ReadOnly + CodeDeploy.
#
#   ROLE:   An identity that AWS SERVICES assume. No password.
#           Temporary credentials that auto-rotate. This is what
#           your ECS tasks, Lambda functions, and EC2 instances use.
#           Also used for cross-account access.
#
#   POLICY: A JSON document listing allowed (or denied) actions.
#           Attached to users, groups, or roles.
#
# ── Policies: The Permission Rules ──────────────────────────
#
#   A policy is a JSON document with this structure:
#
#   {
#     "Version": "2012-10-17",
#     "Statement": [
#       {
#         "Effect": "Allow",           ← Allow or Deny
#         "Action": [                  ← What can they do?
#           "s3:GetObject",
#           "s3:PutObject"
#         ],
#         "Resource": [                ← On which resources?
#           "arn:aws:s3:::book-store-uploads/*"
#         ]
#       }
#     ]
#   }
#
#   Breaking it down:
#     Effect   → "Allow" or "Deny" (Deny always wins)
#     Action   → AWS API actions (service:Action format)
#     Resource → Which specific resources (ARN format)
#
#   Common action patterns:
#     s3:GetObject           → read files from S3
#     s3:PutObject           → upload files to S3
#     s3:*                   → all S3 actions (broad!)
#     dynamodb:GetItem       → read one item from DynamoDB
#     dynamodb:Query         → query items from DynamoDB
#     logs:CreateLogGroup    → create CloudWatch log group
#     logs:PutLogEvents      → write log entries
#     ecr:GetDownloadUrlForLayer → pull Docker images
#     secretsmanager:GetSecretValue → read secrets
#
# ── AWS Managed vs Custom Policies ──────────────────────────
#
#   AWS provides hundreds of pre-built policies:
#
#   ┌────────────────────────────┬────────────────────────────┐
#   │ Managed Policy             │ What it grants             │
#   ├────────────────────────────┼────────────────────────────┤
#   │ AdministratorAccess        │ EVERYTHING (dangerous!)    │
#   │ ReadOnlyAccess             │ Read all services          │
#   │ AmazonS3ReadOnlyAccess     │ Read any S3 bucket         │
#   │ AmazonDynamoDBFullAccess   │ Full DynamoDB access       │
#   │ AmazonECS_FullAccess       │ Full ECS access            │
#   │ CloudWatchLogsFullAccess   │ Full CloudWatch Logs       │
#   │ AmazonSSMReadOnlyAccess    │ Read SSM parameters        │
#   │ SecretsManagerReadWrite    │ Read/write secrets         │
#   │ PowerUserAccess            │ Everything except IAM      │
#   └────────────────────────────┴────────────────────────────┘
#
#   Managed policies are convenient but often too broad.
#   For production, write CUSTOM policies with only the
#   specific actions and resources your service needs.
#
#   Example — custom policy for the book-store ECS task:
#
#   {
#     "Version": "2012-10-17",
#     "Statement": [
#       {
#         "Effect": "Allow",
#         "Action": [
#           "s3:GetObject",
#           "s3:PutObject"
#         ],
#         "Resource": "arn:aws:s3:::book-store-uploads/*"
#       },
#       {
#         "Effect": "Allow",
#         "Action": "dynamodb:Query",
#         "Resource": "arn:aws:dynamodb:eu-west-1:060725138335:
#                      table/book-store-sessions"
#       }
#     ]
#   }
#
# ── Roles: How Services Get Permissions ──────────────────────
#
#   Users log in with a password. Services can't type passwords.
#   Instead, services ASSUME a role. AWS gives them temporary
#   credentials that expire and auto-rotate.
#
#   ┌──────────────────────────────────────────────────────────┐
#   │  ECS Task Definition                                     │
#   │                                                          │
#   │  Two roles needed:                                       │
#   │                                                          │
#   │  1. EXECUTION ROLE (used by ECS itself)                  │
#   │     "ECS, you are allowed to..."                         │
#   │     - Pull images from ECR                               │
#   │     - Read secrets from Secrets Manager                  │
#   │     - Read parameters from SSM                           │
#   │     - Write startup logs to CloudWatch                   │
#   │                                                          │
#   │  2. TASK ROLE (used by YOUR code inside the container)   │
#   │     "Your Python app is allowed to..."                   │
#   │     - Read/write to S3                                   │
#   │     - Query DynamoDB                                     │
#   │     - Publish to SNS                                     │
#   │     - Send messages to SQS                               │
#   │                                                          │
#   │  Think of it like a restaurant:                          │
#   │    Execution role = the building's permission to exist   │
#   │    Task role = the chef's permission to use ingredients  │
#   └──────────────────────────────────────────────────────────┘
#
#   The skills repo ECS tasks use:
#     Execution role → pulls images from ECR, reads secrets
#     Task role → calls Bedrock/OpenAI, writes to CloudWatch,
#                 accesses DynamoDB for sessions
#
# ── Trust Policy: Who Can Assume the Role ────────────────────
#
#   Every role has a TRUST POLICY that says who is allowed
#   to assume it. This is separate from the permissions policy.
#
#   Example: "Only ECS tasks can use this role"
#
#   {
#     "Version": "2012-10-17",
#     "Statement": [
#       {
#         "Effect": "Allow",
#         "Principal": {
#           "Service": "ecs-tasks.amazonaws.com"
#         },
#         "Action": "sts:AssumeRole"
#       }
#     ]
#   }
#
#   Common principals:
#     ecs-tasks.amazonaws.com     → ECS tasks
#     lambda.amazonaws.com        → Lambda functions
#     ec2.amazonaws.com           → EC2 instances
#     codebuild.amazonaws.com     → CodeBuild projects
#     codepipeline.amazonaws.com  → CodePipeline
#
#   Cross-account trust (another AWS account can assume):
#     "Principal": { "AWS": "arn:aws:iam::304853478528:root" }
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   A. CREATE A POLICY
#
#   1. AWS Console → search "IAM" → click it
#      → Left sidebar: Policies → Create policy
#
#   2. Choose JSON editor (easier than the visual editor):
#      ┌──────────────────────────────────────────────────┐
#      │  {                                                │
#      │    "Version": "2012-10-17",                       │
#      │    "Statement": [                                 │
#      │      {                                            │
#      │        "Effect": "Allow",                         │
#      │        "Action": [                                │
#      │          "s3:GetObject",                           │
#      │          "s3:PutObject"                            │
#      │        ],                                         │
#      │        "Resource":                                │
#      │          "arn:aws:s3:::book-store-uploads/*"       │
#      │      }                                            │
#      │    ]                                              │
#      │  }                                                │
#      └──────────────────────────────────────────────────┘
#      → Next → Name: "book-store-s3-access"
#      → Create policy
#
#   B. CREATE A ROLE (for ECS task)
#
#   1. IAM → Roles → Create role
#      ┌──────────────────────────────────────────────────┐
#      │  Trusted entity type:                             │
#      │    AWS service                                    │
#      │                                                    │
#      │  Use case:                                        │
#      │    Elastic Container Service → Elastic Container  │
#      │    Service Task                                    │
#      └──────────────────────────────────────────────────┘
#      → Next
#
#   2. Attach policies:
#      ┌──────────────────────────────────────────────────┐
#      │  Search and select:                               │
#      │    [x] book-store-s3-access (your custom policy) │
#      │    [x] CloudWatchLogsFullAccess (managed)         │
#      └──────────────────────────────────────────────────┘
#      → Next
#
#   3. Name the role:
#      ┌──────────────────────────────────────────────────┐
#      │  Role name: book-store-task-role                   │
#      │  Description: Task role for book-store ECS tasks  │
#      └──────────────────────────────────────────────────┘
#      → Create role
#
#   C. CREATE AN IAM USER (for developer access)
#
#   1. IAM → Users → Create user
#      ┌──────────────────────────────────────────────────┐
#      │  User name: alice-developer                       │
#      │  Access type:                                     │
#      │    [x] AWS Management Console (password)          │
#      │    [x] Programmatic (access key) — optional      │
#      └──────────────────────────────────────────────────┘
#      → Next → Add to group "Developers" → Create user
#
#   NOTE: In enterprise setups (like Thomson Reuters),
#   developers use SSO (Single Sign-On) instead of IAM users.
#   SSO federates from Active Directory / Okta / Sphinx Auth
#   and assigns temporary credentials via IAM roles. The
#   cloud-tool CLI does exactly this — it authenticates via
#   enterprise SSO and writes temporary AWS credentials to
#   ~/.aws/credentials.
#
# ── ARNs: Amazon Resource Names ──────────────────────────────
#
#   Every AWS resource has a unique ARN (address). IAM policies
#   use ARNs to specify which resources a permission applies to.
#
#   Format: arn:aws:<service>:<region>:<account>:<resource>
#
#   Examples:
#     arn:aws:s3:::book-store-uploads           (S3 bucket)
#     arn:aws:s3:::book-store-uploads/*         (all objects in bucket)
#     arn:aws:dynamodb:eu-west-1:060725138335:table/sessions
#     arn:aws:lambda:eu-west-1:060725138335:function:my-func
#     arn:aws:ecs:eu-west-1:060725138335:service/book-store/*
#     arn:aws:secretsmanager:eu-west-1:060725138335:secret:a207920-*
#     arn:aws:iam::060725138335:role/book-store-task-role
#
#   Wildcards:
#     *                    → matches anything
#     arn:aws:s3:::*       → all S3 buckets (too broad!)
#     arn:aws:s3:::book-*  → buckets starting with "book-"
#
#   S3 is special — ARNs have no region or account:
#     arn:aws:s3:::bucket-name     (the bucket itself)
#     arn:aws:s3:::bucket-name/*   (objects inside it)
#     You often need BOTH in a policy.
#
# ── Principle of Least Privilege ─────────────────────────────
#
#   The golden rule of IAM: give the MINIMUM permissions needed.
#
#   BAD (too broad):
#     "Action": "s3:*",
#     "Resource": "*"
#     → Can do anything to any S3 bucket in the account!
#
#   GOOD (specific):
#     "Action": ["s3:GetObject", "s3:PutObject"],
#     "Resource": "arn:aws:s3:::book-store-uploads/*"
#     → Can only read/write objects in one specific bucket.
#
#   Start narrow, add permissions when you get AccessDenied.
#   Never start with AdministratorAccess "just to get it working"
#   — it always stays that way and becomes a security risk.
#
# ── Practical Example: Book Store IAM Setup ──────────────────
#
#   The book-store app needs these roles and policies:
#
#   ┌──────────────────────────────────────────────────────────┐
#   │  ECS Execution Role: book-store-execution-role           │
#   │  ├── ecr:GetDownloadUrlForLayer  (pull Docker images)   │
#   │  ├── ecr:BatchGetImage                                  │
#   │  ├── ecr:GetAuthorizationToken                          │
#   │  ├── secretsmanager:GetSecretValue  (inject secrets)    │
#   │  ├── ssm:GetParameters  (inject config)                 │
#   │  └── logs:CreateLogStream + PutLogEvents  (startup logs)│
#   │                                                          │
#   │  ECS Task Role: book-store-task-role                     │
#   │  ├── s3:GetObject + PutObject  (file uploads)           │
#   │  ├── dynamodb:GetItem + PutItem + Query  (sessions)     │
#   │  ├── sns:Publish  (send notifications)                  │
#   │  └── logs:PutLogEvents  (app logs)                      │
#   │                                                          │
#   │  Lambda Role: book-store-lambda-role                     │
#   │  ├── logs:CreateLogGroup + PutLogEvents                 │
#   │  ├── dynamodb:GetItem + PutItem + Query                 │
#   │  └── s3:GetObject                                       │
#   │                                                          │
#   │  CodeBuild Role: book-store-build-role                   │
#   │  ├── ecr:PutImage + GetAuthorizationToken               │
#   │  ├── s3:PutObject  (build artifacts)                    │
#   │  └── logs:PutLogEvents  (build logs)                    │
#   └──────────────────────────────────────────────────────────┘
#
# ── IAM Access Analyzer ─────────────────────────────────────
#
#   AWS tool that helps you find overly permissive policies.
#
#   IAM → Access Analyzer → Create analyzer
#
#   What it does:
#     - Scans policies for resources shared outside your account
#     - Flags S3 buckets, SQS queues, IAM roles that are
#       publicly accessible or shared with external accounts
#     - Generates least-privilege policies from CloudTrail logs
#       (watches what your service ACTUALLY does, then creates
#        a policy with only those permissions)
#
#   The "generate policy" feature is gold — let your service
#   run for a few days, then ask Access Analyzer to write the
#   tightest possible policy based on real usage.
#
# ── Cost ────────────────────────────────────────────────────
#
#   IAM is completely FREE. No charges for:
#     - Users, groups, roles, policies
#     - API calls (CreateRole, AttachPolicy, etc.)
#     - Access Analyzer
#     - MFA devices (virtual)
#
#   IAM is one of the few AWS services with zero cost.
#   There is never a reason to skip IAM configuration.
#
# ── Common Gotchas ──────────────────────────────────────────
#
#   1. Deny ALWAYS wins over Allow. If any policy says Deny
#      and another says Allow, the result is Deny. This catches
#      people who add an Allow but forget a Deny somewhere else
#      (like an SCP from AWS Organizations).
#
#   2. By default, everything is DENIED. IAM is deny-by-default.
#      You must explicitly Allow each action. No policy attached
#      = no permissions at all.
#
#   3. Execution role vs Task role confusion. If your ECS task
#      can't pull images → check Execution role. If your Python
#      code gets AccessDenied on S3 → check Task role. They are
#      different roles used at different stages.
#
#   4. S3 ARN gotcha: to allow listing a bucket AND reading
#      objects, you need TWO resource entries:
#        "arn:aws:s3:::my-bucket"      → for ListBucket
#        "arn:aws:s3:::my-bucket/*"    → for GetObject/PutObject
#      Missing the /* means GetObject fails silently.
#
#   5. IAM changes take a few seconds to propagate globally.
#      If you attach a policy and immediately test, it might
#      still fail. Wait 10-15 seconds and retry.
#
#   6. Access keys should be rotated every 90 days. Better yet,
#      use roles and temporary credentials everywhere. The skills
#      repo uses cloud-tool which provides temporary credentials
#      via enterprise SSO — no long-lived access keys needed.
#
#   7. Root account: the email you used to create the AWS account
#      has UNRESTRICTED access. Never use root for daily work.
#      Enable MFA on root, lock it away, create IAM users/roles
#      for everything else.
#
#   8. Policy size limit: inline policies max 2,048 characters,
#      managed policies max 6,144 characters. If you hit this,
#      split into multiple policies and attach all of them.
#
#   9. Condition keys let you restrict WHEN a permission applies:
#        "Condition": {
#          "IpAddress": { "aws:SourceIp": "10.0.0.0/16" }
#        }
#      Useful for: IP restrictions, MFA required, time-based
#      access, tag-based access control (ABAC).
