# Monitoring, Logging & Observability

---

## ELI5

A car has a dashboard: speed, fuel level, engine temperature, a
"check engine" light. You don't pop the hood every time you drive —
the dashboard tells you when something's wrong, and roughly WHERE to
look.

**Observability is your system's dashboard.** Without it, the only way
to know something's broken is a user complaining — which is like only
finding out you're out of gas when the car actually stops.

---

## The Real Thing

### The Three Pillars

```
METRICS                    LOGS                       TRACES
────────                    ────                       ──────
Numbers over time          Timestamped text events     The full journey
"CPU usage: 72%"           "10:03:01 ERROR: payment      of ONE request
"requests/sec: 1,204"       failed for user 42"          across MULTIPLE
"p99 latency: 340ms"       Detailed, but expensive       services
Cheap to store, great        to search at scale         "request X hit
 for dashboards/alerts      Best for: "what EXACTLY       Gateway → Users
Best for: "IS something      happened at 10:03:01?"       Service → DB,
 wrong right now?"                                        took 340ms total,
                                                            230ms of that
                                                            was the DB call"
                                                           Best for: "WHERE
                                                            in this chain
                                                            is the request
                                                            actually slow?"
```

```
ONE REQUEST → ALL THREE SIGNALS
  ① request hits API Gateway ──▶ assign request/trace ID = abc123
        │
        ▼
  ② Gateway ──(header: trace-id abc123)──▶ Users Service ──▶ DB
        │   each hop records a SPAN (start, duration) ──▶ trace store
        ▼
  ③ each service writes LOG lines tagged abc123 ──▶ log store
        │
        ▼
  ④ each service bumps METRICS (requests++, latency) ──▶ metrics DB
        │
        ▼
  ⑤ dashboards/alerts read metrics; abc123 links trace ↔ logs
```

Tracing matters MOST once you have microservices (ch.09) — in a
monolith, a slow request is one process to look at; in a microservices
system, a slow request might have hopped through 6 services, and
tracing is the only way to see WHICH one added the delay.

```
Trace visualization (a "waterfall"):

  API Gateway    [========================================] 340ms total
  Users Service    [====] 40ms
  Auth check          [==] 20ms
  DB query               [========================] 230ms  ← the culprit
  Response formatting                            [==] 50ms
```

### Alerting — turning metrics into "wake someone up"

```
Metric crosses a threshold ──▶ Alert fires ──▶ On-call engineer paged
  (e.g. error rate > 5%
   for 5 minutes straight)
```

Good alerting has a real design problem: **alert fatigue**. Too many
low-value alerts and engineers start ignoring pages entirely — which
means alerts should be tied to things that actually need a human
(symptom-based: "users are experiencing errors"), not every possible
internal metric wobble (cause-based noise: "CPU hit 81% for 10 seconds").

```
ALERT EVALUATION — step by step  (rule: error rate > 5% for 5 min)
  ① every ~30s: evaluate the rule against the latest metrics
        │
        ▼
  ② error rate > 5% ? ──── no ───▶ ✓ stay quiet (reset the timer)
        │ yes
        ▼
  ③ held for 5 min straight ? ── no ──▶ keep watching (pending)
        │ yes
        ▼
  ④ alert FIRES ──▶ grouped/deduped with alerts already open
        │
        ▼
  ⑤ page on-call ──▶ dashboard (what) ──▶ trace (where) ──▶ logs (why)
```

### Health Checks (the simplest form of observability)

This is the same `/health` endpoint from ch.03's load balancer — a
minimal signal of "am I alive," which is necessary but far from
sufficient; a server can return `200 OK` on `/health` while its
database connection is completely broken.

```
SHALLOW vs. DEEP HEALTH CHECK
  ① LB ── GET /health ──▶ App server
        │
        ├── shallow: "process is up" ──▶ ✓ 200 OK  (even if DB is down!)
        │
        └── deep: ② ping DB   ③ ping critical downstream services
                  │
                  ├── all OK ───▶ ✓ 200 OK ──▶ stays in rotation
                  └── any fail ─▶ ✗ 503    ──▶ LB pulls it from rotation
```

---

## Interview Angle

**Expect this framing:** "How would you know if this system is
unhealthy in production?" — a surprisingly common closing question,
because it reveals whether a candidate thinks past "make it work" into
"know when it stops working."

**Model answer:** "I'd track the golden signals — latency, traffic,
error rate, and saturation — as metrics with dashboards and threshold
alerts. For debugging a specific slow/failing request across services,
I'd rely on distributed tracing with a request ID passed through every
hop. Logs are for the deep-dive once metrics/traces point at a
specific area."

---

## Gotchas

1. Logs alone don't scale as a debugging tool once you have real
   traffic volume — grepping millions of log lines to find one slow
   request is why metrics (to notice) and traces (to localize) exist.
2. Alerting on every metric anomaly causes alert fatigue — tie alerts
   to user-facing symptoms, not every internal fluctuation.
3. A `/health` check that only confirms "the process is running" gives
   false confidence — a good health check verifies its real
   dependencies (DB connection, downstream services) too.
4. Don't propose "add logging" as your entire answer to an
   observability question — naming metrics AND traces (not just logs)
   signals a more complete mental model.
