# ══════════════════════════════════════════════════════════════════
# AWS Deployment — SNS (Step 13)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 15-dynamodb.py  |  next: 17-sqs.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 13: SNS — SIMPLE NOTIFICATION SERVICE      ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Pub/sub messaging service. Send one message, deliver it
#       to many subscribers simultaneously. Fully managed, no servers.
#       Think of it as a broadcast system — publish once, notify many.
#
# REAL REPO: CloudWatch alarms in the skills deployment send
#            notifications via SNS. When error rate exceeds a
#            threshold or ECS task fails, SNS delivers alerts
#            to the team via email or Slack webhook.
#
# ── How SNS Works ───────────────────────────────────────────
#
#   The core model is: Publisher → Topic → Subscribers
#
#   ┌────────────┐    publish     ┌─────────────┐    deliver
#   │ Publisher   │──────────────►│  SNS Topic   │──────────►  Subscriber 1 (Email)
#   │ (CW Alarm) │               │ "alerts"     │──────────►  Subscriber 2 (Lambda)
#   └────────────┘               └─────────────┘──────────►  Subscriber 3 (SQS)
#                                                ──────────►  Subscriber 4 (HTTPS)
#
#   Publishers don't know (or care) who the subscribers are.
#   Subscribers don't know (or care) who published the message.
#   The topic decouples them completely.
#
# ── Subscription Protocols ──────────────────────────────────
#
#   SNS supports delivering messages over many protocols:
#
#   ┌──────────────────┬──────────────────────────────────────┐
#   │ Protocol         │ Use Case                             │
#   ├──────────────────┼──────────────────────────────────────┤
#   │ Email            │ Alert team when alarms fire          │
#   │ Email-JSON       │ Machine-readable email alerts        │
#   │ SMS              │ Text critical alerts to on-call      │
#   │ HTTPS endpoint   │ Webhook to Slack, PagerDuty, etc.    │
#   │ AWS Lambda       │ Trigger serverless processing        │
#   │ Amazon SQS       │ Queue messages for async consumers   │
#   │ Mobile push      │ iOS/Android push notifications       │
#   │ Kinesis Firehose │ Stream to S3/Redshift/Elasticsearch  │
#   └──────────────────┴──────────────────────────────────────┘
#
# ── SNS + CloudWatch Alarms (Main Use Case in the Repo) ─────
#
#   This is the most common pattern — the one used by the skills
#   infrastructure. When something goes wrong, you want to know.
#
#   Flow:
#     CloudWatch detects metric breach (e.g., error rate > 5%)
#       → CloudWatch Alarm enters ALARM state
#       → Alarm action publishes to SNS topic
#       → SNS delivers to all subscribers (email, Slack, etc.)
#
#   ┌───────────────┐       ┌──────────────┐       ┌────────────┐
#   │  CloudWatch   │       │  SNS Topic   │       │  Email     │
#   │  Alarm:       │──────►│  "skills-    │──────►│  team@     │
#   │  ECS errors>5 │       │   alerts"    │──────►│  reuters   │
#   └───────────────┘       └──────────────┘       ├────────────┤
#                                                   │  Slack     │
#                                                   │  webhook   │
#                                                   └────────────┘
#
#   This is already set up in 10-cloudwatch.py (alarm creation).
#   This file covers the SNS side: creating topics, adding
#   subscribers, and message patterns.
#
# ── Fanout Pattern: SNS → Multiple SQS Queues ──────────────
#
#   One of the most powerful AWS patterns. A single event
#   triggers multiple independent processing pipelines.
#
#   Example: New book published in the store.
#
#   ┌────────────┐        ┌─────────────┐    ┌──────────────┐
#   │ Book Store │        │  SNS Topic  │    │  SQS: email  │→ Lambda: send email
#   │ API        │──pub──►│  "new-book" │───►│  notifications│
#   └────────────┘        │             │    └──────────────┘
#                         │             │    ┌──────────────┐
#                         │             │───►│  SQS: search │→ Lambda: update index
#                         │             │    │  indexing     │
#                         │             │    └──────────────┘
#                         │             │    ┌──────────────┐
#                         │             │───►│  SQS: audit  │→ Lambda: write audit
#                         └─────────────┘    │  log          │
#                                            └──────────────┘
#
#   Each SQS queue processes independently. If the email Lambda
#   fails, the search indexing and audit log are unaffected.
#
# ── Message Filtering ──────────────────────────────────────
#
#   Subscribers can filter messages — only receive what's relevant.
#   Without filtering, every subscriber gets EVERY message.
#
#   Filter policy (set per subscription):
#
#   Topic: "book-events"
#   Message attributes: { "genre": "fiction", "action": "created" }
#
#   Subscriber 1 filter: { "genre": ["fiction"] }
#     → Only receives fiction book events
#
#   Subscriber 2 filter: { "action": ["deleted"] }
#     → Only receives deletion events
#
#   Subscriber 3 filter: (no filter)
#     → Receives ALL messages
#
#   This reduces noise and avoids subscribers processing
#   irrelevant messages. Set up in the subscription, not the topic.
#
# ── Message Structure ──────────────────────────────────────
#
#   SNS messages can include:
#
#   - Body (required): The message content (string, up to 256 KB)
#   - Subject (optional): Email subject line
#   - Message attributes: Key-value metadata for filtering
#   - Message structure: Send different content per protocol
#
#   JSON message with per-protocol content:
#   {
#     "default": "Book '1984' has been added to the store",
#     "email": "New Book Alert!\n\nTitle: 1984\nAuthor: Orwell",
#     "sqs": "{\"book_id\":\"book-001\",\"action\":\"created\"}",
#     "lambda": "{\"book_id\":\"book-001\",\"action\":\"created\"}"
#   }
#
#   Each protocol subscriber gets its own tailored message.
#   The "default" is required — used for protocols without
#   a specific entry.
#
# ── FIFO Topics ─────────────────────────────────────────────
#
#   Standard topics: Best-effort ordering, at-least-once delivery.
#   FIFO topics:     Strict ordering, exactly-once delivery.
#
#   FIFO topic names MUST end in ".fifo" (e.g., "orders.fifo").
#
#   Features:
#     - Message ordering:   Messages arrive in exact send order
#     - Deduplication:      Same message sent twice is delivered once
#     - Message group ID:   Ordering is per-group (different groups
#                           are independent)
#
#   Trade-off: FIFO topics support only 300 publishes/sec
#   (vs virtually unlimited for standard). Use standard unless
#   ordering is critical.
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console → search "SNS" → click "Simple Notification Service"
#
#   2. Click "Create topic"
#      ┌──────────────────────────────────────────────────┐
#      │  Type: Standard                                    │
#      │  Name: book-store-alerts                           │
#      │  Display name: Book Store Alerts  (for SMS/email)  │
#      │                                                    │
#      │  Access policy: Basic                              │
#      │  → Only the topic owner can publish (default)      │
#      │                                                    │
#      │  Encryption: Disabled (default, fine for alerts)   │
#      └──────────────────────────────────────────────────┘
#      → Create topic
#
#   3. Add email subscription:
#      → Click on your topic → "Create subscription"
#      ┌──────────────────────────────────────────────────┐
#      │  Protocol: Email                                   │
#      │  Endpoint: your-team@reuters.com                   │
#      └──────────────────────────────────────────────────┘
#      → Create subscription
#      → CHECK YOUR EMAIL → click "Confirm subscription" link
#      → Status changes from "Pending" to "Confirmed"
#
#   4. Test — publish a message:
#      → Topic → "Publish message"
#      ┌──────────────────────────────────────────────────┐
#      │  Subject: Test Alert                               │
#      │  Message body:                                     │
#      │    Book Store API error rate exceeded 5%.           │
#      │    Check CloudWatch dashboard for details.          │
#      └──────────────────────────────────────────────────┘
#      → Publish message
#      → Check your email — you should receive it within seconds
#
#   5. Wire up to CloudWatch Alarm:
#      → CloudWatch → Alarms → select your alarm → Edit
#      → Notification → In alarm → Select SNS topic:
#        book-store-alerts
#      → Now the alarm automatically publishes to SNS on trigger
#
# ── Boto3 Example ───────────────────────────────────────────
#
#   import boto3
#
#   sns = boto3.client("sns", region_name="eu-west-1")
#
#   # Create a topic
#   response = sns.create_topic(Name="book-store-alerts")
#   topic_arn = response["TopicArn"]
#   # arn:aws:sns:eu-west-1:123456789:book-store-alerts
#
#   # Subscribe an email
#   sns.subscribe(
#       TopicArn=topic_arn,
#       Protocol="email",
#       Endpoint="team@reuters.com"
#   )
#
#   # Publish a message
#   sns.publish(
#       TopicArn=topic_arn,
#       Subject="High Error Rate Alert",
#       Message="Error rate on story-drafting exceeded 5%."
#   )
#
#   # Publish with message attributes (for filtering)
#   sns.publish(
#       TopicArn=topic_arn,
#       Message="ECS task stopped unexpectedly",
#       MessageAttributes={
#           "severity": {"DataType": "String", "StringValue": "critical"},
#           "service":  {"DataType": "String", "StringValue": "story-drafting"}
#       }
#   )
#
# ── Dead Letter Queues for Failed Deliveries ────────────────
#
#   If SNS can't deliver a message (e.g., HTTPS endpoint is down),
#   it retries with backoff. After all retries fail, the message
#   is lost — UNLESS you configure a Dead Letter Queue (DLQ).
#
#   SNS → subscriber fails → retries → still fails → SQS DLQ
#
#   The DLQ is an SQS queue that catches failed messages.
#   You can inspect them later, fix the subscriber, and replay.
#
#   Set per subscription: Subscription → Redrive policy →
#   SQS queue ARN for dead letter queue.
#
# ── SNS vs SQS vs EventBridge ──────────────────────────────
#
#   ┌──────────────────┬──────────────┬───────────────┬────────────────┐
#   │                  │ SNS          │ SQS           │ EventBridge    │
#   ├──────────────────┼──────────────┼───────────────┼────────────────┤
#   │ Pattern          │ Pub/Sub      │ Queue (1:1)   │ Event bus      │
#   │ Delivery         │ Push (fan-out│ Pull (consumer│ Push (rule-    │
#   │                  │ to many)     │ polls queue)  │ based routing) │
#   │ Persistence      │ No (fire &   │ Yes (14 days  │ No (fire &     │
#   │                  │ forget)      │ retention)    │ forget)        │
#   │ Ordering         │ Best-effort  │ FIFO available│ Best-effort    │
#   │ Use when         │ Broadcast to │ Decouple &    │ Route events   │
#   │                  │ many targets │ buffer work   │ by rules/patt. │
#   │ Max message size │ 256 KB       │ 256 KB        │ 256 KB         │
#   └──────────────────┴──────────────┴───────────────┴────────────────┘
#
#   Common combo: SNS for fan-out, SQS for buffering.
#   SNS → SQS → Lambda is the most reliable async pattern.
#
# ── Cost ────────────────────────────────────────────────────
#
#   First 1 million SNS requests/month: FREE
#   After that: $0.50 per 1 million requests
#
#   Email delivery:  $0 for first 1,000 → $2 per 100,000 after
#   SMS delivery:    Varies by country ($0.00645/msg in US)
#   HTTP/S delivery: First 100,000 free → $0.06 per 100,000
#   SQS delivery:    Free (SQS charges apply on the queue side)
#   Lambda delivery: Free (Lambda charges apply on invocation)
#
#   Example (skills alerting):
#     100 alarm notifications/month = FREE (well under 1M)
#     Email delivery for 100 msgs = FREE (under 1,000)
#     Total: $0/month for typical alerting use case
#
# ── Common Gotchas ──────────────────────────────────────────
#
#   1. 256 KB message size limit. For larger payloads, store
#      the data in S3 and send the S3 key/URL in the SNS message.
#
#   2. Email/HTTP subscriptions require CONFIRMATION. After
#      creating a subscription, the endpoint receives a
#      confirmation link/request. Until confirmed, status stays
#      "PendingConfirmation" and no messages are delivered.
#
#   3. SMS spending limit defaults to $1.00/month (US). You'll
#      silently stop receiving SMS once exceeded. Increase via
#      SNS → Text messaging → Spending limit.
#
#   4. Standard topics deliver "at least once" — duplicates are
#      possible. Your subscribers should be idempotent (safe to
#      process the same message twice).
#
#   5. SNS does NOT persist messages. If no subscribers are
#      listening when a message is published, it's lost.
#      Use SNS → SQS for durability.
#
#   6. Cross-account publishing requires explicit topic access
#      policy. The publishing account's IAM isn't enough —
#      the topic must also allow it.
#
#   7. Email subscriptions are per-email-address. You can't
#      subscribe a distribution list and then manage members
#      outside AWS — each email needs its own subscription.
