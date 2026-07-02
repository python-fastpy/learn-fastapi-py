# ══════════════════════════════════════════════════════════════════
#  PYTHON DECORATORS — Condensed Guide
#  @decorator is shortcut for: func = decorator(func)
#  FastAPI's @app.get("/path") is a decorator factory!
# ══════════════════════════════════════════════════════════════════
import time, functools

# ╔══════════════════════════════════════════════════╗
# ║                  BEGINNER                        ║
# ╚══════════════════════════════════════════════════╝

# ── 1. Functions Are Objects ─────────────────────────────
def greet(): return "Hello!"
my_func = greet            # no parens = reference, not call
print(my_func())           # Hello!

def call_twice(func):
    print(func())
    print(func())
call_twice(greet)          # prints "Hello!" twice

# ── 2. Closures — Functions That Return Functions ────────
def make_greeter(name):
    def greeter():
        return f"Hello, {name}!"   # "remembers" name from outer scope
    return greeter

print(make_greeter("Alice")())  # Hello, Alice!
print(make_greeter("Bob")())    # Hello, Bob!

# ── 3. Simplest Decorator ───────────────────────────────
# @my_decorator is EXACTLY: say_hello = my_decorator(say_hello)
def my_decorator(func):
    def wrapper():
        print("BEFORE")
        result = func()
        print("AFTER")
        return result
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")
    return "done"
say_hello()  # BEFORE -> Hello! -> AFTER

print("=" * 50)
# ╔══════════════════════════════════════════════════╗
# ║               INTERMEDIATE                       ║
# ╚══════════════════════════════════════════════════╝

# ── 4. Decorator with *args, **kwargs ────────────────────
def log_call(func):
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}({args}, {kwargs})")
        return func(*args, **kwargs)
    return wrapper

@log_call
def add(a, b): return a + b
print(add(3, 5))  # Calling add((3, 5), {}) -> 8

# ── 5. Decorator Factory (WITH Parameters) ──────────────
# THREE nesting levels: outer(params) -> decorator(func) -> wrapper(*args)
# THIS IS HOW @app.get("/path") WORKS!
def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(times=3)
def say_hi(name): print(f"Hi {name}!")
say_hi("Alice")  # prints "Hi Alice!" three times
# Equivalent: say_hi = repeat(3)(say_hi)

# ── 6. functools.wraps — Preserve Metadata ──────────────
def bad_dec(func):                           # without wraps:
    def wrapper(*a, **kw): return func(*a, **kw)
    return wrapper
def good_dec(func):                          # with wraps:
    @functools.wraps(func)
    def wrapper(*a, **kw): return func(*a, **kw)
    return wrapper

@bad_dec
def func_bad(): """My docstring"""
@good_dec
def func_good(): """My docstring"""
print(f"Bad:  name={func_bad.__name__}, doc={func_bad.__doc__}")    # wrapper, None
print(f"Good: name={func_good.__name__}, doc={func_good.__doc__}")  # func_good, My docstring

# ── 7. Stacking Decorators ──────────────────────────────
# @A / @B / def f  ≡  f = A(B(f))  — bottom-up wrap, top-down execute
def bold(f):
    def w(*a, **kw): return f"<b>{f(*a, **kw)}</b>"
    return w
def italic(f):
    def w(*a, **kw): return f"<i>{f(*a, **kw)}</i>"
    return w

@bold     # outer
@italic   # inner
def format_text(text): return text
print(format_text("Hello"))  # <b><i>Hello</i></b>

# ── 8. Timer Decorator ──────────────────────────────────
def timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__} took {time.time() - start:.4f}s")
        return result
    return wrapper

@timer
def slow_function():
    time.sleep(0.5)
    return "done"
slow_function()  # slow_function took 0.50XXs

# ── 9. Retry Decorator ──────────────────────────────────
def retry(max_attempts=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try: return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts: raise
                    print(f"  Attempt {attempt} failed: {e}")
        return wrapper
    return decorator

_attempt = 0
@retry(max_attempts=3)
def unreliable_api():
    global _attempt; _attempt += 1
    if _attempt < 3: raise ConnectionError("Server down")
    return "Success!"
_attempt = 0
print(unreliable_api())  # fails twice, succeeds on third

# ── 10. Cache / Memoize ─────────────────────────────────
def cache(func):
    stored = {}
    @functools.wraps(func)
    def wrapper(*args):
        if args not in stored: stored[args] = func(*args)
        return stored[args]
    return wrapper

@cache
def expensive_multiply(a, b): return a * b
print(expensive_multiply(3, 4))  # computes -> 12
print(expensive_multiply(3, 4))  # cached   -> 12

# ── 11. Auth / Role Check ───────────────────────────────
current_user = {"name": "Alice", "role": "admin"}
def require_role(role):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if current_user["role"] != role:
                return f"ACCESS DENIED: need {role}, have {current_user['role']}"
            return func(*args, **kwargs)
        return wrapper
    return decorator

@require_role("admin")
def delete_data(): return "All data deleted!"
@require_role("superadmin")
def shutdown(): return "Shutting down..."
print(delete_data())  # All data deleted!
print(shutdown())     # ACCESS DENIED: need superadmin, have admin
print("=" * 50)
# ╔══════════════════════════════════════════════════╗
# ║                  ADVANCED                        ║
# ╚══════════════════════════════════════════════════╝

# ── 12. Class-Based Decorator (no params) ────────────────
class CountCalls:  # __call__ makes instances callable -> works as decorator
    def __init__(self, func): self.func, self.count = func, 0
    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"{self.func.__name__} called {self.count} time(s)")
        return self.func(*args, **kwargs)

@CountCalls  # say_wow = CountCalls(say_wow)
def say_wow(): return "Wow!"
say_wow(); say_wow()  # called 1 time(s) / called 2 time(s)

# ── 13. Class-Based Decorator WITH Parameters ───────────
class RateLimit:
    def __init__(self, max_calls):
        self.max_calls = max_calls
    def __call__(self, func):
        call_count = {"n": 0}
        def wrapper(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] > self.max_calls:
                return f"RATE LIMITED! Max {self.max_calls} calls"
            return func(*args, **kwargs)
        return wrapper

@RateLimit(max_calls=2)
def get_secret(): return "The secret is 42"
print(get_secret())  # The secret is 42
print(get_secret())  # The secret is 42
print(get_secret())  # RATE LIMITED! Max 2 calls

# ── 14. Validation Decorator ────────────────────────────
def validate_positive(func):
    @functools.wraps(func)
    def wrapper(*args, **kw):
        for a in args:
            if isinstance(a, (int, float)) and a < 0:
                raise ValueError(f"Negative not allowed: {a}")
        return func(*args, **kw)
    return wrapper

@validate_positive
def calculate_area(w, h): return w * h
print(calculate_area(5, 10))  # 50
try: calculate_area(-3, 10)
except ValueError as e: print(f"Error: {e}")  # Negative not allowed: -3

# ── 15. FastAPI @app.get() Pattern — Full Simulation ────
# Class stores routes dict; .get()/.post() are decorator factories
class SimpleAPI:
    def __init__(self):
        self.routes = {"GET": {}, "POST": {}, "PUT": {}, "DELETE": {}}
    def _register(self, method, path):
        def decorator(func):
            self.routes[method][path] = func
            return func
        return decorator
    def get(self, path):    return self._register("GET", path)
    def post(self, path):   return self._register("POST", path)
    def put(self, path):    return self._register("PUT", path)
    def delete(self, path): return self._register("DELETE", path)
    def request(self, method, path, **kwargs):
        m = method.upper()
        if m in self.routes and path in self.routes[m]:
            return self.routes[m][path](**kwargs)
        return {"error": f"{m} {path} not found"}

api = SimpleAPI()

@api.get("/users")
def list_users(): return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
@api.post("/users")
def create_user(name="Unknown"): return {"id": 3, "name": name, "created": True}
@api.delete("/users/1")
def delete_user(): return {"id": 1, "deleted": True}

print("GET /users   ->", api.request("GET", "/users"))
print("POST /users  ->", api.request("POST", "/users", name="Charlie"))
print("DELETE       ->", api.request("DELETE", "/users/1"))
print("GET /unknown ->", api.request("GET", "/unknown"))

# ╔══════════════════════════════════════════════════╗
# ║                 CHEAT SHEET                      ║
# ╚══════════════════════════════════════════════════╝
#
# PATTERN                    STRUCTURE                          USE CASE
# ─────────────────────────  ─────────────────────────────────  ────────────────
# Simple decorator           def dec(func):                     logging, timing
#   @dec / def f               def wrapper(*a,**kw): ...
#                              return wrapper
#
# Decorator factory          def factory(param):                auth, retry
#   @factory(param)             def dec(func):
#   def f                         def wrapper(*a,**kw): ...
#                                 return wrapper
#                               return dec
#
# Class decorator            class Dec:                         counting, state
#   @Dec / def f               __init__(self, func)
#                              __call__(self, *a, **kw)
#
# Class factory              class Dec:                         rate limiting
#   @Dec(param)                __init__(self, param)
#   def f                      __call__(self, func) -> wrapper
#
# @app.get("/path")          class App:                         route registration
#   (FastAPI)                   def get(self, path):
#                                 def dec(func):
#                                   routes[path] = func
#                                 return dec
#
# KEY RULES:
#   @A / @B / def f  ->  f = A(B(f))  ->  bottom-up wrap, top-down execute
#   Always use @functools.wraps(func) to preserve __name__ and __doc__
#   @decorator vs @decorator() — parens mean factory (extra nesting level)
