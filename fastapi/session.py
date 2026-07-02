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
