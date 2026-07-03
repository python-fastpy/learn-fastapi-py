# ══════════════════════════════════════════════════════════════════
# AWS Deployment — CloudWatch (Step 9)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 09-alb.py  |  next: 11-route53-cloudfront-acm.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 9: CLOUDWATCH — LOGGING & MONITORING       ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Centralized logs, metrics, alarms, dashboards.
#       Everything in AWS sends data to CloudWatch.
#
# REAL REPO:
#   Lambda logs:  /aws/lambda/a207920-spx-ci-v6-euw1-story-stories-lambda
#                 Retention: 3 days (dev), 7 days (prod)
#   ECS logs:     /aws/ecs/dev-story-drafting-service
#                 Retention: 1 month
#
# ── What Gets Created Automatically ─────────────────────────
#
#   ┌───────────┬──────────────────────────┬────────────────┐
#   │ Source    │ Log Group                 │ Who Creates It │
#   ├───────────┼──────────────────────────┼────────────────┤
#   │ Lambda   │ /aws/lambda/book-store-api│ Lambda service │
#   │ ECS      │ /ecs/book-store           │ Task definition│
#   │ API GW   │ Enable in stage settings  │ You (manual)   │
#   │ ALB      │ Access logs → S3 bucket   │ You (manual)   │
#   └───────────┴──────────────────────────┴────────────────┘
#
# ── AWS Console Steps ───────────────────────────────────────
#
# 9a. View Logs:
#
#   1. AWS Console → search "CloudWatch" → click CloudWatch
#
#   2. Left sidebar → Logs → Log groups
#
#   3. Find /aws/lambda/book-store-api → click it
#      → Click any log stream → see your Lambda execution logs
#      → Every print() and exception traceback appears here
#
#   4. Find /ecs/book-store → click it
#      → See uvicorn startup logs, request logs, errors
#
# 9b. Set Log Retention:
#
#   1. Click on a log group → Actions → "Edit retention setting"
#      ┌──────────────────────────────────────────────────┐
#      │  Retention period: 1 month  (saves cost)         │
#      │  (default is "Never expire" — expensive!)         │
#      └──────────────────────────────────────────────────┘
#
# 9c. Create Alarm:
#
#   1. CloudWatch → Alarms → "Create alarm"
#
#   2. Select metric:
#      → AWS/Lambda → By Function Name
#      → book-store-api → Errors
#      → Select metric
#
#   3. Configure:
#      ┌──────────────────────────────────────────────────┐
#      │  Statistic:  Sum                                  │
#      │  Period:     5 minutes                            │
#      │  Threshold:  Static                               │
#      │  Condition:  Greater than or equal to 5           │
#      │                                                    │
#      │  → "5 or more errors in 5 minutes triggers alarm"│
#      └──────────────────────────────────────────────────┘
#
#   4. Notification:
#      → Create new SNS topic: book-store-errors
#      → Email: your-email@example.com
#      → You'll get a confirmation email — click confirm!
#
#   5. Name: book-store-high-error-rate → Create alarm
#
# 9d. Create Dashboard:
#
#   1. CloudWatch → Dashboards → "Create dashboard"
#      Name: book-store-dashboard
#
#   2. Add widgets:
#      → Add widget → Line → Select metrics:
#        AWS/Lambda → book-store-api → Invocations, Errors, Duration
#      → Add widget → Number → Select metrics:
#        AWS/ECS → book-store-service → CPUUtilization, MemoryUtilization
#
# ── ECS Auto-Scaling (based on CloudWatch metrics) ──────────
#
#   1. ECS → book-store-cluster → book-store-service
#   2. Click "Update service"
#   3. Scroll to "Service auto scaling"
#      ┌──────────────────────────────────────────────────┐
#      │  ✅ Use service auto scaling                      │
#      │  Minimum tasks: 1                                 │
#      │  Maximum tasks: 5                                 │
#      │  Desired tasks: 2                                 │
#      │                                                    │
#      │  Scaling policy:                                  │
#      │    Policy type: Target tracking                   │
#      │    Policy name: cpu-scaling                       │
#      │    ECS metric:  ECSServiceAverageCPUUtilization   │
#      │    Target value: 70  (scale out when CPU > 70%)   │
#      │    Scale-in cooldown:  60 seconds                 │
#      │    Scale-out cooldown: 60 seconds                 │
#      └──────────────────────────────────────────────────┘
#      → Update
#
# ── CloudWatch Key Concepts ─────────────────────────────────
#
#   ── Log Groups ─────────────────────────────────────────────
#
#   A container for log streams. One log group per service.
#   Think of it as a folder for all logs from one application.
#
#   Naming convention:
#     Lambda:  /aws/lambda/<function-name>     ← auto-created
#     ECS:     /ecs/<service-name>             ← you define in task def
#     API GW:  API-Gateway-Execution-Logs_<id> ← enable in settings
#     Custom:  /app/<service-name>             ← from your code
#
#   Real examples from the skills repo:
#     /aws/ecs/dev-story-drafting-service     (retention: 1 month)
#     /aws/ecs/dev-urgent-drafting-service    (retention: 1 month)
#     /aws/lambda/a207920-spx-ci-v6-stories  (retention: 3 days dev, 7 days prod)
#
#   Retention periods (set per log group):
#     1 day, 3 days, 5 days, 1 week, 2 weeks, 1 month, 2 months,
#     3 months, 6 months, 1 year, 13 months, 18 months, 2 years,
#     3 years, 5 years, 10 years, Never expire
#
#     COST WARNING: "Never expire" (default) accumulates storage cost.
#     Set retention! CloudWatch Logs cost $0.50/GB ingested + $0.03/GB stored.
#     For dev: 3-7 days. For prod: 1-3 months.
#
#   ── Log Streams ────────────────────────────────────────────
#
#   Within a log group, logs are split into streams. Each stream
#   is a sequence of events from one source.
#
#   Lambda log streams:
#     YYYY/MM/DD/[$LATEST]<random-id>
#     Each Lambda instance gets its own stream.
#     New cold start = new stream.
#
#   ECS log streams:
#     <prefix>/<container-name>/<task-id>
#     Example: book-store/book-store-container/abc123def456
#     Each ECS task gets its own stream.
#
#   Practical tip: When debugging, look at the NEWEST stream
#   (sort by Last event time). Old streams are from previous tasks.
#
#   ── Log Insights (Querying Logs) ───────────────────────────
#
#   SQL-like query language for searching across millions of log lines.
#   Much faster than scrolling through log streams manually.
#
#   CloudWatch → Logs → Log Insights
#   → Select log group(s) → Write query → Run
#
#   Common queries:
#
#     # Find all errors in the last hour
#     fields @timestamp, @message
#     | filter @message like /ERROR/
#     | sort @timestamp desc
#     | limit 50
#
#     # Count requests per endpoint
#     fields @message
#     | filter @message like /HTTP/
#     | parse @message '"GET * HTTP' as endpoint
#     | stats count(*) by endpoint
#     | sort count desc
#
#     # Find slow requests (> 1 second)
#     fields @timestamp, @message, @duration
#     | filter @duration > 1000
#     | sort @duration desc
#     | limit 20
#
#     # Find a specific request by ID
#     fields @timestamp, @message
#     | filter @message like "abc-123-request-id"
#
#   Log Insights pricing: $0.005 per GB scanned.
#   Narrower time ranges = less data scanned = cheaper.
#
#   ── Metrics ────────────────────────────────────────────────
#
#   Numerical data points collected over time. AWS services
#   automatically publish metrics. You can also publish custom ones.
#
#   Auto-published metrics (free):
#
#     Lambda:
#       Invocations        → total calls
#       Errors             → failed calls (exceptions)
#       Duration           → execution time (ms)
#       Throttles          → requests rejected (concurrency limit)
#       ConcurrentExecs    → active instances
#       ColdStartDuration  → time spent on cold start
#
#     ECS:
#       CPUUtilization     → % of allocated CPU used
#       MemoryUtilization  → % of allocated memory used
#       RunningTaskCount   → number of running tasks
#       DesiredTaskCount   → target number of tasks
#
#     ALB:
#       RequestCount       → total requests
#       TargetResponseTime → how long targets take to respond
#       HTTPCode_Target_2XX → successful responses
#       HTTPCode_Target_5XX → server errors
#       HealthyHostCount   → healthy targets
#       UnHealthyHostCount → unhealthy targets
#       ActiveConnectionCount → current connections
#
#   Custom metrics (from your app code):
#
#     import boto3
#     cloudwatch = boto3.client("cloudwatch")
#     cloudwatch.put_metric_data(
#         Namespace="BookStore",
#         MetricData=[{
#             "MetricName": "BooksCreated",
#             "Value": 1,
#             "Unit": "Count"
#         }]
#     )
#
#   Custom metrics cost: $0.30/metric/month (first 10,000).
#
#   ── Alarms ─────────────────────────────────────────────────
#
#   Watch a metric and trigger an action when it crosses a threshold.
#
#   Alarm states:
#     OK             → metric is within normal range
#     ALARM          → metric crossed the threshold
#     INSUFFICIENT_DATA → not enough data points yet
#
#   Actions you can trigger:
#     SNS notification  → email, SMS, Slack (via Lambda)
#     Auto Scaling      → scale ECS tasks up/down
#     EC2 action        → stop, terminate, reboot instance
#     Lambda function   → run custom remediation code
#
#   Practical examples:
#
#     Error rate alarm:
#       Metric:    Lambda Errors, Sum, 5-minute periods
#       Threshold: >= 5 errors in 5 minutes
#       Action:    SNS → email notification
#       → "Your API had 5+ errors in 5 minutes — investigate!"
#
#     High CPU alarm (auto-scaling trigger):
#       Metric:    ECS CPUUtilization, Average, 1-minute periods
#       Threshold: > 70% for 3 consecutive minutes
#       Action:    ECS auto-scaling policy → add tasks
#       → "CPU above 70% for 3 minutes, scaling from 2 to 3 tasks"
#
#     No traffic alarm:
#       Metric:    ALB RequestCount, Sum, 5-minute periods
#       Threshold: < 1 for 3 periods (15 minutes no traffic)
#       Action:    SNS → PagerDuty/Slack
#       → "Zero requests for 15 minutes — is the service down?"
#
#   Composite alarms:
#     Combine multiple alarms with AND/OR logic.
#     Only alert when BOTH CPU > 70% AND error rate > 5%.
#     Reduces alert fatigue from noisy individual alarms.
#
#   ── Dashboards ─────────────────────────────────────────────
#
#   Visual display of metrics on a single page. Build one per service
#   or per environment for at-a-glance monitoring.
#
#   Cost: $3/month per dashboard (first 3 free).
#
#   Recommended widgets for a FastAPI service:
#
#     Row 1 (Traffic):
#       ALB RequestCount (line) | ALB TargetResponseTime (line)
#
#     Row 2 (Health):
#       ALB 5xx error count (number) | ECS RunningTaskCount (number)
#       HealthyHostCount (number)
#
#     Row 3 (Resources):
#       ECS CPUUtilization (line) | ECS MemoryUtilization (line)
#
#     Row 4 (Lambda path):
#       Lambda Invocations (line) | Lambda Duration p50/p99 (line)
#       Lambda Errors (line)
#
#   ── CloudWatch vs External Tools ───────────────────────────
#
#   CloudWatch works but has limitations. Many teams complement
#   it with external tools:
#
#     ┌──────────────┬──────────────────────────────────────┐
#     │ Datadog      │ Better dashboards, APM tracing,      │
#     │              │ 400+ integrations. $15/host/month.    │
#     ├──────────────┼──────────────────────────────────────┤
#     │ Grafana      │ Open-source dashboards. Uses CW as   │
#     │              │ data source. Free (self-hosted).      │
#     ├──────────────┼──────────────────────────────────────┤
#     │ PagerDuty    │ Incident management, on-call rotation.│
#     │              │ Receives CW alarms via SNS.           │
#     ├──────────────┼──────────────────────────────────────┤
#     │ X-Ray        │ AWS distributed tracing. Traces       │
#     │              │ requests across Lambda/ECS/API GW.    │
#     └──────────────┴──────────────────────────────────────┘
