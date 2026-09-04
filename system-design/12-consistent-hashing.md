# Consistent Hashing

---

## ELI5

A school has 4 lunch tables, and kids are assigned to a table by
`kid_number % 4`. Adding a 5th table changes almost EVERY kid's table
number (`% 4` → `% 5` reshuffles nearly everyone), even though only one
new table showed up.

**Consistent hashing** is a smarter seating chart: kids and tables are
both placed around a big circle. Each kid just walks clockwise to the
nearest table. Adding a 5th table only affects the FEW kids who happen
to be closest to where the new table appears — everyone else stays put.

---

## The Real Thing

### The Problem It Solves

```
NAIVE HASHING: server = hash(key) % N

  N=4 servers: key "cat" → hash=13 → 13 % 4 = 1  → Server 1
  N=5 servers: key "cat" → hash=13 → 13 % 5 = 3  → Server 3  ← MOVED!

  Adding/removing ONE server reshuffles the mapping for almost
  EVERY key → in a cache (ch.04) or sharded database (ch.06), that
  means a near-total cache wipe or mass data migration just to add
  one more node.
```

### The Ring

```
            0°
            │
    Server D┤              Server A
      ●     │                  ●
            │
   270°─────┼─────── 90°
            │
      ●     │              ●
    Server C│              Server B
           180°

  1. Hash each SERVER onto a position on the ring (0°-360°, or a big
     number space like 0-2^32).
  2. Hash each KEY the same way.
  3. A key belongs to whichever server is the NEXT one clockwise
     from the key's position.
```

```
Adding a new server (Server E) between B and C on the ring:

  Server D ── Server A ── Server B ── [Server E] ── Server C ── (back to D)

  ONLY the keys that used to map to Server C, but now fall between
  B and E, move to Server E. Server D, A, B's keys are UNTOUCHED.
```

That's the entire point: **adding or removing one node only remaps the
keys near it on the ring**, not the whole keyspace.

### Virtual Nodes (fixing uneven distribution)

With very few real servers, they can land unevenly on the ring by pure
chance (imagine A, B, C landing right next to each other — C would own
almost nothing, A would own most of the ring). The fix: give each
physical server MANY positions on the ring (virtual nodes), so the
ring is densely and evenly covered no matter how few physical servers
there are.

```
Server A → hashed to 5 different positions: A1, A2, A3, A4, A5
Server B → hashed to 5 different positions: B1, B2, B3, B4, B5
(spread evenly around the ring instead of 2 lumps)
```

### Where This Actually Shows Up

- **Distributed caches** (Memcached clients, Redis Cluster) — deciding
  which cache node owns which key.
- **Sharded databases** (ch.06) — deciding which shard owns which row,
  without a full re-shard every time a node is added.
- **Load balancers** routing to a fixed backend for session affinity
  without needing shared session storage (a less common use).

---

## Interview Angle

**Expect this framing:** "How do you add/remove a cache/database node
without re-shuffling everything?" — this is almost always the exact
trigger phrase for consistent hashing.

**Model answer:** "Instead of `hash(key) % N`, place both servers and
keys on a hash ring; each key maps to the next server clockwise. Adding
or removing a node only affects the keys in its immediate neighborhood
on the ring, not the whole dataset. I'd also use virtual nodes to keep
the load evenly distributed across physical servers."

---

## Gotchas

1. Don't describe consistent hashing as "no data ever moves" — SOME
   data still moves (the keys near the changed node); the win is that
   it's a small fraction, not everything.
2. Without virtual nodes, a small number of physical servers can land
   unevenly and create "hot" nodes — always mention virtual nodes as
   the fix if the interviewer probes on load distribution.
3. This solves REBALANCING cost, not replication — you still need a
   separate strategy (ch.06) for how many copies of each key/shard
   exist for fault tolerance.
4. Confusing this with plain `hash(key) % N` — if you can't clearly
   state WHY modulo hashing breaks on resize, you haven't actually
   demonstrated understanding of the "why," only the buzzword.
