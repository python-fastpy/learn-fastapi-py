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
