import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP ──────────────────────────────────────────────
    print("🚀 Starting up...")
    app.state.http_client = httpx.AsyncClient(timeout=30)
    app.state.shipments = {
        1: {"id": 1, "content": "Wooden Table", "weight": 10, "status": "In Transit"},
        2: {"id": 2, "content": "Steel Chair", "weight": 20, "status": "Delivered"},
        3: {"id": 3, "content": "Glass Vase", "weight": 5, "status": "Pending"},
    }
    print(f"📦 Loaded {len(app.state.shipments)} shipments")

    yield  # ← server is live, handling requests

    # ── SHUTDOWN ─────────────────────────────────────────────
    print("🛑 Shutting down...")
    await app.state.http_client.aclose()
    print("✅ HTTP client closed")


app = FastAPI(
    title="Shipment Tracker API",
    lifespan=lifespan,
)


# ── Routes ───────────────────────────────────────────────────

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

