# ══════════════════════════════════════════════════════════════════
# FastAPI Sessions & Lifespan — Cookie, Redis, JWT
# ══════════════════════════════════════════════════════════════════
# Deps: fastapi, uvicorn, httpx, PyJWT, redis, itsdangerous
#
# Run: uvicorn session:app --reload

import uuid, json
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
import httpx, jwt, redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware

# ╔══════════════════════════════════════════════════╗
# ║               BEGINNER                           ║
# ╚══════════════════════════════════════════════════╝

# ── 1. Lifespan — Startup & Shutdown ───────────────
# @asynccontextmanager turns an async generator into a context manager:
#   before yield = startup, after yield = shutdown.
# Replaces the old @app.on_event("startup") / @app.on_event("shutdown").
# Equivalent to writing __aenter__ / __aexit__ on a class.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: create shared resources once
    print("Starting up...")
    app.state.http_client = httpx.AsyncClient(timeout=30)  # connection-pooled client
    app.state.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
    app.state.shipments = {
        1: {"id": 1, "content": "Wooden Table", "weight": 10, "status": "In Transit"},
        2: {"id": 2, "content": "Steel Chair", "weight": 20, "status": "Delivered"},
        3: {"id": 3, "content": "Glass Vase", "weight": 5, "status": "Pending"},
    }
    print(f"Loaded {len(app.state.shipments)} shipments")
    yield  # server is live, handling requests
    # SHUTDOWN: clean up resources
    print("Shutting down...")
    await app.state.http_client.aclose()
    await app.state.redis.aclose()
    print("All connections closed")

app = FastAPI(title="Shipment Tracker API", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-change-in-prod")
JWT_SECRET = "jwt-secret-key-change-in-prod"
security = HTTPBearer()
SESSION_TTL = 3600  # 1 hour

# ── 2. Shared State via app.state ──────────────────
# app.state persists across requests for the app's lifetime.
# Set in lifespan, accessed in routes via app.state.X or request.app.state.X.
@app.get("/shipments")
async def list_shipments():
    return list(app.state.shipments.values())  # reads from lifespan-loaded data

@app.get("/shipments/{shipment_id}")
async def get_shipment(shipment_id: int):
    shipment = app.state.shipments.get(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment

@app.get("/external")
async def call_external():
    resp = await app.state.http_client.get("https://jsonplaceholder.typicode.com/todos/1")
    return resp.json()  # uses shared httpx client from lifespan

# ╔══════════════════════════════════════════════════╗
# ║             INTERMEDIATE                         ║
# ╚══════════════════════════════════════════════════╝

# ── 3. Cookie-Based Sessions (SessionMiddleware) ──
# Starlette stores session data in a signed cookie (client-side).
# Needs: app.add_middleware(SessionMiddleware, secret_key=...)
# Data lives in request.session dict. Auto-set on response.
@app.get("/cookie/login")
async def cookie_login(request: Request):
    request.session["user"] = "john@reuters.com"  # stored in signed cookie
    request.session["role"] = "editor"
    return {"message": "Logged in via cookie session"}

@app.get("/cookie/profile")
async def cookie_profile(request: Request):
    user = request.session.get("user")
    if not user:
        return {"message": "Not logged in"}
    return {"user": user, "role": request.session.get("role")}

@app.get("/cookie/logout")
async def cookie_logout(request: Request):
    request.session.clear()  # removes all session data
    return {"message": "Logged out"}

# ── 4. Redis Server-Side Sessions ─────────────────
# Session ID in cookie, actual data in Redis. Server-controlled expiry.
# Uses app.state.redis from lifespan.
@app.get("/redis/login")
async def redis_login(request: Request, response: Response):
    session_id = str(uuid.uuid4())
    session_data = {"user": "john@reuters.com", "role": "editor"}
    await request.app.state.redis.setex(  # SET with EXpiry
        f"session:{session_id}", SESSION_TTL, json.dumps(session_data),
    )
    response.set_cookie(key="session_id", value=session_id, httponly=True)
    return {"message": "Logged in via Redis session", "session_id": session_id}

@app.get("/redis/profile")
async def redis_profile(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return {"message": "Not logged in"}
    data = await request.app.state.redis.get(f"session:{session_id}")
    if not data:
        return {"message": "Session expired"}
    return json.loads(data)

@app.get("/redis/logout")
async def redis_logout(request: Request, response: Response):
    session_id = request.cookies.get("session_id")
    if session_id:
        await request.app.state.redis.delete(f"session:{session_id}")
    response.delete_cookie("session_id")
    return {"message": "Logged out"}

# ╔══════════════════════════════════════════════════╗
# ║               ADVANCED                           ║
# ╚══════════════════════════════════════════════════╝

# ── 5. JWT Token-Based Sessions ────────────────────
# Stateless: token carries all session data, signed with secret.
# No server storage needed. Client sends token in Authorization header.
@app.post("/jwt/login")
async def jwt_login():
    payload = {
        "user": "john@reuters.com", "role": "editor",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"message": "Logged in via JWT", "token": token}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        return jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/jwt/profile")
async def jwt_profile(user: dict = Depends(get_current_user)):
    return {"user": user["user"], "role": user["role"]}

# ── 6. Comparison: Cookie vs Redis vs JWT ──────────
#
# ┌─────────────┬──────────────────┬──────────────────┬──────────────────┐
# | Aspect       | Cookie           | Redis            | JWT              |
# ├─────────────┼──────────────────┼──────────────────┼──────────────────┤
# | Storage      | Client (cookie)  | Server (Redis)   | Client (token)   |
# | Size limit   | ~4KB per cookie  | Unlimited        | ~8KB practical   |
# | Scalability  | Stateless        | Needs shared DB  | Stateless        |
# | Revocation   | Clear cookie     | Delete key       | Can't revoke*    |
# | Security     | Signed, not enc  | Server-only data | Signed, not enc  |
# | Server load  | None             | Redis lookup/req | None (decode)    |
# | Best for     | Simple apps      | Production apps  | APIs / SPAs      |
# └─────────────┴──────────────────┴──────────────────┴──────────────────┘
# * JWT revocation requires a blocklist (adds server state)
#
# Pick cookie for prototypes, Redis for production web apps,
# JWT for stateless APIs and microservices.

# ── CHEAT SHEET ────────────────────────────────────
# LIFESPAN
#   @asynccontextmanager + yield       startup/shutdown lifecycle
#   app.state.X = resource             share across requests
#   FastAPI(lifespan=lifespan)          attach to app
#
# COOKIE SESSION
#   SessionMiddleware(secret_key=...)   enable cookie sessions
#   request.session["key"] = val        write session
#   request.session.get("key")          read session
#   request.session.clear()             destroy session
#
# REDIS SESSION
#   redis.setex(key, ttl, data)         store with expiry
#   redis.get(key)                      retrieve
#   redis.delete(key)                   remove
#   response.set_cookie(httponly=True)   secure session cookie
#
# JWT SESSION
#   jwt.encode(payload, secret, alg)    create token
#   jwt.decode(token, secret, algs)     verify + decode
#   Depends(HTTPBearer())               extract from header
#   "exp" claim                         auto-expiry
#
# ══════════════════════════════════════════════════════════════════
#  SESSIONS & AUTH DECLARATIONS — DETAILED REFERENCE
# ══════════════════════════════════════════════════════════════════
#
# ── Lifespan — App startup/shutdown lifecycle ────────────────────
#   @asynccontextmanager
#   async def lifespan(app: FastAPI):
#       app.state.db = connect()       → before yield = STARTUP (create resources)
#       yield                          → server is live, handling requests
#       app.state.db.close()           → after yield = SHUTDOWN (cleanup)
#   FastAPI(lifespan=lifespan)         → attach to app
#   Replaces old @app.on_event("startup") / @app.on_event("shutdown")
#
#   BEGINNER EXAMPLE — Lifespan:
#
#     @asynccontextmanager
#     async def lifespan(app: FastAPI):
#         # STARTUP — runs once before first request
#         app.state.http_client = httpx.AsyncClient(timeout=30)
#         app.state.db = await connect_db()
#         print("Ready!")
#         yield                              # ← server is live here
#         # SHUTDOWN — runs when server stops (Ctrl+C)
#         await app.state.http_client.aclose()
#         await app.state.db.close()
#
#     app = FastAPI(lifespan=lifespan)       # ← attach to app
#
#     # Flow:
#     #   uvicorn session:app --reload
#     #     │
#     #     ▼
#     #   STARTUP: create http_client, connect DB
#     #     │
#     #     ▼
#     #   yield → server handles requests (uses app.state.http_client, app.state.db)
#     #     │
#     #     ▼  (Ctrl+C or server stops)
#     #   SHUTDOWN: close http_client, close DB
#
# ── app.state — Share resources across requests ──────────────────
#   app.state.http_client = httpx.AsyncClient()   → set in lifespan startup
#   Access in routes: app.state.X or request.app.state.X
#   Persists for app's entire lifetime. Use for: DB pools, HTTP clients, caches.
#
#   BEGINNER EXAMPLE — app.state:
#
#     # Set in lifespan startup:
#     app.state.shipments = {1: {"id": 1, "content": "Table"}}
#
#     # Access in any route:
#     @app.get("/shipments")
#     async def list_shipments():
#         return list(app.state.shipments.values())
#
#     # How to call:
#     #   curl "http://localhost:8000/shipments"
#     #     → [{"id": 1, "content": "Table"}]
#     #
#     #   app.state is shared across ALL requests for the app's lifetime
#     #   Set once in startup → use everywhere → cleanup in shutdown
#
# ── SessionMiddleware — Cookie-based sessions ────────────────────
#   app.add_middleware(SessionMiddleware, secret_key="...")
#   request.session["user"] = "john"   → WRITE — stored in signed cookie (client-side)
#   request.session.get("user")        → READ — auto-parsed from cookie
#   request.session.clear()            → DESTROY — removes all session data
#   Data limit: ~4KB (cookie size limit). Signed but NOT encrypted.
#
#   BEGINNER EXAMPLE — Cookie sessions:
#
#     app.add_middleware(SessionMiddleware, secret_key="my-secret")
#
#     @app.get("/cookie/login")
#     async def login(request: Request):
#         request.session["user"] = "john@reuters.com"
#         return {"message": "Logged in"}
#
#     @app.get("/cookie/profile")
#     async def profile(request: Request):
#         user = request.session.get("user")
#         return {"user": user}   # None if not logged in
#
#     # How to call:
#     #   Step 1 — Login (sets cookie):
#     #   curl -c cookies.txt "http://localhost:8000/cookie/login"
#     #     → response sets Set-Cookie header with signed session data
#     #     → cookies.txt stores: session=eyJhb...  (signed, base64-encoded)
#     #
#     #   Step 2 — Access profile (sends cookie back):
#     #   curl -b cookies.txt "http://localhost:8000/cookie/profile"
#     #     → browser/curl sends cookie → FastAPI decodes → request.session populated
#     #     → {"user": "john@reuters.com"}
#     #
#     #   Without cookie:
#     #   curl "http://localhost:8000/cookie/profile"
#     #     → {"user": null}   (no session cookie = empty session)
#     #
#     #   -c cookies.txt = save cookies to file
#     #   -b cookies.txt = send cookies from file
#
# ── Redis sessions — Server-side storage ─────────────────────────
#   Session ID in cookie, actual data in Redis (server-controlled).
#   redis.setex(key, ttl, data)        → store with expiry (auto-delete after TTL)
#   redis.get(key)                     → retrieve (returns None if expired)
#   redis.delete(key)                  → explicit removal (logout)
#   response.set_cookie(httponly=True)  → httponly prevents JS access (XSS protection)
#
#   BEGINNER EXAMPLE — Redis sessions:
#
#     @app.get("/redis/login")
#     async def login(request: Request, response: Response):
#         session_id = str(uuid.uuid4())        # generate unique ID
#         data = {"user": "john@reuters.com"}
#         await redis.setex(f"session:{session_id}", 3600, json.dumps(data))
#         response.set_cookie(key="session_id", value=session_id, httponly=True)
#         return {"message": "Logged in"}
#
#     @app.get("/redis/profile")
#     async def profile(request: Request):
#         session_id = request.cookies.get("session_id")
#         data = await redis.get(f"session:{session_id}")
#         return json.loads(data) if data else {"message": "Not logged in"}
#
#     # How to call:
#     #   Step 1 — Login:
#     #   curl -c cookies.txt "http://localhost:8000/redis/login"
#     #     → generates session_id (e.g., "a1b2c3d4-...")
#     #     → stores {"user": "john"} in Redis with key "session:a1b2c3d4-..."
#     #     → sets cookie: session_id=a1b2c3d4-... (httponly — JS can't read it)
#     #
#     #   Step 2 — Profile:
#     #   curl -b cookies.txt "http://localhost:8000/redis/profile"
#     #     Cookie: session_id=a1b2c3d4-...
#     #                        │
#     #                        ▼
#     #     Redis lookup: GET "session:a1b2c3d4-..."
#     #                        │
#     #                        ▼
#     #     → {"user": "john@reuters.com"}
#     #
#     #   vs Cookie session:
#     #     Cookie: data IN the cookie (client-side, ~4KB limit)
#     #     Redis:  only session_id in cookie, data in Redis (unlimited, server-controlled)
#
# ── JWT — Stateless token-based auth ─────────────────────────────
#   jwt.encode(payload, secret, algorithm="HS256")  → create token (includes "exp" for expiry)
#   jwt.decode(token, secret, algorithms=["HS256"]) → verify signature + decode payload
#   Raises: jwt.ExpiredSignatureError (token too old), jwt.InvalidTokenError (tampered/invalid)
#   Stateless: no server storage needed. Client sends in Authorization: Bearer <token> header.
#
#   BEGINNER EXAMPLE — JWT auth:
#
#     @app.post("/jwt/login")
#     async def login():
#         payload = {"user": "john", "role": "editor",
#                    "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
#         token = jwt.encode(payload, "secret", algorithm="HS256")
#         return {"token": token}
#
#     @app.get("/jwt/profile")
#     async def profile(user: dict = Depends(get_current_user)):
#         return {"user": user["user"]}
#
#     # How to call:
#     #   Step 1 — Login (get token):
#     #   curl -X POST "http://localhost:8000/jwt/login"
#     #     → {"token": "eyJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiam9obi..."}
#     #
#     #   Step 2 — Access protected route (send token):
#     #   curl "http://localhost:8000/jwt/profile" \
#     #        -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9..."
#     #
#     #   Header: Authorization: Bearer eyJhbGci...
#     #                                 │
#     #                                 ▼
#     #   Depends(get_current_user):
#     #     HTTPBearer() extracts token from header
#     #       → jwt.decode(token, secret) → {"user": "john", "role": "editor"}
#     #                                       │
#     #                                       ▼
#     #     user → {"user": "john", "role": "editor"}
#     #
#     #   Bad token:  curl ... -H "Authorization: Bearer invalid"
#     #     → 401! jwt.InvalidTokenError
#     #   Expired:    → 401! jwt.ExpiredSignatureError
#     #   No header:  → 403! HTTPBearer finds no Authorization header
#
# ── Depends() — Dependency injection for auth ────────────────────
#   security = HTTPBearer()
#   async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
#       → HTTPBearer() extracts token from "Authorization: Bearer <token>" header
#       → credentials.credentials = the raw token string
#       → Depends(security) runs HTTPBearer BEFORE your function
#   @app.get("/protected")
#   async def route(user: dict = Depends(get_current_user)):
#       → Depends(get_current_user) runs auth check BEFORE route
#       → If it raises HTTPException, route is skipped (401/403 returned)
#       → Chaining: route depends on get_current_user, which depends on HTTPBearer()
#
#   BEGINNER EXAMPLE — Depends() chain for auth:
#
#     security = HTTPBearer()
#
#     # Dependency 1: extract token from header
#     # Dependency 2: decode and verify token
#     async def get_current_user(cred: HTTPAuthorizationCredentials = Depends(security)):
#         return jwt.decode(cred.credentials, "secret", algorithms=["HS256"])
#
#     @app.get("/profile")
#     async def profile(user: dict = Depends(get_current_user)):
#         return user
#
#     # How the chain works:
#     #   curl "http://localhost:8000/profile" -H "Authorization: Bearer <token>"
#     #
#     #   Request arrives
#     #     │
#     #     ▼
#     #   Depends(get_current_user) runs FIRST
#     #     │
#     #     ├── Depends(security) runs FIRST (inside get_current_user)
#     #     │     → HTTPBearer() extracts "Bearer <token>" from header
#     #     │     → cred.credentials = "<token>" (raw token string)
#     #     │
#     #     ├── jwt.decode(token) → {"user": "john", "role": "editor"}
#     #     │
#     #     ▼
#     #   profile() runs with user = {"user": "john", "role": "editor"}
#     #
#     #   If ANY dependency fails → HTTPException → route NEVER runs
#
# ── Request & Response objects ───────────────────────────────────
#   request: Request                   → access to headers, cookies, session, URL, client IP
#   request.cookies.get("session_id")  → read a specific cookie
#   request.headers.get("Authorization") → read a header
#   response: Response                 → set cookies, headers on outgoing response
#   response.set_cookie(key, value, httponly=True, max_age=3600)
#   response.delete_cookie("session_id") → remove a cookie
#
#   BEGINNER EXAMPLE — Request & Response:
#
#     @app.get("/demo")
#     async def demo(request: Request, response: Response):
#         # READ from request:
#         session = request.cookies.get("session_id")     # read cookie
#         auth = request.headers.get("Authorization")     # read header
#         ip = request.client.host                        # client IP
#
#         # WRITE to response:
#         response.set_cookie("visited", "true", max_age=3600)   # set cookie
#         response.headers["X-Custom"] = "hello"                 # set header
#         return {"session": session, "ip": ip}
#
#     # How to call:
#     #   curl -v "http://localhost:8000/demo" \
#     #        -b "session_id=abc" \
#     #        -H "Authorization: Bearer tok123"
#     #
#     #   Request (what server reads):
#     #     Cookie: session_id=abc          → request.cookies.get("session_id") → "abc"
#     #     Authorization: Bearer tok123    → request.headers.get("Authorization")
#     #     Client IP: 127.0.0.1           → request.client.host
#     #
#     #   Response (what client receives):
#     #     Set-Cookie: visited=true; Max-Age=3600  ← response.set_cookie()
#     #     X-Custom: hello                         ← response.headers[]
#     #     Body: {"session": "abc", "ip": "127.0.0.1"}
#
# ══════════════════════════════════════════════════════════════════
