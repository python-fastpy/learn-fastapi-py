"""
Tests — run with NO AWS account, NO DynamoDB, NO network.

    pytest test_books.py -v

HOW THIS WORKS
──────────────
The endpoints depend on `get_repository`. In tests we override that
dependency with an in-memory fake:

    app.dependency_overrides[get_repository] = lambda: fake_repo

FastAPI then injects `fake_repo` instead of the real one. No
monkeypatching, no env juggling, no changes to main.py. This is exactly
why the repository pattern was worth the extra file.

The fake also serves as a LIVING SPEC: because it satisfies the same
BookRepository protocol, these tests verify the contract that both
repo_json.py and repo_dynamo.py must honour (404 on missing id,
PATCH merges, PUT replaces, DELETE reports whether it removed anything).
"""

import uuid
from typing import Optional

import pytest
from fastapi.testclient import TestClient

from main import app
from models import Book, BookPatch, BookResponse
from repository import BookRepository, get_repository


class FakeBookRepository:
    """In-memory BookRepository — same six methods, a plain dict inside."""

    def __init__(self) -> None:
        self._books: dict[str, dict] = {}

    def list_all(self) -> list[BookResponse]:
        return [BookResponse(id=k, **v) for k, v in self._books.items()]

    def get(self, book_id: str) -> Optional[BookResponse]:
        if book_id not in self._books:
            return None
        return BookResponse(id=book_id, **self._books[book_id])

    def create(self, book: Book) -> BookResponse:
        book_id = str(uuid.uuid4())[:8]
        self._books[book_id] = book.model_dump()
        return BookResponse(id=book_id, **self._books[book_id])

    def replace(self, book_id: str, book: Book) -> Optional[BookResponse]:
        if book_id not in self._books:
            return None
        self._books[book_id] = book.model_dump()
        return BookResponse(id=book_id, **self._books[book_id])

    def patch(self, book_id: str, changes: BookPatch) -> Optional[BookResponse]:
        if book_id not in self._books:
            return None
        self._books[book_id].update(changes.model_dump(exclude_unset=True))
        return BookResponse(id=book_id, **self._books[book_id])

    def delete(self, book_id: str) -> bool:
        return self._books.pop(book_id, None) is not None


@pytest.fixture
def client():
    """A TestClient wired to a FRESH fake repo per test.

    Fresh matters: tests that share mutable state pass or fail depending
    on execution order, which is miserable to debug.

    The cleanup after `yield` is not optional — dependency_overrides is
    a dict on the app object, so a leaked override silently affects
    every later test in the session.
    """
    fake = FakeBookRepository()
    app.dependency_overrides[get_repository] = lambda: fake
    yield TestClient(app)
    app.dependency_overrides.clear()


SAMPLE = {"title": "1984", "author": "Orwell", "price": 9.99, "genre": "dystopia"}


# ── protocol conformance ────────────────────────────────────────────

def test_fake_satisfies_the_repository_protocol():
    """Guards the contract that all three implementations share.

    runtime_checkable Protocols only check that the METHODS exist (not
    their signatures), so this is a smoke test, not a proof — but it
    catches the common mistake of renaming a method in one
    implementation and forgetting the others.
    """
    assert isinstance(FakeBookRepository(), BookRepository)


# ── health ──────────────────────────────────────────────────────────

def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── happy-path CRUD cycle ───────────────────────────────────────────

def test_create_returns_201_and_an_id(client):
    response = client.post("/books", json=SAMPLE)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "1984"
    assert body["id"]                      # server assigned one

def test_list_is_empty_then_reflects_creates(client):
    assert client.get("/books").json() == []
    client.post("/books", json=SAMPLE)
    client.post("/books", json={**SAMPLE, "title": "Animal Farm"})
    assert len(client.get("/books").json()) == 2


def test_get_returns_the_created_book(client):
    book_id = client.post("/books", json=SAMPLE).json()["id"]
    response = client.get(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["author"] == "Orwell"


def test_put_replaces_every_field(client):
    book_id = client.post("/books", json=SAMPLE).json()["id"]
    replacement = {"title": "Dune", "author": "Herbert", "price": 12.5}
    response = client.put(f"/books/{book_id}", json=replacement)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Dune"
    # genre was set to "dystopia" but the PUT payload omitted it, so a
    # full replace must drop it. This is the PUT-vs-PATCH distinction.
    assert body["genre"] is None


def test_patch_merges_and_leaves_other_fields_alone(client):
    book_id = client.post("/books", json=SAMPLE).json()["id"]
    response = client.patch(f"/books/{book_id}", json={"price": 14.99})
    assert response.status_code == 200
    body = response.json()
    assert body["price"] == 14.99
    assert body["title"] == "1984"          # untouched
    assert body["genre"] == "dystopia"      # untouched


def test_delete_returns_204_then_the_book_is_gone(client):
    book_id = client.post("/books", json=SAMPLE).json()["id"]
    assert client.delete(f"/books/{book_id}").status_code == 204
    assert client.get(f"/books/{book_id}").status_code == 404


# ── error paths (the half people forget to test) ────────────────────

@pytest.mark.parametrize(
    "method,path,payload",
    [
        ("get", "/books/nope", None),
        ("put", "/books/nope", SAMPLE),
        ("patch", "/books/nope", {"price": 1.0}),
        ("delete", "/books/nope", None),
    ],
)
def test_unknown_id_returns_404(client, method, path, payload):
    kwargs = {"json": payload} if payload is not None else {}
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == 404


def test_missing_required_field_returns_422(client):
    response = client.post("/books", json={"title": "No author or price"})
    assert response.status_code == 422
    missing = {e["loc"][-1] for e in response.json()["detail"]}
    assert {"author", "price"} <= missing


def test_negative_price_is_rejected_by_validation(client):
    """price has Field(gt=0), so Pydantic rejects this before our code runs."""
    response = client.post("/books", json={**SAMPLE, "price": -5})
    assert response.status_code == 422
