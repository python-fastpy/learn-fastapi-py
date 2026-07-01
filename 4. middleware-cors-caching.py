import time
import hashlib
import json
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


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                    MIDDLEWARE, CORS & CACHING                       ║
# ║                                                                     ║
# ║  Middleware = code that runs BEFORE and AFTER every request          ║
# ║  Request → Middleware 1 → Middleware 2 → Endpoint → Middleware 2 →   ║
# ║  Middleware 1 → Response (like an onion — goes in, comes back out)  ║
# ║                                                                     ║
# ║  CORS = Cross-Origin Resource Sharing — controls which websites     ║
# ║  can call your API from a browser (security feature)                ║
# ║                                                                     ║
# ║  Caching = store responses to avoid recomputing the same result     ║
# ║                                                                     ║
# ║  NOTE: Middleware functions MUST be async def (FastAPI requirement)  ║
# ║  But all ENDPOINTS below are plain def (sync) — no async/await      ║
# ╚══════════════════════════════════════════════════════════════════════╝


# ════════════════════════════════════════════════════
# 1. CORS — allow frontend to call your API
#
#  Without CORS: browser blocks requests from different origins
#  Example: frontend at localhost:3000 calling API at localhost:8000
#
#  allow_origins = which websites can call your API
#  allow_methods = which HTTP methods (GET, POST, etc.)
#  allow_headers = which headers the frontend can send
#  allow_credentials = allow cookies/auth headers
# ════════════════════════════════════════════════════

# OPTION A: Allow specific origins (RECOMMENDED for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server
        "http://localhost:5173",      # Vite dev server
        "https://myapp.example.com",  # production frontend
    ],
    allow_credentials=True,           # allow cookies/JWT
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],              # allow all headers
)

# OPTION B: Allow ALL origins (only for development/public APIs)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],            # any website can call this API
#     allow_credentials=False,        # must be False when origins=["*"]
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# OPTION C: Allow origins by pattern (regex)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origin_regex=r"https://.*\.example\.com",  # any subdomain
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

@app.get("/cors/test")
def cors_test():
    return {"message": "If CORS is set up, your frontend can call this"}
# From browser console on localhost:3000:
# fetch("http://localhost:8000/cors/test").then(r => r.json()).then(console.log)
# Without CORS middleware → browser blocks the request
# With CORS middleware → works fine


# ════════════════════════════════════════════════════
# 2. Built-in GZip middleware — compress responses
#
#  Compresses responses larger than minimum_size bytes
#  Browser sends "Accept-Encoding: gzip" → server compresses
#  Reduces response size by 60-90% for JSON/text
# ════════════════════════════════════════════════════

app.add_middleware(GZipMiddleware, minimum_size=500)

@app.get("/middleware/gzip-test")
def gzip_test():
    return {"data": [shipment_data[k] for k in shipment_data] * 50}
# curl -H "Accept-Encoding: gzip" http://localhost:8000/middleware/gzip-test
# Response is compressed automatically


# ════════════════════════════════════════════════════
# 3. Built-in TrustedHost middleware — block unknown hosts
#
#  Prevents Host header attacks
#  Only allows requests with specific Host header values
# ════════════════════════════════════════════════════

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "myapp.example.com", "*.example.com"],
)
# Requests with Host header not in list → 400 Bad Request


# ════════════════════════════════════════════════════
# 4. Custom middleware — add response time header
#
#  Middleware functions MUST be async def (FastAPI rule)
#  But the ENDPOINTS they protect can be plain def
#
#  request  = incoming request object
#  call_next = calls the next middleware or the endpoint
#  response = what the endpoint returned
# ════════════════════════════════════════════════════

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(round(process_time, 4))
    return response
# Every response now has X-Process-Time header showing how long it took
# curl -v http://localhost:8000/cors/test
# Look for: X-Process-Time: 0.0012


# ════════════════════════════════════════════════════
# 5. Custom middleware — request logging
#
#  Logs every request: method, URL, status code
# ════════════════════════════════════════════════════

@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"→ {request.method} {request.url.path}")
    response = await call_next(request)
    print(f"← {request.method} {request.url.path} → {response.status_code}")
    return response
# Every request prints in the server terminal:
# → GET /cors/test
# ← GET /cors/test → 200


# ════════════════════════════════════════════════════
# 6. Custom middleware — add custom headers to ALL responses
# ════════════════════════════════════════════════════

@app.middleware("http")
async def add_custom_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-App-Name"] = "Shipment-API"
    response.headers["X-App-Version"] = "1.0.0"
    return response
# curl -v http://localhost:8000/cors/test
# X-App-Name: Shipment-API
# X-App-Version: 1.0.0


# ════════════════════════════════════════════════════
# 7. Custom middleware — block specific paths
#
#  Deny access to certain routes without correct token
# ════════════════════════════════════════════════════

@app.middleware("http")
async def block_admin_routes(request: Request, call_next):
    if request.url.path.startswith("/admin"):
        auth_header = request.headers.get("Authorization", "")
        if auth_header != "Bearer admin-secret-token":
            return JSONResponse(
                status_code=403,
                content={"detail": "Admin access denied"},
            )
    return await call_next(request)

@app.get("/admin/dashboard")
def admin_dashboard():
    return {"message": "Welcome to admin dashboard"}
# curl http://localhost:8000/admin/dashboard
# → 403 "Admin access denied"
# curl -H "Authorization: Bearer admin-secret-token" http://localhost:8000/admin/dashboard
# → 200 "Welcome to admin dashboard"


# ════════════════════════════════════════════════════
# 8. Custom middleware — rate limiting (simple)
#
#  Track requests per IP, block if too many
# ════════════════════════════════════════════════════

request_counts: dict[str, list[float]] = {}
RATE_LIMIT = 10         # max requests
RATE_WINDOW = 60.0      # per 60 seconds

@app.middleware("http")
async def rate_limiter(request: Request, call_next):
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()

    if client_ip not in request_counts:
        request_counts[client_ip] = []

    # Remove requests older than the window
    request_counts[client_ip] = [
        t for t in request_counts[client_ip] if now - t < RATE_WINDOW
    ]

    if len(request_counts[client_ip]) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests. Try again later."},
        )

    request_counts[client_ip].append(now)
    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(
        RATE_LIMIT - len(request_counts[client_ip])
    )
    return response
# After 10 requests in 60 seconds:
# curl http://localhost:8000/cors/test  → 429 Too Many Requests


# ════════════════════════════════════════════════════
# 9. Custom middleware — exception handler
#
#  Catch ALL unhandled exceptions and return clean JSON
#  Without this: server returns ugly 500 HTML error
# ════════════════════════════════════════════════════

@app.middleware("http")
async def catch_exceptions(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error": str(e)},
        )


# ════════════════════════════════════════════════════
# 10. Middleware execution order
#
#  Middleware runs in REVERSE order of registration
#  Last added = runs FIRST (outermost layer)
#
#  If you add: A, B, C
#  Execution:  C → B → A → endpoint → A → B → C
# ════════════════════════════════════════════════════

@app.get("/middleware/order-test")
def middleware_order_test():
    return {"message": "Check server logs to see middleware execution order"}
# curl http://localhost:8000/middleware/order-test


# ════════════════════════════════════════════════════
# 11. In-memory cache — simple dict cache
#
#  Store results in a dict, return cached version
#  if the same request comes again within TTL seconds
#
#  Fastest method, but lost on server restart
# ════════════════════════════════════════════════════

cache_store: dict[str, dict] = {}
CACHE_TTL = 30  # seconds

@app.get("/cache/simple/{id}")
def get_with_simple_cache(id: int):
    cache_key = f"shipment:{id}"
    now = time.time()

    # Check cache
    if cache_key in cache_store:
        cached = cache_store[cache_key]
        if now - cached["timestamp"] < CACHE_TTL:
            return {**cached["data"], "_cache": "HIT", "_age": round(now - cached["timestamp"], 1)}

    # Cache miss — fetch data
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    result = shipment_data[id]

    # Store in cache
    cache_store[cache_key] = {"data": result, "timestamp": now}
    return {**result, "_cache": "MISS"}
# curl http://localhost:8000/cache/simple/1   → MISS (first call)
# curl http://localhost:8000/cache/simple/1   → HIT  (from cache)
# Wait 30s, then:
# curl http://localhost:8000/cache/simple/1   → MISS (cache expired)


# ════════════════════════════════════════════════════
# 12. Cache with manual invalidation
#
#  Delete cache when data changes (POST/PUT/DELETE)
#  Prevents serving stale data after updates
# ════════════════════════════════════════════════════

@app.put("/cache/shipment/{id}")
def update_shipment_and_invalidate(id: int, status: str = "Updated"):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    shipment_data[id]["status"] = status

    # Invalidate cache for this shipment
    cache_key = f"shipment:{id}"
    if cache_key in cache_store:
        del cache_store[cache_key]

    return {"updated": shipment_data[id], "cache_invalidated": True}

@app.delete("/cache/clear")
def clear_all_cache():
    cache_store.clear()
    return {"message": "All cache cleared"}
# curl -X PUT "http://localhost:8000/cache/shipment/1?status=Delivered"
# → cache for shipment:1 is deleted, next GET will be fresh
# curl -X DELETE http://localhost:8000/cache/clear
# → all cache entries removed


# ════════════════════════════════════════════════════
# 13. HTTP cache headers — browser/CDN caching
#
#  Cache-Control header tells browsers & CDNs to cache
#  ETag = fingerprint of the data — if unchanged, skip download
#
#  This is CLIENT-SIDE caching (browser stores it)
#  vs. examples 11-12 which are SERVER-SIDE caching
# ════════════════════════════════════════════════════

@app.get("/cache/headers/{id}")
def get_with_cache_headers(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")

    data = shipment_data[id]
    content = json.dumps(data, sort_keys=True)
    etag = hashlib.md5(content.encode()).hexdigest()

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Cache-Control": "public, max-age=60",  # browser caches for 60s
            "ETag": f'"{etag}"',                     # fingerprint of data
        },
    )
# curl -v http://localhost:8000/cache/headers/1
# Response headers:
#   Cache-Control: public, max-age=60
#   ETag: "a1b2c3d4..."
# Browser won't re-request for 60 seconds


# ════════════════════════════════════════════════════
# 14. Cache-Control variants — different caching strategies
# ════════════════════════════════════════════════════

@app.get("/cache/no-cache")
def no_cache_response():
    return Response(
        content=json.dumps({"data": "always fresh", "time": time.time()}),
        media_type="application/json",
        headers={"Cache-Control": "no-store"},
    )

@app.get("/cache/private")
def private_cache():
    return Response(
        content=json.dumps({"user_data": "only for this user"}),
        media_type="application/json",
        headers={"Cache-Control": "private, max-age=300"},
    )

@app.get("/cache/immutable")
def immutable_cache():
    return Response(
        content=json.dumps({"version": "1.0.0", "data": "never changes"}),
        media_type="application/json",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )
# no-store    → never cache (real-time data, auth tokens)
# private     → only browser caches, CDN/proxy does NOT (user-specific data)
# public      → browser AND CDN can cache (static assets, public data)
# immutable   → content will NEVER change at this URL (versioned assets)
# curl -v http://localhost:8000/cache/no-cache
# curl -v http://localhost:8000/cache/private
# curl -v http://localhost:8000/cache/immutable


# ════════════════════════════════════════════════════
# 15. Conditional caching — ETag + If-None-Match
#
#  Client sends ETag back → server checks if data changed
#  If unchanged → return 304 Not Modified (no body, saves bandwidth)
#  If changed → return 200 with new data + new ETag
# ════════════════════════════════════════════════════

@app.get("/cache/conditional/{id}")
def conditional_cache(id: int, request: Request):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")

    data = shipment_data[id]
    content = json.dumps(data, sort_keys=True)
    etag = hashlib.md5(content.encode()).hexdigest()

    # Check if client already has this version
    client_etag = request.headers.get("If-None-Match", "")
    if client_etag == f'"{etag}"':
        return Response(status_code=304)  # Not Modified — no body sent

    return Response(
        content=content,
        media_type="application/json",
        headers={"ETag": f'"{etag}"', "Cache-Control": "public, max-age=60"},
    )
# First call — returns full data + ETag:
# curl -v http://localhost:8000/cache/conditional/1
#
# Second call — send ETag back, get 304 (no body):
# curl -v -H 'If-None-Match: "<etag_from_first_call>"' http://localhost:8000/cache/conditional/1
