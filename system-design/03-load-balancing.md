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

### Routing Algorithms

| Algorithm | How it decides | Good for |
|---|---|---|
| **Round robin** | 1→2→3→1→2→3... in order | Servers are roughly identical |
| **Weighted round robin** | Bigger servers get proportionally more requests | Mixed server sizes |
| **Least connections** | Send to whichever server has fewest active connections | Requests vary a lot in duration |
| **IP hash** | Same client IP always → same server | Need "sticky sessions" without shared storage (a workaround, not a fix — see ch.02's statelessness note) |
| **Consistent hashing** | See ch.12 — used when the "servers" are really cache/data shards, not just app replicas |

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

### Health Checks

The load balancer doesn't just guess a server is alive — it pings a
`/health` endpoint every few seconds. Miss enough checks in a row →
pulled out of rotation automatically. This is HOW horizontal scaling
(ch.02) actually survives a server crashing: the load balancer notices
and routes around it within seconds.

### Where Load Balancers Themselves Live

A single load balancer is itself a single point of failure — so in
production there are usually at least two, with DNS or a floating IP
routing to whichever is currently active (tied to ch.13's
active-passive failover pattern).

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
