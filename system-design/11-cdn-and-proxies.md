# CDN & Proxies (Forward vs. Reverse)

---

## ELI5

Instead of calling the soda factory every single time you're thirsty,
there's a **vending machine down the hall** stocked with the same soda,
much closer to you. Most of the time you never bother the factory at
all — that vending machine is a **CDN**: a cached copy of content,
placed physically close to where people actually are.

A **proxy** is just "something that stands in front of / in between"
— like a receptionist who either (a) fetches things FOR you from
outside (forward proxy), or (b) decides which of several back-office
staff should handle a visitor who came asking for "the company"
(reverse proxy).

---

## The Real Thing

### CDN (Content Delivery Network)

```
Without a CDN:                        With a CDN:
User (Tokyo) ──────────────▶          User (Tokyo) ──▶ CDN edge (Tokyo)
                              far      User (London)──▶ CDN edge (London)
Origin server (Virginia)               User (Sydney) ──▶ CDN edge (Sydney)
                                              │  cache miss only
                                              ▼
                                       Origin server (Virginia)
```

- CDNs cache **static/semi-static content** near users: images, videos,
  CSS/JS bundles, and (with more setup) API responses that don't
  change per-user.
- This is literally the SAME cache-aside idea from ch.04, just
  geographically distributed instead of sitting next to your app servers.
- Massively cuts latency (physics — light/data takes real time to
  travel long distances) AND cuts load on your origin server.

### Forward Proxy vs. Reverse Proxy

```
FORWARD PROXY                          REVERSE PROXY
──────────────                         ──────────────
   Client                                    Client
     │                                         │
     ▼                                         ▼
┌───────────┐                          ┌───────────┐
│  Forward   │  hides the CLIENT        │  Reverse   │  hides the SERVERS
│   Proxy    │  from the internet        │   Proxy    │  from the client
└─────┬─────┘  (client → proxy →         └─────┬─────┘  (client thinks
      ▼         internet)                       ▼         it's talking to
   Internet                              Server1/2/3       ONE thing, but
                                                             it's routing to
Used for: corporate content             Used for: load     many backend
filtering, anonymizing a client,        balancing (ch.03),  servers)
bypassing geo-restrictions              SSL termination,
                                         caching, API Gateway
                                         (ch.09) IS a reverse proxy
```

The load balancer from ch.03 and the API Gateway from ch.09 are BOTH,
technically, reverse proxies with extra responsibilities layered on.

### Geo-Routing (a CDN/DNS-level trick)

DNS can be configured to return a DIFFERENT server IP depending on
WHERE the request is coming from — so a user in Japan gets routed to
the nearest edge/data center automatically, without the client needing
to know anything about geography.

---

## Interview Angle

**Expect this framing:** "Users are complaining about slow load times
in a region far from your servers" — the answer is a CDN for static
assets, and geo-distributed origin servers/regions for dynamic content
if it's a bigger system.

**Model answer:** "Static assets (images, JS bundles) go behind a CDN
with edge caching close to users. For dynamic, personalized content
that can't be CDN-cached, I'd look at deploying app servers/replicas
in multiple regions and routing users to the nearest one via DNS/geo-routing."

---

## Gotchas

1. CDNs cache well for content that's the SAME for everyone — don't
   propose caching personalized/per-user API responses at a CDN edge
   without a cache-key strategy that accounts for the personalization.
2. "Reverse proxy" and "load balancer" aren't different things at the
   architecture-diagram level — a load balancer usually IS a reverse
   proxy; don't draw them as two separate unrelated boxes without reason.
3. Forgetting cache invalidation for CDN-cached content — same problem
   as ch.04, just at a different layer (CDNs use TTLs and cache-busting
   URLs, e.g. `style.css?v=42`, very commonly).
4. A forward proxy protects/anonymizes the CLIENT; a reverse proxy
   protects/load-balances the SERVER — mixing these up in an interview
   is an easy tell that the concept isn't solid.
