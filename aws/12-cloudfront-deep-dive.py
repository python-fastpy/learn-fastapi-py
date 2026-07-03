# ══════════════════════════════════════════════════════════════════
# AWS Deployment — CloudFront Deep Dive
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 11-route53-cloudfront-acm.py  |  next: 13-secrets-manager.py →

# ╔══════════════════════════════════════════════════╗
# ║  CLOUDFRONT DEEP DIVE                            ║
# ╚══════════════════════════════════════════════════╝
#
# Step 10 showed how to create a CloudFront distribution.
# This section goes deeper into HOW CloudFront works and
# the advanced features you'll use in production.
#
# ── How CloudFront Works ─────────────────────────────────────
#
#   CloudFront has 3 tiers of infrastructure:
#
#   User (Tokyo)
#     │
#     ▼
#   Edge Location (400+ worldwide)        ← Layer 1: closest to user
#     │  Cache HIT? → return immediately (1-5ms)
#     │  Cache MISS? ↓
#     ▼
#   Regional Edge Cache (13 worldwide)    ← Layer 2: bigger cache, fewer locations
#     │  Cache HIT? → return, also cache at edge
#     │  Cache MISS? ↓
#     ▼
#   Origin (your ALB / S3 / API Gateway)  ← Layer 3: your actual server
#     │  Response flows back through all tiers,
#     │  getting cached at each level
#
#   Edge Location:          Small cache, many locations (low latency)
#   Regional Edge Cache:    Large cache, fewer locations (higher hit rate)
#   Origin:                 Your server (only hit on cache miss)
#
#   POP (Point of Presence): A physical facility containing
#   edge locations. Major cities have multiple POPs.
#
# ── Origins ──────────────────────────────────────────────────
#
#   An "origin" is where CloudFront fetches content when cache misses.
#   One distribution can have MULTIPLE origins.
#
#   ┌─────────────────┬────────────────────────────────────────┐
#   │ S3 Bucket       │ Static files (images, CSS, JS, HTML).  │
#   │                 │ Use OAC (Origin Access Control) so S3   │
#   │                 │ is private — only CloudFront can read.  │
#   │                 │ Replaces old OAI (Origin Access Identity)│
#   ├─────────────────┼────────────────────────────────────────┤
#   │ ALB / ELB       │ Dynamic API responses. CloudFront      │
#   │                 │ passes requests to your load balancer.  │
#   │                 │ ALB must be internet-facing (public     │
#   │                 │ subnets) for CloudFront to reach it.    │
#   ├─────────────────┼────────────────────────────────────────┤
#   │ API Gateway     │ Serverless API. EDGE type already HAS   │
#   │                 │ CloudFront built in. REGIONAL type lets  │
#   │                 │ you add your own CloudFront in front.    │
#   ├─────────────────┼────────────────────────────────────────┤
#   │ Custom HTTP     │ Any server with a public URL/IP.        │
#   │                 │ On-prem servers, other cloud providers.  │
#   ├─────────────────┼────────────────────────────────────────┤
#   │ MediaStore /    │ Video streaming origins.                │
#   │ MediaPackage    │                                         │
#   └─────────────────┴────────────────────────────────────────┘
#
#   OAC vs OAI:
#     OAI (old): CloudFront special identity → S3 bucket policy grants access.
#     OAC (new): CloudFront signs requests with SigV4 → S3 bucket policy
#                checks the signing. Supports S3 SSE-KMS, more regions.
#     → Always use OAC for new distributions.
#
# ── Behaviors (URL → Origin Routing) ────────────────────────
#
#   Behaviors map URL path patterns to origins + cache settings.
#   Think of them as routing rules. Evaluated top-to-bottom by priority.
#
#   ┌────────────────┬────────────────┬────────────────────────┐
#   │ Path Pattern   │ Origin         │ Cache Policy           │
#   ├────────────────┼────────────────┼────────────────────────┤
#   │ /api/*         │ ALB origin     │ CachingDisabled        │
#   │ /covers/*      │ S3 origin      │ CachingOptimized       │
#   │ /static/*      │ S3 origin      │ CachingOptimized       │
#   │ Default (*)    │ ALB origin     │ CachingDisabled        │
#   └────────────────┴────────────────┴────────────────────────┘
#
#   Each behavior controls:
#     - Which origin gets the request
#     - Whether to cache, and for how long
#     - Which headers/cookies/query strings to forward
#     - Viewer protocol (HTTP, HTTPS, or redirect HTTP→HTTPS)
#     - Allowed HTTP methods (GET only, or all methods)
#     - Whether to compress responses (gzip/brotli)
#     - CloudFront Functions / Lambda@Edge to run
#
#   Path patterns support wildcards:
#     /api/*         → matches /api/books, /api/books/123
#     /images/*.jpg  → matches /images/cat.jpg but NOT /images/cat.png
#     Default (*)    → catch-all, lowest priority
#
# ── Cache Policy vs Origin Request Policy ────────────────────
#
#   These two policies are the KEY to understanding CloudFront caching.
#   They're often confused, but they do very different things:
#
#   ┌───────────────────────────────────────────────────────────┐
#   │                    CACHE POLICY                           │
#   │  "What makes two requests THE SAME (cache key)?"          │
#   │                                                           │
#   │  Controls what goes into the CACHE KEY. If two requests   │
#   │  produce the same cache key, CloudFront serves the        │
#   │  cached response instead of asking the origin.            │
#   │                                                           │
#   │  Include in cache key:                                    │
#   │    Headers:        e.g., Accept-Language → separate       │
#   │                    cache entries per language              │
#   │    Cookies:        e.g., session_id → per-user cache      │
#   │    Query strings:  e.g., ?page=2 → separate cache         │
#   │    TTL:            How long to cache (min/max/default)     │
#   │                                                           │
#   │  MORE items in cache key = LOWER cache hit rate            │
#   │  FEWER items = HIGHER hit rate (but might serve wrong data)│
#   └───────────────────────────────────────────────────────────┘
#
#   ┌───────────────────────────────────────────────────────────┐
#   │                ORIGIN REQUEST POLICY                      │
#   │  "What extra data should I forward to the origin?"        │
#   │                                                           │
#   │  Some headers/cookies/query strings don't affect caching  │
#   │  but the origin still needs them. This policy forwards    │
#   │  them WITHOUT including them in the cache key.            │
#   │                                                           │
#   │  Common use: forward Authorization header (origin needs   │
#   │  it for auth) but DON'T include in cache key (same        │
#   │  content for all authorized users).                       │
#   └───────────────────────────────────────────────────────────┘
#
#   Example for a FastAPI API:
#
#     Cache Policy:     CachingDisabled
#       → API responses change per request, don't cache them
#
#     Origin Request Policy: AllViewer
#       → Forward ALL headers to ALB (Authorization, Content-Type, etc.)
#       → Origin needs these to process the request
#
#   Example for S3 static files:
#
#     Cache Policy:     CachingOptimized (TTL: 24 hours)
#       → Cache key: just the URL path (no headers/cookies/query)
#       → Same image served to everyone from edge cache
#
#     Origin Request Policy: None needed
#       → S3 doesn't need auth headers (OAC handles access)
#
#   AWS Managed Policies (pre-built — use these):
#
#   ┌──────────────────────────┬───────────────────────────────┐
#   │ CachingDisabled          │ TTL=0. Never cache. For APIs. │
#   │ CachingOptimized         │ TTL=24h. For static files.    │
#   │ CachingOptimizedForUncom │ Same + no compression.        │
#   │  pressedObjects          │ For already-compressed files.  │
#   │ Elemental-MediaPackage   │ For video streaming.          │
#   ├──────────────────────────┼───────────────────────────────┤
#   │ AllViewer                │ Forward all headers to origin. │
#   │ AllViewerExceptHostHeader│ Forward all except Host.       │
#   │ AllViewerAndCloudFront...│ Forward all + CF geo headers.  │
#   │ CORS-S3Origin            │ Forward CORS headers to S3.   │
#   │ UserAgentRefererHeaders  │ Forward User-Agent + Referer.  │
#   └──────────────────────────┴───────────────────────────────┘
#
# ── Cache Invalidation ───────────────────────────────────────
#
#   When you update content at the origin (new version of an image,
#   updated CSS), CloudFront still serves the old cached version
#   until the TTL expires. Invalidation forces CloudFront to
#   discard the cached copy.
#
#   AWS Console:
#     CloudFront → Distribution → Invalidations tab
#     → Create invalidation
#     → Enter paths:
#       /covers/abc123.jpg     ← single file
#       /covers/*              ← all files under /covers/
#       /*                     ← everything (nuclear option)
#
#   CLI:
#     aws cloudfront create-invalidation \
#       --distribution-id E1234ABCDEF \
#       --paths "/covers/*" "/static/main.css"
#
#   Cost: First 1000 paths/month FREE. Then $0.005 per path.
#         /covers/* counts as ONE path (wildcard = 1 path).
#
#   Better alternative: VERSION your files instead of invalidating.
#     /static/main-v2.css instead of /static/main.css
#     → New URL = automatic cache miss = no invalidation needed.
#     → This is what production build tools do (Webpack content hash).
#
# ── CloudFront Functions vs Lambda@Edge ──────────────────────
#
#   Both let you run code at the edge. Different use cases:
#
#   ┌──────────────────┬────────────────────┬──────────────────┐
#   │                  │ CloudFront         │ Lambda@Edge      │
#   │                  │ Functions          │                  │
#   ├──────────────────┼────────────────────┼──────────────────┤
#   │ Language         │ JavaScript (ES 5.1)│ Node.js, Python  │
#   │ Max runtime      │ 1 ms               │ 5s (viewer)      │
#   │                  │                    │ 30s (origin)     │
#   │ Max memory       │ 2 MB               │ 128-10240 MB     │
#   │ Network access   │ No                 │ Yes              │
#   │ File system      │ No                 │ Yes (/tmp 512MB) │
#   │ Runs at          │ Edge locations     │ Regional edge    │
#   │ Triggers         │ Viewer req/resp    │ Viewer + Origin  │
#   │                  │ only               │ req/resp (all 4) │
#   │ Cost             │ $0.10 / 1M inv     │ $0.60 / 1M inv   │
#   │ Scale            │ 10M+ req/sec       │ 10K req/sec      │
#   │ Deploy speed     │ Seconds            │ Minutes (global) │
#   └──────────────────┴────────────────────┴──────────────────┘
#
#   4 trigger points where you can run code:
#
#   Viewer Request  → before cache lookup  (modify/reject incoming req)
#   Origin Request  → on cache miss only   (modify request to origin)
#   Origin Response → on cache miss only   (modify response from origin)
#   Viewer Response → before returning     (modify response to user)
#
#   Client → [Viewer Req] → Cache → [Origin Req] → Origin
#                                                      ↓
#   Client ← [Viewer Resp] ← Cache ← [Origin Resp] ← Response
#
#   CloudFront Functions ONLY run at Viewer Request / Viewer Response.
#   Lambda@Edge runs at ALL FOUR points.
#
#   Use CloudFront Functions for:
#     - URL rewrites/redirects
#     - Header manipulation (add security headers)
#     - Simple A/B testing (route to different origins)
#     - Normalize cache keys (lowercase URLs, sort query params)
#     - JWT validation (basic token checks, no network calls)
#
#   Use Lambda@Edge for:
#     - Anything needing network access (auth API calls, DB lookups)
#     - Dynamic image resizing (resize on origin response)
#     - A/B testing with external config
#     - Server-side rendering at the edge
#     - Complex request routing
#
#   CloudFront Function example — add security headers:
#
#     function handler(event) {
#       var response = event.response;
#       var headers = response.headers;
#       headers['strict-transport-security'] =
#         { value: 'max-age=63072000; includeSubdomains; preload' };
#       headers['x-content-type-options'] = { value: 'nosniff' };
#       headers['x-frame-options'] = { value: 'DENY' };
#       headers['x-xss-protection'] = { value: '1; mode=block' };
#       return response;
#     }
#
#   CloudFront Function example — URL rewrite (SPA):
#
#     function handler(event) {
#       var request = event.request;
#       var uri = request.uri;
#       // If no file extension → serve index.html (SPA routing)
#       if (!uri.includes('.')) {
#         request.uri = '/index.html';
#       }
#       return request;
#     }
#
# ── Signed URLs & Signed Cookies ─────────────────────────────
#
#   Restrict access to content — only users with a valid signature
#   can fetch it. Used for premium content, private files, time-
#   limited downloads.
#
#   Signed URLs:
#     Each URL contains an expiration time + cryptographic signature.
#     Your backend generates the signed URL, gives it to the user.
#
#     https://d1234.cloudfront.net/premium/video.mp4
#       ?Expires=1720000000
#       &Signature=ABC123...
#       &Key-Pair-Id=K1234
#
#     → URL works until expiry. Can't be modified (signature breaks).
#     → Use for: individual file downloads, one-time links.
#
#   Signed Cookies:
#     Set a cookie with the signature. ALL requests with that cookie
#     are authorized. No URL changes needed.
#
#     Set-Cookie: CloudFront-Policy=ABC123...; Path=/premium/;
#     Set-Cookie: CloudFront-Signature=XYZ789...; Path=/premium/;
#     Set-Cookie: CloudFront-Key-Pair-Id=K1234; Path=/premium/;
#
#     → Use for: streaming (HLS/DASH with many segment files),
#       or when you don't want to modify URLs.
#
#   Setup:
#     1. CloudFront → Key management → Key groups
#        → Create a CloudFront key pair (RSA 2048)
#     2. Distribution → Behavior → "Restrict viewer access" = Yes
#        → Trusted key groups → select your key group
#     3. In your backend code, use the private key to sign URLs/cookies
#
#   Python signing example (boto3):
#
#     from datetime import datetime, timedelta
#     from botocore.signers import CloudFrontSigner
#     import rsa
#
#     def rsa_signer(message):
#         with open('private_key.pem', 'rb') as f:
#             private_key = rsa.PrivateKey.load_pkcs1(f.read())
#         return rsa.sign(message, private_key, 'SHA-1')
#
#     cf_signer = CloudFrontSigner('K1234KEYID', rsa_signer)
#     signed_url = cf_signer.generate_presigned_url(
#         'https://d1234.cloudfront.net/premium/video.mp4',
#         date_less_than=datetime.utcnow() + timedelta(hours=1)
#     )
#
# ── WAF (Web Application Firewall) Integration ──────────────
#
#   CloudFront integrates with AWS WAF to block malicious traffic
#   BEFORE it reaches your origin. WAF rules are evaluated at
#   every edge location.
#
#   AWS Console:
#     CloudFront → Distribution → General tab → "Edit"
#     → AWS WAF web ACL → select or create one
#
#   Common WAF rules:
#     - Rate limiting:   Block IPs exceeding 2000 req/5min
#     - Geo blocking:    Block traffic from specific countries
#     - SQL injection:   Block requests with SQL in query strings
#     - XSS protection:  Block requests with script tags
#     - IP allowlist:    Only allow known IP ranges
#     - Bot control:     Block known bad bots
#
#   AWS Managed Rule Groups (pre-built, free/paid):
#     AWSManagedRulesCommonRuleSet     → OWASP top 10 protection
#     AWSManagedRulesKnownBadInputs    → Log4j, etc.
#     AWSManagedRulesSQLiRuleSet       → SQL injection
#     AWSManagedRulesAmazonIpReputation → Known bad IPs
#     AWSManagedRulesBotControlRuleSet  → Bot detection ($10/month)
#
#   WAF Cost: $5/month per web ACL + $1/month per rule + $0.60/1M req
#
# ── Origin Failover (Origin Groups) ─────────────────────────
#
#   If your primary origin fails, CloudFront automatically
#   switches to a backup origin. No DNS changes needed.
#
#   Primary (ALB eu-west-1)
#     │
#     ├── 200 OK → return response
#     │
#     └── 500/502/503/504 → failover ──► Secondary (ALB us-east-1)
#
#   Setup:
#     1. Add both origins to the distribution
#     2. CloudFront → Origins tab → "Create origin group"
#        ┌──────────────────────────────────────────────────┐
#        │  Primary origin:   ALB eu-west-1                 │
#        │  Secondary origin: ALB us-east-1                 │
#        │                                                   │
#        │  Failover criteria (HTTP status codes):           │
#        │    ✅ 500  Internal Server Error                  │
#        │    ✅ 502  Bad Gateway                            │
#        │    ✅ 503  Service Unavailable                    │
#        │    ✅ 504  Gateway Timeout                        │
#        └──────────────────────────────────────────────────┘
#     3. In the behavior, select the origin GROUP instead of
#        a single origin.
#
#   Real-world: The skills repo deploys to eu-west-1 and us-east-1
#   for production. Origin groups could provide automatic failover
#   between the two regions.
#
# ── Custom Error Pages ───────────────────────────────────────
#
#   When the origin returns an error (404, 500, etc.), CloudFront
#   can return a custom error page instead of the raw error.
#
#   CloudFront → Distribution → Error pages tab → "Create custom error response"
#
#   ┌──────────────────────────────────────────────────┐
#   │  HTTP error code:     404                         │
#   │  Customize response:  Yes                         │
#   │  Response page path:  /errors/404.html            │
#   │  Response code:       404                         │
#   │  Error caching TTL:   60 seconds                  │
#   └──────────────────────────────────────────────────┘
#
#   For SPAs (React, Vue, Angular):
#     Map 403 and 404 → /index.html with response code 200
#     → CloudFront serves the SPA shell, client-side router handles it
#
#     ┌──────────────────────────────────────────────────┐
#     │  HTTP error code:     403                         │
#     │  Response page path:  /index.html                 │
#     │  Response code:       200                         │
#     │  Error caching TTL:   0                           │
#     │                                                    │
#     │  (Repeat for 404)                                  │
#     └──────────────────────────────────────────────────┘
#
# ── Price Classes ────────────────────────────────────────────
#
#   Control which edge locations CloudFront uses. Fewer locations
#   = lower cost but higher latency for distant users.
#
#   ┌──────────────────────┬───────────────────────────────────┐
#   │ Price Class All      │ All 400+ edge locations.          │
#   │ (default)            │ Best performance, highest cost.   │
#   ├──────────────────────┼───────────────────────────────────┤
#   │ Price Class 200      │ US, Canada, Europe, Asia, Middle  │
#   │                      │ East, Africa. Excludes South      │
#   │                      │ America, Australia.               │
#   ├──────────────────────┼───────────────────────────────────┤
#   │ Price Class 100      │ US, Canada, Europe only.          │
#   │ (cheapest)           │ Good for internal/regional apps.  │
#   └──────────────────────┴───────────────────────────────────┘
#
#   Data transfer pricing (per GB, varies by region):
#     US/Europe:    $0.085/GB (first 10TB)
#     Asia:         $0.114/GB
#     South America: $0.110/GB
#     → First 1TB/month is FREE (free tier)
#
# ── Logging & Monitoring ─────────────────────────────────────
#
#   Standard Logs (free):
#     S3 bucket receives log files every few minutes.
#     Each log line: timestamp, edge location, client IP, URI,
#     status code, bytes, cache hit/miss, time-to-first-byte.
#
#     Setup: Distribution → General → Settings → Edit
#     → Standard logging: On → S3 bucket: your-logs-bucket
#     → Prefix: cloudfront-logs/
#
#   Real-Time Logs (paid):
#     Stream to Kinesis Data Streams within seconds.
#     Can sample (e.g., 10% of requests) to save cost.
#     From Kinesis → Kinesis Firehose → S3/Elasticsearch/Splunk.
#
#   CloudWatch Metrics (automatic, free):
#     Requests, BytesDownloaded, BytesUploaded,
#     4xxErrorRate, 5xxErrorRate, TotalErrorRate,
#     CacheHitRate ← most important metric
#
#   Cache Hit Ratio goal:
#     90%+ for static sites
#     70-80% for mixed static/dynamic
#     0% for pure API (CachingDisabled) — expected and fine
#
# ── CloudFront for Different Architectures ───────────────────
#
#   1. Static Website (S3 + CloudFront):
#      ┌──────────────────────────────────────────────────┐
#      │  Origin:   S3 bucket (OAC access)                │
#      │  Cache:    CachingOptimized (24h TTL)            │
#      │  Compress: Yes (gzip + brotli)                    │
#      │  HTTPS:    Redirect HTTP → HTTPS                  │
#      │  Error:    404 → /index.html, 200 (for SPA)      │
#      │  Function: URL rewrite (/ → /index.html)          │
#      └──────────────────────────────────────────────────┘
#
#   2. API Only (ALB + CloudFront):
#      ┌──────────────────────────────────────────────────┐
#      │  Origin:   ALB (HTTP only, internal)              │
#      │  Cache:    CachingDisabled                        │
#      │  Methods:  ALL (GET, POST, PUT, DELETE, etc.)     │
#      │  Forward:  AllViewer (all headers to origin)       │
#      │  HTTPS:    Redirect HTTP → HTTPS                  │
#      │  WAF:      Enabled (rate limiting + bot control)  │
#      └──────────────────────────────────────────────────┘
#
#   3. Mixed (S3 static + ALB API — the book-store pattern):
#      ┌──────────────────────────────────────────────────┐
#      │  Behavior 1: /covers/*  → S3 (CachingOptimized)  │
#      │  Behavior 2: /static/*  → S3 (CachingOptimized)  │
#      │  Default:    /*         → ALB (CachingDisabled)   │
#      └──────────────────────────────────────────────────┘
#
#   4. Multi-Region Failover:
#      ┌──────────────────────────────────────────────────┐
#      │  Origin Group:                                    │
#      │    Primary:   ALB eu-west-1                       │
#      │    Secondary: ALB us-east-1                       │
#      │  Failover on: 500, 502, 503, 504                  │
#      └──────────────────────────────────────────────────┘
#
# ── HTTP/2 and HTTP/3 ────────────────────────────────────────
#
#   CloudFront supports HTTP/2 (enabled by default) and HTTP/3
#   (opt-in). These are between the viewer and CloudFront only —
#   CloudFront talks HTTP/1.1 to origins.
#
#   HTTP/2:  Multiplexing (multiple requests on one connection),
#            header compression, server push. ~30% faster.
#
#   HTTP/3:  Uses QUIC (UDP instead of TCP). Better on unstable
#            networks (mobile). 0-RTT connection establishment.
#            Enable: Distribution → General → Edit → HTTP/3: On
#
# ── Common Gotchas ───────────────────────────────────────────
#
#   1. ACM certificate MUST be in us-east-1 for CloudFront.
#      Your ALB cert can be in any region, but CloudFront
#      only reads certs from us-east-1.
#
#   2. ALB must be internet-facing. CloudFront can't reach
#      internal ALBs. (Use VPC origins for private ALBs —
#      newer feature, more complex setup.)
#
#   3. CloudFront→ALB uses HTTP by default. The TLS termination
#      happens at CloudFront (viewer→CF = HTTPS, CF→ALB = HTTP).
#      If you need end-to-end encryption, set origin protocol
#      to HTTPS and put an ACM cert on the ALB too.
#
#   4. Don't cache API responses unless you're sure they're
#      the same for all users. A cached authenticated response
#      served to the wrong user = security incident.
#
#   5. If your API is behind CloudFront with CachingDisabled,
#      CloudFront still adds latency (~5-15ms) vs direct ALB.
#      The benefit is WAF, HTTPS termination, and DDoS protection.
#
#   6. Max request body size through CloudFront: 20 GB.
#      But for file uploads, consider pre-signed S3 URLs instead
#      (client uploads directly to S3, bypasses CloudFront).
#
#   7. WebSocket connections work through CloudFront.
#      Set allowed methods to include GET, HEAD, OPTIONS.
#      CloudFront detects the Upgrade header and proxies the
#      WebSocket connection to the origin.
#
#   8. CloudFront Functions have a 1ms time limit and no network
#      access. If your function does anything slow, it'll fail.
#      Use Lambda@Edge for anything beyond simple rewrites.
