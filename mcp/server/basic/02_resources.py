"""Resources & templates -- read-only data, addressed by URI
=================================================================

A resource is read-only data addressed by URI, not called like a function.
A template is a resource whose URI has parameters, so one function serves
many URIs.

    @mcp.resource("data://greeting")        one fixed resource
    @mcp.resource("greet://{name}")         a TEMPLATE -- name comes from the URI

    greet://  {language}  /  {name}        {p}   = one required path segment
    scheme     path params, REQUIRED        {p*}  = many segments (crosses "/")
    greet://{name}{?language,repeat}       {?p}  = OPTIONAL query param --
    scheme     path   query, OPTIONAL              its function arg needs a default

    Rule of thumb: required data in the PATH, optional config in the QUERY.

What you return becomes:
    str              plain text
    dict/list        JSON text (still mime_type text/plain unless you set it)
    ResourceResult   full control: multiple representations, each its own type

Level: BASIC
Run:  uv run python basic/02_resources.py
Test in Inspector:  uv run fastmcp dev inspector basic/02_resources.py
"""

import asyncio
import json
from pathlib import Path

from fastmcp import Client, Context, FastMCP
from fastmcp.exceptions import ResourceError
from fastmcp.resources import ResourceContent, ResourceResult, ResourceSecurity, TextResource

mcp = FastMCP("GreetingService")


# ------------------------------------------------------------- 1. the basics
@mcp.resource("resource://greeting")
def get_greeting() -> str:
    """Provides the default greeting."""
    return "Hello from FastMCP Resources!"


@mcp.resource(
    uri="data://greeting-config",
    name="GreetingConfig",
    mime_type="application/json",   # NOT inferred from returning a dict -- set it explicitly
    tags={"config"},
    meta={"team": "infrastructure"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
def get_greeting_config() -> dict:
    """The greeting templates this server knows."""
    return {"en": "Hello, {name}!", "fr": "Bonjour, {name}!"}


# ---------------------------------------------- 2. many contents at once
@mcp.resource("data://greetings")
def all_greetings() -> ResourceResult:
    """One read, two representations -- the client picks by mime type."""
    return ResourceResult(contents=[
        ResourceContent(content=[{"lang": "en", "text": "Hello!"}], mime_type="application/json"),
        ResourceContent(content="# Greetings\n- en: Hello!", mime_type="text/markdown"),
    ])


# ----------------------------------------------------- 3. context + async
@mcp.resource("resource://greeting-status")
async def greeting_status(ctx: Context) -> str:
    """Resources get Context too -- see 04_context.py for the full picture."""
    return json.dumps({"status": "operational", "request_id": ctx.request_id})


# ------------------------------------------------------------ 4. templates
@mcp.resource("greet://{name}")
def greeting_for(name: str) -> dict:
    """{name} is a required PATH parameter."""
    return {"greeting": f"Hello, {name}!"}


@mcp.resource("greet://{language}/{name}")
def greeting_in(language: str, name: str) -> dict:
    """Two path parameters -> both required function arguments."""
    hello = {"en": "Hello", "fr": "Bonjour", "de": "Hallo"}.get(language, "Hello")
    return {"language": language, "greeting": f"{hello}, {name}!"}


@mcp.resource("greetgroup://{group*}")   # {p*} is a WILDCARD -- it crosses "/"
def greeting_for_group(group: str) -> str:
    """Greets a nested group path, however deep: greetgroup://europe/west/team."""
    return f"Hello, everyone in {group}!"


@mcp.resource("hello://{name}{?language,repeat}")
def hello(name: str, language: str = "en", repeat: int = 1) -> dict:
    """{?a,b} are OPTIONAL query params -- their function args need defaults.
    Query strings are coerced to the annotated type: ?repeat=2 -> int 2."""
    hi = {"en": "Hello", "fr": "Bonjour"}.get(language, "Hello")
    return {"greeting": " ".join([f"{hi}, {name}!"] * repeat)}


@mcp.resource("greetall://{language}{?names*}")   # explode: ?names=a&names=b -> list
def greet_all(language: str, names: list[str] | None = None) -> dict:
    return {"language": language, "greeted": names or []}


# One function, several URI patterns -- call the decorator without "@".
def lookup_greeting(name: str | None = None, email: str | None = None) -> dict:
    """Find someone's greeting by either name or email."""
    return {"by": "email" if email else "name", "greeting": f"Hello, {email or name}!"}


mcp.resource("person://email/{email}")(lookup_greeting)
mcp.resource("person://name/{name}")(lookup_greeting)


# -------------------------------------------------- 5. path traversal guard
# ON BY DEFAULT for templated resources: FastMCP checks parameter values
# BEFORE your handler runs, and rejects "../" escapes, absolute paths, and
# null bytes. A rejected read just looks like "not found" to the client.
CARDS_ROOT = Path(__file__).parent


@mcp.resource("card://{path*}")
def read_greeting_card(path: str) -> str:
    """card://../secret never reaches this function."""
    target = (CARDS_ROOT / path).resolve()
    if not target.is_relative_to(CARDS_ROOT) or not target.is_file():
        raise ResourceError("Card not found")
    return target.read_text(encoding="utf-8")[:60]


# Legitimately traversal-shaped values (git refs, version ranges) can be
# exempted from the guard with security=ResourceSecurity(exempt_params=...).
@mcp.resource("greethistory://{ref}", security=ResourceSecurity(exempt_params={"ref"}))
def greeting_history(ref: str) -> str:
    """ref='HEAD~3..HEAD' is allowed because the param is exempt."""
    return f"greeting history for {ref}"


# ------------------------------------------------------- 6. error handling
@mcp.resource("resource://masked-error")
def fail_masked() -> str:
    """A plain exception is masked when mask_error_details=True (see 08_configuration)."""
    raise ValueError("Sensitive internal path: /etc/secrets.conf")


# ------------------------------------------ 7. resource classes (no function)
# Siblings: FileResource (a local file), BinaryResource (bytes),
# DirectoryResource (a JSON listing), HttpResource (server-side fetch).
# HttpResource keeps `uri` (identity) separate from `url` (what it fetches):
# use a custom scheme like docs:// so clients know the server mediates it.
mcp.add_resource(
    TextResource(uri="resource://notice", text="Greetings are localised for en, fr and de.")
)


async def main():
    async with Client(mcp) as client:
        print("resources:")
        for r in await client.list_resources():
            print(f"  {str(r.uri):<24} {r.mime_type}")

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
            "person://email/ada@example.com",      # same function,
            "person://name/Bob",                   # two URI patterns
            "greethistory://HEAD~3..HEAD",         # exempt from the guard
        ):
            out = (await client.read_resource(uri))[0]
            print(f"  {uri:<34} {out.text[:48]}")

        multi = await client.read_resource("data://greetings")
        print("\ndata://greetings (2 representations) ->", [(c.mime_type, c.text[:20]) for c in multi])

        try:
            await client.read_resource("card://../secret")
        except Exception as e:
            print(f"\ncard://../secret blocked -> {type(e).__name__}")

        ok = await client.read_resource("card://02_resources.py")
        print("card://02_resources.py  ->", ok[0].text.splitlines()[0])


if __name__ == "__main__":
    asyncio.run(main())
