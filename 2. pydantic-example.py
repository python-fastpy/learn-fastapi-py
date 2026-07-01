from enum import Enum
from fastapi import Body, Cookie, FastAPI, File, Form, Header, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional

app = FastAPI()

shipment_data = {
    1: {"id": 1, "content": "Shipment 1 content", "weight": 10, "status": "In Transit"},
    2: {"id": 2, "content": "Shipment 2 content", "weight": 20, "status": "Delivered"},
    3: {"id": 3, "content": "Shipment 3 content", "weight": 15, "status": "Pending"},
}


# ════════════════════════════════════════════════════
# 1. PATH PARAMETER — id is part of the URL path
#    URL: /shipment/1
# ════════════════════════════════════════════════════

@app.get("/shipment/{id}")
def get_by_path(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]
# curl http://localhost:8000/shipment/1


# ════════════════════════════════════════════════════
# 2. PATH PARAMETER with validation (Path())
#    URL: /shipment/validated/1
# ════════════════════════════════════════════════════

@app.get("/shipment/validated/{id}")
def get_by_path_validated(id: int = Path(gt=0, description="Shipment ID must be > 0")):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]
# curl http://localhost:8000/shipment/validated/1
# curl http://localhost:8000/shipment/validated/0  → 422 error (must be > 0)


# ════════════════════════════════════════════════════
# 3. QUERY PARAMETER — id passed as ?id=1
#    URL: /shipment?id=1
# ════════════════════════════════════════════════════

@app.get("/shipment")
def get_by_query(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]
# curl http://localhost:8000/shipment?id=1


# ════════════════════════════════════════════════════
# 4. QUERY PARAMETER with validation (Query())
#    URL: /shipments?status=Pending&limit=10
# ════════════════════════════════════════════════════

@app.get("/shipments")
def get_filtered(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Skip results"),
):
    results = list(shipment_data.values())
    if status:
        results = [s for s in results if s["status"] == status]
    return results[offset:offset + limit]
# curl http://localhost:8000/shipments
# curl http://localhost:8000/shipments?status=Pending
# curl http://localhost:8000/shipments?status=Delivered&limit=5
# curl "http://localhost:8000/shipments?status=In Transit&limit=2&offset=0"


# ════════════════════════════════════════════════════
# 5. REQUEST BODY with raw dict — CREATE
#    Use Body() so FastAPI reads from body, not query
# ════════════════════════════════════════════════════

@app.post("/shipment", status_code=status.HTTP_201_CREATED)
def create_shipment(data: dict = Body()):
    content = data["content"]
    weight = data["weight"]
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": content,
        "weight": weight,
        "status": data.get("status", "Pending"),
    }
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment \
#   -H "Content-Type: application/json" \
#   -d '{"content": "New shipment", "weight": 30}'
#
# curl -X POST http://localhost:8000/shipment \
#   -H "Content-Type: application/json" \
#   -d '{"content": "New shipment", "weight": 30, "status": "In Transit"}'


# ════════════════════════════════════════════════════
# 6. CREATE with query params (no body)
#    URL: /shipment/query?content=Hello&weight=10
# ════════════════════════════════════════════════════

@app.post("/shipment/query", status_code=status.HTTP_201_CREATED)
def create_via_query(
    content: str = Query(..., description="Shipment content"),
    weight: float = Query(..., description="Shipment weight"),
    shipment_status: str = Query("Pending", description="Shipment status"),
):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": content,
        "weight": weight,
        "status": shipment_status,
    }
    return shipment_data[new_id]
# curl -X POST "http://localhost:8000/shipment/query?content=New shipment&weight=30"
# curl -X POST "http://localhost:8000/shipment/query?content=New&weight=30&shipment_status=In Transit"


# ════════════════════════════════════════════════════
# 7. UPDATE (PUT) — path param + body
#    id from URL path, data from JSON body
# ════════════════════════════════════════════════════

@app.put("/shipment/{id}")
def update_shipment(id: int, data: dict = Body()):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    if "content" in data:
        shipment_data[id]["content"] = data["content"]
    if "weight" in data:
        shipment_data[id]["weight"] = data["weight"]
    if "status" in data:
        shipment_data[id]["status"] = data["status"]
    return shipment_data[id]
# curl -X PUT http://localhost:8000/shipment/1 \
#   -H "Content-Type: application/json" \
#   -d '{"status": "Delivered"}'
#
# curl -X PUT http://localhost:8000/shipment/1 \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Updated content", "weight": 50}'


# ════════════════════════════════════════════════════
# 8. PATCH — path + query + body (all three combined)
#    id from path, notify from query, data from body
# ════════════════════════════════════════════════════

@app.patch("/shipment/{id}")
def patch_shipment(
    id: int,
    notify: bool = Query(False, description="Send notification after update"),
    data: dict = Body(),
):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    if "content" in data:
        shipment_data[id]["content"] = data["content"]
    if "weight" in data:
        shipment_data[id]["weight"] = data["weight"]
    if "status" in data:
        shipment_data[id]["status"] = data["status"]
    return {"shipment": shipment_data[id], "notified": notify}
# curl -X PATCH "http://localhost:8000/shipment/1?notify=true" \
#   -H "Content-Type: application/json" \
#   -d '{"status": "Delivered"}'


# ════════════════════════════════════════════════════
# 9. DELETE — path parameter
#    URL: DELETE /shipment/1
# ════════════════════════════════════════════════════

@app.delete("/shipment/{id}")
def delete_by_path(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    deleted = shipment_data.pop(id)
    return {"message": "Deleted", "shipment": deleted}
# curl -X DELETE http://localhost:8000/shipment/1


# ════════════════════════════════════════════════════
# 10. DELETE — query parameter
#    URL: DELETE /shipment?id=2
# ════════════════════════════════════════════════════

@app.delete("/shipment")
def delete_by_query(id: int = Query(..., description="Shipment ID to delete")):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    deleted = shipment_data.pop(id)
    return {"message": "Deleted", "shipment": deleted}
# curl -X DELETE "http://localhost:8000/shipment?id=2"


# ════════════════════════════════════════════════════
# 11. MULTIPLE PATH PARAMETERS
#    URL: /warehouse/NYC/shipment/1
# ════════════════════════════════════════════════════

@app.get("/warehouse/{warehouse_id}/shipment/{shipment_id}")
def get_by_multiple_path(warehouse_id: str, shipment_id: int):
    return {
        "warehouse": warehouse_id,
        "shipment": shipment_data.get(shipment_id, "Not found"),
    }
# curl http://localhost:8000/warehouse/NYC/shipment/1
# curl http://localhost:8000/warehouse/LON/shipment/2


# ════════════════════════════════════════════════════
# 12. PATH + QUERY combined (GET)
#    id from path, fields from query to select output
#    URL: /shipment/1/details?fields=content&fields=status
# ════════════════════════════════════════════════════

@app.get("/shipment/{id}/details")
def get_with_field_filter(
    id: int,
    fields: List[str] = Query(None, description="Fields to include in response"),
):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    shipment = shipment_data[id]
    if fields:
        return {k: v for k, v in shipment.items() if k in fields}
    return shipment
# curl http://localhost:8000/shipment/1/details
# curl "http://localhost:8000/shipment/1/details?fields=content&fields=status"
# curl "http://localhost:8000/shipment/1/details?fields=weight"


# ════════════════════════════════════════════════════
# 13. LIST QUERY PARAMETER — multiple values for same key
#    URL: /shipments/batch?ids=1&ids=2&ids=3
# ════════════════════════════════════════════════════

@app.get("/shipments/batch")
def get_batch(ids: List[int] = Query(..., description="List of shipment IDs")):
    results = []
    for id in ids:
        if id in shipment_data:
            results.append(shipment_data[id])
    return results
# curl "http://localhost:8000/shipments/batch?ids=1&ids=2&ids=3"
# curl "http://localhost:8000/shipments/batch?ids=1&ids=3"


# ════════════════════════════════════════════════════
# 14. HEADER PARAMETER — read from request headers
#    Pass data via HTTP headers
# ════════════════════════════════════════════════════

@app.get("/shipment/auth/{id}")
def get_with_header(
    id: int,
    x_token: str = Header(..., description="Auth token"),
    x_request_id: Optional[str] = Header(None, description="Request tracking ID"),
):
    if x_token != "secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return {"shipment": shipment_data[id], "request_id": x_request_id}
# curl http://localhost:8000/shipment/auth/1 -H "X-Token: secret-token"
# curl http://localhost:8000/shipment/auth/1 -H "X-Token: secret-token" -H "X-Request-ID: req-123"
# curl http://localhost:8000/shipment/auth/1 -H "X-Token: wrong"  → 401


# ════════════════════════════════════════════════════
# 15. COOKIE PARAMETER — read from cookies
# ════════════════════════════════════════════════════

@app.get("/shipment/session/{id}")
def get_with_cookie(
    id: int,
    session_id: Optional[str] = Cookie(None, description="Session cookie"),
):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return {"shipment": shipment_data[id], "session": session_id}
# curl http://localhost:8000/shipment/session/1 -b "session_id=abc123"
# curl http://localhost:8000/shipment/session/1  → session will be None


# ════════════════════════════════════════════════════
# 16. FORM DATA — application/x-www-form-urlencoded
#    Like HTML form submission (not JSON)
# ════════════════════════════════════════════════════

@app.post("/shipment/form", status_code=status.HTTP_201_CREATED)
def create_via_form(
    content: str = Form(..., description="Shipment content"),
    weight: float = Form(..., description="Shipment weight"),
    shipment_status: str = Form("Pending", description="Shipment status"),
):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": content,
        "weight": weight,
        "status": shipment_status,
    }
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/form \
#   -d "content=Form shipment&weight=25"
#
# curl -X POST http://localhost:8000/shipment/form \
#   -d "content=Form shipment&weight=25&shipment_status=In Transit"


# ════════════════════════════════════════════════════
# 17. FILE UPLOAD — multipart/form-data
# ════════════════════════════════════════════════════

@app.post("/shipment/upload")
async def upload_shipment_doc(
    shipment_id: int = Query(..., description="Shipment ID"),
    file: UploadFile = File(..., description="Document to attach"),
):
    if shipment_id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    contents = await file.read()
    return {
        "shipment_id": shipment_id,
        "filename": file.filename,
        "size_bytes": len(contents),
        "content_type": file.content_type,
    }
# curl -X POST "http://localhost:8000/shipment/upload?shipment_id=1" \
#   -F "file=@document.pdf"


# ════════════════════════════════════════════════════
# 18. FILE + FORM DATA combined
# ════════════════════════════════════════════════════

@app.post("/shipment/upload-with-data")
async def upload_with_form(
    content: str = Form(...),
    weight: float = Form(...),
    file: UploadFile = File(...),
):
    file_contents = await file.read()
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": content,
        "weight": weight,
        "status": "Pending",
        "attachment": file.filename,
    }
    return {"shipment": shipment_data[new_id], "file_size": len(file_contents)}
# curl -X POST http://localhost:8000/shipment/upload-with-data \
#   -F "content=New shipment" -F "weight=30" -F "file=@doc.pdf"


# ════════════════════════════════════════════════════
# 19. MULTIPLE FILE UPLOAD
# ════════════════════════════════════════════════════

@app.post("/shipment/upload-multiple")
async def upload_multiple(
    shipment_id: int = Query(...),
    files: List[UploadFile] = File(..., description="Multiple files"),
):
    if shipment_id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    file_info = []
    for f in files:
        contents = await f.read()
        file_info.append({"filename": f.filename, "size": len(contents)})
    return {"shipment_id": shipment_id, "files": file_info}
# curl -X POST "http://localhost:8000/shipment/upload-multiple?shipment_id=1" \
#   -F "files=@file1.pdf" -F "files=@file2.pdf"


# ════════════════════════════════════════════════════
# 20. BODY with embed — single field wrapped in key
#    Body: {"data": {"content": "...", "weight": 30}}
# ════════════════════════════════════════════════════

@app.post("/shipment/embedded", status_code=status.HTTP_201_CREATED)
def create_embedded(data: dict = Body(embed=True)):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": data["content"],
        "weight": data["weight"],
        "status": data.get("status", "Pending"),
    }
    return shipment_data[new_id]
# Without embed=True: body is {"content": "...", "weight": 30}
# With embed=True:    body is {"data": {"content": "...", "weight": 30}}
#
# curl -X POST http://localhost:8000/shipment/embedded \
#   -H "Content-Type: application/json" \
#   -d '{"data": {"content": "Embedded shipment", "weight": 40}}'


# ════════════════════════════════════════════════════
# 21. MULTIPLE BODY PARAMETERS
#    Two separate dicts in body, auto-embedded by key
# ════════════════════════════════════════════════════

@app.post("/shipment/with-metadata", status_code=status.HTTP_201_CREATED)
def create_with_metadata(
    shipment: dict = Body(...),
    metadata: dict = Body(...),
):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": shipment["content"],
        "weight": shipment["weight"],
        "status": shipment.get("status", "Pending"),
        "metadata": metadata,
    }
    return shipment_data[new_id]
# Body: {"shipment": {"content": "...", "weight": 30}, "metadata": {"source": "API"}}
#
# curl -X POST http://localhost:8000/shipment/with-metadata \
#   -H "Content-Type: application/json" \
#   -d '{"shipment": {"content": "New", "weight": 30}, "metadata": {"source": "API", "priority": "high"}}'


# ════════════════════════════════════════════════════
# 22. CUSTOM RESPONSE — set headers, cookies, status
# ════════════════════════════════════════════════════

@app.post("/shipment/custom-response", status_code=status.HTTP_201_CREATED)
def create_with_custom_response(data: dict = Body()):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": data["content"],
        "weight": data["weight"],
        "status": data.get("status", "Pending"),
    }
    response = JSONResponse(
        content={"shipment": shipment_data[new_id]},
        status_code=201,
    )
    response.set_cookie(key="last_shipment_id", value=str(new_id))
    response.headers["X-Shipment-ID"] = str(new_id)
    return response
# curl -v -X POST http://localhost:8000/shipment/custom-response \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Custom response", "weight": 20}'
# Response includes Set-Cookie and X-Shipment-ID headers


# ════════════════════════════════════════════════════
# 23. PATH PARAMETER with string type + enum-like
#    URL: /shipment/status/delivered
# ════════════════════════════════════════════════════

@app.get("/shipment/status/{status_value}")
def get_by_status_path(status_value: str):
    results = [s for s in shipment_data.values() if s["status"].lower() == status_value.lower()]
    if not results:
        raise HTTPException(status_code=404, detail=f"No shipments with status '{status_value}'")
    return results
# curl http://localhost:8000/shipment/status/pending
# curl http://localhost:8000/shipment/status/delivered
# curl "http://localhost:8000/shipment/status/In Transit"  → URL-encode spaces: In%20Transit


# ════════════════════════════════════════════════════
# 24. DEFAULT VALUE vs REQUIRED — query params
# ════════════════════════════════════════════════════

@app.get("/shipments/search")
def search_shipments(
    q: str = Query(..., min_length=1, description="Required search term"),
    status_filter: Optional[str] = Query(None, description="Optional status filter"),
    sort_by: str = Query("id", description="Sort field, defaults to 'id'"),
):
    results = list(shipment_data.values())
    results = [s for s in results if q.lower() in s["content"].lower()]
    if status_filter:
        results = [s for s in results if s["status"] == status_filter]
    return {"query": q, "sort": sort_by, "results": results}
# curl "http://localhost:8000/shipments/search?q=Shipment"                          → required only
# curl "http://localhost:8000/shipments/search?q=Shipment&status_filter=Pending"    → with optional
# curl "http://localhost:8000/shipments/search?q=Shipment&sort_by=weight"           → with default override
# curl "http://localhost:8000/shipments/search"                                     → 422 (q is required)


# ════════════════════════════════════════════════════
# 25. DELETE with body (bulk delete)
# ════════════════════════════════════════════════════

@app.delete("/shipments/bulk")
def delete_bulk(data: dict = Body()):
    ids = data.get("ids", [])
    deleted = []
    not_found = []
    for id in ids:
        if id in shipment_data:
            deleted.append(shipment_data.pop(id))
        else:
            not_found.append(id)
    return {"deleted": deleted, "not_found": not_found}
# curl -X DELETE http://localhost:8000/shipments/bulk \
#   -H "Content-Type: application/json" \
#   -d '{"ids": [1, 2, 99]}'


# ╔══════════════════════════════════════════════════════════════════╗
# ║                     PYDANTIC MODELS                             ║
# ║                                                                 ║
# ║  Pydantic = automatic validation + documentation + type safety  ║
# ║                                                                 ║
# ║  dict = Body()         vs    MyModel (Pydantic)                 ║
# ║  ─────────────────          ─────────────────────               ║
# ║  No validation              Auto-validates all fields           ║
# ║  KeyError at runtime        422 error with clear message        ║
# ║  No docs in Swagger         Full schema in Swagger UI           ║
# ║  Manual data["key"]         Auto data.key (dot access)          ║
# ╚══════════════════════════════════════════════════════════════════╝


# ════════════════════════════════════════════════════
# 26. BASIC PYDANTIC MODEL — auto validation + docs
#
#  BaseModel = define what fields the body MUST have
#  - Required field:  content: str          → must be provided
#  - Optional field:  status: str = "X"     → has default value
#  - FastAPI auto-generates Swagger schema from the model
#  - Invalid data → 422 with detailed error (not 500 KeyError)
# ════════════════════════════════════════════════════

class ShipmentCreate(BaseModel):
    content: str                      # required — no default
    weight: float                     # required — no default
    status: str = "Pending"           # optional — defaults to "Pending"

@app.post("/shipment/pydantic", status_code=status.HTTP_201_CREATED)
def create_with_pydantic(data: ShipmentCreate):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": data.content,      # dot access, not data["content"]
        "weight": data.weight,
        "status": data.status,
    }
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/pydantic \
#   -H "Content-Type: application/json" \
#   -d '{"content": "New shipment", "weight": 30}'
#
# curl -X POST http://localhost:8000/shipment/pydantic \
#   -H "Content-Type: application/json" \
#   -d '{"content": "New shipment", "weight": 30, "status": "In Transit"}'
#
# MISSING FIELD → 422:
# curl -X POST http://localhost:8000/shipment/pydantic \
#   -H "Content-Type: application/json" \
#   -d '{"content": "No weight"}'
#   → {"detail":[{"loc":["body","weight"],"msg":"Field required","type":"missing"}]}
#
# WRONG TYPE → 422:
# curl -X POST http://localhost:8000/shipment/pydantic \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Bad", "weight": "not-a-number"}'
#   → {"detail":[{"loc":["body","weight"],"msg":"Input should be a valid number"}]}


# ════════════════════════════════════════════════════
# 27. PYDANTIC with Field() — add constraints + docs
#
#  Field() = like Query()/Path() but for body fields
#  - min_length, max_length  → string length
#  - gt, ge, lt, le          → number range
#  - description             → shows in Swagger docs
#  - examples                → sample values in docs
# ════════════════════════════════════════════════════

class ShipmentCreateValidated(BaseModel):
    content: str = Field(
        min_length=3,
        max_length=200,
        description="Shipment description (3-200 chars)",
        examples=["Electronics from warehouse A"],
    )
    weight: float = Field(
        gt=0,
        le=10000,
        description="Weight in kg (must be > 0, max 10000)",
        examples=[25.5],
    )
    status: str = Field(
        default="Pending",
        description="Shipment status",
        examples=["Pending", "In Transit", "Delivered"],
    )

@app.post("/shipment/pydantic-validated", status_code=status.HTTP_201_CREATED)
def create_with_field_validation(data: ShipmentCreateValidated):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": data.content,
        "weight": data.weight,
        "status": data.status,
    }
    return shipment_data[new_id]
# VALID:
# curl -X POST http://localhost:8000/shipment/pydantic-validated \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Electronics", "weight": 25.5}'
#
# TOO SHORT content → 422:
# curl -X POST http://localhost:8000/shipment/pydantic-validated \
#   -H "Content-Type: application/json" \
#   -d '{"content": "AB", "weight": 10}'
#   → "String should have at least 3 characters"
#
# NEGATIVE weight → 422:
# curl -X POST http://localhost:8000/shipment/pydantic-validated \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Test", "weight": -5}'
#   → "Input should be greater than 0"


# ════════════════════════════════════════════════════
# 28. PYDANTIC with Optional fields — for PATCH/UPDATE
#
#  Optional[str] = None  → field can be missing from body
#  Useful for partial updates where you only send
#  the fields you want to change
# ════════════════════════════════════════════════════

class ShipmentUpdate(BaseModel):
    content: Optional[str] = None     # can be missing
    weight: Optional[float] = None    # can be missing
    status: Optional[str] = None      # can be missing

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
# Update only status:
# curl -X PUT http://localhost:8000/shipment/pydantic/1 \
#   -H "Content-Type: application/json" \
#   -d '{"status": "Delivered"}'
#
# Update multiple fields:
# curl -X PUT http://localhost:8000/shipment/pydantic/1 \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Updated", "weight": 99}'
#
# Empty body (nothing changes):
# curl -X PUT http://localhost:8000/shipment/pydantic/1 \
#   -H "Content-Type: application/json" \
#   -d '{}'


# ════════════════════════════════════════════════════
# 29. PYDANTIC with Enum — restrict to allowed values
#
#  Enum = only specific values are accepted
#  Anything else → 422 with allowed values listed
# ════════════════════════════════════════════════════

class ShipmentStatus(str, Enum):
    PENDING = "Pending"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"

class ShipmentCreateWithEnum(BaseModel):
    content: str
    weight: float = Field(gt=0)
    status: ShipmentStatus = ShipmentStatus.PENDING   # only 4 values allowed

@app.post("/shipment/pydantic-enum", status_code=status.HTTP_201_CREATED)
def create_with_enum(data: ShipmentCreateWithEnum):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": data.content,
        "weight": data.weight,
        "status": data.status.value,  # .value gets the string
    }
    return shipment_data[new_id]
# VALID:
# curl -X POST http://localhost:8000/shipment/pydantic-enum \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Test", "weight": 10, "status": "In Transit"}'
#
# INVALID status → 422:
# curl -X POST http://localhost:8000/shipment/pydantic-enum \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Test", "weight": 10, "status": "Lost"}'
#   → "Input should be 'Pending', 'In Transit', 'Delivered' or 'Cancelled'"


# ════════════════════════════════════════════════════
# 30. PYDANTIC with field_validator — custom validation
#
#  @field_validator = run your own logic on a field
#  - Runs AFTER type checking
#  - Raise ValueError to reject the value
#  - Return the value (can transform it)
# ════════════════════════════════════════════════════

class ShipmentCreateCustomValidation(BaseModel):
    content: str
    weight: float
    status: str = "Pending"

    @field_validator("content")
    @classmethod
    def content_must_not_be_empty(cls, v: str) -> str:
        if v.strip() == "":
            raise ValueError("Content cannot be empty or whitespace")
        return v.strip()   # auto-trim whitespace

    @field_validator("weight")
    @classmethod
    def weight_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Weight must be greater than 0")
        if v > 50000:
            raise ValueError("Weight cannot exceed 50000 kg")
        return round(v, 2)  # auto-round to 2 decimals

    @field_validator("status")
    @classmethod
    def status_must_be_valid(cls, v: str) -> str:
        allowed = ["Pending", "In Transit", "Delivered", "Cancelled"]
        if v not in allowed:
            raise ValueError(f"Status must be one of: {allowed}")
        return v

@app.post("/shipment/pydantic-custom", status_code=status.HTTP_201_CREATED)
def create_with_custom_validation(data: ShipmentCreateCustomValidation):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": data.content,
        "weight": data.weight,
        "status": data.status,
    }
    return shipment_data[new_id]
# VALID (whitespace trimmed, weight rounded):
# curl -X POST http://localhost:8000/shipment/pydantic-custom \
#   -H "Content-Type: application/json" \
#   -d '{"content": "  Electronics  ", "weight": 25.666}'
#   → content becomes "Electronics", weight becomes 25.67
#
# EMPTY content → 422:
# curl -X POST http://localhost:8000/shipment/pydantic-custom \
#   -H "Content-Type: application/json" \
#   -d '{"content": "   ", "weight": 10}'
#   → "Content cannot be empty or whitespace"
#
# BAD weight → 422:
# curl -X POST http://localhost:8000/shipment/pydantic-custom \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Test", "weight": -5}'
#   → "Weight must be greater than 0"


# ════════════════════════════════════════════════════
# 31. PYDANTIC with model_validator — cross-field validation
#
#  @model_validator = validate multiple fields together
#  - Runs AFTER all field validators
#  - Has access to ALL fields at once
#  - Use when field A depends on field B
# ════════════════════════════════════════════════════

class ShipmentCreateCrossField(BaseModel):
    content: str
    weight: float = Field(gt=0)
    max_weight: float = Field(gt=0)
    status: str = "Pending"

    @model_validator(mode="after")
    def weight_must_not_exceed_max(self):
        if self.weight > self.max_weight:
            raise ValueError(
                f"weight ({self.weight}) cannot exceed max_weight ({self.max_weight})"
            )
        return self

@app.post("/shipment/pydantic-cross", status_code=status.HTTP_201_CREATED)
def create_with_cross_validation(data: ShipmentCreateCrossField):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": data.content,
        "weight": data.weight,
        "max_weight": data.max_weight,
        "status": data.status,
    }
    return shipment_data[new_id]
# VALID:
# curl -X POST http://localhost:8000/shipment/pydantic-cross \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Test", "weight": 20, "max_weight": 50}'
#
# weight > max_weight → 422:
# curl -X POST http://localhost:8000/shipment/pydantic-cross \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Test", "weight": 100, "max_weight": 50}'
#   → "weight (100.0) cannot exceed max_weight (50.0)"


# ════════════════════════════════════════════════════
# 32. PYDANTIC with nested models
#
#  Models inside models — for structured data
#  Each nested model is validated independently
# ════════════════════════════════════════════════════

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
    origin: Address                    # required nested model
    destination: Address               # required nested model
    dimensions: Optional[Dimensions] = None  # optional nested model

@app.post("/shipment/pydantic-nested", status_code=status.HTTP_201_CREATED)
def create_with_nested(data: ShipmentCreateNested):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id,
        "content": data.content,
        "weight": data.weight,
        "origin": data.origin.model_dump(),        # convert model → dict
        "destination": data.destination.model_dump(),
        "dimensions": data.dimensions.model_dump() if data.dimensions else None,
        "status": "Pending",
    }
    return shipment_data[new_id]
# VALID:
# curl -X POST http://localhost:8000/shipment/pydantic-nested \
#   -H "Content-Type: application/json" \
#   -d '{
#     "content": "Electronics",
#     "weight": 25,
#     "origin": {"street": "123 Main St", "city": "New York"},
#     "destination": {"street": "456 Oak Ave", "city": "London", "country": "UK"},
#     "dimensions": {"length": 10, "width": 5, "height": 3}
#   }'
#
# Without optional dimensions:
# curl -X POST http://localhost:8000/shipment/pydantic-nested \
#   -H "Content-Type: application/json" \
#   -d '{
#     "content": "Books",
#     "weight": 5,
#     "origin": {"street": "A", "city": "NYC"},
#     "destination": {"street": "B", "city": "LA"}
#   }'
#
# Missing nested required field → 422:
# curl -X POST http://localhost:8000/shipment/pydantic-nested \
#   -H "Content-Type: application/json" \
#   -d '{"content": "Test", "weight": 5, "origin": {"street": "A"}, "destination": {"street": "B", "city": "LA"}}'
#   → origin.city: "Field required"


# ════════════════════════════════════════════════════
# 33. PYDANTIC with List of models — batch create
#
#  List[Model] = accept an array of objects
#  Each item in the list is validated independently
# ════════════════════════════════════════════════════

class ShipmentItem(BaseModel):
    content: str
    weight: float = Field(gt=0)
    status: str = "Pending"

@app.post("/shipment/pydantic-batch", status_code=status.HTTP_201_CREATED)
def create_batch(items: List[ShipmentItem]):
    created = []
    for item in items:
        new_id = max(shipment_data.keys()) + 1
        shipment_data[new_id] = {
            "id": new_id,
            "content": item.content,
            "weight": item.weight,
            "status": item.status,
        }
        created.append(shipment_data[new_id])
    return {"created": len(created), "shipments": created}
# curl -X POST http://localhost:8000/shipment/pydantic-batch \
#   -H "Content-Type: application/json" \
#   -d '[
#     {"content": "Batch 1", "weight": 10},
#     {"content": "Batch 2", "weight": 20, "status": "In Transit"},
#     {"content": "Batch 3", "weight": 15}
#   ]'
#
# One invalid item fails entire batch → 422:
# curl -X POST http://localhost:8000/shipment/pydantic-batch \
#   -H "Content-Type: application/json" \
#   -d '[
#     {"content": "Good", "weight": 10},
#     {"content": "Bad", "weight": -5}
#   ]'
#   → item 1 weight: "Input should be greater than 0"


# ════════════════════════════════════════════════════
# 34. PYDANTIC as RESPONSE model — control what is returned
#
#  response_model = filter/shape the output
#  - Hides fields you don't want to expose (e.g. internal_id)
#  - Auto-documented in Swagger as response schema
# ════════════════════════════════════════════════════

class ShipmentResponse(BaseModel):
    id: int
    content: str
    weight: float
    status: str

class ShipmentDetailResponse(BaseModel):
    id: int
    content: str
    weight: float
    status: str
    internal_notes: Optional[str] = None   # only shown if present

@app.get("/shipment/pydantic-response/{id}", response_model=ShipmentResponse)
def get_with_response_model(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]
# curl http://localhost:8000/shipment/pydantic-response/1
# Even if shipment_data has extra fields (like "internal_id"),
# response_model strips them — only id, content, weight, status returned


# ════════════════════════════════════════════════════
# 35. PYDANTIC with PATH + QUERY + BODY all together
# ════════════════════════════════════════════════════

class ShipmentPatch(BaseModel):
    content: Optional[str] = None
    weight: Optional[float] = Field(None, gt=0)
    status: Optional[str] = None

@app.patch("/shipment/pydantic/{id}")
def patch_with_pydantic(
    id: int,                                           # from path
    dry_run: bool = Query(False, description="Preview without saving"),  # from query
    data: ShipmentPatch = Body(),                      # from body
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
    return {
        "shipment": shipment_data[id],
        "changes_applied": not dry_run,
        "changes": changes,
    }
# Apply changes:
# curl -X PATCH "http://localhost:8000/shipment/pydantic/1" \
#   -H "Content-Type: application/json" \
#   -d '{"status": "Delivered", "weight": 50}'
#
# Preview only (dry_run=true):
# curl -X PATCH "http://localhost:8000/shipment/pydantic/1?dry_run=true" \
#   -H "Content-Type: application/json" \
#   -d '{"status": "Cancelled"}'
#   → shows what would change, but doesn't save
