# ══════════════════════════════════════════════════════════════════
# PYTHON FUNCTIONS — Essential Guide (Basic → Advanced)
# ══════════════════════════════════════════════════════════════════


# ╔══════════════════════════════════════════════════╗
# ║  BEGINNER                                        ║
# ╚══════════════════════════════════════════════════╝


# ════════════════════════════════════════════════════
# 1. Basics — def, return, None
# ════════════════════════════════════════════════════

def greet(name):
    return f"Hello, {name}!"

print(greet("Alice"))           # Hello, Alice!

def no_return():
    x = 5 + 3

print(no_return())              # None  (no return = returns None)

def early_exit(x):
    if x < 0:
        return "negative"       # function STOPS here
    return "positive"           # only runs if x >= 0


# ════════════════════════════════════════════════════
# 2. Parameter vs Argument
#
#  ┌──────────────────────────────────────────────────┐
#  │  PARAMETER = placeholder (in definition)         │
#  │  ARGUMENT  = actual value (when calling)         │
#  │                                                  │
#  │  def greet(name):     ← name is PARAMETER        │
#  │  greet("Alice")       ← "Alice" is ARGUMENT      │
#  └──────────────────────────────────────────────────┘
# ════════════════════════════════════════════════════

def add(a, b):       # a, b = parameters
    return a + b

print(add(3, 5))     # 3, 5 = arguments  →  8


# ════════════════════════════════════════════════════
# 3. Default values
# ════════════════════════════════════════════════════

def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

print(greet("Alice"))              # Hello, Alice!     (uses default)
print(greet("Bob", "Hi"))          # Hi, Bob!          (overrides default)

# ┌──────────────────────────────────────────────────────────────┐
# │  DANGER: Mutable default (list/dict) is SHARED across calls │
# │                                                              │
# │  BAD:  def f(items=[])        → same list every call!       │
# │  GOOD: def f(items=None)      → new list each call          │
# └──────────────────────────────────────────────────────────────┘

def bad(items=[]):           # BUG — shared list
    items.append(1)
    return items

print(bad())                 # [1]
print(bad())                 # [1, 1]  ← NOT [1]!

def good(items=None):        # CORRECT
    if items is None:
        items = []
    items.append(1)
    return items

print(good())                # [1]
print(good())                # [1]  ← correct


# ════════════════════════════════════════════════════
# 4. COMPARISON: Positional vs Keyword arguments
#
#  ┌──────────────┬──────────────────────────────────┐
#  │ Positional   │ Order matters                    │
#  │              │ f("Alice", 30)                   │
#  ├──────────────┼──────────────────────────────────┤
#  │ Keyword      │ Name matters, order doesn't      │
#  │              │ f(age=30, name="Alice")          │
#  ├──────────────┼──────────────────────────────────┤
#  │ Mixed        │ Positional FIRST, then keyword   │
#  │              │ f("Alice", age=30)       OK      │
#  │              │ f(name="Alice", 30)      ERROR   │
#  └──────────────┴──────────────────────────────────┘
# ════════════════════════════════════════════════════

def register(name, age, email):
    return f"{name}, {age}, {email}"

print(register("Alice", 30, "a@test.com"))                # positional
print(register(email="b@test.com", name="Bob", age=25))   # keyword (any order)
print(register("Charlie", email="c@test.com", age=35))    # mixed

# Skip middle defaults using keyword
def setup(host, port=8000, debug=False, workers=4):
    return f"{host}:{port} debug={debug} workers={workers}"

print(setup("localhost", debug=True))     # skip port, set debug


# ════════════════════════════════════════════════════
# 5. Return multiple values
# ════════════════════════════════════════════════════

def min_max(numbers):
    return min(numbers), max(numbers)   # returns a tuple

result = min_max([5, 2, 8, 1, 9])      # (1, 9)
low, high = min_max([5, 2, 8, 1, 9])   # unpack into 2 vars
print(f"low={low}, high={high}")        # low=1, high=9

# Return dict when you have many values
def analyze(nums):
    return {"sum": sum(nums), "avg": sum(nums) / len(nums)}

print(analyze([10, 20, 30]))            # {'sum': 60, 'avg': 20.0}


# ════════════════════════════════════════════════════
# 6. Error handling in functions
# ════════════════════════════════════════════════════

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

try:
    print(divide(10, 0))
except ValueError as e:
    print(f"Error: {e}")                # Error: Cannot divide by zero

def safe_int(val, default=0):
    try:
        return int(val)
    except (ValueError, TypeError):
        return default

print(safe_int("42"))       # 42
print(safe_int("abc"))      # 0


# ╔══════════════════════════════════════════════════╗
# ║  INTERMEDIATE                                    ║
# ╚══════════════════════════════════════════════════╝


# ════════════════════════════════════════════════════
# 7. COMPARISON: *args vs **kwargs
#
#  ┌──────────┬────────────┬──────────────────────────┐
#  │          │  *args     │  **kwargs                │
#  ├──────────┼────────────┼──────────────────────────┤
#  │ Collects │ positional │ keyword                  │
#  │ Type     │ tuple      │ dict                     │
#  │ Syntax   │ *args      │ **kwargs                 │
#  │ Example  │ f(1, 2, 3) │ f(a=1, b=2)             │
#  │ Inside   │ (1, 2, 3)  │ {'a': 1, 'b': 2}        │
#  └──────────┴────────────┴──────────────────────────┘
# ════════════════════════════════════════════════════

# *args — collects extra positional args into a TUPLE
def add_all(*args):
    return sum(args)           # args is a tuple

print(add_all(1, 2, 3))       # 6
print(add_all())               # 0

# **kwargs — collects extra keyword args into a DICT
def show(**kwargs):
    for k, v in kwargs.items():
        print(f"  {k}={v}")

show(name="Alice", age=30)    # name=Alice  age=30

# Both together — ORDER: regular, *args, **kwargs
def log(level, *tags, **meta):
    print(f"  [{level}] tags={tags} meta={meta}")

log("INFO", "db", "slow", host="prod", latency=200)
# [INFO] tags=('db', 'slow') meta={'host': 'prod', 'latency': 200}


# ════════════════════════════════════════════════════
# 8. COMPARISON: Keyword-only (*)  vs  Positional-only (/)
#
#  ┌──────────────────┬────────────────────────────────┐
#  │ Keyword-only     │ After * — MUST use name=       │
#  │   def f(*, x)    │ f(x=5)  OK    f(5)  ERROR     │
#  ├──────────────────┼────────────────────────────────┤
#  │ Positional-only  │ Before / — CANNOT use name=    │
#  │   def f(x, /)    │ f(5)    OK    f(x=5)  ERROR   │
#  └──────────────────┴────────────────────────────────┘
# ════════════════════════════════════════════════════

# Keyword-only: everything AFTER * must be keyword
def connect(host, port, *, timeout=30, ssl=True):
    return f"{host}:{port} timeout={timeout}"

print(connect("localhost", 8080, timeout=60))   # OK
# connect("localhost", 8080, 60)                # TypeError!

# Positional-only: everything BEFORE / must be positional
def divide(a, b, /):
    return a / b

print(divide(10, 3))       # OK → 3.333...
# divide(a=10, b=3)        # TypeError!

# Full combo:  positional-only / normal * keyword-only
def hybrid(a, b, /, c, d, *, e):
    return f"a={a} b={b} c={c} d={d} e={e}"

print(hybrid(1, 2, 3, d=4, e=5))
# a,b → positional-only  |  c,d → either  |  e → keyword-only


# ════════════════════════════════════════════════════
# 9. Unpacking when CALLING (* vs **)
#
#  ┌───────────────────────────────────────────────────┐
#  │  *list/tuple  → unpacks into positional args      │
#  │  **dict       → unpacks into keyword args         │
#  └───────────────────────────────────────────────────┘
# ════════════════════════════════════════════════════

def add3(a, b, c):
    return a + b + c

print(add3(*[10, 20, 30]))                    # 60 — unpack list
print(add3(**{"a": 1, "b": 2, "c": 3}))      # 6  — unpack dict

# Forwarding — pass everything through to another function
def wrapper(*args, **kwargs):
    return add3(*args, **kwargs)

print(wrapper(1, 2, 3))       # 6


# ════════════════════════════════════════════════════
# 10. COMPARISON: Lambda vs def
#
#  ┌────────┬──────────────────────────────────────────┐
#  │ def    │ Named, multi-line, any logic             │
#  │ lambda │ Anonymous, ONE expression only           │
#  │        │ Best for sorted/map/filter               │
#  └────────┴──────────────────────────────────────────┘
# ════════════════════════════════════════════════════

double = lambda x: x * 2
classify = lambda x: "pos" if x > 0 else "neg" if x < 0 else "zero"

print(double(5))             # 10
print(classify(-3))          # neg

# Lambda shines with sorting / filtering
users = [("Bob", 25), ("Alice", 30), ("Charlie", 20)]
print(sorted(users, key=lambda u: u[1]))      # sort by age

nums = [1, 2, 3, 4, 5, 6, 7, 8]
print(list(filter(lambda n: n % 2 == 0, nums)))   # [2, 4, 6, 8]
print(list(map(lambda n: n ** 2, nums)))           # [1, 4, 9, 16, ...]


# ════════════════════════════════════════════════════
# 11. COMPARISON: map vs filter vs reduce
#
#  ┌──────────┬──────────────────────────┬──────────────┐
#  │ map()    │ Transform EACH item      │ list → list  │
#  │ filter() │ Keep items where True    │ list → list  │
#  │ reduce() │ Combine ALL into ONE     │ list → value │
#  └──────────┴──────────────────────────┴──────────────┘
# ════════════════════════════════════════════════════

from functools import reduce

nums = [1, 2, 3, 4, 5]

mapped   = list(map(lambda x: x * 2, nums))       # [2, 4, 6, 8, 10]
filtered = list(filter(lambda x: x > 3, nums))    # [4, 5]
reduced  = reduce(lambda acc, x: acc + x, nums)   # 15

print(f"map:    {mapped}")
print(f"filter: {filtered}")
print(f"reduce: {reduced}")


# ════════════════════════════════════════════════════
# 12. First-class functions — functions ARE objects
# ════════════════════════════════════════════════════

# Assign to variable
yell = str.upper
print(yell("hello"))                  # HELLO

# Pass as argument
def apply(func, value):
    return func(value)

print(apply(str.upper, "hello"))      # HELLO
print(apply(len, "hello"))            # 5

# Store in dict (dispatch pattern)
ops = {"+": lambda a, b: a + b,
       "-": lambda a, b: a - b,
       "*": lambda a, b: a * b}

for sym in ops:
    print(f"  10 {sym} 3 = {ops[sym](10, 3)}")


# ════════════════════════════════════════════════════
# 13. COMPARISON: global vs nonlocal   (Scope: LEGB)
#
#  ┌──────────┬──────────────────────────────────────┐
#  │ global   │ Access/modify MODULE-level variable  │
#  │ nonlocal │ Access/modify ENCLOSING function var │
#  └──────────┴──────────────────────────────────────┘
#
#  LEGB lookup order:
#  L = Local → E = Enclosing → G = Global → B = Built-in
# ════════════════════════════════════════════════════

x = "global"

def demo_global():
    global x
    x = "modified by function"

demo_global()
print(x)            # modified by function

def outer():
    msg = "original"
    def inner():
        nonlocal msg
        msg = "changed"
    inner()
    return msg

print(outer())      # changed


# ════════════════════════════════════════════════════
# 14. Type hints + Docstrings
#
#  Hints = documentation for humans & tools (NOT enforced)
# ════════════════════════════════════════════════════

from typing import Optional

def find_user(user_id: int) -> Optional[dict]:
    """Look up a user by ID. Returns None if not found."""
    users = {1: {"name": "Alice"}}
    return users.get(user_id)

print(find_user(1))        # {'name': 'Alice'}
print(find_user(99))       # None


# ╔══════════════════════════════════════════════════╗
# ║  ADVANCED                                        ║
# ╚══════════════════════════════════════════════════╝


# ════════════════════════════════════════════════════
# 15. COMPARISON: Closure vs Regular function
#
#  ┌──────────────┬──────────────────────────────────┐
#  │ Regular      │ No memory between calls          │
#  │ Closure      │ Remembers outer function's vars  │
#  │              │ Even after outer function exits   │
#  └──────────────┴──────────────────────────────────┘
# ════════════════════════════════════════════════════

def make_multiplier(factor):      # outer function
    def multiply(x):              # inner (closure) — remembers factor
        return x * factor
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)
print(f"double(5)={double(5)}, triple(5)={triple(5)}")   # 10, 15

# Closure with state (using nonlocal)
def make_counter():
    count = 0
    def increment():
        nonlocal count
        count += 1
        return count
    return increment

c = make_counter()
print(f"{c()}, {c()}, {c()}")    # 1, 2, 3


# ════════════════════════════════════════════════════
# 16. COMPARISON: return vs yield  (Generator)
#
#  ┌──────────┬──────────────────────────────────────────┐
#  │ return   │ Sends ONE value, function ENDS           │
#  │ yield    │ Sends ONE value, function PAUSES         │
#  │          │ Resumes on next() — remembers state      │
#  │          │ Memory efficient — no full list in RAM   │
#  └──────────┴──────────────────────────────────────────┘
# ════════════════════════════════════════════════════

# Regular — builds entire list in memory
def get_squares_list(n):
    return [x**2 for x in range(n)]

# Generator — yields one at a time (lazy)
def get_squares_gen(n):
    for x in range(n):
        yield x**2

print(list(get_squares_gen(5)))   # [0, 1, 4, 9, 16]

# Manual iteration
gen = get_squares_gen(3)
print(next(gen))   # 0
print(next(gen))   # 1
print(next(gen))   # 4
# next(gen)        # StopIteration

# Infinite generator — impossible with list!
def count_forever(start=0):
    n = start
    while True:
        yield n
        n += 1

counter = count_forever()
print([next(counter) for _ in range(5)])   # [0, 1, 2, 3, 4]

# yield from — delegate to another iterable
def combined():
    yield from range(3)       # 0, 1, 2
    yield from range(10, 13)  # 10, 11, 12

print(list(combined()))       # [0, 1, 2, 10, 11, 12]

# Generator expression vs list comprehension
gen_exp = (x**2 for x in range(5))    # lazy — uses () not []
lst_cmp = [x**2 for x in range(5)]    # eager — builds full list


# ════════════════════════════════════════════════════
# 17. Decorators — modify a function's behavior
#
#  @decorator  is shorthand for  func = decorator(func)
# ════════════════════════════════════════════════════

import functools, time

def timer(func):
    @functools.wraps(func)          # preserve original name/doc
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"  {func.__name__} took {time.time()-start:.4f}s")
        return result
    return wrapper

@timer
def slow():
    return sum(range(1_000_000))

slow()

# Decorator WITH arguments (decorator factory)
def repeat(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return [func(*args, **kwargs) for _ in range(times)]
        return wrapper
    return decorator

@repeat(3)
def say(word):
    return word

print(say("hi"))     # ['hi', 'hi', 'hi']


# ════════════════════════════════════════════════════
# 18. Recursion — function calls itself
#
#  MUST have base case or → infinite loop → crash
# ════════════════════════════════════════════════════

def factorial(n):
    if n <= 1: return 1              # base case
    return n * factorial(n - 1)      # recursive case

print(f"5! = {factorial(5)}")        # 120

# Flatten nested list
def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result

print(flatten([1, [2, [3, [4]]]]))   # [1, 2, 3, 4]


# ════════════════════════════════════════════════════
# 19. Memoization — cache expensive results
#
#  @lru_cache = built-in — caches return values by args
# ════════════════════════════════════════════════════

@functools.lru_cache(maxsize=128)
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)

print(f"fib(50) = {fib(50)}")               # instant! (without cache → years)
print(f"Cache: {fib.cache_info()}")
fib.cache_clear()                            # reset cache


# ════════════════════════════════════════════════════
# 20. Partial — pre-fill some arguments
# ════════════════════════════════════════════════════

from functools import partial

def power(base, exp):
    return base ** exp

square = partial(power, exp=2)
cube   = partial(power, exp=3)

print(f"square(5)={square(5)}, cube(3)={cube(3)}")   # 25, 27


# ════════════════════════════════════════════════════
# 21. Common advanced patterns
# ════════════════════════════════════════════════════

# Callback — pass a function to be called later
def process(data, on_done):
    result = [x * 2 for x in data]
    on_done(result)

process([1, 2, 3], lambda r: print(f"Done: {r}"))   # Done: [2, 4, 6]

# Composition — chain functions
def pipe(*fns):
    def piped(x):
        for f in fns:
            x = f(x)
        return x
    return piped

clean = pipe(str.strip, str.lower, str.split)
print(clean("  Hello World  "))    # ['hello', 'world']

# Registry — decorator that registers handlers
registry = {}
def register(name):
    def dec(fn):
        registry[name] = fn
        return fn
    return dec

@register("greet")
def greet_handler(data):
    return f"Hello, {data}!"

print(registry["greet"]("Alice"))   # Hello, Alice!


# ════════════════════════════════════════════════════
# 22. Function introspection
# ════════════════════════════════════════════════════

def example(a: int, b: str = "hi") -> str:
    """Example function."""
    return f"{a} {b}"

print(f"__name__:        {example.__name__}")         # example
print(f"__doc__:         {example.__doc__}")           # Example function.
print(f"__defaults__:    {example.__defaults__}")      # ('hi',)
print(f"__annotations__: {example.__annotations__}")   # {'a': int, ...}
print(f"callable:        {callable(example)}")         # True


# ══════════════════════════════════════════════════════════════════
# CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
#
#  DEFINITION
#  ──────────────────────────────────────────────────
#  def f(a, b):             regular
#  def f(a, b=10):          default value
#  def f(*args):            variable positional → tuple
#  def f(**kwargs):         variable keyword → dict
#  def f(a, /, b, *, c):   a=pos-only, b=either, c=kw-only
#  lambda a, b: a + b      anonymous one-liner
#
#  CALLING
#  ──────────────────────────────────────────────────
#  f(1, 2)                 positional
#  f(a=1, b=2)             keyword
#  f(*[1,2])               unpack list → positional
#  f(**{"a":1})             unpack dict → keyword
#
#  RETURN
#  ──────────────────────────────────────────────────
#  return x                single value
#  return x, y             tuple (unpack with a, b = f())
#  no return               returns None
#  yield x                 generator — lazy, one at a time
#
#  SCOPE
#  ──────────────────────────────────────────────────
#  LEGB:  Local → Enclosing → Global → Built-in
#  global x                modify module-level var
#  nonlocal x              modify enclosing function var
#
#  KEY TOOLS
#  ──────────────────────────────────────────────────
#  map(fn, list)           transform each item
#  filter(fn, list)        keep where fn returns True
#  reduce(fn, list)        combine all into one value
#  partial(fn, arg)        pre-fill arguments
#  @lru_cache              cache results by arguments
#  @decorator              wrap/modify function behavior
#
#  BEST PRACTICES
#  ──────────────────────────────────────────────────
#  Never  def f(items=[])  → use  def f(items=None)
#  Guard clauses           → validate early, return early
#  One function = one job  → single responsibility
#  Type hints              → def f(x: int) -> str
