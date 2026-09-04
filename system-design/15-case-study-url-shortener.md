# Case Study: Design a URL Shortener

*The single most-asked system design question — a great first case
study because it touches almost every fundamental chapter without
being overwhelming.*

---

## ELI5

You want `bit.ly/xk29a` to remember `https://a-really-long-url.com/...`
and take anyone who visits it straight to the long one — like a
nickname for a friend's very long full name, that anyone can shout out
and have people know exactly who's meant.

---

## 1. Requirements

**Functional:**
- Given a long URL, generate a short one.
- Given a short URL, redirect to the original long URL.
- (Optional) Let a user pick a custom short code, and set an expiry.

**Non-functional** (from `01-what-is-system-design.md`):
- Read-heavy: far more redirects (reads) happen than new URLs created (writes).
- Redirect must be FAST — nobody waits happily for a link to resolve.
- Short codes must be unique and unguessable-enough (not sequential/obvious).
- High availability > strong consistency (a link should basically always work).

## 2. Estimate

```
New URLs/day:         1,000,000 (writes)
Redirects/day:        100,000,000 (100x reads, read-heavy — see ch.01)
Reads per second:     ~1,200 avg, ~5,000 peak
Storage per record:   ~500 bytes → 5 years of writes ≈ ~1 TB total
                       (small — storage is NOT the bottleneck here)
```

Conclusion: this is a **read-latency and read-throughput problem, not
a storage problem** — design decisions should optimize for fast reads.

## 3. High-Level Design

```
                     ┌──────────────┐
  Client ───────────▶│ Load Balancer │  (ch.03)
                     └──────┬───────┘
                            ▼
                    ┌───────────────┐
                    │  App Servers   │  (stateless — ch.02)
                    └───────┬───────┘
                     ┌───────┴────────┐
                     ▼                ▼
              ┌────────────┐   ┌──────────────┐
              │ Cache (LRU)│   │  Database      │  (ch.04, ch.05)
              │  short→long│   │  short_code →  │
              └────────────┘   │  long_url      │
                                └──────────────┘
```

## 4. Deep Dive: Generating the Short Code

This is the interesting part interviewers dig into.

```
OPTION A: Auto-increment counter + base62 encode
──────────────────────────────────────────────────
  1, 2, 3, 4, ... → base62 → "1", "2", "3", "4"... "10" ... "zzz"
  (base62 = 0-9, a-z, A-Z → 62 characters, very compact codes)

  + Simple, guaranteed unique, short codes stay short for a long time
  - A single counter is a bottleneck/coordination point at scale
    (fix: give each app server a pre-allocated RANGE of the counter,
    like server 1 owns 1-1000, server 2 owns 1001-2000, so no
    coordination is needed per-request)
  - Sequential codes are guessable/enumerable (fix: shuffle/obfuscate
    the base62 output, don't expose it in creation order)

OPTION B: Hash the long URL (e.g. MD5/SHA, take first 7 chars)
──────────────────────────────────────────────────────────────
  + No coordination needed, same URL can even map to the same code
  - Collisions ARE possible with a short prefix — must check for
    collision and re-hash (e.g. append a salt) if one occurs

OPTION C: Random string, check DB for collision
──────────────────────────────────────────────────
  + Simple, unguessable
  - Gets slower as the keyspace fills up (fix: pre-generate a pool
    of unused random codes ahead of time, hand them out from that pool)
```

**Recommended answer:** Option A (range-partitioned counter) is the
cleanest — no collision handling needed, and the "coordination
bottleneck" concern is solved cheaply by pre-allocating ranges per server.

### Read Path (the hot path — optimize this hardest)

```
1. Request hits /r/xk29a
2. Check cache (ch.04) for "xk29a" → HIT (~99% of the time, since a
   small % of links get most of the traffic — cache the popular ones)
3. Cache MISS → query DB, then POPULATE the cache for next time
4. Return HTTP 301/302 redirect to the long URL
```

301 (permanent) vs 302 (temporary) redirect is a real trade-off:
301 lets BROWSERS cache the redirect themselves (even less load on
your servers on repeat visits), but makes it harder to change the
destination later or track click analytics accurately.

### Scaling Further

- **Database**: read replicas (ch.06) since this is read-heavy; the
  write path (creating new short URLs) is low volume and doesn't need
  sharding at this scale (1TB total, remember).
- **Geographic**: put the redirect service behind a CDN/edge layer
  (ch.11) so the redirect itself happens close to the user.

---

## Interview Angle

The interviewer is watching whether you: (1) asked about read/write
ratio before designing, (2) picked a code-generation strategy AND
explained its trade-off, (3) put a cache in the read path without
being told to, and (4) reasoned about scale numbers instead of just
drawing boxes.

## Gotchas

1. Don't default to random-string-with-collision-check without
   mentioning the slowdown as the keyspace fills — always pair it with
   a mitigation (pre-generated pool).
2. Forgetting to cache the READ path is the most common miss — this
   system is defined by being read-heavy; the design MUST reflect that.
3. Ignoring expiry/deletion — if links can expire, that's either a
   background cleanup job or a lazy check at read time; say which.
4. Treating this as "just a database problem" — the interesting parts
   are code generation and read-path caching, not the schema.
