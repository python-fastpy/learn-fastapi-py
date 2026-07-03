# ══════════════════════════════════════════════════════════════════
# AWS Deployment — CodeDeploy & Pipeline (Step 16)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 18-waf.py  |  next: 20-rds.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 16: CODEDEPLOY & PIPELINE                  ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: CI/CD on AWS. CodeBuild compiles/tests, CodePipeline
#       orchestrates stages, CodeDeploy pushes to ECS/EC2/Lambda.
#
# REAL REPO: The skills repo uses CI/CD pipelines defined in
#            sphinx_leon-assistant-skills/cicd/. Deployments go
#            through dev -> qa -> uat -> prod with approval gates.
#            Each skill has a deploy.sh script and Dockerfile.
#            Docker images are pushed to ECR, then ECS services
#            are updated via rolling deployments.
#
# ── The 3 Code* Services ───────────────────────────────────────
#
#   These three services work together to form a complete CI/CD
#   pipeline on AWS:
#
#   ┌──────────────────────────────────────────────────────────┐
#   │                    CodePipeline                           │
#   │              (orchestrator / conveyor belt)               │
#   │                                                          │
#   │  ┌─────────┐    ┌──────────┐    ┌───────────┐           │
#   │  │ Source   │───>│  Build   │───>│  Deploy   │           │
#   │  │ Stage   │    │  Stage   │    │  Stage    │           │
#   │  └─────────┘    └──────────┘    └───────────┘           │
#   │       │               │               │                  │
#   │   GitHub/         CodeBuild       CodeDeploy             │
#   │   CodeCommit    (compile/test/   (push to ECS/           │
#   │   S3 zip         Docker build)    EC2/Lambda)            │
#   └──────────────────────────────────────────────────────────┘
#
#   CodeBuild:    Compiles code, runs tests, builds Docker images.
#                 Think of it as a managed Jenkins build agent.
#
#   CodePipeline: Orchestrates the stages. Watches for source
#                 changes, triggers builds, gates deployments.
#                 Think of it as a conveyor belt.
#
#   CodeDeploy:   Pushes code to compute targets. Handles rolling,
#                 blue/green, and canary deployment strategies.
#                 Think of it as the delivery truck.
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   A. CREATE CODEBUILD PROJECT
#
#   1. AWS Console -> search "CodeBuild" -> click it
#
#   2. Click "Create build project"
#      ┌──────────────────────────────────────────────────┐
#      │  Project name: book-store-build                   │
#      │                                                    │
#      │  Source:                                           │
#      │    Provider:   GitHub (connect via OAuth)          │
#      │    Repository: your-org/book-store-api             │
#      │    Branch:     main                                │
#      │                                                    │
#      │  Environment:                                     │
#      │    Image:       aws/codebuild/amazonlinux2-x86_64 │
#      │    Runtime:     Standard 7.0                       │
#      │    Compute:     3 GB / 2 vCPU (general1.small)    │
#      │    Privileged:  YES  (needed for Docker builds!)  │
#      │    Service role: Create new role                   │
#      │                                                    │
#      │  Buildspec:                                       │
#      │    Use a buildspec file (in source root)          │
#      │    Buildspec name: buildspec.yml                   │
#      │                                                    │
#      │  Artifacts: No artifacts (pushing to ECR instead)  │
#      │                                                    │
#      │  Logs: CloudWatch (/aws/codebuild/book-store)     │
#      └──────────────────────────────────────────────────┘
#      -> Create build project
#
#   B. CREATE CODEPIPELINE
#
#   1. AWS Console -> search "CodePipeline" -> click it
#
#   2. Click "Create pipeline"
#      ┌──────────────────────────────────────────────────┐
#      │  Pipeline name: book-store-pipeline               │
#      │  Service role:  New service role                   │
#      │                                                    │
#      │  Source stage:                                     │
#      │    Provider:      GitHub (Version 2)              │
#      │    Connection:    Create or select connection      │
#      │    Repository:    your-org/book-store-api          │
#      │    Branch:        main                             │
#      │    Trigger:       On push                          │
#      │                                                    │
#      │  Build stage:                                     │
#      │    Provider:      AWS CodeBuild                    │
#      │    Project:       book-store-build                 │
#      │                                                    │
#      │  Deploy stage:                                    │
#      │    Provider:      Amazon ECS                       │
#      │    Cluster:       book-store-cluster               │
#      │    Service:       book-store-service               │
#      │    Image file:    imagedefinitions.json            │
#      └──────────────────────────────────────────────────┘
#      -> Create pipeline
#
#   C. ADD MANUAL APPROVAL (for production)
#
#   1. Edit pipeline -> Add stage between Build and Deploy
#      ┌──────────────────────────────────────────────────┐
#      │  Stage name: Approval                             │
#      │  Action:     Manual approval                      │
#      │  SNS topic:  book-store-deploy-approval           │
#      │    (optional — sends email for approval)          │
#      │  Comments:   "Approve deployment to production?"  │
#      └──────────────────────────────────────────────────┘
#
#   The skills repo uses approval gates before uat and prod:
#     dev (auto) -> qa (auto) -> uat (approval) -> prod (approval)
#
# ── CodeBuild: buildspec.yml ────────────────────────────────
#
#   The buildspec.yml file tells CodeBuild what to do.
#   It lives in your repository root.
#
#   Structure:
#
#     version: 0.2
#     phases:
#       install:
#         runtime-versions:
#           python: 3.11
#         commands:
#           - pip install -r requirements.txt
#
#       pre_build:
#         commands:
#           - echo "Logging in to ECR..."
#           - aws ecr get-login-password --region $AWS_REGION |
#             docker login --username AWS --password-stdin
#             $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
#           - IMAGE_URI=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.
#             amazonaws.com/book-store-api
#           - COMMIT_HASH=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION
#             | cut -c 1-7)
#           - IMAGE_TAG=${COMMIT_HASH:=latest}
#
#       build:
#         commands:
#           - echo "Running tests..."
#           - pytest tests/
#           - echo "Building Docker image..."
#           - docker build -t $IMAGE_URI:$IMAGE_TAG .
#           - docker tag $IMAGE_URI:$IMAGE_TAG $IMAGE_URI:latest
#
#       post_build:
#         commands:
#           - echo "Pushing to ECR..."
#           - docker push $IMAGE_URI:$IMAGE_TAG
#           - docker push $IMAGE_URI:latest
#           - echo "Writing image definitions..."
#           - printf '[{"name":"book-store-container",
#             "imageUri":"%s"}]' $IMAGE_URI:$IMAGE_TAG
#             > imagedefinitions.json
#
#     artifacts:
#       files:
#         - imagedefinitions.json
#
#   Build phases explained:
#     install:    Install dependencies, runtime setup
#     pre_build:  Login to registries, set variables
#     build:      Run tests, build Docker image
#     post_build: Push image, generate deployment artifacts
#
#   The imagedefinitions.json tells ECS which container image to use.
#   CodePipeline passes this artifact to the Deploy stage.
#
#   Environment variables available in CodeBuild:
#     AWS_REGION                           (from project config)
#     AWS_ACCOUNT_ID                       (from project config)
#     CODEBUILD_RESOLVED_SOURCE_VERSION    (git commit SHA)
#     CODEBUILD_BUILD_NUMBER               (incrementing build #)
#     CODEBUILD_SOURCE_REPO_URL            (source repository URL)
#
# ── CodeDeploy: Deployment Strategies ───────────────────────
#
#   CodeDeploy supports four strategies. Choose based on risk
#   tolerance and downtime requirements:
#
#   ┌──────────────────┬──────────┬──────────┬───────────────┐
#   │ Strategy         │ Downtime │ Rollback │ Best For      │
#   ├──────────────────┼──────────┼──────────┼───────────────┤
#   │ All-at-once      │ Brief    │ Redeploy │ Dev/test      │
#   │ Rolling          │ None     │ Redeploy │ ECS default   │
#   │ Blue/Green       │ None     │ Instant  │ Production    │
#   │ Canary           │ None     │ Instant  │ High-risk     │
#   └──────────────────┴──────────┴──────────┴───────────────┘
#
#   All-at-once:
#     Replace everything simultaneously. Fast but risky.
#     If something breaks, all traffic is affected.
#
#   Rolling (ECS default):
#     Replace tasks one at a time. Old tasks keep serving
#     until new tasks pass health checks.
#     [v1] [v1] -> [v1] [v2] -> [v2] [v2]
#
#   Blue/Green:
#     Deploy entirely new set (green). Run both in parallel.
#     Switch ALB traffic from blue (old) to green (new).
#     Keep blue around for instant rollback.
#
#     ┌──────────────────────────────────────────────────┐
#     │  ALB                                              │
#     │  ├── Target Group BLUE  (v1) <-- 100% traffic    │
#     │  └── Target Group GREEN (v2) <-- 0% traffic      │
#     │                                                    │
#     │  After health checks pass:                         │
#     │  ├── Target Group BLUE  (v1) <-- 0% traffic       │
#     │  └── Target Group GREEN (v2) <-- 100% traffic     │
#     │                                                    │
#     │  Rollback? Flip traffic back to BLUE instantly.   │
#     └──────────────────────────────────────────────────┘
#
#     Requires TWO target groups pre-configured on the ALB.
#
#   Canary:
#     Route a small percentage to new version first.
#     Monitor for errors. If OK, shift all traffic.
#     Example: 10% for 10 minutes, then 100%.
#
#     ┌──────────────────────────────────────────────────┐
#     │  Phase 1:  90% -> v1,  10% -> v2  (10 min)      │
#     │  Phase 2: (if no errors) 0% -> v1, 100% -> v2   │
#     │  Rollback: (if errors)  100% -> v1, 0% -> v2    │
#     └──────────────────────────────────────────────────┘
#
# ── ECS Blue/Green with CodeDeploy ──────────────────────────
#
#   For ECS blue/green deployments, CodeDeploy uses an
#   appspec.yml file:
#
#     version: 0.0
#     Resources:
#       - TargetService:
#           Type: AWS::ECS::Service
#           Properties:
#             TaskDefinition: <TASK_DEFINITION>
#             LoadBalancerInfo:
#               ContainerName: "book-store-container"
#               ContainerPort: 8000
#
#   The <TASK_DEFINITION> placeholder is replaced by CodeDeploy
#   with the new task definition ARN during deployment.
#
#   Required setup for ECS blue/green:
#     1. Two target groups on the ALB (blue + green)
#     2. Production listener (port 443) on the ALB
#     3. Test listener (port 8443) for pre-traffic validation
#     4. CodeDeploy application + deployment group for ECS
#
# ── Practical Example: Book Store Pipeline ──────────────────
#
#   Complete flow: developer pushes code to production.
#
#     Developer pushes to main branch
#            │
#            ▼
#     ┌─────────────────┐
#     │  SOURCE STAGE   │  CodePipeline detects push
#     │  (GitHub)       │  Downloads source code
#     └────────┬────────┘
#              │
#              ▼
#     ┌─────────────────┐
#     │  BUILD STAGE    │  CodeBuild runs buildspec.yml:
#     │  (CodeBuild)    │  1. pip install + pytest
#     │                 │  2. docker build
#     │                 │  3. docker push to ECR
#     │                 │  4. Output imagedefinitions.json
#     └────────┬────────┘
#              │
#              ▼
#     ┌─────────────────┐
#     │  APPROVAL       │  Email sent to team lead
#     │  (Manual)       │  "Approve deploy to prod?"
#     └────────┬────────┘
#              │ (approved)
#              ▼
#     ┌─────────────────┐
#     │  DEPLOY STAGE   │  ECS reads imagedefinitions.json
#     │  (ECS)          │  Creates new task definition
#     │                 │  Rolling update: new tasks start,
#     │                 │  old tasks drain and stop
#     └─────────────────┘
#
#   The skills repo follows a similar pattern:
#     deploy.sh builds Docker -> pushes to ECR -> updates
#     ECS service -> ECS performs rolling deployment.
#     Versioning: v0.1.5-a7f3b2c (semver + git SHA).
#
# ── Cost ────────────────────────────────────────────────────
#
#   CodeBuild:
#     $0.005/build-minute (general1.small — 3GB, 2 vCPU)
#     $0.01/build-minute  (general1.medium — 7GB, 4 vCPU)
#     100 free build-minutes/month (first 12 months)
#
#     Example: 20 builds/day x 5 min each = 100 min/day
#     100 min x 30 days x $0.005 = $15/month
#
#   CodePipeline:
#     $1.00/month per active pipeline (free tier: 1 pipeline)
#     A pipeline is "active" if it has at least one execution
#     that month.
#
#   CodeDeploy:
#     FREE for ECS and Lambda deployments
#     $0.02/on-premises instance deployment
#
#   Total for a small team:
#     1 pipeline ($1) + 100 build-min/day ($15) = ~$16/month
#
# ── Common Gotchas ──────────────────────────────────────────
#
#   1. buildspec.yml must be in the repo root by default.
#      You can configure a different path in the CodeBuild
#      project, but most teams keep it at the root.
#
#   2. CodeBuild timeout defaults to 60 minutes. Docker
#      builds with large base images can exceed this.
#      Set a higher timeout in project settings if needed.
#
#   3. "Privileged" mode must be enabled for Docker builds.
#      Without it, "docker build" fails with permission errors.
#
#   4. Blue/green needs TWO target groups pre-configured
#      on the ALB before you create the CodeDeploy deployment
#      group. Forgetting this causes deployment creation to fail.
#
#   5. imagedefinitions.json format is specific:
#      [{"name":"container-name","imageUri":"image:tag"}]
#      The "name" must match the container name in your
#      ECS task definition exactly.
#
#   6. CodePipeline source connections (GitHub v2) require
#      an AWS CodeStar connection. The first time you set it
#      up, you must authorize via the GitHub OAuth flow in
#      the browser. This cannot be done via CLI alone.
#
#   7. Build cache: Enable S3 caching in CodeBuild to speed
#      up builds. Without it, every build re-downloads all
#      dependencies from scratch.
