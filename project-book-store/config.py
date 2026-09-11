"""
Configuration — the single switch that decides WHERE books are stored.

This is the whole reason the DynamoDB migration is painless. The app
code never says "use JSON" or "use DynamoDB"; it asks for a repository,
and this config decides which one it gets.

    Local development:   STORAGE=json      (no AWS account needed)
    Deployed on AWS:     STORAGE=dynamodb  (set by CloudFormation)

RULE: config comes from the ENVIRONMENT, never hardcoded and never
committed. Real secrets (API keys, DB passwords) belong in AWS Secrets
Manager or SSM Parameter Store — not in a .env file that could be
accidentally committed. See docs/01-engineering-flow.md.
"""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",           # local convenience only; not used on AWS
        env_file_encoding="utf-8",
        extra="ignore",            # ignore unrelated env vars (AWS sets many)
    )

    # Which storage backend to use.
    # Literal[] means an invalid value fails FAST at startup with a clear
    # error, instead of silently falling through to a wrong default.
    storage: Literal["json", "dynamodb"] = "json"

    # Used when storage == "json"
    books_file: str = "books.json"

    # Used when storage == "dynamodb"
    table_name: str = "book-store-books"
    aws_region: str = "us-east-1"

    # Optional: point boto3 at DynamoDB Local instead of real AWS.
    # Empty string means "use the real AWS endpoint".
    dynamodb_endpoint_url: str = ""

    env: str = "local"


@lru_cache
def get_settings() -> Settings:
    """Cached so we read the environment once per process, not per request.

    GOTCHA: because of the cache, changing an env var requires a RESTART,
    not just a new request. In tests, override the dependency instead of
    mutating os.environ (see test_books.py).
    """
    return Settings()
