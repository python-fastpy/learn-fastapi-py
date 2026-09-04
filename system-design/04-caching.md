# Caching

---

## ELI5

If you want a snack every 10 minutes, you don't walk to the kitchen
each time — you keep a bowl of chips on your desk. Refilling the bowl
occasionally is way cheaper than 100 trips to the kitchen.

The bowl on your desk is a **cache**: a smaller, faster copy of data
that lives closer to where it's needed, so you don't hit the slow
"real" source (the kitchen/database) every single time.

---

## The Real Thing

### Where Caches Live

```
Browser cache          CDN edge cache        Server-side cache        Database
(client's disk)   →    (near the user,   →   (Redis/Memcached,   →    (the source
                        e.g. a city over)      near the app servers)   of truth)
   fastest, but             fast, shared         fast, shared          slowest,
   only helps that           across many          across all your      but always
   one user                  users in a region     app servers          correct
```

Each layer you add removes load from everything behind it — a well-hit
CDN cache means your database barely notices traffic spikes.

### Cache Population Strategies

```
CACHE-ASIDE (lazy loading)             WRITE-THROUGH
──────────────────────────             ──────────────
1. App asks cache for data             1. App writes data
2. MISS → app reads DB itself          2. Write goes to cache AND DB
3. App writes result INTO the cache      at the same time (or cache
4. Next read = cache HIT                  first, then DB)
                                        3. Cache is always up to date
Simple, cache only holds what's        Slower writes (2 writes happen),
actually requested                     but reads are never stale right
First request after a miss is slow     after a write
("cold start" / "thundering herd"      GOOD when reads-after-writes must
 if many requests miss at once)        be fresh
```

```
WRITE-BACK (write-behind)              READ-THROUGH
──────────────────────────             ──────────────
1. App writes to CACHE only            Looks like cache-aside from the
2. Cache asynchronously flushes to      app's point of view, but the
   the DB later (batched)              CACHE ITSELF (not the app) is
Fast writes, but data can be LOST       responsible for loading from
if the cache crashes before flushing    the DB on a miss — common in
                                         managed caching layers
```

### Cache Invalidation — "the hard problem"

There's an old joke: *"There are only two hard things in computer
science: cache invalidation, and naming things, and off-by-one errors."*
Stale cached data being served as if it were fresh is a real, constant
risk.

```
TTL (Time To Live)          EXPLICIT INVALIDATION       EVENT-DRIVEN
────────────────────         ──────────────────────      ─────────────
Data auto-expires after      App deletes/updates the      A write publishes
N seconds, next read           cache key the moment the    an "invalidate"
re-fetches from source          underlying data changes     event (see ch.08)
                                                             that other
Simple, but data can be      Correct, but you must find    services subscribe
stale for up to N seconds      EVERY place that can change    to and react to
                                that data — easy to miss one
```

### Eviction — what happens when the cache is FULL

You can't cache everything forever — memory is limited. **LRU (Least
Recently Used)** is the standard eviction policy: throw out whatever
hasn't been touched in the longest time. See `DSA/12-lru-cache.js` in
this repo for a full from-scratch implementation of exactly this
algorithm — it's both an interview data-structure question AND the real
mechanism inside Redis/Memcached.

---

## Interview Angle

**Expect this framing:** "This system is read-heavy — how would you
speed up reads?" is basically always answerable with "add a cache
layer," but the interviewer wants to hear you pick a strategy (cache-
aside is the safe default) AND name an invalidation approach AND
mention eviction (LRU) once memory fills up.

**Model answer:** "Cache-aside with a TTL as a safety net, plus explicit
invalidation on writes to the same key, backed by Redis with LRU
eviction since memory is finite."

---

## Gotchas

1. Caching solves READ load, not write load — don't reach for caching
   when the bottleneck is write throughput.
2. Cache-aside's first request after a cache restart/expiry can cause a
   "thundering herd" (everyone misses at once, DB gets hammered) —
   mention request coalescing/locking as the fix if pressed.
3. Forgetting invalidation entirely is the most common mistake — always
   say explicitly how stale data gets cleared, not just how it gets cached.
4. A cache that's too small just thrashes (constant eviction, low hit
   rate) — sizing the cache to the actual "hot" working set matters.
