"""The app. No AI, no MCP -- just four plain functions and a list.

This is "the simple app" every step in this project builds on top of.
Steps 2 and 3 never change these functions -- only how something ELSE (an
AI assistant, then an MCP server) reaches them changes. That's the whole
point of this project: adding AI/MCP to an app is an ADDITIVE layer, not
a rewrite.
"""

BOOKS: list[dict] = []
_next_id = 1


def add_book(title: str, author: str) -> dict:
    """Add a book to the reading list. Starts with status 'to_read'."""
    global _next_id
    book = {"id": _next_id, "title": title, "author": author, "status": "to_read"}
    BOOKS.append(book)
    _next_id += 1
    return book


def list_books(status: str | None = None) -> list[dict]:
    """List books, optionally filtered by status (to_read / reading / read)."""
    if status is None:
        return list(BOOKS)
    return [b for b in BOOKS if b["status"] == status]


def mark_status(book_id: int, status: str) -> dict:
    """Change a book's status to to_read, reading, or read."""
    for b in BOOKS:
        if b["id"] == book_id:
            b["status"] = status
            return b
    raise ValueError(f"no book with id {book_id}")


def remove_book(book_id: int) -> dict:
    """Remove a book from the list entirely."""
    for i, b in enumerate(BOOKS):
        if b["id"] == book_id:
            return BOOKS.pop(i)
    raise ValueError(f"no book with id {book_id}")
