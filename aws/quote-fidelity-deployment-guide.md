# Quote Fidelity MCP Server — Full Deployment Guide

## Architecture

Quote-fidelity is a standalone FastMCP skill server that wraps the shared quote fidelity engine.
Other skills (e.g. story-drafting) call it via MCP-to-MCP using `QUOTE_FIDELITY_MCP_URL`.

```
story-drafting (ECS) --MCP--> quote-fidelity (ECS) ---> shared quote fidelity engine
                                    |
                              Shared ALB (path: /quote-fidelity/*)
                                    |
                              Target Group (port 8000)
```

**Repo:** `tr/sphinx_leon-assistant-skills`
**Skill dir:** `quote-fidelity/`
**PR:** https://github.com/tr/sphinx_leon-assistant-skills/pull/511

---

## Environments

| Env | ALB Stack Name | DNS Hostname | Deployed URL |
|-----|---------------|--------------|--------------|
| dev | `a207920-leon-skills-shared-alb-ci` | `skills.leon-ci` | `https://skills.leon-ci.8335.aws-int.thomsonreuters.com/quote-fidelity/mcp` |
| QA  | `a207920-leon-skills-shared-alb-test` | `skills.leon-test` | `https://skills.leon-test.8335.aws-int.thomsonreuters.com/quote-fidelity/mcp` |

**AWS Account:** `060725138335` (tr-central-preprod), Region: `eu-west-1`

---

## Step 1: Deploy ALB CloudFormation Stack

This creates the target group and listener rule on the shared ALB.
**Do this for each environment (dev first, then QA).**

### Via AWS Console

1. Go to **AWS Console** → CloudFormation → Stacks (region: `eu-west-1`, account: `060725138335`)
2. **For dev**: select stack `a207920-leon-skills-shared-alb-ci`
   **For QA**: select stack `a207920-leon-skills-shared-alb-test`
3. Click **Update**
4. Select **"Replace current template"** → **Upload a template file**
5. Upload `sphinx_leon-assistant-skills/cloudformation/templates/a207920_leon_skills_shared_alb.yaml`
6. Click **Next** — keep all existing parameter values unchanged
7. Click **Next** through tags/options
8. Review changeset — you should see 3 new resources:
   - `QuoteFidelityTargetGroup` — Add
   - `QuoteFidelityListenerRule` — Add
   - `QuoteFidelityTargetGroupArn` — Add
9. Check "I acknowledge..." if prompted → **Submit**
10. Wait for **UPDATE_COMPLETE**

### Via CLI

```bash
aws cloudformation deploy \
  --template-file sphinx_leon-assistant-skills/cloudformation/templates/a207920_leon_skills_shared_alb.yaml \
  --stack-name a207920-leon-skills-shared-alb-test \
  --parameter-overrides EnvironmentName=test \
  --profile tr-central-preprod \
  --region eu-west-1 \
  --no-fail-on-empty-changeset
```

### Verify

- **EC2 → Target Groups** → search `quotefidelity` — exists with 0 targets
- **CloudFormation → Exports** → search `tg-quote-fidelity` — export visible
- **CloudFormation → Stack → Events tab** → all 3 resources show `CREATE_COMPLETE`

---

## Step 2: Deploy CI/CD CDK Stack (Create CodePipeline)

The CodePipeline doesn't exist until the cicd CDK stack is deployed.

```bash
cd sphinx_leon-assistant-skills/cicd

# Install CDK dependencies (if not already)
pip install -r requirements.txt

# Bootstrap CDK (only needed once per account/region, skip if already done)
cdk bootstrap aws://060725138335/eu-west-1 --profile tr-central-preprod

# Deploy all pipelines (creates quote-fidelity-dev and quote-fidelity-qa)
cdk deploy --all --profile tr-central-preprod --region eu-west-1
```

Confirm with `y` when prompted.

### What gets created

- `quote-fidelity-dev` pipeline — triggers on `develop` branch
- `quote-fidelity-qa` pipeline — triggers on `qa` branch

### Verify

- **AWS Console → CodePipeline** → search `quote-fidelity`
- You should see both `quote-fidelity-dev` and `quote-fidelity-qa`

---

## Step 3: Create ECR Repositories

The pipeline pushes Docker images to ECR. The repos must exist first.

### Via Console

1. Go to **AWS Console → ECR** (region: `eu-west-1`, account: `060725138335`)
2. Create repository: `a207920/quote-fidelity-skill/dev`
3. Create repository: `a207920/quote-fidelity-skill/qa`
4. Image tag mutability: **Mutable**

### Via CLI

```bash
aws ecr create-repository \
  --repository-name "a207920/quote-fidelity-skill/dev" \
  --profile tr-central-preprod \
  --region eu-west-1

aws ecr create-repository \
  --repository-name "a207920/quote-fidelity-skill/qa" \
  --profile tr-central-preprod \
  --region eu-west-1
```

---

## Step 4: Merge PR to `develop`

1. Go to PR #511: https://github.com/tr/sphinx_leon-assistant-skills/pull/511
2. Merge into `develop`
3. This triggers `quote-fidelity-dev` CodePipeline automatically
4. Monitor: **CodePipeline → quote-fidelity-dev** → watch stages (Source → Build → Deploy)

### Verify

- **ECS → Clusters** → find quote-fidelity cluster → service running, task count = 1
- **EC2 → Target Groups** → `quotefidelity` TG → Targets tab → 1 target, status **healthy**
- Test health endpoint:
  ```bash
  curl https://skills.leon-ci.8335.aws-int.thomsonreuters.com/quote-fidelity/health
  # Expected: {"status": "healthy", "server_name": "quote-fidelity"}
  ```

---

## Step 5: Add Security Group Inbound Rule

The ALB needs to reach ECS containers on port 8000. Without this, health checks fail.

1. Go to **AWS Console → EC2 → Security Groups**
2. Find the **ALB security group** — get ID from CloudFormation stack outputs: `SharedAlbSecurityGroupId`
3. Find the **quote-fidelity ECS service security group** — go to ECS → cluster → service → Networking tab → note the SG ID
4. Edit the **ECS service SG** → Inbound rules → Add rule:
   - **Type:** Custom TCP
   - **Port:** 8000
   - **Source:** ALB security group ID
   - **Description:** Allow ALB health checks and traffic
5. Save

### Verify

- Target group targets go from `unhealthy` → `healthy` within ~30 seconds

---

## Step 6: Promote to QA

1. Merge `develop` → `qa` branch (or create a promotion PR)
2. `quote-fidelity-qa` pipeline triggers automatically
3. QA URL: `https://skills.leon-test.8335.aws-int.thomsonreuters.com/quote-fidelity/mcp`

---

## Follow-up: Wire story-drafting to call quote-fidelity

After quote-fidelity is deployed and healthy, add `QUOTE_FIDELITY_MCP_URL` to story-drafting's environment.

| Env | Value |
|-----|-------|
| dev | `https://skills.leon-ci.8335.aws-int.thomsonreuters.com/quote-fidelity/mcp` |
| QA  | `https://skills.leon-test.8335.aws-int.thomsonreuters.com/quote-fidelity/mcp` |

Options:
- Add to AWS Secrets Manager secret `a207920-leon-skills`
- Or add to story-drafting's CDK task definition in `story-drafting/infra/config.py`

---

## Key Files

| Purpose | Path |
|---------|------|
| MCP server entry | `quote-fidelity/src/main.py` |
| Tool implementation | `quote-fidelity/src/tools/check_quote_fidelity.py` |
| CDK infra stack | `quote-fidelity/infra/mcp_stack.py` |
| CDK config (env) | `quote-fidelity/infra/config.py` |
| Deploy script | `quote-fidelity/infra/deploy.sh` |
| CI/CD registry | `cicd/config/skills_registry.py` |
| Shared ALB template | `cloudformation/templates/a207920_leon_skills_shared_alb.yaml` |
| Shared quote engine | `shared/src/shared/quote_fidelity/matcher.py` |
| Story-drafting caller | `story-drafting/src/tools/generate_spot_story.py` (line 248) |

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| CDK deploy fails with "Export not found" | ALB stack not updated yet | Deploy ALB CloudFormation stack first (Step 1) |
| Pipeline not triggering on merge | Pipeline doesn't exist | Deploy cicd CDK stack (Step 2) |
| Docker push fails | ECR repo doesn't exist | Create ECR repos (Step 3) |
| Target group shows `unhealthy` | SG rule missing | Add port 8000 inbound rule from ALB SG (Step 5) |
| `QUOTE_FIDELITY_MCP_URL` not set | Not yet wired | Add env var to story-drafting (Follow-up) |
| Health check returns 503 | ECS task not running | Check ECS service events for errors |

---

## Local Development

```bash
cd sphinx_leon-assistant-skills/quote-fidelity

# Install deps
uv sync

# Create .env
cp .env.example .env

# Run locally
uv run python run.py
# Server at http://localhost:8008/mcp, health at http://localhost:8008/health

# To have story-drafting call it locally, add to story-drafting/.env:
# QUOTE_FIDELITY_MCP_URL=http://localhost:8008/mcp
```
