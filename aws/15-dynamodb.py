# ══════════════════════════════════════════════════════════════════
# AWS Deployment — DynamoDB (Step 12)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 14-cleanup-and-summary.py  |  next: 16-sns.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 12: DYNAMODB — NoSQL DATABASE              ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Fully managed, serverless, key-value + document NoSQL database.
#       Single-digit millisecond latency at any scale. No servers to
#       manage, no patching, no capacity planning (in on-demand mode).
#
# REAL REPO: The reuters-assistant backend uses DynamoDB for ALL storage:
#
#   Table prefix: a209485-assistant-backend-dev- (from DYNAMODB_TABLE_PREFIX)
#
#   ┌──────────────────────────┬───────────────────────────────────┐
#   │ Table                    │ Purpose                           │
#   ├──────────────────────────┼───────────────────────────────────┤
#   │ session-history          │ Chat sessions, messages, metadata │
#   │                          │ TTL auto-deletes expired sessions │
#   ├──────────────────────────┼───────────────────────────────────┤
#   │ skills-registry          │ Registered MCP servers + cached   │
#   │                          │ tool capabilities per tenant      │
#   ├──────────────────────────┼───────────────────────────────────┤
#   │ tenant-registry          │ Tenant config, server access      │
#   │                          │ control (READ/WRITE/ADMIN)        │
#   ├──────────────────────────┼───────────────────────────────────┤
#   │ langgraph-checkpoints    │ LangGraph state checkpoints for   │
#   │                          │ human-in-the-loop interrupt/resume│
#   ├──────────────────────────┼───────────────────────────────────┤
#   │ agent-checkpoints        │ Create Agent PoC checkpoints      │
#   │                          │ (with optional S3 offload)        │
#   └──────────────────────────┴───────────────────────────────────┘
#
# ── Table Structure ─────────────────────────────────────────
#
#   DynamoDB is NOT a relational database. No joins, no schemas.
#   Think of it as a giant hash map / dictionary.
#
#   Core terminology:
#
#     Table     →  A collection of items (like an SQL table)
#     Item      →  A single record (like an SQL row)
#     Attribute →  A field on an item (like an SQL column)
#
#   KEY DIFFERENCE from SQL: Items in the same table can have
#   DIFFERENT attributes. No rigid schema. Item #1 can have
#   "author" while item #2 doesn't — both are fine.
#
#   ┌───────────────────────────────────────────────────────────┐
#   │ Table: books                                              │
#   ├───────────────┬──────────────────┬────────────────────────┤
#   │ book_id (PK)  │ title            │ author                 │
#   ├───────────────┼──────────────────┼────────────────────────┤
#   │ "book-001"    │ "1984"           │ "George Orwell"        │
#   │ "book-002"    │ "Dune"           │ "Frank Herbert"        │
#   │ "book-003"    │ "Neuromancer"    │ "William Gibson"       │
#   └───────────────┴──────────────────┴────────────────────────┘
#
# ── Primary Key Types ───────────────────────────────────────
#
#   Every table MUST have a primary key. Two flavors:
#
#   1. Simple Primary Key (Partition Key only):
#
#      Just one attribute uniquely identifies each item.
#
#      books table:
#        Partition Key (PK) = book_id
#        → Each book_id is globally unique
#        → get_item(book_id="book-001") returns exactly one item
#
#   2. Composite Primary Key (Partition Key + Sort Key):
#
#      Two attributes together form the unique key.
#      Same PK can appear multiple times — SK must differ.
#
#      session-history table (from the real repo):
#        Partition Key (PK) = user_id
#        Sort Key (SK)      = session_id
#
#      ┌──────────────┬────────────────┬──────────┬──────────┐
#      │ user_id (PK) │ session_id (SK)│ messages │ ttl      │
#      ├──────────────┼────────────────┼──────────┼──────────┤
#      │ "user-alice"  │ "sess-001"    │ [...]    │ 172800   │
#      │ "user-alice"  │ "sess-002"    │ [...]    │ 172800   │
#      │ "user-bob"    │ "sess-003"    │ [...]    │ 172800   │
#      └──────────────┴────────────────┴──────────┴──────────┘
#
#      → query(user_id="user-alice") returns BOTH sessions
#      → get_item(user_id="user-alice", session_id="sess-001")
#        returns exactly one item
#
#   Why composite keys? They let you QUERY efficiently.
#   "Give me all sessions for user-alice" is a fast, indexed lookup.
#   Without a composite key you'd have to SCAN the whole table.
#
# ── Query vs Scan ───────────────────────────────────────────
#
#   Query  →  Finds items by primary key (PK, and optionally SK).
#             Uses the index. Fast. Reads only matching items.
#             Cost: proportional to items RETURNED.
#
#   Scan   →  Reads EVERY item in the entire table, then filters.
#             No index used. Slow. Expensive. Avoid in production.
#             Cost: proportional to TOTAL items in table.
#
#   ┌────────────────────────┬─────────────────────────────┐
#   │ Operation              │ What It Reads               │
#   ├────────────────────────┼─────────────────────────────┤
#   │ get_item(PK, SK)       │ Exactly 1 item (O(1))       │
#   │ query(PK)              │ All items with that PK      │
#   │ query(PK, SK begins)   │ Subset of items with PK     │
#   │ scan()                 │ ENTIRE table (O(n)) — avoid │
#   └────────────────────────┴─────────────────────────────┘
#
# ── Secondary Indexes ──────────────────────────────────────
#
#   Problem: Your table PK is book_id, but you want to query
#   by author. Without an index, you'd need a full table scan.
#
#   Solution: Create a secondary index on the "author" attribute.
#
#   GSI (Global Secondary Index):
#     - Completely different partition key and optional sort key
#     - Has its OWN throughput (separate from the base table)
#     - Eventually consistent (slight delay after writes)
#     - You can create up to 20 GSIs per table
#     - Example: GSI on books table with author as PK, title as SK
#       → Now query(author="George Orwell") is fast
#
#   LSI (Local Secondary Index):
#     - SAME partition key as the base table, different sort key
#     - Shares throughput with the base table
#     - Strongly consistent reads available
#     - Must be created at table creation time (cannot add later)
#     - Max 5 LSIs per table
#     - Example: session-history with user_id PK, created_at as LSI SK
#       → query(user_id="alice", created_at > "2025-01-01") is fast
#
#   ┌──────────────────────┬────────────────┬────────────────┐
#   │                      │ GSI            │ LSI            │
#   ├──────────────────────┼────────────────┼────────────────┤
#   │ Partition key        │ Any attribute  │ Same as table  │
#   │ Sort key             │ Any attribute  │ Different      │
#   │ Throughput           │ Independent    │ Shared w/ table│
#   │ Consistency          │ Eventually     │ Strong or event│
#   │ When to create       │ Anytime        │ Table creation │
#   │ Max per table        │ 20             │ 5              │
#   └──────────────────────┴────────────────┴────────────────┘
#
# ── Read/Write Capacity Modes ───────────────────────────────
#
#   On-Demand (recommended for starting out):
#     - Pay per request. No capacity planning.
#     - Instantly scales to thousands of requests/sec.
#     - Slightly more expensive per-request, but zero waste.
#     - Great for unpredictable workloads (the backend uses this).
#
#   Provisioned:
#     - You specify Read Capacity Units (RCU) and Write Capacity Units (WCU).
#     - 1 RCU = one strongly consistent read/sec for items up to 4 KB.
#     - 1 WCU = one write/sec for items up to 1 KB.
#     - Cheaper if traffic is predictable and steady.
#     - Can enable auto-scaling to adjust RCU/WCU automatically.
#
# ── TTL (Time To Live) ──────────────────────────────────────
#
#   Automatically delete expired items at no cost.
#   Specify an attribute containing a Unix epoch timestamp.
#   DynamoDB deletes items within ~48 hours after expiration.
#
#   Real example: session-history uses TTL to auto-clean old sessions.
#   When a session is created, it sets:
#     ttl = current_time + 172800  (48 hours from now)
#
#   After 48 hours, DynamoDB silently deletes the item. No Lambda,
#   no cron job, no extra cost. This prevents unbounded table growth.
#
# ── DynamoDB Streams ────────────────────────────────────────
#
#   Captures a time-ordered sequence of item changes (insert,
#   modify, delete). Trigger a Lambda function on every change.
#
#   Use cases:
#     - Replicate data to another table or region
#     - Send notifications when items change
#     - Build materialized views / aggregations
#     - Audit trail / change log
#
#   Stream record contains: old image, new image, or both.
#
#   ┌─────────────┐     Stream      ┌──────────────┐
#   │  DynamoDB    │───────────────►│   Lambda      │
#   │  put_item()  │   (change log) │   process()   │
#   └─────────────┘                 └──────────────┘
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console → search "DynamoDB" → click it
#
#   2. Click "Create table"
#      ┌──────────────────────────────────────────────────┐
#      │  Table name:      book-store-books                │
#      │  Partition key:   book_id  (String)               │
#      │  Sort key:        (leave empty for simple PK)     │
#      │                                                    │
#      │  Table settings:  Customize settings               │
#      │  Capacity mode:   On-demand                        │
#      └──────────────────────────────────────────────────┘
#      → Create table
#
#   3. Click on your table → "Explore table items"
#      → Create item:
#      ┌──────────────────────────────────────────────────┐
#      │  book_id:  "book-001"   (String)                  │
#      │  + Add new attribute:                             │
#      │    title:   "1984"      (String)                  │
#      │    author:  "George Orwell" (String)              │
#      │    year:    1949        (Number)                  │
#      │    genres:  ["dystopian","political"] (List)      │
#      └──────────────────────────────────────────────────┘
#
#   4. Query the table:
#      → Switch from "Scan" to "Query"
#      → Partition key: book_id = "book-001" → Run
#      → Returns the single matching item instantly
#
#   5. Create a GSI:
#      → Table → Indexes tab → Create index
#      ┌──────────────────────────────────────────────────┐
#      │  Partition key:  author (String)                   │
#      │  Sort key:       title  (String)                   │
#      │  Index name:     author-title-index                │
#      │  Projected attributes: All                        │
#      └──────────────────────────────────────────────────┘
#      → Now you can query by author efficiently
#
# ── Boto3 Examples ──────────────────────────────────────────
#
#   import boto3
#   from boto3.dynamodb.conditions import Key
#
#   dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
#   table = dynamodb.Table("book-store-books")
#
#   # Put an item (create/overwrite)
#   table.put_item(Item={
#       "book_id": "book-001",
#       "title": "1984",
#       "author": "George Orwell",
#       "year": 1949
#   })
#
#   # Get a single item by primary key
#   response = table.get_item(Key={"book_id": "book-001"})
#   book = response["Item"]  # {"book_id": "book-001", "title": "1984", ...}
#
#   # Query (composite key table — e.g., session-history)
#   sessions_table = dynamodb.Table("session-history")
#   response = sessions_table.query(
#       KeyConditionExpression=Key("user_id").eq("user-alice")
#   )
#   sessions = response["Items"]  # All sessions for alice
#
#   # Query with sort key filter
#   response = sessions_table.query(
#       KeyConditionExpression=(
#           Key("user_id").eq("user-alice") &
#           Key("session_id").begins_with("sess-2025")
#       )
#   )
#
#   # Update an item (partial update — only changes specified attrs)
#   table.update_item(
#       Key={"book_id": "book-001"},
#       UpdateExpression="SET #yr = :y, rating = :r",
#       ExpressionAttributeNames={"#yr": "year"},  # "year" is reserved word
#       ExpressionAttributeValues={":y": 1949, ":r": 4.8}
#   )
#
#   # Delete an item
#   table.delete_item(Key={"book_id": "book-001"})
#
# ── Cost ────────────────────────────────────────────────────
#
#   On-Demand pricing (eu-west-1):
#     Write: $1.25 per million write request units
#     Read:  $0.25 per million read request units
#     Storage: $0.25 per GB per month
#
#   Example (book-store, low traffic):
#     1,000 writes/day × 30 = 30,000 writes/month = $0.04
#     5,000 reads/day × 30  = 150,000 reads/month = $0.04
#     Data stored: 50 MB = $0.01
#     Total: ~$0.09/month (essentially free)
#
#   Example (backend session-history, moderate traffic):
#     50,000 writes/day × 30 = 1.5M writes/month = $1.88
#     200,000 reads/day × 30 = 6M reads/month    = $1.50
#     Data stored: 5 GB (with TTL cleanup) = $1.25
#     GSI: adds ~30% to write costs
#     Total: ~$6/month
#
#   Free tier: 25 GB storage + 25 WCU + 25 RCU provisioned
#   (on-demand has a separate free tier of 2.5M read + 1M write/mo)
#
# ── Common Gotchas ──────────────────────────────────────────
#
#   1. 400 KB item size limit. You CANNOT store a 1 MB JSON blob
#      in a single item. The agent-checkpoints table works around
#      this by offloading large state to S3 and storing the S3 key.
#
#   2. 1 MB query result limit. A single query returns max 1 MB
#      of data. If there's more, you get a LastEvaluatedKey —
#      pass it as ExclusiveStartKey to paginate.
#
#   3. Hot partitions. If one partition key gets way more traffic
#      than others, that partition throttles. Design keys to
#      distribute evenly (don't use "status" as PK — only a few
#      values, most traffic hits "active").
#
#   4. GSI eventual consistency. After a write to the base table,
#      the GSI may take milliseconds to seconds to reflect it.
#      If you write then immediately query the GSI, you might
#      get stale data.
#
#   5. Reserved words. "year", "name", "status", "data" are
#      reserved. Use ExpressionAttributeNames (#yr for year)
#      in update/query expressions.
#
#   6. No native joins. If you need relational queries, either
#      denormalize (store redundant data) or use a relational
#      database (RDS/Aurora) instead.
#
#   7. Scans are expensive. A scan on a 1 GB table reads ALL
#      1 GB even if you only want 10 items. Always prefer
#      query with a proper key design over scan with a filter.
