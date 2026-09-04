# ══════════════════════════════════════════════════════════════════
#  PYDANTIC — Condensed Guide (Pure Python, no FastAPI)
#  Pydantic = data validation & parsing using Python type hints
#  Instead of manually checking types, lengths, formats,
#  Pydantic does it automatically and gives clear errors
# ══════════════════════════════════════════════════════════════════
from pydantic import (
    BaseModel, Field, field_validator, model_validator,
    ConfigDict, EmailStr, computed_field, ValidationError,
    field_serializer, model_serializer,
)
from typing import Optional, Literal
from datetime import datetime, date
from enum import Enum

# ╔══════════════════════════════════════════════════╗
# ║                  BEGINNER                        ║
# ╚══════════════════════════════════════════════════╝

# ── 1. The Problem — Why Pydantic? ────────────────
# Without Pydantic: manual checks everywhere, easy to miss things

def create_user_manual(data: dict):
    if not isinstance(data.get("name"), str):
        raise ValueError("name must be a string")
    if not isinstance(data.get("age"), int):
        raise ValueError("age must be an int")
    if data["age"] < 0:
        raise ValueError("age must be positive")
    # ... 50 more checks for every field ...
    return data

# With Pydantic: declare the shape, validation is automatic
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

user = User(name="Alice", age=30)
print(user)          # name='Alice' age=30
print(user.name)     # Alice
print(user.age)      # 30

# ── 2. Automatic Type Coercion ───────────────────
# Pydantic CONVERTS compatible types (str→int, int→float, etc.)

user2 = User(name="Bob", age="25")     # "25" → 25 (str→int)
print(user2.age)                        # 25 (int, not str!)
print(type(user2.age))                  # <class 'int'>

# but it won't force impossible conversions:
try:
    User(name="Charlie", age="not_a_number")
except ValidationError as e:
    print(e)
    # Input should be a valid integer, unable to parse string as an integer

# ── 3. Validation Errors ────────────────────────
# Missing fields, wrong types → clear error messages

try:
    User(name="Dave")   # missing 'age'
except ValidationError as e:
    print(e)
    # age - Field required

try:
    User(name=123, age="abc")
except ValidationError as e:
    print(e.error_count())    # 1 (name coerces 123→"123", age fails)
    for err in e.errors():
        print(f"  {err['loc']}: {err['msg']}")

# ── 4. Optional & Default Values ─────────────────

class UserWithDefaults(BaseModel):
    name: str
    age: int = 0                        # default value
    email: Optional[str] = None         # optional, defaults to None
    role: str = "user"                  # default

u1 = UserWithDefaults(name="Eve")
print(u1)   # name='Eve' age=0 email=None role='user'

u2 = UserWithDefaults(name="Frank", age=28, email="frank@example.com")
print(u2)   # name='Frank' age=28 email='frank@example.com' role='user'

# ── 5. Nested Models ────────────────────────────
# Models inside models — validated recursively

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class Employee(BaseModel):
    name: str
    address: Address           # nested model

emp = Employee(
    name="Grace",
    address={"street": "123 Main St", "city": "Springfield", "zip_code": "62701"}
)
print(emp.address.city)        # Springfield
# the dict is automatically parsed into an Address object!

# ── 6. Model Methods — .model_dump() & .model_validate() ─

class Product(BaseModel):
    name: str
    price: float
    in_stock: bool = True

p = Product(name="Widget", price=9.99)

# model → dict
data = p.model_dump()
print(data)   # {'name': 'Widget', 'price': 9.99, 'in_stock': True}

# dict → model
p2 = Product.model_validate({"name": "Gadget", "price": 19.99})
print(p2)     # name='Gadget' price=19.99 in_stock=True

# model → JSON string
json_str = p.model_dump_json()
print(json_str)   # {"name":"Widget","price":9.99,"in_stock":true}

# JSON string → model
p3 = Product.model_validate_json('{"name": "Doohickey", "price": 5.0}')
print(p3)         # name='Doohickey' price=5.0 in_stock=True

# ── 7. List & Dict Fields ───────────────────────

class Team(BaseModel):
    name: str
    members: list[str]
    scores: dict[str, int]

team = Team(
    name="Alpha",
    members=["Alice", "Bob", "Charlie"],
    scores={"Alice": 95, "Bob": 87, "Charlie": 92}
)
print(team.members[0])        # Alice
print(team.scores["Bob"])     # 87


# ╔══════════════════════════════════════════════════╗
# ║               INTERMEDIATE                       ║
# ╚══════════════════════════════════════════════════╝

# ── 8. Field() — Constraints & Metadata ──────────
# Field() adds validation rules: min, max, length, regex, etc.

class Item(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, description="Price must be positive")
    quantity: int = Field(ge=0, le=10000, default=0)
    tags: list[str] = Field(default_factory=list, max_length=10)

item = Item(name="Laptop", price=999.99, quantity=5, tags=["electronics"])
print(item)

try:
    Item(name="", price=-10, quantity=-1)
except ValidationError as e:
    for err in e.errors():
        print(f"  {err['loc']}: {err['msg']}")
    # ('name',): String should have at least 1 character
    # ('price',): Input should be greater than 0
    # ('quantity',): Input should be greater than or equal to 0

# ── 9. field_validator — Custom Validation ───────
# Add your own validation logic per field

class SignupForm(BaseModel):
    username: str
    password: str
    age: int

    @field_validator("username")
    @classmethod
    def username_must_be_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError("username must be alphanumeric")
        return v.lower()    # transform: always lowercase

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("password must contain an uppercase letter")
        return v

signup = SignupForm(username="Alice123", password="SecurePass1", age=25)
print(signup.username)   # alice123 (lowercased by validator)

try:
    SignupForm(username="bad user!", password="short", age=25)
except ValidationError as e:
    for err in e.errors():
        print(f"  {err['loc']}: {err['msg']}")

# ── 10. model_validator — Cross-Field Validation ─
# Validate fields that depend on EACH OTHER

class DateRange(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def end_after_start(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self

valid = DateRange(start_date="2024-01-01", end_date="2024-12-31")
print(valid)

try:
    DateRange(start_date="2024-12-31", end_date="2024-01-01")
except ValidationError as e:
    print(e)   # end_date must be after start_date

# ── 11. Enum Fields & Literal ────────────────────

class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class Account(BaseModel):
    name: str
    status: Status
    priority: Literal["low", "medium", "high"]   # only these 3 values

acc = Account(name="Acme", status="active", priority="high")
print(acc.status)          # Status.ACTIVE
print(acc.status.value)    # active
print(acc.priority)        # high

try:
    Account(name="Bad", status="deleted", priority="urgent")
except ValidationError as e:
    for err in e.errors():
        print(f"  {err['loc']}: {err['msg']}")

# ── 12. computed_field — Derived Properties ──────
# Fields calculated from other fields, included in serialization

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

    @computed_field
    @property
    def perimeter(self) -> float:
        return 2 * (self.width + self.height)

rect = Rectangle(width=5, height=3)
print(rect.area)           # 15.0
print(rect.perimeter)      # 16.0
print(rect.model_dump())   # {'width': 5.0, 'height': 3.0, 'area': 15.0, 'perimeter': 16.0}

# ── 13. Immutable Models (frozen) ────────────────
# Prevent modification after creation

class Config(BaseModel):
    model_config = ConfigDict(frozen=True)

    db_host: str
    db_port: int = 5432

config = Config(db_host="localhost")
print(config.db_host)       # localhost

try:
    config.db_host = "remote"   # can't modify!
except ValidationError as e:
    print("Cannot modify frozen model")

# ── 14. Model Inheritance ────────────────────────

class BaseUser(BaseModel):
    id: int
    name: str
    email: str

class AdminUser(BaseUser):
    permissions: list[str]
    department: str

class GuestUser(BaseUser):
    expires_at: datetime
    access_level: Literal["read", "write"] = "read"

admin = AdminUser(
    id=1, name="Admin", email="admin@co.com",
    permissions=["create", "delete"], department="IT"
)
guest = GuestUser(
    id=2, name="Guest", email="guest@co.com",
    expires_at="2025-12-31T23:59:59"
)
print(admin)
print(guest)
print(isinstance(admin, BaseUser))   # True

# ── 15. Aliases — Different Names for Input/Output ─
# API sends "firstName" but you want "first_name" in Python

class APIResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email_address: str = Field(alias="emailAddress")

# works with alias (from API)
resp = APIResponse(firstName="Jane", lastName="Doe", emailAddress="jane@co.com")
print(resp.first_name)     # Jane

# also works with Python name (populate_by_name=True)
resp2 = APIResponse(first_name="John", last_name="Smith", email_address="john@co.com")
print(resp2.first_name)    # John

# serialize with aliases
print(resp.model_dump(by_alias=True))
# {'firstName': 'Jane', 'lastName': 'Doe', 'emailAddress': 'jane@co.com'}


# ╔══════════════════════════════════════════════════╗
# ║                  ADVANCED                        ║
# ╚══════════════════════════════════════════════════╝

# ── 16. Discriminated Unions — Polymorphic Models ─
# Different model types in the same field, chosen by a "type" field

from typing import Annotated, Union

class CreditCard(BaseModel):
    type: Literal["credit_card"]
    card_number: str
    cvv: str

class BankTransfer(BaseModel):
    type: Literal["bank_transfer"]
    account_number: str
    routing_number: str

class PayPal(BaseModel):
    type: Literal["paypal"]
    email: str

PaymentMethod = Annotated[
    Union[CreditCard, BankTransfer, PayPal],
    Field(discriminator="type")
]

class Order(BaseModel):
    order_id: int
    payment: PaymentMethod

# Pydantic picks the right model based on "type"
o1 = Order(order_id=1, payment={"type": "credit_card", "card_number": "4111...", "cvv": "123"})
o2 = Order(order_id=2, payment={"type": "paypal", "email": "user@co.com"})

print(type(o1.payment))   # <class 'CreditCard'>
print(type(o2.payment))   # <class 'PayPal'>

# ── 17. Custom Serialization ────────────────────
# Control how fields are exported to dict/JSON

class Event(BaseModel):
    name: str
    timestamp: datetime

    @field_serializer("timestamp")
    def serialize_timestamp(self, v: datetime, _info):
        return v.strftime("%Y-%m-%d %H:%M")

event = Event(name="Launch", timestamp="2025-06-15T14:30:00")
print(event.model_dump())
# {'name': 'Launch', 'timestamp': '2025-06-15 14:30'}

# ── 18. Strict Mode — No Coercion ───────────────
# By default Pydantic coerces "25" → 25
# Strict mode: "25" stays str → validation error

class StrictUser(BaseModel):
    model_config = ConfigDict(strict=True)

    name: str
    age: int

strict_user = StrictUser(name="Alice", age=30)   # OK
print(strict_user)

try:
    StrictUser(name="Bob", age="25")   # FAILS in strict mode!
except ValidationError as e:
    print("Strict mode: str not accepted for int field")

# ── 19. model_validator mode="before" — Raw Data ─
# Validate/transform data BEFORE Pydantic parses it

class FlexibleUser(BaseModel):
    name: str
    age: int

    @model_validator(mode="before")
    @classmethod
    def handle_full_name(cls, data):
        if isinstance(data, dict) and "full_name" in data:
            data["name"] = data.pop("full_name")
        return data

u = FlexibleUser(full_name="Alice Smith", age=30)
print(u.name)   # Alice Smith

# ── 20. Generic Models ──────────────────────────
# Reusable model templates with type parameters

from typing import Generic, TypeVar

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int

    @computed_field
    @property
    def total_pages(self) -> int:
        return (self.total + self.per_page - 1) // self.per_page

# use with any model
class UserItem(BaseModel):
    name: str
    email: str

response = PaginatedResponse[UserItem](
    items=[
        {"name": "Alice", "email": "alice@co.com"},
        {"name": "Bob", "email": "bob@co.com"},
    ],
    total=50,
    page=1,
    per_page=10,
)
print(response.total_pages)   # 5
print(response.items[0].name) # Alice

# ── 21. JSON Schema Generation ──────────────────
# Pydantic models can generate JSON schemas (useful for APIs, docs)

class Task(BaseModel):
    """A task in the todo list."""
    title: str = Field(description="Task title", examples=["Buy groceries"])
    done: bool = Field(default=False, description="Completion status")
    priority: Literal["low", "medium", "high"] = "medium"

import json
schema = Task.model_json_schema()
print(json.dumps(schema, indent=2))
# generates full JSON Schema with types, descriptions, examples, etc.

# ── 22. Custom Types with Annotated ─────────────
# Create reusable validation rules

from pydantic import AfterValidator
from typing import Annotated

def must_be_positive(v: int) -> int:
    if v <= 0:
        raise ValueError("must be positive")
    return v

PositiveInt = Annotated[int, AfterValidator(must_be_positive)]

class Invoice(BaseModel):
    amount: PositiveInt
    quantity: PositiveInt

inv = Invoice(amount=100, quantity=5)
print(inv)

try:
    Invoice(amount=-50, quantity=0)
except ValidationError as e:
    for err in e.errors():
        print(f"  {err['loc']}: {err['msg']}")


# ══════════════════════════════════════════════════════════════════
#  CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
#
#  BASICS:
#    class MyModel(BaseModel):       define a model
#    field: type                     required field
#    field: type = default           field with default
#    field: Optional[type] = None    optional field
#
#  CREATING INSTANCES:
#    m = MyModel(field=value)        from kwargs
#    m = MyModel.model_validate(d)   from dict
#    m = MyModel.model_validate_json(s)  from JSON string
#
#  EXPORTING:
#    m.model_dump()                  → dict
#    m.model_dump(by_alias=True)     → dict with alias names
#    m.model_dump(exclude={"field"}) → dict without field
#    m.model_dump_json()             → JSON string
#
#  FIELD CONSTRAINTS (Field()):
#    gt, ge, lt, le                  numeric bounds
#    min_length, max_length          string/list length
#    pattern                         regex pattern
#    default, default_factory        default values
#    alias                           alternative input name
#
#  VALIDATORS:
#    @field_validator("field")       validate one field
#    @model_validator(mode="after")  validate across fields (parsed data)
#    @model_validator(mode="before") validate/transform raw input
#
#  SERIALIZATION:
#    @field_serializer("field")      custom field output
#    @computed_field + @property     derived field in output
#
#  CONFIG (model_config = ConfigDict(...)):
#    frozen=True                     immutable model
#    strict=True                     no type coercion
#    populate_by_name=True           allow both alias & field name
#    str_strip_whitespace=True       auto-strip strings
#    extra="forbid"                  error on unknown fields
#
#  ADVANCED:
#    Generic[T]                      reusable model templates
#    Literal["a","b"]                restrict to specific values
#    Annotated[type, validator]      reusable custom types
#    Field(discriminator="type")     polymorphic unions
#    model_json_schema()             generate JSON Schema
#
#  KEY RULES:
#    Pydantic v2 uses model_dump()   not .dict() (v1)
#    Pydantic v2 uses model_validate()  not .parse_obj() (v1)
#    field_validator replaces         @validator (v1)
#    model_validator replaces         @root_validator (v1)
#    ConfigDict replaces              class Config (v1)
# ══════════════════════════════════════════════════════════════════

# ╔══════════════════════════════════════════════════╗
# ║          INTERVIEW GOTCHAS                       ║
# ╚══════════════════════════════════════════════════╝

# ── Q: What's the difference between Pydantic v1 and v2? ──
# v2: rewritten in Rust (faster), new API names:
#   .dict() → .model_dump()
#   .parse_obj() → .model_validate()
#   @validator → @field_validator
#   @root_validator → @model_validator
#   class Config → model_config = ConfigDict(...)
# v2 is 5-50x faster than v1

# ── Q: Does Pydantic validate at assignment or creation? ──
# By default: only at creation (MyModel(field=value))
# After creation: m.field = "bad" → NO validation
# To validate on assignment: model_config = ConfigDict(validate_assignment=True)

# ── Q: BaseModel vs dataclass — when to use which? ──
# BaseModel → validation, serialization, APIs, external data
# dataclass → internal data structures, no validation needed
# Pydantic also has @pydantic.dataclass — dataclass syntax + validation

# ── Q: What does model_validate() do vs __init__? ──
# Both validate. model_validate() accepts dict/object, __init__() accepts kwargs
# model_validate() also handles nested parsing and ORM objects

# ── Q: How does Pydantic handle extra fields? ──
# Default: extra fields are IGNORED (silently dropped)
# extra="forbid" → raises error on unknown fields
# extra="allow" → stores extra fields in model.__pydantic_extra__

# ── Q: Can Pydantic validate function arguments? ──
# Yes — use @pydantic.validate_call:
#   from pydantic import validate_call
#   @validate_call
#   def greet(name: str, age: int) -> str:
#       return f"Hi {name}, age {age}"
#   greet("Alice", "30")  # "30" → 30 automatically
