"""
Tests for the DynamoDB repository that need NO AWS account.

    pytest test_repo_dynamo.py -v

We cannot call real DynamoDB here, but two things are worth testing
offline and they're exactly the parts that break in practice:

  1. The Decimal <-> float conversion (the classic DynamoDB gotcha)
  2. That DynamoBookRepository and JsonBookRepository really do expose
     the same interface, so swapping STORAGE can't fail at runtime

To test against an actual table, see docs/03-stage2-dynamodb.md
(DynamoDB Local, free), or use `moto` to mock AWS in-process.

NOTE: this file needs boto3 installed (repo_dynamo imports it). If you
are only doing stage 1, `pytest test_books.py` is the suite to run.
"""

from decimal import Decimal

import pytest

pytest.importorskip("boto3", reason="stage 2 only; run `uv pip install boto3`")

import repo_dynamo as rd                     # noqa: E402
from repo_json import JsonBookRepository      # noqa: E402

PROTOCOL_METHODS = ("list_all", "get", "create", "replace", "patch", "delete")


# ── the Decimal gotcha ──────────────────────────────────────────────

def test_float_becomes_decimal():
    """DynamoDB has no float type; boto3 raises TypeError on floats."""
    assert rd._to_dynamo(9.99) == Decimal("9.99")
    assert isinstance(rd._to_dynamo(9.99), Decimal)


def test_conversion_goes_through_str_to_avoid_binary_noise():
    """The whole reason _to_dynamo uses Decimal(str(x)), not Decimal(x).

        Decimal(9.99)      -> 9.99000000000000021316...
        Decimal(str(9.99)) -> 9.99
    """
    assert str(rd._to_dynamo(9.99)) == "9.99"
    # Prove the naive version really is different, so this test is
    # guarding something real rather than restating the implementation.
    assert str(Decimal(9.99)) != "9.99"


def test_decimal_comes_back_as_plain_python():
    """json.dumps() can't serialise Decimal, so we convert at the boundary."""
    assert rd._from_dynamo(Decimal("9.99")) == 9.99
    assert isinstance(rd._from_dynamo(Decimal("9.99")), float)


def test_whole_numbers_come_back_as_int_not_float():
    """3 rather than 3.0 - avoids ugly prices like 12.0 in responses."""
    result = rd._from_dynamo(Decimal("3"))
    assert result == 3
    assert isinstance(result, int)


def test_conversion_recurses_into_dicts_and_lists():
    converted = rd._to_dynamo({"price": 1.5, "tags": [2.5, 3.0]})
    assert converted["price"] == Decimal("1.5")
    assert converted["tags"] == [Decimal("2.5"), Decimal("3.0")]


def test_non_numeric_values_pass_through_untouched():
    assert rd._to_dynamo("1984") == "1984"
    assert rd._to_dynamo(None) is None
    assert rd._to_dynamo(True) is True


def test_round_trip_preserves_the_value():
    for original in (9.99, 0.01, 12.5, 1234.56):
        assert rd._from_dynamo(rd._to_dynamo(original)) == original


# ── interface parity: the safety net for swapping STORAGE ───────────

@pytest.mark.parametrize("cls", [rd.DynamoBookRepository, JsonBookRepository])
def test_both_repositories_expose_the_same_interface(cls):
    """If these ever diverge, STORAGE=dynamodb would crash at runtime
    instead of at import time. Checking the class (not an instance)
    means no boto3 client is created and no AWS call is made.
    """
    missing = [m for m in PROTOCOL_METHODS if not callable(getattr(cls, m, None))]
    assert not missing, f"{cls.__name__} is missing: {missing}"
