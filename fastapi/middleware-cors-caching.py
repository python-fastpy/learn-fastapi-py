# ══════════════════════════════════════════════════════════════════
# 4. MIDDLEWARE, CORS & CACHING
#
# Middleware = code that runs BEFORE and AFTER every request
# Request -> MW1 -> MW2 -> Endpoint -> MW2 -> MW1 -> Response (onion model)
# CORS = which websites can call your API from a browser
# Caching = store responses to avoid recomputing
# NOTE: Middleware functions MUST be async def; endpoints can be sync
# ══════════════════════════════════════════════════════════════════
import time, hashlib, json
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()
shipment_data = {
    1: {"id": 1, "content": "Shipment 1", "weight": 10, "status": "In Transit"},
    2: {"id": 2, "content": "Shipment 2", "weight": 20, "status": "Delivered"},
    3: {"id": 3, "content": "Shipment 3", "weight": 15, "status": "Pending"},
}

# ╔══════════════════════════════════════════════════╗
# ║              BEGINNER                            ║
# ╚══════════════════════════════════════════════════╝

# ── 1. CORS — Allow Frontend to Call Your API ─────────────────────
# Without CORS: browser blocks requests from different origins
# allow_origins = which sites | allow_methods = which HTTP verbs
# allow_headers = which headers | allow_credentials = cookies/auth

# OPTION A: Specific origins (RECOMMENDED for prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "https://myapp.example.com"],
    allow_credentials=True,                                        # allow cookies/JWT
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)
# OPTION B: allow_origins=["*"], allow_credentials=False           — any site, dev/public APIs only
# OPTION C: allow_origin_regex=r"https://.*\.example\.com"         — regex pattern matching

@app.get("/cors/test")
def cors_test():
    return {"message": "If CORS is set up, your frontend can call this"}

# ── 2. GZip — Compress Responses ──────────────────────────────────
# Compresses responses > minimum_size bytes (60-90% smaller for JSON)
app.add_middleware(GZipMiddleware, minimum_size=500)

@app.get("/middleware/gzip-test")
def gzip_test():
    return {"data": [shipment_data[k] for k in shipment_data] * 50}
# curl -H "Accept-Encoding: gzip" http://localhost:8000/middleware/gzip-test

# ── 3. TrustedHost — Block Unknown Hosts ──────────────────────────
# Prevents Host header attacks; non-matching Host -> 400
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "myapp.example.com", "*.example.com"],
)

# ╔══════════════════════════════════════════════════╗
# ║            INTERMEDIATE                          ║
# ╚══════════════════════════════════════════════════╝

# ── 4. Custom Middleware — Process Time Header ────────────────────
# request = incoming | call_next = calls next middleware/endpoint | response = result
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    response.headers["X-Process-Time"] = str(round(time.time() - start, 4))
    return response  # curl -v ... -> X-Process-Time: 0.0012

# ── 5. Custom Middleware — Request Logging ────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"-> {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"<- {request.method} {request.url.path} -> {response.status_code}")
    return response

# ── 6. Custom Middleware — Block Paths ────────────────────────────
# Deny access to /admin/* without correct token
@app.middleware("http")
async def block_admin_routes(request: Request, call_next):
    if request.url.path.startswith("/admin"):
        if request.headers.get("Authorization", "") != "Bearer admin-secret-token":
            return JSONResponse(status_code=403, content={"detail": "Admin access denied"})
    return await call_next(request)

@app.get("/admin/dashboard")
def admin_dashboard():
    return {"message": "Welcome to admin dashboard"}

# ── 7. Custom Middleware — Rate Limiting ──────────────────────────
# Track requests per IP, block if too many in window
request_counts: dict[str, list[float]] = {}
RATE_LIMIT = 10    # max requests
RATE_WINDOW = 60.0 # per N seconds

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    if client_ip not in request_counts:
        request_counts[client_ip] = []
    request_counts[client_ip] = [t for t in request_counts[client_ip] if now - t < RATE_WINDOW]
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})
    request_counts[client_ip].append(now)
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT - len(request_counts[client_ip]))
    return response

# ── 8. Custom Middleware — Exception Handler ──────────────────────
# Catch ALL unhandled exceptions -> clean JSON instead of ugly 500 HTML
@app.middleware("http")
async def catch_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "error": str(e)})

# ╔══════════════════════════════════════════════════╗
# ║              ADVANCED                            ║
# ╚══════════════════════════════════════════════════╝

# ── 9. Middleware Execution Order ─────────────────────────────────
# Middleware runs in REVERSE order of registration!
# Added: A, B, C  ->  Execution: C -> B -> A -> endpoint -> A -> B -> C
# Last added = outermost layer (runs first)

@app.get("/middleware/order-test")
def middleware_order_test():
    return {"message": "Check server logs to see middleware execution order"}

# ── 10. In-Memory Cache (Server-Side) ────────────────────────────
# Dict cache with TTL — fastest, but lost on restart
cache_store: dict[str, dict] = {}
CACHE_TTL = 30  # seconds

@app.get("/cache/simple/{id}")
def get_with_simple_cache(id: int):
    cache_key, now = f"shipment:{id}", time.time()
    if cache_key in cache_store:                                   # check cache
        cached = cache_store[cache_key]
        if now - cached["timestamp"] < CACHE_TTL:
            return {**cached["data"], "_cache": "HIT", "_age": round(now - cached["timestamp"], 1)}
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    result = shipment_data[id]
    cache_store[cache_key] = {"data": result, "timestamp": now}    # store in cache
    return {**result, "_cache": "MISS"}

# ── 11. Cache Invalidation ───────────────────────────────────────
# Delete cache when data changes (PUT/DELETE) to prevent stale data
@app.put("/cache/shipment/{id}")
def update_shipment_and_invalidate(id: int, status: str = "Updated"):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    shipment_data[id]["status"] = status
    cache_store.pop(f"shipment:{id}", None)                        # invalidate
    return {"updated": shipment_data[id], "cache_invalidated": True}

@app.delete("/cache/clear")
def clear_all_cache():
    cache_store.clear()
    return {"message": "All cache cleared"}

# ── 12. HTTP Cache Headers (Client-Side) ─────────────────────────
# Cache-Control tells browsers/CDNs to cache; ETag = data fingerprint
# Client-side caching (browser stores it) vs server-side (dict cache above)
@app.get("/cache/headers/{id}")
def get_with_cache_headers(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    data = shipment_data[id]
    content = json.dumps(data, sort_keys=True)
    etag = hashlib.md5(content.encode()).hexdigest()
    return Response(
        content=content, media_type="application/json",
        headers={"Cache-Control": "public, max-age=60", "ETag": f'"{etag}"'},
    )

# Cache-Control variants:
# no-store                             -> never cache (real-time data, auth tokens)
# private, max-age=300                 -> only browser caches, NOT CDN (user-specific)
# public, max-age=60                   -> browser AND CDN can cache (public data)
# public, max-age=31536000, immutable  -> content NEVER changes at this URL (versioned assets)

# ── 13. Conditional Caching — ETag + If-None-Match ────────────────
# Client sends ETag back -> server checks if data changed
# Unchanged -> 304 Not Modified (no body, saves bandwidth)
# Changed -> 200 with new data + new ETag
@app.get("/cache/conditional/{id}")
def conditional_cache(id: int, request: Request):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    data = shipment_data[id]
    content = json.dumps(data, sort_keys=True)
    etag = hashlib.md5(content.encode()).hexdigest()
    if request.headers.get("If-None-Match", "") == f'"{etag}"':    # client already has this version
        return Response(status_code=304)
    return Response(
        content=content, media_type="application/json",
        headers={"ETag": f'"{etag}"', "Cache-Control": "public, max-age=60"},
    )
# 1st call: curl -v /cache/conditional/1                          -> 200 + ETag
# 2nd call: curl -v -H 'If-None-Match: "<etag>"' /cache/cond/1   -> 304 (no body)

# ── CHEAT SHEET ───────────────────────────────────────────────────
# CORS:
#   Specific origins (prod)   | allow_origins=["https://app.com"]
#   All origins (dev only)    | allow_origins=["*"], allow_credentials=False
#   Regex pattern             | allow_origin_regex=r"https://.*\.example\.com"
#
# BUILT-IN MIDDLEWARE:
#   GZipMiddleware            | Compress responses > N bytes
#   TrustedHostMiddleware     | Block unknown Host headers
#
# CUSTOM MIDDLEWARE PATTERN:
#   @app.middleware("http")
#   async def mw(request: Request, call_next):
#       response = await call_next(request)    # call next layer
#       return response
#
# EXECUTION ORDER:
#   Added A, B, C -> runs C -> B -> A -> endpoint -> A -> B -> C
#
# CACHING COMPARISON:
#   In-memory dict            | Server-side, fast, lost on restart
#   Cache-Control header      | Client-side, browser/CDN stores it
#   ETag + If-None-Match      | Conditional: 304 if unchanged, saves bandwidth
#
# CACHE-CONTROL VALUES:
#   no-store                  | Never cache (real-time, auth)
#   private, max-age=N        | Browser only, no CDN (user data)
#   public, max-age=N         | Browser + CDN (public data)
#   immutable                 | Content never changes (versioned assets)
#
# RATE LIMITING:             Track timestamps per IP, prune old, reject if >= limit
# EXCEPTION MIDDLEWARE:      try/except around call_next -> clean JSON 500
#
# ══════════════════════════════════════════════════════════════════
#  MIDDLEWARE, CORS & CACHING — DETAILED REFERENCE
# ══════════════════════════════════════════════════════════════════
#
# ── CORSMiddleware — Cross-Origin Resource Sharing ───────────────
#   app.add_middleware(CORSMiddleware, allow_origins=[...], ...)
#   allow_origins=["http://localhost:3000"]   → specific origins (RECOMMENDED for prod)
#   allow_origins=["*"]                       → any site (dev/public APIs only)
#   allow_origin_regex=r"https://.*\.example\.com"  → regex pattern
#   allow_credentials=True                    → allow cookies/JWT in cross-origin requests
#   allow_methods=["GET","POST",...]          → which HTTP verbs are allowed
#   allow_headers=["*"]                       → which request headers are allowed
#   Without CORS: browser blocks requests from different origins (same-origin policy)
#
#   BEGINNER EXAMPLE — CORSMiddleware:
#
#     from fastapi.middleware.cors import CORSMiddleware
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["http://localhost:3000"],  # ← React dev server
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )
#
#     # Problem CORS solves:
#     #   React app at http://localhost:3000 calls API at http://localhost:8000
#     #   Browser sees DIFFERENT origins (different ports) → blocks the request!
#     #
#     #   With CORSMiddleware:
#     #   Browser → OPTIONS /api/items (preflight check)
#     #         ← Access-Control-Allow-Origin: http://localhost:3000  ✓
#     #   Browser → GET /api/items (actual request, now allowed)
#     #         ← data + CORS headers
#     #
#     #   allow_origins=["*"]  → any website can call your API (ok for public APIs)
#     #   allow_origins=["http://localhost:3000"] → only React app can call (safer)
#
# ── GZipMiddleware — Response compression ────────────────────────
#   app.add_middleware(GZipMiddleware, minimum_size=500)
#   Compresses responses > minimum_size bytes. 60-90% smaller for JSON.
#   Client must send Accept-Encoding: gzip header.
#
#   BEGINNER EXAMPLE — GZipMiddleware:
#
#     from starlette.middleware.gzip import GZipMiddleware
#     app.add_middleware(GZipMiddleware, minimum_size=500)
#
#     # curl -H "Accept-Encoding: gzip" "http://localhost:8000/big-data"
#     #
#     #   Without GZip:
#     #     Server → 10,000 bytes JSON → Client
#     #
#     #   With GZip:
#     #     Server → compress → 2,000 bytes → Client → decompress → 10,000 bytes
#     #     (60-90% smaller, faster over slow networks)
#     #
#     #   minimum_size=500 → only compress responses > 500 bytes
#     #   (small responses: compression overhead > savings)
#
# ── TrustedHostMiddleware — Host header protection ───────────────
#   app.add_middleware(TrustedHostMiddleware, allowed_hosts=["myapp.com", "*.example.com"])
#   Requests with non-matching Host header → 400 Bad Request.
#   Prevents Host header injection attacks.
#
#   BEGINNER EXAMPLE — TrustedHostMiddleware:
#
#     from starlette.middleware.trustedhost import TrustedHostMiddleware
#     app.add_middleware(TrustedHostMiddleware, allowed_hosts=["myapp.com", "*.myapp.com"])
#
#     # curl -H "Host: myapp.com" "http://localhost:8000/"    → ✓ 200 OK
#     # curl -H "Host: evil.com"  "http://localhost:8000/"    → ✗ 400 Bad Request
#     #
#     # Prevents: attacker sends fake Host header to trick server
#     # into generating links/redirects to evil.com
#
# ── Custom middleware pattern ────────────────────────────────────
#   @app.middleware("http")
#   async def my_middleware(request: Request, call_next):
#       # BEFORE: runs before endpoint
#       response = await call_next(request)  → calls next middleware/endpoint
#       # AFTER: runs after endpoint
#       return response
#   Must be async def. Can modify request before, response after.
#   Can short-circuit: return JSONResponse(...) without calling call_next.
#
#   BEGINNER EXAMPLE — Custom middleware:
#
#     import time
#
#     @app.middleware("http")
#     async def add_timing(request: Request, call_next):
#         start = time.time()                    # BEFORE endpoint
#         response = await call_next(request)    # run endpoint
#         elapsed = time.time() - start          # AFTER endpoint
#         response.headers["X-Process-Time"] = str(elapsed)
#         return response
#
#     # curl -v "http://localhost:8000/any-route"
#     #
#     #   Request arrives
#     #     │
#     #     ▼ BEFORE: start = time.time()
#     #     │
#     #     ▼ call_next(request) → endpoint runs → returns response
#     #     │
#     #     ▼ AFTER: calculate elapsed, add header
#     #     │
#     #   Response sent with X-Process-Time: 0.0023
#     #
#     #   Short-circuit (skip endpoint):
#     #     if "Authorization" not in request.headers:
#     #         return JSONResponse({"error": "No auth"}, status_code=401)
#
# ── Middleware execution order ───────────────────────────────────
#   Registered: A, B, C → Runs: C → B → A → endpoint → A → B → C
#   Last added = outermost layer (runs first). Like an onion — wraps around.
#
#   BEGINNER EXAMPLE — Execution order:
#
#     # Register order:
#     app.add_middleware(A)   # added first
#     app.add_middleware(B)   # added second
#     app.add_middleware(C)   # added last
#
#     # Execution order (REVERSED — like wrapping an onion):
#     #   Request comes in:
#     #     C (before) → B (before) → A (before) → ENDPOINT
#     #   Response goes out:
#     #     A (after)  → B (after)  → C (after)  → CLIENT
#     #
#     #   Visual:
#     #     ┌─── C ────────────────────────────────┐
#     #     │ ┌─── B ──────────────────────────┐   │
#     #     │ │ ┌─── A ────────────────────┐   │   │
#     #     │ │ │       ENDPOINT           │   │   │
#     #     │ │ └──────────────────────────┘   │   │
#     #     │ └────────────────────────────────┘   │
#     #     └──────────────────────────────────────┘
#     #   Last added (C) wraps outermost → runs FIRST on request, LAST on response
#
# ── request: Request — Available in middleware & routes ──────────
#   request.url.path          → "/api/items"
#   request.method            → "GET", "POST", etc.
#   request.headers           → all HTTP headers
#   request.client.host       → client IP address
#   request.cookies           → all cookies
#   request.query_params      → URL query parameters
#
#   BEGINNER EXAMPLE — Request object:
#
#     from fastapi import Request
#
#     @app.get("/debug")
#     async def debug(request: Request):
#         return {
#             "path": request.url.path,            # → "/debug"
#             "method": request.method,             # → "GET"
#             "user_agent": request.headers.get("user-agent"),
#             "client_ip": request.client.host,     # → "127.0.0.1"
#             "cookies": dict(request.cookies),     # → {"session_id": "abc"}
#             "query": dict(request.query_params),  # → {"page": "1"}
#         }
#
#     # curl "http://localhost:8000/debug?page=1" -b "session_id=abc"
#     #   → {"path":"/debug","method":"GET","client_ip":"127.0.0.1",
#     #      "cookies":{"session_id":"abc"},"query":{"page":"1"}}
#
# ── In-memory cache (server-side) ────────────────────────────────
#   cache_store[key] = {"data": result, "timestamp": time.time()}
#   Check: if now - cached["timestamp"] < TTL → return cached (HIT)
#   Invalidate: cache_store.pop(key, None) on PUT/DELETE (prevent stale data)
#   Pros: fastest. Cons: lost on restart, per-process (not shared across workers).
#
#   BEGINNER EXAMPLE — In-memory cache:
#
#     import time
#     cache = {}
#     TTL = 60  # seconds
#
#     @app.get("/items")
#     async def get_items():
#         now = time.time()
#         if "items" in cache and now - cache["items"]["ts"] < TTL:
#             return {"data": cache["items"]["data"], "source": "cache"}  # HIT
#         data = await fetch_items_from_db()          # MISS — query DB
#         cache["items"] = {"data": data, "ts": now}  # store in cache
#         return {"data": data, "source": "db"}
#
#     @app.delete("/items/{id}")
#     async def delete_item(id: int):
#         await db_delete(id)
#         cache.pop("items", None)   # ← invalidate cache (prevent stale data)
#         return {"deleted": id}
#
#     # Flow:
#     #   curl GET /items      → MISS → query DB → cache result → return
#     #   curl GET /items      → HIT  → return from cache (fast!)
#     #   ... 60 seconds pass ...
#     #   curl GET /items      → MISS → cache expired → query DB again
#     #   curl DELETE /items/1 → delete + invalidate cache → next GET re-fetches
#
# ── Cache-Control header (client-side) ───────────────────────────
#   "no-store"                           → never cache (real-time data, auth tokens)
#   "private, max-age=300"               → browser only, NOT CDN (user-specific data)
#   "public, max-age=60"                 → browser + CDN can cache (public data)
#   "public, max-age=31536000, immutable"→ never changes at this URL (versioned assets)
#   Tells browser/CDN to store the response — server not contacted until expiry.
#
#   BEGINNER EXAMPLE — Cache-Control:
#
#     from fastapi.responses import JSONResponse
#
#     @app.get("/public-data")
#     async def public():
#         data = get_public_data()
#         return JSONResponse(data, headers={"Cache-Control": "public, max-age=60"})
#
#     @app.get("/user-profile")
#     async def profile():
#         data = get_user_data()
#         return JSONResponse(data, headers={"Cache-Control": "private, max-age=300"})
#
#     @app.get("/stock-price")
#     async def stock():
#         data = get_live_price()
#         return JSONResponse(data, headers={"Cache-Control": "no-store"})
#
#     # curl -v "http://localhost:8000/public-data"
#     #   ← Cache-Control: public, max-age=60
#     #
#     #   What happens:
#     #     "no-store"         → browser NEVER caches (stock prices, auth tokens)
#     #     "private, 300"     → browser caches 5min, CDN does NOT (user-specific)
#     #     "public, 60"       → browser AND CDN cache 60s (shared public data)
#     #     "immutable"        → never changes at this URL (app.abc123.js)
#     #
#     #   Flow with "public, max-age=60":
#     #     Request 1: Browser → Server → 200 + data (stored in browser cache)
#     #     Request 2 (within 60s): Browser → cache HIT → no server contact!
#     #     Request 3 (after 60s): Browser → Server → fresh 200
#
# ── ETag + If-None-Match (conditional caching) ──────────────────
#   Server: response with ETag: "abc123" (content fingerprint, usually MD5 hash)
#   Client: next request with If-None-Match: "abc123"
#   Server: data unchanged → 304 Not Modified (no body, saves bandwidth)
#   Server: data changed → 200 with new data + new ETag
#   Combines with Cache-Control for optimal caching strategy.
#
#   BEGINNER EXAMPLE — ETag:
#
#     import hashlib, json
#     from fastapi import Response
#
#     @app.get("/article/{id}")
#     async def get_article(id: int, request: Request):
#         article = get_article_from_db(id)
#         etag = hashlib.md5(json.dumps(article).encode()).hexdigest()
#
#         if request.headers.get("if-none-match") == etag:
#             return Response(status_code=304)       # not modified — no body
#
#         return JSONResponse(article, headers={"ETag": etag})
#
#     # Flow:
#     #   1st request:
#     #     curl "http://localhost:8000/article/1"
#     #       ← 200 + {"title":"..."} + ETag: "abc123"
#     #       (browser stores response + ETag)
#     #
#     #   2nd request (data UNCHANGED):
#     #     curl -H "If-None-Match: abc123" "http://localhost:8000/article/1"
#     #       ← 304 Not Modified (NO BODY — saves bandwidth!)
#     #       (browser uses stored version)
#     #
#     #   3rd request (data CHANGED — article was edited):
#     #     curl -H "If-None-Match: abc123" "http://localhost:8000/article/1"
#     #       ← 200 + {"title":"new..."} + ETag: "xyz789"
#     #       (browser replaces stored version)
#
# ── Rate limiting pattern ────────────────────────────────────────
#   Track request timestamps per client IP in a dict.
#   Prune timestamps older than RATE_WINDOW seconds.
#   If count >= RATE_LIMIT → return 429 Too Many Requests.
#   Add X-RateLimit-Remaining header for client awareness.
#
#   BEGINNER EXAMPLE — Rate limiting:
#
#     import time
#     from collections import defaultdict
#
#     RATE_LIMIT = 5       # max requests
#     RATE_WINDOW = 60     # per 60 seconds
#     request_log = defaultdict(list)
#
#     @app.middleware("http")
#     async def rate_limit(request: Request, call_next):
#         ip = request.client.host
#         now = time.time()
#         request_log[ip] = [t for t in request_log[ip] if now - t < RATE_WINDOW]
#
#         if len(request_log[ip]) >= RATE_LIMIT:
#             return JSONResponse(
#                 {"error": "Too many requests"}, status_code=429,
#                 headers={"X-RateLimit-Remaining": "0"}
#             )
#
#         request_log[ip].append(now)
#         remaining = RATE_LIMIT - len(request_log[ip])
#         response = await call_next(request)
#         response.headers["X-RateLimit-Remaining"] = str(remaining)
#         return response
#
#     # curl "http://localhost:8000/anything"  → 200 (X-RateLimit-Remaining: 4)
#     # curl "http://localhost:8000/anything"  → 200 (X-RateLimit-Remaining: 3)
#     # ... 3 more ...
#     # curl "http://localhost:8000/anything"  → 429 "Too many requests"
#     #
#     # After 60 seconds: old timestamps pruned → can make requests again
#
# ══════════════════════════════════════════════════════════════════
