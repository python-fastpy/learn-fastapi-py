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
KEY LOOKUP — walking the ring  (A=45°, B=135°, C=225°, D=315°)
  ① hash("cat") ──▶ position 100°  (same hash function as the servers)
        │
        ▼
  ② search sorted server positions for the first one ≥ 100°
        │
        ▼
  ③ found B (135°) ──▶ ✓ "cat" lives on Server B
        │  (key at 330°? nothing ≥ 330° → wrap past 360° to A at 45°)
        ▼
  ④ client/router sends GET cat ──▶ Server B
```

```
Adding a new server (Server E) between B and C on the ring:

  Server D ── Server A ── Server B ── [Server E] ── Server C ── (back to D)

  ONLY the keys that used to map to Server C, but now fall between
  B and E, move to Server E. Server D, A, B's keys are UNTOUCHED.
```

```
ADDING SERVER E — step by step  (B=135°, new E=180°, C=225°)
  ① hash("Server E") ──▶ 180°, insert E into the ring
        │
        ▼
  ② E's clockwise successor ──▶ Server C (225°) — the only donor
        │
        ▼
  ③ keys in (135°, 180°] move  C ──▶ E
        │
        ▼
  ④ ✓ lookups for those keys now stop at E
     ✓ keys in (180°, 225°] stay on C;  A, B, D untouched
```

That's the entire point: **adding or removing one node only remaps the
keys near it on the ring**, not the whole keyspace.

```
REMOVING SERVER B — step by step  (original ring A, B, C, D)
  ① B (135°) fails or is decommissioned ──▶ removed from the ring
        │
        ▼
  ② B's keys, range (45°, 135°], now walk clockwise past 135° ...
        │
        ▼
  ③ ... to the next server ──▶ Server C (225°) takes them over
        │
        ▼
  ④ ✓ only B's range moves (to C);  A's and D's keys stay put
     ✗ with hash % N, dropping to N=3 would remap almost every key
```

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

```
LOOKUP WITH VIRTUAL NODES
  ① hash("cat") ──▶ position on the ring
        │
        ▼
  ② next point clockwise ──▶ virtual node B3
        │
        ▼
  ③ map virtual → physical:  B3 ──▶ Server B  ──▶ ✓ "cat" lives on B
        │
        ▼
  ④ if Server B dies: B1..B5 vanish, each small range falls to its own
     next point clockwise → load spreads over the survivors, not one
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
