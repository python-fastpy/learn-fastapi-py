# ══════════════════════════════════════════════════════════════════
# PYTHON FUNCTIONS — Essential Guide (Basic → Advanced)
# ══════════════════════════════════════════════════════════════════

# ╔══════════════════════════════════════════════════╗
# ║  BEGINNER                                        ║
# ╚══════════════════════════════════════════════════╝

# ── 1. Basics — def, return, None ──────────────────

def greet(name):
    return f"Hello, {name}!"

print(greet("Alice"))           # Hello, Alice!

def no_return():
    x = 5 + 3

print(no_return())              # None  (no return = returns None)

def early_exit(x):
    if x < 0: return "negative" # function STOPS here
    return "positive"           # only runs if x >= 0

# Parameter = placeholder in def  |  Argument = actual value when calling
# def greet(name):   ← PARAMETER  |  greet("Alice")  ← ARGUMENT

def add(a, b):       # a, b = parameters
    return a + b
print(add(3, 5))     # 3, 5 = arguments  →  8


# ── 2. Default values ─────────────────────────────

def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

print(greet("Alice"))              # Hello, Alice!     (uses default)
print(greet("Bob", "Hi"))          # Hi, Bob!          (overrides default)

# DANGER: Mutable default is SHARED across calls
# BAD:  def f(items=[])   → same list every call!
# GOOD: def f(items=None) → new list each call

def bad(items=[]):
    items.append(1); return items
print(bad())                 # [1]
print(bad())                 # [1, 1]  ← NOT [1]!

def good(items=None):
    if items is None: items = []
    items.append(1); return items
print(good())                # [1]
print(good())                # [1]  ← correct


# ── 3. Positional vs Keyword arguments ─────────────
# Positional: order matters         → f("Alice", 30)
# Keyword:   name matters           → f(age=30, name="Alice")
# Mixed:     positional FIRST       → f("Alice", age=30)  OK
#            keyword first = ERROR  → f(name="Alice", 30)  ERROR

def register(name, age, email):
    return f"{name}, {age}, {email}"

print(register("Alice", 30, "a@test.com"))                # positional
print(register(email="b@test.com", name="Bob", age=25))   # keyword
print(register("Charlie", email="c@test.com", age=35))    # mixed

# Skip middle defaults using keyword
def setup(host, port=8000, debug=False, workers=4):
    return f"{host}:{port} debug={debug} workers={workers}"
print(setup("localhost", debug=True))     # skip port, set debug


# ── 4. Return multiple values ──────────────────────

def min_max(numbers):
    return min(numbers), max(numbers)   # returns a tuple

low, high = min_max([5, 2, 8, 1, 9])   # unpack into 2 vars
print(f"low={low}, high={high}")        # low=1, high=9

def analyze(nums):
    return {"sum": sum(nums), "avg": sum(nums) / len(nums)}
print(analyze([10, 20, 30]))            # {'sum': 60, 'avg': 20.0}


# ── 5. Error handling ─────────────────────────────

def divide(a, b):
    if b == 0: raise ValueError("Cannot divide by zero")
    return a / b

try:
    print(divide(10, 0))
except ValueError as e:
    print(f"Error: {e}")                # Error: Cannot divide by zero

def safe_int(val, default=0):
    try: return int(val)
    except (ValueError, TypeError): return default

print(safe_int("42"))       # 42
print(safe_int("abc"))      # 0


# ╔══════════════════════════════════════════════════╗
# ║  INTERMEDIATE                                    ║
# ╚══════════════════════════════════════════════════╝

# ── 6. *args vs **kwargs ──────────────────────────
#  *args    → collects positional → tuple    → f(1, 2, 3)
#  **kwargs → collects keyword    → dict     → f(a=1, b=2)

def add_all(*args):
    return sum(args)           # args is a tuple
print(add_all(1, 2, 3))       # 6

def show(**kwargs):
    for k, v in kwargs.items():
        print(f"  {k}={v}")
show(name="Alice", age=30)    # name=Alice  age=30

# Both together — ORDER: regular, *args, **kwargs
def log(level, *tags, **meta):
    print(f"  [{level}] tags={tags} meta={meta}")
log("INFO", "db", "slow", host="prod", latency=200)
# [INFO] tags=('db', 'slow') meta={'host': 'prod', 'latency': 200}


# ── 7. Keyword-only (*) vs Positional-only (/) ────
#  After *  → MUST use name=       →  def f(*, x):   f(x=5) OK, f(5) ERROR
#  Before / → CANNOT use name=     →  def f(x, /):   f(5) OK, f(x=5) ERROR

def connect(host, port, *, timeout=30, ssl=True):
    return f"{host}:{port} timeout={timeout}"
print(connect("localhost", 8080, timeout=60))   # OK
# connect("localhost", 8080, 60)                # TypeError!

def divide(a, b, /):
    return a / b
print(divide(10, 3))       # OK → 3.333...
# divide(a=10, b=3)        # TypeError!

# Full combo:  positional-only / normal * keyword-only
def hybrid(a, b, /, c, d, *, e):
    return f"a={a} b={b} c={c} d={d} e={e}"
print(hybrid(1, 2, 3, d=4, e=5))


# ── 8. Unpacking when calling (* vs **) ───────────
#  *list   → unpacks into positional   f(*[1,2,3])  = f(1,2,3)
#  **dict  → unpacks into keyword      f(**{"a":1}) = f(a=1)

def add3(a, b, c): return a + b + c

print(add3(*[10, 20, 30]))                    # 60
print(add3(**{"a": 1, "b": 2, "c": 3}))      # 6

# Forwarding — pass everything through
def wrapper(*args, **kwargs):
    return add3(*args, **kwargs)
print(wrapper(1, 2, 3))       # 6


# ── 9. Lambda vs def ──────────────────────────────
#  def    → named, multi-line, any logic
#  lambda → anonymous, ONE expression only, best for sorted/map/filter

double = lambda x: x * 2
classify = lambda x: "pos" if x > 0 else "neg" if x < 0 else "zero"
print(double(5))             # 10
print(classify(-3))          # neg

users = [("Bob", 25), ("Alice", 30), ("Charlie", 20)]
print(sorted(users, key=lambda u: u[1]))      # sort by age

nums = [1, 2, 3, 4, 5, 6, 7, 8]
print(list(filter(lambda n: n % 2 == 0, nums)))   # [2, 4, 6, 8]
print(list(map(lambda n: n ** 2, nums)))           # [1, 4, 9, 16, ...]


# ── 10. map vs filter vs reduce ───────────────────
#  map()    → transform each item      → list → list
#  filter() → keep items where True    → list → list
#  reduce() → combine all into one     → list → value

from functools import reduce
nums = [1, 2, 3, 4, 5]
print(list(map(lambda x: x * 2, nums)))       # [2, 4, 6, 8, 10]
print(list(filter(lambda x: x > 3, nums)))    # [4, 5]
print(reduce(lambda acc, x: acc + x, nums))   # 15


# ── 11. First-class functions ─────────────────────
# Functions ARE objects — assign, pass, store them

yell = str.upper
print(yell("hello"))                  # HELLO

def apply(func, value): return func(value)
print(apply(len, "hello"))            # 5

# Dispatch pattern — store in dict
ops = {"+": lambda a, b: a + b, "-": lambda a, b: a - b}
print(ops["+"](10, 3))               # 13


# ── 12. global vs nonlocal  (Scope: LEGB) ─────────
#  global   → modify MODULE-level variable
#  nonlocal → modify ENCLOSING function var
#  LEGB: Local → Enclosing → Global → Built-in

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


# ── 13. Type hints + Docstrings ────────────────────
# Hints = for humans & tools (NOT enforced at runtime)

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

# ── 14. Closure — function that remembers outer vars
#  Regular → no memory between calls
#  Closure → remembers outer function's vars, even after it exits

def make_multiplier(factor):
    def multiply(x): return x * factor  # remembers factor
    return multiply

double = make_multiplier(2)
triple = make_multiplier(3)
print(f"double(5)={double(5)}, triple(5)={triple(5)}")   # 10, 15

# Closure with mutable state
def make_counter():
    count = 0
    def increment():
        nonlocal count
        count += 1
        return count
    return increment

c = make_counter()
print(f"{c()}, {c()}, {c()}")    # 1, 2, 3


# ── 15. return vs yield (Generator) ───────────────
#  return → sends ONE value, function ENDS
#  yield  → sends ONE value, function PAUSES, resumes on next()
#  Generators are memory efficient — no full list in RAM

def get_squares_list(n):         # builds ENTIRE list in memory
    return [x**2 for x in range(n)]

def get_squares_gen(n):          # yields ONE at a time (lazy)
    for x in range(n):
        yield x**2

print(list(get_squares_gen(5)))   # [0, 1, 4, 9, 16]

gen = get_squares_gen(3)
print(next(gen), next(gen), next(gen))   # 0 1 4
# next(gen)  → StopIteration

# Infinite generator — impossible with return!
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
gen_exp = (x**2 for x in range(5))    # lazy — uses ()
lst_cmp = [x**2 for x in range(5)]    # eager — builds full list


# ── 16. Decorators ────────────────────────────────
# @decorator = shorthand for func = decorator(func)

import functools, time

def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"  {func.__name__} took {time.time()-start:.4f}s")
        return result
    return wrapper

@timer
def slow(): return sum(range(1_000_000))
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
def say(word): return word
print(say("hi"))     # ['hi', 'hi', 'hi']


# ── 17. Recursion ─────────────────────────────────
# Function calls itself — MUST have base case or → crash

def factorial(n):
    if n <= 1: return 1              # base case
    return n * factorial(n - 1)      # recursive case
print(f"5! = {factorial(5)}")        # 120

def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list): result.extend(flatten(item))
        else: result.append(item)
    return result
print(flatten([1, [2, [3, [4]]]]))   # [1, 2, 3, 4]


# ── 18. Memoization — @lru_cache ──────────────────
# Caches return values by arguments — makes repeated calls instant

@functools.lru_cache(maxsize=128)
def fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)

print(f"fib(50) = {fib(50)}")        # instant! (without cache → years)
print(f"Cache: {fib.cache_info()}")
fib.cache_clear()                    # reset cache


# ── 19. Partial — pre-fill arguments ──────────────

from functools import partial

def power(base, exp): return base ** exp
square = partial(power, exp=2)
cube   = partial(power, exp=3)
print(f"square(5)={square(5)}, cube(3)={cube(3)}")   # 25, 27


# ── 20. Common patterns ──────────────────────────

# Callback — pass a function to run later
def process(data, on_done):
    on_done([x * 2 for x in data])
process([1, 2, 3], lambda r: print(f"Done: {r}"))   # Done: [2, 4, 6]

# Composition — chain functions left to right
def pipe(*fns):
    def piped(x):
        for f in fns: x = f(x)
        return x
    return piped
clean = pipe(str.strip, str.lower, str.split)
print(clean("  Hello World  "))    # ['hello', 'world']

# Registry — decorator that registers handlers
registry = {}
def register(name):
    def dec(fn): registry[name] = fn; return fn
    return dec

@register("greet")
def greet_handler(data): return f"Hello, {data}!"
print(registry["greet"]("Alice"))   # Hello, Alice!


# ── 21. Function introspection ────────────────────

def example(a: int, b: str = "hi") -> str:
    """Example function."""
    return f"{a} {b}"

print(f"__name__:     {example.__name__}")         # example
print(f"__doc__:      {example.__doc__}")           # Example function.
print(f"__defaults__: {example.__defaults__}")      # ('hi',)
print(f"callable:     {callable(example)}")         # True


# ══════════════════════════════════════════════════════════════════
# CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
#
#  DEFINITION                            CALLING
#  ────────────────────────────────────   ──────────────────────────
#  def f(a, b):         regular          f(1, 2)        positional
#  def f(a, b=10):      default          f(a=1, b=2)    keyword
#  def f(*args):        → tuple          f(*[1,2])      unpack list
#  def f(**kwargs):     → dict           f(**{"a":1})   unpack dict
#  def f(a, /, b, *, c): pos/kw-only
#  lambda a, b: a + b   one-liner
#
#  RETURN                                SCOPE (LEGB)
#  ────────────────────────────────────   ──────────────────────────
#  return x         single value         Local → Enclosing →
#  return x, y      tuple                  Global → Built-in
#  no return        → None               global x    module-level
#  yield x          generator (lazy)     nonlocal x  enclosing func
#
#  KEY TOOLS                             BEST PRACTICES
#  ────────────────────────────────────   ──────────────────────────
#  map(fn, list)    transform each       Never def f(items=[])
#  filter(fn, list) keep where True       → use def f(items=None)
#  reduce(fn, list) combine into one     Guard clauses: validate early
#  partial(fn, arg) pre-fill args        One function = one job
#  @lru_cache       cache by args        Type hints: def f(x: int)
#  @decorator       wrap behavior
