"""
The repository interface — THE most important file in this project.

WHY THIS EXISTS
───────────────
Without it, every endpoint in main.py would contain storage code:

    @app.get("/books")
    def list_books():
        with open("books.json") as f:      # <-- storage detail leaks
            return json.load(f)             #     into the HTTP layer

Then migrating to DynamoDB means rewriting EVERY endpoint, and you can't
test without touching real storage.

With it, endpoints depend on an *interface*. Swapping JSON for DynamoDB
becomes a config change (STORAGE=dynamodb), not a rewrite. Tests inject
a fake. Same idea as an "interface" in Java/C# or a "trait" in Rust.

    main.py  ──depends on──▶  BookRepository (this file, abstract)
                                      ▲
                        ┌─────────────┴─────────────┐
              JsonBookRepository            DynamoBookRepository
              (repo_json.py)                (repo_dynamo.py)
"""

from typing import Optional, Protocol, runtime_checkable

from fastapi import Depends, Request

from config import Settings, get_settings
from models import Book, BookPatch, BookResponse


@runtime_checkable
class BookRepository(Protocol):
    """What ANY storage backend must be able to do.

    We use typing.Protocol (structural typing) rather than an ABC base
    class: an implementation just needs these methods with these
    signatures — it does not have to inherit from anything. Less
    coupling, and it still type-checks.
    """

    def list_all(self) -> list[BookResponse]:
        """Return every book. Empty list if there are none."""
        ...

    def get(self, book_id: str) -> Optional[BookResponse]:
        """Return one book, or None if that id doesn't exist.

        NOTE: returns None rather than raising. Deciding that "not found"
        means HTTP 404 is the API layer's job, not storage's — this keeps
        the repository reusable outside a web app (CLI, worker, etc).
        """
        ...

    def create(self, book: Book) -> BookResponse:
        """Store a new book under a freshly generated id."""
        ...

    def replace(self, book_id: str, book: Book) -> Optional[BookResponse]:
        """Full overwrite (PUT). None if the id doesn't exist."""
        ...

    def patch(self, book_id: str, changes: BookPatch) -> Optional[BookResponse]:
        """Partial update (PATCH). None if the id doesn't exist."""
        ...

    def delete(self, book_id: str) -> bool:
        """True if something was deleted, False if the id wasn't found."""
        ...


def build_repository(settings: Settings) -> BookRepository:
    """Pick an implementation based on config. The ONLY place that chooses.

    Imports are done INSIDE each branch on purpose: running locally with
    STORAGE=json then never imports boto3, so you don't need boto3
    installed (or AWS credentials configured) just to try stage 1.
    """
    if settings.storage == "json":
        from repo_json import JsonBookRepository

        return JsonBookRepository(settings.books_file)

    if settings.storage == "dynamodb":
        from repo_dynamo import DynamoBookRepository

        return DynamoBookRepository(
            table_name=settings.table_name,
            region=settings.aws_region,
            endpoint_url=settings.dynamodb_endpoint_url or None,
        )

    # Unreachable: config.py's Literal[...] already rejects bad values at
    # startup. Kept so a future backend added to the Literal but not here
    # fails loudly instead of silently returning None.
    raise ValueError(f"Unknown STORAGE backend: {settings.storage!r}")


def get_repository(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> BookRepository:
    """FastAPI dependency that hands endpoints a ready repository.

    Reuses the single instance created in main.py's lifespan (stored on
    app.state) so we don't rebuild a boto3 client on every request —
    creating one per request is a real, common performance bug.

    If the lifespan never ran, we build the repository once and CACHE it
    on app.state, so subsequent requests reuse it. This matters on
    Lambda, where we run Mangum with lifespan="off" (see
    lambda_handler.py): without caching here, every invocation would
    construct a fresh boto3 client.
    """
    repo = getattr(request.app.state, "repository", None)
    if repo is None:
        repo = build_repository(settings)
        request.app.state.repository = repo   # build once, reuse after
    return repo
