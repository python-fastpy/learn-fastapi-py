# Load Balancing

---

## ELI5

You walk into a restaurant with 5 waiters. A host stands at the door and
sends you to whichever waiter is least busy, instead of everyone
crowding around waiter #1 while the other four stand idle. The host is
the **load balancer**. The waiters are your **servers**.

If a waiter goes home sick, the host stops sending people to them — the
restaurant keeps running with the remaining waiters.

---

## The Real Thing

```
                         ┌─────────────────┐
   Clients ───requests──▶│  Load Balancer   │
                         └────────┬─────────┘
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              ┌──────────┐  ┌──────────┐  ┌──────────┐
              │ Server 1 │  │ Server 2 │  │ Server 3 │
              └──────────┘  └──────────┘  └──────────┘
                    ▲ health-checked continuously ▲
                (unhealthy servers are removed from rotation)
```

```
ONE REQUEST THROUGH THE LOAD BALANCER
  ① Client ──▶ Load Balancer  (one public address)
        │
        ▼
  ② LB keeps only healthy servers in its pool: [S1, S2, S3]
        │
        ▼
  ③ routing algorithm picks one (e.g. round robin → S2)
        │
        ▼
  ④ LB ──▶ Server 2 ──▶ response ──▶ LB ──▶ Client  ✓ 200 OK
```

### Routing Algorithms

| Algorithm | How it decides | Good for |
|---|---|---|
| **Round robin** | 1→2→3→1→2→3... in order | Servers are roughly identical |
| **Weighted round robin** | Bigger servers get proportionally more requests | Mixed server sizes |
| **Least connections** | Send to whichever server has fewest active connections | Requests vary a lot in duration |
| **IP hash** | Same client IP always → same server | Need "sticky sessions" without shared storage (a workaround, not a fix — see ch.02's statelessness note) |
| **Consistent hashing** | See ch.12 — used when the "servers" are really cache/data shards, not just app replicas |

```
ROUND ROBIN vs. LEAST CONNECTIONS — the next request arrives
  ① active connections right now:   S1 = 12    S2 = 3    S3 = 7
  ② ROUND ROBIN:       last went to S2 ──▶ next in order ──▶ S3
                       (ignores that S3 is busier than S2)
  ③ LEAST CONNECTIONS: min(12, 3, 7) ──▶ S2 ──▶ S2 now = 4  ✓
```

### Layer 4 vs. Layer 7 Load Balancing

```
LAYER 4 (Transport)                  LAYER 7 (Application)
────────────────────                 ──────────────────────
Looks only at IP + port              Reads the actual HTTP request
Fast, simple, protocol-agnostic      Can route by URL path, header,
                                       cookie ("/api/* → API servers,
                                       /images/* → image servers")
Can't do content-based routing       Can do SSL termination, A/B
                                       testing, canary releases
```

```
LAYER 7 PATH-BASED ROUTING
  ① GET /images/cat.png ──▶ L7 LB reads the HTTP request
        │
        ▼
  ② path starts with /api/ ? ───── yes ──▶ API server pool
        │ no
        ▼
  ③ path starts with /images/ ? ── yes ──▶ image server pool  ✓ (this one)
        │ no
        ▼
  ④ default server pool
  (an L4 LB only sees IP + port — it can't make decisions ② or ③)
```

### Health Checks

The load balancer doesn't just guess a server is alive — it pings a
`/health` endpoint every few seconds. Miss enough checks in a row →
pulled out of rotation automatically. This is HOW horizontal scaling
(ch.02) actually survives a server crashing: the load balancer notices
and routes around it within seconds.

```
HEALTH CHECK LOOP — Server 2 crashes
  ① every few seconds: LB ──GET /health──▶ each server
        │
        ▼
  ② 200 OK ? ── yes ──▶ ✓ stays in rotation
        │ no / timeout
        ▼
  ③ missed checks in a row ≥ threshold ? ── no ──▶ keep checking
        │ yes
        ▼
  ④ ✗ S2 pulled from rotation ──▶ traffic goes to S1, S3 only
  ⑤ S2 recovers + passes checks again ──▶ back in rotation
```

### Where Load Balancers Themselves Live

A single load balancer is itself a single point of failure — so in
production there are usually at least two, with DNS or a floating IP
routing to whichever is currently active (tied to ch.13's
active-passive failover pattern).

```
LOAD BALANCER FAILOVER (active-passive)
  ① Client ──▶ DNS / floating IP ──▶ LB-A (active)     LB-B (standby)
        │
        ▼
  ② ✗ LB-A dies ──▶ LB-B notices LB-A stopped responding
        │
        ▼
  ③ floating IP / DNS is switched to point at LB-B
        │
        ▼
  ④ Client ──▶ LB-B ──▶ servers  ✓ traffic keeps flowing
```

---

## Interview Angle

**Expect this framing:** "How does traffic get distributed across your
servers?" or embedded inside a bigger design ("design Twitter" — you're
expected to draw the load balancer box without being asked explicitly).

**Model answer:** name the algorithm AND justify it against the
workload ("since requests are similar in cost, round robin is fine;
if some requests are much heavier, I'd use least-connections instead"),
then mention health checks so the interviewer knows you've thought
about failure, not just the happy path.

---

## Gotchas

1. Round robin assumes all requests cost roughly the same — if one
   endpoint is 100x more expensive than another, round robin can
   overload a server that got unlucky with a run of heavy requests.
2. IP-hash "sticky sessions" are a band-aid for stateful servers, not a
   real solution — the real fix is making servers stateless (ch.02).
3. Forgetting the load balancer itself needs redundancy — "what if the
   load balancer dies?" is a fair follow-up question.
4. Layer 4 can't inspect the request, so it can't do path-based routing
   — don't propose L4 for a design that needs `/api` vs `/static` split
   routing.
