# Scalability: Vertical vs. Horizontal Scaling

---

## ELI5

Your kitchen can only cook so many pizzas an hour. Two ways to make more:

1. **Buy a bigger oven** (fits more pizzas, cooks faster) — but there's
   a biggest oven money can buy, and if it breaks, ALL cooking stops.
2. **Buy more ovens** and hire more cooks — you can keep adding ovens
   almost forever, and if one breaks, the others keep cooking.

Option 1 is **vertical scaling**. Option 2 is **horizontal scaling**.

---

## The Real Thing

```
VERTICAL SCALING ("scale up")          HORIZONTAL SCALING ("scale out")
──────────────────────────             ──────────────────────────────
   ┌─────────┐                            ┌───┐ ┌───┐ ┌───┐ ┌───┐
   │ BIGGER  │  add more CPU/RAM/disk     │ 1 │ │ 2 │ │ 3 │ │ 4 │  add
   │ SERVER  │  to the SAME machine       └───┘ └───┘ └───┘ └───┘  MORE
   └─────────┘                              same-size machines    machines

   Simple: no code changes needed        Complex: needs a load balancer,
   Single point of failure                needs the app to be STATELESS
   Hits a hard ceiling (biggest           No hard ceiling — add machine #501
     machine you can buy/afford)          Failure of one node ≠ outage
```

### Why horizontal scaling needs "statelessness"

If server #1 stores a logged-in user's session in its own memory, and
the load balancer sends that user's NEXT request to server #2, server
#2 has no idea who they are. Horizontal scaling only works cleanly when
any server can handle any request — which means session/state has to
live somewhere shared (a database, Redis, or in a token the client
carries — see `08-session.py` in `fastapi/` for exactly this problem).

```
BAD (stateful):                       GOOD (stateless):
  Server 1: [user A's session]          Server 1 ─┐
  Server 2: [user B's session]          Server 2 ─┼──▶ Shared session
  → user A's next request MUST          Server 3 ─┘     store (Redis)
    go back to Server 1                → ANY server can serve ANY user
```

### Diminishing Returns of Vertical Scaling

```
Performance
    │                              ← flattens out: doubling RAM doesn't
    │                    ●●●●●●●●●   double throughput forever (I/O,
    │              ●●●●●●             network, and single-CPU limits
    │        ●●●●●●                   start to dominate)
    │   ●●●●●
    │●●●
    └──────────────────────────────── Machine size / cost
```

### When to Use Which

| Scenario | Pick |
|---|---|
| Early-stage app, low traffic, want simplicity | Vertical (one bigger box) |
| Need to survive a single server dying | Horizontal (redundancy) |
| Traffic is spiky/unpredictable | Horizontal (add/remove nodes on demand) |
| A single database that's hard to distribute (some relational workloads) | Vertical, up to a point — then look at replication/sharding (ch.06) |
| You expect 10x-100x growth | Horizontal from early on — retrofitting statelessness later is painful |

---

## Interview Angle

**Expect this framing:** "How would you handle 10x more traffic?" The
weak answer is "add more servers." The strong answer names the
*specific* bottleneck first: "Is it CPU-bound compute, or is it the
database? If it's stateless app servers, horizontal scaling behind a
load balancer is straightforward. If it's the database, that's harder —
see database scaling (ch.06)."

**Model answer structure:** identify the bottleneck → say whether the
component can even BE horizontally scaled → note what needs to change
to make it stateless if it currently isn't.

---

## Gotchas

1. "Just add more servers" is not a complete answer if the app is
   stateful — say explicitly what has to change (externalize session/state).
2. Vertical scaling isn't "bad" — it's the right first move for most
   early-stage systems because it requires zero architecture changes.
3. Horizontal scaling needs a load balancer (ch.03) to actually
   distribute traffic — scaling out with nothing routing to the new
   machines does nothing.
4. Databases don't horizontally scale as easily as stateless app
   servers — that's WHY replication/sharding (ch.06) is its own topic
   instead of "just add more DB servers."
