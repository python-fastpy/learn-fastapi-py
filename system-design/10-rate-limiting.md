# Rate Limiting & Throttling

---

## ELI5

A bouncer outside a small club only lets in 1 person per minute, no
matter how big the crowd outside gets. It's not that the club hates
people — if everyone rushed in at once, the club would get so crowded
nobody could move. The bouncer protects the people ALREADY inside.

**Rate limiting is that bouncer**, applied to API requests instead of
people.

---

## The Real Thing

### Why It Exists

1. **Protect the backend** from being overwhelmed (accidentally by a
   buggy client retry loop, or intentionally by an attack).
2. **Fairness** — one client hammering the API shouldn't starve
   everyone else of capacity.
3. **Cost control** — every request costs compute/money; unbounded
   usage from one client is a real bill, not just a theoretical concern.

### Algorithms

```
TOKEN BUCKET
────────────
  Bucket holds up to N tokens, refills at a steady rate.
  Each request consumes 1 token. No tokens left → request rejected/queued.

  ┌─────────┐   refill 1 token/sec
  │ ● ● ● ● │ ◀───────────────────
  │ bucket  │   (max capacity 10)
  └─────────┘
  request arrives → take 1 token → if bucket empty, reject (429)

  Allows short BURSTS up to the bucket size, then settles to the
  steady refill rate — this is the most commonly used algorithm because
  it tolerates real traffic (which is bursty, not perfectly smooth).
```

```
LEAKY BUCKET                          FIXED WINDOW COUNTER
────────────                          ─────────────────────
Requests queue up, processed          Count requests in the current
at a FIXED steady rate (like a         fixed clock window (e.g. this
bucket with a hole leaking at a        minute). Reset to 0 each window.
constant rate) — smooths bursts       Simple, but has a BOUNDARY BUG:
into a steady output instead of        a client can send N requests at
allowing them through                  11:00:59 and another N at
                                        11:01:00 → 2N requests in 1 real
                                        second, right at the window edge
```

```
SLIDING WINDOW (fixes the boundary bug)
────────────────────────────────────────
Instead of a hard reset at each clock boundary, weight the previous
window's count by how much it overlaps the current sliding window.
More accurate, slightly more computation/memory.
```

### Where Enforcement Happens

```
Client ──▶ CDN/Edge (ch.11) ──▶ API Gateway (ch.09) ──▶ App server
             │                     │
    can reject obviously      the MOST COMMON place —
    abusive traffic before    centralizes the limiting logic
    it even reaches your      instead of duplicating it in
    infrastructure            every single service
```

### Where the Counter State Lives

If you have multiple app servers behind a load balancer (ch.03), the
rate-limit COUNT can't just live in one server's memory — server A
doesn't know what server B has already counted for the same client.
The counter needs to live in a **shared, fast store** — Redis is the
standard choice (`INCR` + a short `EXPIRE` is a simple token-bucket-ish
implementation in about 2 lines).

### What the Client Sees

A well-designed API tells the client where it stands, instead of just
failing unpredictably:

```
HTTP/1.1 429 Too Many Requests
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
Retry-After: 42
```

---

## Interview Angle

**Expect this framing:** "How would you prevent one client from
overwhelming your API?" or it shows up as a natural follow-up after
you draw the API Gateway box in a bigger design.

**Model answer:** "Token bucket per client (identified by API key or
user ID), enforced at the gateway, with counters in Redis so it works
correctly across multiple app server instances. Return 429 with a
`Retry-After` header so clients can back off gracefully."

**See `system-design/16-case-study-rate-limiter.md`** for the full
end-to-end design of rate limiting AS a standalone distributed service.

---

## Gotchas

1. Fixed window counters have the boundary-burst bug above — mention
   sliding window or token bucket if precision matters.
2. Rate-limit state in a single server's local memory silently breaks
   the moment you have more than one server — always say where the
   shared counter lives.
3. Limiting by IP address alone breaks for users behind a shared
   corporate NAT (many real users, one IP) — prefer API key/user ID
   when available, IP as a fallback.
4. Returning a bare `403`/`500` on rate-limit instead of `429` with
   `Retry-After` forces well-behaved clients to guess when to retry —
   always include that header.
