# ══════════════════════════════════════════════════════════════════
# Testing FastAPI Apps — TestClient & pytest
# ══════════════════════════════════════════════════════════════════
# Deps:  pip install fastapi httpx pytest pytest-asyncio
# Run:   pytest 09-testing-with-pytest.py -v
#
# NOTE: For testing lifespan (startup/shutdown) specifically, see
# 07-lifespan.py section 10 — this file covers testing ORDINARY routes:
# CRUD assertions, mocking dependencies, async clients, validation errors.
# ══════════════════════════════════════════════════════════════════
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

app = FastAPI()
shipment_data = {1: {"id": 1, "content": "Books", "weight": 5.0, "status": "Pending"}}


class ShipmentCreate(BaseModel):
    content: str
    weight: float


class ShipmentOut(BaseModel):
    id: int
    content: str
    weight: float
    status: str


def get_current_user():
    # In real code: decode a JWT/session (see 08-session.py). Kept trivial
    # here so the DEPENDENCY OVERRIDE example below has something to swap.
    return {"username": "real-user"}


@app.get("/shipments/{shipment_id}", response_model=ShipmentOut)
def get_shipment(shipment_id: int):
    if shipment_id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[shipment_id]


@app.post("/shipments", response_model=ShipmentOut, status_code=201)
def create_shipment(data: ShipmentCreate, user: dict = Depends(get_current_user)):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": data.content, "weight": data.weight, "status": "Pending"}
    return shipment_data[new_id]


# ╔══════════════════════════════════════════════════╗
# ║                   BEGINNER                       ║
# ╚══════════════════════════════════════════════════╝

# ── 1. TestClient basics — GET ──────────────────────────────
# TestClient wraps the app and lets you call routes directly, in-process,
# with NO real network socket or running server needed.
client = TestClient(app)


def test_get_existing_shipment():
    response = client.get("/shipments/1")
    assert response.status_code == 200
    assert response.json()["content"] == "Books"


def test_get_missing_shipment_returns_404():
    response = client.get("/shipments/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found"}


# ── 2. POST / body payloads ──────────────────────────────
def test_create_shipment():
    response = client.post("/shipments", json={"content": "Laptops", "weight": 12.5})
    assert response.status_code == 201
    body = response.json()
    assert body["content"] == "Laptops"
    assert body["status"] == "Pending"  # server-assigned default


# ── 3. Validation errors (422) ──────────────────────────────
def test_create_shipment_missing_field_returns_422():
    response = client.post("/shipments", json={"content": "Laptops"})  # weight missing
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(e["loc"][-1] == "weight" for e in errors)


# ╔══════════════════════════════════════════════════╗
# ║               INTERMEDIATE                       ║
# ╚══════════════════════════════════════════════════╝

# ── 4. Dependency overrides — mock auth/DB without touching real code ──────
# app.dependency_overrides is a dict: {original_dependency: replacement_fn}.
# This is THE standard way to swap a real auth/DB dependency for a fake one
# in tests — no monkeypatching, no changing the endpoint code at all.
def fake_current_user():
    return {"username": "test-user"}


def test_create_shipment_with_overridden_dependency():
    app.dependency_overrides[get_current_user] = fake_current_user
    try:
        response = client.post("/shipments", json={"content": "Books", "weight": 1.0})
        assert response.status_code == 201
    finally:
        app.dependency_overrides.clear()  # GOTCHA: always clear — overrides leak across tests otherwise


# ── 5. Async endpoint testing — httpx.AsyncClient + ASGITransport ──────
# TestClient is sync and fine for most cases. For genuinely async test code
# (e.g. awaiting other async fixtures), use AsyncClient wired directly to
# the app via ASGITransport — no real network, same in-process call.
@pytest.mark.asyncio
async def test_get_shipment_async():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/shipments/1")
    assert response.status_code == 200


# ══════════════════════════════════════════════════════════════════
# CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
# NEED                          | HOW
# ------------------------------|----------------------------------------
# Call a route in a test         | TestClient(app).get/post/put/delete(...)
# Assert JSON body               | response.json() == {...}
# Assert validation error        | response.status_code == 422
# Mock a dependency               | app.dependency_overrides[dep] = fake_dep
# Undo a mock                     | app.dependency_overrides.clear()
# Test an async endpoint          | httpx.AsyncClient(transport=ASGITransport(app=app))
# Test startup/shutdown           | see 07-lifespan.py §10 (TestClient triggers lifespan)
# ══════════════════════════════════════════════════════════════════
#
# ══════════════════════════════════════════════════════════════════
#  TESTING FASTAPI APPS — DETAILED REFERENCE
# ══════════════════════════════════════════════════════════════════
#
# ── Why TestClient needs no running server ─────────────────────
#   TestClient is built on httpx and talks to your `app` object directly
#   through its ASGI interface — the same interface uvicorn uses to call
#   your app, just without a real socket/port. That's why tests are fast
#   and don't need `uvicorn` running in the background.
#
# ── dependency_overrides gotchas ─────────────────────
#   1. Keys are the ORIGINAL function object, not a string name:
#        app.dependency_overrides[get_current_user] = fake_current_user
#   2. Overrides are GLOBAL and MUTABLE on the `app` instance — if one test
#      forgets to clear them, later tests silently inherit the mock. Prefer
#      a pytest fixture with a `yield` + cleanup, or a try/finally as above.
#   3. You can override a dependency with another dependency that itself
#      has sub-dependencies — FastAPI resolves the whole replaced chain.
#
# ── A typical pytest fixture version of the override pattern ───
#   import pytest
#
#   @pytest.fixture
#   def client_as_test_user():
#       app.dependency_overrides[get_current_user] = fake_current_user
#       yield TestClient(app)
#       app.dependency_overrides.clear()
#
#   def test_something(client_as_test_user):
#       response = client_as_test_user.post("/shipments", json={...})
#       assert response.status_code == 201
#
# ── Testing raised HTTPException vs uncaught exceptions ───
#   TestClient re-raises unhandled server errors by default so tests fail
#   loudly instead of silently returning a 500. To assert on a 500 response
#   itself (rare), pass `raise_server_exceptions=False` to TestClient(...).
#
# ── conftest.py pattern for a real project ───
#   Put the `client` fixture (and any dependency-override fixtures) in a
#   conftest.py at your test root so every test file can use them without
#   re-importing TestClient/the app in each file.
# ══════════════════════════════════════════════════════════════════
