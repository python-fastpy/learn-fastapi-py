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
