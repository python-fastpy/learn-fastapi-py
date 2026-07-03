# ══════════════════════════════════════════════════════════════════
# AWS Deployment — WAF (Step 15)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 17-sqs.py  |  next: 19-codedeploy-pipeline.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 15: WAF — WEB APPLICATION FIREWALL         ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Filters malicious HTTP traffic BEFORE it reaches your app.
#       Protects against SQL injection, XSS, bot abuse, DDoS, and
#       other OWASP Top 10 attacks. You write rules; WAF enforces
#       them at the edge.
#
# REAL REPO: CloudFront distributions can integrate WAF for global
#            protection. The skills ALB could also use WAF for rate
#            limiting (prevent abuse of LLM endpoints) and bot
#            protection. WAF was briefly introduced in
#            12-cloudfront-deep-dive.py — this file goes deeper.
#
# ── How WAF Works ───────────────────────────────────────────
#
#   Request → WAF evaluates rules → Allow or Block → App
#
#   ┌──────────┐       ┌───────────────────────────┐       ┌──────────┐
#   │  Client  │──────►│         AWS WAF            │──────►│  Your    │
#   │  Request │       │  ┌─────────────────────┐   │       │  App     │
#   │          │       │  │ Rule 1: Rate limit   │  │       │ (ALB/    │
#   │          │       │  │ Rule 2: Block SQLi   │  │       │  CF/     │
#   │          │       │  │ Rule 3: Geo restrict │  │       │  API GW) │
#   │          │       │  │ Rule 4: IP allowlist │  │       │          │
#   │          │       │  └─────────────────────┘   │       └──────────┘
#   │          │       │  Action: ALLOW / BLOCK     │
#   └──────────┘       └───────────────────────────┘
#                        │                    │
#                   (allowed)            (blocked)
#                        │                    │
#                        ▼                    ▼
#                   reaches app         403 Forbidden
#
# ── Web ACL (Access Control List) ───────────────────────────
#
#   The Web ACL is the TOP-LEVEL WAF resource. It contains:
#     - An ordered list of rules (evaluated top to bottom)
#     - A default action (Allow or Block if no rules match)
#     - Association with a resource (CloudFront, ALB, API Gateway)
#
#   Each rule has an ACTION:
#     Allow   → Let the request through
#     Block   → Return 403 Forbidden
#     Count   → Allow, but log it (for testing rules)
#     CAPTCHA → Challenge the client with a CAPTCHA
#
#   Rule evaluation order MATTERS. First matching rule wins.
#   Place your highest-priority rules first (e.g., IP allowlist
#   before rate limiting).
#
# ── AWS Managed Rule Groups (Free) ─────────────────────────
#
#   AWS provides pre-built rule groups that cover common attacks.
#   You don't write these rules — just enable them.
#
#   ┌──────────────────────────────┬──────────────────────────────┐
#   │ Managed Rule Group           │ What It Blocks               │
#   ├──────────────────────────────┼──────────────────────────────┤
#   │ AWSManagedRulesCommonRuleSet │ OWASP Top 10: XSS, path     │
#   │ (Core Rule Set — CRS)        │ traversal, file inclusion,   │
#   │                              │ protocol violations          │
#   ├──────────────────────────────┼──────────────────────────────┤
#   │ AWSManagedRulesKnownBad      │ Log4j/Log4Shell, Java       │
#   │ InputsRuleSet                │ deserialization, known CVEs  │
#   ├──────────────────────────────┼──────────────────────────────┤
#   │ AWSManagedRulesSQLiRuleSet   │ SQL injection patterns in   │
#   │                              │ query strings, body, headers │
#   ├──────────────────────────────┼──────────────────────────────┤
#   │ AWSManagedRulesAmazonIp      │ Requests from known bad IPs:│
#   │ ReputationList               │ botnets, scanners, scrapers │
#   ├──────────────────────────────┼──────────────────────────────┤
#   │ AWSManagedRulesAnonymousIp   │ VPN, Tor, hosting provider  │
#   │ List                         │ IPs (optional — may over-    │
#   │                              │ block legitimate users)      │
#   ├──────────────────────────────┼──────────────────────────────┤
#   │ AWSManagedRulesLinuxRuleSet  │ Linux-specific exploits      │
#   │                              │ (LFI, command injection)     │
#   └──────────────────────────────┴──────────────────────────────┘
#
#   Recommended starting combo:
#     1. AWSManagedRulesCommonRuleSet     (general OWASP)
#     2. AWSManagedRulesKnownBadInputsRuleSet (Log4j, etc.)
#     3. AWSManagedRulesAmazonIpReputationList (bad IP blocking)
#
# ── Rate-Based Rules ────────────────────────────────────────
#
#   Block IP addresses that exceed a request threshold within
#   a 5-minute window. Automatic, no manual IP management.
#
#   Example: Block any IP sending more than 2,000 requests
#   in 5 minutes to the /api/ path.
#
#   ┌──────────────────────────────────────────────────┐
#   │  Rule type:       Rate-based                      │
#   │  Rate limit:      2,000 requests per 5 minutes    │
#   │  Scope:           URI path starts with "/api/"    │
#   │  Action:          Block                           │
#   │                                                    │
#   │  When an IP exceeds 2,000 requests/5min:           │
#   │    → WAF automatically blocks that IP              │
#   │    → When rate drops below threshold, unblocks     │
#   └──────────────────────────────────────────────────┘
#
#   This is critical for LLM-based APIs like the skills endpoints.
#   Without rate limiting, a single client could consume enormous
#   compute by spamming generate_spot_story calls.
#
# ── Geo-Matching Rules ──────────────────────────────────────
#
#   Allow or block requests based on the country of origin.
#
#   Use cases:
#     - Block countries where you don't have users
#     - Comply with export regulations (sanctions)
#     - Reduce attack surface from high-risk regions
#
#   Example: Only allow traffic from US, UK, and EU:
#     → Geo match condition: Country NOT IN [US, GB, DE, FR, ...]
#     → Action: Block
#
# ── IP Set Rules ────────────────────────────────────────────
#
#   Allowlist or blocklist specific IP addresses or CIDR ranges.
#
#   Allowlist example: Only allow your office IPs to access /admin:
#     → IP set: [10.0.0.0/8, 172.16.0.0/12]
#     → Condition: URI path = "/admin"
#     → Action: Allow (with higher priority than other rules)
#
#   Blocklist example: Block known attacker IPs immediately:
#     → IP set: [1.2.3.4/32, 5.6.0.0/16]
#     → Action: Block
#
# ── Custom Rules with Conditions ────────────────────────────
#
#   Build fine-grained rules matching request properties:
#
#   ┌──────────────────────┬──────────────────────────────────┐
#   │ Match condition      │ Example                          │
#   ├──────────────────────┼──────────────────────────────────┤
#   │ URI path             │ Starts with "/api/v1/admin"      │
#   │ Query string         │ Contains "UNION SELECT"          │
#   │ Header               │ User-Agent contains "sqlmap"     │
#   │ Body                 │ Size exceeds 10 KB               │
#   │ HTTP method          │ Not in [GET, POST, PUT, DELETE]  │
#   │ Country              │ Origin country = CN              │
#   │ IP address           │ Source IP in CIDR range          │
#   │ Label (from other    │ Has label "awswaf:managed:       │
#   │  rules)              │  aws:bot-control:signal:non-     │
#   │                      │  browser-user-agent"             │
#   └──────────────────────┴──────────────────────────────────┘
#
#   You can combine conditions with AND/OR/NOT logic.
#
# ── WAF Integration Points ─────────────────────────────────
#
#   WAF can protect these AWS services:
#
#   ┌────────────────────┬──────────────────────────────────────┐
#   │ Service            │ When to Use                          │
#   ├────────────────────┼──────────────────────────────────────┤
#   │ CloudFront         │ Global protection at the edge.       │
#   │                    │ Best performance (lowest latency).   │
#   │                    │ Must use WAF in us-east-1.           │
#   ├────────────────────┼──────────────────────────────────────┤
#   │ ALB                │ Regional protection for container    │
#   │                    │ workloads. Used for skills ALB.      │
#   │                    │ WAF in same region as ALB.           │
#   ├────────────────────┼──────────────────────────────────────┤
#   │ API Gateway        │ Protect REST/HTTP APIs. WAF in       │
#   │                    │ same region as the API.              │
#   ├────────────────────┼──────────────────────────────────────┤
#   │ AppSync            │ Protect GraphQL APIs.                │
#   └────────────────────┴──────────────────────────────────────┘
#
#   For the book-store: attach WAF to your ALB or CloudFront.
#   For the real repo: attach to the skills shared ALB and/or
#   the CloudFront distribution.
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console → search "WAF" → click "WAF & Shield"
#
#   2. Click "Create web ACL"
#      ┌──────────────────────────────────────────────────┐
#      │  Name:        book-store-waf                       │
#      │  Region:      EU (Ireland) eu-west-1               │
#      │    (Use "Global (CloudFront)" if attaching to CF)  │
#      │  Resource type: Regional resources                 │
#      │                                                    │
#      │  Associated resources: Add AWS resources           │
#      │    → Select your ALB: book-store-alb               │
#      └──────────────────────────────────────────────────┘
#      → Next
#
#   3. Add managed rule groups:
#      ┌──────────────────────────────────────────────────┐
#      │  Add managed rule groups:                          │
#      │                                                    │
#      │  ☑ AWS managed rule groups (free):                 │
#      │    ☑ Core rule set (CRS) — Action: Block           │
#      │    ☑ Known bad inputs     — Action: Block           │
#      │    ☑ Amazon IP reputation — Action: Block           │
#      │    ☐ SQL database         — (enable if using SQL)   │
#      │    ☐ Linux OS             — (enable if on Linux)    │
#      │                                                    │
#      │  ☐ AWS Marketplace rule groups (paid):             │
#      │    ☐ Bot Control          — $10/month + per-req     │
#      │    ☐ Account takeover     — $10/month + per-req     │
#      └──────────────────────────────────────────────────┘
#      → Next
#
#   4. Add a rate-based rule:
#      ┌──────────────────────────────────────────────────┐
#      │  Rule name:   rate-limit-api                       │
#      │  Type:        Rate-based rule                      │
#      │  Rate limit:  2000  (requests per 5 minutes)       │
#      │  Action:      Block                                │
#      │                                                    │
#      │  Optional scope-down: URI path starts with /api/   │
#      └──────────────────────────────────────────────────┘
#      → Add rule → Next
#
#   5. Set rule priority (evaluation order):
#      1. rate-limit-api        (stop abusers first)
#      2. IP reputation list    (block known bad IPs)
#      3. Known bad inputs      (block Log4j etc.)
#      4. Core rule set         (OWASP general)
#      → Next
#
#   6. Default action: Allow
#      (requests not matching any rule are allowed through)
#      → Next → Create web ACL
#
# ── WAF Logging ─────────────────────────────────────────────
#
#   Log every request WAF evaluates (allowed AND blocked).
#   Essential for debugging false positives and security audits.
#
#   Logging destinations:
#     - CloudWatch Logs (easiest — use Log Insights to query)
#     - S3 bucket (cheapest for long-term storage)
#     - Kinesis Data Firehose (real-time analytics pipeline)
#
#   Setup:
#     Web ACL → Logging → Enable logging
#     → Resource: CloudWatch log group
#     → Log group name must start with: aws-waf-logs-
#     → Filter: Log only blocked requests (reduces volume/cost)
#
#   Log format includes: timestamp, action (ALLOW/BLOCK/COUNT),
#   matching rule, client IP, URI, headers, country.
#
# ── Bot Control (Paid Managed Rule Group) ───────────────────
#
#   Beyond basic rate limiting, AWS offers an intelligent bot
#   detection rule group that identifies:
#     - Known bots (Google, Bing crawlers — allow these)
#     - Unknown bots (scrapers, vulnerability scanners)
#     - Browser fingerprint anomalies
#
#   Cost: $10/month + $1.00 per 1 million requests inspected.
#   Worth it for production APIs with public exposure.
#
# ── AWS Shield (DDoS Protection) ────────────────────────────
#
#   WAF protects against application-layer attacks (Layer 7).
#   Shield protects against network-layer attacks (Layer 3/4).
#
#   ┌──────────────────────┬───────────────────┬───────────────────┐
#   │                      │ Shield Standard   │ Shield Advanced   │
#   ├──────────────────────┼───────────────────┼───────────────────┤
#   │ Cost                 │ Free (automatic)  │ $3,000/month      │
#   │ Protection           │ Common DDoS       │ Sophisticated DDoS│
#   │ Scope                │ All AWS resources  │ Enrolled resources│
#   │ DDoS Response Team   │ No                │ 24/7 access       │
#   │ Cost protection      │ No                │ Credits for scale │
#   │                      │                   │ events             │
#   │ WAF included         │ No                │ Yes (WAF free)    │
#   └──────────────────────┴───────────────────┴───────────────────┘
#
#   Shield Standard is always on — you're already protected
#   against basic volumetric DDoS at no cost.
#
#   Shield Advanced is for high-value targets expecting
#   sophisticated attacks. The $3,000/mo includes free WAF.
#
# ── Cost ────────────────────────────────────────────────────
#
#   Web ACL:        $5.00/month per Web ACL
#   Rules:          $1.00/month per rule
#   Requests:       $0.60 per 1 million requests inspected
#   Bot Control:    $10.00/month + $1.00 per 1M requests
#   Shield Standard: Free
#   Shield Advanced: $3,000/month
#
#   Example (book-store with 3 managed groups + 1 custom rule):
#     1 Web ACL:                    $5.00
#     3 managed rule groups:        $0 (free managed rules)
#     1 rate-based custom rule:     $1.00
#     500,000 requests/month:       $0.30
#     Total: ~$6.30/month
#
#   Example (production skills ALB, moderate traffic):
#     1 Web ACL:                    $5.00
#     3 managed + 2 custom rules:   $2.00
#     5 million requests/month:     $3.00
#     Bot Control:                  $10.00 + $5.00
#     Total: ~$25/month
#
# ── Common Gotchas ──────────────────────────────────────────
#
#   1. Rule evaluation order matters. Rules are evaluated
#      top-to-bottom. First match wins. If your allowlist rule
#      is BELOW a block rule, the allowlist never fires.
#      Put allowlists first, then rate limits, then blocks.
#
#   2. False positives from managed rules. The Core Rule Set
#      may block legitimate requests (e.g., JSON body that
#      looks like SQL). ALWAYS deploy in COUNT mode first for
#      1-2 weeks, review logs, then switch to BLOCK.
#
#   3. WAF does NOT protect against network-layer DDoS.
#      WAF operates at Layer 7 (HTTP). For volumetric attacks
#      (UDP/SYN floods), rely on Shield Standard (automatic)
#      or Shield Advanced.
#
#   4. CloudFront WAF must be in us-east-1. Even if your app
#      is in eu-west-1, the Web ACL for a CloudFront distribution
#      MUST be created in the us-east-1 region.
#
#   5. Each Web ACL can protect multiple resources, but each
#      resource can only have ONE Web ACL. You can't stack
#      two Web ACLs on the same ALB.
#
#   6. Managed rule group updates are automatic. AWS updates
#      managed rules to address new threats. Usually good, but
#      an update could introduce a false positive. Monitor
#      after rule group version changes.
#
#   7. WAF pricing adds up with high traffic. At 100M requests/
#      month, WAF inspection alone costs $60. For very high-
#      traffic sites, evaluate whether Shield Advanced (which
#      includes WAF) is more economical.
