# Databases: SQL vs. NoSQL

---

## ELI5

A **SQL database** is a strict filing cabinet: every folder (table) has
labeled slots (columns), and every piece of paper (row) MUST fill in
every slot the same way. Great for keeping things consistent, but
rigid — adding a new slot means redesigning every folder.

A **NoSQL database** is a pile of labeled sticky notes: each note can
have whatever information you want on it, in whatever shape. Fast to
add new kinds of notes, but nothing forces them to stay consistent
with each other.

---

## The Real Thing

### Relational (SQL)

```
users table                    orders table
┌────┬────────┬───────┐        ┌────┬─────────┬──────────┐
│ id │ name   │ email │        │ id │ user_id │ total    │
├────┼────────┼───────┤        ├────┼─────────┼──────────┤
│ 1  │ Alice  │ a@... │        │ 101│ 1       │ 49.99    │
│ 2  │ Bob    │ b@... │        │ 102│ 1       │ 12.00    │
└────┴────────┴───────┘        └────┴─────────┴──────────┘
        ▲                              │
        └────── user_id (foreign key) ─┘
   JOIN users ON orders.user_id = users.id
```

Fixed schema, relationships enforced via foreign keys, and **ACID**
transactions (Atomicity, Consistency, Isolation, Durability) guarantee
a multi-step operation (like "transfer money between two accounts")
either fully happens or fully doesn't — never half-way.

### NoSQL — Four Common Shapes

| Type | Shape | Example use | Example DB |
|---|---|---|---|
| **Key-Value** | `key → blob` | Session storage, caching | Redis, DynamoDB |
| **Document** | `key → JSON-like nested doc` | User profiles, catalogs (flexible fields) | MongoDB |
| **Column-family** | Rows with huge, sparse, varying columns | Time-series, huge write volume | Cassandra, HBase |
| **Graph** | Nodes + edges | Social networks, recommendations | Neo4j |

```
Document example (MongoDB-style):
{
  "_id": "user_1",
  "name": "Alice",
  "orders": [
    { "id": 101, "total": 49.99 },
    { "id": 102, "total": 12.00 }
  ]
}
← the whole "user + their orders" is ONE document, no JOIN needed
```

### The Real Trade-off

```
SQL                                    NoSQL
────────────────────                   ────────────────────
Strong consistency, ACID               Flexible/no fixed schema
Great for complex relationships         Great for huge write volume
  (JOINs across many tables)             and horizontal scale
Schema changes = migrations             Schema changes = just add a field
Vertical scaling is easier;             Built to shard/scale horizontally
  horizontal (sharding) is harder        from the start
Best when data integrity/               Best when speed/flexibility
  relationships matter most              matters more than strict structure
```

**This is not "NoSQL is faster/newer/better"** — it's a genuinely
different trade-off. A bank's ledger needs SQL-style ACID guarantees. A
social media "like" counter can tolerate NoSQL's looser guarantees in
exchange for effortless horizontal scale.

---

## Interview Angle

**Expect this framing:** "Would you use SQL or NoSQL for this?" — the
weak answer picks one dogmatically. The strong answer asks: "does this
data have complex relationships that need transactions/JOINs, or is it
mostly independent records that need to scale to huge write volume?"

**Model answer for a chat app:** "Messages themselves fit a document
or wide-column store well — they're mostly independent, high write
volume, don't need cross-message transactions. But user accounts and
billing probably still want SQL, for the consistency guarantees." Many
real systems use BOTH — this is called **polyglot persistence**.

---

## Gotchas

1. "NoSQL scales better" is not universally true — it's that NoSQL
   databases are usually DESIGNED to shard easily; some SQL databases
   (with effort, see ch.06) scale plenty for most systems.
2. Don't say "NoSQL has no schema" as if that's purely a benefit — it
   means the APPLICATION has to enforce consistency instead of the DB,
   which is a real cost, not a free lunch.
3. Losing ACID transactions is a real trade-off, not a footnote — if a
   design needs "transfer money atomically," that's a strong signal
   toward SQL (or a NoSQL DB with limited multi-document transaction
   support).
4. Don't pick a database type before you've stated the access
   pattern — "how is this data read/written" should come before
   "which database."
