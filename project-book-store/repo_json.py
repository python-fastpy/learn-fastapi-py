"""
STAGE 1 — books stored in a local JSON file.

Zero setup, no AWS account, no Docker. You can see your data by opening
books.json in an editor, which makes it a great way to learn the shape of
the app before adding cloud infrastructure.

On-disk format — a dict keyed by book id:

    {
      "a1b2c3d4": {"title": "1984", "author": "Orwell", "price": 9.99,
                   "genre": "dystopia"},
      "e5f6a7b8": {"title": "Dune",  "author": "Herbert", "price": 12.50,
                   "genre": null}
    }

READ docs/02-stage1-json-file.md for the walkthrough.
"""

import json
import os
import tempfile
import uuid
from typing import Optional

from models import Book, BookPatch, BookResponse


class JsonBookRepository:
    """Implements the BookRepository protocol on top of a JSON file.

    Strategy: read the whole file on each operation, write the whole file
    on each change. Simple and obvious — and fine for development, where
    you have a handful of records and one process.

    See the LIMITS section at the bottom of this file for exactly why
    this is not a production database.
    """

    def __init__(self, path: str = "books.json") -> None:
        self.path = path
        # Create the file on first use so every later read can assume it
        # exists. Without this, the first GET /books would crash with
        # FileNotFoundError instead of returning an empty list.
        if not os.path.exists(self.path):
            self._write_all({})

    # ── internal helpers ────────────────────────────────────────────

    def _read_all(self) -> dict[str, dict]:
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_all(self, data: dict[str, dict]) -> None:
        """Write the file ATOMICALLY: full temp file first, then rename.

        Why not just open(path, "w") and dump into it? Because that
        truncates the real file immediately. If the process dies
        mid-write (Ctrl-C, crash, disk full), books.json is left
        truncated and your data is gone.

        os.replace() is atomic on both Windows and POSIX: readers see
        either the complete old file or the complete new one, never a
        half-written one.
        """
        directory = os.path.dirname(os.path.abspath(self.path))
        fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.path)   # atomic swap
        except Exception:
            # Don't leave temp files behind if the write failed.
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    # ── BookRepository implementation ───────────────────────────────

    def list_all(self) -> list[BookResponse]:
        return [
            BookResponse(id=book_id, **fields)
            for book_id, fields in self._read_all().items()
        ]

    def get(self, book_id: str) -> Optional[BookResponse]:
        data = self._read_all()
        if book_id not in data:
            return None
        return BookResponse(id=book_id, **data[book_id])

    def create(self, book: Book) -> BookResponse:
        data = self._read_all()
        # uuid4 sliced to 8 chars: short and readable for a tutorial.
        # Production would keep the full uuid4 — 8 hex chars is only ~4
        # billion values, and birthday-collisions get likely sooner than
        # people expect. We check-and-retry to stay correct either way.
        book_id = str(uuid.uuid4())[:8]
        while book_id in data:
            book_id = str(uuid.uuid4())[:8]

        data[book_id] = book.model_dump()
        self._write_all(data)
        return BookResponse(id=book_id, **data[book_id])

    def replace(self, book_id: str, book: Book) -> Optional[BookResponse]:
        data = self._read_all()
        if book_id not in data:
            return None
        data[book_id] = book.model_dump()      # full overwrite
        self._write_all(data)
        return BookResponse(id=book_id, **data[book_id])

    def patch(self, book_id: str, changes: BookPatch) -> Optional[BookResponse]:
        data = self._read_all()
        if book_id not in data:
            return None
        # exclude_unset=True is the key to PATCH: it gives us ONLY the
        # fields the client actually sent. Without it, unsent fields
        # would come through as None and wipe existing values.
        updates = changes.model_dump(exclude_unset=True)
        data[book_id].update(updates)
        self._write_all(data)
        return BookResponse(id=book_id, **data[book_id])

    def delete(self, book_id: str) -> bool:
        data = self._read_all()
        if book_id not in data:
            return False
        del data[book_id]
        self._write_all(data)
        return True


# ── LIMITS — why this is development-only ───────────────────────────
#
# 1. NO CONCURRENT-WRITE SAFETY. Two simultaneous writes both read the
#    file, both modify their own copy, and the second write silently
#    discards the first one's change (a "lost update"). Fine with one
#    dev hitting it; broken with real traffic or multiple app instances.
#
# 2. WHOLE-FILE REWRITE ON EVERY CHANGE — O(n) per write. Adding one
#    book to a 50,000-book file rewrites all 50,000 records.
#
# 3. NO SHARED STATE ACROSS INSTANCES. On Lambda or Fargate you run many
#    containers; each would have its own local file with different data.
#    Worse, Lambda's filesystem is ephemeral — writes vanish when the
#    execution environment is recycled.
#
# 4. NO QUERYING. Want "all books by Orwell"? You load everything into
#    memory and filter in Python. A database does that with an index.
#
# Every one of these is exactly what DynamoDB fixes in stage 2
# (repo_dynamo.py). Note that the CLASS INTERFACE stays identical —
# that's the payoff of the repository pattern.
