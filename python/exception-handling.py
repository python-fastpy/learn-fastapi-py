# ══════════════════════════════════════════════════════════════════
#  PYTHON EXCEPTION HANDLING — Complete Guide (Condensed)
#
#  Exception = runtime error that breaks normal flow
#  Handling = catch it, deal with it, keep running
#
#  try/except vs if/else:
#    if/else  → check BEFORE doing   (LBYL: Look Before You Leap)
#    try/except → just DO it, catch failure  (EAFP: Easier to Ask Forgiveness)
#    Python community prefers EAFP
# ══════════════════════════════════════════════════════════════════

# ╔══════════════════════════════════════════════════╗
# ║                  BEGINNER                        ║
# ╚══════════════════════════════════════════════════╝

# ── 1. Basic try/except ─────────────────────────────
# Without handling:  1/0  →  ZeroDivisionError  →  program CRASHES
# With handling:     catch it, print message, program continues
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero")       # this runs
print("Program continues")               # still alive!

# ── 2. Catch specific vs generic ────────────────────
# ALWAYS catch specific exceptions first — generic last
try:
    x = int("abc")
except ValueError:                        # specific — catches int("abc")
    print("Not a number")
except Exception:                         # generic — catches everything else
    print("Something else went wrong")

# ── 3. Access the error message ─────────────────────
try:
    [1, 2, 3][10]
except IndexError as e:                   # "as e" captures the error object
    print(f"Error: {e}")                  # "list index out of range"
    print(f"Type:  {type(e).__name__}")   # "IndexError"

# ── 4. Multiple exceptions in one line ──────────────
try:
    x = int("abc")
except (ValueError, TypeError) as e:     # catch either — same handler
    print(f"Bad input: {e}")

# vs separate handlers (different logic per error):
try:
    data = {"a": 1}
    print(data["b"])
except KeyError:
    print("Key not found")               # runs for missing dict key
except TypeError:
    print("Wrong type")                   # runs for wrong type operation

# ── 5. try / except / else / finally ────────────────
# else = runs ONLY if no exception | finally = runs ALWAYS
try:
    result = 10 / 2
except ZeroDivisionError:
    print("Error!")                       # skipped (no error)
else:
    print(f"Result: {result}")            # runs because no exception → 5.0
finally:
    print("Cleanup done")                # ALWAYS runs — error or not

# COMPARISON:
# try:     code that MIGHT fail
# except:  handle the failure
# else:    runs if try SUCCEEDED (no exception) — put success logic here, not in try
# finally: runs ALWAYS — cleanup (close files, connections, release locks)

# ── 6. Why use else? ────────────────────────────────
# Without else — accidental catch:
try:
    value = int("5")
    result = value / 0       # BUG! — ZeroDivisionError caught by wrong handler
except (ValueError, ZeroDivisionError):
    print("Parse error?")    # misleading — it's actually a division error

# With else — clean separation:
try:
    value = int("5")         # only THIS can raise ValueError
except ValueError:
    print("Parse error")
else:
    result = value / 2       # this is NOT inside try — its errors bubble up naturally
    print(f"Result: {result}")

# ╔══════════════════════════════════════════════════╗
# ║               INTERMEDIATE                       ║
# ╚══════════════════════════════════════════════════╝

# ── 7. raise — Throw your own exceptions ───────────
def withdraw(amount):
    if amount <= 0:
        raise ValueError("Amount must be positive")    # throw error
    if amount > 1000:
        raise ValueError("Cannot withdraw over 1000")
    return f"Withdrew {amount}"

try:
    print(withdraw(-50))
except ValueError as e:
    print(f"Failed: {e}")     # Failed: Amount must be positive

# ── 8. re-raise — Catch, log, then re-throw ────────
# Catch for logging but let it propagate up
def process_data(data):
    try:
        return int(data)
    except ValueError:
        print(f"LOG: bad data '{data}'")  # log it
        raise                             # re-raise SAME exception (bare raise)

try:
    process_data("abc")
except ValueError as e:
    print(f"Caller caught: {e}")          # still reaches caller

# raise vs raise e:
#   raise     → preserves original traceback (PREFERRED)
#   raise e   → resets traceback to this line (loses context)

# ── 9. raise from — Chain exceptions ───────────────
# "The real cause was X, but I'm reporting Y"
def connect_db():
    try:
        raise ConnectionError("DB timeout")
    except ConnectionError as e:
        raise RuntimeError("Service unavailable") from e  # chains original cause

try:
    connect_db()
except RuntimeError as e:
    print(f"Error: {e}")                  # Service unavailable
    print(f"Cause: {e.__cause__}")        # DB timeout

# raise X from None → suppress chain (hide original cause)

# ── 10. Custom exceptions ──────────────────────────
# Inherit from Exception (or a subclass). Use for domain-specific errors.
class InsufficientFundsError(Exception):
    def __init__(self, balance, amount):
        self.balance = balance
        self.amount = amount
        super().__init__(f"Cannot withdraw {amount}, balance is {balance}")

class AccountLockedError(Exception):
    pass                                  # simplest custom exception — just a name

class BankError(Exception):              # base class for all bank errors
    pass
class OverdraftError(BankError):         # hierarchy — catch BankError catches both
    pass
class FraudError(BankError):
    pass

try:
    raise InsufficientFundsError(100, 500)
except InsufficientFundsError as e:
    print(f"{e}")                         # Cannot withdraw 500, balance is 100
    print(f"Short by: {e.amount - e.balance}")  # 400 — access custom attrs

# ── 11. LBYL vs EAFP ───────────────────────────────
data = {"name": "Alice", "age": 30}

# LBYL (Look Before You Leap) — check first, then act
if "email" in data:
    email = data["email"]
else:
    email = "N/A"

# EAFP (Easier to Ask Forgiveness) — just try it
try:
    email = data["email"]
except KeyError:
    email = "N/A"

# COMPARISON:
# LBYL:  if os.path.exists(f): open(f)   → race condition! file could be deleted between check and open
# EAFP:  try: open(f) except FileNotFoundError  → atomic, no race condition
# LBYL:  if x != 0: y = 10/x             → safe for simple checks
# EAFP:  try: y = 10/x except ZeroDivision  → better when multiple things can fail
# Python prefers EAFP. Java/C# prefer LBYL.

# ── 12. Common built-in exceptions ──────────────────
examples = {
    "ValueError":       lambda: int("abc"),                # wrong value for type
    "TypeError":        lambda: "2" + 2,                   # wrong type in operation
    "KeyError":         lambda: {}["missing"],              # dict key not found
    "IndexError":       lambda: [1,2][10],                  # list index out of range
    "AttributeError":   lambda: None.split(),               # object has no attribute
    "NameError":        lambda: eval("undefined_var"),       # variable not defined
    "FileNotFoundError":lambda: open("nonexistent.txt"),    # file not found
    "ZeroDivisionError":lambda: 1/0,                       # division by zero
    "ImportError":      lambda: __import__("nonexistent"),  # module not found
    "StopIteration":    lambda: next(iter([])),             # iterator exhausted
    "OverflowError":    lambda: 10.0 ** 1000,              # number too large
    "RecursionError":   None,                               # max recursion depth
    "PermissionError":  None,                               # OS denies access
    "TimeoutError":     None,                               # operation timed out
    "ConnectionError":  None,                               # network connection failed
    "UnicodeDecodeError": lambda: b'\x80'.decode('utf-8'),  # invalid unicode
}

for name, fn in examples.items():
    if fn is None: continue
    try:
        fn()
    except Exception as e:
        print(f"  {type(e).__name__:25s} → {e}")

# ╔══════════════════════════════════════════════════╗
# ║                  ADVANCED                        ║
# ╚══════════════════════════════════════════════════╝

# ── 13. Exception hierarchy ─────────────────────────
# BaseException → Exception → ValueError, TypeError, ...
# BaseException
# ├── SystemExit            (sys.exit() — don't catch!)
# ├── KeyboardInterrupt     (Ctrl+C — don't catch!)
# ├── GeneratorExit         (generator closed — don't catch!)
# └── Exception             (all "normal" exceptions — CATCH THIS)
#     ├── ValueError, TypeError, KeyError, IndexError, ...
#     ├── OSError
#     │   ├── FileNotFoundError, PermissionError, TimeoutError, ConnectionError
#     │   └── FileExistsError, IsADirectoryError
#     ├── RuntimeError
#     │   └── RecursionError
#     ├── LookupError
#     │   ├── KeyError, IndexError
#     ├── ArithmeticError
#     │   ├── ZeroDivisionError, OverflowError, FloatingPointError
#     └── StopIteration, StopAsyncIteration
#
# RULE: catch Exception, NOT BaseException
#   except Exception:         → catches all normal errors (GOOD)
#   except BaseException:     → also catches Ctrl+C and sys.exit() (BAD)
#   except:                   → same as BaseException (BAD — never use bare except)

# ── 14. Context managers — auto-cleanup with exceptions ──
# try/finally vs with statement:

# Manual (error-prone):
f = None
try:
    f = open("test_exc.txt", "w")
    f.write("data")
finally:
    if f: f.close()                       # must remember to close!

# Context manager (automatic):
with open("test_exc.txt", "w") as f:
    f.write("data")
# f.close() called AUTOMATICALLY — even if exception occurs inside with block

# COMPARISON:
# try/finally:  you handle cleanup  →  easy to forget, verbose
# with:         auto-cleanup        →  clean, safe, Pythonic
# Common with:  open(), lock, db connection, http session, tempfile

# ── 15. Nested try blocks ──────────────────────────
def fetch_and_parse(url_data):
    try:                                  # outer: network layer
        try:                              # inner: parsing layer
            return int(url_data)
        except ValueError:
            print("  Parse failed, using default")
            return 0
    except Exception as e:
        print(f"  Unexpected: {e}")
        return -1

print(fetch_and_parse("123"))             # 123
print(fetch_and_parse("abc"))             # Parse failed → 0

# Better pattern — separate into functions instead of nesting:
def parse_safe(data):
    try: return int(data)
    except ValueError: return 0

def fetch_and_parse_v2(data):
    try: return parse_safe(data)
    except Exception: return -1

# ── 16. Exception groups (Python 3.11+) ─────────────
# ExceptionGroup = multiple exceptions at once (from parallel tasks)
# except* = catch some types, let others propagate
def run_tasks():
    errors = []
    for i, val in enumerate(["1", "abc", "3", None]):
        try:
            int(val)
        except (ValueError, TypeError) as e:
            errors.append(e)
    if errors:
        raise ExceptionGroup("batch failed", errors)

try:
    run_tasks()
except ExceptionGroup as eg:
    print(f"ExceptionGroup: {len(eg.exceptions)} errors")
    for e in eg.exceptions:
        print(f"  {type(e).__name__}: {e}")

# except* (3.11+) — catch specific types from group:
# try:
#     run_tasks()
# except* ValueError as eg:       → catches only ValueErrors from the group
#     print(f"{len(eg.exceptions)} ValueErrors")
# except* TypeError as eg:        → catches only TypeErrors
#     print(f"{len(eg.exceptions)} TypeErrors")

# ── 17. Warnings vs Exceptions ─────────────────────
import warnings

# Exception:  STOPS execution  |  Warning:  CONTINUES execution
# raise ValueError("bad")     |  warnings.warn("careful", UserWarning)

warnings.warn("Deprecated function", DeprecationWarning)   # program continues
# Control behavior:
# warnings.filterwarnings("ignore", category=DeprecationWarning)   → suppress
# warnings.filterwarnings("error", category=DeprecationWarning)    → turn into exception

# ── 18. Logging exceptions ─────────────────────────
import logging, traceback

logging.basicConfig(level=logging.DEBUG)

try:
    1 / 0
except ZeroDivisionError:
    logging.exception("Math error")       # logs full traceback automatically
    # vs logging.error("Math error")      # logs message only — no traceback

# Manual traceback capture:
try:
    1 / 0
except ZeroDivisionError:
    tb = traceback.format_exc()           # full traceback as string
    print(f"Traceback:\n{tb}")

# ── 19. Decorator for exception handling ────────────
import functools

def safe_call(default=None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"  {func.__name__} failed: {e}")
                return default
        return wrapper
    return decorator

@safe_call(default=0)
def risky_divide(a, b): return a / b

print(risky_divide(10, 2))               # 5.0
print(risky_divide(10, 0))               # risky_divide failed → 0

# ── 20. Retry decorator with specific exceptions ───
def retry(exceptions=(Exception,), max_tries=3, delay=0):
    import time
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_tries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_tries:
                        raise
                    print(f"  Retry {attempt}/{max_tries}: {e}")
                    if delay: time.sleep(delay)
        return wrapper
    return decorator

_count = 0
@retry(exceptions=(ConnectionError, TimeoutError), max_tries=3)
def call_api():
    global _count; _count += 1
    if _count < 3: raise ConnectionError(f"Attempt {_count} failed")
    return "API response"

_count = 0
print(call_api())                         # retries twice, succeeds third time

# ── 21. Context manager for exception handling ──────
from contextlib import contextmanager, suppress

# suppress — ignore specific exceptions:
from collections import defaultdict
d = {}
with suppress(KeyError):                  # silently ignores KeyError
    val = d["missing"]
# equivalent to: try: d["missing"] except KeyError: pass

# Custom context manager:
@contextmanager
def error_boundary(label):
    try:
        yield
    except Exception as e:
        print(f"[{label}] Caught: {type(e).__name__}: {e}")

with error_boundary("data-load"):
    int("not_a_number")                   # caught and logged, program continues

# ── 22. Assertions — Debug-time checks ──────────────
# assert = "this MUST be true, crash if not"
# Removed when running with python -O (optimized) — NEVER use for validation!
def divide(a, b):
    assert b != 0, "Divisor cannot be zero"     # dev check — NOT for user input!
    return a / b

try:
    divide(10, 0)
except AssertionError as e:
    print(f"Assertion: {e}")              # Divisor cannot be zero

# COMPARISON:
# assert x > 0        → debug check, removed with -O, for IMPOSSIBLE states
# if x <= 0: raise    → validation, always runs, for USER INPUT / API boundaries
# Rule: if it could happen in production, use raise, not assert

# ── 23. sys.exc_info() — Low-level exception access ─
import sys
try:
    1 / 0
except:
    exc_type, exc_value, exc_tb = sys.exc_info()
    print(f"Type:  {exc_type.__name__}")  # ZeroDivisionError
    print(f"Value: {exc_value}")          # division by zero
    print(f"Line:  {exc_tb.tb_lineno}")   # line number where error occurred

# ── 24. Exception in generators ─────────────────────
def safe_generator(items):
    for item in items:
        try:
            yield int(item)               # yields valid, skips invalid
        except (ValueError, TypeError):
            print(f"  Skipping invalid: {item}")

results = list(safe_generator(["1", "abc", "3", None, "5"]))
print(f"Valid items: {results}")          # [1, 3, 5]

# generator.throw() — inject exception into generator:
def gen():
    while True:
        try:
            value = yield
            print(f"  Got: {value}")
        except ValueError:
            print("  Received ValueError!")

g = gen(); next(g)                        # prime generator
g.send("hello")                           # Got: hello
g.throw(ValueError, "bad data")           # Received ValueError!

# ── 25. Async exception handling ────────────────────
import asyncio

async def async_divide(a, b):
    await asyncio.sleep(0.01)             # simulate I/O
    if b == 0: raise ZeroDivisionError("async division by zero")
    return a / b

async def main():
    # Single async try/except — same as sync
    try:
        result = await async_divide(10, 0)
    except ZeroDivisionError as e:
        print(f"Async error: {e}")

    # Gather with return_exceptions — parallel error handling
    results = await asyncio.gather(
        async_divide(10, 2), async_divide(10, 0), async_divide(6, 3),
        return_exceptions=True,
    )
    for r in results:
        if isinstance(r, Exception):
            print(f"  Failed: {r}")       # Failed: async division by zero
        else:
            print(f"  Result: {r}")       # Result: 5.0, Result: 2.0

asyncio.run(main())

# ── 26. Anti-patterns — What NOT to do ──────────────

# BAD: bare except (catches Ctrl+C, sys.exit!)
# try: ...
# except:                           → catches EVERYTHING including KeyboardInterrupt
#     pass                          → silently swallows — impossible to debug

# GOOD:
# except Exception:                 → catches all normal errors, not Ctrl+C/sys.exit

# BAD: catch-all with pass (silent failure)
# try: do_something()
# except Exception: pass            → error vanishes — no one knows it happened

# GOOD: at minimum, log it
# except Exception as e:
#     logging.exception(f"Failed: {e}")

# BAD: too broad try block
# try:
#     data = read_file()            # could fail
#     parsed = parse(data)          # could fail
#     result = calculate(parsed)    # could fail
# except Exception: ...             # which one failed? can't tell!

# GOOD: narrow try blocks
# data = read_file()                # let it crash if file missing
# try:
#     parsed = parse(data)          # only catch parse errors
# except ValueError: ...

# BAD: using exceptions for flow control
# try: d["key"]                     # → just use d.get("key", default)
# except KeyError: default

# BAD: assert for validation
# assert user_input > 0             # removed with -O flag!

# ╔══════════════════════════════════════════════════╗
# ║                 CHEAT SHEET                      ║
# ╚══════════════════════════════════════════════════╝
#
# SYNTAX              │ PURPOSE                        │ EXAMPLE
# ────────────────────┼────────────────────────────────┼──────────────────────────
# try/except          │ catch and handle error         │ except ValueError as e:
# try/except/else     │ else = success path            │ else: print(result)
# try/except/finally  │ finally = always cleanup       │ finally: f.close()
# except (A, B):      │ catch multiple types           │ except (Key, Index):
# except Exception:   │ catch all normal errors        │ NOT BaseException!
# as e                │ capture error object           │ e.args, str(e), type(e)
# raise               │ throw / re-raise exception     │ raise ValueError("msg")
# raise X from Y      │ chain exceptions               │ raise New() from original
# assert cond, msg    │ debug check (removed with -O)  │ assert x > 0, "positive"
#
# CUSTOM EXCEPTIONS:
#   class MyError(Exception):              minimal — just a name
#   class MyError(Exception):              with data:
#       def __init__(self, detail):            super().__init__(f"...")
#           self.detail = detail               self.detail = detail
#   class Base(Exception): pass            hierarchy:
#   class Sub1(Base): pass                   except Base catches Sub1 & Sub2
#   class Sub2(Base): pass
#
# COMPARISON TABLE:
# ────────────────────┬──────────────────────────────────────────
# bare except:        │ catches EVERYTHING (Ctrl+C too) — NEVER use
# except Exception:   │ catches all normal errors — PREFERRED
# except ValueError:  │ catches specific error — MOST SPECIFIC
# try/finally:        │ manual cleanup — verbose, error-prone
# with statement:     │ auto cleanup — clean, safe, Pythonic
# raise vs raise e:   │ raise keeps traceback, raise e resets it
# assert vs raise:    │ assert = debug only, raise = production validation
# LBYL vs EAFP:       │ if/check-first vs try/catch — Python prefers EAFP
# Exception vs warn:  │ exception STOPS, warning CONTINUES
# logging.exception:  │ logs message + full traceback automatically
# logging.error:      │ logs message only — no traceback
# suppress(Error):    │ context manager — silently ignore specific exceptions
# ────────────────────┴──────────────────────────────────────────
#
# COMMON PATTERNS:
#   Retry:      for i in range(n): try: return f() except: sleep(delay*i)
#   Default:    try: val = d["key"] except KeyError: val = default
#   Parse:      try: x = int(s) except ValueError: x = 0
#   Cleanup:    try: ... finally: resource.close()  OR  with resource:
#   Log+raise:  except E: logging.exception("..."); raise
#   Safe gen:   try: yield val except E: continue
#
# ══════════════════════════════════════════════════════════════════
#
# ══════════════════════════════════════════════════════════════════
#  EXCEPTION HANDLING — DETAILED REFERENCE
# ══════════════════════════════════════════════════════════════════
#
# ── try/except — Basic error catching ────────────────────────────
#   try:
#       risky_code()                → code that MIGHT raise an exception
#   except SomeError as e:          → catches SomeError (and its subclasses)
#       handle(e)                   → e is the exception object: str(e), type(e), e.args
#   If no exception: except block is SKIPPED.
#   If exception matches: except block runs, program continues AFTER the block.
#   If exception doesn't match: propagates UP the call stack (crash if uncaught).
#
# ── else — Success-only code ─────────────────────────────────────
#   try:
#       result = parse(data)        → only THIS can trigger the except
#   except ValueError:
#       handle_error()
#   else:
#       use(result)                 → runs ONLY if try succeeded — keeps try block narrow
#   Why not put it in try? Because errors in use(result) would be caught too.
#
# ── finally — Always runs ───────────────────────────────────────
#   try: ...
#   finally: cleanup()              → runs whether exception occurred or not
#   Even runs if: return in try, break in loop, exception propagates up.
#   Use for: closing files, releasing locks, DB rollback, network disconnect.
#
# ── raise — Throw exceptions ────────────────────────────────────
#   raise ValueError("msg")         → throw new exception
#   raise                           → re-raise current exception (in except block)
#   raise NewError() from original  → chain: NewError.__cause__ = original
#   raise NewError() from None      → suppress chain (hide original cause)
#
# ── Custom exceptions ───────────────────────────────────────────
#   class MyError(Exception):       → inherit from Exception (or a subclass)
#   Add __init__ for custom attributes (balance, code, detail, etc.)
#   Build hierarchies: class Base(Exception) → class Sub(Base)
#   Catching Base catches all Sub exceptions too.
#
# ── ExceptionGroup (3.11+) ──────────────────────────────────────
#   raise ExceptionGroup("msg", [e1, e2, e3])  → multiple errors at once
#   except* ValueError as eg:       → catches only ValueErrors from group
#   eg.exceptions                   → tuple of matched exceptions
#   Unmatched types propagate as a new ExceptionGroup. Used for parallel tasks.
#
# ── Context managers — Exception-safe resource management ───────
#   with open(f) as fh:             → __enter__ opens, __exit__ closes (even on error)
#   with suppress(KeyError):        → silently ignores KeyError (contextlib)
#   @contextmanager + try/yield/except → custom context manager with error handling
#
# ── Assertions ──────────────────────────────────────────────────
#   assert condition, "message"     → raises AssertionError if False
#   REMOVED by python -O flag! Never use for: user input, API validation, security.
#   Use for: invariants in tests, debug-only sanity checks, "this should never happen".
#
# ── Async exceptions ────────────────────────────────────────────
#   try: result = await coro() except E:    → same syntax, just add await
#   asyncio.gather(return_exceptions=True)  → errors returned as values, not raised
#   isinstance(r, Exception)                → check which results are errors
#
# ══════════════════════════════════════════════════════════════════

import os
if os.path.exists("test_exc.txt"):
    os.remove("test_exc.txt")
