# ══════════════════════════════════════════════════════════════════
#  PYTHON TypedDict — Condensed Guide
#  TypedDict = a dict with KNOWN keys and TYPED values
#  Regular dict[str, Any] → no idea what keys exist
#  TypedDict → "this dict MUST have name(str), age(int), email(str)"
#  Python does NOT enforce at runtime — type checkers (mypy/pyright) do
# ══════════════════════════════════════════════════════════════════

from typing import TypedDict, NotRequired, Required, get_type_hints, Any

# ╔══════════════════════════════════════════════════╗
# ║                  BEGINNER                        ║
# ╚══════════════════════════════════════════════════╝

# ── 1. Problem — Why Not Just dict? ───────────────
# dict[str, Any] = "some keys, some values" — no safety

def process_user_bad(user: dict) -> str:
    return f"{user['name']} is {user['age']}"  # what if "name" is missing? KeyError at runtime

user_bad = {"name": "Alice", "age": 30}
print(process_user_bad(user_bad))         # works
# process_user_bad({"age": 30})           # KeyError: 'name' — no warning before running

# TypedDict fixes this — type checker catches missing keys BEFORE you run the code

# ── 2. Basic TypedDict ───────────────────────────
# class Name(TypedDict): → defines which keys are required and their types
class User(TypedDict):
    name: str
    age: int
    email: str

# creating — looks like a normal dict
alice: User = {"name": "Alice", "age": 30, "email": "alice@test.com"}  # valid
print(alice)           # {'name': 'Alice', 'age': 30, 'email': 'alice@test.com'}
print(alice["name"])   # Alice — access like normal dict
print(type(alice))     # <class 'dict'> — it IS a dict, TypedDict adds no overhead

# these would be caught by mypy/pyright (but Python itself won't stop you):
# bad1: User = {"name": "Alice", "age": 30}               # missing "email"
# bad2: User = {"name": "Alice", "age": "thirty", "email": "a@b.com"}  # age should be int
# bad3: User = {"name": "Alice", "age": 30, "email": "a@b.com", "extra": True}  # extra key

# ── 3. Using in Functions ─────────────────────────
def greet_user(user: User) -> str:
    return f"Hello {user['name']}, age {user['age']}"

def create_user(name: str, age: int, email: str) -> User:
    return {"name": name, "age": age, "email": email}

print(greet_user(alice))                           # Hello Alice, age 30
print(create_user("Bob", 25, "bob@test.com"))     # {'name': 'Bob', 'age': 25, ...}

# ── 4. TypedDict vs dict vs dataclass ────────────
#
#  dict[str, Any]         → no key safety, no type safety
#  TypedDict              → key + type safety (type checker only), still a plain dict
#  dataclass              → real Python class, attrs via dot notation, __init__ generated
#  Pydantic BaseModel     → runtime validation + auto-conversion
#
#  When to use TypedDict:
#    - Working with JSON / API responses (already dicts)
#    - FastAPI request/response bodies
#    - Config dicts you pass around
#    - Anywhere you want dict[str, Any] but with structure
#
#  When to use dataclass instead:
#    - You want user.name not user["name"]
#    - You need methods on the object
#    - You need immutability (frozen=True)

# ╔══════════════════════════════════════════════════╗
# ║               INTERMEDIATE                       ║
# ╚══════════════════════════════════════════════════╝

# ── 5. Optional Keys — total=False ────────────────
# By default all keys are REQUIRED (total=True)
# total=False → ALL keys become optional

class Config(TypedDict, total=False):
    host: str
    port: int
    debug: bool

config1: Config = {"host": "localhost"}                    # valid — all optional
config2: Config = {"host": "0.0.0.0", "port": 8080}      # valid
config3: Config = {}                                       # valid — empty is fine
print(config1)  # {'host': 'localhost'}

# ── 6. Mix Required + Optional — NotRequired ─────
# Best approach: keep total=True (default), mark optional keys with NotRequired
class APIResponse(TypedDict):
    status: int                         # required
    data: dict                          # required
    error: NotRequired[str]             # optional — can be missing
    metadata: NotRequired[dict]         # optional

resp1: APIResponse = {"status": 200, "data": {"id": 1}}                         # valid
resp2: APIResponse = {"status": 500, "data": {}, "error": "Server Error"}       # valid
print(resp1)  # {'status': 200, 'data': {'id': 1}}
print(resp2)  # {'status': 500, 'data': {}, 'error': 'Server Error'}

# ── 7. Opposite — Required in total=False ─────────
# If most keys are optional but a few are required:
class Filters(TypedDict, total=False):
    query: Required[str]     # this one is required even though total=False
    page: int                # optional
    limit: int               # optional
    sort_by: str             # optional

f1: Filters = {"query": "python"}                          # valid — only required key
f2: Filters = {"query": "python", "page": 1, "limit": 10} # valid
# f3: Filters = {"page": 1}  # error — "query" is required

# ── 8. Nested TypedDict ──────────────────────────
class Address(TypedDict):
    street: str
    city: str
    country: str

class Company(TypedDict):
    name: str
    address: Address        # TypedDict inside TypedDict

class Employee(TypedDict):
    name: str
    age: int
    company: Company
    tags: list[str]         # list of strings

emp: Employee = {
    "name": "Alice",
    "age": 30,
    "company": {
        "name": "Reuters",
        "address": {"street": "123 Main", "city": "London", "country": "UK"},
    },
    "tags": ["engineering", "senior"],
}
print(emp["company"]["address"]["city"])  # London

# ── 9. Inheritance — Extend a TypedDict ───────────
class BaseUser(TypedDict):
    name: str
    email: str

class AdminUser(BaseUser):     # inherits name + email, adds role + permissions
    role: str
    permissions: list[str]

admin: AdminUser = {
    "name": "Alice",
    "email": "alice@test.com",
    "role": "admin",
    "permissions": ["read", "write", "delete"],
}
print(admin)  # has all 4 keys

# common pattern — base with required, child adds optional
class BaseEvent(TypedDict):
    event_type: str
    timestamp: str

class ClickEvent(BaseEvent):
    page: str
    x: NotRequired[int]
    y: NotRequired[int]

click: ClickEvent = {"event_type": "click", "timestamp": "2024-01-15T10:30:00", "page": "/home"}
print(click)

# ╔══════════════════════════════════════════════════╗
# ║                  ADVANCED                        ║
# ╚══════════════════════════════════════════════════╝

# ── 10. Functional Syntax — keys with spaces/hyphens ─
# class syntax doesn't allow "content-type" as a key name
# functional syntax does:
HTTPHeaders = TypedDict("HTTPHeaders", {
    "content-type": str,
    "x-request-id": str,
    "authorization": str,
})
headers: HTTPHeaders = {
    "content-type": "application/json",
    "x-request-id": "abc-123",
    "authorization": "Bearer token123",
}
print(headers["content-type"])  # application/json

# ── 11. Runtime Inspection ────────────────────────
# TypedDict stores type info — you can read it at runtime
print(User.__annotations__)          # {'name': <class 'str'>, 'age': <class 'int'>, 'email': <class 'str'>}
print(User.__required_keys__)        # frozenset({'name', 'age', 'email'})
print(User.__optional_keys__)        # frozenset()

print(APIResponse.__required_keys__)   # frozenset({'status', 'data'})
print(APIResponse.__optional_keys__)   # frozenset({'error', 'metadata'})

hints = get_type_hints(Employee)
print(hints)  # {'name': str, 'age': int, 'company': Company, 'tags': list[str]}

# ── 12. TypedDict with JSON / API Responses ──────
# Most common real-world use — typing API responses
import json

class PaginatedResponse(TypedDict):
    total: int
    page: int
    per_page: int
    items: list[dict[str, Any]]
    next_page: NotRequired[str | None]

def parse_api_response(raw_json: str) -> PaginatedResponse:
    data: PaginatedResponse = json.loads(raw_json)
    return data

raw = '{"total": 100, "page": 1, "per_page": 10, "items": [{"id": 1}]}'
response = parse_api_response(raw)
print(f"Page {response['page']} of {response['total']} items")  # Page 1 of 100 items

# ── 13. TypedDict Does NOT Validate at Runtime ───
# THIS IS THE KEY THING TO UNDERSTAND
# TypedDict is ONLY for type checkers (mypy/pyright) — Python ignores it

wrong_user: User = {"name": 123, "age": "thirty", "email": True}  # type: ignore
print(wrong_user)  # runs fine! {'name': 123, 'age': 'thirty', 'email': True}

# If you need runtime validation → use Pydantic
# from pydantic import TypeAdapter
# adapter = TypeAdapter(User)
# adapter.validate_python({"name": 123, "age": "thirty"})  # → ValidationError

# ── 14. Pattern — Config / Settings ──────────────
class DBConfig(TypedDict):
    host: str
    port: int
    database: str
    username: str
    password: str
    pool_size: NotRequired[int]
    ssl: NotRequired[bool]

class AppSettings(TypedDict):
    app_name: str
    debug: bool
    db: DBConfig
    allowed_origins: list[str]

settings: AppSettings = {
    "app_name": "MyAPI",
    "debug": True,
    "db": {
        "host": "localhost",
        "port": 5432,
        "database": "mydb",
        "username": "admin",
        "password": "secret",
        "pool_size": 10,
    },
    "allowed_origins": ["http://localhost:3000"],
}
print(settings["db"]["host"])  # localhost

# ── 15. Pattern — FastAPI / LLM Tool Parameters ──
class ToolInput(TypedDict):
    query: str
    max_results: NotRequired[int]
    filters: NotRequired[dict[str, str]]

class ToolOutput(TypedDict):
    status: str
    results: list[dict[str, Any]]
    error: NotRequired[str]

def search_tool(params: ToolInput) -> ToolOutput:
    return {
        "status": "success",
        "results": [{"title": f"Result for: {params['query']}"}],
    }

print(search_tool({"query": "python typeddict"}))

# ══════════════════════════════════════════════════════════════════
#  CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
#
#  DEFINE:
#    class Name(TypedDict):              all keys required
#    class Name(TypedDict, total=False): all keys optional
#
#  OPTIONAL KEYS:
#    key: NotRequired[str]    optional in total=True  (default)
#    key: Required[str]       required in total=False
#
#  INHERIT:
#    class Child(Parent):     inherits all parent keys, adds new ones
#
#  FUNCTIONAL (special key names):
#    Name = TypedDict("Name", {"x-key": str, "another": int})
#
#  RUNTIME INSPECTION:
#    MyDict.__annotations__     → {key: type, ...}
#    MyDict.__required_keys__   → frozenset of required
#    MyDict.__optional_keys__   → frozenset of optional
#    get_type_hints(MyDict)     → resolved types
#
#  KEY FACTS:
#    - TypedDict is a PLAIN dict at runtime — zero overhead
#    - Python does NOT enforce types — only mypy/pyright do
#    - For runtime validation → use Pydantic
#    - Best for: JSON, API responses, configs, function params
#
#  vs OTHER OPTIONS:
#    dict[str, Any]     → no safety
#    TypedDict          → type checker safety, still a dict
#    dataclass          → real class, dot access, methods
#    NamedTuple         → immutable, tuple-like
#    Pydantic BaseModel → runtime validation + conversion
# ══════════════════════════════════════════════════════════════════

# ╔══════════════════════════════════════════════════╗
# ║          INTERVIEW GOTCHAS                       ║
# ╚══════════════════════════════════════════════════╝

# ── Q: Does TypedDict validate at runtime? ──
class StrictUser(TypedDict):
    name: str
    age: int

wrong: StrictUser = {"name": 123, "age": "thirty"}  # type: ignore
print(wrong)  # runs fine! {'name': 123, 'age': 'thirty'}
# TypedDict is ONLY for type checkers — Python ignores it completely
# For runtime validation → use Pydantic

# ── Q: TypedDict vs dataclass — when to use which? ──
# TypedDict → when data is already a dict (JSON, API responses, configs)
# dataclass → when you want user.name (dot access), methods, immutability

# ── Q: What's the difference between total=False and NotRequired? ──
# total=False → makes ALL keys optional
# NotRequired → makes INDIVIDUAL keys optional (more precise)
# Use NotRequired when most keys are required but a few are optional
