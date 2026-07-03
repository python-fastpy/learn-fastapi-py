# ══════════════════════════════════════════════════════════════════
# AWS Deployment — Route 53 + CloudFront + ACM (Step 10)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 10-cloudwatch.py  |  next: 12-cloudfront-deep-dive.py →

# ╔══════════════════════════════════════════════════╗
# ║  STEP 10: ROUTE 53 + CLOUDFRONT + ACM            ║
# ╚══════════════════════════════════════════════════╝
#
# These three services work together to give you:
#   books.yourname.com → HTTPS → CDN → your app
#
# REAL REPO: Skills ALB gets a Route53 ALIAS record:
#   skills.leon-ci.8335.aws-int.thomsonreuters.com → ALB
#   EDGE API Gateway automatically gets CloudFront.
#
# ── Route 53 (DNS) ──────────────────────────────────────────
#
# WHAT: AWS's DNS service. Translates domain names → IP addresses.
#       Also does health checks and failover routing.
#
# DNS Record Types:
#   ┌────────┬────────────────────────────────────────────────┐
#   │ A      │ Domain → IPv4 address                          │
#   │        │ books.example.com → 1.2.3.4                    │
#   ├────────┼────────────────────────────────────────────────┤
#   │ AAAA   │ Domain → IPv6 address                          │
#   ├────────┼────────────────────────────────────────────────┤
#   │ CNAME  │ Domain → another domain name                   │
#   │        │ books.example.com → alb-123.amazonaws.com      │
#   │        │ CANNOT be used at zone apex (example.com)      │
#   ├────────┼────────────────────────────────────────────────┤
#   │ ALIAS  │ AWS-special: domain → AWS resource             │
#   │        │ books.example.com → ALB / CloudFront / S3      │
#   │        │ CAN be used at zone apex. No extra DNS lookup. │
#   │        │ FREE (no charge for ALIAS queries).             │
#   ├────────┼────────────────────────────────────────────────┤
#   │ MX     │ Email routing (not relevant here)              │
#   ├────────┼────────────────────────────────────────────────┤
#   │ TXT    │ Text records (SPF, domain verification)        │
#   └────────┴────────────────────────────────────────────────┘
#
# Hosted Zone Types:
#   Public  → accessible from internet (books.yourname.com)
#   Private → accessible only from within a VPC (internal DNS)
#             The repo uses private: skills.leon-ci.8335.aws-int...
#
# AWS Console Steps — Route 53:
#
#   Option A: You own a domain (or buy one in Route53 ~$12/year)
#
#   1. Route 53 → Hosted zones → "Create hosted zone"
#      ┌──────────────────────────────────────────────────┐
#      │  Domain name: yourname.com                        │
#      │  Type:        Public hosted zone                  │
#      └──────────────────────────────────────────────────┘
#      → Create
#
#   2. Note the 4 NS (name server) records.
#      If you bought domain elsewhere (GoDaddy, Namecheap),
#      go there and set custom name servers to these 4 values.
#
#   Option B: No domain (for learning)
#     Skip Route 53 — use ALB DNS name or API Gateway URL directly.
#     You can always add DNS later.
#
# ── ACM (Certificate Manager) ───────────────────────────────
#
# WHAT: Free SSL/TLS certificates for HTTPS. Auto-renews.
#       Required for HTTPS on ALB and CloudFront.
#
#   IMPORTANT: For CloudFront, certificate MUST be in us-east-1.
#              For ALB, certificate must be in same region as ALB.
#
# AWS Console Steps — ACM:
#
#   1. Switch region to us-east-1 (for CloudFront)
#      AWS Console → search "Certificate Manager" → ACM
#
#   2. Click "Request certificate"
#      ┌──────────────────────────────────────────────────┐
#      │  Certificate type: Public                         │
#      │                                                    │
#      │  Domain names:                                    │
#      │    books.yourname.com                             │
#      │    *.yourname.com      (wildcard — optional)      │
#      │                                                    │
#      │  Validation method:                               │
#      │    ○ DNS validation (recommended — automatic)     │
#      │      ACM gives you a CNAME record to add to       │
#      │      Route 53. It auto-validates.                  │
#      │    ○ Email validation                              │
#      │      AWS emails domain contacts. Manual.           │
#      └──────────────────────────────────────────────────┘
#      → Request
#
#   3. Click into the certificate → "Create records in Route 53"
#      → AWS auto-creates the validation CNAME records
#      → Status changes to "Issued" within ~5 minutes
#
#   4. Also request a certificate in YOUR ALB region (if different
#      from us-east-1) for ALB HTTPS listener.
#
# ── CloudFront (CDN) ────────────────────────────────────────
#
# WHAT: Content Delivery Network. 400+ edge locations worldwide.
#       Caches content close to users. Also provides HTTPS.
#
#   User (Tokyo) → Tokyo Edge → Origin (eu-west-1 ALB)
#                    ↑
#         cached response if available (static files)
#         or pass-through to origin (API calls)
#
# AWS Console Steps — CloudFront:
#
#   1. AWS Console → search "CloudFront" → CloudFront
#
#   2. Click "Create distribution"
#
#   3. Origin Settings:
#      ┌──────────────────────────────────────────────────┐
#      │  Origin domain:  book-store-alb-123.eu-west-1.   │
#      │                  elb.amazonaws.com               │
#      │                  (select your ALB from dropdown)  │
#      │                                                    │
#      │  Protocol:       HTTP only                        │
#      │    (CloudFront→ALB is internal, no need for HTTPS│
#      │     on that leg. HTTPS is client→CloudFront.)     │
#      │                                                    │
#      │  Origin path:    (leave empty)                    │
#      └──────────────────────────────────────────────────┘
#
#   4. Default Cache Behavior:
#      ┌──────────────────────────────────────────────────┐
#      │  Path pattern:          Default (*)               │
#      │  Viewer protocol:      Redirect HTTP to HTTPS    │
#      │                                                    │
#      │  Allowed HTTP methods:  GET, HEAD, OPTIONS,      │
#      │                         PUT, POST, PATCH, DELETE  │
#      │    (ALL methods — it's an API, not a static site) │
#      │                                                    │
#      │  Cache policy:         CachingDisabled            │
#      │    (API responses should NOT be cached)           │
#      │                                                    │
#      │  Origin request policy: AllViewer                 │
#      │    (forward all headers, cookies to origin)       │
#      └──────────────────────────────────────────────────┘
#
#   5. Add S3 Origin (for static files like book covers):
#      → Click "Add origin"
#      ┌──────────────────────────────────────────────────┐
#      │  Origin domain: book-store-covers-xxx.s3...      │
#      │                 (select your S3 bucket)           │
#      │                                                    │
#      │  Origin access: Origin access control settings   │
#      │                 (OAC — recommended)               │
#      │  → Create new OAC:                                │
#      │    Name: book-store-s3-oac                        │
#      │    Signing: Sign requests (recommended)           │
#      └──────────────────────────────────────────────────┘
#
#   6. Add S3 Behavior:
#      → Behaviors tab → Create behavior
#      ┌──────────────────────────────────────────────────┐
#      │  Path pattern:   /covers/*                        │
#      │  Origin:         S3 bucket origin                 │
#      │  Cache policy:   CachingOptimized                 │
#      │    (static files SHOULD be cached at edge)        │
#      └──────────────────────────────────────────────────┘
#
#   7. Settings:
#      ┌──────────────────────────────────────────────────┐
#      │  Alternate domain names (CNAMEs):                 │
#      │    books.yourname.com                             │
#      │                                                    │
#      │  Custom SSL certificate:                          │
#      │    Select your ACM cert from dropdown             │
#      │    (must be in us-east-1!)                         │
#      │                                                    │
#      │  Default root object: (leave empty for APIs)      │
#      │  Price class: Use all edge locations (or cheaper) │
#      └──────────────────────────────────────────────────┘
#      → Create distribution
#
#   8. Wait for Status: "Deployed" (~5-10 minutes)
#
#   9. Copy the distribution domain:
#      d1234abcdef.cloudfront.net
#
# ── Wire It All Together ────────────────────────────────────
#
#   Route 53 → Create/Update A record:
#      ┌──────────────────────────────────────────────────┐
#      │  Record name: books                               │
#      │  Record type: A                                   │
#      │  ✅ Alias: Yes                                    │
#      │  Route to: Alias to CloudFront distribution       │
#      │  → select your distribution                       │
#      └──────────────────────────────────────────────────┘
#
#   Final test:
#     curl https://books.yourname.com/health
#     curl https://books.yourname.com/books
