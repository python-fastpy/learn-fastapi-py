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
#
# ══════════════════════════════════════════════════════════════════
#  PYDANTIC & FASTAPI DECLARATIONS — DETAILED REFERENCE
# ══════════════════════════════════════════════════════════════════
#
# ── BaseModel — The core Pydantic model ──────────────────────────
#   class ShipmentCreate(BaseModel):
#       content: str                   → required, no default — request fails 422 without it
#       weight: float                  → required, auto-validates type (string "abc" → 422)
#       status: str = "Pending"        → optional, uses default if omitted
#   Usage: def create(data: ShipmentCreate)  → FastAPI auto-reads from JSON body
#   vs dict = Body(): BaseModel gives validation, dot access (data.content), Swagger schema
#
#   BEGINNER EXAMPLE — BaseModel:
#
#     class ShipmentCreate(BaseModel):
#         content: str                     # required
#         weight: float                    # required
#         status: str = "Pending"          # optional, default "Pending"
#
#     @app.post("/shipment")
#     def create(data: ShipmentCreate):
#         ...
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/shipment" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"content": "Table", "weight": 25.5}'
#     #
#     #   Body: {"content": "Table", "weight": 25.5}
#     #          │                    │
#     #          ▼                    ▼
#     #   Inside function:
#     #     data.content → "Table"       ← from body (required)
#     #     data.weight  → 25.5          ← from body (required)
#     #     data.status  → "Pending"     ← NOT sent → uses default
#     #
#     #   curl ... -d '{"content": "Table"}'           → 422! weight is required
#     #   curl ... -d '{"content": "Table", "weight": "abc"}'  → 422! float expected
#     #
#     # vs dict = Body():
#     #   BaseModel: data.content (dot access), auto-validation, Swagger schema
#     #   dict:      data["content"] (bracket access), no validation, no schema
#
# ── Field() — Validation constraints for model fields ────────────
#   content: str = Field(min_length=3, max_length=200)   → string length limits
#   weight: float = Field(gt=0, le=10000)                → numeric range (gt/ge/lt/le)
#   status: str = Field(default="Pending")               → default value
#   Field(description="...", examples=["..."])            → OpenAPI docs metadata
#   Field() is to BaseModel what Query()/Path() is to route parameters
#
#   BEGINNER EXAMPLE — Field():
#
#     class Item(BaseModel):
#         content: str = Field(min_length=3, max_length=200)
#         weight: float = Field(gt=0, le=10000)
#
#     @app.post("/item")
#     def create(data: Item):
#         ...
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/item" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"content": "Wooden Table", "weight": 25.0}'
#     #
#     #   Body: {"content": "Wooden Table", "weight": 25.0}
#     #          │                           │
#     #          ▼                           ▼
#     #   Inside function:
#     #     data.content → "Wooden Table"   ← valid (3-200 chars)
#     #     data.weight  → 25.0             ← valid (0 < 25 <= 10000)
#     #
#     #   curl ... -d '{"content": "AB", "weight": 5}'   → 422! min_length=3 fails
#     #   curl ... -d '{"content": "OK", "weight": -1}'  → 422! gt=0 fails
#     #   curl ... -d '{"content": "OK", "weight": 99999}' → 422! le=10000 fails
#
# ── Optional fields — For PATCH/partial updates ──────────────────
#   content: Optional[str] = None     → field can be missing from request body
#   Check with: if data.content is not None → only update fields that were sent
#   Use model_dump(exclude_unset=True) to get only fields explicitly provided
#
#   BEGINNER EXAMPLE — Optional fields (PATCH):
#
#     class ShipmentPatch(BaseModel):
#         content: Optional[str] = None
#         weight: Optional[float] = None
#         status: Optional[str] = None
#
#     @app.patch("/shipment/{id}")
#     def update(id: int, data: ShipmentPatch):
#         ...
#
#     # How to call (send only what changed):
#     #   curl -X PATCH "http://localhost:8000/shipment/1" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"status": "Delivered"}'
#     #
#     #   Body: {"status": "Delivered"}     ← only status sent
#     #          │
#     #          ▼
#     #   Inside function:
#     #     data.content → None          ← not sent → None (skip update)
#     #     data.weight  → None          ← not sent → None (skip update)
#     #     data.status  → "Delivered"   ← sent → update this field
#     #
#     #   curl ... -d '{}'    → all fields None → no changes (valid request)
#     #   curl ... -d '{"weight": 50, "content": "New"}' → updates 2 fields
#
# ── Enum — Restrict to allowed values ────────────────────────────
#   class Status(str, Enum):          → must inherit BOTH str and Enum
#       PENDING = "Pending"
#   Invalid value → 422: "Input should be 'Pending', 'In Transit', ..."
#   Access: data.status.value → "Pending" (string), data.status → Status.PENDING (enum)
#
#   BEGINNER EXAMPLE — Enum validation:
#
#     class Status(str, Enum):
#         PENDING = "Pending"
#         TRANSIT = "In Transit"
#         DELIVERED = "Delivered"
#
#     class Shipment(BaseModel):
#         content: str
#         status: Status = Status.PENDING
#
#     @app.post("/shipment")
#     def create(data: Shipment):
#         ...
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/shipment" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"content": "Table", "status": "Delivered"}'
#     #
#     #   Inside function:
#     #     data.status       → Status.DELIVERED   ← enum member
#     #     data.status.value → "Delivered"         ← string value
#     #
#     #   curl ... -d '{"content": "Table", "status": "Lost"}'
#     #     → 422! "Input should be 'Pending', 'In Transit' or 'Delivered'"
#
# ── @field_validator — Custom per-field logic ────────────────────
#   @field_validator("content")
#   @classmethod
#   def validate_content(cls, v: str) -> str:
#       if not v.strip(): raise ValueError("Cannot be empty")
#       return v.strip()              → can transform the value (trim, round, etc.)
#   Runs after type validation. Raise ValueError for custom error messages.
#
#   BEGINNER EXAMPLE — @field_validator:
#
#     class Item(BaseModel):
#         content: str
#         weight: float
#
#         @field_validator("content")
#         @classmethod
#         def validate_content(cls, v):
#             if not v.strip(): raise ValueError("Cannot be empty/whitespace")
#             return v.strip().title()       # transforms: "  wooden table  " → "Wooden Table"
#
#     # How to call:
#     #   curl ... -d '{"content": "  wooden table  ", "weight": 10}'
#     #     data.content → "Wooden Table"    ← stripped + title-cased by validator
#     #
#     #   curl ... -d '{"content": "   ", "weight": 10}'
#     #     → 422! "Cannot be empty/whitespace" (custom error message)
#
# ── @model_validator — Cross-field validation ────────────────────
#   @model_validator(mode="after")    → runs after all field validators
#   def check_fields(self):           → has access to all fields via self.field_name
#       if self.weight > self.max_weight: raise ValueError(...)
#       return self                   → must return self
#   mode="before" runs on raw dict before field parsing
#
#   BEGINNER EXAMPLE — @model_validator:
#
#     class DateRange(BaseModel):
#         start_date: str
#         end_date: str
#
#         @model_validator(mode="after")
#         def check_dates(self):
#             if self.end_date < self.start_date:
#                 raise ValueError("end_date must be after start_date")
#             return self
#
#     # How to call:
#     #   curl ... -d '{"start_date": "2024-01-01", "end_date": "2024-06-01"}'
#     #     → valid (end > start)
#     #
#     #   curl ... -d '{"start_date": "2024-06-01", "end_date": "2024-01-01"}'
#     #     → 422! "end_date must be after start_date"
#     #     (cross-field check — needs BOTH fields, so model_validator not field_validator)
#
# ── Nested models — Deep structured validation ───────────────────
#   class Address(BaseModel):
#       street: str; city: str
#   class Shipment(BaseModel):
#       origin: Address               → required nested object
#       dims: Optional[Dims] = None   → optional nested object
#   Validates recursively: missing origin.city → 422 with path ["body","origin","city"]
#   Convert to dict: data.origin.model_dump()
#
#   BEGINNER EXAMPLE — Nested models:
#
#     class Address(BaseModel):
#         street: str
#         city: str
#         country: str = "US"
#
#     class Shipment(BaseModel):
#         content: str
#         origin: Address                  # required nested
#         destination: Optional[Address] = None  # optional nested
#
#     @app.post("/shipment")
#     def create(data: Shipment):
#         ...
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/shipment" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{
#     #              "content": "Electronics",
#     #              "origin": {"street": "123 Main", "city": "NYC"},
#     #              "destination": {"street": "456 Oak", "city": "London", "country": "UK"}
#     #            }'
#     #
#     #   Body structure:
#     #     {
#     #       "content": "Electronics",      ← data.content
#     #       "origin": {                    ← data.origin (Address model)
#     #         "street": "123 Main",            ← data.origin.street
#     #         "city": "NYC"                    ← data.origin.city
#     #                                          ← data.origin.country → "US" (default)
#     #       },
#     #       "destination": {               ← data.destination (optional Address)
#     #         "street": "456 Oak",
#     #         "city": "London",
#     #         "country": "UK"                  ← overrides default "US"
#     #       }
#     #     }
#     #
#     #   curl ... -d '{"content": "X", "origin": {"street": "A"}}'
#     #     → 422! origin.city is required — error path: ["body","origin","city"]
#
# ── List[Model] — Batch operations ──────────────────────────────
#   def create_batch(items: List[ShipmentItem]):
#   Request body: [{"content":"A","weight":10}, {"content":"B","weight":20}]
#   Each item validated individually. One bad item → entire batch fails 422.
#
#   BEGINNER EXAMPLE — List[Model]:
#
#     class Item(BaseModel):
#         content: str
#         weight: float = Field(gt=0)
#
#     @app.post("/batch")
#     def create_batch(items: List[Item]):
#         ...
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/batch" \
#     #        -H "Content-Type: application/json" \
#     #        -d '[
#     #              {"content": "Table", "weight": 25},
#     #              {"content": "Chair", "weight": 10}
#     #            ]'
#     #
#     #   Body: [ {...}, {...} ]       ← JSON array (NOT object!)
#     #          │        │
#     #          ▼        ▼
#     #   Inside function:
#     #     items[0].content → "Table"     ← first item
#     #     items[0].weight  → 25
#     #     items[1].content → "Chair"     ← second item
#     #     items[1].weight  → 10
#     #     len(items)       → 2
#     #
#     #   curl ... -d '[{"content": "A", "weight": 5}, {"content": "B", "weight": -1}]'
#     #     → 422! items[1].weight must be > 0 — ONE bad item fails ENTIRE batch
#
# ── response_model — Control output shape ────────────────────────
#   @app.get("/item/{id}", response_model=ItemResponse)
#   Strips fields not in ItemResponse from the response (e.g., hides internal fields)
#   Also generates response schema in Swagger docs
#
#   BEGINNER EXAMPLE — response_model:
#
#     class ShipmentResponse(BaseModel):
#         id: int
#         content: str
#         status: str
#         # NOTE: "weight" and "internal_notes" are NOT here — hidden from response
#
#     @app.get("/shipment/{id}", response_model=ShipmentResponse)
#     def get_shipment(id: int):
#         return {"id": 1, "content": "Table", "status": "Delivered",
#                 "weight": 25, "internal_notes": "fragile"}
#
#     # How to call:
#     #   curl "http://localhost:8000/shipment/1"
#     #
#     #   What function returns (internal):
#     #     {"id": 1, "content": "Table", "status": "Delivered",
#     #      "weight": 25, "internal_notes": "fragile"}
#     #
#     #   What client receives (filtered by response_model):
#     #     {"id": 1, "content": "Table", "status": "Delivered"}
#     #      ↑         ↑                  ↑
#     #      in model   in model           in model
#     #                     weight → STRIPPED (not in ShipmentResponse)
#     #                     internal_notes → STRIPPED (not in ShipmentResponse)
#
# ── model_dump() — Convert model to dict ─────────────────────────
#   data.model_dump()                 → all fields as dict
#   data.model_dump(exclude_unset=True)  → only fields explicitly set (for PATCH)
#   data.model_dump(exclude={"password"}) → exclude specific fields
#
#   BEGINNER EXAMPLE — model_dump():
#
#     class Item(BaseModel):
#         content: str
#         weight: float
#         status: str = "Pending"
#
#     data = Item(content="Table", weight=25)
#
#     # data.model_dump()
#     #   → {"content": "Table", "weight": 25.0, "status": "Pending"}
#     #      ← ALL fields including defaults
#     #
#     # data.model_dump(exclude_unset=True)
#     #   → {"content": "Table", "weight": 25.0}
#     #      ← only fields EXPLICITLY SET (status was default, so excluded)
#     #      ← useful for PATCH: only update what user actually sent
#     #
#     # data.model_dump(exclude={"weight"})
#     #   → {"content": "Table", "status": "Pending"}
#     #      ← weight explicitly excluded
#
# ── Body() + Query() + Path() with Pydantic ─────────────────────
#   def patch(id: int, dry_run: bool = Query(False), data: Model = Body()):
#   id → from URL path (auto-detected)
#   dry_run → from query string (?dry_run=true)
#   data → from JSON body (Pydantic model)
#   FastAPI can combine all three in one endpoint
#
#   BEGINNER EXAMPLE — Path + Query + Body combined:
#
#     @app.patch("/shipment/{id}")
#     def update(id: int, dry_run: bool = Query(False), data: ShipmentPatch = Body()):
#         ...
#
#     # How to call:
#     #   curl -X PATCH "http://localhost:8000/shipment/42?dry_run=true" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"status": "Delivered", "weight": 50}'
#     #
#     #   URL:  /shipment/42?dry_run=true
#     #                   │         │
#     #                   ▼         ▼
#     #     id      → 42        ← from URL path (auto: matches {id})
#     #     dry_run → True      ← from query string (?dry_run=true)
#     #
#     #   Body: {"status": "Delivered", "weight": 50}
#     #          │                      │
#     #          ▼                      ▼
#     #     data.status → "Delivered"   ← from JSON body
#     #     data.weight → 50            ← from JSON body
#     #
#     #   3 sources in 1 endpoint:
#     #     Path  → /shipment/{id}          → id
#     #     Query → ?dry_run=true           → dry_run
#     #     Body  → {"status": "Delivered"} → data (Pydantic model)
#
# ══════════════════════════════════════════════════════════════════
