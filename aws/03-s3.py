# ══════════════════════════════════════════════════════════════════
# AWS Deployment — S3 (Step 2)
# ══════════════════════════════════════════════════════════════════
# Navigation:  ← prev: 02-vpc.py  |  next: 04-ec2.py →

# ╔══════════════════════════════════════════════════╗
# ║         STEP 2: S3 — FILE STORAGE               ║
# ╚══════════════════════════════════════════════════╝
#
# WHAT: Simple Storage Service. Stores ANY file (images, PDFs, logs,
#       deployment artifacts, static websites). Unlimited storage.
#       Files are called "objects", folders are called "prefixes".
#
# COST: ~$0.023/GB/month. Almost free for small projects.
#
# ── AWS Console Steps ───────────────────────────────────────
#
#   1. AWS Console → search "S3" → click S3
#
#   2. Click "Create bucket" (orange button)
#
#   3. Fill in:
#      ┌──────────────────────────────────────────────────┐
#      │  Bucket name: book-store-covers-<your-acct-id>   │
#      │               (must be globally unique!)          │
#      │  AWS Region:  Same as your VPC (e.g. eu-west-1)  │
#      │                                                    │
#      │  Object Ownership: ACLs disabled (recommended)    │
#      │                                                    │
#      │  Block Public Access: ✅ Block ALL (on)           │
#      │  (We serve files via CloudFront, not direct S3)   │
#      │                                                    │
#      │  Bucket Versioning: ✅ Enable                     │
#      │  (Recover accidentally deleted/overwritten files)  │
#      │                                                    │
#      │  Encryption: SSE-S3 (default, free)               │
#      └──────────────────────────────────────────────────┘
#
#   4. Click "Create bucket"
#
#   5. Test: Click into the bucket → "Upload" → drag any image
#      → "Upload". You'll see it listed.
#
# ── Key S3 Concepts ─────────────────────────────────────────
#
#   Bucket:      Top-level container. Name is globally unique across ALL
#                AWS accounts. Like a drive letter.
#   Object:      A file. Identified by key (path): "covers/abc123.jpg"
#   Prefix:      Folder-like path: "covers/" — not a real folder, just
#                a naming convention. S3 is flat storage.
#   Versioning:  Keep every version of every object. Can recover deleted files.
#   Lifecycle:   Auto-move old objects to cheaper storage or delete them.
#   ACL vs Policy: Use bucket policies (JSON). ACLs are legacy.
#
#   Storage Classes:
#     Standard         → frequent access ($0.023/GB)
#     Infrequent (IA)  → rarely accessed ($0.0125/GB, retrieval fee)
#     Glacier          → archive, minutes-to-hours retrieval ($0.004/GB)
#     Glacier Deep     → long-term archive, 12-hour retrieval ($0.00099/GB)
#
# ── S3 Bucket Policy (allow CloudFront to read) ─────────────
#
#   Bucket → Permissions → Bucket policy → paste:
#
#   {
#     "Version": "2012-10-17",
#     "Statement": [{
#       "Sid": "AllowCloudFrontOAC",
#       "Effect": "Allow",
#       "Principal": {"Service": "cloudfront.amazonaws.com"},
#       "Action": "s3:GetObject",
#       "Resource": "arn:aws:s3:::book-store-covers-<acct-id>/*",
#       "Condition": {
#         "StringEquals": {
#           "AWS:SourceArn": "arn:aws:cloudfront::<acct-id>:distribution/<dist-id>"
#         }
#       }
#     }]
#   }
#   (You'll fill in <dist-id> after creating CloudFront in Step 10)
