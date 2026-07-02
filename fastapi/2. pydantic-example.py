# ══════════════════════════════════════════════════════════════════
#  FastAPI + Pydantic — Typed Models, Validation, Nested Data
#  Run: uvicorn "2. pydantic-example":app --reload
#
#  NOTE: See 1.CRUD.py for raw dict CRUD patterns (path/query/body/
#  header/cookie/form/file). This file covers Pydantic-only features.
#
#  dict = Body()        vs   BaseModel (Pydantic)
#  ──────────────────        ────────────────────
#  No validation             Auto-validates all fields
#  KeyError at runtime       422 error with clear message
#  No docs in Swagger        Full schema in Swagger UI
#  data["key"]               data.key (dot access)
# ══════════════════════════════════════════════════════════════════
from enum import Enum
from fastapi import Body, FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional

app = FastAPI()
shipment_data = {
    1: {"id": 1, "content": "Shipment 1 content", "weight": 10, "status": "In Transit"},
    2: {"id": 2, "content": "Shipment 2 content", "weight": 20, "status": "Delivered"},
    3: {"id": 3, "content": "Shipment 3 content", "weight": 15, "status": "Pending"},
}

# ╔══════════════════════════════════════════════════╗
# ║              BEGINNER                            ║
# ╚══════════════════════════════════════════════════╝

# ── 1. Basic BaseModel — auto validation + Swagger docs ──────────────────────────────
class ShipmentCreate(BaseModel):
    content: str                       # required — no default
    weight: float                      # required — no default
    status: str = "Pending"            # optional — has default

@app.post("/shipment/pydantic", status_code=status.HTTP_201_CREATED)
def create_with_pydantic(data: ShipmentCreate):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": data.content, "weight": data.weight, "status": data.status}
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/pydantic -H "Content-Type: application/json" -d '{"content":"New","weight":30}'
# Missing field -> 422: {"detail":[{"loc":["body","weight"],"msg":"Field required"}]}
# Wrong type   -> 422: {"detail":[{"loc":["body","weight"],"msg":"Input should be a valid number"}]}

# ── 2. Field() Constraints — like Query()/Path() but for body ──────────────────────────────
class ShipmentCreateValidated(BaseModel):
    content: str = Field(min_length=3, max_length=200, description="3-200 chars", examples=["Electronics from warehouse A"])
    weight: float = Field(gt=0, le=10000, description="Weight in kg (>0, max 10000)", examples=[25.5])
    status: str = Field(default="Pending", examples=["Pending", "In Transit", "Delivered"])

@app.post("/shipment/pydantic-validated", status_code=status.HTTP_201_CREATED)
def create_with_field_validation(data: ShipmentCreateValidated):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": data.content, "weight": data.weight, "status": data.status}
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/pydantic-validated -H "Content-Type: application/json" -d '{"content":"Electronics","weight":25.5}'
# content="AB" -> 422: "String should have at least 3 characters"
# weight=-5    -> 422: "Input should be greater than 0"

# ╔══════════════════════════════════════════════════╗
# ║            INTERMEDIATE                          ║
# ╚══════════════════════════════════════════════════╝

# ── 3. Optional Fields — for PATCH/partial update ──────────────────────────────
class ShipmentUpdate(BaseModel):
    content: Optional[str] = None      # can be missing
    weight: Optional[float] = None
    status: Optional[str] = None

@app.put("/shipment/pydantic/{id}")
def update_with_pydantic(id: int, data: ShipmentUpdate):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    if data.content is not None:
        shipment_data[id]["content"] = data.content
    if data.weight is not None:
        shipment_data[id]["weight"] = data.weight
    if data.status is not None:
        shipment_data[id]["status"] = data.status
    return shipment_data[id]
# curl -X PUT http://localhost:8000/shipment/pydantic/1 -H "Content-Type: application/json" -d '{"status":"Delivered"}'
# Empty body {} -> nothing changes, returns current state

# ── 4. Enum Validation — restrict to allowed values ──────────────────────────────
class ShipmentStatus(str, Enum):
    PENDING = "Pending"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"

class ShipmentCreateWithEnum(BaseModel):
    content: str
    weight: float = Field(gt=0)
    status: ShipmentStatus = ShipmentStatus.PENDING  # only 4 values allowed

@app.post("/shipment/pydantic-enum", status_code=status.HTTP_201_CREATED)
def create_with_enum(data: ShipmentCreateWithEnum):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": data.content, "weight": data.weight, "status": data.status.value}
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/pydantic-enum -H "Content-Type: application/json" -d '{"content":"Test","weight":10,"status":"In Transit"}'
# status="Lost" -> 422: "Input should be 'Pending', 'In Transit', 'Delivered' or 'Cancelled'"

# ── 5. field_validator — custom validation logic ──────────────────────────────
class ShipmentCreateCustomValidation(BaseModel):
    content: str
    weight: float
    status: str = "Pending"

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("Content cannot be empty or whitespace")
        return v.strip()  # auto-trim

    @field_validator("weight")
    @classmethod
    def weight_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Weight must be > 0")
        if v > 50000:
            raise ValueError("Weight cannot exceed 50000 kg")
        return round(v, 2)  # auto-round

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: str) -> str:
        allowed = ["Pending", "In Transit", "Delivered", "Cancelled"]
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v

@app.post("/shipment/pydantic-custom", status_code=status.HTTP_201_CREATED)
def create_with_custom_validation(data: ShipmentCreateCustomValidation):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": data.content, "weight": data.weight, "status": data.status}
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/pydantic-custom -H "Content-Type: application/json" -d '{"content":"  Electronics  ","weight":25.666}'
# -> content="Electronics" (trimmed), weight=25.67 (rounded)
# content="   " -> 422: "Content cannot be empty or whitespace"

# ── 6. model_validator — cross-field validation ──────────────────────────────
class ShipmentCreateCrossField(BaseModel):
    content: str
    weight: float = Field(gt=0)
    max_weight: float = Field(gt=0)
    status: str = "Pending"

    @model_validator(mode="after")
    def weight_must_not_exceed_max(self):
        if self.weight > self.max_weight:
            raise ValueError(f"weight ({self.weight}) cannot exceed max_weight ({self.max_weight})")
        return self

@app.post("/shipment/pydantic-cross", status_code=status.HTTP_201_CREATED)
def create_with_cross_validation(data: ShipmentCreateCrossField):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id, "content": data.content, "weight": data.weight,
        "max_weight": data.max_weight, "status": data.status,
    }
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/pydantic-cross -H "Content-Type: application/json" -d '{"content":"Test","weight":20,"max_weight":50}'
# weight=100, max_weight=50 -> 422: "weight (100.0) cannot exceed max_weight (50.0)"

# ╔══════════════════════════════════════════════════╗
# ║              ADVANCED                            ║
# ╚══════════════════════════════════════════════════╝

# ── 7. Nested Models — structured data ──────────────────────────────
class Address(BaseModel):
    street: str
    city: str
    country: str = "US"
    zip_code: Optional[str] = None

class Dimensions(BaseModel):
    length: float = Field(gt=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)

class ShipmentCreateNested(BaseModel):
    content: str
    weight: float = Field(gt=0)
    origin: Address                           # required nested
    destination: Address                      # required nested
    dimensions: Optional[Dimensions] = None   # optional nested

@app.post("/shipment/pydantic-nested", status_code=status.HTTP_201_CREATED)
def create_with_nested(data: ShipmentCreateNested):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id, "content": data.content, "weight": data.weight,
        "origin": data.origin.model_dump(),
        "destination": data.destination.model_dump(),
        "dimensions": data.dimensions.model_dump() if data.dimensions else None,
        "status": "Pending",
    }
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/pydantic-nested -H "Content-Type: application/json" -d '{"content":"Electronics","weight":25,"origin":{"street":"123 Main","city":"NYC"},"destination":{"street":"456 Oak","city":"London","country":"UK"}}'
# Missing nested field -> 422: origin.city "Field required"

# ── 8. List[Model] — batch create ──────────────────────────────
class ShipmentItem(BaseModel):
    content: str
    weight: float = Field(gt=0)
    status: str = "Pending"

@app.post("/shipment/pydantic-batch", status_code=status.HTTP_201_CREATED)
def create_batch(items: List[ShipmentItem]):
    created = []
    for item in items:
        new_id = max(shipment_data.keys()) + 1
        shipment_data[new_id] = {"id": new_id, "content": item.content, "weight": item.weight, "status": item.status}
        created.append(shipment_data[new_id])
    return {"created": len(created), "shipments": created}
# curl -X POST http://localhost:8000/shipment/pydantic-batch -H "Content-Type: application/json" -d '[{"content":"A","weight":10},{"content":"B","weight":20}]'
# One bad item fails entire batch: weight=-5 -> 422

# ── 9. response_model — control output shape ──────────────────────────────
class ShipmentResponse(BaseModel):
    id: int
    content: str
    weight: float
    status: str

@app.get("/shipment/pydantic-response/{id}", response_model=ShipmentResponse)
def get_with_response_model(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]  # extra fields stripped by response_model
# curl http://localhost:8000/shipment/pydantic-response/1

# ── 10. PATH + QUERY + BODY all together ──────────────────────────────
class ShipmentPatch(BaseModel):
    content: Optional[str] = None
    weight: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None

@app.patch("/shipment/pydantic/{id}")
def patch_with_pydantic(
    id: int,                                                          # path
    dry_run: bool = Query(False, description="Preview without saving"),  # query
    data: ShipmentPatch = Body(),                                     # body
):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    changes = {}
    if data.content is not None:
        changes["content"] = data.content
    if data.weight is not None:
        changes["weight"] = data.weight
    if data.status is not None:
        changes["status"] = data.status
    if not dry_run:
        shipment_data[id].update(changes)
    return {"shipment": shipment_data[id], "changes_applied": not dry_run, "changes": changes}
# curl -X PATCH "http://localhost:8000/shipment/pydantic/1" -H "Content-Type: application/json" -d '{"status":"Delivered","weight":50}'
# curl -X PATCH "http://localhost:8000/shipment/pydantic/1?dry_run=true" -H "Content-Type: application/json" -d '{"status":"Cancelled"}'

# ══════════════════════════════════════════════════════════════════
#  CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
# FEATURE              | SYNTAX                                  | EFFECT
# ---------------------|----------------------------------------|---------------------------
# BaseModel            | class M(BaseModel): name: str          | Auto-validate + Swagger
# Field() constraints  | Field(gt=0, max_length=200)            | Range/length checks
# Optional field       | name: Optional[str] = None             | Can be missing (PATCH)
# Default value        | status: str = "Pending"                | Fallback if omitted
# Enum validation      | class S(str, Enum): A="a"              | Restrict allowed values
# field_validator      | @field_validator("name")                | Custom per-field logic
# model_validator      | @model_validator(mode="after")          | Cross-field checks
# Nested model         | address: Address                       | Deep validation
# List[Model]          | items: List[Item]                      | Batch with per-item checks
# response_model       | @app.get(..., response_model=M)        | Filter output fields
# model_dump()         | data.model_dump()                      | Model -> dict
# ══════════════════════════════════════════════════════════════════
