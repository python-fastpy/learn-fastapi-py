# Database Scaling: Replication & Sharding

---

## ELI5

**Replication** is like photocopying a book and putting a copy in
several libraries across town — everyone reads from whichever copy is
closest, and if one library burns down, the others still have it.

**Sharding** is different: instead of copying the WHOLE book, you rip
it into volumes — Volume A-M goes to one library, Volume N-Z goes to
another. No single library holds the whole book anymore, but together
they do, and each library only has to manage half as much.

---

## The Real Thing

### Replication (copies of the SAME data)

```
                    ┌──────────┐
   writes ─────────▶│  LEADER  │  (a.k.a. primary/master)
                     └────┬─────┘
              replicates changes to
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │FOLLOWER 1│ │FOLLOWER 2│ │FOLLOWER 3│  (a.k.a. replicas/slaves)
        └──────────┘ └──────────┘ └──────────┘
              ▲            ▲            ▲
           reads ◀───── reads ◀───── reads
```

- **All writes go to the leader** (there's one source of truth for writes).
- **Reads can go to any follower** — this is HOW you scale a read-heavy
  workload (ch.01's "reads >>> writes" estimate) without touching the
  write path at all.
- **Replication lag**: followers are updated *slightly* after the
  leader — a follower can briefly serve stale data. This is the
  "eventual consistency" trade-off from ch.07.
- If the leader dies, one follower is promoted (failover, see ch.13).

### Sharding / Partitioning (splitting DIFFERENT data across machines)

```
              ┌───────────────┐
   query ────▶│ Shard router /  │
              │  application    │
              └────────┬────────┘
       ┌────────────────┼────────────────┐
       ▼                ▼                ▼
 ┌───────────┐   ┌───────────┐   ┌───────────┐
 │ Shard 1    │   │ Shard 2    │   │ Shard 3    │
 │ users A-H  │   │ users I-Q  │   │ users R-Z  │
 └───────────┘   └───────────┘   └───────────┘
```

**Sharding key** choice matters enormously:
- By user ID range (as above): simple, but can create "hot shards" if
  some letters/ranges are far more active than others.
- By hash of user ID: spreads load evenly, but range queries ("give me
  all users A-H") now have to ask EVERY shard.
- Geographic (US shard, EU shard): great for latency and data residency
  laws, bad if a huge % of users are in one region.

**The cost of sharding**: queries that need data from multiple shards
(e.g. a JOIN across two users on different shards) become slow or
impossible without extra coordination — this is the #1 reason teams
delay sharding as long as possible and reach for replication + a
bigger leader first.

### Indexing (a smaller, related idea)

An index is a separate, sorted lookup structure so the database doesn't
have to scan every single row to find a match — conceptually the same
trade-off as a book's index: a bit of extra storage and slower writes
(the index must also update), for much faster reads/lookups.

```
WITHOUT INDEX: scan all 10M rows to find email="a@b.com"   → O(n)
WITH INDEX:    binary search a sorted structure              → O(log n)
```

---

## Interview Angle

**Expect this framing:** "Your single database is struggling under
load — what do you do?" The strong answer distinguishes READ load
(add read replicas — cheap, simple) from WRITE load (much harder —
sharding, or picking a database designed to shard, see ch.05).

**Model answer:** "First check if it's reads or writes. If reads:
add replicas behind the load balancer, accept eventual consistency.
If writes: that's a harder problem — I'd shard by [key], accepting
that cross-shard queries get more complex."

---

## Gotchas

1. Replication scales READS, not writes — all writes still go through
   one leader. Don't propose replication as a fix for write-heavy load.
2. Sharding is a one-way door in practice — re-sharding a live system
   with a bad key choice is one of the most painful operations in
   distributed systems. Say you'd pick the key carefully up front.
3. "Just add an index" isn't free — every index slows down writes
   (the index has to be updated too) and costs storage.
4. Replication lag means a user can write something, immediately read
   it back from a follower, and NOT see their own write — this is a
   real, common bug class ("read-your-writes consistency" — see ch.07).
