"""
The Book Store API — HTTP layer only.

READ THIS FIRST: nothing in this file knows whether books live in a JSON
file or in DynamoDB. It asks for a `BookRepository` and uses it. That is
why stage 1 -> stage 2 is a config change (STORAGE=dynamodb) and not a
rewrite, and why the tests can run with no AWS access at all.

Run it:
    uvicorn main:app --reload          # then open http://localhost:8000/docs

Endpoints:
    GET    /health           liveness — what AWS health checks hit
    GET    /books            list all
    GET    /books/{id}       fetch one
    POST   /books            create
    PUT    /books/{id}       full replace
    PATCH  /books/{id}       partial update
    DELETE /books/{id}       delete
"""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status

from config import Settings, get_settings
from models import Book, BookPatch, BookResponse
from repository import BookRepository, build_repository, get_repository


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build expensive, reusable resources ONCE at startup.

    The repository (and, for DynamoDB, its boto3 client) is created here
    and stored on app.state, then handed to every request by the
    get_repository dependency. Creating a boto3 client per request is a
    classic, easily-missed performance bug.

    Code after `yield` runs at shutdown — the place to close connections
    and flush buffers. Nothing to clean up here, but the structure is
    what matters: whatever you open before yield, you close after it.
    """
    settings = get_settings()
    app.state.repository = build_repository(settings)
    app.state.settings = settings
    print(f"[startup] storage={settings.storage} env={settings.env}")
    yield
    print("[shutdown] bye")


app = FastAPI(
    title="Book Store API",
    version="1.0.0",
    description="CRUD API that runs against a JSON file locally and DynamoDB on AWS.",
    lifespan=lifespan,
)


# ── health ──────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health_check(settings: Settings = Depends(get_settings)):
    """Liveness probe.

    Every AWS component we deploy checks this: the ALB target group polls
    it to decide if a container is healthy, and it's the first thing to
    curl after a deploy to confirm the app is actually up.

    Kept deliberately cheap — it does NOT touch storage. A health check
    that queries the database will fail (and get your container killed
    and replaced) during a brief DB blip, even though the app is fine.
    If you do want a dependency check, expose it separately as
    /health/ready and let the load balancer keep using this one.
    """
    return {"status": "ok", "version": "1.0.0", "storage": settings.storage,
            "env": settings.env}


# ── CRUD ────────────────────────────────────────────────────────────

@app.get("/books", response_model=list[BookResponse], tags=["books"])
def list_books(repo: BookRepository = Depends(get_repository)):
    return repo.list_all()


@app.get("/books/{book_id}", response_model=BookResponse, tags=["books"])
def get_book(book_id: str, repo: BookRepository = Depends(get_repository)):
    book = repo.get(book_id)
    # The repository returns None for "not found"; turning that into an
    # HTTP status is this layer's job, not storage's.
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return book


@app.post("/books", response_model=BookResponse,
          status_code=status.HTTP_201_CREATED, tags=["books"])
def create_book(book: Book, repo: BookRepository = Depends(get_repository)):
    """201 Created, not 200 — the correct status for "a new thing exists"."""
    return repo.create(book)


@app.put("/books/{book_id}", response_model=BookResponse, tags=["books"])
def replace_book(book_id: str, book: Book,
                 repo: BookRepository = Depends(get_repository)):
    """Full replace. Every field is required; omitted fields are NOT kept.

    PUT vs PATCH is a real interview question: PUT is idempotent and
    replaces the whole resource, PATCH merges a partial change.
    """
    updated = repo.replace(book_id, book)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return updated


@app.patch("/books/{book_id}", response_model=BookResponse, tags=["books"])
def patch_book(book_id: str, changes: BookPatch,
               repo: BookRepository = Depends(get_repository)):
    """Partial update — send only the fields you want to change."""
    updated = repo.patch(book_id, changes)
    if updated is None:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return updated


@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT,
            tags=["books"])
def delete_book(book_id: str, repo: BookRepository = Depends(get_repository)):
    """204 No Content — success, and deliberately no response body."""
    if not repo.delete(book_id):
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return None
