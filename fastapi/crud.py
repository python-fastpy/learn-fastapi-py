# ══════════════════════════════════════════════════════════════════
#  FastAPI CRUD — Raw Dict Patterns (No Pydantic)
#  Run: uvicorn 1.CRUD:app --reload
# ══════════════════════════════════════════════════════════════════
from fastapi import Body, Cookie, FastAPI, File, Form, Header, HTTPException, Path, Query, UploadFile, status
from fastapi.responses import JSONResponse
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

# ── 1. Path Parameter ──────────────────────────────
@app.get("/shipment/{id}")
def get_by_path(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]
# curl http://localhost:8000/shipment/1

# ── 2. Query Parameter ──────────────────────────────
@app.get("/shipment")
def get_by_query(id: int):  # auto-read from ?id=1
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]
# curl http://localhost:8000/shipment?id=1

# ── 3. Request Body (raw dict) — CREATE ──────────────────────────────
@app.post("/shipment", status_code=status.HTTP_201_CREATED)
def create_shipment(data: dict = Body()):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id, "content": data["content"],
        "weight": data["weight"], "status": data.get("status", "Pending"),
    }
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment -H "Content-Type: application/json" -d '{"content":"New","weight":30}'

# ── 4. CREATE via Query Params ──────────────────────────────
@app.post("/shipment/query", status_code=status.HTTP_201_CREATED)
def create_via_query(
    content: str = Query(...), weight: float = Query(...),
    shipment_status: str = Query("Pending"),
):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": content, "weight": weight, "status": shipment_status}
    return shipment_data[new_id]
# curl -X POST "http://localhost:8000/shipment/query?content=New&weight=30"

# ── 5. UPDATE (PUT) — path + body ──────────────────────────────
@app.put("/shipment/{id}")
def update_shipment(id: int, data: dict = Body()):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    for key in ("content", "weight", "status"):
        if key in data:
            shipment_data[id][key] = data[key]
    return shipment_data[id]
# curl -X PUT http://localhost:8000/shipment/1 -H "Content-Type: application/json" -d '{"status":"Delivered"}'

# ── 6. DELETE — path parameter ──────────────────────────────
@app.delete("/shipment/{id}")
def delete_by_path(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted", "shipment": shipment_data.pop(id)}
# curl -X DELETE http://localhost:8000/shipment/1

# ── 7. DELETE — query parameter ──────────────────────────────
@app.delete("/shipment")
def delete_by_query(id: int = Query(...)):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "Deleted", "shipment": shipment_data.pop(id)}
# curl -X DELETE "http://localhost:8000/shipment?id=2"

# ── 8. Multiple Path Parameters ──────────────────────────────
@app.get("/warehouse/{warehouse_id}/shipment/{shipment_id}")
def get_by_multiple_path(warehouse_id: str, shipment_id: int):
    return {"warehouse": warehouse_id, "shipment": shipment_data.get(shipment_id, "Not found")}
# curl http://localhost:8000/warehouse/NYC/shipment/1

# ╔══════════════════════════════════════════════════╗
# ║            INTERMEDIATE                          ║
# ╚══════════════════════════════════════════════════╝

# ── 9. Path with Validation (Path()) ──────────────────────────────
@app.get("/shipment/validated/{id}")
def get_by_path_validated(id: int = Path(gt=0, description="Must be > 0")):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]
# curl http://localhost:8000/shipment/validated/0  -> 422

# ── 10. Query with Validation (Query()) ──────────────────────────────
@app.get("/shipments")
def get_filtered(
    status: Optional[str] = Query(None), limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    results = list(shipment_data.values())
    if status:
        results = [s for s in results if s["status"] == status]
    return results[offset:offset + limit]
# curl "http://localhost:8000/shipments?status=Pending&limit=5"

# ── 11. PATCH — path + query + body combined ──────────────────────────────
@app.patch("/shipment/{id}")
def patch_shipment(id: int, notify: bool = Query(False), data: dict = Body()):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    for key in ("content", "weight", "status"):
        if key in data:
            shipment_data[id][key] = data[key]
    return {"shipment": shipment_data[id], "notified": notify}
# curl -X PATCH "http://localhost:8000/shipment/1?notify=true" -H "Content-Type: application/json" -d '{"status":"Delivered"}'

# ── 12. Path + Query — field selection ──────────────────────────────
@app.get("/shipment/{id}/details")
def get_with_field_filter(id: int, fields: List[str] = Query(None)):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    shipment = shipment_data[id]
    return {k: v for k, v in shipment.items() if k in fields} if fields else shipment
# curl "http://localhost:8000/shipment/1/details?fields=content&fields=status"

# ── 13. Required vs Optional vs Default query params ──────────────────────────────
@app.get("/shipments/search")
def search_shipments(
    q: str = Query(..., min_length=1),                     # required
    status_filter: Optional[str] = Query(None),            # optional (None)
    sort_by: str = Query("id"),                            # default value
):
    results = [s for s in shipment_data.values() if q.lower() in s["content"].lower()]
    if status_filter:
        results = [s for s in results if s["status"] == status_filter]
    return {"query": q, "sort": sort_by, "results": results}
# curl "http://localhost:8000/shipments/search?q=Shipment&status_filter=Pending"

# ── 14. Header Parameter ──────────────────────────────
@app.get("/shipment/auth/{id}")
def get_with_header(
    id: int, x_token: str = Header(...),
    x_request_id: Optional[str] = Header(None),
):
    if x_token != "secret-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return {"shipment": shipment_data[id], "request_id": x_request_id}
# curl http://localhost:8000/shipment/auth/1 -H "X-Token: secret-token"

# ── 15. Cookie Parameter ──────────────────────────────
@app.get("/shipment/session/{id}")
def get_with_cookie(id: int, session_id: Optional[str] = Cookie(None)):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return {"shipment": shipment_data[id], "session": session_id}
# curl http://localhost:8000/shipment/session/1 -b "session_id=abc123"

# ── 16. Form Data ──────────────────────────────
@app.post("/shipment/form", status_code=status.HTTP_201_CREATED)
def create_via_form(content: str = Form(...), weight: float = Form(...), shipment_status: str = Form("Pending")):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": content, "weight": weight, "status": shipment_status}
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/form -d "content=FormShipment&weight=25"

# ── 17. File Upload ──────────────────────────────
@app.post("/shipment/upload")
async def upload_shipment_doc(shipment_id: int = Query(...), file: UploadFile = File(...)):
    if shipment_id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    contents = await file.read()
    return {"shipment_id": shipment_id, "filename": file.filename, "size_bytes": len(contents)}
# curl -X POST "http://localhost:8000/shipment/upload?shipment_id=1" -F "file=@doc.pdf"

# ── 18. File + Form Data ──────────────────────────────
@app.post("/shipment/upload-with-data")
async def upload_with_form(content: str = Form(...), weight: float = Form(...), file: UploadFile = File(...)):
    file_contents = await file.read()
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": content, "weight": weight, "status": "Pending", "attachment": file.filename}
    return {"shipment": shipment_data[new_id], "file_size": len(file_contents)}
# curl -X POST http://localhost:8000/shipment/upload-with-data -F "content=New" -F "weight=30" -F "file=@doc.pdf"

# ── 19. Multiple File Upload ──────────────────────────────
@app.post("/shipment/upload-multiple")
async def upload_multiple(shipment_id: int = Query(...), files: List[UploadFile] = File(...)):
    if shipment_id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    file_info = [{"filename": f.filename, "size": len(await f.read())} for f in files]
    return {"shipment_id": shipment_id, "files": file_info}
# curl -X POST "http://localhost:8000/shipment/upload-multiple?shipment_id=1" -F "files=@a.pdf" -F "files=@b.pdf"

# ╔══════════════════════════════════════════════════╗
# ║              ADVANCED                            ║
# ╚══════════════════════════════════════════════════╝

# ── 20. Body with embed=True ──────────────────────────────
# Without embed: {"content":"...", "weight":30}
# With embed:    {"data": {"content":"...", "weight":30}}
@app.post("/shipment/embedded", status_code=status.HTTP_201_CREATED)
def create_embedded(data: dict = Body(embed=True)):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": data["content"], "weight": data["weight"], "status": data.get("status", "Pending")}
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/embedded -H "Content-Type: application/json" -d '{"data":{"content":"Embedded","weight":40}}'

# ── 21. Multiple Body Parameters ──────────────────────────────
# Body: {"shipment": {...}, "metadata": {...}} — auto-embedded by param name
@app.post("/shipment/with-metadata", status_code=status.HTTP_201_CREATED)
def create_with_metadata(shipment: dict = Body(...), metadata: dict = Body(...)):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {
        "id": new_id, "content": shipment["content"], "weight": shipment["weight"],
        "status": shipment.get("status", "Pending"), "metadata": metadata,
    }
    return shipment_data[new_id]
# curl -X POST http://localhost:8000/shipment/with-metadata -H "Content-Type: application/json" -d '{"shipment":{"content":"New","weight":30},"metadata":{"source":"API"}}'

# ── 22. Custom Response — headers, cookies, status ──────────────────────────────
@app.post("/shipment/custom-response", status_code=status.HTTP_201_CREATED)
def create_with_custom_response(data: dict = Body()):
    new_id = max(shipment_data.keys()) + 1
    shipment_data[new_id] = {"id": new_id, "content": data["content"], "weight": data["weight"], "status": data.get("status", "Pending")}
    response = JSONResponse(content={"shipment": shipment_data[new_id]}, status_code=201)
    response.set_cookie(key="last_shipment_id", value=str(new_id))
    response.headers["X-Shipment-ID"] = str(new_id)
    return response
# curl -v -X POST http://localhost:8000/shipment/custom-response -H "Content-Type: application/json" -d '{"content":"Custom","weight":20}'

# ── 23. Enum-like Path Parameter ──────────────────────────────
@app.get("/shipment/status/{status_value}")
def get_by_status_path(status_value: str):
    results = [s for s in shipment_data.values() if s["status"].lower() == status_value.lower()]
    if not results:
        raise HTTPException(status_code=404, detail=f"No shipments with status '{status_value}'")
    return results
# curl http://localhost:8000/shipment/status/pending

# ── 24. List Query Parameter — batch GET ──────────────────────────────
@app.get("/shipments/batch")
def get_batch(ids: List[int] = Query(...)):
    return [shipment_data[id] for id in ids if id in shipment_data]
# curl "http://localhost:8000/shipments/batch?ids=1&ids=2&ids=3"

# ── 25. Bulk DELETE with body ──────────────────────────────
@app.delete("/shipments/bulk")
def delete_bulk(data: dict = Body()):
    ids = data.get("ids", [])
    deleted, not_found = [], []
    for id in ids:
        (deleted if id in shipment_data else not_found).append(shipment_data.pop(id) if id in shipment_data else id)
    return {"deleted": deleted, "not_found": not_found}
# curl -X DELETE http://localhost:8000/shipments/bulk -H "Content-Type: application/json" -d '{"ids":[1,2,99]}'

# ══════════════════════════════════════════════════════════════════
#  CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
# SOURCE        | SYNTAX                          | EXAMPLE
# --------------|--------------------------------|----------------------------
# Path param    | def f(id: int)                 | /shipment/{id}
# Path valid.   | id: int = Path(gt=0)           | /shipment/validated/{id}
# Query param   | def f(id: int)                 | /shipment?id=1
# Query valid.  | limit: int = Query(10, ge=1)   | ?limit=5
# Query list    | ids: List[int] = Query(...)    | ?ids=1&ids=2
# Body (dict)   | data: dict = Body()            | JSON body
# Body embed    | data: dict = Body(embed=True)  | {"data": {...}}
# Multi body    | a: dict = Body(), b: dict = Body() | {"a":{...},"b":{...}}
# Header        | x_token: str = Header(...)     | -H "X-Token: val"
# Cookie        | sid: str = Cookie(None)        | -b "sid=abc"
# Form          | name: str = Form(...)          | -d "name=val"
# File          | file: UploadFile = File(...)    | -F "file=@f.pdf"
# Custom resp   | return JSONResponse(...)       | set cookies/headers
# ══════════════════════════════════════════════════════════════════
#
# ══════════════════════════════════════════════════════════════════
#  PARAMETER DECLARATIONS — DETAILED REFERENCE
# ══════════════════════════════════════════════════════════════════
#
# ── Body() — Reads from JSON request body ────────────────────────
#   data: dict = Body()             → optional, reads entire JSON body as dict
#   data: dict = Body(...)          → required (... = Ellipsis = no default allowed)
#   data: dict = Body(embed=True)   → expects {"data": {...}} — wraps value under param name
#   a: dict = Body(), b: dict = Body()  → multiple body params: {"a":{...},"b":{...}}
#   Note: Body() is needed to tell FastAPI "read from body" explicitly.
#         Without it, simple types (str, int) would be treated as query params.
#
#   BEGINNER EXAMPLE — Why Body() matters:
#
#     # ── CASE 1: WITHOUT Body() ─────────────────────────────────────
#     @app.post("/test")
#     def test(name: str, data: dict):
#         ...
#     # name: str   → simple type, no Body()  → FastAPI reads from QUERY string
#     # data: dict  → complex type            → FastAPI reads from JSON BODY
#     #
#     # How to call:
#     #   curl -X POST "http://localhost:8000/test?name=abc" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"key": "val"}'
#     #
#     #   URL:  /test?name=abc          ← name comes from here (query)
#     #   Body: {"key": "val"}          ← data comes from here (entire body = data)
#     #
#     #   Inside function:
#     #     name → "abc"                ← from query string
#     #     data → {"key": "val"}       ← from JSON body
#
#     # ── CASE 2: WITH Body() on all params ──────────────────────────
#     @app.post("/test")
#     def test(name: str = Body(), data: dict = Body()):
#         ...
#     # name: str = Body()  → Body() overrides → reads from JSON BODY
#     # data: dict = Body() → Body() explicit  → reads from JSON BODY
#     #
#     # How to call:
#     #   curl -X POST "http://localhost:8000/test" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"name": "abc", "data": {"key": "val"}}'
#     #
#     #   URL:  /test                   ← no query params needed
#     #   Body: {                       ← BOTH params come from body
#     #           "name": "abc",            ← name comes from here
#     #           "data": {"key": "val"}    ← data comes from here
#     #         }
#     #
#     #   Inside function:
#     #     name → "abc"                ← from body["name"]
#     #     data → {"key": "val"}       ← from body["data"]
#
#     # ── CASE 3: Single Body param (no Body()) ──────────────────────
#     @app.post("/shipment")
#     def create(data: dict = Body()):
#         ...
#     # Only ONE body param → body IS the value directly (no wrapping)
#     #
#     # How to call:
#     #   curl -X POST "http://localhost:8000/shipment" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"content": "Table", "weight": 10}'
#     #
#     #   Body: {"content": "Table", "weight": 10}   ← entire body = data
#     #
#     #   Inside function:
#     #     data → {"content": "Table", "weight": 10}  ← body itself
#
#     # ── CASE 4: Single Body param WITH embed=True ──────────────────
#     @app.post("/shipment")
#     def create(data: dict = Body(embed=True)):
#         ...
#     # embed=True → wraps under param name, even for single param
#     #
#     # How to call:
#     #   curl -X POST "http://localhost:8000/shipment" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"data": {"content": "Table", "weight": 10}}'
#     #
#     #   Body: {                                     ← wrapped under "data" key
#     #           "data": {"content": "Table", "weight": 10}
#     #         }
#     #
#     #   Inside function:
#     #     data → {"content": "Table", "weight": 10}  ← extracted from body["data"]
#
#   RULES FastAPI uses (when you DON'T add Body/Query/Path/etc.):
#     simple type (str, int, float, bool) → Query param   (?key=val)
#     complex type (dict, list, Pydantic) → Body param    (JSON)
#     name matches {name} in URL path    → Path param     (/items/{name})
#
#   Body() OVERRIDES the default → forces any type to be read from JSON body.
#   Body(...) = required  |  Body() = optional  |  Body("default") = has default
#
# ── Query() — Reads from URL query string (?key=value) ───────────
#   q: str = Query(...)                   → required, no default
#   q: str = Query(..., min_length=1)     → required + string length validation
#   status: str = Query("Pending")        → optional, defaults to "Pending"
#   status: Optional[str] = Query(None)   → optional, defaults to None
#   limit: int = Query(10, ge=1, le=100)  → default 10, must be between 1-100
#   ids: List[int] = Query(...)           → list param: ?ids=1&ids=2&ids=3
#   Validators: ge (>=), le (<=), gt (>), lt (<), min_length, max_length
#
#   BEGINNER EXAMPLE — Query():
#
#     @app.get("/search")
#     def search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=100)):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/search?q=table&limit=5"
#     #
#     #   URL:  /search?q=table&limit=5
#     #                  │        │
#     #                  ▼        ▼
#     #   Inside function:
#     #     q     → "table"     ← from ?q=table (required — omit → 422)
#     #     limit → 5           ← from ?limit=5 (optional — omit → default 10)
#     #
#     #   curl "http://localhost:8000/search"            → 422! q is required (...)
#     #   curl "http://localhost:8000/search?q=&limit=5" → 422! min_length=1 fails
#     #   curl "http://localhost:8000/search?q=x&limit=200" → 422! le=100 fails
#
#     # List query param:
#     @app.get("/filter")
#     def filter_items(ids: List[int] = Query(...)):
#         ...
#     #   curl "http://localhost:8000/filter?ids=1&ids=2&ids=3"
#     #     ids → [1, 2, 3]     ← repeated key = list
#
# ── Path() — Reads from URL path (/items/{id}) ───────────────────
#   id: int = Path(gt=0, description="Must be > 0")
#   Path params are always required (they're part of the URL).
#   Use Path() to add validation (gt, ge, lt, le) and OpenAPI docs metadata.
#
#   BEGINNER EXAMPLE — Path():
#
#     @app.get("/shipment/{id}")
#     def get_shipment(id: int = Path(gt=0, le=10000)):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/shipment/42"
#     #
#     #   URL:  /shipment/42
#     #                   │
#     #                   ▼
#     #   Inside function:
#     #     id → 42              ← from URL path segment (always required)
#     #
#     #   curl "http://localhost:8000/shipment/0"     → 422! gt=0 fails (must be > 0)
#     #   curl "http://localhost:8000/shipment/abc"   → 422! not a valid int
#     #   curl "http://localhost:8000/shipment/"      → 404! path segment missing
#
# ── Header() — Reads from HTTP headers ───────────────────────────
#   x_token: str = Header(...)              → required header
#   x_request_id: Optional[str] = Header(None)  → optional header
#   FastAPI auto-converts: x_token → "X-Token" (underscores → hyphens)
#
#   BEGINNER EXAMPLE — Header():
#
#     @app.get("/secure")
#     def secure(x_token: str = Header(...), x_request_id: Optional[str] = Header(None)):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/secure" \
#     #        -H "X-Token: my-secret-123" \
#     #        -H "X-Request-Id: req-456"
#     #
#     #   Headers:
#     #     X-Token: my-secret-123       ← x_token reads this (underscore → hyphen)
#     #     X-Request-Id: req-456        ← x_request_id reads this
#     #            │                │
#     #            ▼                ▼
#     #   Inside function:
#     #     x_token      → "my-secret-123"  ← required — omit → 422
#     #     x_request_id → "req-456"        ← optional — omit → None
#     #
#     #   curl "http://localhost:8000/secure"  → 422! X-Token header missing
#     #   NOTE: Python uses _ but HTTP headers use - (auto-converted by FastAPI)
#
# ── Cookie() — Reads from cookies ────────────────────────────────
#   session_id: Optional[str] = Cookie(None)  → optional cookie
#   Reads from the Cookie header, matches by parameter name.
#
#   BEGINNER EXAMPLE — Cookie():
#
#     @app.get("/profile")
#     def profile(session_id: Optional[str] = Cookie(None)):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/profile" -b "session_id=abc123"
#     #
#     #   Cookie header: session_id=abc123
#     #                            │
#     #                            ▼
#     #   Inside function:
#     #     session_id → "abc123"   ← from cookie (optional — no cookie → None)
#     #
#     #   curl "http://localhost:8000/profile"  → session_id = None (optional)
#     #   -b flag = --cookie = send cookie header
#
# ── Form() — Reads from form-encoded body (application/x-www-form-urlencoded) ──
#   content: str = Form(...)          → required form field
#   status: str = Form("Pending")     → optional with default
#   Used for HTML form submissions or curl -d. Cannot mix with Body().
#
#   BEGINNER EXAMPLE — Form():
#
#     @app.post("/login")
#     def login(username: str = Form(...), password: str = Form(...)):
#         ...
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/login" \
#     #        -d "username=john&password=secret123"
#     #
#     #   Form body: username=john&password=secret123
#     #              │              │
#     #              ▼              ▼
#     #   Inside function:
#     #     username → "john"         ← from form field
#     #     password → "secret123"    ← from form field
#     #
#     #   Content-Type: application/x-www-form-urlencoded  (auto-set by curl -d)
#     #   This is what HTML <form> sends by default
#     #   CANNOT mix Form() with Body() in same endpoint!
#
# ── File() — Reads uploaded files (multipart/form-data) ──────────
#   file: UploadFile = File(...)              → single file upload
#   files: List[UploadFile] = File(...)       → multiple file upload
#   UploadFile provides: .filename, .content_type, .read(), .size
#   Can mix with Form() but NOT with Body().
#
#   BEGINNER EXAMPLE — File():
#
#     @app.post("/upload")
#     def upload(file: UploadFile = File(...), description: str = Form("none")):
#         ...
#
#     # How to call (single file):
#     #   curl -X POST "http://localhost:8000/upload" \
#     #        -F "file=@report.pdf" \
#     #        -F "description=Q1 Report"
#     #
#     #   Multipart body:
#     #     file=@report.pdf            ← file upload
#     #     description=Q1 Report       ← form field alongside file
#     #        │             │
#     #        ▼             ▼
#     #   Inside function:
#     #     file.filename     → "report.pdf"
#     #     file.content_type → "application/pdf"
#     #     file.size         → 102400 (bytes)
#     #     await file.read() → b"..." (file bytes)
#     #     description       → "Q1 Report"
#     #
#     #   Multiple files:
#     #   curl -X POST "/upload-multi" -F "files=@a.pdf" -F "files=@b.pdf"
#     #     files → [UploadFile("a.pdf"), UploadFile("b.pdf")]
#     #   -F flag = --form = multipart/form-data
#     #   CAN mix File() + Form()  |  CANNOT mix File() + Body()
#
# ── Depends() — Dependency injection (see session.py) ────────────
#   user: dict = Depends(get_current_user)    → runs function, injects result
#   db: Session = Depends(get_db)             → DB session injection
#   Runs BEFORE the route handler. If dependency raises, route is skipped.
#   Can chain: dependencies can have their own Depends().
#   Can also go on decorator: @app.get("/x", dependencies=[Depends(verify)])
#
#   BEGINNER EXAMPLE — Depends():
#
#     # Step 1: Define a dependency function
#     def pagination_params(page: int = Query(1, ge=1), size: int = Query(10, ge=1, le=100)):
#         return {"page": page, "size": size, "skip": (page - 1) * size}
#
#     # Step 2: Use it in a route
#     @app.get("/items")
#     def list_items(pagination: dict = Depends(pagination_params)):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/items?page=2&size=20"
#     #
#     #   URL:  /items?page=2&size=20
#     #                │        │
#     #                ▼        ▼
#     #   Depends() runs pagination_params(page=2, size=20) FIRST
#     #     returns → {"page": 2, "size": 20, "skip": 20}
#     #                              │
#     #                              ▼
#     #   Inside route function:
#     #     pagination → {"page": 2, "size": 20, "skip": 20}  ← injected result
#     #
#     #   curl "http://localhost:8000/items"  → page=1, size=10 (defaults)
#     #   The route itself has NO query params — Depends() handles them!
#
#     # Auth dependency (chain):
#     #   @app.get("/profile")
#     #   def profile(user: dict = Depends(get_current_user)):
#     #
#     #   curl "http://localhost:8000/profile" -H "Authorization: Bearer <token>"
#     #     Depends(get_current_user) → extracts token → verifies → returns user dict
#     #     If token invalid → raises HTTPException(401) → route NEVER runs
#
# ── ... (Ellipsis) vs None vs value ──────────────────────────────
#   = Query(...)          → REQUIRED — request fails 422 without it
#   = Query(None)         → OPTIONAL — defaults to None
#   = Query("default")    → OPTIONAL — defaults to "default"
#   = Query()             → OPTIONAL — same as Query(None) for most types
#
#   BEGINNER EXAMPLE — Ellipsis (...) vs None vs default:
#
#     @app.get("/demo")
#     def demo(
#         a: str = Query(...),           # required
#         b: str = Query(None),          # optional, default None
#         c: str = Query("hello"),       # optional, default "hello"
#     ):
#         ...
#
#     # curl "http://localhost:8000/demo?a=foo"
#     #   a → "foo"     ← provided
#     #   b → None      ← not provided → default None
#     #   c → "hello"   ← not provided → default "hello"
#     #
#     # curl "http://localhost:8000/demo?a=foo&b=bar&c=world"
#     #   a → "foo"     ← provided
#     #   b → "bar"     ← provided (overrides None)
#     #   c → "world"   ← provided (overrides "hello")
#     #
#     # curl "http://localhost:8000/demo"
#     #   → 422 ERROR! "a" is required (...) and not provided
#     #
#     # COMPARISON:
#     #   ...       → "MUST send this"    → 422 if missing
#     #   None      → "send if you want"  → None if missing
#     #   "default" → "send if you want"  → "default" if missing
#     #   ()        → same as None        → None if missing
#
# ── Annotated[] style (modern, see routes.py) ────────────────────
#   Old: id: int = Path(gt=0)
#   New: id: Annotated[int, Path(gt=0)]
#   Both are equivalent. Annotated separates type hint from FastAPI metadata,
#   making it reusable and cleaner with type checkers. Recommended approach.
#
#   BEGINNER EXAMPLE — Annotated[] vs old style:
#
#     from typing import Annotated
#
#     # Old style (still works):
#     @app.get("/old/{id}")
#     def old_style(id: int = Path(gt=0), q: str = Query("default")):
#         ...
#
#     # New style (recommended):
#     @app.get("/new/{id}")
#     def new_style(id: Annotated[int, Path(gt=0)], q: Annotated[str, Query()] = "default"):
#         ...
#
#     # Both called EXACTLY the same way:
#     #   curl "http://localhost:8000/old/42?q=test"
#     #   curl "http://localhost:8000/new/42?q=test"
#     #     id → 42, q → "test"
#     #
#     # Reusable type aliases:
#     #   PositiveInt = Annotated[int, Path(gt=0)]
#     #   @app.get("/a/{id}")
#     #   def route_a(id: PositiveInt): ...    ← reuse same validation
#     #   @app.get("/b/{id}")
#     #   def route_b(id: PositiveInt): ...    ← no duplication
#
# ══════════════════════════════════════════════════════════════════
