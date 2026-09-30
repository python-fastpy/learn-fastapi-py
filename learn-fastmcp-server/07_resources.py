"""Lesson 07 -- Resources & templates in depth
=============================================

A resource is read-only data addressed by a URI, not called like a function.
A template is a resource whose URI has parameters, so one function serves
infinitely many URIs. Everything here serves greetings.

    @mcp.resource("data://greeting")        one fixed resource
    @mcp.resource("greet://{name}")         a TEMPLATE -- name comes from the URI
    @mcp.resource("greet://path/{p*}")      wildcard: {p*} matches across slashes
    @mcp.resource("greet://{name}{?lang}")  {?lang} is an optional query param
                                             (its function argument needs a default)

What you return becomes:
    str            plain text
    bytes          base64-encoded binary
    dict/list      JSON text (still text/plain unless you set mime_type)
    ResourceResult full control: multiple representations, each with its own type

Run:  uv run python 07_resources.py
"""

import asyncio
import json
from pathlib import Path

from fastmcp import Client, Context, FastMCP
from fastmcp.exceptions import ResourceError
from fastmcp.resources import (
    ResourceContent,
    ResourceResult,
    ResourceSecurity,
    TextResource,
)

mcp = FastMCP("GreetingService")


# ------------------------------------------------------------- 1. the basics
@mcp.resource("resource://greeting")
def get_greeting() -> str:
    """Provides the default greeting."""
    return "Hello from FastMCP Resources!"


# Full metadata. Set mime_type explicitly -- it is NOT inferred from the fact
# that you returned a dict.
@mcp.resource(
    uri="data://greeting-config",
    name="GreetingConfig",
    description="The greeting templates this server knows.",
    mime_type="application/json",
    tags={"config", "greeting"},
    meta={"team": "infrastructure"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def get_greeting_config() -> dict:
    return {"en": "Hello, {name}!", "fr": "Bonjour, {name}!", "default": "en"}


# ---------------------------------------------- 2. many contents at once
@mcp.resource("data://greetings")
def all_greetings() -> ResourceResult:
    """One read, two representations -- the client picks by mime type."""
    return ResourceResult(
        contents=[
            ResourceContent(content=[{"lang": "en", "text": "Hello!"}],
                            mime_type="application/json"),
            ResourceContent(content="# Greetings\n- en: Hello!", mime_type="text/markdown"),
        ],
        meta={"total": 1},
    )


# ----------------------------------------------------- 3. context + async
@mcp.resource("resource://greeting-status")
async def greeting_status(ctx: Context) -> str:
    """Resources get Context too (lesson 09)."""
    return json.dumps({"status": "operational", "request_id": ctx.request_id})


# ------------------------------------------------------------ 4. templates
@mcp.resource("greet://{name}")
def greeting_for(name: str) -> dict:
    """Provides a greeting for a specific person."""
    return {"name": name.capitalize(), "greeting": f"Hello, {name.capitalize()}!"}


@mcp.resource("greet://{language}/{name}")
def greeting_in(language: str, name: str) -> dict:
    """Two path parameters -> both required function arguments."""
    hello = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}.get(language, "Hello")
    return {"language": language, "greeting": f"{hello}, {name}!"}


# {group*} is a WILDCARD: it crosses "/" boundaries. Plain {p} would not.
@mcp.resource("greetgroup://{group*}")
def greeting_for_group(group: str) -> str:
    """Greets a nested group path, however deep."""
    return f"Hello, everyone in {group}!"


# Query parameters {?a,b} must map to arguments WITH defaults. Path params map
# to required arguments. Rule of thumb: required data in the path, optional
# config in the query string.
@mcp.resource("hello://{name}{?language,repeat}")
def hello(name: str, language: str = "en", repeat: int = 1) -> dict:
    """Strings from the query string are coerced to the annotated types."""
    hi = {"en": "Hello", "fr": "Bonjour"}.get(language, "Hello")
    return {"greeting": " ".join([f"{hi}, {name}!"] * repeat), "repeat": repeat}


# The explode modifier {?names*} accepts a repeated query parameter as a list.
@mcp.resource("greetall://{language}{?names*}")
def greet_all(language: str, names: list[str] | None = None) -> dict:
    return {"language": language, "greeted": names or []}


# One function, several URI patterns -- apply the decorator manually.
def lookup_greeting(name: str | None = None, email: str | None = None) -> dict:
    """Find someone's greeting by either name or email."""
    return {"by": "email" if email else "name", "greeting": f"Hello, {email or name}!"}


mcp.resource("person://email/{email}")(lookup_greeting)
mcp.resource("person://name/{name}")(lookup_greeting)


# -------------------------------------------------- 5. path traversal guard
# ON BY DEFAULT for templated resources: FastMCP checks parameter values
# before your handler runs, and rejects "../" escapes, absolute paths, and
# null bytes. A rejected read just looks like "not found" to the client.
CARDS_ROOT = Path(__file__).parent


@mcp.resource("card://{path*}")
def read_greeting_card(path: str) -> str:
    """card://../secret never reaches this function."""
    target = (CARDS_ROOT / path).resolve()
    # Screening bounds relative escapes; anchoring inside a root is still YOUR job.
    if not target.is_relative_to(CARDS_ROOT) or not target.is_file():
        raise ResourceError("Card not found")
    return target.read_text(encoding="utf-8")[:60]


# Legitimately traversal-shaped values (git refs, version ranges) get exempted.
@mcp.resource("greethistory://{ref}", security=ResourceSecurity(exempt_params={"ref"}))
def greeting_history(ref: str) -> str:
    """ref='HEAD~3..HEAD' is allowed because the param is exempt."""
    return f"greeting history for {ref}"


# ------------------------------------------------------- 6. error handling
@mcp.resource("resource://masked-error")
def fail_masked() -> str:
    """A plain exception is masked when mask_error_details=True."""
    raise ValueError("Sensitive internal path: /etc/secrets.conf")


# ------------------------------------------ 7. resource classes (no function)
mcp.add_resource(
    TextResource(
        uri="resource://notice",
        name="Greeting Notice",
        text="Greetings are localised for en, fr and de.",
        tags={"notification"},
    )
)
# Siblings: FileResource (a local file), BinaryResource (bytes),
# DirectoryResource (a JSON listing), HttpResource (server-side fetch).
# HttpResource keeps `uri` (identity) separate from `url` (what it fetches):
# use a custom scheme like docs:// so clients know the server mediates it.


async def main():
    async with Client(mcp) as client:
        print("resources:")
        for r in await client.list_resources():
            print(f"  {str(r.uri):<28} {r.mime_type}")

        print("\ntemplates:")
        for t in await client.list_resource_templates():
            print(f"  {t.uri_template}")

        print("\nreads")
        for uri in (
            "resource://greeting",
            "data://greeting-config",
            "resource://notice",
            "greet://alice",
            "greet://fr/Ada",
            "greetgroup://europe/west/team",       # wildcard crosses slashes
            "hello://Ada?language=fr&repeat=2",    # query params coerced to int
            "greetall://en?names=ada&names=bob",   # explode -> list
            "person://email/ada@example.com",
            "person://name/Bob",
            "greethistory://HEAD~3..HEAD",         # exempt from screening
        ):
            out = (await client.read_resource(uri))[0]
            print(f"  {uri:<38} {out.text[:52]}")

        # one read, two contents
        multi = await client.read_resource("data://greetings")
        print("\ndata://greetings ->", [(c.mime_type, c.text[:22]) for c in multi])

        # the traversal guard, before the handler runs
        try:
            await client.read_resource("card://../secret")
            print("\ncard://../secret was ALLOWED (unexpected)")
        except Exception as e:
            print(f"\ncard://../secret blocked -> {type(e).__name__}: {e}")

        ok = await client.read_resource("card://07_resources.py")
        print("card://07_resources.py  ->", ok[0].text.splitlines()[0])


if __name__ == "__main__":
    asyncio.run(main())

# Exercises:
# 1. Return a dict from a resource WITHOUT mime_type="application/json".
#    Confirm the content is JSON text but the mime type still says text/plain.
# 2. Change {group*} to {group} and re-read greetgroup://europe/west/team.
# 3. Give a template a required argument that is NOT in the URI -- FastMCP
#    rejects it at registration. Read the error.
# 4. Set security=None on read_greeting_card and retry card://../secret.
#    (Then put it back.)
