# ══════════════════════════════════════════════════════════════════
#  PYTHON ANNOTATIONS & TYPE HINTS — Condensed Guide
#  Annotations = metadata labels on variables/functions
#  Python does NOT enforce them — they are HINTS only
#  But frameworks (FastAPI, Pydantic, dataclasses) READ them at runtime
# ══════════════════════════════════════════════════════════════════

from __future__ import annotations  # makes all annotations lazy strings (3.7+)
import typing, functools
from typing import (
    Optional, Union, Any, Callable, Literal, TypeAlias,
    TypedDict, Annotated, TypeVar, Protocol, runtime_checkable,
    Final, final, ClassVar, NamedTuple, NotRequired, Sized, get_type_hints,
)
from dataclasses import dataclass, field

# ╔══════════════════════════════════════════════════╗
# ║                  BEGINNER                        ║
# ╚══════════════════════════════════════════════════╝

# ── 1. Basic Function Annotations ──────────────────
# param: Type → annotate parameter  |  -> Type → annotate return
# Stored in func.__annotations__  |  Python IGNORES them — no enforcement!
def greet(name: str) -> str:
    return f"Hello, {name}!"
print(greet("Alice"))   # Hello, Alice!
print(greet(123))       # Hello, 123!  — no error, annotations aren't enforced
print(greet.__annotations__)  # {'name': <class 'str'>, 'return': <class 'str'>}

def add(a: int, b: int) -> int:
    return a + b
print(add("hello", " world"))  # works fine — Python doesn't care

# ── 2. Variable Annotations (3.6+) ─────────────────
# variable: Type = value — just a label, no validation
name: str = "Alice"
age: int = 30
price: float = 9.99
active: bool = True
wrong: int = "this is a string"  # no error! annotation is just a hint
future_value: int  # declares "will exist" — but variable doesn't exist yet
# print(future_value)  # NameError! annotation alone doesn't create it

# ── 3. Collection Type Annotations ─────────────────
# 3.9+: list[int], dict[str, int], tuple[int, str], set[str]
# 3.8:  List[int], Dict[str, int] (from typing — avoid in new code)
def sum_scores(scores: list[int]) -> int:        return sum(scores)
def get_config() -> dict[str, str]:              return {"host": "localhost", "port": "8000"}
def get_point() -> tuple[int, int]:              return (10, 20)
def group_scores() -> dict[str, list[int]]:      return {"math": [90, 85]}  # nested
print(sum_scores([10, 20, 30]))  # 60
print(get_point())               # (10, 20)

# ╔══════════════════════════════════════════════════╗
# ║               INTERMEDIATE                       ║
# ╚══════════════════════════════════════════════════╝

# ── 4. Optional — value can be X or None ───────────
# Optional[str] == str | None (3.10+ pipe syntax)
def find_user(user_id: int) -> Optional[dict]:     # old style
    return {1: {"name": "Alice"}}.get(user_id)
def find_item(item_id: int) -> dict | None:        # 3.10+ style (same thing)
    return {1: {"name": "Laptop"}}.get(item_id)
def greet_user(name: str, title: Optional[str] = None) -> str:
    return f"Hello, {title + ' ' if title else ''}{name}!"
print(find_user(1))    # {'name': 'Alice'}
print(find_user(99))   # None

# ── 5. Union — one of several types ────────────────
# Union[str, int] == str | int (3.10+)
def format_id(user_id: Union[str, int]) -> str:    # old style
    return f"USER-{user_id}"
def flexible(value: str | int | float) -> str:     # 3.10+ style
    return str(value)
print(format_id(42))     # USER-42
print(format_id("abc"))  # USER-abc

# ── 6. Any — accept anything ──────────────────────
# Use sparingly — defeats purpose of type hints
def log_value(value: Any) -> str:
    return f"Logged: {value} ({type(value).__name__})"
print(log_value([1, 2]))  # Logged: [1, 2] (list)

# ── 7. Callable — functions as parameters ──────────
# Callable[[param_types], return_type]
def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)
print(apply(lambda x, y: x * y, 3, 5))  # 15

def run_task(task: Callable[[], str]) -> str:      return task()      # no-arg callable
def execute(func: Callable[..., Any]) -> Any:      return func()      # any-arg callable

# Callback pattern
def fetch_data(url: str, on_success: Callable[[dict], None]) -> None:
    on_success({"url": url, "status": 200})
fetch_data("https://api.com", on_success=lambda d: print(f"  Got: {d}"))

# ── 8. Literal — restrict to specific values ──────
# Like an enum but simpler — type checkers enforce it
def set_color(color: Literal["red", "green", "blue"]) -> str:
    return f"Color: {color}"
def set_priority(level: Literal[1, 2, 3]) -> str:
    return {1: "High", 2: "Medium", 3: "Low"}.get(level, "Unknown")
print(set_color("red"))       # Color: red
print(set_color("purple"))    # runs fine — but mypy flags it
print(set_priority(1))        # High

# ── 9. TypeAlias — name complex types ─────────────
UserRecord: TypeAlias = dict[str, list[tuple[int, str]]]
JSON: TypeAlias = dict[str, Any]
Headers: TypeAlias = dict[str, str]
Coordinates: TypeAlias = tuple[float, float]

def make_request(url: str, headers: Headers) -> JSON:
    return {"url": url, "headers": headers}
def distance(p1: Coordinates, p2: Coordinates) -> float:
    return ((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2) ** 0.5
print(distance((0, 0), (3, 4)))  # 5.0

# ── 10. TypedDict — typed dictionary structure ─────
# Regular dict[str, Any] doesn't specify which keys exist
class UserDict(TypedDict):
    name: str
    age: int
    email: str

class Config(TypedDict, total=False):   # all keys optional
    host: str
    port: int

class APIResponse(TypedDict):
    status: int                         # required
    data: dict                          # required
    error: NotRequired[str]             # optional

def create_user() -> UserDict:
    return {"name": "Alice", "age": 30, "email": "alice@test.com"}
print(create_user())  # {'name': 'Alice', 'age': 30, 'email': 'alice@test.com'}

# ── 11. Annotated — attach metadata to types ──────
# Annotated[Type, metadata...] — Python ignores metadata, frameworks read it
# THIS is how FastAPI reads validation rules
def create_item(
    name: Annotated[str, "Item name, max 100 chars"],
    price: Annotated[float, "Price in USD, > 0"],
) -> dict:
    return {"name": name, "price": price}
print(create_item("Laptop", 999.99))  # {'name': 'Laptop', 'price': 999.99}

# FastAPI usage (not runnable without FastAPI):
# @app.get("/items")
# def get_items(
#     q: Annotated[str, Query(min_length=3, max_length=50)],
#     skip: Annotated[int, Query(ge=0)] = 0,
#     limit: Annotated[int, Query(le=100)] = 10,
# ): ...
# FastAPI reads Query() from Annotated → enforces validation + generates docs

# Custom metadata class — access at runtime
class Range:
    def __init__(self, min_val: int, max_val: int):
        self.min_val, self.max_val = min_val, max_val
    def __repr__(self): return f"Range({self.min_val}, {self.max_val})"

def set_volume(level: Annotated[int, Range(0, 100)]) -> str:
    return f"Volume: {level}"
hints = get_type_hints(set_volume, include_extras=True)
print(hints)  # {'level': typing.Annotated[int, Range(0, 100)], ...}

# ── 12. Class Annotations ─────────────────────────
class User:
    name: str
    age: int
    def __init__(self, name: str, age: int) -> None:
        self.name, self.age = name, age
    def greet(self) -> str:
        return f"Hi, I'm {self.name}, age {self.age}"
print(User("Alice", 30).greet())   # Hi, I'm Alice, age 30
print(User.__annotations__)        # {'name': <class 'str'>, 'age': <class 'int'>}

# ── 13. dataclass — annotations create real attributes ──
# @dataclass reads annotations → auto-generates __init__, __repr__, __eq__
@dataclass
class Product:
    name: str                                       # required
    price: float                                    # required
    quantity: int = 0                               # optional with default
    tags: list[str] = field(default_factory=list)   # mutable default
print(Product("Laptop", 999.99, 5, ["tech"]))  # Product(name='Laptop', ...)
print(Product("Mouse", 25.0))                   # Product(name='Mouse', price=25.0, ...)

@dataclass(frozen=True)    # immutable — Point(3,4).x = 5 → FrozenInstanceError
class Point:
    x: float
    y: float

@dataclass
class Rectangle:
    width: float
    height: float
    area: float = field(init=False)   # computed, not in __init__
    def __post_init__(self) -> None:
        self.area = self.width * self.height
print(Rectangle(5.0, 3.0))  # Rectangle(width=5.0, height=3.0, area=15.0)

# ── 14. NamedTuple with annotations ───────────────
class Coordinate(NamedTuple):
    x: float
    y: float
    label: str = "origin"
c = Coordinate(3.0, 4.0, "A")
print(c.x, c.label)       # 3.0 A
x, y, label = c           # unpack like a tuple — immutable (c.x = 10 → error)

# ╔══════════════════════════════════════════════════╗
# ║                  ADVANCED                        ║
# ╚══════════════════════════════════════════════════╝

# ── 15. TypeVar — generic type placeholders ────────
# "T" = whatever type the caller passes — keeps input/output consistent
T = TypeVar("T")
def first(items: list[T]) -> T:    # type checker knows first([1,2]) returns int
    return items[0]
print(first([1, 2, 3]))     # 1 (int → int)
print(first(["a", "b"]))    # a (str → str)

Number = TypeVar("Number", int, float)     # constrained — only int or float
def double(n: Number) -> Number:
    return n * 2

S = TypeVar("S", bound=Sized)              # bounded — must have __len__
def get_length(item: S) -> int:
    return len(item)
print(double(5))           # 10
print(get_length("hello")) # 5

# ── 16. Protocol — structural typing (duck typing) ─
# "Any object with these methods works" — no inheritance needed
@runtime_checkable
class Printable(Protocol):
    def to_string(self) -> str: ...

class UserP:
    def __init__(self, n: str): self.name = n
    def to_string(self) -> str: return f"User({self.name})"

class ProductP:
    def __init__(self, n: str, p: float): self.name, self.price = n, p
    def to_string(self) -> str: return f"Product({self.name}, ${self.price})"

def display(item: Printable) -> None:
    print(item.to_string())
display(UserP("Alice"))      # User(Alice) — matches Protocol, no inheritance
display(ProductP("Laptop", 999))
print(isinstance(UserP("Bob"), Printable))  # True (runtime_checkable)

# ── 17. Final — constants & non-overridable ────────
MAX_RETRIES: Final[int] = 3
API_URL: Final[str] = "https://api.example.com"
PI: Final = 3.14159          # type inferred
# MAX_RETRIES = 5  → mypy error: Cannot assign to final name

class Base:
    @final
    def critical(self) -> str:  # subclass can't override
        return "Don't override me"

# ── 18. ClassVar — class-level, not in __init__ ────
@dataclass
class Employee:
    name: str
    salary: float
    company: ClassVar[str] = "Reuters"     # shared, NOT in __init__
    count: ClassVar[int] = 0
    def __post_init__(self) -> None:
        Employee.count += 1
e1, e2 = Employee("Alice", 90000), Employee("Bob", 85000)
print(f"Company: {Employee.company}, Count: {Employee.count}")  # Reuters, 2

# ── 19. get_type_hints() — runtime inspection ─────
# Better than __annotations__ — resolves forward refs
def process(name: str, age: int, scores: list[float]) -> dict[str, Any]:
    return {"name": name, "age": age, "avg": sum(scores) / len(scores)}
hints = get_type_hints(process)
print(hints)  # {'name': str, 'age': int, 'scores': list[float], 'return': dict[str, Any]}

# Auto-validate using annotations
def validate(func: Callable, **kwargs: Any) -> dict[str, bool]:
    hints = get_type_hints(func)
    return {k: isinstance(kwargs[k], v) for k, v in hints.items()
            if k != "return" and k in kwargs}
print(validate(process, name="Alice", age=30, scores=[90.0]))  # all True
print(validate(process, name="Alice", age="thirty"))           # age: False

# ── 20. Forward References ────────────────────────
# Use "ClassName" string when type isn't defined yet
# Or: from __future__ import annotations (top of file) — makes ALL lazy
class TreeNode:
    def __init__(self, val: int, children: list[TreeNode] | None = None):
        self.val, self.children = val, children or []
    def __repr__(self) -> str:
        return f"Tree({self.val}{', ' + repr(self.children) if self.children else ''})"
tree = TreeNode(1, [TreeNode(2), TreeNode(3, [TreeNode(4)])])
print(tree)  # Tree(1, [Tree(2), Tree(3, [Tree(4)])])

# ── 21. Framework Usage Comparison ────────────────
# Pure Python — annotations IGNORED, no enforcement
# dataclass — annotations → auto __init__, __repr__, __eq__
# FastAPI — reads annotations for validation, conversion, docs generation
# Pydantic — ENFORCES types + auto-converts at runtime

# FastAPI (pseudocode):
# @app.get("/items/{item_id}")
# def get_item(
#     item_id: int,                              # path param, auto-convert
#     skip: Annotated[int, Query(ge=0)] = 0,     # query param, validated
# ): ...

try:
    from pydantic import BaseModel, ValidationError
    class UserModel(BaseModel):
        name: str
        age: int
        active: bool = True
    print(UserModel(name="Alice", age="25"))      # auto-converts "25" → 25
    try:
        UserModel(name="X", age="not a number")
    except ValidationError as e:
        print(f"  Pydantic caught {e.error_count()} error(s)")
except ImportError:
    print("  (pydantic not installed)")

# ── 22. mypy — Static Type Checking ──────────────
# pip install mypy && mypy file.py — catches bugs without running code
# pyright is a faster alternative. IDEs (VSCode/PyCharm) check in real-time.

# ── 23. Decorator Preserving Annotations ─────────
def logged(func: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        return func(*args, **kwargs)
    return wrapper

@logged
def compute(x: int, y: int) -> int:
    return x + y
print(f"Result: {compute(3, 5)}, name: {compute.__name__}")  # 8, compute

# ══════════════════════════════════════════════════════════════════
#  CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
#  SYNTAX:
#    param: Type              annotate parameter
#    -> Type                  annotate return value
#    var: Type = value        annotate variable
#    func.__annotations__    raw annotation dict
#    get_type_hints(func)    resolved (handles forward refs)
#
#  BASIC TYPES:
#    str, int, float, bool               primitives
#    list[int], dict[str, Any]           collections (3.9+)
#    tuple[int, str], set[str]           fixed tuple, set
#    List[int], Dict[str, int]           old style (typing, 3.8)
#
#  TYPING MODULE:
#    Optional[X]         X | None             value or None
#    Union[X, Y]         X | Y  (3.10+)       one of several types
#    Any                                       no restriction
#    Literal["a","b"]                          specific values only
#    Callable[[args], ret]                     function type
#    TypeAlias            = complex_type       readable name
#    TypedDict                                 dict with typed keys
#    Annotated[X, meta]                        type + framework metadata
#    TypeVar("T")                              generic placeholder
#    Protocol                                  structural/duck typing
#    Final[X]                                  constant, don't reassign
#    ClassVar[X]                               class-level, not instance
#    NamedTuple                                typed immutable tuple
#
#  FORWARD REFS:
#    "ClassName"                        use type before definition
#    from __future__ import annotations auto-stringify all
#
#  WHO READS ANNOTATIONS:
#    Pure Python  → IGNORED (just labels)
#    dataclass    → creates __init__, __repr__, __eq__
#    FastAPI      → validates, converts, generates docs
#    Pydantic     → enforces types, auto-converts
#    mypy/pyright → static checking (no runtime)
# ══════════════════════════════════════════════════════════════════
