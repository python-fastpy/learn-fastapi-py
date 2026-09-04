# Case Study: Design a News Feed (Twitter-Style Timeline)

*The capstone case study — pulls together caching (ch.04), database
scaling (ch.06), and consistent hashing (ch.12) to solve one famously
tricky problem: what happens when a "celebrity" account has 100
million followers?*

---

## ELI5

Imagine a school newsletter. Every time the most popular kid in school
posts something, the newsletter club would have to run to EVERY single
student's locker and drop in a copy — that's a lot of running for one
post. But if instead every student just checks a shared bulletin board
for "things posted by people I follow," the popular kid only has to
pin ONE copy up, and everyone reads it from the same place.

That tension — "deliver to everyone's personal mailbox" vs. "let
everyone check a shared board" — is the entire core problem of this
case study.

---

## 1. Requirements

**Functional:**
- Users post short messages ("tweets").
- Users follow other users.
- Users see a feed of posts from people they follow, roughly newest first.

**Non-functional:**
- Read-heavy: feed is checked constantly, posts happen far less often.
- Feed load must be FAST (users check it dozens of times a day; slow
  feed loads directly hurt engagement).
- Eventual consistency is fine — seeing a post a few seconds late is
  a non-issue (ch.07).
- Must handle wildly UNEVEN follower counts (most users have a few
  hundred followers; a small number have tens of millions).

## 2. Estimate

```
Daily active users:      200,000,000
Posts/day:                ~100,000,000 (writes)
Feed reads/day:            ~2,000,000,000 (20x posts — very read-heavy)
Avg followers/user:        ~200
Max followers (celebrity): ~100,000,000
```

That LAST number — a 100M-follower outlier sitting next to a typical
200-follower user — is the whole design challenge. Any approach that
works great for typical users breaks catastrophically for celebrities,
and vice versa.

## 3. High-Level Design — Two Competing Strategies

### Fan-out-on-write ("push" — deliver to everyone's personal feed
immediately when they post)

```
User posts ──▶ Post Service ──▶ for EACH follower:
                                    write this post into their
                                    PRE-COMPUTED feed (cached list)

  User's feed = just read their own pre-computed list → FAST reads
  (the expensive work already happened at post time)
```

```
+ Feed reads are extremely fast (just read one pre-built list,
  ideal given this is a read-heavy 20:1 system)
- A celebrity with 100M followers posting means 100M individual
  writes for ONE post — a massive, slow write spike (the "celebrity
  problem" / "hot key problem")
```

### Fan-out-on-read ("pull" — compute the feed fresh when requested)

```
User requests feed ──▶ Feed Service ──▶ look up who they follow ──▶
                          fetch each followed user's recent posts ──▶
                          merge + sort by time ──▶ return
```

```
+ Posting is cheap no matter how many followers you have (ONE write)
- Every feed READ now does real work (fetch from N followed users,
  merge, sort) — slow for users who follow a LOT of people, and this
  is the HOT path (20:1 read-heavy!) — bad fit on its own
```

## 4. Deep Dive: The Hybrid Approach (the real answer)

```
                    Follower count?
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                     ▼
  NORMAL USER                          CELEBRITY (e.g. >1M followers)
  (fan-out-on-write)                   (fan-out-on-read, for THIS
                                         person's posts only)

  Posting → pushed into all           Posting → NOT pushed to millions
  followers' pre-built feeds            of individual feeds; just
                                         stored once
  Reading → read your own                Reading → your pre-built feed
  pre-built feed (fast)                    is merged with a live pull
                                           of celebrity posts you follow,
                                           at READ time
```

This directly mirrors ch.12's consistent hashing lesson in spirit: an
even, general-purpose strategy (fan-out-on-write) breaks down for a
small number of extreme outliers, so you special-case the outliers
instead of redesigning the whole system around them.

### Supporting Pieces

- **Cache** (ch.04): a user's pre-built feed IS effectively a cache —
  hot/active users' feeds stay cached; inactive users' feeds can be
  computed lazily on their (rare) next login instead of maintained
  continuously.
- **Database sharding** (ch.06): posts and the follow graph are sharded
  by user ID — a user's own posts and follow-list are looked up together
  often, so co-locating them by user ID reduces cross-shard queries.
- **Message queue** (ch.08): fan-out-on-write is naturally async — the
  post is saved immediately (fast response to the poster), and an
  async worker does the (potentially slow, for a mid-size account)
  fan-out to followers' feeds in the background.

---

## Interview Angle

The interviewer is specifically testing whether you'll propose PURE
fan-out-on-write (which sounds reasonable until the celebrity problem
comes up) and whether you can adapt once that flaw is pointed out —
saying "I'd use a hybrid, splitting by follower count" BEFORE being
prompted is a strong signal you've seen this class of problem before.

## Gotchas

1. Proposing pure fan-out-on-write without ever mentioning the
   celebrity/hot-key problem is the single most common gap in this
   exact case study — always raise it yourself.
2. Proposing pure fan-out-on-read ignores that this system is
   READ-heavy (20:1) — optimizing writes at the direct expense of the
   dominant read path is backwards for these numbers.
3. Forgetting that fan-out-on-write should be ASYNCHRONOUS (ch.08) —
   doing it synchronously means the poster waits for potentially
   thousands of writes to finish before their post "succeeds."
4. Not stating the follower-count threshold that decides which
   strategy applies to a given user — a vague "we mix both" without a
   concrete split is a weaker answer than naming the actual mechanism.
