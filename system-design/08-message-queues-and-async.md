# Message Queues & Async/Event-Driven Processing

---

## ELI5

A restaurant kitchen has an order ticket rail. The waiter doesn't stand
there watching the cook make each dish — they clip the ticket to the
rail and immediately go take the next table's order. The cook pulls
tickets off the rail whenever they're free and cooks them one by one.

The **ticket rail is the queue**. It lets the waiter (the part that
talks to customers) and the cook (the part that does slow work) run at
their OWN pace, instead of the waiter standing around waiting.

---

## The Real Thing

### The Basic Shape

```
  Producer                    Queue                    Consumer
(e.g. web server)         (buffers messages)      (e.g. worker process)
      │                                                    │
      │  "resize this image"                                │
      ├──────────────────▶ [msg1][msg2][msg3] ──────────────┤
      │  returns to user                        pulls msg1,
      │  IMMEDIATELY                             processes it,
      │  (doesn't wait                           pulls msg2...
      │   for the resize)
```

This decouples the producer's speed from the consumer's speed — a
traffic spike fills up the queue instead of crashing the consumer, and
the consumer catches up when things calm down (this is called
**backpressure absorption**, or informally "smoothing out spikes").

### Point-to-Point Queue vs. Pub-Sub

```
QUEUE (point-to-point)                 PUB-SUB (fan-out)
────────────────────────               ────────────────────────
Producer → [queue] → ONE consumer      Publisher → [topic] → EVERY
  (of many workers) picks up            subscriber gets a COPY
  each message                          of the message
Good for: distributing work             Good for: notifying multiple
  across a worker pool (each job         independent systems about
  done exactly once, by whoever's        one event ("order placed" →
  free)                                  email service AND analytics
                                          AND inventory service each
                                          react independently)
```

### Delivery Guarantees

| Guarantee | Meaning | Risk |
|---|---|---|
| **At-most-once** | Message might be lost, never duplicated | Simplest, but can silently drop work |
| **At-least-once** | Message is never lost, but might be delivered twice | Consumer MUST be idempotent (safe to process the same message twice) |
| **Exactly-once** | Never lost, never duplicated | Hardest to build correctly; often "at-least-once + dedup" underneath |

```
Why idempotency matters (at-least-once in practice):
  "charge $10" processed TWICE by accident → customer charged $20  ✗
  "set balance = current - 10, only if not already applied this
   request_id" → safe to run twice, same end result             ✓
```

### Async/Event-Driven Processing

Beyond just "a queue," this is a broader style: instead of Service A
directly calling Service B and waiting, Service A emits an **event**
("OrderPlaced") and doesn't care who's listening. Service B, C, and D
each independently react. Adding Service E later means E just
subscribes — A never needs to change.

```
SYNCHRONOUS (tightly coupled)          EVENT-DRIVEN (decoupled)
────────────────────────────           ────────────────────────
A calls B directly, waits              A emits "OrderPlaced" event
If B is slow/down, A is stuck          A moves on immediately
Adding a new consumer of this          Adding a new consumer = just
  data means changing A's code           subscribe, zero change to A
```

---

## Interview Angle

**Expect this framing:** "This action is slow (sending an email,
resizing an image, notifying 3 other services) — how do you keep the
user-facing request fast?" The answer is almost always: don't do it
inline, publish it to a queue and process it asynchronously.

**Model answer:** "The API returns immediately after publishing an
event/message; a worker pool consumes it separately. I'd design
consumers to be idempotent since most queues offer at-least-once
delivery, not exactly-once."

---

## Gotchas

1. Async processing means the user DOESN'T get an immediate confirmation
   that the slow work is done — say explicitly how they find out later
   (polling, websocket push, email).
2. "At-least-once" is the realistic default for most systems — don't
   assume exactly-once unless you've specifically designed for it (and
   even then, mention the dedup mechanism).
3. A queue with no consumers running, or consumers slower than
   producers, grows forever — mention monitoring queue depth (ties to
   ch.14) and being able to scale consumers horizontally.
4. Don't reach for a message queue for things that genuinely need an
   immediate answer (e.g. "is this password correct?") — queues are
   for work that can happen *later*, not everything.
