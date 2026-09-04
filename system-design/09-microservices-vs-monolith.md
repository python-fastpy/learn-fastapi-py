# Microservices vs. Monolith & API Gateway

---

## ELI5

A **Swiss Army knife** does everything — knife, scissors, screwdriver —
all in one folded tool. Easy to carry, but if the corkscrew breaks, you
might have to send the WHOLE knife in for repair, and it's a little
bulky for someone who only ever uses the scissors.

A **toolbox** has a separate knife, separate scissors, separate
screwdriver. Each tool can be replaced/upgraded on its own, and you
only grab what you need — but now you're carrying (and organizing) a
whole box instead of one thing.

The knife is a **monolith**. The toolbox is **microservices**.

---

## The Real Thing

### Monolith

```
┌─────────────────────────────────────┐
│              ONE APPLICATION          │
│  ┌────────┐ ┌────────┐ ┌──────────┐  │
│  │  Users  │ │ Orders  │ │ Payments  │  │  all in one codebase,
│  └────────┘ └────────┘ └──────────┘  │  one deploy, one database
└─────────────────────────────────────┘
```

### Microservices

```
┌──────────┐   ┌──────────┐   ┌──────────┐
│  Users    │   │ Orders    │   │ Payments  │   each: own codebase,
│  Service  │   │ Service   │   │ Service   │   own deploy, often
│  own DB   │   │  own DB   │   │  own DB   │   own database too
└────┬─────┘   └────┬─────┘   └────┬─────┘
     └───────────────┼───────────────┘
                      ▼
              (services call each
               other over the network,
               often via an API Gateway)
```

### The Real Trade-off

| | Monolith | Microservices |
|---|---|---|
| Early-stage speed | Fast to build, one thing to run | Slower — network calls, more moving parts |
| Deploys | One deploy for everything | Each service deploys independently |
| Scaling | Scale the WHOLE app, even if only 1 part is hot | Scale JUST the hot service |
| Failure isolation | One bug can crash everything | One service crashing doesn't (necessarily) take down others |
| Team ownership | Everyone touches the same codebase | Different teams own different services cleanly |
| Complexity | Low operational complexity | High — needs service discovery, distributed tracing (ch.14), network reliability handling |
| Data consistency | Easy (one DB, real transactions) | Hard — cross-service transactions need patterns like Sagas |

**Neither is "correct"** — most successful systems START as a monolith
(faster to build and reason about while the product is still changing
a lot) and split into microservices only once specific parts need
independent scaling or independent teams. Splitting too early is a
very common, very real mistake, not just a theoretical one.

### API Gateway

Once you have several services, clients shouldn't need to know about
all of them individually. An **API Gateway** sits in front:

```
                     ┌───────────────┐
  Client ───────────▶│  API Gateway   │
                     └───────┬───────┘
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
   Users Service    Orders Service    Payments Service
```

The gateway typically handles things that would otherwise be
duplicated in every service: **authentication, rate limiting (ch.10),
request routing, SSL termination, and sometimes response aggregation**
(combining several services' responses into one for the client).

---

## Interview Angle

**Expect this framing:** "Should this be a monolith or microservices?"
The strong answer ties it to the STATED requirements: team size,
expected scale, and whether different parts genuinely need to scale
independently — not "microservices are more modern."

**Model answer:** "Given this is a new product with one small team, I'd
start monolithic — it's faster to iterate and there's no real
independent-scaling need yet. I'd split out [the specific heavy
component] into its own service once it clearly needs to scale
differently from the rest."

---

## Gotchas

1. "Microservices are more scalable" is only true for the PARTS that
   actually need independent scaling — splitting everything up front
   adds network overhead and operational complexity for no benefit.
2. Microservices don't remove the need for a shared database strategy —
   each service typically needs its OWN database (shared databases
   between services reintroduce tight coupling).
3. Cross-service transactions ("update Orders AND Payments atomically")
   lose the easy ACID guarantee a monolith's single database gives you
   for free — this is a real cost, mention it if proposing a split.
4. Don't forget the API Gateway becomes a new single point of failure
   and needs the same redundancy thinking as a load balancer (ch.03).
