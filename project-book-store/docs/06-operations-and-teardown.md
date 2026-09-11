# 06 — Operations & Teardown

`Navigation: ← prev: 05-deploy-fargate.md`

A deploy isn't finished when it returns 200 once. This covers knowing
when it breaks, how to roll back, what it costs, and — importantly —
how to delete it all.

**If you only read one section, read [Teardown](#teardown--do-this-when-youre-done).**

---

## 1. Logs

```bash
# Lambda path
aws logs tail /aws/lambda/book-store-api-dev --follow

# Fargate path
aws logs tail /ecs/book-store-dev --follow

# Only errors, last hour
aws logs tail /aws/lambda/book-store-api-dev --since 1h \
  --filter-pattern "ERROR"
```

Both templates declare their log group **explicitly** with
`RetentionInDays: 14`. That's deliberate: log groups auto-created by
Lambda/ECS default to *never expire* and quietly bill you forever. It
also means the logs are deleted with the stack instead of being orphaned.

> **Take care of:** never log secrets, tokens, passwords, or full
> request bodies containing personal data. CloudWatch logs are
> searchable by anyone with read access to the account.

## 2. Metrics worth watching

The four "golden signals", and where they live:

| Signal | Lambda metric | Fargate metric |
|---|---|---|
| Errors | `Errors`, `Throttles` | ALB `HTTPCode_Target_5XX_Count` |
| Latency | `Duration` (p50/p99) | ALB `TargetResponseTime` |
| Traffic | `Invocations` | ALB `RequestCount` |
| Saturation | `ConcurrentExecutions` | ECS `CPUUtilization`, `MemoryUtilization` |

Plus DynamoDB, for both paths: `ThrottledRequests`,
`ConsumedReadCapacityUnits`, `UserErrors`.

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda --metric-name Errors \
  --dimensions Name=FunctionName,Value=book-store-api-dev \
  --start-time 2026-09-08T00:00:00Z --end-time 2026-09-08T23:59:59Z \
  --period 3600 --statistics Sum
```

## 3. Alarms — get told before a user tells you

Minimum useful alarm: error rate.

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name book-store-lambda-errors \
  --namespace AWS/Lambda --metric-name Errors \
  --dimensions Name=FunctionName,Value=book-store-api-dev \
  --statistic Sum --period 300 --evaluation-periods 1 \
  --threshold 5 --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:my-alerts
```

(`--alarm-actions` needs an SNS topic; create one with
`aws sns create-topic --name my-alerts` and subscribe your email.)

> **Alert on symptoms, not causes.** "Users are getting 5xx" deserves a
> page. "CPU touched 81% for 10 seconds" does not. Too many
> low-value alerts and people start ignoring all of them — that's alert
> fatigue, and it's how real outages get missed.

## 4. Rollback

**A failed deploy rolls back automatically.** CloudFormation reverts to
the last good state if any resource fails to create/update. That's a
major reason to use IaC over console clicking.

**A deploy that succeeds but ships a bug** needs you to act. Redeploy
the previous artifact:

```bash
# Lambda — point back at the old zip key
aws cloudformation deploy --template-file infra-lambda.yaml \
  --stack-name book-store-lambda-dev \
  --parameter-overrides CodeS3Bucket="$BUCKET" \
                        CodeS3Key=book-store/function-v1.zip \
  --capabilities CAPABILITY_NAMED_IAM

# Fargate — point back at the old image tag
aws cloudformation deploy --template-file infra-fargate.yaml \
  --stack-name book-store-fargate-dev \
  --parameter-overrides VpcId="$VPC" SubnetIds="$SUBNETS" \
                        ContainerImage="$REPO:v1" \
  --capabilities CAPABILITY_NAMED_IAM
```

This is exactly why doc 04 and 05 insist on **versioned zip keys and
image tags**. With `:latest` everywhere, there is no previous version to
go back to.

**See what a deploy will change, before it changes it:**

```bash
aws cloudformation deploy ... --no-execute-changeset
# prints the changeset; review, then execute it
```

Look for `Replacement: True` — that means a resource will be *destroyed
and recreated*, not modified in place. On a DynamoDB table that's data
loss. Changing `TableName` or a `KeySchema` triggers exactly this.

## 5. Cost

Rough US-East-1 figures for a low-traffic API. Verify current pricing —
this changes.

| | Lambda path | Fargate path |
|---|---|---|
| Compute idle | **$0** | ~$9/mo (2 × 0.25vCPU/0.5GB) |
| Load balancer | none | **~$16-18/mo** |
| API Gateway | $1 per million requests | none |
| DynamoDB (on-demand) | ~$0 idle | ~$0 idle |
| CloudWatch logs | pennies at 14-day retention | pennies |
| **Idle total** | **~$0** | **~$25-27/mo** |

The ALB dominates the Fargate cost and bills hourly whether or not
anyone calls your API. This is the single biggest practical difference
between the two paths.

**Watch spend:**

```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-09-01,End=2026-09-30 \
  --granularity MONTHLY --metrics UnblendedCost \
  --group-by Type=DIMENSION,Key=SERVICE
```

Also set a **billing alarm** in the console (Billing → Budgets) the
first time you use AWS. It's the cheapest insurance there is.

## 6. CI/CD — the outline

Manual `aws cloudformation deploy` is fine for learning. A real pipeline:

```
git push
   │
   ▼
1. Lint + type check          ruff, mypy
   │
   ▼
2. Run tests                  pytest test_books.py   ← must gate the deploy
   │
   ▼
3. Build artifact             zip (Lambda) or docker build (Fargate)
   │                          tag with the git commit SHA
   ▼
4. Push artifact              S3 or ECR
   │
   ▼
5. Deploy to dev              cloudformation deploy, Environment=dev
   │
   ▼
6. Smoke test dev             curl /health, assert 200
   │
   ▼
7. Manual approval            ← a human decides prod is OK
   │
   ▼
8. Deploy to prod             same template, Environment=prod
   │
   ▼
9. Smoke test prod            + watch alarms for 15 min
```

Key principles regardless of tool (GitHub Actions, CodePipeline,
GitLab CI):

- **Tests gate the deploy.** A red build never reaches AWS.
- **Tag artifacts with the commit SHA.** You can always answer "what
  code is running in prod?"
- **Same template, different parameters.** Never a separate
  `prod-template.yaml` that drifts from dev.
- **Never store AWS keys in CI.** Use OIDC federation so the runner
  assumes a role with no long-lived credentials.
- **Deploy to dev first, always.**

---

## Teardown — do this when you're done

**This is not optional if you care about your bill.** The Fargate path
costs ~$25/month sitting idle.

Because everything was created by CloudFormation, deleting is one
command per stack — no hunting for orphaned resources.

```bash
# Lambda path
aws cloudformation delete-stack --stack-name book-store-lambda-dev
aws cloudformation wait stack-delete-complete --stack-name book-store-lambda-dev

# Fargate path
aws cloudformation delete-stack --stack-name book-store-fargate-dev
aws cloudformation wait stack-delete-complete --stack-name book-store-fargate-dev
```

That removes the DynamoDB table, Lambda/ECS, ALB, API Gateway, IAM
roles, security groups, and log groups — because both templates use
`DeletionPolicy: Delete` on the table.

> For real data you'd set `DeletionPolicy: Retain` on the table, so a
> stack deletion can't destroy it. Then teardown is deliberately a
> two-step operation.

**Clean up what CloudFormation does NOT own** (they were created by
hand in docs 04/05):

```bash
# The S3 deployment bucket
aws s3 rm "s3://$BUCKET" --recursive
aws s3 rb "s3://$BUCKET"

# The ECR repository and all images
aws ecr delete-repository --repository-name book-store-api --force

# Any alarms you created
aws cloudwatch delete-alarms --alarm-names book-store-lambda-errors
```

**Verify nothing is left:**

```bash
aws cloudformation list-stacks \
  --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query 'StackSummaries[?contains(StackName,`book-store`)].StackName'
# should be empty

aws elbv2 describe-load-balancers --query 'LoadBalancers[].LoadBalancerName'
# no book-store ALB — this is the expensive one, double-check it
```

**Local cleanup:**

```bash
docker rm -f dynamodb-local          # if you ran DynamoDB Local
rm -rf build function.zip books.json .venv
```

---

## Operations checklist

- [ ] Log groups have a retention period (not "never expire")
- [ ] At least one alarm on error rate, wired to somewhere a human looks
- [ ] Artifacts versioned by commit SHA (so rollback is possible)
- [ ] A billing alarm/budget exists on the account
- [ ] You've reviewed a changeset for `Replacement: True` before a prod deploy
- [ ] Teardown verified — no stacks, no ALB, no ECR images left behind

---

`Navigation: ← prev: 05-deploy-fargate.md | back to: ../README.md`
