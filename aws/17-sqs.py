# ══════════════════════════════════════════════════════════════════
# AWS Deployment — SQS (Step 14)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 16-sns.py  |  next: 18-waf.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 14: SQS — SIMPLE QUEUE SERVICE             ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Fully managed message queuing service. Decouples producers
#       from consumers. Messages are stored durably until a consumer
#       processes and deletes them. Scales to unlimited throughput.
#
# REAL REPO: Lambda destinations in the skills repo can send failures
#            to SQS dead letter queues. SQS enables async processing
#            patterns for skill execution results and retries.
#
# ── How SQS Works ───────────────────────────────────────────
#
#   Producer sends message → SQS stores it → Consumer polls,
#   processes, and deletes.
#
#   ┌────────────┐   send    ┌──────────────────┐   receive   ┌────────────┐
#   │ Producer   │─────────►│                  │◄───────────│ Consumer   │
#   │ (API/      │           │   SQS Queue      │             │ (Lambda/   │
#   │  Lambda)   │           │   ┌──┬──┬──┬──┐  │   delete    │  ECS)      │
#   └────────────┘           │   │m4│m3│m2│m1│  │◄───────────│            │
#                            │   └──┴──┴──┴──┘  │             └────────────┘
#                            └──────────────────┘
#
#   Messages are PERSISTENT. They stay in the queue until:
#     - A consumer explicitly deletes them (after processing)
#     - The retention period expires (default: 4 days, max: 14 days)
#
#   This is different from SNS (fire-and-forget). SQS guarantees
#   the message will be processed — even if the consumer is down.
#
# ── Queue Types ─────────────────────────────────────────────
#
#   ┌──────────────────┬────────────────────┬────────────────────┐
#   │                  │ Standard           │ FIFO               │
#   ├──────────────────┼────────────────────┼────────────────────┤
#   │ Delivery         │ At-least-once      │ Exactly-once       │
#   │                  │ (possible dupes)   │ (deduplication)    │
#   │ Ordering         │ Best-effort        │ Strict (per group) │
#   │ Throughput       │ Unlimited          │ 300 msg/sec without│
#   │                  │                    │ batching, 3000 with│
#   │ Name             │ my-queue           │ my-queue.fifo      │
#   │ Use when         │ High throughput,   │ Order matters,     │
#   │                  │ dupes are OK       │ no duplicates      │
#   └──────────────────┴────────────────────┴────────────────────┘
#
#   Standard is the default and right choice 90% of the time.
#   Use FIFO only when message ordering or deduplication is critical
#   (e.g., financial transactions, sequential workflow steps).
#
# ── Core Concepts ───────────────────────────────────────────
#
#   Visibility Timeout:
#     When a consumer receives a message, the message becomes
#     INVISIBLE to other consumers for this duration (default: 30s).
#     If the consumer processes and deletes it, great.
#     If the consumer crashes, the message becomes visible again
#     and another consumer picks it up.
#
#     ┌──────────┐   receive   ┌──────────┐  30 sec   ┌──────────┐
#     │ visible  │────────────►│ invisible│──────────►│ visible  │
#     │ (in queue)│            │ (locked) │  (timeout) │ (retry)  │
#     └──────────┘            └──────────┘           └──────────┘
#                                   │ delete
#                                   ▼
#                              (gone forever)
#
#     Set visibility timeout > your processing time.
#     If processing takes 60 seconds, set timeout to 90 seconds.
#
#   Retention Period:
#     How long unprocessed messages stay in the queue.
#     Default: 4 days. Max: 14 days. After that, messages are lost.
#
#   Long Polling vs Short Polling:
#     Short polling: Returns immediately, even if queue is empty.
#       → Wasteful — lots of empty responses, costs money.
#     Long polling: Waits up to 20 seconds for a message to arrive.
#       → Efficient — fewer API calls, lower cost.
#     Set ReceiveMessageWaitTimeSeconds = 20 (always use long polling).
#
#   Delay Queues:
#     Delay delivery of ALL messages in the queue by N seconds.
#     Range: 0 to 900 seconds (15 minutes).
#     Use case: "Process this order, but wait 5 minutes first"
#     (gives the user time to cancel).
#
# ── Dead Letter Queue (DLQ) ─────────────────────────────────
#
#   When a message fails processing repeatedly, move it to a
#   separate "dead letter" queue for inspection instead of
#   retrying forever.
#
#   ┌────────────┐    fail ×3     ┌────────────────┐
#   │ Main Queue │───────────────►│ Dead Letter Q   │
#   │ "orders"   │  (maxReceive   │ "orders-dlq"    │
#   │            │   Count = 3)   │                  │
#   └────────────┘                │ Inspect failed   │
#                                 │ messages here    │
#                                 └────────────────┘
#
#   Configuration:
#     Main queue → Redrive policy:
#       Dead letter queue: orders-dlq
#       Maximum receives: 3  (after 3 failed processing attempts)
#
#   The DLQ is just a regular SQS queue. You can:
#     - Inspect messages manually (Console → Poll for messages)
#     - Trigger a Lambda to alert your team
#     - Redrive: move messages back to the main queue for retry
#       (Console → Dead-letter queue → "Start DLQ redrive")
#
# ── Lambda Trigger from SQS ────────────────────────────────
#
#   SQS can automatically trigger a Lambda function when
#   messages arrive. Lambda polls the queue for you.
#
#   ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
#   │ SQS Queue    │───────►│   Lambda     │───────►│  DynamoDB    │
#   │ "orders"     │ trigger│ process_order│  write  │  "orders"    │
#   └──────────────┘        └──────────────┘        └──────────────┘
#
#   Configuration (Lambda → Configuration → Triggers → Add trigger):
#   ┌──────────────────────────────────────────────────┐
#   │  Source:     SQS                                  │
#   │  Queue:      orders-queue                         │
#   │  Batch size: 10  (Lambda receives up to 10 msgs) │
#   │  Batch window: 5 sec (wait for more msgs)        │
#   │  Report batch item failures: ENABLE              │
#   │    → Only failed messages go back to queue        │
#   │    → Without this, ALL messages retry on any fail │
#   └──────────────────────────────────────────────────┘
#
#   Lambda handler for SQS events:
#
#   def handler(event, context):
#       failed_ids = []
#       for record in event["Records"]:
#           try:
#               body = json.loads(record["body"])
#               process_order(body)
#           except Exception:
#               failed_ids.append({"itemIdentifier": record["messageId"]})
#       return {"batchItemFailures": failed_ids}
#       # Only failed messages return to queue for retry
#
# ── Practical Example: Book Store Order Processing ──────────
#
#   User places order → API writes to SQS → Lambda processes
#   asynchronously → writes to DynamoDB.
#
#   Why not process directly in the API?
#     - API responds instantly (200 OK, "order received")
#     - Processing happens in background (no timeout risk)
#     - If processing fails, message stays in queue (auto-retry)
#     - Handles traffic spikes (queue absorbs the burst)
#
#   ┌──────────┐  POST /orders  ┌──────────┐  send_msg  ┌──────────┐
#   │  User    │───────────────►│ FastAPI  │───────────►│  SQS     │
#   │          │◄───────────────│ 202      │            │ "orders" │
#   └──────────┘  "accepted"    └──────────┘            └────┬─────┘
#                                                            │ trigger
#                                                       ┌────▼─────┐
#                                                       │  Lambda  │
#                                                       │ process  │
#                                                       │ order    │
#                                                       └────┬─────┘
#                                                            │ put_item
#                                                       ┌────▼─────┐
#                                                       │ DynamoDB │
#                                                       │ "orders" │
#                                                       └──────────┘
#
# ── FIFO Features ───────────────────────────────────────────
#
#   Message Deduplication ID:
#     Prevents duplicate messages within a 5-minute window.
#     If you send the same DeduplicationId twice, SQS ignores
#     the second. Can also enable content-based deduplication
#     (SHA-256 of the message body).
#
#   Message Group ID:
#     Messages with the same GroupId are processed in order.
#     Different GroupIds are processed in parallel.
#
#     Example: Order processing per customer.
#       GroupId="customer-123" → orders for cust 123 are sequential
#       GroupId="customer-456" → orders for cust 456 are sequential
#       But 123 and 456 orders process in parallel.
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console → search "SQS" → click "Simple Queue Service"
#
#   2. Click "Create queue"
#      ┌──────────────────────────────────────────────────┐
#      │  Type: Standard                                    │
#      │  Name: book-store-orders                           │
#      │                                                    │
#      │  Configuration:                                    │
#      │    Visibility timeout:    60 seconds                │
#      │    Message retention:     4 days                    │
#      │    Maximum message size:  256 KB                    │
#      │    Delivery delay:        0 seconds                 │
#      │    Receive message wait:  20 seconds (long polling) │
#      └──────────────────────────────────────────────────┘
#      → Create queue
#
#   3. Create a Dead Letter Queue:
#      → Create queue → Name: book-store-orders-dlq → Create
#      → Go back to book-store-orders → Edit
#      → Dead-letter queue: Enabled
#      ┌──────────────────────────────────────────────────┐
#      │  Queue: book-store-orders-dlq                      │
#      │  Maximum receives: 3                               │
#      └──────────────────────────────────────────────────┘
#      → Save
#
#   4. Send a test message:
#      → Click book-store-orders → "Send and receive messages"
#      ┌──────────────────────────────────────────────────┐
#      │  Message body:                                     │
#      │  {"order_id":"ord-001","book_id":"book-001",      │
#      │   "quantity":2,"user_id":"user-alice"}             │
#      └──────────────────────────────────────────────────┘
#      → Send message
#
#   5. Receive and delete:
#      → "Poll for messages" → message appears
#      → Click message to inspect body → Delete
#
# ── Boto3 Examples ──────────────────────────────────────────
#
#   import boto3, json
#
#   sqs = boto3.client("sqs", region_name="eu-west-1")
#   queue_url = "https://sqs.eu-west-1.amazonaws.com/123456789/book-store-orders"
#
#   # Send a message
#   sqs.send_message(
#       QueueUrl=queue_url,
#       MessageBody=json.dumps({
#           "order_id": "ord-001",
#           "book_id": "book-001",
#           "quantity": 2
#       }),
#       MessageAttributes={
#           "priority": {"DataType": "String", "StringValue": "high"}
#       }
#   )
#
#   # Receive messages (long poll, batch of 10)
#   response = sqs.receive_message(
#       QueueUrl=queue_url,
#       MaxNumberOfMessages=10,
#       WaitTimeSeconds=20,    # Long polling
#       MessageAttributeNames=["All"]
#   )
#   messages = response.get("Messages", [])
#
#   # Process and delete
#   for msg in messages:
#       body = json.loads(msg["Body"])
#       process_order(body)
#       sqs.delete_message(
#           QueueUrl=queue_url,
#           ReceiptHandle=msg["ReceiptHandle"]  # NOT MessageId
#       )
#
# ── SQS vs Kinesis ──────────────────────────────────────────
#
#   ┌──────────────────┬──────────────────┬──────────────────┐
#   │                  │ SQS              │ Kinesis Streams  │
#   ├──────────────────┼──────────────────┼──────────────────┤
#   │ Pattern          │ Message queue    │ Event stream     │
#   │ Consumer model   │ One consumer per │ Multiple consumers│
#   │                  │ message (delete) │ read same stream  │
#   │ Retention        │ Up to 14 days    │ Up to 365 days   │
#   │ Ordering         │ Best-effort/FIFO │ Per-shard ordering│
#   │ Throughput       │ Unlimited        │ Per-shard limited │
#   │ Scaling          │ Automatic        │ Manual (add shards│
#   │ Replay           │ No (deleted)     │ Yes (reread)     │
#   │ Pricing          │ Per request      │ Per shard-hour   │
#   │ Best for         │ Task queues,     │ Real-time analytics│
#   │                  │ decoupling       │ log aggregation   │
#   └──────────────────┴──────────────────┴──────────────────┘
#
#   Rule: "Process once and done" → SQS.
#         "Multiple readers, replay, real-time" → Kinesis.
#
# ── Cost ────────────────────────────────────────────────────
#
#   Standard queues:
#     First 1 million requests/month: FREE
#     After that: $0.40 per 1 million requests
#
#   FIFO queues:
#     First 1 million requests/month: FREE
#     After that: $0.50 per 1 million requests
#
#   A "request" is any API call: SendMessage, ReceiveMessage,
#   DeleteMessage, etc. Batch operations count as 1 request
#   (up to 10 messages per batch).
#
#   Data transfer: First 1 GB/month free, then standard rates.
#
#   Example (book-store orders):
#     500 orders/day × 30 = 15,000 messages/month
#     Each message: send + receive + delete = 3 requests
#     Total: 45,000 requests/month = FREE
#
# ── Common Gotchas ──────────────────────────────────────────
#
#   1. 256 KB message size limit. For larger payloads, use the
#      "claim check" pattern: store data in S3, send S3 key
#      in the SQS message. The AWS SQS Extended Client Library
#      automates this.
#
#   2. Visibility timeout tuning. Too short: message reappears
#      while still being processed → duplicate processing.
#      Too long: if consumer crashes, long wait before retry.
#      Rule of thumb: 6x your average processing time.
#
#   3. FIFO throughput limits. 300 messages/sec without batching.
#      With batching (10 messages per batch): 3,000 msgs/sec.
#      If you need more, use multiple message group IDs
#      or switch to standard queue.
#
#   4. ReceiptHandle, NOT MessageId. To delete a message you
#      must use the ReceiptHandle from the receive call, not
#      the MessageId. Each receive generates a new handle.
#
#   5. Partial batch failures with Lambda. Without enabling
#      "Report batch item failures", if ONE message in a batch
#      of 10 fails, ALL 10 return to the queue. Enable partial
#      batch failure reporting (see Lambda trigger section).
#
#   6. Long polling saves money. Short polling charges you for
#      every empty ReceiveMessage call. With long polling
#      (WaitTimeSeconds=20), you only pay when messages exist.
#
#   7. Don't use SQS for pub/sub. If multiple consumers each
#      need a copy of every message, use SNS → SQS fanout.
#      A single SQS queue delivers each message to only ONE
#      consumer.
