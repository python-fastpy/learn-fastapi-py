# ╔══════════════════════════════════════════════════════════════════════╗
# ║              PYTHON FUNCTIONS — All Concepts Master Guide           ║
# ║                                                                     ║
# ║  Function = reusable block of code that does ONE thing              ║
# ║  def function_name(parameters):                                     ║
# ║      body                                                           ║
# ║      return result                                                  ║
# ║                                                                     ║
# ║  Why functions?                                                     ║
# ║    1. Reusability — write once, use many times                      ║
# ║    2. Organization — break big problem into small pieces            ║
# ║    3. Readability — give meaningful names to code blocks            ║
# ║    4. Testing — test each piece independently                       ║
# ╚══════════════════════════════════════════════════════════════════════╝


# ════════════════════════════════════════════════════
# 1. Basic function — def, call, return
#
#  def = define a function
#  return = send a value back to the caller
#  If no return → function returns None
# ════════════════════════════════════════════════════

print("=" * 50)
print("1. Basic function")
print("=" * 50)

# Simplest function — no parameters, no return
def say_hello():
    print("  Hello!")

say_hello()    # call the function

# Function with return
def get_greeting():
    return "Hello from function!"

message = get_greeting()
print(f"  {message}")

# No return → returns None
def no_return():
    x = 5 + 3

result = no_return()
print(f"  No return value: {result}")    # None

# Return stops the function — code after return never runs
def early_return():
    return "I returned early"
    print("This NEVER runs")    # unreachable code

print(f"  {early_return()}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 2. Parameters and arguments
#
#  Parameter = variable in function definition (placeholder)
#  Argument  = actual value passed when calling
#
#  def greet(name):     ← name is a PARAMETER
#      print(name)
#  greet("Alice")       ← "Alice" is an ARGUMENT
# ════════════════════════════════════════════════════

print("2. Parameters and arguments")

def greet(name):                       # name = parameter
    return f"Hello, {name}!"

print(f"  {greet('Alice')}")           # "Alice" = argument
print(f"  {greet('Bob')}")

# Multiple parameters
def add(a, b):
    return a + b

print(f"  add(3, 5) = {add(3, 5)}")
print(f"  add(10, 20) = {add(10, 20)}")

# Parameters with different types
def describe(name, age, active):
    return f"{name}, age {age}, active={active}"

print(f"  {describe('Alice', 30, True)}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 3. Default parameter values
#
#  Give a parameter a default → it becomes optional
#  Required params MUST come before default params
# ════════════════════════════════════════════════════

print("3. Default parameters")

def greet_user(name, greeting="Hello"):    # greeting has default
    return f"{greeting}, {name}!"

print(f"  {greet_user('Alice')}")                  # uses default "Hello"
print(f"  {greet_user('Bob', 'Hi')}")              # overrides default
print(f"  {greet_user('Charlie', 'Hey there')}")

# Multiple defaults
def create_user(name, role="user", active=True, country="US"):
    return {"name": name, "role": role, "active": active, "country": country}

print(f"  {create_user('Alice')}")                          # all defaults
print(f"  {create_user('Bob', 'admin')}")                   # override role
print(f"  {create_user('Charlie', 'editor', False, 'UK')}")  # override all

# DANGER: mutable default argument — DON'T use list/dict as default
def bad_append(item, items=[]):    # BUG! same list shared across calls
    items.append(item)
    return items

print(f"  Bad: {bad_append('a')}")    # ['a']
print(f"  Bad: {bad_append('b')}")    # ['a', 'b'] — NOT ['b']!

# CORRECT way — use None as default
def good_append(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

print(f"  Good: {good_append('a')}")    # ['a']
print(f"  Good: {good_append('b')}")    # ['b'] — correct!

print("=" * 50)


# ════════════════════════════════════════════════════
# 4. Positional vs keyword arguments
#
#  Positional = order matters     → greet("Alice", 30)
#  Keyword    = name=value        → greet(name="Alice", age=30)
#  You can mix them, but positional must come FIRST
# ════════════════════════════════════════════════════

print("4. Positional vs keyword arguments")

def register(name, age, email):
    return f"{name}, {age}, {email}"

# All positional (order matters)
print(f"  Positional: {register('Alice', 30, 'alice@test.com')}")

# All keyword (order doesn't matter)
print(f"  Keyword: {register(email='bob@test.com', name='Bob', age=25)}")

# Mixed — positional first, then keyword
print(f"  Mixed: {register('Charlie', email='c@test.com', age=35)}")

# ERROR: positional after keyword
# register(name="Alice", 30, "email")    # SyntaxError!

# Skip middle defaults with keyword args
def setup(host, port=8000, debug=False, workers=4):
    return f"{host}:{port} debug={debug} workers={workers}"

print(f"  {setup('localhost')}")                            # all defaults
print(f"  {setup('localhost', debug=True)}")                # skip port, set debug
print(f"  {setup('localhost', workers=8, debug=True)}")     # skip port, set both

print("=" * 50)


# ════════════════════════════════════════════════════
# 5. *args — variable number of positional arguments
#
#  *args collects extra positional args into a TUPLE
#  Can pass 0, 1, 5, 100... arguments
#  "args" is convention — *numbers, *items work too
# ════════════════════════════════════════════════════

print("5. *args — variable positional arguments")

def add_all(*args):
    print(f"  args = {args}, type = {type(args)}")    # tuple
    return sum(args)

print(f"  add_all(1, 2, 3) = {add_all(1, 2, 3)}")
print(f"  add_all(10) = {add_all(10)}")
print(f"  add_all() = {add_all()}")

# *args with regular parameters
def greet_all(greeting, *names):
    for name in names:
        print(f"  {greeting}, {name}!")

greet_all("Hello", "Alice", "Bob", "Charlie")

# *args — find min and max
def stats(*numbers):
    if not numbers:
        return "No numbers"
    return {
        "count": len(numbers),
        "min": min(numbers),
        "max": max(numbers),
        "avg": sum(numbers) / len(numbers),
    }

print(f"  Stats: {stats(10, 20, 30, 40, 50)}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 6. **kwargs — variable number of keyword arguments
#
#  **kwargs collects extra keyword args into a DICT
#  "kwargs" is convention — **options, **config work too
# ════════════════════════════════════════════════════

print("6. **kwargs — variable keyword arguments")

def show_info(**kwargs):
    print(f"  kwargs = {kwargs}, type = {type(kwargs)}")    # dict
    for key, value in kwargs.items():
        print(f"    {key}: {value}")

show_info(name="Alice", age=30, city="NYC")

# **kwargs with regular parameters
def create_profile(name, **details):
    profile = {"name": name}
    profile.update(details)
    return profile

print(f"  {create_profile('Alice', age=30, job='dev', city='NYC')}")
print(f"  {create_profile('Bob')}")    # no extra kwargs — works fine

# Build HTML tag with **kwargs
def html_tag(tag, text, **attributes):
    attrs = " ".join(f'{k}="{v}"' for k, v in attributes.items())
    if attrs:
        return f"<{tag} {attrs}>{text}</{tag}>"
    return f"<{tag}>{text}</{tag}>"

print(f"  {html_tag('p', 'Hello')}")
print(f"  {html_tag('a', 'Click here', href='https://example.com', target='_blank')}")
print(f"  {html_tag('div', 'Content', id='main', style='color:red')}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 7. Combining all parameter types
#
#  ORDER MUST BE:
#  1. Regular positional
#  2. *args
#  3. Keyword-only (after *args)
#  4. **kwargs
#
#  def func(a, b, *args, key1, key2="default", **kwargs)
# ════════════════════════════════════════════════════

print("7. All parameter types combined")

def mega_function(a, b, *args, required_key, optional_key="default", **kwargs):
    print(f"  a={a}, b={b}")
    print(f"  *args={args}")
    print(f"  required_key={required_key}")
    print(f"  optional_key={optional_key}")
    print(f"  **kwargs={kwargs}")

mega_function(
    1, 2,                               # a, b (positional)
    3, 4, 5,                            # *args
    required_key="must_provide",        # keyword-only (after *args)
    optional_key="custom",              # keyword with default
    extra1="x", extra2="y",            # **kwargs
)

# Real-world example: logging function
def log(level, message, *tags, timestamp=None, **metadata):
    tag_str = f" [{', '.join(tags)}]" if tags else ""
    ts = timestamp or "now"
    meta = f" | {metadata}" if metadata else ""
    print(f"  [{level}] {ts}{tag_str} {message}{meta}")

log("INFO", "Server started")
log("ERROR", "Connection failed", "db", "critical", timestamp="10:30", host="prod", retry=3)

print("=" * 50)


# ════════════════════════════════════════════════════
# 8. Keyword-only arguments — force keyword usage
#
#  Parameters AFTER * must be passed as keywords
#  Prevents confusing positional argument order
# ════════════════════════════════════════════════════

print("8. Keyword-only arguments")

# Everything after * is keyword-only
def connect(host, port, *, timeout=30, ssl=True):
    return f"{host}:{port} timeout={timeout} ssl={ssl}"

print(f"  {connect('localhost', 8080)}")                   # works
print(f"  {connect('localhost', 8080, timeout=60)}")       # works
# connect("localhost", 8080, 60)    # TypeError! timeout is keyword-only

# All keyword-only (no positional at all)
def config(*, host, port, debug=False):
    return f"{host}:{port} debug={debug}"

print(f"  {config(host='localhost', port=8000)}")
# config("localhost", 8000)    # TypeError! all are keyword-only

print("=" * 50)


# ════════════════════════════════════════════════════
# 9. Positional-only arguments (Python 3.8+)
#
#  Parameters BEFORE / must be passed positionally
#  Can't use keyword for them
# ════════════════════════════════════════════════════

print("9. Positional-only arguments (/ syntax)")

def divide(a, b, /):    # a and b are positional-only
    return a / b

print(f"  divide(10, 3) = {divide(10, 3):.2f}")
# divide(a=10, b=3)    # TypeError! positional-only

# Mix: positional-only, normal, keyword-only
def hybrid(a, b, /, c, d, *, e, f=10):
    return f"a={a} b={b} c={c} d={d} e={e} f={f}"

print(f"  {hybrid(1, 2, 3, d=4, e=5)}")
# a,b = positional-only (before /)
# c,d = normal (positional or keyword)
# e,f = keyword-only (after *)

print("=" * 50)


# ════════════════════════════════════════════════════
# 10. Return multiple values
#
#  Python can return multiple values as a tuple
#  You can unpack them into separate variables
# ════════════════════════════════════════════════════

print("10. Return multiple values")

# Return tuple (most common)
def min_max(numbers):
    return min(numbers), max(numbers)    # returns a tuple

result = min_max([5, 2, 8, 1, 9])
print(f"  As tuple: {result}")           # (1, 9)

low, high = min_max([5, 2, 8, 1, 9])    # unpack
print(f"  Unpacked: low={low}, high={high}")

# Return dict (when you have many values)
def analyze(numbers):
    return {
        "count": len(numbers),
        "sum": sum(numbers),
        "avg": sum(numbers) / len(numbers),
        "min": min(numbers),
        "max": max(numbers),
    }

stats = analyze([10, 20, 30, 40, 50])
print(f"  Dict return: avg={stats['avg']}, min={stats['min']}")

# Return named tuple (best of both worlds)
from collections import namedtuple

Result = namedtuple("Result", ["min", "max", "avg"])

def analyze_v2(numbers):
    return Result(
        min=min(numbers),
        max=max(numbers),
        avg=sum(numbers) / len(numbers),
    )

r = analyze_v2([10, 20, 30])
print(f"  Named tuple: min={r.min}, max={r.max}, avg={r.avg}")

# Return bool + value (success pattern)
def safe_divide(a, b):
    if b == 0:
        return False, 0
    return True, a / b

success, value = safe_divide(10, 3)
print(f"  10/3: success={success}, value={value:.2f}")

success, value = safe_divide(10, 0)
print(f"  10/0: success={success}, value={value}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 11. Unpacking arguments — * and ** when CALLING
#
#  * unpacks a list/tuple into positional args
#  ** unpacks a dict into keyword args
# ════════════════════════════════════════════════════

print("11. Unpacking arguments in function calls")

def add_three(a, b, c):
    return a + b + c

# Unpack list/tuple into positional arguments
numbers = [10, 20, 30]
print(f"  *list: {add_three(*numbers)}")    # same as add_three(10, 20, 30)

coords = (1, 2, 3)
print(f"  *tuple: {add_three(*coords)}")

# Unpack dict into keyword arguments
params = {"a": 100, "b": 200, "c": 300}
print(f"  **dict: {add_three(**params)}")    # same as add_three(a=100, b=200, c=300)

# Mix unpacking
def create_user(name, age, city, role="user"):
    return f"{name}, {age}, {city}, {role}"

base = ("Alice", 30)
extra = {"city": "NYC", "role": "admin"}
print(f"  Mixed: {create_user(*base, **extra)}")

# Forwarding arguments to another function
def wrapper(*args, **kwargs):
    print(f"  Forwarding args={args}, kwargs={kwargs}")
    return add_three(*args, **kwargs)

print(f"  Forwarded: {wrapper(1, 2, 3)}")
print(f"  Forwarded: {wrapper(a=1, b=2, c=3)}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 12. Lambda — anonymous (inline) functions
#
#  lambda args: expression
#  Can only have ONE expression (no statements, no if/else blocks)
#  Used for short throwaway functions
# ════════════════════════════════════════════════════

print("12. Lambda functions")

# Basic lambda
double = lambda x: x * 2
print(f"  double(5) = {double(5)}")

# Multiple parameters
add = lambda a, b: a + b
print(f"  add(3, 7) = {add(3, 7)}")

# Lambda with conditional expression
classify = lambda x: "positive" if x > 0 else "negative" if x < 0 else "zero"
print(f"  classify(5) = {classify(5)}")
print(f"  classify(-3) = {classify(-3)}")
print(f"  classify(0) = {classify(0)}")

# Lambda with default
greet = lambda name, greeting="Hello": f"{greeting}, {name}!"
print(f"  {greet('Alice')}")
print(f"  {greet('Bob', 'Hi')}")

# Lambda is MOST useful with built-in functions:

# sorted() with key
users = [("Bob", 25), ("Alice", 30), ("Charlie", 20)]
by_age = sorted(users, key=lambda u: u[1])
print(f"  Sorted by age: {by_age}")

by_name = sorted(users, key=lambda u: u[0])
print(f"  Sorted by name: {by_name}")

# filter() — keep items that match condition
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
evens = list(filter(lambda n: n % 2 == 0, numbers))
print(f"  filter evens: {evens}")

# map() — apply function to every item
doubled = list(map(lambda n: n * 2, numbers))
print(f"  map double: {doubled}")

# min/max with key
products = [{"name": "Laptop", "price": 999}, {"name": "Mouse", "price": 25}, {"name": "Monitor", "price": 400}]
cheapest = min(products, key=lambda p: p["price"])
print(f"  Cheapest: {cheapest['name']} (${cheapest['price']})")

print("=" * 50)


# ════════════════════════════════════════════════════
# 13. First-class functions — functions as objects
#
#  In Python, functions are objects. You can:
#  - Assign to variables
#  - Pass as arguments
#  - Return from other functions
#  - Store in lists/dicts
# ════════════════════════════════════════════════════

print("13. First-class functions")

# Assign function to variable
def shout(text):
    return text.upper()

def whisper(text):
    return text.lower()

yell = shout               # yell is now the same function as shout
print(f"  yell('hello') = {yell('hello')}")

# Pass function as argument
def apply(func, value):
    return func(value)

print(f"  apply(shout, 'hello') = {apply(shout, 'hello')}")
print(f"  apply(whisper, 'HELLO') = {apply(whisper, 'HELLO')}")

# Store functions in a list
formatters = [str.upper, str.lower, str.title, str.capitalize]
text = "hello world"
for f in formatters:
    print(f"  {f.__name__}: {f(text)}")

# Store functions in a dict (dispatch pattern)
def op_add(a, b): return a + b
def op_sub(a, b): return a - b
def op_mul(a, b): return a * b
def op_div(a, b): return a / b if b != 0 else "Error: div by zero"

operations = {"+": op_add, "-": op_sub, "*": op_mul, "/": op_div}

for symbol in ["+", "-", "*", "/"]:
    result = operations[symbol](10, 3)
    print(f"  10 {symbol} 3 = {result}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 14. Higher-order functions — map, filter, reduce
#
#  Higher-order function = takes/returns a function
#  map()    = apply function to each item
#  filter() = keep items where function returns True
#  reduce() = combine all items into one value
# ════════════════════════════════════════════════════

print("14. Higher-order functions")

from functools import reduce

numbers = [1, 2, 3, 4, 5]

# map — transform each item
squares = list(map(lambda x: x**2, numbers))
print(f"  map squares: {squares}")           # [1, 4, 9, 16, 25]

# map with named function
def celsius_to_fahrenheit(c):
    return (c * 9/5) + 32

temps_c = [0, 20, 37, 100]
temps_f = list(map(celsius_to_fahrenheit, temps_c))
print(f"  map temps: {temps_f}")             # [32.0, 68.0, 98.6, 212.0]

# map with multiple iterables
a = [1, 2, 3]
b = [10, 20, 30]
sums = list(map(lambda x, y: x + y, a, b))
print(f"  map two lists: {sums}")            # [11, 22, 33]

# filter — keep matching items
words = ["hello", "world", "hi", "hey", "how", "python"]
h_words = list(filter(lambda w: w.startswith("h"), words))
print(f"  filter h-words: {h_words}")        # ['hello', 'hi', 'hey', 'how']

# reduce — combine into one value
total = reduce(lambda acc, x: acc + x, numbers)
print(f"  reduce sum: {total}")              # 15

product = reduce(lambda acc, x: acc * x, numbers)
print(f"  reduce product: {product}")        # 120

# reduce with initial value
total_plus_100 = reduce(lambda acc, x: acc + x, numbers, 100)
print(f"  reduce with initial 100: {total_plus_100}")    # 115

# find max with reduce
biggest = reduce(lambda a, b: a if a > b else b, [5, 2, 8, 1, 9])
print(f"  reduce max: {biggest}")            # 9

print("=" * 50)


# ════════════════════════════════════════════════════
# 15. Closures — function that remembers its scope
#
#  Inner function can access variables from outer function
#  Even AFTER outer function has finished executing
# ════════════════════════════════════════════════════

print("15. Closures")

# Basic closure
def make_multiplier(factor):
    def multiply(x):             # inner function
        return x * factor        # uses factor from outer scope
    return multiply              # return the inner function

double = make_multiplier(2)
triple = make_multiplier(3)

print(f"  double(5) = {double(5)}")      # 10
print(f"  triple(5) = {triple(5)}")      # 15

# Closure with state (counter)
def make_counter(start=0):
    count = [start]    # list so inner function can modify it
    def increment():
        count[0] += 1
        return count[0]
    return increment

counter = make_counter()
print(f"  counter: {counter()}, {counter()}, {counter()}")    # 1, 2, 3

counter_from_10 = make_counter(10)
print(f"  from 10: {counter_from_10()}, {counter_from_10()}")  # 11, 12

# Closure with nonlocal (modify outer variable)
def make_accumulator():
    total = 0
    def add(n):
        nonlocal total    # allows modifying outer variable
        total += n
        return total
    return add

acc = make_accumulator()
print(f"  accumulator: {acc(5)}, {acc(3)}, {acc(7)}")    # 5, 8, 15

# Practical closure — logger with prefix
def make_logger(prefix):
    def log(message):
        print(f"  [{prefix}] {message}")
    return log

info = make_logger("INFO")
error = make_logger("ERROR")

info("Server started")
error("Connection failed")

print("=" * 50)


# ════════════════════════════════════════════════════
# 16. Nested functions — function inside a function
# ════════════════════════════════════════════════════

print("16. Nested functions")

def calculate_stats(numbers):
    # Helper functions — only visible inside calculate_stats
    def mean():
        return sum(numbers) / len(numbers)

    def variance():
        avg = mean()
        return sum((x - avg) ** 2 for x in numbers) / len(numbers)

    def std_dev():
        return variance() ** 0.5

    return {
        "mean": round(mean(), 2),
        "variance": round(variance(), 2),
        "std_dev": round(std_dev(), 2),
    }

result = calculate_stats([10, 20, 30, 40, 50])
print(f"  Stats: {result}")

# mean()    # NameError! — not accessible outside calculate_stats

print("=" * 50)


# ════════════════════════════════════════════════════
# 17. Recursion — function that calls itself
#
#  Must have a BASE CASE (stop condition)
#  Without base case → infinite loop → stack overflow
# ════════════════════════════════════════════════════

print("17. Recursion")

# Factorial: 5! = 5 × 4 × 3 × 2 × 1 = 120
def factorial(n):
    if n <= 1:              # base case
        return 1
    return n * factorial(n - 1)    # recursive case

print(f"  5! = {factorial(5)}")       # 120
print(f"  10! = {factorial(10)}")     # 3628800

# Fibonacci: 0, 1, 1, 2, 3, 5, 8, 13, 21...
def fibonacci(n):
    if n <= 0: return 0       # base case
    if n == 1: return 1       # base case
    return fibonacci(n - 1) + fibonacci(n - 2)

fib_seq = [fibonacci(i) for i in range(10)]
print(f"  Fibonacci: {fib_seq}")

# Flatten nested list
def flatten(lst):
    result = []
    for item in lst:
        if isinstance(item, list):
            result.extend(flatten(item))    # recurse into sublists
        else:
            result.append(item)
    return result

nested = [1, [2, 3], [4, [5, 6]], [7, [8, [9]]]]
print(f"  Flatten: {flatten(nested)}")     # [1, 2, 3, 4, 5, 6, 7, 8, 9]

# Sum nested dict values
def sum_nested(d):
    total = 0
    for value in d.values():
        if isinstance(value, dict):
            total += sum_nested(value)
        elif isinstance(value, (int, float)):
            total += value
    return total

budget = {"food": 200, "rent": 1000, "utilities": {"gas": 50, "electric": 80, "water": 30}}
print(f"  Nested sum: {sum_nested(budget)}")    # 1360

# Python recursion limit
import sys
print(f"  Recursion limit: {sys.getrecursionlimit()}")    # usually 1000

print("=" * 50)


# ════════════════════════════════════════════════════
# 18. Type hints — annotate parameter and return types
#
#  Python does NOT enforce types — hints are for documentation
#  Tools like mypy can check them
# ════════════════════════════════════════════════════

print("18. Type hints")

# Basic type hints
def add_typed(a: int, b: int) -> int:
    return a + b

print(f"  add_typed(3, 5) = {add_typed(3, 5)}")
print(f"  add_typed('a', 'b') = {add_typed('a', 'b')}")    # still works! hints not enforced

# Complex type hints
from typing import Optional, Union

def find_user(user_id: int) -> Optional[dict]:    # returns dict or None
    users = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
    return users.get(user_id)

print(f"  find_user(1) = {find_user(1)}")
print(f"  find_user(99) = {find_user(99)}")    # None

def process(data: Union[str, list]) -> str:    # accepts str OR list
    if isinstance(data, list):
        return ", ".join(str(x) for x in data)
    return data

print(f"  process('hello') = {process('hello')}")
print(f"  process([1,2,3]) = {process([1, 2, 3])}")

# Type hints for collections
def total_scores(scores: list[int]) -> float:
    return sum(scores) / len(scores)

def get_config() -> dict[str, str]:
    return {"host": "localhost", "port": "8000"}

# Type hints with defaults
def greet_typed(name: str, times: int = 1) -> list[str]:
    return [f"Hello, {name}!"] * times

print(f"  {greet_typed('Alice', 2)}")

# Callable type hint
from typing import Callable

def apply_fn(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

print(f"  apply_fn(add_typed, 3, 5) = {apply_fn(add_typed, 3, 5)}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 19. Docstrings — document your functions
#
#  Triple-quoted string right after def
#  Accessible via help() and func.__doc__
# ════════════════════════════════════════════════════

print("19. Docstrings")

# Simple docstring
def square(n):
    """Return the square of a number."""
    return n ** 2

# Detailed docstring (Google style)
def calculate_bmi(weight: float, height: float) -> float:
    """Calculate Body Mass Index.

    Args:
        weight: Weight in kilograms.
        height: Height in meters.

    Returns:
        BMI value as a float.

    Raises:
        ValueError: If height is zero or negative.
    """
    if height <= 0:
        raise ValueError("Height must be positive")
    return weight / (height ** 2)

print(f"  square(5) = {square(5)}")
print(f"  square.__doc__ = '{square.__doc__}'")

print(f"  BMI: {calculate_bmi(70, 1.75):.1f}")
print(f"  BMI doc: '{calculate_bmi.__doc__.strip().split(chr(10))[0]}'")

# Access docstring
# help(calculate_bmi)    # prints full docstring in terminal

print("=" * 50)


# ════════════════════════════════════════════════════
# 20. Function attributes and introspection
#
#  Functions are objects — they have attributes
#  __name__, __doc__, __defaults__, __annotations__
# ════════════════════════════════════════════════════

print("20. Function introspection")

def example(a: int, b: str = "hello", c: float = 3.14) -> str:
    """An example function."""
    return f"{a} {b} {c}"

print(f"  __name__: {example.__name__}")
print(f"  __doc__: {example.__doc__}")
print(f"  __defaults__: {example.__defaults__}")          # ('hello', 3.14)
print(f"  __annotations__: {example.__annotations__}")    # {'a': int, 'b': str, ...}

# inspect module — detailed function info
import inspect

sig = inspect.signature(example)
print(f"  signature: {sig}")
for name, param in sig.parameters.items():
    print(f"    {name}: default={param.default}, kind={param.kind.name}")

# Check if something is callable
print(f"  callable(example): {callable(example)}")
print(f"  callable(42): {callable(42)}")

# Get source code (only works for functions defined in .py files)
source = inspect.getsource(square)
print(f"  source of square:\n    {source.strip()}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 21. Generators — yield instead of return
#
#  yield = produce values one at a time (lazy)
#  Generator doesn't store all values in memory
#  Perfect for large/infinite sequences
# ════════════════════════════════════════════════════

print("21. Generators")

# Basic generator
def count_up(start, end):
    current = start
    while current <= end:
        yield current          # produce one value, pause here
        current += 1

# Use generator in a for loop
print("  count_up(1, 5):", end=" ")
for n in count_up(1, 5):
    print(n, end=" ")
print()

# Generator produces values lazily
gen = count_up(1, 3)
print(f"  next(): {next(gen)}")    # 1
print(f"  next(): {next(gen)}")    # 2
print(f"  next(): {next(gen)}")    # 3
# next(gen)    # StopIteration!

# Fibonacci generator — infinite sequence
def fib_generator():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

fib = fib_generator()
first_10 = [next(fib) for _ in range(10)]
print(f"  Infinite fibonacci: {first_10}")

# Generator to read large file line by line
def read_lines(filename):
    with open(filename, "r") as f:
        for line in f:
            yield line.strip()

# Pipeline of generators
def numbers():
    yield from range(1, 11)    # yield from = delegate to another iterable

def squared(gen):
    for n in gen:
        yield n ** 2

def only_even(gen):
    for n in gen:
        if n % 2 == 0:
            yield n

# Chain generators: numbers → squared → only_even
pipeline = only_even(squared(numbers()))
print(f"  Pipeline: {list(pipeline)}")    # [4, 16, 36, 64, 100]

# Generator expression (like list comprehension but lazy)
gen_expr = (x**2 for x in range(10))
print(f"  Gen expression type: {type(gen_expr)}")
print(f"  Gen expression list: {list(gen_expr)}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 22. Decorators — functions that modify functions
#
#  @decorator is shorthand for:
#  func = decorator(func)
# ════════════════════════════════════════════════════

print("22. Decorators (brief)")

import functools
import time

# Basic decorator
def uppercase_result(func):
    @functools.wraps(func)    # preserves original function's name/doc
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return result.upper()
    return wrapper

@uppercase_result
def say_hi(name):
    return f"hi, {name}"

print(f"  {say_hi('Alice')}")    # "HI, ALICE"

# Timer decorator
def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"  {func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    total = sum(range(1000000))
    return total

slow_function()

# Decorator with parameters (decorator factory)
def repeat(times):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                results.append(func(*args, **kwargs))
            return results
        return wrapper
    return decorator

@repeat(times=3)
def say_word(word):
    return word

print(f"  repeat(3): {say_word('hello')}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 23. Global vs Local scope
#
#  Local  = inside function (dies when function ends)
#  Global = outside all functions (lives forever)
#  global keyword = modify global variable from inside function
#  nonlocal = modify enclosing function's variable
# ════════════════════════════════════════════════════

print("23. Scope — global, local, nonlocal")

x = "global x"    # global variable

def scope_test():
    y = "local y"    # local variable — only exists inside this function
    print(f"  Inside function: x='{x}', y='{y}'")

scope_test()
print(f"  Outside function: x='{x}'")
# print(y)    # NameError! y doesn't exist outside

# Modifying global variable
counter = 0

def increment_bad():
    # counter += 1    # UnboundLocalError! can't modify global without declaring
    pass

def increment_good():
    global counter
    counter += 1

increment_good()
increment_good()
print(f"  Global counter: {counter}")    # 2

# nonlocal — modify enclosing scope
def outer():
    message = "original"

    def inner():
        nonlocal message
        message = "modified by inner"

    inner()
    return message

print(f"  nonlocal: {outer()}")    # "modified by inner"

# LEGB rule — Python looks for variables in this order:
# L = Local (inside current function)
# E = Enclosing (inside outer function, for closures)
# G = Global (module level)
# B = Built-in (Python built-ins like len, print, etc.)

x = "global"

def outer_fn():
    x = "enclosing"

    def inner_fn():
        x = "local"
        print(f"  LEGB inner: {x}")    # "local"

    inner_fn()
    print(f"  LEGB outer: {x}")        # "enclosing"

outer_fn()
print(f"  LEGB global: {x}")           # "global"

print("=" * 50)


# ════════════════════════════════════════════════════
# 24. Memoization — cache function results
#
#  Store results of expensive function calls
#  Return cached result for same arguments
#  functools.lru_cache does this automatically
# ════════════════════════════════════════════════════

print("24. Memoization / caching")

# Manual memoization
def memoize(func):
    cache = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper

@memoize
def slow_square(n):
    time.sleep(0.01)    # simulate slow computation
    return n ** 2

start = time.time()
results = [slow_square(i) for i in range(20)]
first_run = time.time() - start

start = time.time()
results = [slow_square(i) for i in range(20)]
second_run = time.time() - start

print(f"  First run: {first_run:.3f}s")
print(f"  Second run (cached): {second_run:.5f}s")

# Built-in lru_cache — RECOMMENDED
@functools.lru_cache(maxsize=128)    # maxsize=None for unlimited
def fib_cached(n):
    if n <= 1:
        return n
    return fib_cached(n - 1) + fib_cached(n - 2)

print(f"  fib(50) = {fib_cached(50)}")    # instant! (without cache → years)
print(f"  Cache info: {fib_cached.cache_info()}")

# Clear cache
fib_cached.cache_clear()

print("=" * 50)


# ════════════════════════════════════════════════════
# 25. Partial functions — pre-fill some arguments
#
#  functools.partial creates a new function with
#  some arguments already filled in
# ════════════════════════════════════════════════════

print("25. Partial functions")

from functools import partial

def power(base, exponent):
    return base ** exponent

# Create specialized versions
square = partial(power, exponent=2)
cube = partial(power, exponent=3)

print(f"  square(5) = {square(5)}")    # 25
print(f"  cube(5) = {cube(5)}")        # 125

# Practical: pre-configure API calls
def fetch_data(base_url, endpoint, timeout=30):
    return f"GET {base_url}/{endpoint} (timeout={timeout})"

fetch_prod = partial(fetch_data, "https://api.prod.com", timeout=10)
fetch_dev = partial(fetch_data, "https://localhost:8000", timeout=60)

print(f"  {fetch_prod('users')}")
print(f"  {fetch_dev('users')}")

# Partial with print
debug_print = partial(print, "[DEBUG]")
debug_print("something happened")    # [DEBUG] something happened

print("=" * 50)


# ════════════════════════════════════════════════════
# 26. Error handling in functions
#
#  try/except inside functions
#  Raise custom exceptions
#  Guard clauses (early return on bad input)
# ════════════════════════════════════════════════════

print("26. Error handling")

# Guard clauses — validate early, return early
def divide(a, b):
    if not isinstance(a, (int, float)):
        raise TypeError(f"Expected number, got {type(a).__name__}")
    if not isinstance(b, (int, float)):
        raise TypeError(f"Expected number, got {type(b).__name__}")
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

print(f"  divide(10, 3) = {divide(10, 3):.2f}")

try:
    divide(10, 0)
except ValueError as e:
    print(f"  Error: {e}")

try:
    divide("ten", 3)
except TypeError as e:
    print(f"  Error: {e}")

# Return None or default on error
def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

print(f"  safe_int('42') = {safe_int('42')}")
print(f"  safe_int('abc') = {safe_int('abc')}")
print(f"  safe_int('abc', -1) = {safe_int('abc', -1)}")

# Custom exception
class ValidationError(Exception):
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")

def validate_age(age):
    if not isinstance(age, int):
        raise ValidationError("age", "must be an integer")
    if age < 0 or age > 150:
        raise ValidationError("age", "must be between 0 and 150")
    return True

try:
    validate_age(200)
except ValidationError as e:
    print(f"  ValidationError: {e.field} — {e.message}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 27. Callback pattern — pass function to be called later
# ════════════════════════════════════════════════════

print("27. Callbacks")

def process_data(data, on_success, on_error):
    try:
        result = [x * 2 for x in data]
        on_success(result)
    except Exception as e:
        on_error(str(e))

def handle_success(result):
    print(f"  Success: {result}")

def handle_error(error):
    print(f"  Error: {error}")

process_data([1, 2, 3], handle_success, handle_error)
process_data("not a list of numbers", handle_success, handle_error)

# Event handler pattern
def on_click(handler):
    print(f"  Button clicked → calling {handler.__name__}")
    handler()

def save_action():
    print("  Saving document...")

def delete_action():
    print("  Deleting item...")

on_click(save_action)
on_click(delete_action)

print("=" * 50)


# ════════════════════════════════════════════════════
# 28. Function composition — chain functions together
# ════════════════════════════════════════════════════

print("28. Function composition")

# Manual composition
def add_one(x): return x + 1
def double_it(x): return x * 2
def square_it(x): return x ** 2

# Apply in sequence
result = square_it(double_it(add_one(3)))    # 3→4→8→64
print(f"  Manual: add_one → double → square: 3 → {result}")

# Compose function
def compose(*functions):
    def composed(x):
        for func in reversed(functions):
            x = func(x)
        return x
    return composed

transform = compose(square_it, double_it, add_one)    # reads right to left
print(f"  Composed: {transform(3)}")    # 64

# Pipe function (left to right — more readable)
def pipe(*functions):
    def piped(x):
        for func in functions:
            x = func(x)
        return x
    return piped

transform2 = pipe(add_one, double_it, square_it)    # reads left to right
print(f"  Piped: {transform2(3)}")    # 64

# Practical: data processing pipeline
def clean(text): return text.strip()
def lower(text): return text.lower()
def remove_punctuation(text): return "".join(c for c in text if c.isalnum() or c == " ")
def split_words(text): return text.split()

process_text = pipe(clean, lower, remove_punctuation, split_words)
result = process_text("  Hello, World! How ARE you?  ")
print(f"  Pipeline: {result}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 29. Walrus operator in functions (Python 3.8+)
#
#  := assigns AND returns in one expression
# ════════════════════════════════════════════════════

print("29. Walrus operator (:=)")

# Without walrus — call function twice or use temp variable
def get_length(text):
    return len(text)

text = "Hello World"
# Old way:
length = get_length(text)
if length > 5:
    print(f"  Old way: '{text}' has {length} chars")

# With walrus — assign and check in one line
if (n := get_length(text)) > 5:
    print(f"  Walrus: '{text}' has {n} chars")

# Walrus in list comprehension
import random
random.seed(42)
def roll_dice():
    return random.randint(1, 6)

# Keep rolling until we get a 6
rolls = []
while (roll := roll_dice()) != 6:
    rolls.append(roll)
print(f"  Rolled {rolls} before getting 6")

# Filter and transform in one pass
data = ["hello", "", "world", "", "python"]
non_empty = [upper for s in data if (upper := s.upper())]
print(f"  Non-empty upper: {non_empty}")

print("=" * 50)


# ════════════════════════════════════════════════════
# 30. Common patterns and best practices
# ════════════════════════════════════════════════════

print("30. Common patterns")

# Pattern 1: Default factory (avoid mutable default args)
def create_response(data, errors=None, metadata=None):
    return {
        "data": data,
        "errors": errors or [],        # None → empty list
        "metadata": metadata or {},    # None → empty dict
    }

print(f"  Response: {create_response('ok')}")

# Pattern 2: Early return (guard clauses)
def process_order(order):
    if not order:
        return {"error": "No order"}
    if "items" not in order:
        return {"error": "No items"}
    if not order["items"]:
        return {"error": "Empty items"}
    # Main logic only runs if all checks pass
    return {"status": "processed", "count": len(order["items"])}

print(f"  {process_order(None)}")
print(f"  {process_order({'items': ['a', 'b']})}")

# Pattern 3: Strategy pattern with functions
def sort_users(users, strategy="name"):
    strategies = {
        "name": lambda u: u["name"],
        "age": lambda u: u["age"],
        "email": lambda u: u["email"],
    }
    key_func = strategies.get(strategy, strategies["name"])
    return sorted(users, key=key_func)

users = [
    {"name": "Charlie", "age": 25, "email": "c@test.com"},
    {"name": "Alice", "age": 30, "email": "a@test.com"},
    {"name": "Bob", "age": 20, "email": "b@test.com"},
]

by_name = sort_users(users, "name")
by_age = sort_users(users, "age")
print(f"  By name: {[u['name'] for u in by_name]}")
print(f"  By age: {[u['name'] for u in by_age]}")

# Pattern 4: Function registry
registry = {}

def register(name):
    def decorator(func):
        registry[name] = func
        return func
    return decorator

@register("greet")
def greet_handler(data):
    return f"Hello, {data['name']}!"

@register("farewell")
def farewell_handler(data):
    return f"Goodbye, {data['name']}!"

# Use registry
for action in ["greet", "farewell"]:
    handler = registry[action]
    print(f"  {action}: {handler({'name': 'Alice'})}")

print("=" * 50)


# ════════════════════════════════════════════════════
# SUMMARY
#
#  BASICS:
#    def, return, parameters, arguments
#    Default values, None for mutable defaults
#
#  ARGUMENT TYPES:
#    Positional      → func(a, b)
#    Keyword         → func(a=1, b=2)
#    *args           → variable positional (tuple)
#    **kwargs        → variable keyword (dict)
#    Keyword-only    → def func(*, key)  (after *)
#    Positional-only → def func(a, b, /)  (before /)
#
#  CALLING:
#    *list  → unpack list into positional args
#    **dict → unpack dict into keyword args
#
#  RETURN:
#    Single value, tuple, dict, named tuple
#    No return → None
#
#  ADVANCED:
#    Lambda        → lambda x: x * 2
#    Closures      → inner function remembers outer scope
#    Generators    → yield (lazy, memory efficient)
#    Decorators    → @decorator modifies function
#    Recursion     → function calls itself
#    Memoization   → @lru_cache caches results
#    Partial       → partial(func, arg) pre-fills args
#
#  SCOPE:
#    LEGB: Local → Enclosing → Global → Built-in
#    global    → modify global from inside function
#    nonlocal  → modify enclosing from inner function
#
#  FIRST-CLASS:
#    Functions ARE objects — assign, pass, return, store
#    map(), filter(), reduce() — higher-order functions
#    Callbacks, composition, pipelines
#
#  BEST PRACTICES:
#    Guard clauses — validate early, return early
#    Type hints — def func(x: int) -> str
#    Docstrings — """Describe what function does."""
#    None for mutable defaults — never def f(items=[])
#    Single responsibility — each function does ONE thing
# ════════════════════════════════════════════════════
