# ══════════════════════════════════════════════════════════════════
# Python Async/Await Guide with FastAPI  (~25 patterns, condensed)
# ══════════════════════════════════════════════════════════════════
import asyncio, httpx
from fastapi import FastAPI, HTTPException
from typing import Optional
app = FastAPI()
shipment_data = {
    1: {"id": 1, "content": "Shipment 1", "weight": 10, "status": "In Transit"},
    2: {"id": 2, "content": "Shipment 2", "weight": 20, "status": "Delivered"},
    3: {"id": 3, "content": "Shipment 3", "weight": 15, "status": "Pending"},
}

# ╔══════════════════════════════════════════════════╗
# ║               BEGINNER                           ║
# ╚══════════════════════════════════════════════════╝

# ── 1. Sync vs Async Endpoints ─────────────────────
#  def        → thread pool (CPU work)  |  async def → event loop (I/O)
#  KEY RULE: inside async def, "await" before any async op
@app.get("/sync/shipment/{id}")
def get_shipment_sync(id: int):                       # sync — thread pool
    if id not in shipment_data: raise HTTPException(404, "Not found")
    return shipment_data[id]
@app.get("/async/shipment/{id}")
async def get_shipment_async(id: int):                # async — event loop
    if id not in shipment_data: raise HTTPException(404, "Not found")
    return shipment_data[id]

# ── 2. Await a Sleep ───────────────────────────────
#  asyncio.sleep() = non-blocking  |  time.sleep() = BLOCKING (freezes server!)
@app.get("/async/slow-shipment/{id}")
async def get_shipment_slow(id: int):
    await asyncio.sleep(2)  # server handles other requests during wait
    if id not in shipment_data: raise HTTPException(404, "Not found")
    return {"shipment": shipment_data[id]}

# ── 3. Await HTTP Call (httpx) ─────────────────────
#  httpx.AsyncClient = async  |  requests.get() = BLOCKING (never in async def!)
@app.get("/async/external-api")
async def call_external_api():
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://jsonplaceholder.typicode.com/todos/1")
    return {"external_data": resp.json()}

# ── 4. Sequential Awaits ──────────────────────────
#  Each await waits for previous → total = sum of all waits
@app.get("/async/sequential")
async def sequential_calls():
    async with httpx.AsyncClient() as client:
        r1 = await client.get("https://jsonplaceholder.typicode.com/todos/1")
        r2 = await client.get("https://jsonplaceholder.typicode.com/todos/2")
        r3 = await client.get("https://jsonplaceholder.typicode.com/todos/3")
    return {"t1": r1.json()["title"], "t2": r2.json()["title"], "t3": r3.json()["title"]}

# ╔══════════════════════════════════════════════════╗
# ║             INTERMEDIATE                         ║
# ╚══════════════════════════════════════════════════╝

# ── 5. asyncio.gather() — Parallel ────────────────
#  gather(*coros) → all at once, results IN ORDER, total = max wait
@app.get("/async/parallel")
async def parallel_calls():
    async with httpx.AsyncClient() as client:
        r1, r2, r3 = await asyncio.gather(
            client.get("https://jsonplaceholder.typicode.com/todos/1"),
            client.get("https://jsonplaceholder.typicode.com/todos/2"),
            client.get("https://jsonplaceholder.typicode.com/todos/3"),
        )  # ~1s total instead of ~3s
    return {"t1": r1.json()["title"], "t2": r2.json()["title"], "t3": r3.json()["title"]}

# ── 6. Gather — Dynamic List ─────────────────────
@app.get("/async/parallel-dynamic")
async def parallel_dynamic(ids: str = "1,2,3,4,5"):
    todo_ids = [int(i) for i in ids.split(",")]
    async with httpx.AsyncClient() as client:
        responses = await asyncio.gather(
            *[client.get(f"https://jsonplaceholder.typicode.com/todos/{t}") for t in todo_ids])
    return {"results": [r.json()["title"] for r in responses]}

# ── 7. Gather — Error Handling ────────────────────
#  return_exceptions=True → failed tasks return Exception, others still complete
@app.get("/async/parallel-safe")
async def parallel_with_error_handling():
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            client.get("https://jsonplaceholder.typicode.com/todos/1"),
            client.get("https://invalid-url.com/data"),
            client.get("https://jsonplaceholder.typicode.com/todos/3"),
            return_exceptions=True)
    return [{"task": i+1, "error": str(r)} if isinstance(r, Exception)
            else {"task": i+1, "data": r.json()["title"]} for i, r in enumerate(results)]

# ── 8-9. Async Helpers (Sequential & Parallel) ────
async def fetch_from_db(id: int) -> dict:
    await asyncio.sleep(0.5); return shipment_data.get(id)
async def enrich(shipment: dict) -> dict:
    await asyncio.sleep(0.3); shipment["tracking"] = f"https://track.example.com/{shipment['id']}"; return shipment
async def get_weight(id: int): await asyncio.sleep(0.5); return shipment_data.get(id, {}).get("weight", 0)
async def get_status(id: int): await asyncio.sleep(0.5); return shipment_data.get(id, {}).get("status", "?")

@app.get("/async/helper/{id}")
async def get_with_helpers(id: int):                  # sequential: 0.5 + 0.3 = 0.8s
    s = await fetch_from_db(id)
    if not s: raise HTTPException(404, "Not found")
    return await enrich(s.copy())

@app.get("/async/parallel-helpers/{id}")
async def get_with_parallel_helpers(id: int):         # parallel: max(0.5, 0.5) = 0.5s
    if id not in shipment_data: raise HTTPException(404, "Not found")
    weight, status = await asyncio.gather(get_weight(id), get_status(id))
    return {"id": id, "weight": weight, "status": status}

# ── 10. create_task() — Fire and Forget ───────────
#  Starts background work; endpoint returns immediately. Task lost on shutdown.
async def send_notification(sid: int, msg: str):
    await asyncio.sleep(2); print(f"NOTIFICATION: Shipment {sid} - {msg}")

@app.post("/async/fire-and-forget/{id}")
async def update_and_notify(id: int):
    if id not in shipment_data: raise HTTPException(404, "Not found")
    shipment_data[id]["status"] = "Delivered"
    asyncio.create_task(send_notification(id, "Status changed"))
    return {"shipment": shipment_data[id]}

# ── 11. wait_for() — Timeout ─────────────────────
async def slow_db_query(id: int): await asyncio.sleep(5); return shipment_data.get(id)

@app.get("/async/timeout/{id}")
async def get_with_timeout(id: int):
    try: return await asyncio.wait_for(slow_db_query(id), timeout=2.0)
    except asyncio.TimeoutError: raise HTTPException(504, "Timed out after 2s")

# ── 12. Semaphore — Limit Concurrency ────────────
#  Semaphore(N) = max N concurrent; others wait for a slot
sem = asyncio.Semaphore(3)
async def rate_limited_fetch(client: httpx.AsyncClient, tid: int):
    async with sem:
        return (await client.get(f"https://jsonplaceholder.typicode.com/todos/{tid}")).json()

@app.get("/async/semaphore")
async def get_with_semaphore():
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(*[rate_limited_fetch(client, i) for i in range(1, 11)])
    return {"count": len(results), "titles": [r["title"] for r in results]}

# ── 13. Lock — Prevent Race Conditions ────────────
#  Lock = only ONE task at a time  (vs Semaphore = N at a time)
counter = {"value": 0}
lock = asyncio.Lock()
async def inc_safe():
    async with lock: c = counter["value"]; await asyncio.sleep(0.01); counter["value"] = c + 1
async def inc_unsafe():
    c = counter["value"]; await asyncio.sleep(0.01); counter["value"] = c + 1

@app.get("/async/lock-demo")
async def lock_demo():
    counter["value"] = 0; await asyncio.gather(*[inc_safe() for _ in range(10)])
    safe = counter["value"]  # always 10
    counter["value"] = 0; await asyncio.gather(*[inc_unsafe() for _ in range(10)])
    return {"with_lock": safe, "without_lock": counter["value"]}  # unsafe might be < 10

# ── 14. Event — Coordinate Tasks ─────────────────
#  set() = signal  |  wait() = block until set  |  clear() = reset
@app.get("/async/event-demo")
async def event_demo():
    ready, steps = asyncio.Event(), []
    async def setup():
        steps.append("DB starting"); await asyncio.sleep(1); steps.append("DB ready"); ready.set()
    async def query():
        steps.append("Query waiting"); await ready.wait(); steps.append("Query running")
    await asyncio.gather(setup(), query())
    return {"steps": steps}

# ── 15. Queue — Producer/Consumer ─────────────────
@app.post("/async/queue-demo")
async def queue_demo():
    q, results = asyncio.Queue(), []
    async def producer():
        for id in shipment_data: await q.put(id); await asyncio.sleep(0.1)
        await q.put(None)
    async def consumer():
        while (id := await q.get()) is not None:
            await asyncio.sleep(0.2); results.append({"id": id, "ok": True}); q.task_done()
    await asyncio.gather(producer(), consumer())
    return {"processed": results}

# ╔══════════════════════════════════════════════════╗
# ║               ADVANCED                           ║
# ╚══════════════════════════════════════════════════╝

# ── 16. async for — Async Generators ─────────────
async def fetch_pages(page_size: int = 2):
    ids = list(shipment_data.keys())
    for i in range(0, len(ids), page_size):
        await asyncio.sleep(0.3)
        yield [shipment_data[sid] for sid in ids[i:i+page_size]]

@app.get("/async/async-for")
async def get_with_async_for():
    items, pages = [], 0
    async for page in fetch_pages():
        pages += 1; items.extend(page)
    return {"pages": pages, "total": len(items), "data": items}

# ── 17. async with — Async Context Manager ───────
class AsyncDBConn:
    async def __aenter__(self):
        await asyncio.sleep(0.2); self.connected = True; return self
    async def __aexit__(self, *exc):
        await asyncio.sleep(0.1); self.connected = False; return False
    async def query(self, id: int) -> Optional[dict]:
        await asyncio.sleep(0.1); return shipment_data.get(id)

@app.get("/async/context-manager/{id}")
async def get_with_ctx(id: int):
    async with AsyncDBConn() as db:
        result = await db.query(id)
        if not result: raise HTTPException(404, "Not found")
        return {"shipment": result, "connected": db.connected}

# ── 18. shield() — Protect from Cancellation ─────
#  Inner task survives even if outer is cancelled. Use for payments, saves.
async def critical_save(id: int):
    await asyncio.sleep(1); shipment_data[id]["status"] = "Saved"; return shipment_data[id]

@app.post("/async/shield/{id}")
async def save_with_shield(id: int):
    if id not in shipment_data: raise HTTPException(404, "Not found")
    try: return await asyncio.wait_for(asyncio.shield(critical_save(id)), timeout=0.5)
    except asyncio.TimeoutError: return {"note": "Timed out, but save still running"}

# ── 19. to_thread() — Sync in Async ─────────────
def heavy_cpu_work(id: int): return {"id": id, "sum": sum(range(1_000_000))}

@app.get("/async/sync-in-async/{id}")
async def call_sync_from_async(id: int):
    return await asyncio.to_thread(heavy_cpu_work, id)

# ── 20. as_completed() — Fastest First ───────────
#  gather = input order  |  as_completed = finish order
async def fetch_delayed(id: int, delay: float):
    await asyncio.sleep(delay); return {"id": id, "delay": delay}

@app.get("/async/as-completed")
async def process_as_completed():
    tasks = [asyncio.create_task(fetch_delayed(1, 2.0)),
             asyncio.create_task(fetch_delayed(2, 0.5)),
             asyncio.create_task(fetch_delayed(3, 1.0))]
    results, n = [], 1
    for done in asyncio.as_completed(tasks):
        r = await done; r["order"] = n; results.append(r); n += 1
    return {"results": results}  # id=2 first, id=3 second, id=1 last

# ── 21. Retry Pattern ────────────────────────────
_attempts = {"n": 0}
async def unreliable():
    _attempts["n"] += 1
    if _attempts["n"] < 3: raise Exception(f"Fail #{_attempts['n']}")
    return {"data": "ok", "attempts": _attempts["n"]}

async def retry_async(func, retries=3, delay=0.5):
    for i in range(1, retries + 1):
        try: return await func()
        except Exception as e:
            if i == retries: raise
            await asyncio.sleep(delay * i)

@app.get("/async/retry")
async def get_with_retry():
    _attempts["n"] = 0
    try: return await retry_async(unreliable, retries=5, delay=0.3)
    except Exception as e: raise HTTPException(503, str(e))

# ── 22. Async Comprehension ──────────────────────
async def process_one(id: int):
    await asyncio.sleep(0.1); s = shipment_data.get(id)
    return {**s, "processed": True} if s else {"id": id, "processed": False}

@app.get("/async/comprehension")
async def async_comprehension():
    # WRONG: [await process_one(id) for id in ids]  ← sequential!
    # RIGHT: gather for parallel
    return {"results": list(await asyncio.gather(*[process_one(id) for id in shipment_data]))}

# ── 23. Chaining — fetch -> transform -> validate
async def s_fetch(id: int): await asyncio.sleep(0.2); return shipment_data.get(id, {})
async def s_transform(d: dict): await asyncio.sleep(0.2); d["weight_lbs"] = round(d.get("weight", 0) * 2.205, 2); return d
async def s_validate(d: dict): await asyncio.sleep(0.1); d["valid"] = d.get("weight_lbs", 0) > 0; return d

@app.get("/async/chain/{id}")
async def chained_pipeline(id: int):
    if id not in shipment_data: raise HTTPException(404, "Not found")
    return await s_validate(await s_transform((await s_fetch(id)).copy()))

# ── 24. Fan-Out / Fan-In ─────────────────────────
#  Fan-out: 1 input -> N parallel tasks  |  Fan-in: N results -> 1 output
async def check_warehouse(wh: str, id: int):
    await asyncio.sleep(0.3); return {"wh": wh, "avail": (id + hash(wh)) % 2 == 0}

@app.get("/async/fan-out/{id}")
async def fan_out_fan_in(id: int):
    whs = ["NYC", "LON", "TYO", "SYD", "BER"]
    results = await asyncio.gather(*[check_warehouse(w, id) for w in whs])
    return {"id": id, "available": [r["wh"] for r in results if r["avail"]], "checked": len(results)}

# ══════════════════════════════════════════════════════════════════
# CHEAT SHEET
# ══════════════════════════════════════════════════════════════════
#  CONCEPT              │ TOOL                        │ USE WHEN
# ──────────────────────┼─────────────────────────────┼─────────────────────────────
#  Non-blocking wait    │ await asyncio.sleep(n)      │ Simulate delay, yield control
#  Async HTTP           │ httpx.AsyncClient           │ External API calls
#  Run in parallel      │ asyncio.gather(*coros)      │ Multiple independent I/O ops
#  Safe parallel        │ gather(return_exceptions=T) │ Some tasks may fail
#  Background task      │ asyncio.create_task(coro)   │ Fire-and-forget (logs, notifs)
#  Timeout              │ asyncio.wait_for(c, t)      │ Cancel if too slow
#  Limit concurrency    │ asyncio.Semaphore(N)        │ Rate-limit API/DB calls
#  Mutual exclusion     │ asyncio.Lock()              │ Prevent race conditions
#  Signal readiness     │ asyncio.Event()             │ "Wait until X is ready"
#  Producer/consumer    │ asyncio.Queue()             │ Job processing pipelines
#  Protect from cancel  │ asyncio.shield(coro)        │ Critical ops (payments, saves)
#  Sync in async        │ asyncio.to_thread(fn)       │ CPU work / blocking libraries
#  Fastest first        │ asyncio.as_completed(tasks) │ Process results as they arrive
#  Retry on failure     │ retry_async(fn, n, delay)   │ Unreliable external services
#  Async iteration      │ async for x in gen()        │ Paginated/streaming data
#  Async context mgr    │ async with Resource() as r  │ Setup/teardown needing await
#  Async comprehension  │ gather(*[coro for ...])     │ Parallel list processing
#  Chaining             │ await g(await f(x))         │ Pipeline: fetch->transform->save
#  Fan-out/fan-in       │ gather → filter/combine     │ Split work, merge results
#
#  COMPARISON           │ A                           │ B
# ──────────────────────┼─────────────────────────────┼─────────────────────────────
#  Blocking vs async    │ time.sleep() — blocks       │ asyncio.sleep() — yields
#  HTTP client          │ requests.get() — sync       │ httpx.AsyncClient — async
#  Endpoint             │ def f() — thread pool       │ async def f() — event loop
#  gather vs create_task│ gather: await all results   │ create_task: fire-and-forget
#  gather vs as_compl.  │ gather: input order         │ as_completed: finish order
#  Semaphore vs Lock    │ Semaphore(N): N concurrent  │ Lock: exactly 1 at a time
#  Sequential vs ||     │ await a; await b — sum time │ gather(a,b) — max time
# ══════════════════════════════════════════════════════════════════
#
# ══════════════════════════════════════════════════════════════════
#  ASYNC/AWAIT — DETAILED REFERENCE
# ══════════════════════════════════════════════════════════════════
#
# ── async def vs def — When to use which ─────────────────────────
#   async def route():     → runs on event loop, use for I/O (HTTP, DB, files)
#   def route():           → runs in thread pool, use for CPU work (calculations)
#   KEY RULE: inside async def, you MUST "await" any async operation
#   NEVER use time.sleep() or requests.get() in async def — they BLOCK the event loop
#
#   BEGINNER EXAMPLE — async vs sync endpoints:
#
#     # Async — for I/O (HTTP calls, DB queries, file reads):
#     @app.get("/async")
#     async def async_route():
#         data = await fetch_from_db()    # ← yields control, doesn't block
#         return data
#
#     # Sync — for CPU work (calculations, image processing):
#     @app.get("/sync")
#     def sync_route():
#         result = heavy_calculation()     # ← runs in thread pool automatically
#         return result
#
#     # Both called the same way:
#     #   curl "http://localhost:8000/async"
#     #   curl "http://localhost:8000/sync"
#     #
#     # Difference is INTERNAL — async yields to event loop, sync gets a thread
#
# ── await — Pause and yield control ──────────────────────────────
#   result = await some_async_function()
#   Pauses THIS function, lets event loop handle other requests.
#   Only works inside async def. The awaited function must be a coroutine.
#
# ── asyncio.gather() — Run tasks in parallel ─────────────────────
#   r1, r2, r3 = await asyncio.gather(coro1(), coro2(), coro3())
#   All run concurrently. Results returned IN INPUT ORDER.
#   Total time = max(individual times), not sum.
#   return_exceptions=True → failed tasks return Exception object instead of crashing all.
#   Dynamic: await asyncio.gather(*[fetch(id) for id in ids])
#
#   BEGINNER EXAMPLE — gather():
#
#     async def fetch_user(id): await asyncio.sleep(1); return {"id": id}
#     async def fetch_orders(id): await asyncio.sleep(1); return [{"order": 1}]
#     async def fetch_prefs(id): await asyncio.sleep(1); return {"theme": "dark"}
#
#     @app.get("/user/{id}")
#     async def get_user_full(id: int):
#         user, orders, prefs = await asyncio.gather(
#             fetch_user(id), fetch_orders(id), fetch_prefs(id)
#         )
#         return {"user": user, "orders": orders, "prefs": prefs}
#
#     # How to call:
#     #   curl "http://localhost:8000/user/1"
#     #
#     #   WITHOUT gather (sequential):
#     #     fetch_user   ──1s──▶
#     #     fetch_orders        ──1s──▶
#     #     fetch_prefs                ──1s──▶
#     #     Total: 3 seconds
#     #
#     #   WITH gather (parallel):
#     #     fetch_user   ──1s──▶
#     #     fetch_orders ──1s──▶  ← all start at same time
#     #     fetch_prefs  ──1s──▶
#     #     Total: 1 second (max of individual times)
#     #
#     #   Results returned in INPUT order (not finish order):
#     #     user → {"id": 1}, orders → [{"order": 1}], prefs → {"theme": "dark"}
#
# ── asyncio.create_task() — Fire and forget ──────────────────────
#   asyncio.create_task(send_email(user))
#   Starts background work. Endpoint returns immediately.
#   Task runs in background. WARNING: lost on server shutdown.
#   Use for: logging, notifications, non-critical side effects.
#
#   BEGINNER EXAMPLE — create_task():
#
#     async def send_notification(user_id: int, msg: str):
#         await asyncio.sleep(2)       # simulate slow email
#         print(f"Notified user {user_id}: {msg}")
#
#     @app.post("/order")
#     async def create_order():
#         order = {"id": 99, "status": "created"}
#         asyncio.create_task(send_notification(1, "Order created"))
#         return order                  # ← returns IMMEDIATELY, email sends in background
#
#     # How to call:
#     #   curl -X POST "http://localhost:8000/order"
#     #     → {"id": 99, "status": "created"}  (instant response)
#     #     → 2 seconds later: "Notified user 1: Order created" (in server logs)
#     #
#     #   Timeline:
#     #     create_order() ──returns──▶ client gets response
#     #     send_notification() ──────────2s──────────▶ prints in background
#
# ── asyncio.wait_for() — Timeout ────────────────────────────────
#   result = await asyncio.wait_for(slow_query(), timeout=2.0)
#   Raises asyncio.TimeoutError if not done in time. Cancels the task.
#
#   BEGINNER EXAMPLE — wait_for() timeout:
#
#     async def slow_query():
#         await asyncio.sleep(5)       # takes 5 seconds
#         return {"data": "result"}
#
#     @app.get("/query")
#     async def get_query():
#         try:
#             result = await asyncio.wait_for(slow_query(), timeout=2.0)
#             return result
#         except asyncio.TimeoutError:
#             raise HTTPException(504, "Query took too long")
#
#     # How to call:
#     #   curl "http://localhost:8000/query"
#     #
#     #   Timeline:
#     #     slow_query() starts ──2s──▶ TIMEOUT! → 504 "Query took too long"
#     #                                 (cancelled at 2s, never reaches 5s)
#     #
#     #   If query finishes in < 2s → normal response
#     #   If query takes > 2s → TimeoutError → task cancelled
#
# ── asyncio.Semaphore(N) — Limit concurrency ────────────────────
#   sem = asyncio.Semaphore(3)        → max 3 concurrent
#   async with sem:                   → acquire slot (blocks if all N taken)
#       await do_work()               → work runs with slot held
#   Use for: rate-limiting API calls, DB connection limits.
#
#   BEGINNER EXAMPLE — Semaphore:
#
#     sem = asyncio.Semaphore(3)   # max 3 concurrent API calls
#
#     async def call_api(id):
#         async with sem:            # ← waits if 3 already running
#             await asyncio.sleep(1) # simulate API call
#             return {"id": id}
#
#     @app.get("/batch")
#     async def batch():
#         results = await asyncio.gather(*[call_api(i) for i in range(10)])
#         return results
#
#     # How to call:
#     #   curl "http://localhost:8000/batch"
#     #
#     #   10 tasks but Semaphore(3) → only 3 run at a time:
#     #     Time 0s: tasks 0,1,2 start  │ tasks 3-9 wait
#     #     Time 1s: tasks 0,1,2 done   │ tasks 3,4,5 start
#     #     Time 2s: tasks 3,4,5 done   │ tasks 6,7,8 start
#     #     Time 3s: tasks 6,7,8 done   │ task 9 starts
#     #     Time 4s: task 9 done        │ total ~4s (not 10s, not 1s)
#
# ── asyncio.Lock() — Mutual exclusion ───────────────────────────
#   lock = asyncio.Lock()
#   async with lock:                  → only ONE task at a time
#       counter += 1                  → safe from race conditions
#   Semaphore(1) == Lock(). Use Lock when exactly-one is the intent.
#
#   BEGINNER EXAMPLE — Lock:
#
#     counter = {"value": 0}
#     lock = asyncio.Lock()
#
#     @app.post("/increment")
#     async def increment():
#         async with lock:                 # ← only ONE request at a time
#             counter["value"] += 1        # safe — no race condition
#         return counter
#
#     # Without lock: 2 requests at same time could both read 0, both write 1
#     # With lock: request A holds lock → B waits → A writes 1 → B reads 1, writes 2
#
# ── asyncio.Event() — Signal between tasks ──────────────────────
#   event = asyncio.Event()
#   await event.wait()                → blocks until event.set() is called
#   event.set()                       → unblocks all waiters
#   event.clear()                     → reset to unset state
#   Use for: "wait until database is ready", "wait until config loaded"
#
#   BEGINNER EXAMPLE — Event:
#
#     db_ready = asyncio.Event()
#
#     async def init_db():
#         await asyncio.sleep(2)       # simulate slow DB connect
#         db_ready.set()               # ← signal "ready!"
#
#     @app.get("/data")
#     async def get_data():
#         await db_ready.wait()        # ← blocks until db_ready.set() is called
#         return {"status": "db is ready"}
#
#     # Flow:
#     #   Server starts → init_db() begins (2s)
#     #   curl /data at 0s → waits... waits...
#     #   At 2s: db_ready.set() → all waiters unblocked → response returned
#
# ── asyncio.Queue() — Producer/consumer ─────────────────────────
#   q = asyncio.Queue()
#   await q.put(item)                 → producer adds work
#   item = await q.get()              → consumer takes work (blocks if empty)
#   q.task_done()                     → mark item as processed
#   Use for: job processing, work distribution, buffering.
#
#   BEGINNER EXAMPLE — Queue:
#
#     job_queue = asyncio.Queue()
#
#     @app.post("/job")
#     async def submit_job():
#         await job_queue.put({"task": "process", "id": 1})  # producer
#         return {"queued": True, "pending": job_queue.qsize()}
#
#     async def worker():
#         while True:
#             job = await job_queue.get()    # blocks until job available
#             print(f"Processing: {job}")
#             job_queue.task_done()
#
#     # curl -X POST "http://localhost:8000/job"
#     #   → {"queued": true, "pending": 1}
#     #   → worker picks up job from queue and processes it
#
# ── asyncio.shield() — Protect from cancellation ────────────────
#   await asyncio.shield(critical_save(data))
#   Even if outer task is cancelled, shielded task keeps running.
#   Use for: payments, database commits, anything that MUST finish.
#
#   BEGINNER EXAMPLE — shield:
#
#     async def save_payment(id):
#         await asyncio.sleep(3)        # slow but MUST complete
#         return {"id": id, "saved": True}
#
#     @app.post("/pay/{id}")
#     async def pay(id: int):
#         try:
#             return await asyncio.wait_for(asyncio.shield(save_payment(id)), timeout=1)
#         except asyncio.TimeoutError:
#             return {"msg": "Timed out, but payment still processing"}
#
#     # curl -X POST "http://localhost:8000/pay/1"
#     #   → timeout after 1s → {"msg": "Timed out, but payment still processing"}
#     #   → BUT save_payment keeps running in background (shield protects it)
#     #   Without shield: timeout would CANCEL save_payment → payment lost!
#
# ── asyncio.to_thread() — Run sync code in async context ────────
#   result = await asyncio.to_thread(heavy_cpu_function, arg1, arg2)
#   Runs sync function in thread pool, doesn't block event loop.
#   Use for: CPU-heavy work, libraries that don't support async.
#
#   BEGINNER EXAMPLE — to_thread:
#
#     def heavy_cpu_work(n):           # sync function — can't use await
#         return sum(range(n))         # CPU-intensive calculation
#
#     @app.get("/compute/{n}")
#     async def compute(n: int):
#         result = await asyncio.to_thread(heavy_cpu_work, n)
#         return {"sum": result}
#
#     # curl "http://localhost:8000/compute/1000000"
#     #   → {"sum": 499999500000}
#     #
#     #   Without to_thread: heavy_cpu_work BLOCKS event loop → other requests wait
#     #   With to_thread: runs in thread pool → event loop stays free for other requests
#
# ── asyncio.as_completed() — Process fastest first ──────────────
#   for done in asyncio.as_completed(tasks):
#       result = await done            → get result in FINISH ORDER (not input order)
#   vs gather: returns in input order. as_completed: returns as each finishes.
#
#   BEGINNER EXAMPLE — as_completed:
#
#     async def fetch(id, delay):
#         await asyncio.sleep(delay)
#         return {"id": id, "delay": delay}
#
#     @app.get("/race")
#     async def race():
#         tasks = [fetch(1, 2.0), fetch(2, 0.5), fetch(3, 1.0)]
#         results = []
#         for done in asyncio.as_completed(tasks):
#             r = await done
#             results.append(r)
#         return results
#
#     # curl "http://localhost:8000/race"
#     #
#     #   gather would return: [id=1, id=2, id=3]  ← input order
#     #   as_completed returns: [id=2, id=3, id=1]  ← finish order (fastest first)
#     #
#     #   Timeline:
#     #     0.5s: id=2 finishes first  → results[0]
#     #     1.0s: id=3 finishes second → results[1]
#     #     2.0s: id=1 finishes last   → results[2]
#
# ── async for — Async iteration ─────────────────────────────────
#   async def fetch_pages():
#       yield page                     → async generator (yields data over time)
#   async for page in fetch_pages():
#       process(page)                  → processes each page as it arrives
#   Use for: paginated APIs, streaming data, chunked file reads.
#
#   BEGINNER EXAMPLE — async for:
#
#     async def fetch_pages():
#         for page_num in range(1, 4):
#             await asyncio.sleep(0.5)     # simulate API delay
#             yield [f"item_{page_num}_1", f"item_{page_num}_2"]
#
#     @app.get("/pages")
#     async def get_all_pages():
#         all_items = []
#         async for page in fetch_pages():  # ← processes each page as it arrives
#             all_items.extend(page)
#         return {"items": all_items}
#
#     # curl "http://localhost:8000/pages"
#     #   → page 1 arrives at 0.5s → page 2 at 1.0s → page 3 at 1.5s
#     #   → {"items": ["item_1_1","item_1_2","item_2_1",...]}
#
# ── async with — Async context manager ──────────────────────────
#   async with httpx.AsyncClient() as client:
#       response = await client.get(url)
#   __aenter__ = async setup, __aexit__ = async cleanup
#   Use for: connections, sessions, resources needing async open/close.
#
#   BEGINNER EXAMPLE — async with:
#
#     @app.get("/external")
#     async def call_external():
#         async with httpx.AsyncClient() as client:    # ← opens connection
#             resp = await client.get("https://api.example.com/data")
#             return resp.json()
#         # ← connection auto-closed here (even if error occurs)
#
#     # curl "http://localhost:8000/external"
#     #   async with opens client → makes request → returns data → closes client
#     #   Same as try/finally but cleaner — cleanup guaranteed
#
# ── Retry pattern ───────────────────────────────────────────────
#   for i in range(retries):
#       try: return await func()
#       except: await asyncio.sleep(delay * i)  → exponential backoff
#   Use for: unreliable external APIs, transient network errors.
#
#   BEGINNER EXAMPLE — Retry:
#
#     async def retry_async(func, retries=3, delay=0.5):
#         for i in range(1, retries + 1):
#             try:
#                 return await func()
#             except Exception as e:
#                 if i == retries: raise      # last attempt — give up
#                 await asyncio.sleep(delay * i)  # wait longer each time
#
#     @app.get("/api-call")
#     async def get_api():
#         return await retry_async(unreliable_api, retries=3, delay=0.5)
#
#     # curl "http://localhost:8000/api-call"
#     #
#     #   Attempt 1: fails → wait 0.5s
#     #   Attempt 2: fails → wait 1.0s (exponential backoff)
#     #   Attempt 3: succeeds → return result
#     #   OR Attempt 3: fails → raise exception (503)
#
# ── httpx.AsyncClient — Async HTTP client ───────────────────────
#   async with httpx.AsyncClient() as client:
#       resp = await client.get(url)
#   NEVER use requests.get() in async def — it blocks the event loop.
#   httpx is the async-native replacement for requests.
#
#   BEGINNER EXAMPLE — httpx:
#
#     # BAD — blocks event loop:
#     #   import requests
#     #   resp = requests.get("https://api.com/data")  ← BLOCKS all other requests!
#     #
#     # GOOD — non-blocking:
#     #   async with httpx.AsyncClient() as client:
#     #       resp = await client.get("https://api.com/data")  ← yields control
#     #
#     # curl "http://localhost:8000/external"
#     #   → httpx makes async HTTP call → event loop handles other requests meanwhile
#
# ══════════════════════════════════════════════════════════════════
