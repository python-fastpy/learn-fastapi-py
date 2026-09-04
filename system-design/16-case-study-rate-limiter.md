# Case Study: Design a Rate Limiter

*Ties directly back to `10-rate-limiting.md` — this case study asks you
to build rate limiting as its own standalone, reusable, distributed
service, not just a feature bolted onto one API.*

---

## ELI5

Instead of every single club in town hiring its own bouncer and
training them differently, imagine ONE professional bouncer service
that any club can call: "hey, has this person already used their entry
for this minute?" One shared answer, used everywhere.

---

## 1. Requirements

**Functional:**
- Given a client identifier (API key/user ID/IP) and an action, decide
  ALLOW or REJECT based on how many requests that client has recently made.
- Must work correctly even though MANY app servers are checking limits
  for the SAME client at the same time.

**Non-functional:**
- The rate limiter check itself must be very fast (it's on the hot path
  of EVERY request) — adding meaningful latency defeats the purpose.
- Must be accurate enough to actually protect the backend, but perfect
  precision isn't required (a client getting 101 requests through
  instead of exactly 100 is an acceptable trade-off for speed).
- Must survive the rate limiter's own storage layer being briefly slow
  without taking down all API traffic.

## 2. Estimate

```
Peak API requests across the platform:  ~50,000 req/sec
Each request needs ONE rate-limit check → the limiter itself must
handle 50,000 checks/sec with sub-millisecond latency.
```

This single number rules out anything that hits a slow disk-based
database per check — it points straight at an in-memory store.

## 3. High-Level Design

```
  Client ──▶ API Gateway (ch.09) ──▶ Rate Limiter check ──▶ App Server
                                            │
                                            ▼
                                    ┌────────────────┐
                                    │  Redis (shared,   │  (ch.02's
                                    │  in-memory store)  │  statelessness
                                    └────────────────┘   problem, solved)
```

Enforcing at the **API Gateway**, not inside each individual service,
means every service gets rate limiting for free without duplicating
the logic (this is exactly the API Gateway's job from ch.09).

## 4. Deep Dive: The Algorithm & the Storage

**Algorithm choice (from ch.10): Token Bucket.** It's the standard
choice because real traffic is bursty, and token bucket tolerates
short bursts while still enforcing a steady long-term rate — a fixed
window counter's boundary-burst bug (ch.10) is a real correctness
problem here, not a nitpick.

```
Redis implementation sketch (token bucket, per client key):

  key = f"ratelimit:{client_id}"

  On each request:
    1. tokens_left = GET key  (or initialize to max capacity if absent)
    2. If tokens_left > 0:
         DECR key
         ALLOW, set EXPIRE on key to refill window if not already set
       Else:
         REJECT with 429 + Retry-After header
```

Redis is chosen specifically because: (1) it's in-memory → fast enough
for the 50,000/sec target, (2) it's SHARED across all app server
instances → solves the exact multi-server counter problem from ch.02
and ch.10, (3) it supports atomic `INCR`/`DECR` → no race condition
between two servers checking the same client at the same instant.

### What Happens When Redis Itself Is Slow/Down?

This is the follow-up question that separates strong answers:

```
FAIL OPEN                              FAIL CLOSED
──────────                              ───────────
If the rate limiter can't reach          If the rate limiter can't reach
Redis, ALLOW the request anyway          Redis, REJECT the request
(availability > perfect enforcement)     (protection > availability)

Good default for most APIs — a           Good for something where
rate limiter outage shouldn't take       unrestrained traffic could
down the whole platform                  genuinely take down critical
                                          infrastructure
```

Most real systems **fail open**, because a rate limiter's job is to
protect the system from overload — the rate limiter itself becoming
the reason for an outage defeats its purpose. Explicitly choosing and
justifying this is a strong signal in an interview.

### Where Enforcement Happens: Edge vs. Origin

- **Edge/CDN-level** (ch.11): can reject obviously abusive traffic
  (e.g. a clear DDoS pattern) before it even reaches your infrastructure.
- **Gateway-level** (this design): the main, precise, per-client
  enforcement point.
- **Per-service**: rare, only for a specific expensive endpoint that
  needs a STRICTER limit than the platform-wide default.

---

## Interview Angle

Interviewers commonly follow up with: "what if this needs to work
across multiple DATA CENTERS, not just multiple servers in one DC?"
— the honest answer is that a single shared Redis becomes a
cross-region latency problem, and real systems either accept
per-region approximate limits (each region enforces its OWN slice of
the limit) or invest in a more complex distributed counting system —
naming this trade-off explicitly is the "senior" answer, not pretending
there's a clean free solution.

## Gotchas

1. Don't put the counter in each app server's local memory — that's
   the exact multi-server bug ch.02 and ch.10 warn about; always name
   Redis (or equivalent shared store) explicitly.
2. Not addressing "what if the rate limiter's own storage fails" is a
   common gap — always state fail-open vs. fail-closed and why.
3. Forgetting the `Retry-After` header on a 429 response (ch.10) — it's
   a small detail that signals attention to real API usability.
4. Assuming ONE global limit is enough — real systems often need
   PER-ENDPOINT limits too (login attempts need a much stricter limit
   than general read traffic).
