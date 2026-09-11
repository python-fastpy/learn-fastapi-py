"""
STAGE 2 — books stored in DynamoDB.

Compare this file to repo_json.py: SAME six methods, same signatures,
same return types. main.py does not change at all. That is the entire
point of the repository pattern.

TABLE DESIGN (deliberately the simplest thing that works)

    Table: book-store-books
    Partition key: book_id (String)   ← no sort key

    ┌──────────────────────────────────────────────────────────────┐
    │ book_id (PK) │ title │ author  │ price │ genre               │
    ├──────────────────────────────────────────────────────────────┤
    │ a1b2c3d4     │ 1984  │ Orwell  │ 9.99  │ dystopia            │
    │ e5f6a7b8     │ Dune  │ Herbert │ 12.50 │ (absent)            │
    └──────────────────────────────────────────────────────────────┘

  Why a bare partition key with no sort key? Because every access here
  is "give me the book with this exact id". A sort key earns its
  complexity only when you need to store multiple related items under
  one partition (e.g. a book AND its reviews) or query ranges.

  DynamoDB is schemaless per-item: the `genre: None` book simply has no
  `genre` attribute stored at all, rather than a NULL column.

READ docs/03-stage2-dynamodb.md for the walkthrough (incl. DynamoDB
Local, so you can run this with no AWS account).
"""

import uuid
from decimal import Decimal
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

from models import Book, BookPatch, BookResponse

# DynamoDB reserved words can't be used bare in expressions. `year` is the
# classic trap; we don't use it here, but `name`, `status`, `size`, and
# `value` are all reserved too. The fix is ExpressionAttributeNames —
# see the #placeholder pattern in patch() below, which we apply to EVERY
# attribute so you never have to remember the reserved list.


def _to_dynamo(value: Any) -> Any:
    """Convert Python types into what DynamoDB accepts.

    THE classic DynamoDB gotcha: it has no float type. boto3 raises
    `TypeError: Float types are not supported` if you hand it a float.
    Everything numeric must be a Decimal.

    We go through str() rather than Decimal(float) on purpose:
        Decimal(9.99)      -> 9.9900000000000002131628...  (binary float noise)
        Decimal(str(9.99)) -> 9.99                          (what you meant)
    """
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: _to_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_dynamo(v) for v in value]
    return value


def _from_dynamo(value: Any) -> Any:
    """Convert DynamoDB types back into plain Python.

    Decimals coming out would otherwise leak into our Pydantic models
    and JSON responses. Pydantic would coerce them, but json.dumps on a
    raw Decimal raises TypeError — so we normalise here, at the boundary.
    """
    if isinstance(value, Decimal):
        # int if it's a whole number (3 not 3.0), else float.
        return int(value) if value % 1 == 0 else float(value)
    if isinstance(value, dict):
        return {k: _from_dynamo(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_from_dynamo(v) for v in value]
    return value


class DynamoBookRepository:
    """Implements the BookRepository protocol on top of a DynamoDB table."""

    def __init__(
        self,
        table_name: str = "book-store-books",
        region: str = "us-east-1",
        endpoint_url: Optional[str] = None,
    ) -> None:
        # Created ONCE and reused for the lifetime of the process.
        # Creating a boto3 resource per request is a common performance
        # bug: each one re-resolves credentials and opens new TLS
        # connections. main.py builds this in the lifespan handler.
        #
        # No credentials are passed here on purpose. boto3 finds them
        # automatically: env vars locally, and the IAM role attached to
        # the Lambda function / ECS task when deployed. Never hardcode
        # access keys.
        self._dynamodb = boto3.resource(
            "dynamodb",
            region_name=region,
            endpoint_url=endpoint_url,   # None = real AWS; set for DynamoDB Local
        )
        self.table = self._dynamodb.Table(table_name)
        self.table_name = table_name

    # ── BookRepository implementation ───────────────────────────────

    def list_all(self) -> list[BookResponse]:
        """Return every book.

        Uses Scan, which reads EVERY item in the table. That is
        acceptable here (a demo table) but is the operation you should
        be most suspicious of in real systems:

          Scan  — reads the whole table, cost grows with total size
          Query — reads only one partition, cost grows with matches

        If "list all books" needed to scale, you would restructure so it
        becomes a Query (e.g. partition by genre and query one genre), or
        keep a separate index. Also note Scan returns at most 1 MB per
        call — we page through LastEvaluatedKey so nothing is silently
        dropped, which is an easy bug to ship.
        """
        books: list[BookResponse] = []
        kwargs: dict[str, Any] = {}
        while True:
            response = self.table.scan(**kwargs)
            for item in response.get("Items", []):
                books.append(self._item_to_response(item))
            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            kwargs["ExclusiveStartKey"] = last_key
        return books

    def get(self, book_id: str) -> Optional[BookResponse]:
        """Fetch one book by primary key — the cheapest DynamoDB read."""
        response = self.table.get_item(Key={"book_id": book_id})
        item = response.get("Item")     # absent key => no "Item" at all
        if item is None:
            return None
        return self._item_to_response(item)

    def create(self, book: Book) -> BookResponse:
        book_id = str(uuid.uuid4())[:8]
        item = {"book_id": book_id, **book.model_dump()}

        # Drop None values: DynamoDB can store null, but omitting the
        # attribute entirely is the idiomatic "no value" and keeps items
        # smaller (you pay per byte).
        item = {k: v for k, v in item.items() if v is not None}

        self.table.put_item(
            Item=_to_dynamo(item),
            # Guard against overwriting an existing id. Without this,
            # put_item silently REPLACES any item with the same key —
            # a uuid collision would destroy a real book.
            ConditionExpression="attribute_not_exists(book_id)",
        )
        return BookResponse(id=book_id, **book.model_dump())

    def replace(self, book_id: str, book: Book) -> Optional[BookResponse]:
        """Full overwrite (PUT), but only if the id already exists."""
        item = {"book_id": book_id, **book.model_dump()}
        item = {k: v for k, v in item.items() if v is not None}
        try:
            self.table.put_item(
                Item=_to_dynamo(item),
                # PUT must not CREATE. Without this condition, replacing
                # a non-existent id would quietly insert a new book and
                # we'd wrongly return 200 instead of 404.
                ConditionExpression="attribute_exists(book_id)",
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None          # didn't exist -> caller sends 404
            raise
        return BookResponse(id=book_id, **book.model_dump())

    def patch(self, book_id: str, changes: BookPatch) -> Optional[BookResponse]:
        """Partial update (PATCH) via an UpdateExpression.

        Unlike the JSON backend, we do NOT read-then-write here.
        update_item changes only the named attributes server-side, which
        avoids the lost-update race that repo_json.py suffers from.
        """
        updates = changes.model_dump(exclude_unset=True)
        if not updates:
            # Nothing to change — just return current state (or 404).
            return self.get(book_id)

        # Build "SET #title = :title, #price = :price" dynamically.
        # Every attribute goes through a #placeholder so reserved words
        # (name, status, size, year, ...) can never break the expression.
        set_parts = []
        expr_names: dict[str, str] = {}
        expr_values: dict[str, Any] = {}
        for field, value in updates.items():
            set_parts.append(f"#{field} = :{field}")
            expr_names[f"#{field}"] = field
            expr_values[f":{field}"] = _to_dynamo(value)

        try:
            response = self.table.update_item(
                Key={"book_id": book_id},
                UpdateExpression="SET " + ", ".join(set_parts),
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
                ConditionExpression="attribute_exists(book_id)",
                ReturnValues="ALL_NEW",   # give us the full updated item back
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return None
            raise
        return self._item_to_response(response["Attributes"])

    def delete(self, book_id: str) -> bool:
        try:
            self.table.delete_item(
                Key={"book_id": book_id},
                # delete_item on a missing key SUCCEEDS by default
                # (it's idempotent). We want to distinguish "deleted"
                # from "wasn't there" so the API can return 404.
                ConditionExpression="attribute_exists(book_id)",
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise
        return True

    # ── internal helper ─────────────────────────────────────────────

    def _item_to_response(self, item: dict[str, Any]) -> BookResponse:
        """Map a DynamoDB item to our API model.

        Storage calls the key `book_id`; the API calls it `id`. Doing the
        rename here keeps the storage schema free to change without
        breaking the public API contract.
        """
        clean = _from_dynamo(item)
        book_id = clean.pop("book_id")
        return BookResponse(id=book_id, **clean)


# ── WHAT DYNAMODB FIXED vs THE JSON FILE ────────────────────────────
#
#   JSON file (stage 1)              DynamoDB (stage 2)
#   ─────────────────────            ──────────────────────────────
#   Lost updates on concurrent  ->   update_item is atomic server-side
#     writes                          + ConditionExpression guards
#   Rewrites whole file O(n)    ->   writes touch only that one item
#   Per-instance local file     ->   one shared table, all instances
#     (breaks on Lambda/ECS)          see the same data
#   No querying, filter in      ->   Query/GSI (see docs/03) for real
#     Python                          indexed access patterns
#
# NEW things to watch that the JSON file never had:
#   - Costs money per request (tiny, but non-zero — see docs/06)
#   - Needs IAM permissions (the CFN templates grant exactly this table)
#   - Eventual consistency on reads by default; pass
#     ConsistentRead=True to get_item when you must read your own write
#     immediately (costs 2x the read units)
#   - 400 KB max item size
