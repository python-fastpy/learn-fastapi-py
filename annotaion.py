# ╔══════════════════════════════════════════════════════════════════════╗
# ║          PYTHON ANNOTATIONS — All Concepts Master Guide             ║
# ║                                                                     ║
# ║  Annotation = metadata label attached to variables/functions        ║
# ║  Python does NOT enforce them — they are HINTS only                 ║
# ║  But frameworks like FastAPI/Pydantic READ them at runtime          ║
# ║                                                                     ║
# ║  Two main uses:                                                     ║
# ║    1. Type hints     → tell humans/tools what type is expected      ║
# ║    2. Framework magic → FastAPI, Pydantic, dataclasses use them     ║
# ╚══════════════════════════════════════════════════════════════════════╝


# ════════════════════════════════════════════════════
# 1. Basic function annotations
#
#  param: Type     → annotate parameter
#  -> Type         → annotate return value
#  Stored in func.__annotations__ dict
#  Python IGNORES them — no enforcement!
# ════════════════════════════════════════════════════

print("=" * 60)
print("1. Basic function annotations")
print("=" * 60)

def greet(name: str) -> str:
    return f"Hello, {name}!"

# Works fine — annotation says str
print(f"  greet('Alice') = {greet('Alice')}")

# ALSO works — Python does NOT enforce annotations
print(f"  greet(123) = {greet(123)}")    # no error! "Hello, 123!"

# Where annotations are stored
print(f"  __annotations__ = {greet.__annotations__}")
# {'name': str, 'return': str}

# Multiple parameters
def add(a: int, b: int) -> int:
    return a + b

print(f"  add(3, 5) = {add(3, 5)}")
print(f"  add('hello', ' world') = {add('hello', ' world')}")    # still works!
print(f"  add.__annotations__ = {add.__annotations__}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 2. Variable annotations (Python 3.6+)
#
#  variable: Type = value
#  Just a label — no validation, no conversion
# ════════════════════════════════════════════════════

print("2. Variable annotations")

# Annotated variables
name: str = "Alice"
age: int = 30
price: float = 9.99
active: bool = True

print(f"  name: str = {name}")
print(f"  age: int = {age}")
print(f"  price: float = {price}")
print(f"  active: bool = {active}")

# Python does NOT enforce — this "works" (no error)
wrong: int = "this is a string, not int"
print(f"  wrong: int = '{wrong}' (type is actually {type(wrong).__name__})")

# Annotation without value (just declares "this will exist")
future_value: int    # no assignment — variable doesn't exist yet!
# print(future_value)    # NameError! — annotation alone doesn't create the variable

# Module-level annotations are stored here:
import __main__
annotations = getattr(__main__, '__annotations__', {})
print(f"  Module annotations (first 5): {dict(list(annotations.items())[:5])}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 3. Common built-in types for annotations
#
#  str, int, float, bool         → basic types
#  list, dict, tuple, set        → collections (Python 3.9+)
#  list[int], dict[str, int]     → generic collections (3.9+)
#  For Python 3.8: from typing import List, Dict, Tuple, Set
# ════════════════════════════════════════════════════

print("3. Built-in type annotations")

# Basic types
def process_user(name: str, age: int, score: float, active: bool) -> str:
    return f"{name}, {age}, {score}, {active}"

print(f"  {process_user('Alice', 30, 95.5, True)}")

# Collection types (Python 3.9+ syntax)
def sum_scores(scores: list[int]) -> int:
    return sum(scores)

print(f"  sum_scores([10, 20, 30]) = {sum_scores([10, 20, 30])}")

def get_config() -> dict[str, str]:
    return {"host": "localhost", "port": "8000"}

print(f"  get_config() = {get_config()}")

def get_point() -> tuple[int, int]:
    return (10, 20)

print(f"  get_point() = {get_point()}")

def unique_names(names: list[str]) -> set[str]:
    return set(names)

print(f"  unique_names = {unique_names(['Alice', 'Bob', 'Alice'])}")

# Nested collections
def group_scores() -> dict[str, list[int]]:
    return {"math": [90, 85], "english": [78, 92]}

print(f"  group_scores() = {group_scores()}")

# Python 3.8 and earlier — must use typing module
from typing import List, Dict, Tuple, Set

def old_style(items: List[int]) -> Dict[str, int]:
    return {"count": len(items), "sum": sum(items)}

print(f"  old_style([1,2,3]) = {old_style([1, 2, 3])}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 4. Optional — value can be X or None
#
#  Optional[str] means str | None
#  Use when a value might not exist
# ════════════════════════════════════════════════════

print("4. Optional")

from typing import Optional

# Optional = might be None
def find_user(user_id: int) -> Optional[dict]:
    users = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
    return users.get(user_id)    # returns None if not found

print(f"  find_user(1) = {find_user(1)}")
print(f"  find_user(99) = {find_user(99)}")    # None

# Optional parameter with default None
def greet_user(name: str, title: Optional[str] = None) -> str:
    if title:
        return f"Hello, {title} {name}!"
    return f"Hello, {name}!"

print(f"  {greet_user('Alice')}")
print(f"  {greet_user('Alice', 'Dr.')}")

# Python 3.10+ syntax — use | instead of Optional
def find_item(item_id: int) -> dict | None:    # same as Optional[dict]
    items = {1: {"name": "Laptop"}}
    return items.get(item_id)

print(f"  find_item(1) = {find_item(1)}")
print(f"  find_item(99) = {find_item(99)}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 5. Union — value can be one of several types
#
#  Union[str, int] means str OR int
#  Python 3.10+ can use: str | int
# ════════════════════════════════════════════════════

print("5. Union")

from typing import Union

# Accept str OR int
def format_id(user_id: Union[str, int]) -> str:
    return f"USER-{user_id}"

print(f"  format_id(42) = {format_id(42)}")
print(f"  format_id('abc') = {format_id('abc')}")

# Multiple types
def process_input(data: Union[str, int, float, list]) -> str:
    if isinstance(data, list):
        return f"List with {len(data)} items"
    return f"Value: {data} (type: {type(data).__name__})"

print(f"  {process_input('hello')}")
print(f"  {process_input(42)}")
print(f"  {process_input([1, 2, 3])}")

# Python 3.10+ syntax — pipe operator
def flexible(value: str | int | float) -> str:
    return str(value)

print(f"  flexible(42) = {flexible(42)}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 6. Any — accept literally anything
#
#  Any = no type restriction at all
#  Use sparingly — defeats the purpose of type hints
# ════════════════════════════════════════════════════

print("6. Any")

from typing import Any

def log_value(value: Any) -> str:
    return f"Logged: {value} (type: {type(value).__name__})"

print(f"  {log_value('hello')}")
print(f"  {log_value(42)}")
print(f"  {log_value([1, 2, 3])}")
print(f"  {log_value({'key': 'value'})}")

# Any in collections
def store_items(items: list[Any]) -> int:
    return len(items)

print(f"  store_items([1, 'two', 3.0, True]) = {store_items([1, 'two', 3.0, True])}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 7. Callable — annotate functions as parameters
#
#  Callable[[param_types], return_type]
#  Says "this parameter is a function"
# ════════════════════════════════════════════════════

print("7. Callable")

from typing import Callable

# Function that takes a function as parameter
def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

def multiply(x: int, y: int) -> int:
    return x * y

print(f"  apply(multiply, 3, 5) = {apply(multiply, 3, 5)}")

# Callable with no args
def run_task(task: Callable[[], str]) -> str:
    return task()

def hello() -> str:
    return "Hello from task!"

print(f"  run_task(hello) = {run_task(hello)}")

# Callable that takes any args (...)
def execute(func: Callable[..., Any]) -> Any:
    return func()

print(f"  execute(hello) = {execute(hello)}")

# Callback pattern with annotation
def fetch_data(url: str, on_success: Callable[[dict], None], on_error: Callable[[str], None]) -> None:
    try:
        data = {"url": url, "status": 200}
        on_success(data)
    except Exception as e:
        on_error(str(e))

fetch_data(
    "https://api.example.com",
    on_success=lambda d: print(f"  Success: {d}"),
    on_error=lambda e: print(f"  Error: {e}"),
)

print("=" * 60)


# ════════════════════════════════════════════════════
# 8. Literal — restrict to specific values
#
#  Literal["a", "b", "c"] means only those exact values
#  Like an enum but simpler
# ════════════════════════════════════════════════════

print("8. Literal")

from typing import Literal

def set_color(color: Literal["red", "green", "blue"]) -> str:
    return f"Color set to {color}"

print(f"  {set_color('red')}")
print(f"  {set_color('green')}")

# Python won't stop this, but mypy/IDE will warn:
print(f"  {set_color('purple')}")    # "works" but type checker flags it

# Literal with numbers
def set_priority(level: Literal[1, 2, 3]) -> str:
    labels = {1: "High", 2: "Medium", 3: "Low"}
    return labels.get(level, "Unknown")

print(f"  priority(1) = {set_priority(1)}")
print(f"  priority(3) = {set_priority(3)}")

# Literal with bool
def set_mode(mode: Literal["read", "write", "append"]) -> str:
    return f"File opened in {mode} mode"

print(f"  {set_mode('read')}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 9. TypeAlias — give a name to complex types
#
#  Create readable aliases for long/complex type hints
# ════════════════════════════════════════════════════

print("9. TypeAlias")

from typing import TypeAlias

# Without alias — hard to read
def process_v1(data: dict[str, list[tuple[int, str]]]) -> list[dict[str, Any]]:
    return [{"processed": True}]

# With alias — much clearer
UserRecord: TypeAlias = dict[str, list[tuple[int, str]]]
ProcessedResult: TypeAlias = list[dict[str, Any]]

def process_v2(data: UserRecord) -> ProcessedResult:
    return [{"processed": True}]

print(f"  process_v2 result: {process_v2({})}")

# Common aliases
JSON: TypeAlias = dict[str, Any]
Headers: TypeAlias = dict[str, str]
Coordinates: TypeAlias = tuple[float, float]
Matrix: TypeAlias = list[list[int]]

def make_request(url: str, headers: Headers) -> JSON:
    return {"url": url, "headers": headers}

print(f"  {make_request('https://api.com', {'Auth': 'Bearer token'})}")

def distance(point1: Coordinates, point2: Coordinates) -> float:
    return ((point2[0] - point1[0])**2 + (point2[1] - point1[1])**2) ** 0.5

print(f"  distance((0,0), (3,4)) = {distance((0, 0), (3, 4))}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 10. TypedDict — annotate dictionary keys and value types
#
#  Regular dict[str, Any] doesn't specify which keys exist
#  TypedDict defines exact structure
# ════════════════════════════════════════════════════

print("10. TypedDict")

from typing import TypedDict

class UserDict(TypedDict):
    name: str
    age: int
    email: str

def create_user() -> UserDict:
    return {"name": "Alice", "age": 30, "email": "alice@test.com"}

user = create_user()
print(f"  User: {user}")
print(f"  Name: {user['name']}, Age: {user['age']}")

# TypedDict with optional keys (total=False)
class Config(TypedDict, total=False):    # all keys optional
    host: str
    port: int
    debug: bool

def get_config() -> Config:
    return {"host": "localhost"}    # port and debug omitted — OK

print(f"  Config: {get_config()}")

# Mix required and optional
from typing import Required, NotRequired

class APIResponse(TypedDict):
    status: int                       # required
    data: dict                        # required
    error: NotRequired[str]           # optional
    metadata: NotRequired[dict]       # optional

def success_response() -> APIResponse:
    return {"status": 200, "data": {"result": "ok"}}

def error_response() -> APIResponse:
    return {"status": 500, "data": {}, "error": "Server failed"}

print(f"  Success: {success_response()}")
print(f"  Error: {error_response()}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 11. Annotated — attach extra metadata to types
#
#  Annotated[Type, metadata1, metadata2, ...]
#  The extra metadata is ignored by Python
#  But frameworks like FastAPI/Pydantic READ it
# ════════════════════════════════════════════════════

print("11. Annotated")

from typing import Annotated

# Basic Annotated — adds description metadata
def create_item(
    name: Annotated[str, "Item name, max 100 chars"],
    price: Annotated[float, "Price in USD, must be > 0"],
    quantity: Annotated[int, "Stock count, must be >= 0"],
) -> dict:
    return {"name": name, "price": price, "qty": quantity}

print(f"  {create_item('Laptop', 999.99, 10)}")

# Check annotations — metadata is stored but Python ignores it
import typing
print(f"  Annotations: {create_item.__annotations__}")

# Annotated is KEY for FastAPI — this is how FastAPI reads validation rules:
#
# from fastapi import Query, Path, Body
#
# @app.get("/items")
# def get_items(
#     q: Annotated[str, Query(min_length=3, max_length=50)],
#     skip: Annotated[int, Query(ge=0)] = 0,
#     limit: Annotated[int, Query(le=100)] = 10,
# ):
#     return {"q": q, "skip": skip, "limit": limit}
#
# FastAPI reads the Query() metadata and enforces min_length, max_length, etc.
# Without Annotated, you'd write: q: str = Query(min_length=3)

# Annotated with custom metadata class
class Range:
    def __init__(self, min_val: int, max_val: int):
        self.min_val = min_val
        self.max_val = max_val

    def __repr__(self):
        return f"Range({self.min_val}, {self.max_val})"

def set_volume(level: Annotated[int, Range(0, 100)]) -> str:
    return f"Volume set to {level}"

print(f"  {set_volume(75)}")

# Access the metadata
hints = typing.get_type_hints(set_volume, include_extras=True)
print(f"  Type hints with extras: {hints}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 12. Type annotations in classes
# ════════════════════════════════════════════════════

print("12. Class annotations")

# Regular class with annotations
class User:
    name: str
    age: int
    email: str

    def __init__(self, name: str, age: int, email: str) -> None:
        self.name = name
        self.age = age
        self.email = email

    def greet(self) -> str:
        return f"Hi, I'm {self.name}, age {self.age}"

u = User("Alice", 30, "alice@test.com")
print(f"  {u.greet()}")
print(f"  Class annotations: {User.__annotations__}")

# Class variable vs instance variable annotations
class Counter:
    count: int = 0            # class variable (shared by all instances)

    def __init__(self, name: str) -> None:
        self.name: str = name    # instance variable annotation

    def increment(self) -> int:
        Counter.count += 1
        return Counter.count

c1 = Counter("c1")
c2 = Counter("c2")
c1.increment()
c2.increment()
print(f"  Shared count: {Counter.count}")    # 2

print("=" * 60)


# ════════════════════════════════════════════════════
# 13. dataclass — annotations create real attributes
#
#  @dataclass reads annotations and auto-generates:
#  __init__, __repr__, __eq__, and more
#  THIS is where annotations have real power in plain Python
# ════════════════════════════════════════════════════

print("13. dataclass (annotations → real code)")

from dataclasses import dataclass, field

@dataclass
class Product:
    name: str                    # required field
    price: float                 # required field
    quantity: int = 0            # optional with default
    tags: list[str] = field(default_factory=list)    # mutable default

# @dataclass auto-generates __init__ from annotations!
# No need to write def __init__(self, name, price, ...): self.name = name ...

p1 = Product("Laptop", 999.99, 5, ["electronics", "tech"])
p2 = Product("Mouse", 25.0)

print(f"  p1 = {p1}")    # auto-generated __repr__
print(f"  p2 = {p2}")
print(f"  p1 == p2: {p1 == p2}")    # auto-generated __eq__

# Frozen dataclass (immutable)
@dataclass(frozen=True)
class Point:
    x: float
    y: float

pt = Point(3.0, 4.0)
print(f"  Point: {pt}")
# pt.x = 5    # FrozenInstanceError! — immutable

# dataclass with post_init
@dataclass
class Rectangle:
    width: float
    height: float
    area: float = field(init=False)    # computed, not passed to __init__

    def __post_init__(self) -> None:
        self.area = self.width * self.height

r = Rectangle(5.0, 3.0)
print(f"  Rectangle: {r}")    # area auto-computed as 15.0

print("=" * 60)


# ════════════════════════════════════════════════════
# 14. NamedTuple with annotations
#
#  Alternative to collections.namedtuple
#  Uses annotations for field types
# ════════════════════════════════════════════════════

print("14. NamedTuple with annotations")

from typing import NamedTuple

class Coordinate(NamedTuple):
    x: float
    y: float
    label: str = "origin"

c1 = Coordinate(3.0, 4.0, "point A")
c2 = Coordinate(0.0, 0.0)    # uses default label

print(f"  c1 = {c1}")
print(f"  c2 = {c2}")
print(f"  c1.x = {c1.x}, c1.label = {c1.label}")

# Unpack like a tuple
x, y, label = c1
print(f"  Unpacked: x={x}, y={y}, label={label}")

# Immutable — can't change values
# c1.x = 10    # AttributeError!

class APIResult(NamedTuple):
    success: bool
    data: dict
    status_code: int = 200

result = APIResult(True, {"user": "Alice"})
print(f"  API result: {result}")
print(f"  success={result.success}, code={result.status_code}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 15. Generic types — TypeVar
#
#  TypeVar creates a placeholder type
#  "T" means "whatever type the caller passes"
#  Keeps input/output types consistent
# ════════════════════════════════════════════════════

print("15. TypeVar — generic types")

from typing import TypeVar

T = TypeVar("T")    # T = any type

# first() returns the SAME type as the input list contains
def first(items: list[T]) -> T:
    return items[0]

print(f"  first([1, 2, 3]) = {first([1, 2, 3])}")          # int → int
print(f"  first(['a', 'b']) = {first(['a', 'b'])}")         # str → str

# Without TypeVar, you'd need Union or Any — losing type info
# With TypeVar: type checker knows first([1,2,3]) returns int, not Any

# TypeVar with constraints
Number = TypeVar("Number", int, float)    # only int or float

def double(n: Number) -> Number:
    return n * 2

print(f"  double(5) = {double(5)}")
print(f"  double(3.14) = {double(3.14)}")

# TypeVar with bound (must be subclass of...)
from typing import Sized

S = TypeVar("S", bound=Sized)    # must have __len__

def get_length(item: S) -> int:
    return len(item)

print(f"  get_length('hello') = {get_length('hello')}")
print(f"  get_length([1,2,3]) = {get_length([1, 2, 3])}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 16. Protocol — structural typing (duck typing with hints)
#
#  Protocol says "any object with these methods works"
#  Don't need to inherit — just have the right methods
#  "If it walks like a duck and quacks like a duck..."
# ════════════════════════════════════════════════════

print("16. Protocol — structural typing")

from typing import Protocol, runtime_checkable

@runtime_checkable
class Printable(Protocol):
    def to_string(self) -> str: ...    # any class with to_string() matches

class UserP:
    def __init__(self, name: str):
        self.name = name
    def to_string(self) -> str:
        return f"User({self.name})"

class ProductP:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price
    def to_string(self) -> str:
        return f"Product({self.name}, ${self.price})"

# Both match Printable — no inheritance needed!
def display(item: Printable) -> None:
    print(f"  {item.to_string()}")

display(UserP("Alice"))
display(ProductP("Laptop", 999))

# runtime_checkable lets you use isinstance
print(f"  UserP is Printable? {isinstance(UserP('Bob'), Printable)}")
print(f"  str is Printable? {isinstance('hello', Printable)}")

# Protocol with __len__
class HasLength(Protocol):
    def __len__(self) -> int: ...

def show_length(item: HasLength) -> int:
    return len(item)

print(f"  len('hello') = {show_length('hello')}")
print(f"  len([1,2,3]) = {show_length([1, 2, 3])}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 17. Final — mark as constant / not overridable
# ════════════════════════════════════════════════════

print("17. Final")

from typing import Final

# Final variable — should not be reassigned
MAX_RETRIES: Final[int] = 3
API_URL: Final[str] = "https://api.example.com"
PI: Final = 3.14159    # type inferred as float

print(f"  MAX_RETRIES = {MAX_RETRIES}")
print(f"  API_URL = {API_URL}")
print(f"  PI = {PI}")

# Python won't stop you, but mypy will flag this:
# MAX_RETRIES = 5    # mypy error: Cannot assign to final name "MAX_RETRIES"

# Final in class — method can't be overridden by subclass
from typing import final

class Base:
    @final
    def critical_method(self) -> str:
        return "This should NOT be overridden"

    def normal_method(self) -> str:
        return "This CAN be overridden"

b = Base()
print(f"  {b.critical_method()}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 18. ClassVar — class-level variable annotation
#
#  ClassVar[Type] = shared by all instances
#  Not included in dataclass __init__
# ════════════════════════════════════════════════════

print("18. ClassVar")

from typing import ClassVar

@dataclass
class Employee:
    name: str
    salary: float
    company: ClassVar[str] = "Reuters"    # shared, not in __init__
    employee_count: ClassVar[int] = 0     # shared counter

    def __post_init__(self) -> None:
        Employee.employee_count += 1

e1 = Employee("Alice", 90000)
e2 = Employee("Bob", 85000)

print(f"  e1 = {e1}")
print(f"  e2 = {e2}")
print(f"  Company: {Employee.company}")
print(f"  Total employees: {Employee.employee_count}")    # 2

print("=" * 60)


# ════════════════════════════════════════════════════
# 19. get_type_hints() — programmatic access
#
#  typing.get_type_hints() resolves forward refs
#  and returns clean annotation dict
#  Better than __annotations__ for runtime inspection
# ════════════════════════════════════════════════════

print("19. get_type_hints() — runtime inspection")

def process(name: str, age: int, scores: list[float]) -> dict[str, Any]:
    return {"name": name, "age": age, "avg": sum(scores) / len(scores)}

# __annotations__ — raw dict
print(f"  __annotations__: {process.__annotations__}")

# get_type_hints() — resolved and clean
hints = typing.get_type_hints(process)
print(f"  get_type_hints: {hints}")

# Iterate over type hints
for param_name, param_type in hints.items():
    print(f"    {param_name}: {param_type}")

# Practical: auto-validate using annotations
def validate(func: Callable, **kwargs: Any) -> dict[str, bool]:
    hints = typing.get_type_hints(func)
    results = {}
    for name, expected_type in hints.items():
        if name == "return":
            continue
        if name in kwargs:
            results[name] = isinstance(kwargs[name], expected_type)
    return results

check = validate(process, name="Alice", age=30, scores=[90.0, 85.0])
print(f"  Validation: {check}")

check = validate(process, name="Alice", age="thirty", scores="not a list")
print(f"  Bad input: {check}")

print("=" * 60)


# ════════════════════════════════════════════════════
# 20. Forward references — use type before it's defined
#
#  Put type name in quotes: "ClassName"
#  Or use from __future__ import annotations (Python 3.7+)
# ════════════════════════════════════════════════════

print("20. Forward references")

# Problem: Tree refers to itself — doesn't exist yet during definition
# Solution: use string "Tree"
class TreeNode:
    def __init__(self, value: int, children: list["TreeNode"] | None = None):
        self.value = value
        self.children = children or []

    def __repr__(self) -> str:
        if self.children:
            return f"Tree({self.value}, children={self.children})"
        return f"Tree({self.value})"

tree = TreeNode(1, [TreeNode(2), TreeNode(3, [TreeNode(4)])])
print(f"  {tree}")

# Mutual references
class Department:
    def __init__(self, name: str, manager: "ManagerPerson | None" = None):
        self.name = name
        self.manager = manager

    def __repr__(self) -> str:
        mgr = self.manager.name if self.manager else "None"
        return f"Dept({self.name}, manager={mgr})"

class ManagerPerson:
    def __init__(self, name: str, department: Department | None = None):
        self.name = name
        self.department = department

dept = Department("Engineering")
mgr = ManagerPerson("Alice", dept)
dept.manager = mgr
print(f"  {dept}")

# With from __future__ import annotations:
# ALL annotations become strings automatically (lazy evaluation)
# No need for quotes. Uncomment at TOP of file to use:
# from __future__ import annotations

print("=" * 60)


# ════════════════════════════════════════════════════
# 21. Annotations in real frameworks
#
#  Annotations are JUST LABELS in pure Python
#  But frameworks give them POWER:
# ════════════════════════════════════════════════════

print("21. How frameworks use annotations")

# ── PURE PYTHON: annotations do NOTHING ──
def pure_python(name: str, age: int) -> str:
    return f"{name}, {age}"

# These ALL work — no enforcement
print(f"  pure_python(123, 'abc') = {pure_python(123, 'abc')}")
print()

# ── DATACLASS: annotations → auto __init__, __repr__, __eq__ ──
@dataclass
class Item:
    name: str        # @dataclass reads this and creates self.name = name
    price: float     # @dataclass reads this and creates self.price = price

item = Item("Laptop", 999)
print(f"  dataclass reads annotations: {item}")
print()

# ── HOW FASTAPI USES ANNOTATIONS (pseudocode — not runnable without FastAPI) ──
#
# @app.get("/items/{item_id}")
# def get_item(item_id: int, q: str = None):
#     return {"id": item_id, "q": q}
#
# FastAPI reads annotations at startup:
#   1. item_id: int → path parameter, auto-convert to int, reject non-int
#   2. q: str = None → query parameter, optional
#   3. -> dict → response model hint for docs
#
# With Annotated (modern FastAPI):
# @app.get("/users")
# def list_users(
#     skip: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
#     limit: Annotated[int, Query(le=100)] = 10,
# ):
#     ...
#
# FastAPI reads Query() from Annotated and enforces ge=0, le=100
# Without annotations, FastAPI can't know types → no validation, no docs

# ── HOW PYDANTIC USES ANNOTATIONS (runnable) ──
try:
    from pydantic import BaseModel, ValidationError

    class UserModel(BaseModel):
        name: str          # Pydantic reads this → ENFORCES str type
        age: int           # Pydantic reads this → ENFORCES int type
        active: bool = True

    # Valid input
    u1 = UserModel(name="Alice", age=30)
    print(f"  Pydantic valid: {u1}")

    # Auto-conversion — Pydantic converts "25" to int 25
    u2 = UserModel(name="Bob", age="25")
    print(f"  Pydantic auto-convert: {u2}, age type = {type(u2.age).__name__}")

    # Invalid input — Pydantic raises ValidationError
    try:
        u3 = UserModel(name="Charlie", age="not a number")
    except ValidationError as e:
        print(f"  Pydantic error: {e.error_count()} validation error(s)")

except ImportError:
    print("  (pydantic not installed — skipping)")

print("=" * 60)


# ════════════════════════════════════════════════════
# 22. Type checking with mypy
#
#  mypy reads annotations and catches type bugs
#  WITHOUT running the code
#
#  Install: pip install mypy
#  Run:     mypy your_file.py
# ════════════════════════════════════════════════════

print("22. Type checking with mypy (static analysis)")

# These functions are CORRECT — mypy would pass them
def safe_add(a: int, b: int) -> int:
    return a + b

def safe_greet(name: str) -> str:
    return f"Hello, {name}!"

# These would make mypy COMPLAIN (but Python runs them fine):
#
# def buggy() -> int:
#     return "not an int"        # mypy: Incompatible return type
#
# result: int = safe_greet("hi")  # mypy: str assigned to int variable
#
# def process(items: list[int]) -> int:
#     return items + 1            # mypy: unsupported operand types

# mypy helps catch bugs BEFORE you run the code:
#
# $ mypy test.py
# test.py:10: error: Incompatible return value type (got "str", expected "int")
# test.py:12: error: Incompatible types in assignment (expression has type "str", variable has type "int")

print("  mypy checks types WITHOUT running code")
print("  Install: pip install mypy")
print("  Run:     mypy your_file.py")
print("  It catches type bugs before they become runtime errors")

print("=" * 60)


# ════════════════════════════════════════════════════
# 23. Common annotation patterns & best practices
# ════════════════════════════════════════════════════

print("23. Common patterns")

# Pattern 1: Optional with default None
def fetch(url: str, timeout: int | None = None) -> dict:
    t = timeout or 30
    return {"url": url, "timeout": t}

print(f"  {fetch('https://api.com')}")
print(f"  {fetch('https://api.com', 10)}")

# Pattern 2: Return different types
def parse(text: str) -> int | float | str:
    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            return text

print(f"  parse('42') = {parse('42')} ({type(parse('42')).__name__})")
print(f"  parse('3.14') = {parse('3.14')} ({type(parse('3.14')).__name__})")
print(f"  parse('abc') = {parse('abc')} ({type(parse('abc')).__name__})")

# Pattern 3: Dict return with TypedDict
class SearchResult(TypedDict):
    query: str
    results: list[str]
    count: int

def search(query: str) -> SearchResult:
    results = [f"Result for '{query}' #{i}" for i in range(3)]
    return {"query": query, "results": results, "count": len(results)}

print(f"  search('python') = {search('python')}")

# Pattern 4: Decorator preserving annotations
import functools

def logged(func: Callable[..., T]) -> Callable[..., T]:
    @functools.wraps(func)    # preserves __annotations__ and __name__
    def wrapper(*args: Any, **kwargs: Any) -> T:
        print(f"  Calling {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

@logged
def compute(x: int, y: int) -> int:
    return x + y

print(f"  compute(3, 5) = {compute(3, 5)}")
print(f"  Preserved name: {compute.__name__}")
print(f"  Preserved hints: {typing.get_type_hints(compute)}")

print("=" * 60)


# ════════════════════════════════════════════════════
# SUMMARY
#
#  BASICS:
#    param: Type           → annotate parameter
#    -> Type               → annotate return value
#    var: Type = value     → annotate variable
#    func.__annotations__  → stored in dict
#
#  COMMON TYPES:
#    str, int, float, bool     → basic types
#    list[int], dict[str, Any] → collection types (3.9+)
#    tuple[int, str]           → fixed-length tuple
#    set[str]                  → set type
#
#  SPECIAL TYPES (from typing):
#    Optional[X]     → X | None
#    Union[X, Y]     → X or Y (Python 3.10+: X | Y)
#    Any             → any type at all
#    Literal["a","b"] → only specific values
#    Callable[[args], ret] → function type
#    TypeVar("T")    → generic placeholder
#    Final[X]        → constant, don't reassign
#    ClassVar[X]     → class-level, not instance
#    TypeAlias       → name for complex types
#    TypedDict       → dict with specific keys/types
#    Annotated[X, meta] → type + extra metadata
#    Protocol        → structural typing (duck typing)
#    NamedTuple      → annotated named tuple
#
#  FORWARD REFERENCES:
#    "ClassName"                → use type before it's defined
#    from __future__ import annotations → auto string all annotations
#
#  KEY INSIGHT:
#    Pure Python   → annotations are IGNORED (just labels)
#    dataclass     → annotations CREATE __init__, __repr__
#    FastAPI       → annotations VALIDATE & CONVERT request data
#    Pydantic      → annotations ENFORCE types at runtime
#    mypy          → annotations CHECKED statically (no runtime)
#
#  TOOLS:
#    mypy your_file.py   → static type checking
#    pyright              → faster alternative to mypy
#    IDE (VSCode/PyCharm) → real-time type checking
# ════════════════════════════════════════════════════
