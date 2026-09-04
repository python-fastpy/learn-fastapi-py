# ══════════════════════════════════════════════════════════════════
#  PYTHON ASYNC/AWAIT — Condensed Guide (Pure Python, no FastAPI)
#  async/await = write concurrent code that WAITS efficiently
#  Instead of blocking (freezing) while waiting for I/O,
#  Python switches to other tasks and comes back when ready
# ══════════════════════════════════════════════════════════════════
import asyncio
import time

# ╔══════════════════════════════════════════════════╗
# ║                  BEGINNER                        ║
# ╚══════════════════════════════════════════════════╝

# ── 1. The Problem — Why Async? ───────────────────
# Sync = one thing at a time, BLOCKS while waiting
# Async = start waiting tasks, switch to other work, come back when done

# SYNC — total time: 3 seconds (waits for each one)
def sync_example():
    time.sleep(1)    # blocks 1s — program frozen
    time.sleep(1)    # blocks 1s
    time.sleep(1)    # blocks 1s

# ASYNC — total time: 1 second (all 3 wait at the same time)
async def async_example():
    await asyncio.gather(
        asyncio.sleep(1),   # starts waiting
        asyncio.sleep(1),   # starts waiting at SAME time
        asyncio.sleep(1),   # starts waiting at SAME time
    )

# ── 2. Basic async/await ─────────────────────────
# async def → makes a COROUTINE (not a regular function)
# await     → pauses here, lets other tasks run, resumes when done

async def greet(name):
    print(f"Hello {name}!")
    await asyncio.sleep(1)          # non-blocking wait (other tasks can run)
    print(f"Goodbye {name}!")

# calling a coroutine:
# greet("Alice")              # WRONG — returns coroutine object, doesn't run!
# await greet("Alice")        # RIGHT — but only works inside another async func
# asyncio.run(greet("Alice")) # RIGHT — entry point from sync code

asyncio.run(greet("Alice"))
# Output: Hello Alice! → (1s pause) → Goodbye Alice!

# ── 3. asyncio.run() — The Entry Point ───────────
# asyncio.run() = starts the event loop and runs ONE coroutine
# You call this ONCE from sync code — everything else uses await

async def main():
    print("start")
    await asyncio.sleep(0.5)
    print("done")

asyncio.run(main())
# asyncio.run() does: create event loop → run main() → close loop

# ── 4. Coroutine vs Regular Function ─────────────
def regular():
    return "I run immediately"

async def coroutine():
    return "I need to be awaited"

print(regular())               # "I run immediately"
print(coroutine())             # <coroutine object ...> — NOT the result!
# print(await coroutine())     # "I need to be awaited" — only inside async

# ── 5. Sequential vs Concurrent ──────────────────
async def fetch_data(name, seconds):
    print(f"  Fetching {name}...")
    await asyncio.sleep(seconds)
    print(f"  Got {name}!")
    return f"{name} data"

# SEQUENTIAL — one after another (slow)
async def sequential():
    start = time.time()
    a = await fetch_data("users", 1)      # wait 1s
    b = await fetch_data("orders", 1)     # wait 1s
    c = await fetch_data("products", 1)   # wait 1s
    print(f"  Sequential: {time.time() - start:.1f}s")  # ~3.0s

# CONCURRENT — all at once (fast)
async def concurrent():
    start = time.time()
    a, b, c = await asyncio.gather(
        fetch_data("users", 1),            # starts immediately
        fetch_data("orders", 1),           # starts immediately
        fetch_data("products", 1),         # starts immediately
    )
    print(f"  Concurrent: {time.time() - start:.1f}s")  # ~1.0s

print("\n--- Sequential ---")
asyncio.run(sequential())
print("\n--- Concurrent ---")
asyncio.run(concurrent())


# ╔══════════════════════════════════════════════════╗
# ║               INTERMEDIATE                       ║
# ╚══════════════════════════════════════════════════╝

# ── 6. asyncio.gather() — Run Multiple Coroutines ─
# gather = run all, wait for ALL to finish, return results in order

async def gather_example():
    results = await asyncio.gather(
        fetch_data("A", 2),
        fetch_data("B", 1),
        fetch_data("C", 3),
    )
    print(f"  Results: {results}")   # ['A data', 'B data', 'C data'] — order preserved
    # Total time: ~3s (slowest), not 6s (sum)

asyncio.run(gather_example())

# ── 7. asyncio.gather() — Error Handling ─────────
async def might_fail(name, fail=False):
    await asyncio.sleep(0.5)
    if fail:
        raise ValueError(f"{name} failed!")
    return f"{name} ok"

# return_exceptions=True → errors returned as values, not raised
async def gather_errors():
    results = await asyncio.gather(
        might_fail("A"),
        might_fail("B", fail=True),
        might_fail("C"),
        return_exceptions=True,      # don't crash, collect errors
    )
    for r in results:
        if isinstance(r, Exception):
            print(f"  Error: {r}")
        else:
            print(f"  Success: {r}")

asyncio.run(gather_errors())
# Success: A ok
# Error: B failed!
# Success: C ok

# ── 8. create_task() — Fire and Continue ──────────
# create_task = schedule coroutine to run in background
# You can do other work while it runs

async def background_job(name, seconds):
    await asyncio.sleep(seconds)
    print(f"  Background {name} done!")
    return f"{name} result"

async def create_task_example():
    # schedule tasks — they start running immediately
    task1 = asyncio.create_task(background_job("download", 2))
    task2 = asyncio.create_task(background_job("upload", 1))

    print("  Tasks scheduled, doing other work...")
    await asyncio.sleep(0.5)
    print("  Still working...")

    # await when you need the results
    result1 = await task1
    result2 = await task2
    print(f"  Results: {result1}, {result2}")

asyncio.run(create_task_example())

# ── 9. gather() vs create_task() ─────────────────
#
#  gather():
#    results = await asyncio.gather(coro1(), coro2())
#    → runs all, waits for ALL, returns results as list
#    → best when: you need all results together
#
#  create_task():
#    task = asyncio.create_task(coro())
#    → schedules task, returns immediately
#    → await task later when you need the result
#    → best when: you want to do other work in between

# ── 10. Timeouts — asyncio.wait_for() ────────────
async def slow_operation():
    await asyncio.sleep(10)
    return "done"

async def timeout_example():
    try:
        result = await asyncio.wait_for(slow_operation(), timeout=2.0)
    except asyncio.TimeoutError:
        print("  Timed out after 2 seconds!")

asyncio.run(timeout_example())

# ── 11. async for — Async Iteration ──────────────
# Process items as they arrive (streaming, pagination, etc.)

async def fetch_pages():
    for page in range(1, 4):
        await asyncio.sleep(0.5)    # simulate API call
        yield {"page": page, "items": [f"item_{page}_{i}" for i in range(3)]}

async def async_for_example():
    async for page_data in fetch_pages():
        print(f"  Got page {page_data['page']}: {page_data['items']}")

asyncio.run(async_for_example())

# ── 12. async with — Async Context Manager ───────
# Like "with open()" but for async resources (DB connections, HTTP clients)

class AsyncDBConnection:
    async def __aenter__(self):
        print("  Connecting to DB...")
        await asyncio.sleep(0.3)
        print("  Connected!")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("  Closing DB connection...")
        await asyncio.sleep(0.1)
        print("  Closed!")

    async def query(self, sql):
        await asyncio.sleep(0.2)
        return [{"id": 1, "name": "Alice"}]

async def async_with_example():
    async with AsyncDBConnection() as db:
        results = await db.query("SELECT * FROM users")
        print(f"  Results: {results}")
    # connection auto-closed here

asyncio.run(async_with_example())


# ╔══════════════════════════════════════════════════╗
# ║                  ADVANCED                        ║
# ╚══════════════════════════════════════════════════╝

# ── 13. Semaphore — Limit Concurrency ────────────
# Problem: gather() with 1000 API calls → overwhelms the server
# Semaphore = "only N tasks at a time"

async def limited_fetch(sem, name):
    async with sem:              # only enters if < N tasks inside
        print(f"  Fetching {name}...")
        await asyncio.sleep(1)
        print(f"  Done {name}")
        return f"{name} data"

async def semaphore_example():
    sem = asyncio.Semaphore(3)   # max 3 concurrent tasks
    tasks = [limited_fetch(sem, f"item-{i}") for i in range(8)]
    results = await asyncio.gather(*tasks)
    print(f"  Got {len(results)} results")
    # runs 3 at a time: [0,1,2] → [3,4,5] → [6,7]

asyncio.run(semaphore_example())

# ── 14. Lock — Prevent Race Conditions ───────────
# When multiple tasks read/write the same variable

counter = 0

async def unsafe_increment(n):
    global counter
    for _ in range(n):
        temp = counter
        await asyncio.sleep(0)   # yield control — another task can change counter!
        counter = temp + 1

async def safe_increment(lock, n):
    global counter
    for _ in range(n):
        async with lock:         # only one task at a time
            temp = counter
            await asyncio.sleep(0)
            counter = temp + 1

async def lock_example():
    global counter

    # UNSAFE — race condition
    counter = 0
    await asyncio.gather(unsafe_increment(100), unsafe_increment(100))
    print(f"  Unsafe counter: {counter}")   # likely < 200!

    # SAFE — with lock
    counter = 0
    lock = asyncio.Lock()
    await asyncio.gather(safe_increment(lock, 100), safe_increment(lock, 100))
    print(f"  Safe counter: {counter}")     # always 200

asyncio.run(lock_example())

# ── 15. Queue — Producer/Consumer Pattern ────────
# Producer adds items, consumer processes them — decoupled

async def producer(queue, name, items):
    for item in items:
        await asyncio.sleep(0.2)
        await queue.put(f"{name}:{item}")
        print(f"  Produced {name}:{item}")
    await queue.put(None)        # signal "I'm done"

async def consumer(queue, name):
    while True:
        item = await queue.get()
        if item is None:
            break
        await asyncio.sleep(0.3)
        print(f"  {name} consumed {item}")

async def queue_example():
    queue = asyncio.Queue(maxsize=5)   # max 5 items buffered
    await asyncio.gather(
        producer(queue, "P1", ["a", "b", "c"]),
        consumer(queue, "C1"),
    )

asyncio.run(queue_example())

# ── 16. Event — Signal Between Tasks ─────────────
# One task waits for a signal, another task sends it

async def waiter(event, name):
    print(f"  {name} waiting for signal...")
    await event.wait()           # blocks until event is set
    print(f"  {name} got the signal!")

async def trigger(event):
    print("  Preparing data...")
    await asyncio.sleep(1)
    print("  Setting event!")
    event.set()                  # all waiters wake up

async def event_example():
    event = asyncio.Event()
    await asyncio.gather(
        waiter(event, "Task-A"),
        waiter(event, "Task-B"),
        trigger(event),
    )

asyncio.run(event_example())

# ── 17. shield() — Protect from Cancellation ─────
# Normally, cancelling a parent cancels children too
# shield() prevents a specific task from being cancelled

async def critical_operation():
    print("  Critical operation started...")
    await asyncio.sleep(2)
    print("  Critical operation done!")
    return "important result"

async def shield_example():
    task = asyncio.create_task(asyncio.shield(critical_operation()))
    await asyncio.sleep(0.5)
    task.cancel()                # tries to cancel
    try:
        await task
    except asyncio.CancelledError:
        print("  Task was cancelled, but shielded operation continues")

asyncio.run(shield_example())

# ── 18. TaskGroup (3.11+) — Structured Concurrency ─
# Like gather() but cancels all tasks if ANY one fails

async def task_group_example():
    try:
        async with asyncio.TaskGroup() as tg:
            task1 = tg.create_task(fetch_data("A", 1))
            task2 = tg.create_task(fetch_data("B", 2))
            # all tasks must complete before exiting the block
        print(f"  Results: {task1.result()}, {task2.result()}")
    except* ValueError as eg:       # ExceptionGroup (3.11+)
        for e in eg.exceptions:
            print(f"  Error: {e}")

asyncio.run(task_group_example())

# ── 19. Running Sync Code in Async ───────────────
# Problem: you have a blocking function (file I/O, CPU work)
# Solution: run it in a thread pool so it doesn't block the event loop

import hashlib

def blocking_hash(data):
    """CPU-heavy work — would block the event loop"""
    return hashlib.sha256(data.encode()).hexdigest()

async def run_sync_example():
    loop = asyncio.get_event_loop()
    # run_in_executor → runs in thread pool, doesn't block event loop
    result = await loop.run_in_executor(None, blocking_hash, "hello world")
    print(f"  Hash: {result[:16]}...")

asyncio.run(run_sync_example())

# ── 20. asyncio.wait() — More Control Than gather ─
# wait() gives you done/pending sets — you can process as they finish

async def random_delay(name, seconds):
    await asyncio.sleep(seconds)
    return f"{name} done in {seconds}s"

async def wait_example():
    tasks = [
        asyncio.create_task(random_delay("fast", 0.5)),
        asyncio.create_task(random_delay("medium", 1.5)),
        asyncio.create_task(random_delay("slow", 2.5)),
    ]

    # FIRST_COMPLETED — returns as soon as ANY one finishes
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for t in done:
        print(f"  First done: {t.result()}")
    print(f"  Still pending: {len(pending)}")

    # wait for the rest
    done2, _ = await asyncio.wait(pending)
    for t in done2:
        print(f"  Later done: {t.result()}")

asyncio.run(wait_example())


# ══════════════════════════════════════════════════════════════════
#  CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
#
#  BASICS:
#    async def f():             define a coroutine
#    await coro()               pause here, run other tasks, resume when done
#    asyncio.run(main())        entry point from sync code (call ONCE)
#
#  RUNNING CONCURRENTLY:
#    asyncio.gather(a, b, c)    run all, wait ALL, return results list
#    asyncio.create_task(c)     schedule in background, await later
#    async with TaskGroup() as tg:  structured concurrency (3.11+)
#
#  CONTROL:
#    asyncio.wait_for(c, timeout=5)   timeout a coroutine
#    asyncio.wait(tasks)              fine-grained done/pending control
#    asyncio.shield(c)                protect from cancellation
#
#  SYNC PRIMITIVES:
#    Semaphore(n)     limit to N concurrent tasks
#    Lock()           one task at a time (prevent race conditions)
#    Event()          signal between tasks (wait/set)
#    Queue()          producer/consumer pattern
#
#  ASYNC PATTERNS:
#    async for x in gen:   iterate over async generator
#    async with ctx:       async context manager (__aenter__/__aexit__)
#    yield in async def    async generator (stream data)
#
#  BLOCKING CODE IN ASYNC:
#    await loop.run_in_executor(None, sync_func, args)
#    → runs in thread pool, doesn't freeze event loop
#
#  KEY RULES:
#    Never time.sleep() in async    → use asyncio.sleep()
#    Never requests.get() in async  → use httpx.AsyncClient
#    Never blocking I/O in async    → use run_in_executor()
#    await only inside async def    → asyncio.run() from sync
#
#  gather() vs create_task():
#    gather   → need all results together → await asyncio.gather(a, b)
#    task     → do work in between       → t = create_task(a); ...; await t
#
#  ERRORS:
#    gather(return_exceptions=True)  → errors in results, no crash
#    TaskGroup                       → cancels all if one fails (3.11+)
#    shield()                        → protect task from parent cancel
# ══════════════════════════════════════════════════════════════════

# ╔══════════════════════════════════════════════════╗
# ║          INTERVIEW GOTCHAS                       ║
# ╚══════════════════════════════════════════════════╝

# ── Q: What's the difference between concurrency and parallelism? ──
# Concurrency = multiple tasks in progress (switching between them) — ONE thread
# Parallelism = multiple tasks running at the SAME instant — multiple threads/CPUs
# asyncio = CONCURRENT, not parallel — single thread, switches during await

# ── Q: What happens if you call time.sleep() in async? ──
# It BLOCKS the entire event loop — no other task can run!
# Always use asyncio.sleep() in async code

# ── Q: Can you await a regular function? ──
# No — you can only await a coroutine (async def) or an awaitable object
# await regular_func()  → TypeError: object int can't be used in 'await'

# ── Q: gather() vs TaskGroup — when to use which? ──
# gather()    → older, more flexible, return_exceptions=True
# TaskGroup() → 3.11+, structured, cancels all on first error (safer)

# ── Q: What is the event loop? ──
# The event loop is the scheduler that runs async tasks
# It checks: "any task ready to resume?" → runs it until next await → checks again
# asyncio.run() creates the loop, asyncio.get_event_loop() gets the current one

# ── Q: Why can't you use requests library in async code? ──
# requests.get() is BLOCKING — it freezes the event loop while waiting
# Use httpx.AsyncClient instead — it's async-native:
#   async with httpx.AsyncClient() as client:
#       resp = await client.get(url)
