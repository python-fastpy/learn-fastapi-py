# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FastAPI Routes — Every Way to Handle Routes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Run: uv run uvicorn routes:app --reload
# Docs: http://localhost:8000/docs
#
# Dependencies: fastapi, uvicorn (already in pyproject.toml)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from enum import Enum
from typing import Annotated

from fastapi import (
    FastAPI,
    APIRouter,
    HTTPException,
    Query,
    Path,
    Body,
    Header,
    Cookie,
    Form,
    File,
    UploadFile,
    Request,
    Response,
    Depends,
    status,
)
from fastapi.responses import (
    JSONResponse,
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    StreamingResponse,
    FileResponse,
)
from pydantic import BaseModel, Field


app = FastAPI(title="FastAPI Routes — All Approaches")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. BASIC HTTP METHODS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# FastAPI provides a decorator for every HTTP method.
# Each maps to a different operation:
#   GET    — Read data (no body)
#   POST   — Create new data (has body)
#   PUT    — Replace entire resource (has body)
#   PATCH  — Update part of resource (has body)
#   DELETE — Remove resource
#   HEAD   — Same as GET but returns only headers, no body
#   OPTIONS — Returns allowed methods for a URL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/items")
async def get_items():
    return [{"id": 1, "name": "Laptop"}, {"id": 2, "name": "Phone"}]


@app.post("/items", status_code=status.HTTP_201_CREATED)
async def create_item():
    return {"id": 3, "name": "Tablet", "created": True}


@app.put("/items/{item_id}")
async def replace_item(item_id: int):
    return {"id": item_id, "replaced": True}


@app.patch("/items/{item_id}")
async def update_item(item_id: int):
    return {"id": item_id, "updated": True}


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: int):
    return None


@app.head("/items")
async def head_items():
    return Response(headers={"X-Total-Count": "2"})


@app.options("/items")
async def options_items():
    return Response(headers={"Allow": "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS"})


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. PATH PARAMETERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Values extracted from the URL path itself.
# FastAPI auto-validates the type — if you say int, it rejects "abc".
#
# URL: /users/42          → user_id = 42
# URL: /users/abc         → 422 Validation Error (not an int)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 2a. Simple path parameter — type hint does the validation
@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return {"user_id": user_id}


# 2b. Multiple path parameters
# URL: /orgs/reuters/teams/engineering
@app.get("/orgs/{org_name}/teams/{team_name}")
async def get_team(org_name: str, team_name: str):
    return {"org": org_name, "team": team_name}


# 2c. Path() — adds validation, docs description, and constraints
# URL: /products/5   → OK
# URL: /products/0   → 422 error (ge=1 means "greater than or equal to 1")
@app.get("/products/{product_id}")
async def get_product(
    product_id: Annotated[int, Path(title="Product ID", ge=1, le=10000)],
):
    return {"product_id": product_id}


# 2d. Enum path parameter — restricts to fixed choices
# URL: /models/gpt-4o    → OK
# URL: /models/random     → 422 error
class ModelName(str, Enum):
    GPT4O = "gpt-4o"
    CLAUDE = "claude-sonnet"
    GEMINI = "gemini-pro"


@app.get("/models/{model_name}")
async def get_model(model_name: ModelName):
    return {"model": model_name, "value": model_name.value}


# 2e. Catch-all path parameter — captures slashes too
# URL: /files/docs/reports/q1.pdf → file_path = "docs/reports/q1.pdf"
@app.get("/files/{file_path:path}")
async def get_file(file_path: str):
    return {"file_path": file_path}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. QUERY PARAMETERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Values from the ?key=value part of the URL.
# Any function parameter NOT in the path is treated as a query param.
#
# URL: /search?q=fastapi&page=2&limit=20
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 3a. Simple query params — defaults make them optional
# URL: /search?q=python             → page=1, limit=10 (defaults)
# URL: /search?q=python&page=3      → page=3, limit=10
# URL: /search                      → 422 error (q is required, no default)
@app.get("/search")
async def search(q: str, page: int = 1, limit: int = 10):
    return {"query": q, "page": page, "limit": limit}


# 3b. Optional query param — None means truly optional
# URL: /articles          → tag = None
# URL: /articles?tag=tech → tag = "tech"
@app.get("/articles")
async def list_articles(tag: str | None = None):
    if tag:
        return {"articles": f"filtered by {tag}"}
    return {"articles": "all"}


# 3c. Query() — adds validation, description, aliases
# URL: /events?start=2024-01-01&end=2024-12-31&max-results=5
@app.get("/events")
async def list_events(
    start: Annotated[str, Query(description="Start date (YYYY-MM-DD)")],
    end: Annotated[str, Query(description="End date (YYYY-MM-DD)")],
    max_results: Annotated[
        int,
        Query(alias="max-results", ge=1, le=100, description="Max results to return"),
    ] = 10,
):
    return {"start": start, "end": end, "max_results": max_results}


# 3d. List query parameter — same key repeated
# URL: /filter?status=active&status=pending → status = ["active", "pending"]
@app.get("/filter")
async def filter_items(status: Annotated[list[str], Query()] = ["active"]):
    return {"statuses": status}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. REQUEST BODY (Pydantic models)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# POST/PUT/PATCH typically send JSON in the request body.
# Define a Pydantic model → FastAPI validates, parses, and documents it.
#
# curl -X POST /orders -H "Content-Type: application/json" \
#   -d '{"product": "Laptop", "quantity": 2, "price": 999.99}'
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
    notes: str | None = None


# 4a. Single body model
@app.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(order: OrderCreate):
    return OrderResponse(
        id=1,
        product=order.product,
        quantity=order.quantity,
        price=order.price,
        total=order.quantity * order.price,
        notes=order.notes,
    )


# 4b. Path param + body together
# URL: PUT /orders/1  with JSON body
@app.put("/orders/{order_id}", response_model=OrderResponse)
async def replace_order(order_id: int, order: OrderCreate):
    return OrderResponse(
        id=order_id,
        product=order.product,
        quantity=order.quantity,
        price=order.price,
        total=order.quantity * order.price,
        notes=order.notes,
    )


# 4c. Partial update model (all fields optional)
class OrderUpdate(BaseModel):
    product: str | None = None
    quantity: int | None = Field(default=None, ge=1)
    price: float | None = Field(default=None, gt=0)
    notes: str | None = None


@app.patch("/orders/{order_id}")
async def partial_update_order(order_id: int, updates: OrderUpdate):
    changed = updates.model_dump(exclude_unset=True)
    return {"id": order_id, "updated_fields": changed}


# 4d. Multiple body parameters — use Body() to embed
@app.post("/shipping")
async def create_shipping(
    order: OrderCreate,
    address: Annotated[str, Body(embed=True)],
    priority: Annotated[bool, Body(embed=True)] = False,
):
    # Request body looks like:
    # {
    #   "order": {"product": "Laptop", "quantity": 1, "price": 999},
    #   "address": "123 Main St",
    #   "priority": true
    # }
    return {"order": order.product, "address": address, "priority": priority}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. HEADERS, COOKIES, FORM DATA, FILE UPLOADS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 5a. Read request headers
# curl -H "X-Request-ID: abc123" -H "User-Agent: my-app" /headers
@app.get("/headers")
async def read_headers(
    user_agent: Annotated[str, Header()],
    x_request_id: Annotated[str | None, Header()] = None,
):
    # Note: Header names are auto-converted from hyphen to underscore
    # "X-Request-ID" → x_request_id
    return {"user_agent": user_agent, "request_id": x_request_id}


# 5b. Read cookies
# Browser sends Cookie: session_token=xyz automatically
@app.get("/cookies")
async def read_cookies(
    session_token: Annotated[str | None, Cookie()] = None,
):
    return {"session_token": session_token}


# 5c. Form data (HTML form submissions, not JSON)
# curl -X POST /login -d "username=john&password=secret"
@app.post("/login")
async def login_form(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    return {"username": username, "logged_in": True}


# 5d. File upload
# curl -X POST /upload -F "file=@photo.jpg"
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": len(contents),
    }


# 5e. Multiple file upload
@app.post("/upload-many")
async def upload_files(files: list[UploadFile] = File(...)):
    return [{"filename": f.filename, "size": f.size} for f in files]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. RESPONSE TYPES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# By default FastAPI returns JSON. You can return other formats:
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 6a. JSON (default) — just return a dict or Pydantic model
@app.get("/response/json")
async def json_response():
    return {"format": "json", "auto": True}


# 6b. Custom JSON response with status code and headers
@app.get("/response/custom-json")
async def custom_json_response():
    return JSONResponse(
        content={"message": "custom"},
        status_code=200,
        headers={"X-Custom-Header": "my-value"},
    )


# 6c. HTML response
@app.get("/response/html", response_class=HTMLResponse)
async def html_response():
    return "<h1>Hello from FastAPI</h1><p>This is HTML</p>"


# 6d. Plain text response
@app.get("/response/text", response_class=PlainTextResponse)
async def text_response():
    return "Just plain text, no JSON"


# 6e. Redirect
@app.get("/response/redirect")
async def redirect_response():
    return RedirectResponse(url="/items", status_code=302)


# 6f. Streaming response (for large data)
@app.get("/response/stream")
async def streaming_response():
    async def generate():
        for i in range(5):
            yield f"chunk {i}\n"

    return StreamingResponse(generate(), media_type="text/plain")


# 6g. Set cookies in response
@app.get("/response/set-cookie")
async def set_cookie_response(response: Response):
    response.set_cookie(key="theme", value="dark", max_age=3600, httponly=True)
    return {"message": "Cookie set"}


# 6h. Set custom headers in response
@app.get("/response/custom-headers")
async def custom_headers_response(response: Response):
    response.headers["X-Process-Time"] = "0.5s"
    response.headers["Cache-Control"] = "no-cache"
    return {"message": "Check response headers"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 7. DEPENDENCY INJECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Depends() lets you inject reusable logic into routes.
# Common uses: auth checks, DB connections, pagination, logging.
#
# The dependency function runs BEFORE the route. If it raises
# an exception, the route never executes.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 7a. Simple dependency — reusable pagination
async def pagination_params(page: int = 1, limit: int = Query(default=10, le=100)):
    return {"page": page, "limit": limit, "offset": (page - 1) * limit}


@app.get("/posts")
async def list_posts(pagination: dict = Depends(pagination_params)):
    return {"posts": [], **pagination}


@app.get("/comments")
async def list_comments(pagination: dict = Depends(pagination_params)):
    return {"comments": [], **pagination}


# 7b. Auth dependency — blocks route if unauthorized
async def verify_api_key(x_api_key: Annotated[str, Header()]):
    if x_api_key != "secret-key-123":
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


@app.get("/admin/dashboard")
async def admin_dashboard(api_key: str = Depends(verify_api_key)):
    return {"dashboard": "admin data", "authenticated_with": api_key}


# 7c. Class-based dependency
class DBSession:
    def __init__(self):
        self.connected = True

    def query(self, table: str):
        return [{"id": 1, "table": table}]


async def get_db():
    db = DBSession()
    try:
        yield db  # route uses the db
    finally:
        db.connected = False  # cleanup after route completes


@app.get("/db-demo")
async def db_demo(db: DBSession = Depends(get_db)):
    return db.query("shipments")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 8. APIRouter — ORGANIZING ROUTES INTO SEPARATE FILES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# In real apps, you split routes into routers (like Flask blueprints).
# Each router handles a domain: users, orders, auth, etc.
#
# In production you'd put each router in its own file:
#   routers/
#     users.py    → router = APIRouter(prefix="/users")
#     orders.py   → router = APIRouter(prefix="/orders")
#   main.py       → app.include_router(users.router)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 8a. Router with prefix — all routes get /api/v1/customers/...
customer_router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Customers"],  # groups them in Swagger docs
)


@customer_router.get("/")
async def list_customers():
    return [{"id": 1, "name": "Acme Corp"}, {"id": 2, "name": "Globex"}]


@customer_router.get("/{customer_id}")
async def get_customer(customer_id: int):
    return {"id": customer_id, "name": "Acme Corp"}


@customer_router.post("/", status_code=201)
async def create_customer(name: str = Body(embed=True)):
    return {"id": 3, "name": name}


# 8b. Router with shared dependencies — every route requires API key
protected_router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"],
    dependencies=[Depends(verify_api_key)],  # applied to ALL routes in this router
)


@protected_router.get("/sales")
async def sales_report():
    return {"report": "sales", "total": 50000}


@protected_router.get("/inventory")
async def inventory_report():
    return {"report": "inventory", "items": 342}


# Register routers with the app
app.include_router(customer_router)
app.include_router(protected_router)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 9. RAW REQUEST & RESPONSE ACCESS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Sometimes you need the raw Request/Response objects directly.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/raw-request")
async def raw_request(request: Request):
    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "client_ip": request.client.host if request.client else None,
        "cookies": request.cookies,
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 10. ERROR HANDLING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 10a. HTTPException — standard way to return errors
@app.get("/fail/{error_code}")
async def fail(error_code: int):
    if error_code == 404:
        raise HTTPException(status_code=404, detail="Resource not found")
    if error_code == 403:
        raise HTTPException(
            status_code=403,
            detail="Forbidden",
            headers={"X-Error": "Not allowed"},
        )
    return {"status": "ok"}


# 10b. Custom exception + handler — for domain-specific errors
class ShipmentNotFoundError(Exception):
    def __init__(self, shipment_id: int):
        self.shipment_id = shipment_id


@app.exception_handler(ShipmentNotFoundError)
async def shipment_not_found_handler(request: Request, exc: ShipmentNotFoundError):
    return JSONResponse(
        status_code=404,
        content={"error": "shipment_not_found", "shipment_id": exc.shipment_id},
    )


@app.get("/shipments-demo/{shipment_id}")
async def get_shipment_demo(shipment_id: int):
    if shipment_id > 100:
        raise ShipmentNotFoundError(shipment_id)
    return {"id": shipment_id, "status": "delivered"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 11. ASYNC vs SYNC ROUTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# async def — use for I/O-bound work (DB, HTTP calls, file reads)
#             runs on the event loop, doesn't block other requests
#
# def       — use for CPU-bound work or sync libraries
#             FastAPI runs it in a thread pool automatically
#
# Rule: if you use "await" inside, use "async def".
#       if you don't, plain "def" is fine.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Async — for I/O operations
@app.get("/async-demo")
async def async_route():
    # await some_db_call()
    # await some_http_call()
    return {"type": "async", "blocks_event_loop": False}


# Sync — FastAPI auto-wraps in threadpool
@app.get("/sync-demo")
def sync_route():
    # cpu_heavy_computation()
    # sync_library_call()
    return {"type": "sync", "runs_in": "threadpool"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 12. MULTIPLE DECORATORS — same function, multiple URLs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.api_route("/multi", methods=["GET", "POST"])
async def multi_method(request: Request):
    if request.method == "GET":
        return {"action": "reading"}
    return {"action": "creating"}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SUMMARY — Quick reference of all parameter sources
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
# Source        | How FastAPI detects it          | Example
# --------------|--------------------------------|----------------------------
# Path param    | In the URL path {name}         | /users/{id}  → id: int
# Query param   | Not in path, simple type       | ?page=2      → page: int = 1
# Request body  | Pydantic model type hint       | order: OrderCreate
# Header        | Header() annotation            | x_token: str = Header()
# Cookie        | Cookie() annotation            | session: str = Cookie()
# Form          | Form() annotation              | username: str = Form()
# File          | File() / UploadFile             | file: UploadFile = File()
# Dependency    | Depends() annotation            | db: Session = Depends(get_db)
# Raw request   | Request type hint               | request: Request
# Raw response  | Response type hint              | response: Response
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
