# ══════════════════════════════════════════════════════════════════
# AWS Deployment — SSM Parameter Store (Step 19)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 21-cognito.py  |  next: 23-iam.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 19: SSM PARAMETER STORE                    ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Centralized config storage. Key-value pairs for application
#       configuration, feature flags, and non-sensitive settings.
#       Part of AWS Systems Manager (SSM).
#
# REAL REPO: The skills repo uses environment variables in .env
#            for non-sensitive config (URLs, feature flags, counts).
#            SSM Parameter Store is the AWS-native way to do this.
#            Secrets Manager handles secrets (passwords, API keys).
#            Parameter Store handles config (URLs, flags, limits).
#
# NOTE: This was briefly compared to Secrets Manager in
#       13-secrets-manager.py. This file goes deeper.
#
# ── Parameter Types ─────────────────────────────────────────
#
#   ┌──────────────┬────────────────────────────────────────┐
#   │ Type         │ Description                            │
#   ├──────────────┼────────────────────────────────────────┤
#   │ String       │ Plain text value. Most common.         │
#   │              │ e.g., "https://api.example.com"        │
#   ├──────────────┼────────────────────────────────────────┤
#   │ StringList   │ Comma-separated values.                │
#   │              │ e.g., "us-east-1,eu-west-1,ap-south-1" │
#   │              │ SDK returns as a single string — you   │
#   │              │ split it yourself.                     │
#   ├──────────────┼────────────────────────────────────────┤
#   │ SecureString │ Encrypted with AWS KMS.                │
#   │              │ For sensitive config that doesn't need  │
#   │              │ rotation (use Secrets Manager if it     │
#   │              │ does). Decrypted at read time.          │
#   └──────────────┴────────────────────────────────────────┘
#
# ── Tiers ───────────────────────────────────────────────────
#
#   ┌────────────────────┬───────────────┬──────────────────┐
#   │                    │ Standard      │ Advanced         │
#   ├────────────────────┼───────────────┼──────────────────┤
#   │ Max parameters     │ 10,000        │ 100,000          │
#   │ Max value size     │ 4 KB          │ 8 KB             │
#   │ Parameter policies │ No            │ Yes (expiration, │
#   │                    │               │  notifications)  │
#   │ Cost               │ FREE          │ $0.05/param/mo   │
#   │ API calls          │ FREE          │ FREE             │
#   └────────────────────┴───────────────┴──────────────────┘
#
#   Standard tier is sufficient for most applications.
#   10,000 parameters per account/region is rarely a limit.
#   Advanced only needed for: >10K params, >4KB values,
#   or parameter expiration policies.
#
# ── Hierarchical Naming ─────────────────────────────────────
#
#   Parameters are organized with path-like names using "/":
#
#     /book-store/production/database-url
#     /book-store/production/log-level
#     /book-store/production/max-page-size
#     /book-store/production/feature-new-ui
#     /book-store/staging/database-url
#     /book-store/staging/log-level
#
#   This enables fetching ALL config for an environment
#   in a single call using GetParametersByPath.
#
#   Naming conventions:
#     /<app>/<env>/<key>             (most common)
#     /<team>/<app>/<env>/<key>      (multi-team orgs)
#     /<project-id>/<service>/<key>  (enterprise)
#
#   Real repo equivalents:
#     /leon-skills/production/orchestrator-endpoint
#     /leon-skills/production/mcp-port
#     /leon-skills/production/log-level
#     /leon-skills/production/max-retries
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console -> search "Systems Manager" -> click it
#      -> Left sidebar: Parameter Store
#
#   2. Click "Create parameter"
#      ┌──────────────────────────────────────────────────┐
#      │  Name:  /book-store/production/log-level          │
#      │  Description: Log level for production            │
#      │  Tier:  Standard                                  │
#      │  Type:  String                                    │
#      │  Value: INFO                                      │
#      │                                                    │
#      │  Tags:                                            │
#      │    service: book-store                            │
#      │    environment: production                        │
#      └──────────────────────────────────────────────────┘
#      -> Create parameter
#
#   3. Create more parameters:
#      ┌──────────────────────────────────────────────────┐
#      │  /book-store/production/max-page-size    → 50    │
#      │  /book-store/production/feature-new-ui   → true  │
#      │  /book-store/production/allowed-origins  →       │
#      │    https://books.example.com,http://localhost:3000│
#      │    (StringList type for comma-separated values)  │
#      └──────────────────────────────────────────────────┘
#
#   4. Retrieve by path:
#      Systems Manager -> Parameter Store -> filter by path:
#      /book-store/production/
#      -> Shows all parameters under that path prefix
#
# ── Versioning ──────────────────────────────────────────────
#
#   Every update to a parameter creates a new version.
#   You can retrieve specific versions:
#
#     /book-store/production/log-level
#       Version 1: "DEBUG"     (created 2024-01-01)
#       Version 2: "INFO"      (updated 2024-03-15)
#       Version 3: "WARNING"   (updated 2024-06-01)  <- current
#
#   Default: GetParameter returns the latest version.
#   Specific: get_parameter(Name="/key:2") returns version 2.
#
# ── boto3 Examples ──────────────────────────────────────────
#
#   import boto3
#
#   ssm = boto3.client("ssm", region_name="eu-west-1")
#
#   # Put a parameter
#   ssm.put_parameter(
#       Name="/book-store/production/log-level",
#       Value="INFO",
#       Type="String",
#       Overwrite=True  # Required for updates
#   )
#
#   # Get a single parameter
#   response = ssm.get_parameter(
#       Name="/book-store/production/log-level"
#   )
#   log_level = response["Parameter"]["Value"]  # "INFO"
#
#   # Get a SecureString (with decryption)
#   response = ssm.get_parameter(
#       Name="/book-store/production/db-password",
#       WithDecryption=True  # Required for SecureString
#   )
#
#   # Get ALL parameters by path (one API call)
#   response = ssm.get_parameters_by_path(
#       Path="/book-store/production/",
#       Recursive=True,
#       WithDecryption=True
#   )
#   config = {
#       p["Name"].split("/")[-1]: p["Value"]
#       for p in response["Parameters"]
#   }
#   # {"log-level": "INFO", "max-page-size": "50", ...}
#
#   # IMPORTANT: get_parameters_by_path returns max 10 results!
#   # You MUST paginate using NextToken for more.
#
# ── ECS Task Definition Injection ───────────────────────────
#
#   Just like Secrets Manager, SSM parameters can be injected
#   into ECS containers at startup. Same mechanism, different
#   ARN format.
#
#   Task Definition -> Container -> Environment -> Secrets:
#     Name:      LOG_LEVEL
#     ValueFrom: arn:aws:ssm:eu-west-1:060725138335:
#                parameter/book-store/production/log-level
#
#   In your Python code:
#     import os
#     log_level = os.environ["LOG_LEVEL"]  # "INFO"
#
#   The ECS Execution Role needs SSM permissions:
#     {
#       "Effect": "Allow",
#       "Action": "ssm:GetParameters",
#       "Resource": "arn:aws:ssm:eu-west-1:060725138335:
#                    parameter/book-store/production/*"
#     }
#
# ── Lambda Integration ──────────────────────────────────────
#
#   For Lambda, use the AWS Parameters and Secrets Lambda
#   Extension. It caches parameter values locally — no SDK
#   calls needed on every invocation.
#
#   Add the extension as a Lambda layer:
#     arn:aws:lambda:eu-west-1:015030872274:layer:
#       AWS-Parameters-and-Secrets-Lambda-Extension:11
#
#   The extension runs a local HTTP server on port 2773.
#   Your Lambda reads from localhost (cached, fast) instead
#   of calling the SSM API directly on every invocation.
#   Works for both SSM and Secrets Manager values.
#
# ── CloudFormation / CDK Integration ────────────────────────
#
#   SSM parameters can be referenced in CloudFormation
#   templates using dynamic references:
#
#     Resources:
#       MyBucket:
#         Type: AWS::S3::Bucket
#         Properties:
#           BucketName: !Sub
#             "{{resolve:ssm:/book-store/${Environment}/bucket-name}}"
#
#   In CDK (Python):
#
#     from aws_cdk import aws_ssm as ssm
#
#     log_level = ssm.StringParameter.value_for_string_parameter(
#         self, "/book-store/production/log-level"
#     )
#
#   NOTE: SecureString cannot be resolved by CloudFormation
#   directly. Use dynamic references for SecureString:
#     {{resolve:ssm-secure:/path/to/param}}
#   But this only works in supported resource properties.
#
# ── Parameter Policies (Advanced Tier Only) ─────────────────
#
#   Advanced tier parameters support lifecycle policies:
#
#   Expiration:             Auto-delete after a date.
#   ExpirationNotification: Alert N days before expiration
#                           (sends to EventBridge).
#   NoChangeNotification:   Alert if not updated within N days.
#                           "Config not reviewed in 90 days."
#
# ── Practical Example: Book Store Config ────────────────────
#
#   Parameters for the book-store API:
#
#   ┌────────────────────────────────────┬─────────┬────────┐
#   │ Parameter                          │ Type    │ Value  │
#   ├────────────────────────────────────┼─────────┼────────┤
#   │ /book-store/prod/log-level         │ String  │ INFO   │
#   │ /book-store/prod/max-page-size     │ String  │ 50     │
#   │ /book-store/prod/feature-new-ui    │ String  │ true   │
#   │ /book-store/prod/cors-origins      │ StrList │ https: │
#   │                                    │         │ //...  │
#   │ /book-store/prod/rate-limit-rpm    │ String  │ 100    │
#   │ /book-store/prod/cache-ttl-seconds │ String  │ 300    │
#   └────────────────────────────────────┴─────────┴────────┘
#
#   In FastAPI:
#
#     import boto3
#
#     ssm = boto3.client("ssm")
#
#     def load_config(env: str) -> dict:
#         """Load all config for an environment."""
#         params = ssm.get_parameters_by_path(
#             Path=f"/book-store/{env}/",
#             Recursive=True,
#             WithDecryption=True,
#         )
#         return {
#             p["Name"].split("/")[-1]: p["Value"]
#             for p in params["Parameters"]
#         }
#
#     config = load_config("prod")
#     MAX_PAGE = int(config["max-page-size"])      # 50
#     LOG_LEVEL = config["log-level"]               # "INFO"
#     FEATURE_NEW_UI = config["feature-new-ui"] == "true"
#
# ── SSM Parameter Store vs Secrets Manager vs .env ──────────
#
#   ┌────────────────────┬───────────────┬───────────────┬──────────┐
#   │                    │ SSM Param     │ Secrets Mgr   │ .env     │
#   ├────────────────────┼───────────────┼───────────────┼──────────┤
#   │ Cost               │ FREE (std)    │ $0.40/secret  │ Free     │
#   │ Encryption         │ Optional      │ Always        │ None     │
#   │ Auto rotation      │ No            │ Yes (Lambda)  │ No       │
#   │ Max size           │ 4 KB / 8 KB   │ 64 KB         │ Unlimited│
#   │ Versioning         │ Yes           │ Yes (full)    │ Git only │
#   │ Cross-account      │ No            │ Yes           │ No       │
#   │ ECS injection      │ Yes           │ Yes           │ env_file │
#   │ Audit trail        │ CloudTrail    │ CloudTrail    │ None     │
#   │ Best for           │ Config, flags │ Passwords,    │ Local    │
#   │                    │ URLs, counts  │ API keys      │ dev only │
#   └────────────────────┴───────────────┴───────────────┴──────────┘
#
#   Rule of thumb:
#     Passwords, API keys, tokens     -> Secrets Manager
#     URLs, feature flags, limits     -> SSM Parameter Store
#     Local development only          -> .env files
#
#   The skills repo currently uses:
#     Secrets Manager -> all sensitive values (15+ keys)
#     .env files -> non-sensitive config (URLs, ports, flags)
#     SSM Parameter Store -> could replace .env for AWS-hosted config
#
# ── Cost ────────────────────────────────────────────────────
#
#   Standard tier:
#     Parameters:  FREE (up to 10,000 per account/region)
#     API calls:   FREE (GetParameter, PutParameter, etc.)
#     SecureString: FREE (uses default aws/ssm KMS key)
#
#   Advanced tier:
#     $0.05 per advanced parameter per month
#     API calls: still free
#
#   Example:
#     50 Standard parameters = $0/month
#     50 Standard parameters + 5 Advanced = $0.25/month
#
#   This makes Parameter Store the cheapest config management
#   service on AWS. Compared to Secrets Manager ($0.40/secret/mo),
#   it is essentially free for non-sensitive configuration.
#
# ── Common Gotchas ──────────────────────────────────────────
#
#   1. Standard tier limit: 10,000 parameters per account
#      per region. Sounds like a lot, but large organizations
#      with many services can hit this. Monitor usage via
#      CloudWatch metric: SSM.ParameterStoreUsageCount.
#
#   2. GetParametersByPath returns MAX 10 results per call.
#      You MUST paginate using NextToken. Without pagination,
#      you silently lose parameters. This is the most common
#      bug when using Parameter Store.
#
#   3. SecureString cannot be decrypted by CloudFormation
#      for all resource types. Use the dynamic reference
#      syntax {{resolve:ssm-secure:/path}} and check the
#      CloudFormation docs for which resources support it.
#
#   4. Parameter names cannot be reused for 30 seconds after
#      deletion. If you delete /my/param and immediately
#      recreate it, you get ParameterAlreadyExists. Wait
#      30 seconds or use a different name.
#
#   5. All parameter values are strings. There is no native
#      integer, boolean, or JSON type. You must parse/convert
#      in your application code:
#        max_page = int(param_value)        # "50" -> 50
#        enabled = param_value == "true"    # "true" -> True
#
#   6. Parameter Store has lower API throughput than Secrets
#      Manager. Default: 40 GetParameter TPS (transactions
#      per second). Request an increase for high-traffic apps.
#      Use caching (Lambda Extension or app-level cache) to
#      stay well under this limit.
#
#   7. No built-in change notifications. To react to parameter
#      changes, set up a CloudWatch Events rule on the SSM
#      PutParameter API call via CloudTrail. Secrets Manager
#      has built-in rotation events; Parameter Store does not.
