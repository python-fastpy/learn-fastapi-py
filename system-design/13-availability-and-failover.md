# Availability, Reliability & Failover

---

## ELI5

You carry a spare tire in your car. Not because you expect a flat every
day, but because when it DOES happen, you don't want to be stranded —
you swap the tire and keep driving.

**Redundancy is the spare tire of system design**: having a backup
ready so one failure doesn't turn into "the whole trip is ruined."

---

## The Real Thing

### Availability — measured in "Nines"

```
Availability     Downtime per year        Downtime per day
────────────     ──────────────────       ──────────────────
99%    ("two nines")    ~3.65 days              ~14.4 min
99.9%  ("three nines")  ~8.76 hours             ~1.44 min
99.99% ("four nines")   ~52.6 minutes           ~8.6 sec
99.999%("five nines")   ~5.26 minutes           ~0.86 sec
```

Each extra "nine" is dramatically more expensive to achieve — going
from 99.9% to 99.99% often costs far more than 10x the engineering
effort, because you're eliminating rarer and rarer classes of failure.
**This is why the FIRST interview question about availability should
be "what level do we actually need?"** — not every system needs five
nines.

### SLA vs. SLO vs. SLI (quick vocabulary)

```
SLI (Indicator) = the actual measured metric   ("99.95% of requests succeeded")
SLO (Objective) = the internal target           ("we aim for 99.9% success")
SLA (Agreement) = the external promise/contract ("99.9% or you get a refund")
```

### Redundancy Patterns

```
ACTIVE-PASSIVE                        ACTIVE-ACTIVE
────────────────                      ────────────────
┌────────┐   standby, doing           ┌────────┐  ┌────────┐
│ Primary │◀──nothing until            │ Node A  │  │ Node B  │
│ (active)│   primary fails            │ (active)│  │ (active)│
└────────┘   ┌────────┐                └────────┘  └────────┘
             │ Backup  │               BOTH handle real traffic
             │(passive)│               at the same time
             └────────┘
Simple, but the backup is            Better resource use (nothing sits
"wasted" capacity until needed        idle), but harder — both nodes
Failover = detect failure, promote    must handle writes/consistency
  backup, redirect traffic            (ties to ch.07's CAP trade-offs)
Some downtime during the switch        Can lose one node with ZERO
  (detection + promotion time)          downtime — the other just
                                        keeps serving
```

### Graceful Degradation

Instead of "everything works" or "everything is down," design so LESS
critical features fail first, while the core keeps working:

```
Example: an e-commerce site under heavy load
  ✓ Checkout still works                    (critical — keep this up)
  ✓ Browsing/search still works             (critical)
  ✗ "Recommended for you" section disabled   (nice-to-have — drop it
                                              first to save capacity)
  ✗ Real-time inventory count → shows        (approximate is fine
    "cached ~5 min ago" instead              temporarily)
```

This is often paired with a **circuit breaker**: if a downstream
dependency (e.g. the recommendations service) is failing/slow, STOP
calling it for a while instead of letting every request hang waiting
on it — fail fast and fall back, rather than cascading the failure
upward into the whole system.

```
Circuit breaker states:
  CLOSED (normal) ──too many failures──▶ OPEN (reject immediately,
      ▲                                        don't even try calling)
      │                                          │
      └──── success on a trial request ◀── HALF-OPEN (after a cooldown,
                                                   try ONE request to see
                                                   if it recovered)
```

---

## Interview Angle

**Expect this framing:** "What happens if [component] goes down?" —
asked about almost every box you draw. The strong answer names the
FAILOVER mechanism specifically (not just "we'd have a backup").

**Model answer:** "The database has a standby replica; if the primary
fails, a health check detects it within seconds and promotes the
replica (active-passive). For the app servers, since they're stateless
and behind a load balancer, losing one just removes it from rotation —
effectively active-active, zero special handling needed."

---

## Gotchas

1. "We'd just add a backup" without explaining HOW failure is
   detected and HOW traffic gets redirected is an incomplete answer —
   the mechanism matters, not just the intent.
2. Active-passive still has a gap during failover (detection +
   promotion time) — don't claim zero downtime unless it's genuinely
   active-active.
3. Higher availability numbers aren't free — always connect a
   reliability claim to a cost/complexity trade-off, or it sounds like
   you're reciting a buzzword.
4. Not every dependency needs a circuit breaker — reserve that
   reasoning for calls to external/less-critical services, not your
   own primary database.
