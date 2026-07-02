# ══════════════════════════════════════════════════════════════════
# PYTHON OOP — Complete Guide (Condensed)
#
# Class = blueprint/template  |  Object = instance from a class
# 4 Pillars: Encapsulation, Inheritance, Polymorphism, Abstraction
# ══════════════════════════════════════════════════════════════════

# ╔══════════════════════════════════════════════════╗
# ║                  BEGINNER                        ║
# ╚══════════════════════════════════════════════════╝

# ── 1. Basic Class & Object ──────────────────────────────
class Car:
    def __init__(self, brand, color):  # constructor
        self.brand = brand             # instance variable
        self.color = color
    def describe(self):
        return f"{self.color} {self.brand}"

car1, car2 = Car("Toyota", "Red"), Car("Honda", "Blue")
print(car1.describe())  # Red Toyota
car1.color = "Black"
print(car1.describe())  # Black Toyota  (car2 unchanged — separate objects)

# ── 2. Instance vs Class Variables ──────────────────────────────
class Employee:
    company = "Reuters"    # class var — shared by ALL instances
    count = 0
    def __init__(self, name, salary):
        self.name = name   # instance var — unique per object
        self.salary = salary
        Employee.count += 1

emp1, emp2 = Employee("Alice", 50000), Employee("Bob", 60000)
print(emp1.name, emp2.name)       # Alice Bob  (instance — different)
print(emp1.company, emp2.company) # Reuters Reuters  (class — same)
print(Employee.count)             # 2

# ── 3. Methods: Instance vs Class vs Static ──────────────────────────────
#  instance  — def method(self)     works on ONE object
#  class     — @classmethod         works on the CLASS (cls), alt constructors
#  static    — @staticmethod        utility, no self/cls
class Pizza:
    base_price = 10
    def __init__(self, size, toppings):
        self.size, self.toppings = size, toppings
    def get_price(self):                          # instance method
        return Pizza.base_price + len(self.toppings) * 2
    @classmethod
    def set_base_price(cls, price):               # class method
        cls.base_price = price
    @classmethod
    def margherita(cls):                           # alt constructor
        return cls("Medium", ["cheese", "tomato"])
    @staticmethod
    def is_valid_size(size):                       # static
        return size in ["Small", "Medium", "Large"]

p1 = Pizza("Large", ["cheese", "mushroom", "olive"])
print(p1.get_price())              # 16  (10 + 3*2)
Pizza.set_base_price(12)
print(p1.get_price())              # 18  (12 + 3*2) — changed for ALL
print(Pizza.margherita().toppings) # ['cheese', 'tomato']
print(Pizza.is_valid_size("Huge")) # False

# ── 4. Encapsulation & Property ──────────────────────────────
#  public    name    — anyone can access
#  protected _name   — convention: "internal use"
#  private   __name  — name-mangled to _ClassName__name
#  @property         — getter/setter/deleter as attribute syntax
class BankAccount:
    def __init__(self, owner, balance):
        self.owner = owner        # public
        self._bank = "Chase"      # protected (convention)
        self.__balance = balance   # private (mangled)
    @property
    def balance(self):
        return self.__balance
    @balance.setter
    def balance(self, amount):
        if amount < 0: raise ValueError("Balance cannot be negative")
        self.__balance = amount
    def deposit(self, amount):
        if amount > 0: self.__balance += amount
        return self.__balance

acc = BankAccount("Alice", 1000)
print(acc.owner)                    # Alice  (public)
print(acc._bank)                    # Chase  (protected — works but discouraged)
# print(acc.__balance)              # AttributeError!
print(acc._BankAccount__balance)    # 1000  (name mangling — not recommended)
print(acc.balance)                  # 1000  (property getter)
acc.balance = 2000                  # property setter
print(acc.deposit(500))             # 2500
try:
    acc.balance = -500
except ValueError as e:
    print(f"Error: {e}")            # Balance cannot be negative

# Computed properties — no stored value
class Temperature:
    def __init__(self, celsius): self._celsius = celsius
    @property
    def fahrenheit(self):       return (self._celsius * 9/5) + 32
    @fahrenheit.setter
    def fahrenheit(self, v):    self._celsius = (v - 32) * 5/9

temp = Temperature(100)
print(temp.fahrenheit)   # 212.0
temp.fahrenheit = 32
print(temp._celsius)     # 0.0

# ╔══════════════════════════════════════════════════╗
# ║                INTERMEDIATE                      ║
# ╚══════════════════════════════════════════════════╝

# ── 5. Inheritance — Single ──────────────────────────────
class Animal:
    def __init__(self, name, sound):
        self.name, self.sound = name, sound
    def speak(self):  return f"{self.name} says {self.sound}!"
    def info(self):   return f"Animal: {self.name}"

class Dog(Animal):
    def __init__(self, name, breed):
        super().__init__(name, "Woof")  # call parent __init__
        self.breed = breed
    def info(self):  return f"Dog: {self.name}, Breed: {self.breed}"  # override

class Cat(Animal):
    def __init__(self, name): super().__init__(name, "Meow")

dog, cat = Dog("Rex", "Labrador"), Cat("Whiskers")
print(dog.speak())  # Rex says Woof!       (inherited)
print(dog.info())   # Dog: Rex, Breed: ... (overridden)
print(cat.info())   # Animal: Whiskers     (parent's)
print(isinstance(dog, Animal), isinstance(cat, Dog))  # True False

# ── 6. Multi-Level & Multiple Inheritance ──────────────────────────────
# Multi-level: Vehicle -> ElectricVehicle -> Tesla
class Vehicle:
    def __init__(self, brand): self.brand = brand
    def start(self): return f"{self.brand} starting..."
class ElectricVehicle(Vehicle):
    def __init__(self, brand, bat):
        super().__init__(brand); self.battery = bat
    def charge(self): return f"Charging {self.brand} ({self.battery}kWh)"
class Tesla(ElectricVehicle):
    def __init__(self, model, bat):
        super().__init__("Tesla", bat); self.model = model

t = Tesla("Model 3", 75)
print(t.start())   # Tesla starting...  (grandparent)
print(t.charge())  # Charging Tesla...  (parent)
print(Tesla.__mro__)  # Tesla -> ElectricVehicle -> Vehicle -> object

# Multiple: two parents — MRO decides conflict winner
class Flyable:
    def move(self): return "Flying"
class Swimmable:
    def move(self): return "Swimming"
class Duck(Flyable, Swimmable): pass  # Flyable listed first

duck = Duck()
print(duck.move())   # Flying  (Flyable wins — listed first)

# ── 7. Polymorphism ──────────────────────────────
class Circle:
    def __init__(self, r):    self.r = r
    def area(self):           return 3.14 * self.r ** 2
class Rectangle:
    def __init__(self, w, h): self.w, self.h = w, h
    def area(self):           return self.w * self.h
class Triangle:
    def __init__(self, b, h): self.b, self.h = b, h
    def area(self):           return 0.5 * self.b * self.h

for s in [Circle(5), Rectangle(4, 6), Triangle(3, 8)]:
    print(f"{s.__class__.__name__} -> {s.area()}")  # 78.5, 24, 12.0

# ── 8. Abstraction — ABC ──────────────────────────────
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self): pass         # child MUST implement
    @abstractmethod
    def perimeter(self): pass
    def description(self):        # concrete — inherited as-is
        return f"I am a {self.__class__.__name__}"

class Square(Shape):
    def __init__(self, side): self.side = side
    def area(self):           return self.side ** 2
    def perimeter(self):      return 4 * self.side

# Shape()  # TypeError: Can't instantiate abstract class
sq = Square(5)
print(sq.area(), sq.perimeter(), sq.description())  # 25 20 I am a Square

# ── 9. Magic / Dunder Methods ──────────────────────────────
class Product:
    def __init__(self, name, price):
        self.name, self.price = name, price
    def __str__(self):        return f"{self.name}: ${self.price}"           # print()
    def __repr__(self):       return f"Product('{self.name}', {self.price})" # debug
    def __eq__(self, other):  return self.name == other.name and self.price == other.price
    def __lt__(self, other):  return self.price < other.price               # enables sort
    def __add__(self, other): return Product(f"{self.name}+{other.name}", self.price + other.price)
    def __len__(self):        return len(self.name)
    def __bool__(self):       return self.price > 0

p1, p2 = Product("Laptop", 999), Product("Mouse", 25)
print(p1)                # Laptop: $999          (__str__)
print(repr(p2))          # Product('Mouse', 25)  (__repr__)
print(p1 == Product("Laptop", 999))  # True      (__eq__)
print(p2 < p1)           # True  (25 < 999)      (__lt__)
print(p1 + p2)           # Laptop+Mouse: $1024   (__add__)
print(len(p1))           # 6                     (__len__)
print(bool(Product("Free", 0)))  # False         (__bool__)

# ── 10. Subscriptable Objects ──────────────────────────────
class Inventory:
    def __init__(self):          self._items = {}
    def __getitem__(self, k):    return self._items.get(k, "Not found")
    def __setitem__(self, k, v): self._items[k] = v
    def __delitem__(self, k):
        if k in self._items: del self._items[k]
    def __contains__(self, k):   return k in self._items
    def __len__(self):           return len(self._items)
    def __iter__(self):          return iter(self._items)

inv = Inventory()
inv["laptop"] = 5; inv["mouse"] = 20  # __setitem__
print(inv["laptop"])      # 5     (__getitem__)
print("mouse" in inv)     # True  (__contains__)
del inv["mouse"]          #       (__delitem__)
print(len(inv))           # 1     (__len__)

# ── 11. Composition — "has a" vs "is a" ──────────────────────────────
class Engine:
    def __init__(self, hp): self.hp, self.running = hp, False
    def start(self):        self.running = True; return f"Engine ({self.hp}hp) started"
class GPS:
    def navigate(self, dest): return f"Navigating to {dest}..."

class MyCar:  # Car HAS an Engine + GPS (composition > inheritance)
    def __init__(self, brand, hp):
        self.brand, self.engine, self.gps = brand, Engine(hp), GPS()
    def start(self):    return f"{self.brand}: {self.engine.start()}"
    def go_to(self, p): return self.gps.navigate(p) if self.engine.running else "Start first!"

my_car = MyCar("BMW", 300)
print(my_car.start())           # BMW: Engine (300hp) started
print(my_car.go_to("Airport"))  # Navigating to Airport...

# ╔══════════════════════════════════════════════════╗
# ║                  ADVANCED                        ║
# ╚══════════════════════════════════════════════════╝

# ── 12. Dataclass ──────────────────────────────
from dataclasses import dataclass, field

@dataclass
class User:
    name: str; email: str; age: int
    active: bool = True
    tags: list = field(default_factory=list)  # mutable default

u1 = User("Alice", "a@test.com", 30)
print(u1)           # User(name='Alice', ...) — auto __repr__
print(u1 == User("Alice", "a@test.com", 30))  # True — auto __eq__

@dataclass
class Point:
    x: float; y: float
    def distance(self): return (self.x**2 + self.y**2) ** 0.5
print(Point(3, 4).distance())  # 5.0

@dataclass(frozen=True)   # immutable — can't change after creation
class Color:
    r: int; g: int; b: int
# Color(255,0,0).r = 100  # FrozenInstanceError!

@dataclass(order=True)    # enables <, >, sorted()
class Score:
    value: int; player: str = ""
print(sorted([Score(85,"A"), Score(92,"B"), Score(78,"C")]))  # [78, 85, 92]

# ── 13. __slots__ — Memory Optimization ──────────────────────────────
class WithSlots:
    __slots__ = ("x", "y")  # fixed attrs — no __dict__, ~40% less memory
    def __init__(self, x, y): self.x, self.y = x, y

b = WithSlots(1, 2)
# b.z = 3    # AttributeError! z not in __slots__
# b.__dict__ # AttributeError — no __dict__ with slots

# ── 14. Mixins — Reusable Behavior ──────────────────────────────
import json

class JsonMixin:
    def to_json(self):     return json.dumps(self.__dict__, indent=2)
    @classmethod
    def from_json(cls, s): return cls(**json.loads(s))

class PrintableMixin:
    def print_info(self):
        attrs = ", ".join(f"{k}={v}" for k, v in self.__dict__.items())
        print(f"[{self.__class__.__name__}] {attrs}")

class Article(JsonMixin, PrintableMixin):
    def __init__(self, title, author, words=0):
        self.title, self.author, self.words = title, author, words

art = Article("Breaking News", "Alice", 500)
art.print_info()  # [Article] title=Breaking News, author=Alice, words=500
Article.from_json('{"title":"Update","author":"Bob","words":300}').print_info()

# ── 15. Enum — Named Constants ──────────────────────────────
from enum import Enum, auto

class Status(Enum):
    PENDING = "pending"; ACTIVE = "active"; INACTIVE = "inactive"
class Priority(Enum):
    LOW = auto(); MEDIUM = auto(); HIGH = auto()  # auto: 1, 2, 3

print(Status.ACTIVE.value)   # active
print(Priority.HIGH.value)   # 3

# ── 16. Method Chaining — return self ──────────────────────────────
class QueryBuilder:
    def __init__(self, table):
        self.table, self._conds, self._order, self._limit = table, [], None, None
    def where(self, c):   self._conds.append(c); return self
    def order_by(self, c): self._order = c; return self
    def limit(self, n):   self._limit = n; return self
    def build(self):
        q = f"SELECT * FROM {self.table}"
        if self._conds: q += " WHERE " + " AND ".join(self._conds)
        if self._order: q += f" ORDER BY {self._order}"
        if self._limit: q += f" LIMIT {self._limit}"
        return q

q = QueryBuilder("users").where("age > 18").where("active = true").order_by("name").limit(10).build()
print(q)  # SELECT * FROM users WHERE age > 18 AND active = true ORDER BY name LIMIT 10

# ── 17. Context Manager — __enter__ / __exit__ ──────────────────────────────
class FileLogger:
    def __init__(self, fn): self.fn, self.logs = fn, []
    def __enter__(self):
        print(f"Logger started for {self.fn}"); return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Logger finished. {len(self.logs)} logs.")
        return False  # don't suppress exceptions
    def log(self, msg):
        self.logs.append(msg); print(f"  LOG: {msg}")

with FileLogger("app.log") as logger:
    logger.log("Started"); logger.log("Logged in")

# ── 18. Singleton — Only ONE Instance ──────────────────────────────
class Database:
    _instance = None
    def __new__(cls, *args, **kwargs):
        if cls._instance is None: cls._instance = super().__new__(cls)
        return cls._instance
    def __init__(self, host="localhost"): self.host = host

db1, db2 = Database("server1"), Database("server2")
print(db1 is db2)  # True — same object!
print(db1.host)    # server2 — last __init__ overwrote

# ── 19. __call__ — Callable Object ──────────────────────────────
class Multiplier:
    def __init__(self, factor):  self.factor = factor
    def __call__(self, value):   return value * self.factor

double = Multiplier(2)
print(double(5))          # 10
print(callable(double))   # True

# ── 20. Descriptor — Reusable Attribute Logic ──────────────────────────────
class PositiveNumber:
    def __set_name__(self, owner, name): self.name = name
    def __get__(self, obj, typ=None):    return getattr(obj, f"_{self.name}", 0)
    def __set__(self, obj, value):
        if value < 0: raise ValueError(f"{self.name} must be positive, got {value}")
        setattr(obj, f"_{self.name}", value)

class Order:
    quantity = PositiveNumber()
    price = PositiveNumber()
    def __init__(self, item, qty, price):
        self.item, self.quantity, self.price = item, qty, price
    def total(self): return self.quantity * self.price

order = Order("Widget", 5, 9.99)
print(order.total())  # 49.95
try:    order.quantity = -3
except ValueError as e: print(f"Error: {e}")  # quantity must be positive

# ── 21. isinstance / issubclass ──────────────────────────────
class Media: pass
class Video(Media): pass
class Audio(Media): pass
class Podcast(Audio): pass

print(isinstance(Video(), Media))      # True  — Video IS-A Media
print(isinstance(Podcast(), Audio))    # True  — Podcast IS-A Audio
print(issubclass(Podcast, Media))      # True  — Podcast -> Audio -> Media
print(issubclass(Video, Audio))        # False

# ── 22. __init_subclass__ — Auto-Register Subclasses ──────────────────────────────
class Plugin:
    registry = []
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.registry.append(cls.__name__)

class PDFExporter(Plugin): pass
class CSVExporter(Plugin): pass
class XMLExporter(Plugin): pass
print(Plugin.registry)  # ['PDFExporter', 'CSVExporter', 'XMLExporter']

# ╔══════════════════════════════════════════════════╗
# ║               CHEAT SHEET                        ║
# ╚══════════════════════════════════════════════════╝
# CLASS BASICS:    class Foo | __init__(self) | self.x (instance) | Foo.x (class)
# METHOD TYPES:    def m(self) instance | @classmethod def(cls) | @staticmethod def()
# ACCESS CONTROL:  name (public) | _name (protected) | __name (private/mangled)
# PROPERTY:        @property getter | @x.setter | @x.deleter — attr syntax
# INHERITANCE:     class B(A) single | class C(B) multi-level | class D(A,B) multiple
#                  super().__init__() | __mro__ resolution order
# POLYMORPHISM:    same method name, different behavior per class
# ABSTRACTION:     ABC + @abstractmethod — must implement in child
# DUNDERS:         __str__ print | __repr__ debug | __eq__ == | __lt__ < (sort)
#                  __add__ + | __len__ len() | __bool__ bool() | __call__ obj()
#                  __getitem__ obj[k] | __setitem__ obj[k]=v | __contains__ in
#                  __iter__ for | __enter__/__exit__ with | __new__ singleton
#                  __init_subclass__ hook | __set_name__/__get__/__set__ descriptor
# DATACLASS:       @dataclass auto init/repr/eq | frozen=True immutable | order=True
# SLOTS:           __slots__=(...) no __dict__, less memory, faster access
# PATTERNS:        Mixin (reusable MI) | Enum/auto() | return self (chaining)
#                  Composition > Inheritance — "has-a" beats "is-a"
