# Case Study: Design a Chat Application

*Ties to `08-message-queues-and-async.md` for delivery, and forces a
real decision from `07-cap-theorem-and-consistency.md` on message
ordering.*

---

## ELI5

A phone call is "live" both ways at once. A chat app is more like
passing paper notes back and forth in class — sometimes the other
person isn't looking right at that second, so the note has to WAIT
until they check, but it should still arrive, and arrive in the order
you wrote them.

---

## 1. Requirements

**Functional:**
- Send/receive 1-on-1 messages in near real-time.
- Messages arrive even if the recipient is briefly offline (delivered
  when they reconnect).
- Show "online"/"last seen" status.
- (Optional) group chats, read receipts, typing indicators.

**Non-functional:**
- Low latency for delivery when both users are online.
- Messages must not be LOST (delivery guarantee matters more than
  strict real-time speed).
- Message ORDER within a conversation must be preserved.
- Moderate consistency needs: online status can be eventually
  consistent (ch.07) — a few seconds of staleness on "last seen" is fine.

## 2. Estimate

```
Daily active users:        50,000,000
Messages/user/day:         ~40
Total messages/day:        2,000,000,000
Messages/sec (avg):        ~23,000
Peak (3-5x avg):           ~100,000/sec
Storage/message:           ~200 bytes → 2B/day × 200B ≈ 400 GB/day
                            → sharding (ch.06) is needed for message storage
```

## 3. High-Level Design

```
User A                                          User B
  │  persistent connection                        │  persistent connection
  ▼  (WebSocket)                                   ▼  (WebSocket)
┌──────────────┐                             ┌──────────────┐
│ Connection     │                             │ Connection     │
│ Server (A's)   │                             │ Server (B's)   │
└──────┬───────┘                             └──────┬───────┘
       │                                              ▲
       │      A sends msg for B                       │ if B is online,
       ▼                                               │ push directly
┌─────────────────────────────────────────────────────┘
│  Message Service ── writes to ──▶ Message Store (sharded DB)
│        │
│        └── if B is OFFLINE: message just sits in the store;
│            delivered on B's next reconnect (pull unread messages)
└──────────────────────────────────────────────────────
```

## 4. Deep Dive

### WebSockets vs. Long Polling vs. Plain HTTP Polling

```
PLAIN POLLING              LONG POLLING                WEBSOCKET
──────────────              ─────────────                ─────────
Client asks "new           Client asks, server           ONE persistent
messages?" every            HOLDS the request open        connection, server
few seconds                 until there's a message        can push anytime
Simple, but wasteful        (or a timeout), then           without the client
 and adds delay              responds and client            re-asking
                              immediately re-asks           Lowest latency,
                             Better than plain polling,     most efficient for
                              still some overhead per        frequent bidirectional
                              request cycle                 traffic — the right
                                                             choice here
```

### Message Delivery & Ordering

Applying ch.08 directly: this needs **at-least-once delivery** (never
silently drop a message) with a client-side **idempotency/dedup**
mechanism (each message has a unique client-generated ID; if the same
ID arrives twice due to a retry, the client/server ignores the
duplicate).

```
Ordering: each message gets a monotonically increasing sequence number
PER CONVERSATION (not globally) — assigned by the Message Service at
write time. Clients render messages sorted by this sequence number,
which survives out-of-order network delivery.
```

### Handling the "Connection Server" Problem

Persistent WebSocket connections mean a user is "pinned" to whichever
specific connection server they connected to — this is the STATEFUL
exception to ch.02's stateless rule. The fix: a shared lookup service
(e.g. `user_id → connection_server_id`, kept in a fast store like
Redis) so the Message Service knows WHERE to push a message for an
online user, regardless of which of many connection servers they're
attached to.

```
Message Service needs to deliver to User B:
  1. Look up: "which connection server is User B attached to?"
     (Redis: user_id → server_id)
  2. Found → forward the message to THAT specific server, which
     pushes it down B's open WebSocket
  3. Not found (offline) → just persist; deliver on next reconnect
```

### Online Presence

"Last seen" / online status is a perfect eventual-consistency (ch.07)
use case — briefly stale presence info causes zero real harm, so it's
fine to update it via a lightweight heartbeat (e.g. every 30 seconds)
rather than requiring instant, strongly consistent propagation.

---

## Interview Angle

A strong candidate explicitly separates the TWO delivery paths (online
push vs. offline store-and-forward) rather than describing only the
happy path where both users are online at once — that's the detail
that usually reveals whether someone has really thought it through.

## Gotchas

1. Forgetting the offline case entirely — "how does B get the message
   if they're not connected right now" is close to a mandatory
   follow-up question.
2. Using a GLOBAL sequence number for ordering instead of per-conversation
   — unnecessary coordination overhead for no benefit, since
   conversations don't need to be ordered relative to EACH OTHER.
3. Treating WebSocket connections as stateless — they're not, and the
   connection-server lookup problem above is the direct consequence.
4. Proposing strong consistency for presence/online-status — this is
   the textbook case where eventual consistency (ch.07) is clearly
   the right, not just acceptable, choice.
