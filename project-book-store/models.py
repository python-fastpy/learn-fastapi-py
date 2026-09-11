"""
Pydantic models for the Book Store API.

These NEVER change across the whole project — not when we swap the JSON
file for DynamoDB, and not when we deploy to Lambda or Fargate.
That is deliberate: the API contract is independent of storage.
"""

from typing import Optional

from pydantic import BaseModel, Field


class Book(BaseModel):
    """Full book payload — used for POST (create) and PUT (replace)."""

    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Must be greater than 0")
    genre: Optional[str] = None


class BookPatch(BaseModel):
    """Partial payload — used for PATCH. Every field optional.

    Why a separate model? With PATCH the client sends ONLY the fields it
    wants changed. If we reused `Book`, FastAPI would reject a request
    that omitted `title`, because `Book.title` is required.
    """

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    author: Optional[str] = Field(default=None, min_length=1, max_length=100)
    price: Optional[float] = Field(default=None, gt=0)
    genre: Optional[str] = None


class BookResponse(Book):
    """What we send back — the book plus its server-assigned id."""

    id: str
