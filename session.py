# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Dependencies required (install via: uv sync)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# fastapi      — Web framework (provides FastAPI, Request, Response, Depends, HTTPException)
# uvicorn      — ASGI server to run the FastAPI app
# httpx        — Async HTTP client (used in lifespan for shared connection pooling)
# PyJWT        — JWT token encoding/decoding (approach 3: token-based sessions)
# redis        — Async Redis client (approach 2: server-side sessions)
# itsdangerous — Cookie signing library (required by starlette SessionMiddleware)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

import uuid
import json
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

import httpx
import jwt
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Request, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.sessions import SessionMiddleware


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Lifespan — startup / shutdown
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# @asynccontextmanager explained:
#
# A decorator from Python's contextlib that turns an async generator function
# into an async context manager (something you can use with "async with").
#
# How it works:
#   1. Everything BEFORE "yield" runs when the context is entered (startup)
#   2. "yield" pauses the function — control is handed to the caller
#   3. Everything AFTER "yield" runs when the context exits (shutdown)
#
# Without @asynccontextmanager you would need to write a full class with
# __aenter__ and __aexit__ methods. This decorator is the shortcut.
#
# Example of what it replaces:
#
#   class Lifespan:
#       async def __aenter__(self):
#           # startup code here
#           return self
#       async def __aexit__(self, exc_type, exc_val, exc_tb):
#           # shutdown code here
#           pass
#
# With the decorator, you just write a single function with "yield" in the
# middle — Python handles the enter/exit lifecycle for you.
#
# FastAPI expects its lifespan parameter to be an async context manager,
# which is exactly what @asynccontextmanager produces.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──
    print("Starting up...")
    app.state.http_client = httpx.AsyncClient(timeout=30)
    app.state.redis = redis.Redis(host="localhost", port=6379, decode_responses=True)
    app.state.shipments = {
        1: {"id": 1, "content": "Wooden Table", "weight": 10, "status": "In Transit"},
        2: {"id": 2, "content": "Steel Chair", "weight": 20, "status": "Delivered"},
        3: {"id": 3, "content": "Glass Vase", "weight": 5, "status": "Pending"},
    }
    print(f"Loaded {len(app.state.shipments)} shipments")

    yield

    # ── SHUTDOWN ──
    print("Shutting down...")
    await app.state.http_client.aclose()
    await app.state.redis.aclose()
    print("All connections closed")


app = FastAPI(title="Shipment Tracker API", lifespan=lifespan)

# Cookie-based sessions need this middleware
app.add_middleware(SessionMiddleware, secret_key="super-secret-key-change-in-prod")

JWT_SECRET = "jwt-secret-key-change-in-prod"
security = HTTPBearer()
SESSION_TTL = 3600  # 1 hour


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Shipment routes (using lifespan shared state)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/shipments")
async def list_shipments():
    return list(app.state.shipments.values())


@app.get("/shipments/{shipment_id}")
async def get_shipment(shipment_id: int):
    shipment = app.state.shipments.get(shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    return shipment


@app.get("/external")
async def call_external():
    resp = await app.state.http_client.get(
        "https://jsonplaceholder.typicode.com/todos/1"
    )
    return resp.json()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Approach 1: Cookie-based sessions (starlette SessionMiddleware)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/cookie/login")
async def cookie_login(request: Request):
    request.session["user"] = "john@reuters.com"
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
    request.session.clear()
    return {"message": "Logged out"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Approach 2: Server-side sessions with Redis
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/redis/login")
async def redis_login(request: Request, response: Response):
    session_id = str(uuid.uuid4())
    session_data = {"user": "john@reuters.com", "role": "editor"}
    await request.app.state.redis.setex(
        f"session:{session_id}",
        SESSION_TTL,
        json.dumps(session_data),
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Approach 3: Token-based sessions with JWT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/jwt/login")
async def jwt_login():
    payload = {
        "user": "john@reuters.com",
        "role": "editor",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return {"message": "Logged in via JWT", "token": token}


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/jwt/profile")
async def jwt_profile(user: dict = Depends(get_current_user)):
    return {"user": user["user"], "role": user["role"]}
