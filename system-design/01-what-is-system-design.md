# What Is System Design?

---

## ELI5

Imagine you and a friend sell lemonade at the end of your driveway. One
pitcher, one table, done — if 3 people show up, you pour 3 cups.

Now imagine you have to sell lemonade to your *entire city*, every day,
all day, and it can never run out. Suddenly you need: trucks bringing
lemons from many farms, several kitchens making lemonade at once, fridges
all over town so it stays cold near people, a plan for what happens when
one kitchen catches fire, and a way to know how much lemonade is left
*without driving to every stand*.

**System design is the "how do we build the city-wide lemonade operation"
conversation** — not "how do we make lemonade" (that part's easy), but
how do we make it work reliably at a scale where any single simple
answer breaks.

---

## The Real Thing

System design interviews test whether you can take a vague product idea
("design Twitter", "design a URL shortener") and turn it into a concrete
architecture, while thinking out loud about trade-offs. There's rarely
one "correct" answer — the interviewer is grading your *process*.

### Functional vs. Non-Functional Requirements

```
FUNCTIONAL REQUIREMENTS            NON-FUNCTIONAL REQUIREMENTS
("what must it DO")                ("how well must it do it")
─────────────────────────          ─────────────────────────
- Users can post a tweet           - 99.99% uptime (availability)
- Users can follow others          - Feed loads in < 200ms (latency)
- Users see a feed of posts        - Handles 50M daily active users
                                    - Reads >>> writes (read-heavy)
                                    - Eventual consistency is OK
```

Almost every real interview mistake comes from skipping the
non-functional side and jumping straight to drawing boxes. **Scale,
latency, and consistency requirements decide the entire architecture** —
a system for 100 users and a system for 100 million users are not the
same system with "more servers," they're different designs entirely.

### Back-of-the-Envelope Estimation

You don't need exact numbers — you need to know which order of magnitude
you're in, because that decides whether a single database is fine or
whether you need sharding.

```
Example: "design a URL shortener"

  Daily new URLs:        1,000,000
  Reads (redirects) are
  usually ~100x writes:  100,000,000 reads/day

  Requests per second (RPS):
    100,000,000 / 86,400 seconds  ≈  1,200 reads/sec (average)
    (peak traffic is often 3-5x average → plan for ~5,000/sec)

  Storage for 5 years of URLs:
    1M/day × 365 × 5 × ~500 bytes/record  ≈  ~1 TB

  Conclusion so far: read-heavy by 100x → caching matters A LOT.
  1TB over 5 years is small → storage isn't the bottleneck, read
  throughput and latency are.
```

That one estimate already tells you: cache aggressively, optimize for
fast reads, don't over-engineer the write path.

### The Standard Interview Flow

```
1. Clarify requirements  ──▶ 2. Estimate scale  ──▶ 3. High-level design
        (functional +              (RPS, storage,        (boxes: client,
         non-functional)            bandwidth)            LB, servers, DB,
                                                            cache, queue)
                                                                 │
                                                                 ▼
                              5. Wrap up trade-offs  ◀──  4. Deep dive
                                 (what you'd improve       (pick 1-2 tricky
                                  with more time)           components and
                                                             go deep)
```

Every "Case Study" chapter later in this folder (15-18) follows exactly
this flow.

---

## Interview Angle

**Expect this exact framing:** "Design [X]. Take a few minutes to think,
then walk me through it." They are NOT expecting a finished diagram in
2 minutes — they're watching whether you ask clarifying questions first.

**Model answer opener:** "Before I design this, let me confirm scope:
who are the users, what's the read/write ratio, roughly how many users,
and is strong consistency required or is eventual consistency fine?"
This single sentence signals seniority more than anything you draw.

---

## Gotchas

1. Jumping straight to "I'll use microservices and Kafka" before
   establishing scale — for a 10,000-user app, that's over-engineering,
   not a solution. **Match the design to the stated scale.**
2. Treating every requirement as equally important — a chat app caring
   about message *ordering* is very different from one caring about
   message *delivery speed*. Ask which matters more.
3. Forgetting non-functional requirements entirely and only listing
   features — this is the single most common reason candidates struggle
   later, because they never decided how much scale to design for.
4. Trying to design for infinite scale from day one — real systems
   start simple and evolve; say so explicitly ("start with one DB, add
   read replicas when reads become the bottleneck").
