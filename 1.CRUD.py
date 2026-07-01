from fastapi import Body, Cookie, FastAPI, File, Form, Header, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import JSONResponse
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
