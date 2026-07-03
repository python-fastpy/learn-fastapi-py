# ══════════════════════════════════════════════════════════════════
# PYTHON DATA TYPES — CONDENSED REFERENCE
# ══════════════════════════════════════════════════════════════════
import math, copy, re, weakref
from enum import Enum, IntEnum, Flag, auto
from typing import (List, Dict, Tuple, Set, Optional, Union,
                    Any, Callable, Final, Literal, NamedTuple, TypedDict)
from collections import namedtuple, OrderedDict, defaultdict, Counter, deque, ChainMap
from dataclasses import dataclass, field
from datetime import date, time, datetime, timedelta, timezone
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path
from queue import Queue, LifoQueue, PriorityQueue
from contextlib import contextmanager
from functools import partial

# ╔══════════════════════════════════════════════════╗
# ║                   BEGINNER                       ║
# ╚══════════════════════════════════════════════════╝

# ── 1. int ──────────────────────────────────────────
a = 10; b = -5; c = 1_000_000       # underscores for readability
d = 0b1010; e = 0o17; f = 0xFF      # binary=10, octal=15, hex=255
g = int("42"); h = int("1010", 2)   # str->int, binary str->int=10
i = int(3.9)                         # truncates toward zero => 3
big = 10**100                        # arbitrary precision, no overflow
print(f"int: {a}, bin={d}, oct={e}, hex={f}")  # 10, 10, 15, 255
print(f"int(3.9)={i}, int(-3.9)={int(-3.9)}") # 3, -3 (truncates, NOT rounds)
# input: num = int(input("Enter integer: "))

# ── 2. float ────────────────────────────────────────
# 64-bit IEEE 754 double precision (~15-17 significant digits)
a_f = 3.14; b_f = 3.14e2             # standard, scientific=314.0
c_f = float("inf"); d_f = float("nan")
print(f"float: {a_f}, sci={b_f}, inf={c_f}, nan={d_f}")
print(f"0.1 + 0.2 = {0.1 + 0.2}")                     # 0.30000000000000004
print(f"0.1+0.2 == 0.3 => {0.1 + 0.2 == 0.3}")        # False  GOTCHA!
print(f"math.isclose => {math.isclose(0.1 + 0.2, 0.3)}")  # True  FIX
print(f"isnan={math.isnan(d_f)}, isinf={math.isinf(c_f)}")  # True, True
# input: price = float(input("Enter price: "))

# ── 3. complex ──────────────────────────────────────
z = 3 + 4j                           #  same as complex(3, 4)
print(f"complex: {z}, real={z.real}, imag={z.imag}")  # 3.0, 4.0
print(f"conjugate={z.conjugate()}, abs={abs(z)}")     # (3-4j), 5.0
# GOTCHA: complex("3+4j") OK, complex("3 + 4j") ValueError (no spaces!)

# ── 4. bool ─────────────────────────────────────────
# Subclass of int: True==1, False==0
print(f"True+True={True+True}, True*10={True*10}")  # 2, 10
print(f"isinstance(True, int)={isinstance(True, int)}")  # True
# Falsy: False, None, 0, 0.0, 0j, '', [], (), {}, set(), frozenset()
# Truthy: everything else
print(f"bool('')={bool('')}, bool('x')={bool('x')}")       # False, True
print(f"bool([])={bool([])}, bool(None)={bool(None)}")     # False, False
# GOTCHA: bool("False") => True (non-empty string!)
# input: answer = input("y/n: ").strip().lower() in ("yes","y","1")

# ── 5. str ──────────────────────────────────────────
# Immutable sequence of Unicode characters
s1 = 'single'; s2 = "double"
s3 = """triple\nfor multiline"""
s4 = str(42)                          # "42"
s5 = r"raw\nstring"                   # no escape processing

# Key methods
word = "Hello, World!"
print(f"len={len(word)}, upper={word.upper()}, lower={word.lower()}")
print(f"strip='{'  hi  '.strip()}', replace={word.replace('World','Python')}")
print(f"split={'a,b,c'.split(',')}, join={'-'.join(['a','b','c'])}")
print(f"find={word.find('World')}, count={'banana'.count('a')}")
print(f"startswith={word.startswith('Hello')}, isdigit={'123'.isdigit()}")

# Indexing & slicing
text = "Python"
print(f"[0]={text[0]}, [-1]={text[-1]}, [0:3]={text[0:3]}, [::-1]={text[::-1]}")

# Formatting
name, age = "Alice", 30
print(f"f-string: {name} is {age}")           # f-string: Alice is 30
print(f"{3.14159:.2f}, {1000000:,}, {255:08b}, {255:#x}")  # 3.14, 1,000,000, 11111111, 0xff
# IMMUTABLE: text[0] = 'p' => TypeError

# ── 6. NoneType ─────────────────────────────────────
n = None
print(f"None is None: {n is None}")            # True (always use 'is', not ==)
print(f"bool(None)={bool(None)}")              # False
def no_return(): pass
print(f"no return => {no_return()}")           # None

# ╔══════════════════════════════════════════════════╗
# ║                 INTERMEDIATE                     ║
# ╚══════════════════════════════════════════════════╝

# ── 7. list ─────────────────────────────────────────
# Mutable, ordered, allows duplicates and mixed types
l1 = [1, 2, 3]; l2 = list("hello")   # ['h','e','l','l','o']
l3 = list(range(5))                   # [0,1,2,3,4]
# Indexing: l1[0]=1, l1[-1]=3, l1[1:3]=[2,3], l1[::-1]=[3,2,1]

lst = [3, 1, 4, 1, 5]
lst.append(9)                         # [3,1,4,1,5,9]
lst.insert(0, 0)                      # [0,3,1,4,1,5,9]
lst.extend([6, 7])                    # adds multiple to end
popped = lst.pop()                    # remove & return last
lst.remove(1)                         # remove first occurrence
print(f"count={lst.count(1)}, index={lst.index(4)}")

lst2 = [3, 1, 4, 1, 5]
lst2.sort()                           # in-place => [1,1,3,4,5]
lst2.sort(reverse=True)               # descending
new_sorted = sorted([3, 1, 2])        # returns new list, original unchanged

# Comprehension
squares = [x**2 for x in range(6)]    # [0,1,4,9,16,25]
evens = [x for x in range(10) if x % 2 == 0]

# Unpacking
first, *rest = [1, 2, 3, 4]           # first=1, rest=[2,3,4]

# Copying
shallow = lst2.copy()                 # same as lst2[:]
deep = copy.deepcopy([[1,2],[3,4]])   # deep copy for nested
# input: nums = list(map(int, input("numbers: ").split()))

# ── 8. tuple ────────────────────────────────────────
# Immutable, ordered, hashable (if elements are hashable)
t1 = (1, 2, 3); t2 = (1,)            # COMMA required for single element!
t3 = tuple([1, 2, 3])
# GOTCHA: (1) is int, (1,) is tuple
print(f"single: {t2}, type={type(t2)}")  # (1,), <class 'tuple'>
print(f"NOT tuple: type((1))={type((1))}")  # <class 'int'>

# Only 2 methods: count() and index()
a_t, b_t, c_t = t1                   # unpacking
x, y = 10, 20; x, y = y, x           # swap via tuple unpacking

# Mutable objects INSIDE a tuple CAN change  GOTCHA
tricky = ([1, 2], [3, 4])
tricky[0].append(3)                   # ([1,2,3], [3,4]) — no error!

#  list vs tuple: list=mutable,slower | tuple=immutable,hashable,faster

# Named tuple
Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
print(f"namedtuple: {p}, x={p.x}")    # Point(x=3, y=4), x=3

# ── 9. range ────────────────────────────────────────
r1 = range(5)                         # 0,1,2,3,4
r2 = range(2, 8)                      # 2,3,4,5,6,7
r3 = range(0, 10, 2)                  # 0,2,4,6,8
r4 = range(10, 0, -1)                 # countdown 10..1
print(f"range: {list(r3)}, len={len(r1)}, 5 in range(10)={5 in range(10)}")

# ── 10. set ─────────────────────────────────────────
# Mutable, unordered, unique elements, elements must be hashable
s1 = {1, 2, 3}; s2 = {1, 2, 2, 3}    # duplicates removed => {1,2,3}
s3 = set("hello")                     # {'h','e','l','o'}
s4 = set()                            # empty set
# GOTCHA: {} creates dict, NOT set! Use set() for empty set

s = {1, 2, 3}
s.add(4)                              # add single
s.update([5, 6])                      # add multiple
s.discard(6)                          # remove if present (no error)
s.remove(5)                           # remove (KeyError if missing!)

# Set operations
a_s, b_s = {1, 2, 3, 4}, {3, 4, 5, 6}
print(f"union: {a_s | b_s}")          # {1,2,3,4,5,6}
print(f"intersect: {a_s & b_s}")      # {3,4}
print(f"diff: {a_s - b_s}")           # {1,2}
print(f"sym_diff: {a_s ^ b_s}")       # {1,2,5,6}
print(f"subset: {{1,2}} <= a_s = {({1,2}).issubset(a_s)}")  # True

# Set comprehension
even_set = {x for x in range(10) if x % 2 == 0}

# ── 11. frozenset ───────────────────────────────────
# Immutable set — can be dict key or set element
fs = frozenset([1, 2, 3])
# fs.add(4)  # AttributeError!
d_fs = {fs: "value"}                  # works because hashable
#  set vs frozenset: set=mutable | frozenset=immutable,hashable

# ── 12. dict ────────────────────────────────────────
# Mutable key-value mapping. Keys must be hashable. Insertion-ordered (3.7+)
d1 = {"name": "Alice", "age": 30}
d2 = dict(name="Alice", age=30)       # keyword args
d3 = dict(zip(["x","y"], [1,2]))      # from zip
d4 = {i: i**2 for i in range(5)}      # comprehension

# Access
print(f"d1['name']={d1['name']}")      # Alice
print(f"get={d1.get('missing','default')}")  # default (no KeyError)
# d1['missing']  => KeyError

# Modify
d1["email"] = "a@b.com"               # add/update
d1.update({"age": 31, "city": "NYC"}) # update multiple
d1.setdefault("country", "US")        # set only if missing

# Remove
popped_d = d1.pop("email")            # remove & return
last = d1.popitem()                   # remove last inserted (3.7+)

# Views & iteration
print(f"keys={list(d1.keys())}, values={list(d1.values())}")
print(f"items={list(d1.items())}")
print(f"'name' in d1: {'name' in d1}")  # checks KEYS, not values

# Merge (3.9+)
merged = {"a": 1} | {"a": 2, "b": 3}  # {'a':2,'b':3} — right wins

# ── 13. bytes & bytearray ──────────────────────────
# bytes: immutable, each element 0-255
b1 = b"hello"                         # ASCII bytes literal
b2 = bytes([72, 101])                 # from int list
b3 = "hello".encode("utf-8")          # str -> bytes
b4 = b"hello".decode("utf-8")         # bytes -> str
print(f"b1[0]={b1[0]}, hex={b1.hex()}")  # 104, 68656c6c6f

# bytearray: mutable version of bytes
ba = bytearray(b"hello")
ba[0] = 72                            # modify in place => b'Hello'
ba.append(33)                         # append '!'

# memoryview: zero-copy view into bytes/bytearray buffer
data = bytearray(b"Hello World")
mv = memoryview(data)
mv[6:11] = b"Earth"                   # modifies data in place
mv.release()

# ╔══════════════════════════════════════════════════╗
# ║                   ADVANCED                       ║
# ╚══════════════════════════════════════════════════╝

# ── 14. Enum ────────────────────────────────────────
class Color(Enum):
    RED = 1; GREEN = 2; BLUE = 3

class Direction(Enum):
    NORTH = auto(); SOUTH = auto()     # auto-assigned values

class Permission(IntEnum):             # comparable with ints
    READ = 4; WRITE = 2; EXECUTE = 1

class FileFlag(Flag):
    READ = auto(); WRITE = auto(); EXECUTE = auto()

print(f"Color.RED: name={Color.RED.name}, value={Color.RED.value}")
print(f"Color(1)={Color(1)}, Color['RED']={Color['RED']}")
combined = FileFlag.READ | FileFlag.WRITE
print(f"flags: {combined}, READ in it: {FileFlag.READ in combined}")  # True

# ── 15. Type Hints ──────────────────────────────────
# Not runtime types — static analysis only
numbers: list[int] = [1, 2, 3]        # 3.9+ built-in generics
mapping: dict[str, int] = {"a": 1}
maybe: Optional[str] = None           # str or None
flex: Union[int, str] = "hello"       # int or str
anything: Any = [1, "two"]
constant: Final = 42                  # should not reassign
direction: Literal["n", "s"] = "n"

def greet(name: str, times: int = 1) -> str:
    return f"Hello, {name}! " * times

def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

print(f"greet: {greet('Bob', 2)}")     # Hello, Bob! Hello, Bob!
print(f"apply: {apply(lambda a,b: a+b, 3, 4)}")  # 7

# ── 16. Collections Module ─────────────────────────
# defaultdict — auto-creates missing keys with factory
dd = defaultdict(int)
dd["a"] += 1; dd["b"] += 5
print(f"defaultdict: {dict(dd)}, missing={dd['x']}")  # {'a':1,'b':5}, 0

dd_list = defaultdict(list)
dd_list["fruits"].append("apple")      # no KeyError!

# Counter — count occurrences
cnt = Counter("abracadabra")
print(f"Counter: {cnt.most_common(2)}")  # [('a',5),('b',2)]

# deque — double-ended queue, O(1) append/pop both ends
dq = deque([1, 2, 3])
dq.appendleft(0); dq.append(4)        # [0,1,2,3,4]
dq.popleft()                          # remove from left
dq.rotate(1)                          # rotate right
bounded = deque(maxlen=3)             # auto-discards oldest when full
for i in range(5): bounded.append(i)
print(f"bounded: {bounded}")           # deque([2,3,4], maxlen=3)

# OrderedDict — remembers insertion order (redundant since dict 3.7+, but has move_to_end)
od = OrderedDict([("b", 2), ("a", 1)])
od.move_to_end("a")                   # move to end
od.move_to_end("b", last=False)       # move to beginning

# ChainMap — search multiple dicts as one
defaults = {"color": "blue", "size": "M"}
prefs = {"color": "red"}
cm = ChainMap(prefs, defaults)
print(f"ChainMap: color={cm['color']}, size={cm['size']}")  # red, M

# ── 17. dataclass ───────────────────────────────────
@dataclass
class Person:
    name: str
    age: int
    hobbies: list = field(default_factory=list)  # GOTCHA: never use mutable default!
    def greet(self): return f"Hi, I'm {self.name}!"

@dataclass(frozen=True)                # immutable dataclass
class Coordinate:
    x: float; y: float

p1 = Person("Alice", 30, ["reading"])
p2 = Person("Alice", 30, ["reading"])
print(f"dataclass: {p1}, eq={p1 == p2}")  # auto __eq__
# coord.x = 3.0 => FrozenInstanceError (frozen=True)

# typing.NamedTuple — typed immutable record
class Employee(NamedTuple):
    name: str; department: str; salary: float = 50000.0

emp = Employee("Bob", "Eng", 75000.0)
print(f"NamedTuple: {emp.name}, {emp[1]}")  # Bob, Eng

# TypedDict — type hints for dict (runtime is still plain dict)
class Movie(TypedDict):
    title: str; year: int; rating: float

movie: Movie = {"title": "Inception", "year": 2010, "rating": 8.8}
print(f"TypedDict type: {type(movie)}")  # <class 'dict'>

# ── 18. Iterator & Generator ───────────────────────
# Iterator protocol: __iter__() + __next__()
it = iter([10, 20, 30])
print(f"next: {next(it)}, {next(it)}, {next(it)}")  # 10, 20, 30
# next(it) => StopIteration

# Custom iterator
class Countdown:
    def __init__(self, start): self.start = start
    def __iter__(self): return self
    def __next__(self):
        if self.start <= 0: raise StopIteration
        self.start -= 1
        return self.start + 1

print(f"Countdown: {list(Countdown(3))}")  # [3, 2, 1]

# Generator — lazy iterator via yield
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

print(f"fib: {list(fibonacci(8))}")    # [0,1,1,2,3,5,8,13]

# Generator expression (lazy list comprehension)
gen = (x**2 for x in range(5))
print(f"genexpr: {list(gen)}")         # [0,1,4,9,16]

# Generator with send()
def accumulator():
    total = 0
    while True:
        value = yield total
        if value is None: break
        total += value

acc = accumulator()
next(acc)                              # prime the generator
print(f"send: {acc.send(10)}, {acc.send(20)}")  # 10, 30

# ── 19. Callable Types ─────────────────────────────
def add(a, b): return a + b           # function
multiply = lambda a, b: a * b         # lambda

class Multiplier:                      # callable object (__call__)
    def __init__(self, factor): self.factor = factor
    def __call__(self, value): return value * self.factor

double = Multiplier(2)
print(f"callable obj: {double(5)}, callable={callable(double)}")  # 10, True

# Closure
def make_adder(n):
    def adder(x): return x + n
    return adder
add5 = make_adder(5)
print(f"closure: {add5(10)}")          # 15

# Partial
add10 = partial(add, 10)
print(f"partial: {add10(5)}")          # 15

# ── 20. Context Manager ────────────────────────────
class ManagedResource:
    def __enter__(self):
        print("  acquired"); return self
    def __exit__(self, *args):
        print("  released"); return False

@contextmanager
def managed():
    print("  setup"); yield "value"; print("  teardown")

with ManagedResource(): pass           # acquired -> released
with managed() as v: print(f"  val={v}")  # setup -> val=value -> teardown

# ── 21. Regex Match ─────────────────────────────────
match = re.search(r"(\d{4})-(\d{2})-(\d{2})", "Date: 2024-01-15!")
if match:
    print(f"match: {match.group()}, groups={match.groups()}, span={match.span()}")
    # 2024-01-15, ('2024','01','15'), (6,16)

# ── 22. datetime ────────────────────────────────────
d = date(2024, 1, 15); today = date.today()
print(f"date: {d}, weekday={d.weekday()}")  # 0=Monday
print(f"strftime: {d.strftime('%B %d, %Y')}")  # January 15, 2024

dt = datetime(2024, 1, 15, 14, 30, 45)
now = datetime.now(); utc = datetime.now(timezone.utc)
parsed = datetime.strptime("2024-01-15", "%Y-%m-%d")

delta = timedelta(days=7, hours=3)
print(f"delta: {delta}, total_sec={delta.total_seconds()}")
print(f"date+delta: {d + delta}")      # 2024-01-22

# ── 23. Decimal & Fraction ──────────────────────────
# Decimal — exact decimal arithmetic (no float rounding)
print(f"Decimal: {Decimal('0.1') + Decimal('0.2')}")  # 0.3  (exact!)
print(f"float:   {0.1 + 0.2}")                        # 0.300...04  (inexact)
getcontext().prec = 50                 # set precision

# Fraction — exact rational arithmetic
f1 = Fraction(1, 3); f2 = Fraction(1, 6)
print(f"Fraction: {f1}+{f2}={f1+f2}")  # 1/3+1/6=1/2
print(f"from str: {Fraction('7/3')}")   # 7/3
print(f"pi approx: {Fraction(3.14159).limit_denominator(100)}")  # 311/99

# ── 24. Path ────────────────────────────────────────
p = Path(".")
print(f"cwd={Path.cwd()}, home={Path.home()}, exists={p.exists()}")
p2 = Path("folder") / "sub" / "file.txt"  # path joining with /
print(f"parent={p2.parent}, stem={p2.stem}, suffix={p2.suffix}")

# ── 25. Queue Types (Thread-safe) ───────────────────
q = Queue(maxsize=3); q.put("a"); q.put("b")
print(f"FIFO: {q.get()}")             # a

lq = LifoQueue(); lq.put("a"); lq.put("b")
print(f"LIFO: {lq.get()}")            # b (stack)

pq = PriorityQueue()
pq.put((2, "med")); pq.put((1, "high")); pq.put((3, "low"))
print(f"Priority: {pq.get()}")        # (1, 'high')

# ── 26. Special Types ──────────────────────────────
# type() — the type of types (metaclass)
print(f"type(42)={type(42)}, type(int)={type(int)}, type(type)={type(type)}")
MyClass = type("MyClass", (object,), {"x": 10})  # dynamic class creation

# object — base class of everything
print(f"isinstance(42, object)={isinstance(42, object)}")  # True

# Ellipsis — placeholder in stubs, NumPy slicing
print(f"... is Ellipsis: {... is Ellipsis}")  # True

# weakref — reference that doesn't prevent GC
class MyObj:
    def __init__(self, name): self.name = name
obj = MyObj("test"); weak = weakref.ref(obj)
print(f"weakref alive: {weak().name}")  # test
del obj
print(f"weakref dead: {weak()}")        # None

# ── 27. Type Checking Utilities ─────────────────────
# type() vs isinstance()
print(f"type(42)==int: {type(42)==int}")                   # True
print(f"isinstance(True,int): {isinstance(True,int)}")    # True  GOTCHA: bool IS int
print(f"isinstance(42,(int,float)): {isinstance(42,(int,float))}")  # tuple of types

# issubclass()
print(f"issubclass(bool,int): {issubclass(bool,int)}")    # True

# is vs ==
a_id = [1,2]; b_id = a_id; c_id = [1,2]
print(f"a is b: {a_id is b_id}, a is c: {a_id is c_id}, a==c: {a_id==c_id}")
# True (same obj), False (diff obj), True (same value)


# ══════════════════════════════════════════════════════════════════
# CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
print()
print("=" * 70)
print("PYTHON DATA TYPES CHEAT SHEET")
print("=" * 70)
print(f"""
{'Type':<15} {'Mutable':<9} {'Ordered':<9} {'Hashable':<10} {'Literal Syntax'}
{'-'*15} {'-'*9} {'-'*9} {'-'*10} {'-'*25}
{'int':<15} {'No':<9} {'N/A':<9} {'Yes':<10} 42, 0xFF, 0b1010
{'float':<15} {'No':<9} {'N/A':<9} {'Yes':<10} 3.14, 1e-3, float("inf")
{'complex':<15} {'No':<9} {'N/A':<9} {'Yes':<10} 3+4j
{'bool':<15} {'No':<9} {'N/A':<9} {'Yes':<10} True, False
{'str':<15} {'No':<9} {'Yes':<9} {'Yes':<10} "hello", f"{{x}}"
{'bytes':<15} {'No':<9} {'Yes':<9} {'Yes':<10} b"hello"
{'bytearray':<15} {'Yes':<9} {'Yes':<9} {'No':<10} bytearray(b"hi")
{'list':<15} {'Yes':<9} {'Yes':<9} {'No':<10} [1, 2, 3]
{'tuple':<15} {'No':<9} {'Yes':<9} {'Yes*':<10} (1, 2, 3)
{'range':<15} {'No':<9} {'Yes':<9} {'Yes':<10} range(10)
{'set':<15} {'Yes':<9} {'No':<9} {'No':<10} {{1, 2, 3}}
{'frozenset':<15} {'No':<9} {'No':<9} {'Yes':<10} frozenset([1,2])
{'dict':<15} {'Yes':<9} {'Yes**':<9} {'No':<10} {{"a": 1}}
{'NoneType':<15} {'N/A':<9} {'N/A':<9} {'Yes':<10} None
{'Decimal':<15} {'No':<9} {'N/A':<9} {'Yes':<10} Decimal("0.1")
{'Fraction':<15} {'No':<9} {'N/A':<9} {'Yes':<10} Fraction(1, 3)

*  tuple hashable only if all elements hashable
** dict insertion-ordered since Python 3.7

KEY GOTCHAS:
  {{}} is dict, NOT set        -> use set() for empty set
  (1) is int, NOT tuple       -> use (1,) for single-element tuple
  0.1+0.2 != 0.3              -> use math.isclose() or Decimal
  bool("False") is True       -> non-empty string is truthy
  isinstance(True, int)=True  -> bool is subclass of int
  mutable default args shared -> use field(default_factory=list)
  list.sort() returns None    -> use sorted() for new list
""")
