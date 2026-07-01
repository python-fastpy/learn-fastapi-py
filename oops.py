# ╔══════════════════════════════════════════════════════════════════════╗
# ║                  PYTHON OOP — All Concepts Guide                    ║
# ║                                                                     ║
# ║  Class = blueprint/template for creating objects                    ║
# ║  Object = instance created from a class                            ║
# ║                                                                     ║
# ║  4 Pillars of OOP:                                                  ║
# ║    1. Encapsulation  — hide data, expose methods                    ║
# ║    2. Inheritance    — child class gets parent's stuff              ║
# ║    3. Polymorphism   — same method name, different behavior         ║
# ║    4. Abstraction    — hide complex details, show simple interface  ║
# ╚══════════════════════════════════════════════════════════════════════╝


# ════════════════════════════════════════════════════
# 1. Basic class and object
#
#  class = template
#  object = thing created from template
#  __init__ = runs when object is created (constructor)
#  self = refers to the current object
# ════════════════════════════════════════════════════

class Car:
    def __init__(self, brand, color):    # constructor — called on Car(...)
        self.brand = brand               # self.brand = instance variable
        self.color = color

    def describe(self):                  # method — function inside a class
        return f"{self.color} {self.brand}"

# Create objects (instances)
car1 = Car("Toyota", "Red")
car2 = Car("Honda", "Blue")

print(car1.describe())    # "Red Toyota"
print(car2.describe())    # "Blue Honda"
print(car1.brand)         # "Toyota" — access attribute directly

# car1 and car2 are separate objects — changing one doesn't affect the other
car1.color = "Black"
print(car1.describe())    # "Black Toyota"
print(car2.describe())    # "Blue Honda" — unchanged

print("=" * 50)


# ════════════════════════════════════════════════════
# 2. Instance variables vs Class variables
#
#  Instance variable (self.x) = unique to each object
#  Class variable (inside class, outside __init__) = shared by ALL objects
# ════════════════════════════════════════════════════

class Employee:
    company = "Reuters"       # class variable — same for ALL employees
    employee_count = 0        # class variable — tracks total count

    def __init__(self, name, salary):
        self.name = name      # instance variable — unique per object
        self.salary = salary  # instance variable
        Employee.employee_count += 1    # modify class variable

emp1 = Employee("Alice", 50000)
emp2 = Employee("Bob", 60000)

print(emp1.name)              # "Alice" — instance variable
print(emp2.name)              # "Bob"   — different per object
print(emp1.company)           # "Reuters" — class variable (same for all)
print(emp2.company)           # "Reuters"
print(Employee.employee_count)  # 2 — shared counter

# Class variable can be accessed from class itself OR any instance
print(Employee.company)       # "Reuters"

print("=" * 50)


# ════════════════════════════════════════════════════
# 3. Methods — instance, class, static
#
#  Instance method  — def method(self)     — works on ONE object
#  Class method     — @classmethod         — works on the CLASS itself
#  Static method    — @staticmethod        — utility, no access to class/object
# ════════════════════════════════════════════════════

class Pizza:
    base_price = 10    # class variable

    def __init__(self, size, toppings):
        self.size = size            # instance variable
        self.toppings = toppings

    # Instance method — uses self (the specific pizza object)
    def get_price(self):
        return Pizza.base_price + (len(self.toppings) * 2)

    # Class method — uses cls (the Pizza class itself)
    # Can modify class variables, can't access instance variables
    @classmethod
    def set_base_price(cls, price):
        cls.base_price = price      # modifies class variable for ALL pizzas

    # Class method as alternative constructor
    @classmethod
    def margherita(cls):
        return cls("Medium", ["cheese", "tomato"])    # creates a Pizza object

    # Static method — no self, no cls — just a utility function
    # Could be a regular function, but logically belongs to Pizza
    @staticmethod
    def is_valid_size(size):
        return size in ["Small", "Medium", "Large"]

# Instance method
p1 = Pizza("Large", ["cheese", "mushroom", "olive"])
print(p1.get_price())              # 16 (10 + 3*2)

# Class method — modify class variable
Pizza.set_base_price(12)
print(p1.get_price())              # 18 (12 + 3*2) — base price changed for ALL

# Class method — alternative constructor
p2 = Pizza.margherita()
print(p2.toppings)                 # ["cheese", "tomato"]

# Static method — no object needed
print(Pizza.is_valid_size("Large"))    # True
print(Pizza.is_valid_size("Huge"))     # False

print("=" * 50)


# ════════════════════════════════════════════════════
# 4. ENCAPSULATION — public, protected, private
#
#  public     = name       → anyone can access
#  protected  = _name      → convention: "don't touch from outside"
#  private    = __name     → Python name-mangles it (hard to access)
#
#  Use properties (@property) to control access
# ════════════════════════════════════════════════════

class BankAccount:
    def __init__(self, owner, balance):
        self.owner = owner          # public — anyone can read/write
        self._bank = "Chase"        # protected — convention only, still accessible
        self.__balance = balance    # private — name-mangled to _BankAccount__balance

    # Getter — read __balance safely
    @property
    def balance(self):
        return self.__balance

    # Setter — write __balance with validation
    @balance.setter
    def balance(self, amount):
        if amount < 0:
            raise ValueError("Balance cannot be negative")
        self.__balance = amount

    # Deleter — optional, runs on: del account.balance
    @balance.deleter
    def balance(self):
        print("Closing account...")
        self.__balance = 0

    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
        return self.__balance

    def withdraw(self, amount):
        if amount > self.__balance:
            return "Insufficient funds"
        self.__balance -= amount
        return self.__balance

acc = BankAccount("Alice", 1000)

# Public — direct access
print(acc.owner)             # "Alice"

# Protected — accessible but convention says "don't"
print(acc._bank)             # "Chase" — works but shouldn't be used outside

# Private — can't access directly
# print(acc.__balance)       # AttributeError!
print(acc._BankAccount__balance)   # 1000 — Python's name mangling (not recommended)

# Property — clean access with validation
print(acc.balance)           # 1000 — calls @property getter
acc.balance = 2000           # calls @balance.setter
print(acc.balance)           # 2000

try:
    acc.balance = -500       # setter rejects negative
except ValueError as e:
    print(f"Error: {e}")     # "Balance cannot be negative"

# Methods for controlled access
print(acc.deposit(500))      # 2500
print(acc.withdraw(100))     # 2400

print("=" * 50)


# ════════════════════════════════════════════════════
# 5. INHERITANCE — single inheritance
#
#  Child class gets ALL methods and attributes from parent
#  Child can add new ones or override parent's
#  super() calls the parent's method
# ════════════════════════════════════════════════════

class Animal:
    def __init__(self, name, sound):
        self.name = name
        self.sound = sound

    def speak(self):
        return f"{self.name} says {self.sound}!"

    def info(self):
        return f"Animal: {self.name}"

class Dog(Animal):     # Dog inherits from Animal
    def __init__(self, name, breed):
        super().__init__(name, "Woof")   # call parent's __init__
        self.breed = breed               # add new attribute

    def fetch(self):                     # new method (not in Animal)
        return f"{self.name} fetches the ball!"

    def info(self):                      # OVERRIDE parent's method
        return f"Dog: {self.name}, Breed: {self.breed}"

class Cat(Animal):
    def __init__(self, name):
        super().__init__(name, "Meow")

dog = Dog("Rex", "Labrador")
cat = Cat("Whiskers")

print(dog.speak())      # "Rex says Woof!"     — inherited from Animal
print(dog.fetch())      # "Rex fetches..."     — Dog's own method
print(dog.info())       # "Dog: Rex, Breed..."  — overridden method
print(dog.breed)        # "Labrador"           — Dog's own attribute

print(cat.speak())      # "Whiskers says Meow!" — inherited from Animal
print(cat.info())       # "Animal: Whiskers"    — NOT overridden, uses parent's

# Check inheritance
print(isinstance(dog, Dog))      # True
print(isinstance(dog, Animal))   # True — Dog IS an Animal
print(isinstance(cat, Dog))      # False — Cat is NOT a Dog

print("=" * 50)


# ════════════════════════════════════════════════════
# 6. INHERITANCE — multi-level (grandparent → parent → child)
# ════════════════════════════════════════════════════

class Vehicle:
    def __init__(self, brand):
        self.brand = brand

    def start(self):
        return f"{self.brand} starting..."

class ElectricVehicle(Vehicle):        # inherits from Vehicle
    def __init__(self, brand, battery):
        super().__init__(brand)
        self.battery = battery

    def charge(self):
        return f"Charging {self.brand} ({self.battery}kWh)"

class Tesla(ElectricVehicle):          # inherits from ElectricVehicle
    def __init__(self, model, battery):
        super().__init__("Tesla", battery)
        self.model = model

    def autopilot(self):
        return f"Tesla {self.model} — autopilot engaged!"

t = Tesla("Model 3", 75)
print(t.start())       # "Tesla starting..."    — from Vehicle (grandparent)
print(t.charge())      # "Charging Tesla..."    — from ElectricVehicle (parent)
print(t.autopilot())   # "Tesla Model 3..."     — from Tesla (self)

# Method Resolution Order — which class is checked first
print(Tesla.__mro__)
# Tesla → ElectricVehicle → Vehicle → object

print("=" * 50)


# ════════════════════════════════════════════════════
# 7. INHERITANCE — multiple (child has TWO parents)
#
#  Python supports multiple inheritance
#  MRO (Method Resolution Order) decides which parent's method wins
# ════════════════════════════════════════════════════

class Flyable:
    def fly(self):
        return "I can fly!"

    def move(self):
        return "Flying through air"

class Swimmable:
    def swim(self):
        return "I can swim!"

    def move(self):
        return "Swimming in water"

class Duck(Flyable, Swimmable):    # inherits from BOTH
    def quack(self):
        return "Quack!"

duck = Duck()
print(duck.fly())      # "I can fly!"        — from Flyable
print(duck.swim())     # "I can swim!"       — from Swimmable
print(duck.quack())    # "Quack!"            — from Duck
print(duck.move())     # "Flying through air" — Flyable listed FIRST, so it wins

# MRO shows the order Python checks
print(Duck.__mro__)
# Duck → Flyable → Swimmable → object

print("=" * 50)


# ════════════════════════════════════════════════════
# 8. POLYMORPHISM — same method name, different behavior
#
#  Different classes have the same method name
#  but each does something different
#  You can loop over them and call the same method
# ════════════════════════════════════════════════════

class Circle:
    def __init__(self, radius):
        self.radius = radius

    def area(self):
        return 3.14 * self.radius ** 2

    def describe(self):
        return f"Circle with radius {self.radius}"

class Rectangle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

    def area(self):
        return self.width * self.height

    def describe(self):
        return f"Rectangle {self.width}x{self.height}"

class Triangle:
    def __init__(self, base, height):
        self.base = base
        self.height = height

    def area(self):
        return 0.5 * self.base * self.height

    def describe(self):
        return f"Triangle base={self.base}, height={self.height}"

# Polymorphism — same method name, different classes
shapes = [Circle(5), Rectangle(4, 6), Triangle(3, 8)]

for shape in shapes:
    # Calls the RIGHT area() method for each type
    print(f"{shape.describe()} → area = {shape.area()}")
# Circle with radius 5 → area = 78.5
# Rectangle 4x6 → area = 24
# Triangle base=3, height=8 → area = 12.0

print("=" * 50)


# ════════════════════════════════════════════════════
# 9. ABSTRACTION — abstract base class (ABC)
#
#  Abstract class = template that CANNOT be instantiated
#  Forces child classes to implement certain methods
#  If child doesn't implement → error at creation time
# ════════════════════════════════════════════════════

from abc import ABC, abstractmethod

class Shape(ABC):    # abstract class — can't create Shape() directly

    @abstractmethod
    def area(self):
        pass         # no implementation — child MUST provide it

    @abstractmethod
    def perimeter(self):
        pass

    def description(self):                    # concrete method — child inherits this
        return f"I am a {self.__class__.__name__}"

class Square(Shape):
    def __init__(self, side):
        self.side = side

    def area(self):                           # MUST implement
        return self.side ** 2

    def perimeter(self):                      # MUST implement
        return 4 * self.side

# Can't create abstract class directly:
# s = Shape()    # TypeError: Can't instantiate abstract class

sq = Square(5)
print(sq.area())           # 25
print(sq.perimeter())      # 20
print(sq.description())   # "I am a Square" — inherited from Shape

# If you forget to implement an abstract method:
# class BadShape(Shape):
#     def area(self):
#         return 0
#     # missing perimeter() → TypeError when you try BadShape()

print("=" * 50)


# ════════════════════════════════════════════════════
# 10. Dunder/Magic methods — customize object behavior
#
#  __init__    = constructor (creating object)
#  __str__     = print(obj) and str(obj)
#  __repr__    = developer representation
#  __len__     = len(obj)
#  __eq__      = obj1 == obj2
#  __lt__      = obj1 < obj2
#  __add__     = obj1 + obj2
#  __getitem__ = obj[key]
#  __contains__= item in obj
# ════════════════════════════════════════════════════

class Product:
    def __init__(self, name, price):
        self.name = name
        self.price = price

    def __str__(self):                # print(product) — for users
        return f"{self.name}: ${self.price}"

    def __repr__(self):               # for developers / debugging
        return f"Product('{self.name}', {self.price})"

    def __eq__(self, other):          # product1 == product2
        return self.name == other.name and self.price == other.price

    def __lt__(self, other):          # product1 < product2
        return self.price < other.price

    def __add__(self, other):         # product1 + product2
        return Product(f"{self.name} + {other.name}", self.price + other.price)

    def __len__(self):                # len(product) — length of name
        return len(self.name)

    def __bool__(self):               # if product: — truthy if price > 0
        return self.price > 0

p1 = Product("Laptop", 999)
p2 = Product("Mouse", 25)
p3 = Product("Laptop", 999)

print(p1)                  # "Laptop: $999"      — __str__
print(repr(p2))            # "Product('Mouse', 25)" — __repr__
print(p1 == p3)            # True                — __eq__
print(p1 == p2)            # False
print(p2 < p1)             # True (25 < 999)     — __lt__
print(sorted([p1, p2]))    # [Mouse: $25, Laptop: $999] — uses __lt__

combo = p1 + p2            # __add__
print(combo)               # "Laptop + Mouse: $1024"
print(len(p1))             # 6 ("Laptop")        — __len__

free = Product("Sample", 0)
print(bool(p1))            # True (price > 0)    — __bool__
print(bool(free))           # False (price = 0)

print("=" * 50)


# ════════════════════════════════════════════════════
# 11. __getitem__, __setitem__, __contains__ — make object subscriptable
# ════════════════════════════════════════════════════

class Inventory:
    def __init__(self):
        self._items = {}

    def __getitem__(self, key):        # inventory["laptop"]
        return self._items.get(key, "Not found")

    def __setitem__(self, key, value): # inventory["laptop"] = 5
        self._items[key] = value

    def __delitem__(self, key):        # del inventory["laptop"]
        if key in self._items:
            del self._items[key]

    def __contains__(self, key):       # "laptop" in inventory
        return key in self._items

    def __len__(self):                 # len(inventory)
        return len(self._items)

    def __iter__(self):                # for item in inventory
        return iter(self._items)

    def __str__(self):
        return str(self._items)

inv = Inventory()
inv["laptop"] = 5             # __setitem__
inv["mouse"] = 20
inv["keyboard"] = 15

print(inv["laptop"])          # 5 — __getitem__
print("mouse" in inv)        # True — __contains__
print(len(inv))               # 3 — __len__

del inv["keyboard"]           # __delitem__
print(len(inv))               # 2

for item in inv:              # __iter__
    print(f"  {item}: {inv[item]}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 12. Property — getter, setter, deleter (clean version)
#
#  @property = access method like an attribute
#  No parentheses needed: obj.name instead of obj.get_name()
# ════════════════════════════════════════════════════

class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius

    @property
    def celsius(self):
        return self._celsius

    @celsius.setter
    def celsius(self, value):
        if value < -273.15:
            raise ValueError("Temperature below absolute zero!")
        self._celsius = value

    @property
    def fahrenheit(self):           # computed property — no stored value
        return (self._celsius * 9/5) + 32

    @fahrenheit.setter
    def fahrenheit(self, value):    # set celsius from fahrenheit
        self._celsius = (value - 32) * 5/9

temp = Temperature(100)
print(temp.celsius)        # 100     — getter (no parentheses!)
print(temp.fahrenheit)     # 212.0   — computed on the fly

temp.fahrenheit = 32       # setter — converts to celsius
print(temp.celsius)        # 0.0

try:
    temp.celsius = -300
except ValueError as e:
    print(f"Error: {e}")   # "Temperature below absolute zero!"

print("=" * 50)


# ════════════════════════════════════════════════════
# 13. Composition — "has a" relationship
#
#  Inheritance = "is a" (Dog IS an Animal)
#  Composition = "has a" (Car HAS an Engine)
#
#  Composition is often BETTER than inheritance
#  because it's more flexible
# ════════════════════════════════════════════════════

class Engine:
    def __init__(self, horsepower):
        self.horsepower = horsepower
        self.running = False

    def start(self):
        self.running = True
        return f"Engine ({self.horsepower}hp) started"

    def stop(self):
        self.running = False
        return "Engine stopped"

class GPS:
    def navigate(self, destination):
        return f"Navigating to {destination}..."

class MyCar:
    def __init__(self, brand, horsepower):
        self.brand = brand
        self.engine = Engine(horsepower)    # Car HAS an Engine
        self.gps = GPS()                    # Car HAS a GPS

    def start(self):
        return f"{self.brand}: {self.engine.start()}"

    def go_to(self, place):
        if not self.engine.running:
            return "Start the engine first!"
        return self.gps.navigate(place)

my_car = MyCar("BMW", 300)
print(my_car.start())               # "BMW: Engine (300hp) started"
print(my_car.go_to("Airport"))      # "Navigating to Airport..."
print(my_car.engine.horsepower)     # 300 — access composed object directly

print("=" * 50)


# ════════════════════════════════════════════════════
# 14. Dataclass — automatic __init__, __repr__, __eq__
#
#  @dataclass generates boilerplate code for you
#  No need to write __init__, __repr__, __eq__ manually
# ════════════════════════════════════════════════════

from dataclasses import dataclass, field

@dataclass
class User:
    name: str
    email: str
    age: int
    active: bool = True                        # default value
    tags: list = field(default_factory=list)    # mutable default

# Auto-generated __init__:
u1 = User("Alice", "alice@test.com", 30)
u2 = User("Bob", "bob@test.com", 25, active=False)
u3 = User("Alice", "alice@test.com", 30)

# Auto-generated __repr__:
print(u1)    # User(name='Alice', email='alice@test.com', age=30, active=True, tags=[])

# Auto-generated __eq__:
print(u1 == u3)    # True — same values
print(u1 == u2)    # False

# You can still add methods
@dataclass
class Point:
    x: float
    y: float

    def distance_from_origin(self):
        return (self.x ** 2 + self.y ** 2) ** 0.5

p = Point(3, 4)
print(p.distance_from_origin())    # 5.0

# Frozen dataclass — immutable (can't change after creation)
@dataclass(frozen=True)
class Color:
    r: int
    g: int
    b: int

red = Color(255, 0, 0)
# red.r = 100    # FrozenInstanceError! — can't modify

# Ordered dataclass — enables <, >, sorting
@dataclass(order=True)
class Score:
    value: int
    player: str = ""

scores = [Score(85, "Alice"), Score(92, "Bob"), Score(78, "Charlie")]
print(sorted(scores))
# [Score(value=78, player='Charlie'), Score(value=85, player='Alice'), Score(value=92, player='Bob')]

print("=" * 50)


# ════════════════════════════════════════════════════
# 15. Slots — save memory, faster attribute access
#
#  __slots__ = fixed list of attributes
#  Python stores them in a tuple instead of a dict
#  Uses ~40% less memory, ~10% faster access
# ════════════════════════════════════════════════════

class WithoutSlots:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class WithSlots:
    __slots__ = ("x", "y")    # only these attributes allowed

    def __init__(self, x, y):
        self.x = x
        self.y = y

a = WithoutSlots(1, 2)
b = WithSlots(1, 2)

a.z = 3          # works — can add any attribute
# b.z = 3        # AttributeError! — z not in __slots__

print(a.__dict__)     # {'x': 1, 'y': 2, 'z': 3} — has __dict__
# print(b.__dict__)   # AttributeError! — no __dict__ with slots

print(b.x, b.y)      # 1 2 — works fine for declared slots

print("=" * 50)


# ════════════════════════════════════════════════════
# 16. Mixins — reusable behavior through multiple inheritance
#
#  Mixin = small class that adds ONE specific capability
#  Not meant to be used alone — mixed into other classes
# ════════════════════════════════════════════════════

import json

class JsonMixin:
    def to_json(self):
        return json.dumps(self.__dict__, indent=2)

    @classmethod
    def from_json(cls, json_string):
        data = json.loads(json_string)
        return cls(**data)

class PrintableMixin:
    def print_info(self):
        attrs = ", ".join(f"{k}={v}" for k, v in self.__dict__.items())
        print(f"[{self.__class__.__name__}] {attrs}")

class Article(JsonMixin, PrintableMixin):
    def __init__(self, title, author, words=0):
        self.title = title
        self.author = author
        self.words = words

art = Article("Breaking News", "Alice", 500)
art.print_info()          # [Article] title=Breaking News, author=Alice, words=500
print(art.to_json())
# {
#   "title": "Breaking News",
#   "author": "Alice",
#   "words": 500
# }

# Create from JSON
art2 = Article.from_json('{"title": "Update", "author": "Bob", "words": 300}')
art2.print_info()         # [Article] title=Update, author=Bob, words=300

print("=" * 50)


# ════════════════════════════════════════════════════
# 17. Enum with class — named constants
# ════════════════════════════════════════════════════

from enum import Enum, auto

class Status(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"

class Priority(Enum):
    LOW = auto()       # auto-assigns 1
    MEDIUM = auto()    # auto-assigns 2
    HIGH = auto()      # auto-assigns 3

class Task:
    def __init__(self, title, status, priority):
        self.title = title
        self.status = status
        self.priority = priority

    def __str__(self):
        return f"[{self.priority.name}] {self.title} ({self.status.value})"

task = Task("Fix bug", Status.ACTIVE, Priority.HIGH)
print(task)                        # [HIGH] Fix bug (active)
print(task.status == Status.ACTIVE)  # True
print(task.priority.value)         # 3

# Loop through all values
for s in Status:
    print(f"  {s.name} = {s.value}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 18. Method chaining — return self for fluent API
#
#  Each method returns self so you can chain calls:
#  builder.set_name("X").set_age(25).build()
# ════════════════════════════════════════════════════

class QueryBuilder:
    def __init__(self, table):
        self.table = table
        self._conditions = []
        self._order = None
        self._limit = None

    def where(self, condition):
        self._conditions.append(condition)
        return self                          # return self for chaining

    def order_by(self, column):
        self._order = column
        return self

    def limit(self, n):
        self._limit = n
        return self

    def build(self):
        query = f"SELECT * FROM {self.table}"
        if self._conditions:
            query += " WHERE " + " AND ".join(self._conditions)
        if self._order:
            query += f" ORDER BY {self._order}"
        if self._limit:
            query += f" LIMIT {self._limit}"
        return query

# Method chaining — reads like English
query = (
    QueryBuilder("users")
    .where("age > 18")
    .where("active = true")
    .order_by("name")
    .limit(10)
    .build()
)
print(query)
# SELECT * FROM users WHERE age > 18 AND active = true ORDER BY name LIMIT 10

print("=" * 50)


# ════════════════════════════════════════════════════
# 19. Context manager — with statement (__enter__ / __exit__)
#
#  "with" ensures cleanup happens even if error occurs
#  __enter__ = setup (runs at start of with block)
#  __exit__  = cleanup (runs at end, even on error)
# ════════════════════════════════════════════════════

class FileLogger:
    def __init__(self, filename):
        self.filename = filename
        self.logs = []

    def __enter__(self):
        print(f"Logger started for {self.filename}")
        return self                    # this is what "as logger" receives

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"Logger finished. {len(self.logs)} logs written.")
        if exc_type:
            print(f"Error occurred: {exc_val}")
        return False                   # False = don't suppress exceptions

    def log(self, message):
        self.logs.append(message)
        print(f"  LOG: {message}")

with FileLogger("app.log") as logger:
    logger.log("Application started")
    logger.log("User logged in")
    logger.log("Processing data")
# Logger started for app.log
#   LOG: Application started
#   LOG: User logged in
#   LOG: Processing data
# Logger finished. 3 logs written.

print("=" * 50)


# ════════════════════════════════════════════════════
# 20. Singleton — only ONE instance ever exists
# ════════════════════════════════════════════════════

class Database:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host="localhost"):
        self.host = host

db1 = Database("server1")
db2 = Database("server2")

print(db1 is db2)       # True — same object!
print(db1.host)          # "server2" — last __init__ ran
print(id(db1) == id(db2))  # True — same memory address

print("=" * 50)


# ════════════════════════════════════════════════════
# 21. __call__ — make object callable like a function
# ════════════════════════════════════════════════════

class Multiplier:
    def __init__(self, factor):
        self.factor = factor

    def __call__(self, value):     # makes instance callable
        return value * self.factor

double = Multiplier(2)
triple = Multiplier(3)

print(double(5))      # 10 — calling object like a function
print(triple(5))      # 15

# Check if object is callable
print(callable(double))   # True

print("=" * 50)


# ════════════════════════════════════════════════════
# 22. Descriptor — control attribute access across classes
#
#  __get__, __set__, __delete__ on a class
#  Used by @property internally
# ════════════════════════════════════════════════════

class PositiveNumber:
    def __init__(self, name):
        self.name = name

    def __set_name__(self, owner, name):    # called when class is created
        self.name = name

    def __get__(self, obj, objtype=None):
        return getattr(obj, f"_{self.name}", 0)

    def __set__(self, obj, value):
        if value < 0:
            raise ValueError(f"{self.name} must be positive, got {value}")
        setattr(obj, f"_{self.name}", value)

class Order:
    quantity = PositiveNumber("quantity")    # descriptor
    price = PositiveNumber("price")         # descriptor

    def __init__(self, item, quantity, price):
        self.item = item
        self.quantity = quantity    # goes through __set__
        self.price = price

    def total(self):
        return self.quantity * self.price

order = Order("Widget", 5, 9.99)
print(order.total())          # 49.95

try:
    order.quantity = -3        # goes through __set__ → ValueError
except ValueError as e:
    print(f"Error: {e}")       # "quantity must be positive, got -3"

print("=" * 50)


# ════════════════════════════════════════════════════
# 23. Type checking with isinstance and issubclass
# ════════════════════════════════════════════════════

class Media:
    pass

class Video(Media):
    pass

class Audio(Media):
    pass

class Podcast(Audio):
    pass

v = Video()
p = Podcast()

# isinstance — is this object a (type)?
print(isinstance(v, Video))     # True
print(isinstance(v, Media))     # True — Video is a subclass of Media
print(isinstance(v, Audio))     # False

print(isinstance(p, Podcast))   # True
print(isinstance(p, Audio))     # True — Podcast inherits from Audio
print(isinstance(p, Media))     # True — Audio inherits from Media

# issubclass — is this class a child of (parent)?
print(issubclass(Video, Media))     # True
print(issubclass(Podcast, Media))   # True
print(issubclass(Video, Audio))     # False

print("=" * 50)


# ════════════════════════════════════════════════════
# 24. __init_subclass__ — hook when class is inherited
#
#  Runs automatically when someone creates a child class
#  Useful for registering plugins, validating subclasses
# ════════════════════════════════════════════════════

class Plugin:
    registry = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin.registry.append(cls.__name__)
        print(f"  Plugin registered: {cls.__name__}")

class PDFExporter(Plugin):       # auto-registered
    pass

class CSVExporter(Plugin):       # auto-registered
    pass

class XMLExporter(Plugin):       # auto-registered
    pass

print(f"All plugins: {Plugin.registry}")
# All plugins: ['PDFExporter', 'CSVExporter', 'XMLExporter']

print("=" * 50)


# ════════════════════════════════════════════════════
# SUMMARY
#
#  Basics:         class, __init__, self, instance vs class variables
#  Methods:        instance, @classmethod, @staticmethod
#  Encapsulation:  public, _protected, __private, @property
#  Inheritance:    single, multi-level, multiple, super()
#  Polymorphism:   same method name, different behavior
#  Abstraction:    ABC, @abstractmethod
#  Magic methods:  __str__, __repr__, __eq__, __lt__, __add__,
#                  __getitem__, __contains__, __len__, __call__
#  Composition:    "has a" vs "is a"
#  Dataclass:      @dataclass — auto-generates boilerplate
#  Slots:          __slots__ — memory optimization
#  Mixins:         reusable behavior via multiple inheritance
#  Enum:           named constants
#  Chaining:       return self for fluent API
#  Context mgr:    __enter__ / __exit__ (with statement)
#  Singleton:      __new__ — only one instance
#  Descriptor:     __get__ / __set__ — reusable attribute logic
#  Subclass hook:  __init_subclass__ — auto-register children
# ════════════════════════════════════════════════════
