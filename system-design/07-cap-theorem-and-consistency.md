# CAP Theorem & Consistency Models

---

## ELI5

You and a friend are on a phone call, each writing down a shared to-do
list. The call drops (a **network partition**). Do you:

- **(A) Stop writing anything new until the call reconnects**, so your
  lists never disagree? → you're choosing **Consistency**.
- **(B) Keep writing on your own copy**, and reconcile the two lists
  once the call reconnects, accepting they might briefly disagree? →
  you're choosing **Availability**.

You cannot do both perfectly during the dropped call. That's the whole
theorem in one phone call.

---

## The Real Thing

### CAP: Pick 2 of 3 — but really, Partition Tolerance isn't optional

```
        Consistency (C)              Every read gets the
              /\                     MOST RECENT write, or an error
             /  \
            /    \
           /      \
Availability (A)──Partition Tolerance (P)
Every request gets       The system keeps working
a response (even if      even when network messages
not the latest data)     between nodes are lost/delayed
```

In any REAL distributed system, network partitions (P) WILL happen
eventually — a cable gets cut, a data center loses connectivity. So the
real-world choice is actually just **C vs. A when a partition occurs**:

```
CP system (choose Consistency)         AP system (choose Availability)
────────────────────────────           ────────────────────────────
During a partition, nodes that         During a partition, ALL nodes
can't confirm they have the             keep serving requests, even
latest data REFUSE to respond           knowing the answer might be
(better to say nothing than lie)        slightly stale
Example: many traditional               Example: DNS, many NoSQL
  relational/banking systems              databases (Cassandra, DynamoDB)
```

### Strong vs. Eventual Consistency (the practical version of this)

```
STRONG CONSISTENCY                    EVENTUAL CONSISTENCY
────────────────────                  ────────────────────
Every read gets the latest write,     A write is accepted immediately;
  no matter which replica you hit       reads MIGHT see an older value
Requires coordination between          for a short window, until the
  replicas before confirming a write    update propagates everywhere
Slower writes (must sync first)        Fast writes, fast everywhere-reads
Example: a bank balance                Example: a "like" count, or a
                                          social media follower count
```

```
Timeline of an eventually-consistent write:

t=0    write "count=101" to Node A
t=0    Node B still has "count=100"  ← a read here sees the OLD value
t=50ms replication finishes
t=50ms Node B now has "count=101"    ← now consistent
```

That gap between t=0 and t=50ms is the "eventual" part — it converges,
just not instantly.

### Related Consistency Guarantees Worth Naming

- **Read-your-writes**: after YOU write something, YOU always see it
  (even if others might not yet) — a common middle ground.
- **Causal consistency**: if event B happened because of event A,
  everyone sees A before B (but unrelated events can appear in any order).

---

## Interview Angle

**Expect this framing:** "Does this system need strong or eventual
consistency?" — this is one of the most reliable "are they thinking
correctly" questions. The answer depends entirely on the DATA, not a
personal preference.

**Model answers:**
- Bank balance / inventory count for the last item in stock → **strong**
  consistency (showing the wrong number causes real problems: overselling,
  double-spending).
- Social media like count, view count, "user is online" status →
  **eventual** consistency is totally fine (being off by a few for a
  second doesn't hurt anyone).

---

## Gotchas

1. CAP is about behavior DURING a partition — outside of a partition,
   most systems can be both available and consistent. Don't imply
   you're always sacrificing one.
2. "NoSQL = AP, SQL = CP" is a rough generalization, not a law — many
   databases let you TUNE this per-query (e.g. requesting a stronger
   read consistency level on a normally-AP database).
3. Confusing CAP's "Consistency" with ACID's "Consistency" — they mean
   different things (CAP: all nodes see the same data; ACID: a
   transaction leaves the DB in a valid state). Don't conflate them.
4. Not every field in one system needs the same consistency level — a
   chat app might need strong consistency for message ordering but
   eventual consistency for "last seen" timestamps.
