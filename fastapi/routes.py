# ══════════════════════════════════════════════════════════════════
# FastAPI Routes — Condensed Reference
# ══════════════════════════════════════════════════════════════════
# Run:  uv run uvicorn routes:app --reload
# Docs: http://localhost:8000/docs
# ══════════════════════════════════════════════════════════════════
from enum import Enum
from typing import Annotated
from fastapi import (
    FastAPI, APIRouter, HTTPException, Query, Path, Body,
    Header, Cookie, Form, File, UploadFile, Request, Response, Depends, status,
)
from fastapi.responses import (
    JSONResponse, HTMLResponse, PlainTextResponse, RedirectResponse, StreamingResponse,
)
from pydantic import BaseModel, Field

app = FastAPI(title="FastAPI Routes — All Approaches")

# ╔══════════════════════════════════════════════════╗
# ║                   BEGINNER                       ║
# ╚══════════════════════════════════════════════════╝

# ── 1. HTTP Methods ──────────────────────────────
# GET=read  POST=create  PUT=replace  PATCH=partial-update  DELETE=remove
# HEAD/OPTIONS also exist — rarely hand-written (FastAPI auto-generates OPTIONS)
@app.get("/items")
async def get_items():
    return [{"id": 1, "name": "Laptop"}, {"id": 2, "name": "Phone"}]

@app.post("/items", status_code=status.HTTP_201_CREATED)  # 201 for creation
async def create_item():
    return {"id": 3, "name": "Tablet", "created": True}

@app.put("/items/{item_id}")  # replace entire resource
async def replace_item(item_id: int):
    return {"id": item_id, "replaced": True}

@app.patch("/items/{item_id}")  # partial update
async def update_item(item_id: int):
    return {"id": item_id, "updated": True}

@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)  # no body
async def delete_item(item_id: int):
    return None

# ── 2. Path Parameters ──────────────────────────────
# Values from URL path. Type hint = auto-validation. /users/abc -> 422 error
@app.get("/users/{user_id}")  # simple — /users/42 -> user_id=42
async def get_user(user_id: int):
    return {"user_id": user_id}

@app.get("/orgs/{org_name}/teams/{team_name}")  # multiple params
async def get_team(org_name: str, team_name: str):
    return {"org": org_name, "team": team_name}

@app.get("/products/{product_id}")  # Path() — validation + docs
async def get_product(
    product_id: Annotated[int, Path(title="Product ID", ge=1, le=10000)],
):
    return {"product_id": product_id}

class ModelName(str, Enum):  # Enum — fixed choices (/models/random -> 422)
    GPT4O = "gpt-4o"; CLAUDE = "claude-sonnet"; GEMINI = "gemini-pro"

@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    return {"model": model_name, "value": model_name.value}

@app.get("/files/{file_path:path}")  # catch-all — captures slashes
async def get_file(file_path: str):  # /files/docs/reports/q1.pdf -> "docs/reports/q1.pdf"
    return {"file_path": file_path}

# ── 3. Query Parameters ──────────────────────────────
# From ?key=value. Any param NOT in path -> query param automatically.
@app.get("/search")  # default = optional, no default = required. /search -> 422 (q required)
async def search(q: str, page: int = 1, limit: int = 10):
    return {"query": q, "page": page, "limit": limit}

@app.get("/articles")  # None default = truly optional
async def list_articles(tag: str | None = None):
    return {"articles": f"filtered by {tag}" if tag else "all"}

@app.get("/events")  # Query() — validation, description, alias for hyphenated names
async def list_events(
    start: Annotated[str, Query(description="Start date YYYY-MM-DD")],
    end: Annotated[str, Query(description="End date YYYY-MM-DD")],
    max_results: Annotated[int, Query(alias="max-results", ge=1, le=100)] = 10,
):
    return {"start": start, "end": end, "max_results": max_results}

@app.get("/filter")  # list param — /filter?status=active&status=pending
async def filter_items(status: Annotated[list[str], Query()] = ["active"]):
    return {"statuses": status}

# ── 4. Request Body (Pydantic) ──────────────────────────────
# POST/PUT/PATCH send JSON body. Pydantic model = auto-validate + docs.
class OrderCreate(BaseModel):
    product: str = Field(min_length=1, max_length=100)
    quantity: int = Field(ge=1, le=1000)
    price: float = Field(gt=0)
    notes: str | None = None

class OrderResponse(BaseModel):
    id: int
    product: str
    quantity: int
    price: float
    total: float

@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate):  # body model; add path param for PUT /orders/{id}
    return OrderResponse(id=1, **order.model_dump(exclude={"notes"}),
                         total=order.quantity * order.price)

class OrderUpdate(BaseModel):  # partial update — all fields optional
    product: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    price: float | None = Field(default=None, gt=0)

@app.patch("/orders/{order_id}")
async def partial_update_order(order_id: int, updates: OrderUpdate):
    return {"id": order_id, "updated_fields": updates.model_dump(exclude_unset=True)}

@app.post("/shipping")  # multiple body params — Body(embed=True) nests under keys
async def create_shipping(  # body: {"order": {...}, "address": "123 Main", "priority": true}
    order: OrderCreate,
    address: Annotated[str, Body(embed=True)],
    priority: Annotated[bool, Body(embed=True)] = False,
):
    return {"order": order.product, "address": address, "priority": priority}

# ╔══════════════════════════════════════════════════╗
# ║                 INTERMEDIATE                     ║
# ╚══════════════════════════════════════════════════╝

# ── 5. Headers / Cookies / Form / File ──────────────────────────────
@app.get("/headers")  # header names auto-convert: "X-Request-ID" -> x_request_id
async def read_headers(
    user_agent: Annotated[str, Header()],
    x_request_id: Annotated[str | None, Header()] = None,
):
    return {"user_agent": user_agent, "request_id": x_request_id}

@app.get("/cookies")
async def read_cookies(session_token: Annotated[str | None, Cookie()] = None):
    return {"session_token": session_token}

@app.post("/login")  # Form data (not JSON) — curl -d "username=john&password=secret"
async def login_form(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    return {"username": username, "logged_in": True}

@app.post("/upload")  # file upload — curl -F "file=@photo.jpg"
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {"filename": file.filename, "size_bytes": len(contents)}

@app.post("/upload-many")  # multiple files
async def upload_files(files: list[UploadFile] = File(...)):
    return [{"filename": f.filename, "size": f.size} for f in files]

# ── 6. Response Types ──────────────────────────────
# Default=JSON | HTMLResponse | PlainTextResponse | RedirectResponse | StreamingResponse
@app.get("/response/json")  # default — just return dict or Pydantic model
async def json_response():
    return {"format": "json", "auto": True}  # JSONResponse(...) for custom status/headers

@app.get("/response/html", response_class=HTMLResponse)  # or PlainTextResponse for plain text
async def html_response():
    return "<h1>Hello from FastAPI</h1>"

@app.get("/response/text", response_class=PlainTextResponse)
async def text_response():
    return "Just plain text, no JSON"

@app.get("/response/redirect")  # 302 redirect
async def redirect_response():
    return RedirectResponse(url="/items", status_code=302)

@app.get("/response/stream")  # streaming for large data / SSE
async def streaming_response():
    async def generate():
        for i in range(5): yield f"chunk {i}\n"
    return StreamingResponse(generate(), media_type="text/plain")

@app.get("/response/set-cookie")  # set cookie + custom headers via Response param
async def set_cookie_response(response: Response):
    response.set_cookie(key="theme", value="dark", max_age=3600, httponly=True)
    response.headers["X-Process-Time"] = "0.5s"
    return {"message": "Cookie + header set"}

# ── 7. Dependency Injection ──────────────────────────────
# Depends() injects reusable logic. Runs BEFORE route; exception = route skipped.

async def pagination_params(page: int = 1, limit: int = Query(default=10, le=100)):  # 7a. function dep
    return {"page": page, "limit": limit, "offset": (page - 1) * limit}

@app.get("/posts")  # reuse same dep across many routes (/posts, /comments, etc.)
async def list_posts(pagination: dict = Depends(pagination_params)):
    return {"posts": [], **pagination}

async def verify_api_key(x_api_key: Annotated[str, Header()]):  # 7b. auth dep
    if x_api_key != "secret-key-123":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.get("/admin/dashboard")
async def admin_dashboard(api_key: str = Depends(verify_api_key)):
    return {"dashboard": "admin data", "authenticated_with": api_key}

class DBSession:  # 7c. yield dep — setup + cleanup
    def __init__(self): self.connected = True
    def query(self, table: str): return [{"id": 1, "table": table}]

async def get_db():
    db = DBSession()
    try: yield db                  # route uses db
    finally: db.connected = False  # cleanup after route

@app.get("/db-demo")
async def db_demo(db: DBSession = Depends(get_db)):
    return db.query("shipments")

# ╔══════════════════════════════════════════════════╗
# ║                   ADVANCED                       ║
# ╚══════════════════════════════════════════════════╝

# ── 8. APIRouter — Organize Routes ──────────────────────────────
# Like Flask blueprints. Production: routers/users.py, routers/orders.py, main.py includes them.
customer_router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])

@customer_router.get("/")
async def list_customers():
    return [{"id": 1, "name": "Acme Corp"}]

@customer_router.get("/{customer_id}")
async def get_customer(customer_id: int):
    return {"id": customer_id, "name": "Acme Corp"}

@customer_router.post("/", status_code=201)
async def create_customer(name: str = Body(embed=True)):
    return {"id": 3, "name": name}

protected_router = APIRouter(  # shared deps — every route requires API key
    prefix="/api/v1/reports", tags=["Reports"],
    dependencies=[Depends(verify_api_key)],
)

@protected_router.get("/sales")
async def sales_report():
    return {"report": "sales", "total": 50000}

app.include_router(customer_router)
app.include_router(protected_router)

# ── 9. Raw Request Access ──────────────────────────────
@app.get("/raw-request")
async def raw_request(request: Request):
    return {"method": request.method, "url": str(request.url),
            "query_params": dict(request.query_params), "headers": dict(request.headers),
            "client_ip": request.client.host if request.client else None}

# ── 10. Error Handling ──────────────────────────────
@app.get("/fail/{error_code}")  # HTTPException — standard errors
async def fail(error_code: int):
    if error_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found")
    if error_code == 403:
        raise HTTPException(status_code=403, detail="Forbidden", headers={"X-Error": "No"})
    return {"status": "ok"}

class ShipmentNotFoundError(Exception):  # custom exception + handler
    def __init__(self, shipment_id: int): self.shipment_id = shipment_id

@app.exception_handler(ShipmentNotFoundError)
async def shipment_not_found_handler(request: Request, exc: ShipmentNotFoundError):
    return JSONResponse(status_code=404,
                        content={"error": "shipment_not_found", "id": exc.shipment_id})

@app.get("/shipments-demo/{shipment_id}")
async def get_shipment_demo(shipment_id: int):
    if shipment_id > 100: raise ShipmentNotFoundError(shipment_id)
    return {"id": shipment_id, "status": "delivered"}

# ── 11. Async vs Sync ──────────────────────────────
# async def = I/O-bound (await db/http) on event loop | def = CPU-bound, auto-threadpool
@app.get("/async-demo")
async def async_route(): return {"type": "async", "blocks_event_loop": False}  # use await inside

@app.get("/sync-demo")
def sync_route(): return {"type": "sync", "runs_in": "threadpool"}  # no await needed

# ── 12. api_route — Multiple Methods ──────────────────────────────
@app.api_route("/multi", methods=["GET", "POST"])
async def multi_method(request: Request):
    return {"action": "reading" if request.method == "GET" else "creating"}

# ══════════════════════════════════════════════════════════════════
# CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
# SOURCE      | DETECTION               | EXAMPLE
# ------------|-------------------------|------------------------------------
# Path param  | {name} in URL           | /users/{id} -> id: int
# Query param | not in path, simple type| ?page=2 -> page: int = 1
# Body        | Pydantic model hint     | order: OrderCreate
# Header      | Header()                | x_tok: Annotated[str, Header()]
# Cookie      | Cookie()                | sess: Annotated[str, Cookie()]
# Form        | Form()                  | user: Annotated[str, Form()]
# File        | File() / UploadFile     | f: UploadFile = File(...)
# Dependency  | Depends()               | db = Depends(get_db)
# Raw request | Request type hint       | request: Request
#
# RESPONSE    | HOW                     | DEPS: async def()->no cleanup
# JSON default| return dict/model       |        yield->cleanup in finally
# Custom JSON | JSONResponse(...)       |        class->via yield wrapper
# HTML        | response_class=HTML...  |
# Redirect    | RedirectResponse(url=)  | ASYNC vs SYNC
# Streaming   | StreamingResponse(gen)  | async def = I/O (await), event loop
# Plain text  | response_class=Plain... | def = CPU-bound, auto-threadpool
# ══════════════════════════════════════════════════════════════════
#
# ══════════════════════════════════════════════════════════════════
#  ROUTES & ANNOTATED STYLE — DETAILED REFERENCE
# ══════════════════════════════════════════════════════════════════
#
# ── Annotated[] — Modern parameter declaration style ─────────────
#   Old style:  id: int = Path(gt=0)
#   New style:  id: Annotated[int, Path(gt=0)]
#   Both are equivalent. Annotated separates type hint from metadata.
#   Benefits: reusable (UserId = Annotated[int, Path(ge=1)]), cleaner with type checkers
#   Requires: from typing import Annotated
#
#   BEGINNER EXAMPLE — Annotated[]:
#
#     # Old style:
#     @app.get("/old/{id}")
#     def old(id: int = Path(gt=0), q: str = Query("default")):
#         ...
#     # New style (same behavior):
#     @app.get("/new/{id}")
#     def new(id: Annotated[int, Path(gt=0)], q: Annotated[str, Query()] = "default"):
#         ...
#
#     # Both called the same way:
#     #   curl "http://localhost:8000/new/42?q=test"
#     #     id → 42, q → "test"
#     #
#     # Reusable alias:
#     #   PositiveInt = Annotated[int, Path(gt=0)]
#     #   def route_a(id: PositiveInt): ...   ← reuse across routes
#
# ── Path() with Annotated ────────────────────────────────────────
#   product_id: Annotated[int, Path(title="Product ID", ge=1, le=10000)]
#   title/description → shown in Swagger docs
#   ge/le/gt/lt → numeric validation (ge=1 means >= 1)
#
#   BEGINNER EXAMPLE — Path() with Annotated:
#
#     @app.get("/product/{product_id}")
#     def get_product(product_id: Annotated[int, Path(title="Product ID", ge=1, le=10000)]):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/product/42"
#     #
#     #   URL:  /product/42
#     #                  │
#     #                  ▼
#     #   Inside function:
#     #     product_id → 42          ← from URL path, validated ge=1, le=10000
#     #
#     #   curl "http://localhost:8000/product/0"     → 422! ge=1 fails
#     #   curl "http://localhost:8000/product/99999" → 422! le=10000 fails
#
# ── Query() with Annotated ───────────────────────────────────────
#   start: Annotated[str, Query(description="Start date YYYY-MM-DD")]  → required
#   max_results: Annotated[int, Query(alias="max-results", ge=1)] = 10 → optional + alias
#   status: Annotated[list[str], Query()] = ["active"]                 → list query param
#   alias="max-results" → accept hyphenated query param names (?max-results=5)
#
#   BEGINNER EXAMPLE — Query() with Annotated + alias:
#
#     @app.get("/search")
#     def search(
#         q: Annotated[str, Query(description="Search term")],
#         max_results: Annotated[int, Query(alias="max-results", ge=1)] = 10,
#         status: Annotated[list[str], Query()] = ["active"],
#     ):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/search?q=table&max-results=5&status=active&status=pending"
#     #
#     #   URL:  /search?q=table&max-results=5&status=active&status=pending
#     #                 │        │               │             │
#     #                 ▼        ▼               └──────┬──────┘
#     #   Inside function:                              ▼
#     #     q           → "table"          ← required
#     #     max_results → 5                ← alias "max-results" → Python name max_results
#     #     status      → ["active", "pending"]  ← repeated key = list
#     #
#     #   curl "http://localhost:8000/search?q=table"
#     #     max_results → 10 (default)
#     #     status → ["active"] (default list)
#     #   NOTE: alias lets you use hyphens in URLs (?max-results) while Python uses underscores
#
# ── Body() with Annotated ────────────────────────────────────────
#   address: Annotated[str, Body(embed=True)]
#   priority: Annotated[bool, Body(embed=True)] = False
#   embed=True → wraps each param under its name: {"address":"...", "priority":true}
#   Without embed, multiple Body params auto-embed by default
#
#   BEGINNER EXAMPLE — Body() with Annotated + embed:
#
#     @app.post("/order")
#     def create(
#         address: Annotated[str, Body(embed=True)],
#         priority: Annotated[bool, Body(embed=True)] = False,
#     ):
#         ...
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/order" \
#     #        -H "Content-Type: application/json" \
#     #        -d '{"address": "123 Main St", "priority": true}'
#     #
#     #   Body: {"address": "123 Main St", "priority": true}
#     #          │                          │
#     #          ▼                          ▼
#     #   Inside function:
#     #     address  → "123 Main St"    ← from body["address"]
#     #     priority → True             ← from body["priority"]
#     #
#     #   curl ... -d '{"address": "123 Main St"}'
#     #     priority → False (default)
#
# ── Header() with Annotated ──────────────────────────────────────
#   user_agent: Annotated[str, Header()]        → reads "User-Agent" header (auto-converts _ to -)
#   x_request_id: Annotated[str | None, Header()] = None  → optional header
#
#   BEGINNER EXAMPLE — Header() with Annotated:
#
#     @app.get("/info")
#     def info(
#         user_agent: Annotated[str, Header()],
#         x_request_id: Annotated[str | None, Header()] = None,
#     ):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/info" \
#     #        -H "User-Agent: MyApp/1.0" \
#     #        -H "X-Request-Id: req-789"
#     #
#     #   Headers:
#     #     User-Agent: MyApp/1.0        ← user_agent (underscore → hyphen auto-convert)
#     #     X-Request-Id: req-789        ← x_request_id
#     #          │              │
#     #          ▼              ▼
#     #   Inside function:
#     #     user_agent   → "MyApp/1.0"   ← from User-Agent header
#     #     x_request_id → "req-789"     ← from X-Request-Id header (optional)
#
# ── Cookie() with Annotated ──────────────────────────────────────
#   session_token: Annotated[str | None, Cookie()] = None  → optional cookie
#
#   BEGINNER EXAMPLE — Cookie() with Annotated:
#
#     @app.get("/dashboard")
#     def dashboard(session_token: Annotated[str | None, Cookie()] = None):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/dashboard" -b "session_token=tok_abc123"
#     #
#     #   Cookie: session_token=tok_abc123
#     #                         │
#     #                         ▼
#     #   Inside function:
#     #     session_token → "tok_abc123"   ← from cookie (optional — None if absent)
#
# ── Form() with Annotated ───────────────────────────────────────
#   username: Annotated[str, Form()]    → reads from form-encoded body
#   Used for HTML form submissions. Cannot mix with Body() in same endpoint.
#
#   BEGINNER EXAMPLE — Form() with Annotated:
#
#     @app.post("/login")
#     def login(
#         username: Annotated[str, Form()],
#         password: Annotated[str, Form()],
#     ):
#         ...
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/login" \
#     #        -d "username=john&password=secret"
#     #
#     #   Form body: username=john&password=secret
#     #              │             │
#     #              ▼             ▼
#     #   Inside function:
#     #     username → "john"       ← from form field
#     #     password → "secret"     ← from form field
#     #   Content-Type: application/x-www-form-urlencoded (auto-set)
#
# ── File() / UploadFile ──────────────────────────────────────────
#   file: UploadFile = File(...)        → single file upload (multipart/form-data)
#   files: list[UploadFile] = File(...) → multiple files
#   UploadFile attrs: .filename, .content_type, .size, .read(), .seek()
#
#   BEGINNER EXAMPLE — File() upload:
#
#     @app.post("/upload")
#     def upload(file: UploadFile = File(...)):
#         ...
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/upload" -F "file=@photo.jpg"
#     #
#     #   Multipart: file=@photo.jpg
#     #                    │
#     #                    ▼
#     #   Inside function:
#     #     file.filename     → "photo.jpg"
#     #     file.content_type → "image/jpeg"
#     #     await file.read() → b"\xff\xd8..." (raw bytes)
#     #
#     #   Multiple files:
#     #   curl -F "files=@a.jpg" -F "files=@b.png" "http://localhost:8000/upload-multi"
#     #     files → [UploadFile("a.jpg"), UploadFile("b.png")]
#
# ── Depends() — Dependency injection ─────────────────────────────
#   pagination: dict = Depends(pagination_params)     → function dependency (reusable params)
#   api_key: str = Depends(verify_api_key)            → auth guard (raises 403 if invalid)
#   db: DBSession = Depends(get_db)                   → yield dependency (setup + cleanup)
#   dependencies=[Depends(verify_api_key)]            → route-level deps (no return value needed)
#   Yield deps: try: yield resource / finally: cleanup — runs cleanup after route finishes
#
#   BEGINNER EXAMPLE — Depends():
#
#     # Function dep (reusable params):
#     def pagination(page: int = Query(1), size: int = Query(10)):
#         return {"page": page, "size": size, "skip": (page-1)*size}
#
#     @app.get("/items")
#     def list_items(p: dict = Depends(pagination)):
#         ...
#
#     # How to call:
#     #   curl "http://localhost:8000/items?page=2&size=20"
#     #
#     #   Depends() runs pagination(page=2, size=20) FIRST
#     #     → returns {"page": 2, "size": 20, "skip": 20}
#     #                              │
#     #                              ▼
#     #     p → {"page": 2, "size": 20, "skip": 20}
#
#     # Yield dep (setup + cleanup):
#     async def get_db():
#         db = DBSession()
#         try: yield db            # ← route uses db
#         finally: db.close()      # ← cleanup AFTER route finishes
#
#     # Auth guard:
#     #   curl "http://localhost:8000/admin" -H "X-Api-Key: secret-key-123"
#     #     → Depends(verify_api_key) checks header → valid → route runs
#     #   curl "http://localhost:8000/admin" -H "X-Api-Key: wrong"
#     #     → Depends raises HTTPException(403) → route NEVER runs
#
# ── APIRouter — Organize routes into modules ─────────────────────
#   router = APIRouter(prefix="/api/v1/users", tags=["Users"])
#   @router.get("/") → becomes /api/v1/users/
#   app.include_router(router)         → register with main app
#   Like Flask blueprints. Use for: routers/users.py, routers/orders.py, etc.
#   dependencies=[Depends(...)] on router → applies to ALL routes in that router
#
#   BEGINNER EXAMPLE — APIRouter:
#
#     customer_router = APIRouter(prefix="/api/v1/customers", tags=["Customers"])
#
#     @customer_router.get("/")
#     def list_customers(): ...
#
#     @customer_router.get("/{id}")
#     def get_customer(id: int): ...
#
#     app.include_router(customer_router)
#
#     # How to call:
#     #   curl "http://localhost:8000/api/v1/customers/"
#     #     → hits list_customers()    (prefix + "/" = /api/v1/customers/)
#     #
#     #   curl "http://localhost:8000/api/v1/customers/42"
#     #     → hits get_customer(id=42) (prefix + "/{id}" = /api/v1/customers/42)
#     #
#     #   Router with shared auth:
#     #   protected = APIRouter(prefix="/admin", dependencies=[Depends(verify_api_key)])
#     #     → EVERY route in this router requires API key — no need to add Depends per route
#
# ── Response types ───────────────────────────────────────────────
#   return dict/model                  → auto-JSONResponse (default)
#   JSONResponse(content={}, status_code=201)  → custom status/headers
#   HTMLResponse("<h1>Hi</h1>")        → HTML content
#   PlainTextResponse("text")          → plain text
#   RedirectResponse(url="/other", status_code=302) → redirect
#   StreamingResponse(generator, media_type="text/plain") → streaming/SSE
#   response.set_cookie(key, value, httponly=True) → set cookie via Response param
#
#   BEGINNER EXAMPLE — Response types:
#
#     # Default JSON:
#     @app.get("/json")
#     def get_json(): return {"msg": "hello"}
#     #   curl "http://localhost:8000/json"
#     #     → {"msg": "hello"}  (Content-Type: application/json — auto)
#
#     # Custom status:
#     @app.post("/create")
#     def create(): return JSONResponse(content={"id": 1}, status_code=201)
#     #   curl -X POST "http://localhost:8000/create"
#     #     → 201 Created, {"id": 1}
#
#     # HTML:
#     @app.get("/page", response_class=HTMLResponse)
#     def page(): return "<h1>Hello</h1>"
#     #   curl "http://localhost:8000/page"
#     #     → <h1>Hello</h1>  (Content-Type: text/html)
#
#     # Redirect:
#     @app.get("/old")
#     def old(): return RedirectResponse(url="/new", status_code=301)
#     #   curl -L "http://localhost:8000/old"
#     #     → follows redirect to /new
#
# ── Error handling ───────────────────────────────────────────────
#   raise HTTPException(status_code=404, detail="Not found")  → standard error
#   raise HTTPException(status_code=403, headers={"X-Error": "No"}) → with custom headers
#   @app.exception_handler(CustomError)   → custom exception → custom JSON response
#   Custom exception class + handler → clean API error format
#
#   BEGINNER EXAMPLE — Error handling:
#
#     # Standard HTTPException:
#     @app.get("/item/{id}")
#     def get_item(id: int):
#         if id > 100: raise HTTPException(status_code=404, detail="Not found")
#         return {"id": id}
#
#     #   curl "http://localhost:8000/item/1"    → {"id": 1}
#     #   curl "http://localhost:8000/item/999"  → 404: {"detail": "Not found"}
#
#     # Custom exception + handler:
#     class ItemNotFound(Exception):
#         def __init__(self, item_id): self.item_id = item_id
#
#     @app.exception_handler(ItemNotFound)
#     def handle(request, exc):
#         return JSONResponse(status_code=404, content={"error": "item_not_found", "id": exc.item_id})
#
#     #   raise ItemNotFound(42) → {"error": "item_not_found", "id": 42}
#
# ── Enum path parameters ────────────────────────────────────────
#   class ModelName(str, Enum):
#       GPT4O = "gpt-4o"
#   def route(model: ModelName):       → invalid value → 422 auto-error
#
#   BEGINNER EXAMPLE — Enum path:
#
#     class ModelName(str, Enum):
#         GPT4O = "gpt-4o"
#         CLAUDE = "claude-3.5"
#
#     @app.get("/models/{model}")
#     def get_model(model: ModelName):
#         ...
#
#     #   curl "http://localhost:8000/models/gpt-4o"     → model → ModelName.GPT4O
#     #   curl "http://localhost:8000/models/invalid"    → 422! not a valid enum value
#
# ── Catch-all path ──────────────────────────────────────────────
#   @app.get("/files/{file_path:path}")
#   → captures slashes: /files/docs/reports/q1.pdf → file_path="docs/reports/q1.pdf"
#
#   BEGINNER EXAMPLE — Catch-all :path:
#
#     @app.get("/files/{file_path:path}")
#     def get_file(file_path: str):
#         ...
#
#     #   curl "http://localhost:8000/files/docs/reports/q1.pdf"
#     #
#     #   URL:  /files/docs/reports/q1.pdf
#     #                │
#     #                ▼
#     #     file_path → "docs/reports/q1.pdf"  ← captures everything including slashes
#     #   Normal {param} would stop at first / — :path captures the full nested path
#
# ── api_route — Multiple HTTP methods on same path ──────────────
#   @app.api_route("/multi", methods=["GET", "POST"])
#   → request.method to distinguish: "GET" vs "POST"
#
#   BEGINNER EXAMPLE — api_route:
#
#     @app.api_route("/resource", methods=["GET", "POST"])
#     async def resource(request: Request):
#         if request.method == "GET": return {"action": "reading"}
#         else: return {"action": "creating"}
#
#     #   curl "http://localhost:8000/resource"            → {"action": "reading"}
#     #   curl -X POST "http://localhost:8000/resource"    → {"action": "creating"}
#     #   Same path, different behavior based on HTTP method
#
# ── Raw Request access ──────────────────────────────────────────
#   request: Request                   → full access to method, url, headers, cookies, client IP
#   dict(request.query_params)         → all query params as dict
#   dict(request.headers)              → all headers as dict
#   request.client.host                → client IP address
#
#   BEGINNER EXAMPLE — Raw Request:
#
#     @app.get("/debug")
#     async def debug(request: Request):
#         return {
#             "method": request.method,
#             "url": str(request.url),
#             "headers": dict(request.headers),
#             "client_ip": request.client.host,
#         }
#
#     #   curl "http://localhost:8000/debug?foo=bar" -H "X-Custom: hello"
#     #
#     #   Inside function:
#     #     request.method           → "GET"
#     #     request.url              → "http://localhost:8000/debug?foo=bar"
#     #     request.query_params     → {"foo": "bar"}
#     #     request.headers["x-custom"] → "hello"
#     #     request.client.host      → "127.0.0.1"
#
# ══════════════════════════════════════════════════════════════════
