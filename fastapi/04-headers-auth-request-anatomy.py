# ══════════════════════════════════════════════════════════════════
# HTTP Headers, Auth & Request Anatomy — Condensed Reference
# ══════════════════════════════════════════════════════════════════
# Run:  uv run uvicorn headers-auth-request-anatomy:app --reload
# Docs: http://localhost:8000/docs
# ══════════════════════════════════════════════════════════════════
# This file covers the TERMINOLOGY and CONCEPTS behind what you
# send when making an HTTP request — headers, auth schemes,
# API keys, tokens, custom headers, content negotiation, etc.
# ══════════════════════════════════════════════════════════════════
from typing import Annotated
from fastapi import (
    FastAPI, Header, Cookie, Depends, HTTPException, Request, Response, Query, status,
)
from fastapi.security import (
    HTTPBasic, HTTPBasicCredentials, HTTPBearer, HTTPAuthorizationCredentials,
    APIKeyHeader, APIKeyQuery, APIKeyCookie, OAuth2PasswordBearer, OAuth2PasswordRequestForm,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="HTTP Headers, Auth & Request Anatomy")


# ╔══════════════════════════════════════════════════════════════════╗
# ║  WHAT IS AN HTTP REQUEST? — THE FULL ANATOMY                    ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                  ║
# ║  When you call an API (curl, fetch, axios, httpx), you send:     ║
# ║                                                                  ║
# ║  ┌──────────────────────────────────────────────────────────┐    ║
# ║  │  REQUEST LINE                                            │    ║
# ║  │  POST /api/v1/orders?page=2 HTTP/1.1                    │    ║
# ║  │  ───── ─────────────────── ────────                      │    ║
# ║  │  method   URL path+query   protocol                      │    ║
# ║  ├──────────────────────────────────────────────────────────┤    ║
# ║  │  HEADERS (key: value metadata — NOT the data itself)     │    ║
# ║  │  Host: api.example.com                                   │    ║
# ║  │  Authorization: Bearer eyJhbGci...                       │    ║
# ║  │  Content-Type: application/json                          │    ║
# ║  │  Accept: application/json                                │    ║
# ║  │  X-Request-ID: req-abc-123                               │    ║
# ║  │  User-Agent: MyApp/1.0                                   │    ║
# ║  ├──────────────────────────────────────────────────────────┤    ║
# ║  │  BODY (the actual data — only for POST/PUT/PATCH)        │    ║
# ║  │  {"product": "Laptop", "quantity": 2}                    │    ║
# ║  └──────────────────────────────────────────────────────────┘    ║
# ║                                                                  ║
# ║  HEADERS vs BODY vs QUERY PARAMS — When to use which:           ║
# ║  ┌──────────────┬──────────────────────────────────────────┐    ║
# ║  │ Query params │ Filtering/pagination: ?page=2&sort=name  │    ║
# ║  │ Headers      │ Metadata: auth, content type, tracing    │    ║
# ║  │ Body         │ Actual data: the resource you're sending │    ║
# ║  └──────────────┴──────────────────────────────────────────┘    ║
# ╚══════════════════════════════════════════════════════════════════╝


# ╔══════════════════════════════════════════════════════════════════╗
# ║                        BEGINNER                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

# ── 1. WHAT ARE HTTP HEADERS? ────────────────────────────────────
# Headers = key-value pairs sent WITH every request and response.
# They carry METADATA (info about the request), not the data itself.
# Think of them as the "envelope" — the body is the "letter inside".
#
# REQUEST headers  = client tells server about itself and what it wants
# RESPONSE headers = server tells client about the response
#
# Headers are CASE-INSENSITIVE: "Content-Type" = "content-type" = "CONTENT-TYPE"

@app.get("/headers/inspect")
async def inspect_all_headers(request: Request):
    return {
        "all_headers": dict(request.headers),
        "explanation": {
            "host": "Domain the request was sent to",
            "user-agent": "What client/browser sent the request",
            "accept": "What response format the client wants",
            "accept-encoding": "What compression the client supports",
            "connection": "Keep TCP connection open or close after response",
        },
    }
# curl -v http://localhost:8000/headers/inspect
# You'll see headers like: Host, User-Agent, Accept — sent automatically!


# ── 2. STANDARD REQUEST HEADERS (sent by client) ────────────────
# These are headers the CLIENT sends TO the server.
# You don't invent these — they're defined by HTTP standards (RFCs).

@app.get("/headers/standard")
async def standard_headers(
    host: Annotated[str, Header()],                                 # always sent — the domain
    user_agent: Annotated[str, Header()],                           # browser/client identifier
    accept: Annotated[str, Header()] = "application/json",          # what format client wants back
    accept_language: Annotated[str | None, Header()] = None,        # preferred language
    accept_encoding: Annotated[str | None, Header()] = None,        # gzip, br, deflate
    connection: Annotated[str | None, Header()] = None,             # keep-alive or close
    cache_control: Annotated[str | None, Header()] = None,          # caching directives
    referer: Annotated[str | None, Header()] = None,                # page that linked here
):
    return {
        "host": {"value": host, "meaning": "Domain name of the server"},
        "user_agent": {"value": user_agent, "meaning": "Client software identifier"},
        "accept": {"value": accept, "meaning": "Response format client prefers"},
        "accept_language": {"value": accept_language, "meaning": "Preferred human language (en-US)"},
        "accept_encoding": {"value": accept_encoding, "meaning": "Compression methods supported"},
        "connection": {"value": connection, "meaning": "Keep TCP alive or close after response"},
        "cache_control": {"value": cache_control, "meaning": "Caching behavior instructions"},
        "referer": {"value": referer, "meaning": "URL of the page that linked to this one"},
    }
# curl http://localhost:8000/headers/standard -H "Accept-Language: en-US"


# ── 3. STANDARD RESPONSE HEADERS (sent by server) ───────────────
# These are headers the SERVER sends BACK to the client.

@app.get("/headers/response-demo")
async def response_headers_demo(response: Response):
    response.headers["Content-Type"] = "application/json"           # what format the body is
    response.headers["X-Process-Time"] = "0.042s"                   # custom: how long it took
    response.headers["Cache-Control"] = "public, max-age=60"        # caching instruction
    response.headers["ETag"] = '"abc123"'                           # content fingerprint
    response.headers["X-RateLimit-Remaining"] = "98"                # custom: API quota remaining
    return {
        "common_response_headers": {
            "Content-Type": "Format of the response body (application/json, text/html)",
            "Content-Length": "Size of response body in bytes",
            "Cache-Control": "How long client/CDN can cache this response",
            "ETag": "Content fingerprint — used for conditional caching (304)",
            "Set-Cookie": "Tells browser to store a cookie",
            "Location": "Where to redirect (used with 301/302 status codes)",
            "Access-Control-Allow-Origin": "CORS — which origins can access this",
        },
    }


# ── 4. CONTENT-TYPE — What Format Is the Data? ──────────────────
# Tells the receiver what format the body is in.
# REQUEST Content-Type  = "I'm sending you JSON/form-data/XML"
# RESPONSE Content-Type = "I'm giving you back JSON/HTML/plain text"
#
# Common Content-Type values:
#   application/json                     → JSON (most APIs)
#   application/x-www-form-urlencoded    → HTML form data (key=val&key2=val2)
#   multipart/form-data                  → file uploads
#   text/html                            → HTML page
#   text/plain                           → plain text
#   application/xml                      → XML
#   application/octet-stream             → raw binary

@app.post("/headers/content-type-demo")
async def content_type_demo(request: Request):
    content_type = request.headers.get("content-type", "not set")
    return {
        "you_sent_content_type": content_type,
        "note": "FastAPI auto-reads JSON body when Content-Type is application/json",
    }
# curl -X POST http://localhost:8000/headers/content-type-demo \
#      -H "Content-Type: application/json" -d '{"key": "value"}'
# curl -X POST http://localhost:8000/headers/content-type-demo \
#      -d "username=john"   # → Content-Type: application/x-www-form-urlencoded (auto)


# ── 5. ACCEPT — What Format Do You Want Back? ───────────────────
# Client tells server: "Give me the response in THIS format"
# Server checks Accept header and returns appropriate Content-Type.
# Most APIs ignore this and always return JSON — but it's the standard.

@app.get("/headers/accept-demo")
async def accept_demo(accept: Annotated[str, Header()] = "application/json"):
    if "text/html" in accept:
        return Response("<h1>HTML response</h1>", media_type="text/html")
    if "text/plain" in accept:
        return Response("Plain text response", media_type="text/plain")
    return {"format": "json", "message": "Default JSON response"}
# curl http://localhost:8000/headers/accept-demo -H "Accept: text/html"
# curl http://localhost:8000/headers/accept-demo -H "Accept: text/plain"
# curl http://localhost:8000/headers/accept-demo  # → JSON (default)


# ╔══════════════════════════════════════════════════════════════════╗
# ║                      INTERMEDIATE                                ║
# ╚══════════════════════════════════════════════════════════════════╝

# ── 6. AUTHORIZATION HEADER — The Standard Way to Authenticate ──
# Authorization: <scheme> <credentials>
#
# THE MOST IMPORTANT HEADER. Almost every API requires it.
# The value has two parts: the SCHEME (how) and the CREDENTIALS (what).
#
# Common Authorization schemes:
# ┌─────────────────┬────────────────────────────────────────────────┐
# │ Scheme          │ Example                                        │
# ├─────────────────┼────────────────────────────────────────────────┤
# │ Bearer          │ Authorization: Bearer eyJhbGciOi...            │
# │                 │ (JWT or OAuth2 token — most common in APIs)    │
# ├─────────────────┼────────────────────────────────────────────────┤
# │ Basic           │ Authorization: Basic dXNlcjpwYXNz             │
# │                 │ (base64 of "username:password" — simple auth)  │
# ├─────────────────┼────────────────────────────────────────────────┤
# │ ApiKey          │ Authorization: ApiKey sk-abc123...              │
# │                 │ (some APIs use this — not a standard scheme)    │
# ├─────────────────┼────────────────────────────────────────────────┤
# │ Digest          │ Authorization: Digest username="...",nonce=... │
# │                 │ (challenge-response — rare, more secure basic) │
# ├─────────────────┼────────────────────────────────────────────────┤
# │ AWS4-HMAC-SHA256│ Authorization: AWS4-HMAC-SHA256 Credential=...│
# │                 │ (AWS SigV4 — for AWS service calls)            │
# └─────────────────┴────────────────────────────────────────────────┘

# 6a. Bearer Token (JWT / OAuth2) — most common modern API auth
bearer_scheme = HTTPBearer()

@app.get("/auth/bearer")
async def bearer_auth(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    return {
        "scheme": credentials.scheme,          # "Bearer"
        "token": credentials.credentials,       # the actual token string
        "note": "In production, decode and validate the JWT here",
    }
# curl http://localhost:8000/auth/bearer -H "Authorization: Bearer my-jwt-token-here"
# Without the header → 403 Forbidden (HTTPBearer auto-rejects)

# 6b. Basic Auth — username:password base64-encoded
basic_scheme = HTTPBasic()

@app.get("/auth/basic")
async def basic_auth(credentials: HTTPBasicCredentials = Depends(basic_scheme)):
    if credentials.username != "admin" or credentials.password != "secret":
        raise HTTPException(status_code=401, detail="Invalid credentials",
                            headers={"WWW-Authenticate": "Basic"})
    return {"username": credentials.username, "authenticated": True}
# curl http://localhost:8000/auth/basic -u admin:secret
# curl automatically base64-encodes "admin:secret" → "YWRtaW46c2VjcmV0"
# and sends: Authorization: Basic YWRtaW46c2VjcmV0


# ── 7. API KEYS — Alternative to Authorization Header ───────────
# Not all APIs use the Authorization header. API keys can travel in:
#   1. Header:  X-API-Key: sk-abc123        (most common)
#   2. Query:   ?api_key=sk-abc123          (easy but visible in logs/URLs)
#   3. Cookie:  api_key=sk-abc123           (rare for APIs)
#
# API keys vs Tokens:
# ┌─────────────┬────────────────────────────────────────────────┐
# │ API Key     │ Static string, identifies the APPLICATION      │
# │             │ "Which app is calling me?" — billing, rate limit│
# ├─────────────┼────────────────────────────────────────────────┤
# │ Bearer Token│ Dynamic string (JWT), identifies the USER      │
# │ (JWT)       │ "Who is this person?" — permissions, identity  │
# ├─────────────┼────────────────────────────────────────────────┤
# │ Both        │ Some APIs need both: API key (which app) +     │
# │             │ Bearer token (which user)                      │
# └─────────────┴────────────────────────────────────────────────┘

# 7a. API Key in Header
api_key_header = APIKeyHeader(name="X-API-Key")

@app.get("/auth/api-key-header")
async def api_key_in_header(api_key: str = Depends(api_key_header)):
    if api_key != "sk-live-abc123":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return {"api_key_source": "header", "key": api_key[:10] + "..."}
# curl http://localhost:8000/auth/api-key-header -H "X-API-Key: sk-live-abc123"

# 7b. API Key in Query Parameter
api_key_query = APIKeyQuery(name="api_key")

@app.get("/auth/api-key-query")
async def api_key_in_query(api_key: str = Depends(api_key_query)):
    if api_key != "sk-live-abc123":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return {"api_key_source": "query", "key": api_key[:10] + "..."}
# curl "http://localhost:8000/auth/api-key-query?api_key=sk-live-abc123"
# WARNING: query params show up in browser history, server logs, referer headers!

# 7c. API Key in Cookie
api_key_cookie = APIKeyCookie(name="api_key")

@app.get("/auth/api-key-cookie")
async def api_key_in_cookie(api_key: str = Depends(api_key_cookie)):
    if api_key != "sk-live-abc123":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return {"api_key_source": "cookie", "key": api_key[:10] + "..."}
# curl http://localhost:8000/auth/api-key-cookie -b "api_key=sk-live-abc123"


# ── 8. X-<NAME> CUSTOM HEADERS — Application-Specific Metadata ──
# X- prefix = custom/non-standard header. Your app defines these.
# Common patterns in production APIs:
#
# ┌──────────────────────┬───────────────────────────────────────────┐
# │ Header               │ Purpose                                   │
# ├──────────────────────┼───────────────────────────────────────────┤
# │ X-Request-ID         │ Unique ID for tracing a request across    │
# │                      │ services (debugging distributed systems)  │
# ├──────────────────────┼───────────────────────────────────────────┤
# │ X-Correlation-ID     │ Same as X-Request-ID (different name)     │
# ├──────────────────────┼───────────────────────────────────────────┤
# │ X-Tenant-ID          │ Multi-tenant apps: which tenant/org       │
# ├──────────────────────┼───────────────────────────────────────────┤
# │ X-API-Key            │ API key (alternative to Authorization)    │
# ├──────────────────────┼───────────────────────────────────────────┤
# │ X-RateLimit-Limit    │ Max requests allowed in window            │
# │ X-RateLimit-Remaining│ Requests left in current window           │
# │ X-RateLimit-Reset    │ When the window resets (Unix timestamp)   │
# ├──────────────────────┼───────────────────────────────────────────┤
# │ X-Forwarded-For      │ Original client IP when behind a proxy    │
# │ X-Forwarded-Proto    │ Original protocol (http/https) behind LB  │
# │ X-Forwarded-Host     │ Original Host header behind proxy         │
# ├──────────────────────┼───────────────────────────────────────────┤
# │ X-Application-Name   │ Which app is calling (for logging)        │
# │ X-User-ID            │ User identifier (when not in JWT)         │
# │ X-Session-ID         │ Session tracking across requests          │
# └──────────────────────┴───────────────────────────────────────────┘
#
# NOTE: The X- prefix was officially deprecated in RFC 6648 (2012).
# New custom headers don't NEED the prefix, but most APIs still use it
# by convention. Both "X-Request-ID" and "Request-ID" are valid.

@app.get("/headers/custom")
async def custom_headers(
    x_request_id: Annotated[str | None, Header()] = None,
    x_tenant_id: Annotated[str | None, Header()] = None,
    x_correlation_id: Annotated[str | None, Header()] = None,
    x_application_name: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header()] = None,
):
    return {
        "received_custom_headers": {
            "X-Request-ID": x_request_id,
            "X-Tenant-ID": x_tenant_id,
            "X-Correlation-ID": x_correlation_id,
            "X-Application-Name": x_application_name,
            "X-User-ID": x_user_id,
        },
        "note": "FastAPI auto-converts header names: X-Request-ID -> x_request_id",
    }
# curl http://localhost:8000/headers/custom \
#      -H "X-Request-ID: req-abc-123" \
#      -H "X-Tenant-ID: tenant-42" \
#      -H "X-Application-Name: LEON"


# ── 9. REAL-WORLD MULTI-HEADER AUTH PATTERN ──────────────────────
# Many production APIs require MULTIPLE headers together.
# Example: Our Reuters AI Assistant backend expects:
#   Authorization: Bearer <jwt>       ← who is the user
#   X-Tenant-ID: leon-shubham         ← which tenant/organization
#   X-Application-Name: LEON          ← which frontend app
#   X-User-ID: user@reuters.com       ← user identifier
#   X-Request-ID: req-123             ← request tracing

async def verify_full_auth(
    authorization: Annotated[str, Header()],
    x_tenant_id: Annotated[str, Header()],
    x_application_name: Annotated[str | None, Header()] = None,
    x_user_id: Annotated[str | None, Header()] = None,
    x_request_id: Annotated[str | None, Header()] = None,
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = authorization.removeprefix("Bearer ")
    return {
        "token": token,
        "tenant": x_tenant_id,
        "app": x_application_name,
        "user": x_user_id,
        "request_id": x_request_id,
    }

@app.get("/auth/multi-header")
async def multi_header_auth(auth_context: dict = Depends(verify_full_auth)):
    return {"authenticated": True, "context": auth_context}
# curl http://localhost:8000/auth/multi-header \
#      -H "Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.test" \
#      -H "X-Tenant-ID: leon-shubham" \
#      -H "X-Application-Name: LEON" \
#      -H "X-User-ID: john@example.com" \
#      -H "X-Request-ID: req-abc-123"


# ╔══════════════════════════════════════════════════════════════════╗
# ║                        ADVANCED                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

# ── 10. OAuth2 PASSWORD FLOW (FastAPI built-in) ──────────────────
# OAuth2 = standard protocol for token-based auth. Many flows exist:
#   Password flow  = send username+password, get token back (simple)
#   Auth code flow = redirect to login page, get code, exchange for token (Google/GitHub login)
#   Client creds   = machine-to-machine auth (no user involved)
#
# FastAPI has built-in OAuth2 support that auto-generates a login form in /docs.

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

FAKE_USERS_DB = {
    "admin": {"username": "admin", "password": "secret", "role": "admin"},
    "reader": {"username": "reader", "password": "pass123", "role": "reader"},
}

@app.post("/auth/token")
async def login_for_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = FAKE_USERS_DB.get(form_data.username)
    if not user or user["password"] != form_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"access_token": f"fake-jwt-for-{form_data.username}", "token_type": "bearer"}
# curl -X POST http://localhost:8000/auth/token -d "username=admin&password=secret"
# → {"access_token": "fake-jwt-for-admin", "token_type": "bearer"}

@app.get("/auth/protected")
async def protected_route(token: str = Depends(oauth2_scheme)):
    return {"message": "You have access", "token_received": token}
# curl http://localhost:8000/auth/protected -H "Authorization: Bearer fake-jwt-for-admin"


# ── 11. CONTENT NEGOTIATION — Full Pattern ───────────────────────
# Client says what it wants (Accept), server responds accordingly.
# Professional APIs support multiple formats from the same endpoint.

@app.get("/data/{item_id}")
async def get_data_negotiated(item_id: int, request: Request):
    data = {"id": item_id, "name": "Widget", "price": 29.99}
    accept = request.headers.get("accept", "application/json")

    if "text/csv" in accept:
        csv = "id,name,price\n" + f"{data['id']},{data['name']},{data['price']}"
        return Response(content=csv, media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=item_{item_id}.csv"})

    if "text/plain" in accept:
        return Response(content=f"Item {item_id}: {data['name']} - ${data['price']}")

    return data  # default JSON
# curl http://localhost:8000/data/1                          → JSON
# curl http://localhost:8000/data/1 -H "Accept: text/csv"   → CSV download
# curl http://localhost:8000/data/1 -H "Accept: text/plain" → plain text


# ── 12. SECURITY HEADERS (Response) ─────────────────────────────
# Headers the server sends to protect the client (browser security).
# Usually set in middleware or reverse proxy (nginx), not per-route.

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"               # don't guess MIME type
    response.headers["X-Frame-Options"] = "DENY"                         # prevent iframe embedding
    response.headers["Strict-Transport-Security"] = "max-age=31536000"   # force HTTPS for 1 year
    response.headers["X-XSS-Protection"] = "1; mode=block"               # legacy XSS filter
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# ── 13. FORWARDING / PROXY HEADERS ──────────────────────────────
# When your API is behind a load balancer (ALB, nginx, Cloudflare),
# the client IP and protocol get replaced by the proxy's.
# Proxy sets X-Forwarded-* headers with the ORIGINAL values.

@app.get("/headers/proxy-info")
async def proxy_info(request: Request):
    return {
        "direct_client_ip": request.client.host if request.client else None,
        "x_forwarded_for": request.headers.get("x-forwarded-for"),
        "x_forwarded_proto": request.headers.get("x-forwarded-proto"),
        "x_forwarded_host": request.headers.get("x-forwarded-host"),
        "x_real_ip": request.headers.get("x-real-ip"),
        "explanation": {
            "X-Forwarded-For": "Original client IP (can be chain: client, proxy1, proxy2)",
            "X-Forwarded-Proto": "Original protocol (https even if proxy→app is http)",
            "X-Forwarded-Host": "Original Host header before proxy rewrote it",
            "X-Real-IP": "Nginx-specific: single original client IP",
        },
    }
# Behind ALB: client (1.2.3.4) → ALB (10.0.0.1) → your app
#   request.client.host = "10.0.0.1" (ALB's IP — NOT the user!)
#   X-Forwarded-For = "1.2.3.4" (the real user IP)


# ══════════════════════════════════════════════════════════════════
# CHEAT SHEET — HEADER CATEGORIES
# ══════════════════════════════════════════════════════════════════
# CATEGORY          │ HEADER                │ PURPOSE
# ──────────────────┼───────────────────────┼──────────────────────────────
# IDENTITY          │ Host                  │ Target server domain
#                   │ User-Agent            │ Client software identifier
#                   │ Referer               │ Page that linked here
# ──────────────────┼───────────────────────┼──────────────────────────────
# AUTH              │ Authorization         │ Bearer <token> or Basic <b64>
#                   │ X-API-Key             │ API key (custom header)
#                   │ Cookie                │ Session/auth cookie
#                   │ WWW-Authenticate      │ Server tells client how to auth
# ──────────────────┼───────────────────────┼──────────────────────────────
# CONTENT           │ Content-Type          │ Body format (application/json)
#                   │ Content-Length         │ Body size in bytes
#                   │ Accept                │ Desired response format
#                   │ Accept-Encoding       │ Compression support (gzip, br)
#                   │ Accept-Language       │ Preferred language (en-US)
#                   │ Content-Disposition   │ Download filename hint
# ──────────────────┼───────────────────────┼──────────────────────────────
# CACHING           │ Cache-Control         │ Caching rules (max-age, no-store)
#                   │ ETag                  │ Content fingerprint
#                   │ If-None-Match         │ Conditional request (use ETag)
#                   │ Last-Modified         │ When resource last changed
#                   │ If-Modified-Since     │ Conditional request (use date)
# ──────────────────┼───────────────────────┼──────────────────────────────
# SECURITY          │ Strict-Transport-Security │ Force HTTPS
#                   │ X-Content-Type-Options│ Prevent MIME sniffing
#                   │ X-Frame-Options       │ Prevent iframe embedding
#                   │ X-XSS-Protection      │ Legacy XSS filter
#                   │ Referrer-Policy       │ Control referer leakage
# ──────────────────┼───────────────────────┼──────────────────────────────
# CORS              │ Origin                │ Where the request came from
#                   │ Access-Control-Allow-Origin    │ Allowed origins
#                   │ Access-Control-Allow-Methods   │ Allowed HTTP methods
#                   │ Access-Control-Allow-Headers   │ Allowed request headers
# ──────────────────┼───────────────────────┼──────────────────────────────
# PROXY/LB          │ X-Forwarded-For       │ Original client IP
#                   │ X-Forwarded-Proto     │ Original protocol (http/https)
#                   │ X-Forwarded-Host      │ Original host header
#                   │ X-Real-IP             │ Nginx: single client IP
# ──────────────────┼───────────────────────┼──────────────────────────────
# CUSTOM (X-)       │ X-Request-ID          │ Request tracing/correlation
#                   │ X-Tenant-ID           │ Multi-tenant: which org
#                   │ X-Application-Name    │ Which app is calling
#                   │ X-User-ID             │ User identifier
#                   │ X-RateLimit-*         │ Rate limit info
# ──────────────────┼───────────────────────┼──────────────────────────────
# CONNECTION        │ Connection            │ keep-alive or close
#                   │ Transfer-Encoding     │ chunked (streaming)
#                   │ Upgrade               │ Protocol upgrade (WebSocket)
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
# AUTH COMPARISON — When to Use What
# ══════════════════════════════════════════════════════════════════
# METHOD            │ WHERE                 │ WHEN TO USE
# ──────────────────┼───────────────────────┼──────────────────────────
# Bearer Token (JWT)│ Authorization header  │ User auth, modern APIs
#                   │                       │ Contains user info inside token
# ──────────────────┼───────────────────────┼──────────────────────────
# Basic Auth        │ Authorization header  │ Simple server-to-server
#                   │                       │ Username:password base64
# ──────────────────┼───────────────────────┼──────────────────────────
# API Key (header)  │ X-API-Key header      │ App identification, billing
#                   │                       │ Static, doesn't expire
# ──────────────────┼───────────────────────┼──────────────────────────
# API Key (query)   │ ?api_key=xxx          │ Quick testing, webhooks
#                   │                       │ AVOID in prod (leaks in logs)
# ──────────────────┼───────────────────────┼──────────────────────────
# Cookie            │ Cookie header         │ Browser sessions, SSR apps
#                   │                       │ Auto-sent by browser
# ──────────────────┼───────────────────────┼──────────────────────────
# OAuth2 Code Flow  │ Authorization header  │ "Login with Google/GitHub"
#                   │                       │ User redirected → code → token
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
#  HEADERS, AUTH & REQUEST ANATOMY — DETAILED REFERENCE
# ══════════════════════════════════════════════════════════════════
#
# ── What is an HTTP Header? ──────────────────────────────────────
#   A key-value pair sent alongside every HTTP request and response.
#   Headers are METADATA — they describe the request, not the data.
#   Case-insensitive: Content-Type = content-type = CONTENT-TYPE
#   Format: "Header-Name: header-value" (colon + space separator)
#
#   BEGINNER EXAMPLE — What headers look like in raw HTTP:
#
#     # When you run: curl -v http://localhost:8000/items
#     # You see the FULL HTTP request:
#     #
#     #   > GET /items HTTP/1.1              ← request line (method + path)
#     #   > Host: localhost:8000             ← HEADER: which server
#     #   > User-Agent: curl/7.88.1         ← HEADER: what client
#     #   > Accept: */*                     ← HEADER: any format is fine
#     #   >                                 ← empty line = end of headers
#     #                                        (body would go here for POST)
#     #
#     #   < HTTP/1.1 200 OK                 ← response status
#     #   < content-type: application/json  ← RESPONSE HEADER: it's JSON
#     #   < content-length: 42              ← RESPONSE HEADER: 42 bytes
#     #   <                                 ← empty line = end of headers
#     #   < [{"id":1,"name":"Laptop"}]      ← RESPONSE BODY
#     #
#     #   > means REQUEST (sent by you)
#     #   < means RESPONSE (sent by server)
#
# ── Authorization header — Bearer token ──────────────────────────
#   Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
#   "Bearer" = scheme name (tells server how to interpret the token)
#   The token after "Bearer " is typically a JWT (JSON Web Token).
#   JWT contains encoded user info: {user_id, role, exp} signed by server.
#   Server VALIDATES the JWT signature — if tampered, auth fails.
#
#   BEGINNER EXAMPLE — Bearer token flow:
#
#     # Step 1: Login — POST username/password, get token back
#     #   curl -X POST http://localhost:8000/auth/token \
#     #        -d "username=admin&password=secret"
#     #     → {"access_token": "eyJhbG...", "token_type": "bearer"}
#     #
#     # Step 2: Use token — include in every subsequent request
#     #   curl http://localhost:8000/auth/protected \
#     #        -H "Authorization: Bearer eyJhbG..."
#     #     → {"message": "You have access"}
#     #
#     # What happens inside the server:
#     #   1. Extract token from "Authorization: Bearer <token>"
#     #   2. Decode JWT → {"user_id": 42, "role": "admin", "exp": 1700000000}
#     #   3. Verify signature (was it signed by our server's secret key?)
#     #   4. Check expiry (is exp > now?)
#     #   5. If valid → allow request; if invalid → 401 Unauthorized
#     #
#     # Why "Bearer"?
#     #   "Bearer" means "whoever BEARS (carries) this token gets access"
#     #   It's like a concert ticket — anyone holding it can enter
#     #   That's why tokens must be kept secret and sent over HTTPS only
#
# ── Authorization header — Basic auth ────────────────────────────
#   Authorization: Basic dXNlcjpwYXNz
#   "Basic" = scheme name
#   "dXNlcjpwYXNz" = base64("user:pass")
#   base64 is NOT encryption — anyone can decode it!
#   Only safe over HTTPS.
#
#   BEGINNER EXAMPLE — Basic auth:
#
#     # curl -u admin:secret http://localhost:8000/auth/basic
#     #
#     # What curl does behind the scenes:
#     #   1. Takes "admin:secret"
#     #   2. base64 encodes it → "YWRtaW46c2VjcmV0"
#     #   3. Sends: Authorization: Basic YWRtaW46c2VjcmV0
#     #
#     # Server decodes:
#     #   base64("YWRtaW46c2VjcmV0") → "admin:secret"
#     #   Split on ":" → username="admin", password="secret"
#     #   Check against database → valid → 200
#     #
#     # DANGER: base64 is reversible — NOT secure without HTTPS
#     #   echo "YWRtaW46c2VjcmV0" | base64 -d   → "admin:secret"
#
# ── API Keys — Header vs Query vs Cookie ─────────────────────────
#   HEADER:  curl -H "X-API-Key: sk-abc123" http://api.example.com/data
#   QUERY:   curl "http://api.example.com/data?api_key=sk-abc123"
#   COOKIE:  curl -b "api_key=sk-abc123" http://api.example.com/data
#
#   BEGINNER EXAMPLE — API key flow:
#
#     # API keys are like a building pass — identifies WHICH APP, not which user.
#     #
#     # Header (RECOMMENDED):
#     #   curl http://localhost:8000/data -H "X-API-Key: sk-live-abc123"
#     #   Pros: doesn't show in URL, not in browser history
#     #   Cons: can't send from <a href> or <img src> tags
#     #
#     # Query param (easy but risky):
#     #   curl "http://localhost:8000/data?api_key=sk-live-abc123"
#     #   Pros: works everywhere (even in <img src="...?api_key=xxx">)
#     #   Cons: shows in server logs, browser history, Referer header!
#     #         If you share the URL, you share your key
#     #
#     # Real-world examples:
#     #   OpenAI:   Authorization: Bearer sk-...     (Bearer token style)
#     #   Stripe:   Authorization: Bearer sk_live_...
#     #   Google:   ?key=AIzaSy...                   (query param)
#     #   GitHub:   Authorization: token ghp_...     (custom scheme)
#     #   AWS:      Authorization: AWS4-HMAC-SHA256  (SigV4 signature)
#
# ── X-<Name> Custom Headers ──────────────────────────────────────
#   "X-" prefix = custom header defined by YOUR application.
#   FastAPI auto-converts: "X-Request-ID" → Python param x_request_id
#   (underscores replace hyphens, everything lowercase)
#
#   BEGINNER EXAMPLE — Custom headers:
#
#     @app.get("/api/data")
#     async def get_data(
#         x_request_id: Annotated[str | None, Header()] = None,
#         x_tenant_id: Annotated[str | None, Header()] = None,
#     ):
#         ...
#
#     # curl http://localhost:8000/api/data \
#     #      -H "X-Request-ID: req-abc-123" \
#     #      -H "X-Tenant-ID: acme-corp"
#     #
#     #   Header names sent:        Python parameter names:
#     #   X-Request-ID    ────────→  x_request_id
#     #   X-Tenant-ID     ────────→  x_tenant_id
#     #   Content-Type    ────────→  content_type
#     #   User-Agent      ────────→  user_agent
#     #
#     #   Rule: hyphens → underscores, all lowercase
#     #   "X-My-Custom-Header" → x_my_custom_header
#
# ── Content-Type — Common Values ─────────────────────────────────
#   application/json                    → JSON body (most APIs)
#   application/x-www-form-urlencoded   → HTML form: key=val&key2=val2
#   multipart/form-data                 → File uploads
#   text/html                           → HTML page
#   text/plain                          → Plain text
#   text/csv                            → CSV data
#   application/xml                     → XML
#   application/pdf                     → PDF file
#   application/octet-stream            → Raw binary (downloads)
#   image/png, image/jpeg               → Images
#
#   BEGINNER EXAMPLE — Content-Type matters:
#
#     # Sending JSON (most common for APIs):
#     #   curl -X POST http://localhost:8000/orders \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"product": "Laptop", "qty": 2}'
#     #   FastAPI sees Content-Type: application/json → parses body as JSON
#     #
#     # Sending form data (HTML forms, login):
#     #   curl -X POST http://localhost:8000/login \
#     #        -d "username=admin&password=secret"
#     #   curl auto-sets Content-Type: application/x-www-form-urlencoded
#     #   FastAPI uses Form() to read these fields
#     #
#     # Uploading a file:
#     #   curl -X POST http://localhost:8000/upload -F "file=@photo.jpg"
#     #   curl auto-sets Content-Type: multipart/form-data
#     #   FastAPI uses File() / UploadFile to read the file
#     #
#     # KEY INSIGHT: Content-Type tells the server HOW to parse the body.
#     # Wrong Content-Type = server can't read your data!
#
# ── Cookies vs Headers — When to Use Which ───────────────────────
#   Cookies: auto-sent by browser on every request to that domain
#            great for web apps (session tokens, preferences)
#            set by server via Set-Cookie response header
#   Headers: manually added by client code (fetch, axios, curl)
#            great for APIs (tokens, API keys, metadata)
#            not auto-sent — you control exactly what's included
#
#   BEGINNER EXAMPLE — Cookies vs Headers:
#
#     # COOKIE flow (browser web app):
#     #   1. Login: POST /login → server responds with Set-Cookie: session=abc123
#     #   2. Browser AUTOMATICALLY sends Cookie: session=abc123 on every request
#     #   3. No client code needed — browser handles it
#     #
#     # HEADER flow (API / mobile app):
#     #   1. Login: POST /auth/token → server responds with {"token": "eyJ..."}
#     #   2. Client manually stores token (localStorage, keychain)
#     #   3. Client manually adds: Authorization: Bearer eyJ... to every request
#     #   4. Full control — but more work for the developer
#     #
#     # Why APIs prefer headers over cookies:
#     #   - Cookies are domain-bound (can't use cross-domain easily)
#     #   - Cookies are vulnerable to CSRF attacks
#     #   - Headers work identically from any client (browser, mobile, CLI)
#     #   - Headers are explicit — no "magic" auto-sending
#
# ── FastAPI Header() — Conversion Rules ──────────────────────────
#   FastAPI automatically converts between HTTP header names and Python:
#     HTTP header name    →  Python parameter name
#     Content-Type        →  content_type
#     X-Request-ID        →  x_request_id
#     User-Agent          →  user_agent
#     Authorization       →  authorization
#     Accept-Language     →  accept_language
#
#   Rules:
#     1. Hyphens (-) become underscores (_)
#     2. Everything becomes lowercase
#     3. This is automatic — you don't need to configure it
#
#   To disable conversion (rare):
#     x_weird: Annotated[str, Header(convert_underscores=False)]
#     → reads header named literally "x_weird" (with underscore)
#
# ── WWW-Authenticate — Server Tells Client How to Auth ───────────
#   When server returns 401, it SHOULD include WWW-Authenticate header
#   telling the client WHICH auth method to use.
#
#     HTTP/1.1 401 Unauthorized
#     WWW-Authenticate: Bearer realm="api"
#     → Client should retry with: Authorization: Bearer <token>
#
#     HTTP/1.1 401 Unauthorized
#     WWW-Authenticate: Basic realm="admin area"
#     → Browser auto-pops up username/password dialog!
#
# ══════════════════════════════════════════════════════════════════
