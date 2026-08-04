# ══════════════════════════════════════════════════════════════════
# FastAPI Lifespan — Startup, Shutdown & Resource Management
# ══════════════════════════════════════════════════════════════════
# Deps:  pip install fastapi uvicorn httpx
# Run:   uvicorn lifespan:app --reload
# Docs:  http://127.0.0.1:8000/docs
#
# Lifespan = the async context manager that wraps your entire app.
# Code BEFORE yield runs once at startup (open connections, load data).
# Code AFTER  yield runs once at shutdown (close connections, flush).
#
#   startup code
#       |
#       v
#     yield  <-- app serves requests while yielded
#       |
#       v
#   shutdown code

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import httpx
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse


# ── What is @asynccontextmanager? ────────────────────
#
# A decorator from `contextlib` that converts an async generator
# (a function with `yield`) into an `async with`-compatible
# context manager — no class needed.
#
#   WITHOUT it (full class):
#
#     class DBManager:
#         async def __aenter__(self):
#             self.conn = await connect()
#             return self.conn
#         async def __aexit__(self, *exc):
#             await self.conn.close()
#
#   WITH it (shortcut — same behavior):
#
#     @asynccontextmanager
#     async def db_manager():
#         conn = await connect()    # __aenter__ (setup)
#         yield conn                # value for `async with ... as X`
#         await conn.close()        # __aexit__ (cleanup)
#
#   Both used the same way:
#     async with db_manager() as conn:
#         await conn.execute("SELECT 1")
#
#   KEY RULE:
#     before yield = setup    (runs once at start)
#     yield        = hand off (caller runs while yielded)
#     after yield  = cleanup  (runs once at end)
#
#   If setup raises before yield, cleanup code after yield
#   NEVER executes — this is why FastAPI chose it for lifespan.
#
#   Sync equivalent: @contextmanager (regular def + yield, no async)


# ╔══════════════════════════════════════════════════╗
# ║               BEGINNER                           ║
# ╚══════════════════════════════════════════════════╝


# ── 1. Minimal lifespan ─────────────────────────────
# The simplest possible lifespan — just proves the
# startup/shutdown hooks fire.

@asynccontextmanager
async def minimal_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print(">>> APP STARTING")
    yield
    print(">>> APP SHUTTING DOWN")

# Usage: FastAPI(lifespan=minimal_lifespan)


# ── 2. Old vs new (why lifespan replaced on_event) ──
# BEFORE (deprecated since FastAPI 0.93):
#
#   @app.on_event("startup")
#   async def startup():
#       app.state.db = await connect_db()
#
#   @app.on_event("shutdown")
#   async def shutdown():
#       await app.state.db.close()
#
# PROBLEMS with on_event:
#   - startup and shutdown are separate functions with no shared scope
#   - if startup fails halfway, shutdown still runs for resources
#     that were never created -> crashes or silent bugs
#   - no way to guarantee cleanup order
#
# AFTER (lifespan context manager):
#
#   @asynccontextmanager
#   async def lifespan(app):
#       db = await connect_db()      # startup
#       app.state.db = db
#       yield                         # app runs
#       await db.close()              # shutdown (only runs if startup succeeded)
#
# The context manager guarantees: if startup raises before yield,
# the shutdown code after yield never executes.


# ── 3. Sharing resources via app.state ──────────────
# Create expensive resources once, share across all requests.

@asynccontextmanager
async def basic_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup — create an HTTP client with connection pooling
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=20),
    )
    print(f"[startup] HTTP client ready (pool=20)")

    yield  # app serves requests here

    # Shutdown — close the client, release all connections
    await app.state.http_client.aclose()
    print("[shutdown] HTTP client closed")


# ╔══════════════════════════════════════════════════╗
# ║             INTERMEDIATE                         ║
# ╚══════════════════════════════════════════════════╝


# ── 4. Multiple resources in one lifespan ────────────
# Real apps need several resources. Initialise them in order,
# tear them down in reverse order (like a stack).

_cache: dict[str, Any] = {}

@asynccontextmanager
async def multi_resource_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 1) HTTP client
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=20),
    )

    # 2) In-memory cache (stands in for Redis/Memcached)
    _cache.clear()
    _cache["app_version"] = "1.0.0"
    app.state.cache = _cache

    # 3) Simulated DB pool (replace with asyncpg/sqlalchemy in real code)
    app.state.db_pool = {"status": "connected", "max_size": 10}

    print("[startup] All resources initialised")
    yield
    # Teardown in reverse order
    app.state.db_pool = None
    _cache.clear()
    await app.state.http_client.aclose()
    print("[shutdown] All resources released")


# ── 5. Error handling in lifespan ────────────────────
# If one resource fails to init, clean up anything already created.

@asynccontextmanager
async def safe_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    http_client = None
    try:
        # Resource 1 — might succeed
        http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
        app.state.http_client = http_client

        # Resource 2 — might fail (simulated)
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            # Non-critical: warn but continue
            print("[startup] WARNING: DATABASE_URL not set, DB features disabled")
            app.state.db_pool = None
        else:
            app.state.db_pool = {"url": db_url, "status": "connected"}

        print("[startup] Ready")
        yield

    finally:
        # Always clean up whatever was created
        if http_client:
            await http_client.aclose()
            print("[shutdown] HTTP client closed")


# ── 6. Background tasks in lifespan ──────────────────
# Start a periodic background job at startup, cancel on shutdown.

async def _periodic_cleanup(interval_seconds: int = 60):
    """Run cleanup every N seconds until cancelled."""
    while True:
        await asyncio.sleep(interval_seconds)
        print(f"[cleanup] Running periodic cleanup...")
        # Real work: expire cache entries, delete stale sessions, etc.

@asynccontextmanager
async def bg_task_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Start background task
    cleanup_task = asyncio.create_task(
        _periodic_cleanup(interval_seconds=60),
        name="periodic-cleanup",
    )
    print("[startup] Background cleanup task started")

    yield

    # Cancel and await the task so it exits cleanly
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    print("[shutdown] Background cleanup task stopped")


# ── 7. Dependency injection (cleaner than app.state) ─
# Instead of reaching into request.app.state everywhere, create
# a Depends() function that returns the resource. Routes declare
# what they need; FastAPI wires it up.

def get_http_client(request: Request) -> httpx.AsyncClient:
    """Dependency that provides the shared HTTP client."""
    return request.app.state.http_client

def get_cache(request: Request) -> dict[str, Any]:
    """Dependency that provides the shared cache."""
    return request.app.state.cache

# Usage in route:
#   @app.get("/proxy")
#   async def proxy(client: httpx.AsyncClient = Depends(get_http_client)):
#       resp = await client.get("https://httpbin.org/get")
#       return resp.json()


# ╔══════════════════════════════════════════════════╗
# ║               ADVANCED                           ║
# ╚══════════════════════════════════════════════════╝


# ── 8. Startup config validation (production pattern) ─
# Validate configuration at startup and log redacted credentials.
# Fail fast if critical config is missing.
# Pattern from: reuters-assistant_backend/src/app.py

logger = logging.getLogger(__name__)

def _validate_config() -> dict[str, str]:
    """Check required env vars at startup. Raise if critical ones are missing."""
    config = {
        "API_KEY": os.getenv("API_KEY", ""),
        "DATABASE_URL": os.getenv("DATABASE_URL", ""),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
    }

    # Log redacted values so ops can verify secrets resolved
    for key, val in config.items():
        if val:
            redacted = val[:4] + "..." if len(val) > 4 else "***"
            logger.info(f"Config {key}: {redacted}")
        else:
            logger.warning(f"Config {key}: <not set>")

    # Fail fast on critical missing config (only in production)
    if config["ENVIRONMENT"] == "production" and not config["API_KEY"]:
        raise RuntimeError("API_KEY is required in production")

    return config

@asynccontextmanager
async def production_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("=== STARTUP CONFIG CHECK ===")
    config = _validate_config()
    app.state.config = config
    logger.info(f"Environment: {config['ENVIRONMENT']}")
    logger.info("============================")

    # Init resources
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_connections=20),
    )

    # Background cleanup
    cleanup_task = asyncio.create_task(
        _periodic_cleanup(interval_seconds=300),
        name="session-cleanup",
    )

    logger.info("App started successfully")
    yield

    # Graceful shutdown
    logger.info("Shutting down...")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    await app.state.http_client.aclose()
    logger.info("Shutdown complete")


# ── 9. Graceful shutdown with timeout ────────────────
# In production, shutdown must complete within a deadline
# (e.g., ECS sends SIGTERM and kills after 30s).
# Use asyncio.wait_for to enforce a time limit.

async def _shutdown_with_timeout(app: FastAPI, timeout: float = 10.0):
    """Close resources with a hard timeout."""
    try:
        await asyncio.wait_for(
            _do_cleanup(app),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.error(f"Shutdown timed out after {timeout}s - forcing exit")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

async def _do_cleanup(app: FastAPI):
    """Actual cleanup work — may take a while."""
    if hasattr(app.state, "http_client"):
        await app.state.http_client.aclose()
    if hasattr(app.state, "cleanup_task"):
        app.state.cleanup_task.cancel()
        try:
            await app.state.cleanup_task
        except asyncio.CancelledError:
            pass
    logger.info("All resources cleaned up")

@asynccontextmanager
async def timeout_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    app.state.http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))
    app.state.cleanup_task = asyncio.create_task(
        _periodic_cleanup(300), name="cleanup"
    )
    yield
    await _shutdown_with_timeout(app, timeout=10.0)


# ── 10. Testing lifespan ─────────────────────────────
# TestClient automatically triggers lifespan events.
# For async tests, use httpx + ASGITransport.
#
# SYNC test (pytest):
#
#   from fastapi.testclient import TestClient
#
#   def test_startup_creates_client():
#       with TestClient(app) as client:    # triggers lifespan
#           resp = client.get("/status")
#           assert resp.status_code == 200
#           assert resp.json()["http_client"] == "ready"
#       # exiting `with` triggers shutdown
#
#
# ASYNC test (pytest-asyncio):
#
#   import pytest
#   from httpx import ASGITransport, AsyncClient
#
#   @pytest.mark.asyncio
#   async def test_startup_async():
#       transport = ASGITransport(app=app)
#       async with AsyncClient(transport=transport, base_url="http://test") as c:
#           resp = await c.get("/status")
#           assert resp.status_code == 200
#
#
# KEY POINT: TestClient triggers lifespan by default. If you want
# to test WITHOUT lifespan (e.g., unit-testing a single route),
# pass raise_server_exceptions=False or mock app.state directly.


# ═══════════════════════════════════════════════════════
# RUNNABLE APP — uses production_lifespan from section 8
# ═══════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Lifespan Demo", lifespan=production_lifespan)


@app.get("/")
async def root():
    return {"message": "App is running", "environment": app.state.config["ENVIRONMENT"]}


@app.get("/status")
async def status(client: httpx.AsyncClient = Depends(get_http_client)):
    """Check that lifespan-created resources are available."""
    return {
        "http_client": "ready" if client else "missing",
        "config": app.state.config,
    }


@app.get("/proxy")
async def proxy_example(client: httpx.AsyncClient = Depends(get_http_client)):
    """Use the shared HTTP client to call an external API."""
    resp = await client.get("https://httpbin.org/get")
    return resp.json()
