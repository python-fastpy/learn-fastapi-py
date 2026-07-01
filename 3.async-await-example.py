import asyncio
import httpx
from fastapi import FastAPI, HTTPException
from typing import List, Optional

app = FastAPI()

shipment_data = {
    1: {"id": 1, "content": "Shipment 1", "weight": 10, "status": "In Transit"},
    2: {"id": 2, "content": "Shipment 2", "weight": 20, "status": "Delivered"},
    3: {"id": 3, "content": "Shipment 3", "weight": 15, "status": "Pending"},
}


# ╔══════════════════════════════════════════════════════════════════════╗
# ║                   SYNC vs ASYNC in FastAPI                          ║
# ║                                                                     ║
# ║  def my_func():          → sync — runs in a thread pool             ║
# ║  async def my_func():    → async — runs on the event loop           ║
# ║                                                                     ║
# ║  USE sync (def):  CPU work, no I/O waiting                          ║
# ║  USE async (async def): API calls, DB queries, file I/O, sleep      ║
# ║                                                                     ║
# ║  KEY RULE: inside async def, use "await" before any async operation  ║
# ║  If you forget await → you get a coroutine object, not the result   ║
# ╚══════════════════════════════════════════════════════════════════════╝


# ════════════════════════════════════════════════════
# 1. SYNC endpoint — regular def (no async)
#
#  - FastAPI runs this in a thread pool automatically
#  - Fine for simple logic, no waiting involved
#  - Cannot use "await" inside a regular def
# ════════════════════════════════════════════════════

@app.get("/sync/shipment/{id}")
def get_shipment_sync(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]
# curl http://localhost:8000/sync/shipment/1


# ════════════════════════════════════════════════════
# 2. ASYNC endpoint — basic async def
#
#  - Runs on the event loop (not a thread)
#  - Same logic, just declared with "async def"
#  - For simple dict lookups, sync and async behave the same
#  - The real benefit comes when you need to "await" something
# ════════════════════════════════════════════════════

@app.get("/async/shipment/{id}")
async def get_shipment_async(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return shipment_data[id]
# curl http://localhost:8000/async/shipment/1


# ════════════════════════════════════════════════════
# 3. AWAIT a sleep — simulate a slow operation
#
#  asyncio.sleep() = non-blocking wait
#  time.sleep()    = BLOCKING wait (freezes the server!)
#
#  During await asyncio.sleep(), the server handles
#  OTHER requests. During time.sleep(), it does NOTHING.
# ════════════════════════════════════════════════════

@app.get("/async/slow-shipment/{id}")
async def get_shipment_slow(id: int):
    await asyncio.sleep(2)    # simulates 2s DB query — server stays responsive
    # time.sleep(2)           # BAD! blocks entire event loop for 2 seconds
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    return {"shipment": shipment_data[id], "note": "This took 2 seconds"}
# curl http://localhost:8000/async/slow-shipment/1
# Takes 2s, but other requests are handled during the wait


# ════════════════════════════════════════════════════
# 4. AWAIT an HTTP call — call external API
#
#  httpx.AsyncClient = async HTTP client (like requests, but async)
#  requests.get()    = BLOCKING (never use in async def!)
#
#  "async with" = opens and auto-closes the client
#  "await client.get()" = waits for response without blocking
# ════════════════════════════════════════════════════

@app.get("/async/external-api")
async def call_external_api():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://jsonplaceholder.typicode.com/todos/1")
    return {"external_data": response.json()}
# curl http://localhost:8000/async/external-api
# Fetches data from external API without blocking the server


# ════════════════════════════════════════════════════
# 5. MULTIPLE sequential awaits — one after another
#
#  Each await waits for the previous to finish
#  Total time = sum of all waits
#  3 calls × 1s each = ~3 seconds total
# ════════════════════════════════════════════════════

@app.get("/async/sequential")
async def sequential_calls():
    async with httpx.AsyncClient() as client:
        # Call 1 — wait for it to finish
        resp1 = await client.get("https://jsonplaceholder.typicode.com/todos/1")
        # Call 2 — starts AFTER call 1 finishes
        resp2 = await client.get("https://jsonplaceholder.typicode.com/todos/2")
        # Call 3 — starts AFTER call 2 finishes
        resp3 = await client.get("https://jsonplaceholder.typicode.com/todos/3")
    return {
        "todo_1": resp1.json()["title"],
        "todo_2": resp2.json()["title"],
        "todo_3": resp3.json()["title"],
        "note": "These ran one after another (slow)",
    }
# curl http://localhost:8000/async/sequential


# ════════════════════════════════════════════════════
# 6. PARALLEL awaits — asyncio.gather()
#
#  asyncio.gather() = run multiple awaits AT THE SAME TIME
#  Total time = time of the SLOWEST call (not the sum)
#  3 calls × 1s each = ~1 second total (3x faster!)
#
#  gather() returns results IN THE SAME ORDER as inputs
# ════════════════════════════════════════════════════

@app.get("/async/parallel")
async def parallel_calls():
    async with httpx.AsyncClient() as client:
        # All 3 calls start at the same time
        resp1, resp2, resp3 = await asyncio.gather(
            client.get("https://jsonplaceholder.typicode.com/todos/1"),
            client.get("https://jsonplaceholder.typicode.com/todos/2"),
            client.get("https://jsonplaceholder.typicode.com/todos/3"),
        )
    return {
        "todo_1": resp1.json()["title"],
        "todo_2": resp2.json()["title"],
        "todo_3": resp3.json()["title"],
        "note": "These ran in parallel (fast!)",
    }
# curl http://localhost:8000/async/parallel


# ════════════════════════════════════════════════════
# 7. PARALLEL with dynamic list — gather N tasks
#
#  When you don't know how many tasks ahead of time
#  Build a list of coroutines, then gather them all
# ════════════════════════════════════════════════════

@app.get("/async/parallel-dynamic")
async def parallel_dynamic(ids: str = "1,2,3,4,5"):
    todo_ids = [int(i) for i in ids.split(",")]
    async with httpx.AsyncClient() as client:
        # Create a list of coroutines (not yet started)
        tasks = [
            client.get(f"https://jsonplaceholder.typicode.com/todos/{tid}")
            for tid in todo_ids
        ]
        # Run all at once
        responses = await asyncio.gather(*tasks)
    return {
        "results": [r.json()["title"] for r in responses],
        "count": len(responses),
    }
# curl http://localhost:8000/async/parallel-dynamic
# curl "http://localhost:8000/async/parallel-dynamic?ids=1,2,3,4,5,6,7,8,9,10"


# ════════════════════════════════════════════════════
# 8. GATHER with error handling — return_exceptions=True
#
#  By default, if ONE task fails, gather() cancels ALL tasks
#  return_exceptions=True → failed tasks return the exception
#  instead of crashing, so other tasks still complete
# ════════════════════════════════════════════════════

@app.get("/async/parallel-safe")
async def parallel_with_error_handling():
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            client.get("https://jsonplaceholder.typicode.com/todos/1"),
            client.get("https://invalid-url-that-will-fail.com/data"),  # this will fail
            client.get("https://jsonplaceholder.typicode.com/todos/3"),
            return_exceptions=True,  # don't crash if one fails
        )
    output = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            output.append({"task": i + 1, "status": "failed", "error": str(result)})
        else:
            output.append({"task": i + 1, "status": "success", "data": result.json()["title"]})
    return output
# curl http://localhost:8000/async/parallel-safe
# Task 1: success, Task 2: failed, Task 3: success


# ════════════════════════════════════════════════════
# 9. ASYNC helper function — await your own functions
#
#  You can create your own async functions and await them
#  Useful for reusable logic (DB queries, API calls, etc.)
# ════════════════════════════════════════════════════

async def fetch_shipment_from_db(id: int) -> dict:
    """Simulates an async database query"""
    await asyncio.sleep(0.5)  # simulate DB latency
    if id not in shipment_data:
        return None
    return shipment_data[id]

async def enrich_shipment(shipment: dict) -> dict:
    """Simulates calling an external service to add tracking info"""
    await asyncio.sleep(0.3)  # simulate API latency
    shipment["tracking_url"] = f"https://track.example.com/{shipment['id']}"
    return shipment

@app.get("/async/helper/{id}")
async def get_with_helpers(id: int):
    # await your own async functions
    shipment = await fetch_shipment_from_db(id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Not found")
    enriched = await enrich_shipment(shipment.copy())
    return enriched
# curl http://localhost:8000/async/helper/1
# Takes ~0.8s (0.5 + 0.3 sequential)


# ════════════════════════════════════════════════════
# 10. PARALLEL helper calls — run your own functions in parallel
# ════════════════════════════════════════════════════

async def get_shipment_weight(id: int) -> float:
    await asyncio.sleep(0.5)
    return shipment_data.get(id, {}).get("weight", 0)

async def get_shipment_status(id: int) -> str:
    await asyncio.sleep(0.5)
    return shipment_data.get(id, {}).get("status", "Unknown")

async def get_shipment_content(id: int) -> str:
    await asyncio.sleep(0.5)
    return shipment_data.get(id, {}).get("content", "Unknown")

@app.get("/async/parallel-helpers/{id}")
async def get_with_parallel_helpers(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")

    # Sequential: 0.5 + 0.5 + 0.5 = 1.5s
    # Parallel:   max(0.5, 0.5, 0.5) = 0.5s
    weight, status, content = await asyncio.gather(
        get_shipment_weight(id),
        get_shipment_status(id),
        get_shipment_content(id),
    )
    return {"id": id, "weight": weight, "status": status, "content": content}
# curl http://localhost:8000/async/parallel-helpers/1
# Takes ~0.5s instead of 1.5s


# ════════════════════════════════════════════════════
# 11. asyncio.create_task() — fire and forget
#
#  create_task() = start a background task, don't wait for it
#  The endpoint returns immediately while the task runs
#  Useful for: logging, notifications, cleanup
#
#  WARNING: if the server shuts down, the task is lost
# ════════════════════════════════════════════════════

async def send_notification(shipment_id: int, message: str):
    """Background task — runs after response is sent"""
    await asyncio.sleep(2)  # simulate sending email/webhook
    print(f"NOTIFICATION: Shipment {shipment_id} — {message}")

@app.post("/async/fire-and-forget/{id}")
async def update_and_notify(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    shipment_data[id]["status"] = "Delivered"

    # Start notification but DON'T wait for it
    asyncio.create_task(send_notification(id, "Status changed to Delivered"))

    # Response returns immediately, notification runs in background
    return {"shipment": shipment_data[id], "note": "Notification sent in background"}
# curl -X POST http://localhost:8000/async/fire-and-forget/1
# Returns instantly, "NOTIFICATION: ..." prints 2s later in server logs


# ════════════════════════════════════════════════════
# 12. asyncio.wait_for() — await with timeout
#
#  wait_for() = await something, but cancel if too slow
#  Raises asyncio.TimeoutError if the task takes too long
# ════════════════════════════════════════════════════

async def slow_database_query(id: int) -> dict:
    await asyncio.sleep(5)  # simulates very slow query
    return shipment_data.get(id)

@app.get("/async/timeout/{id}")
async def get_with_timeout(id: int):
    try:
        # Wait max 2 seconds for the query
        result = await asyncio.wait_for(slow_database_query(id), timeout=2.0)
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Database query timed out after 2 seconds",
        )
# curl http://localhost:8000/async/timeout/1
# Always times out because slow_database_query takes 5s but timeout is 2s


# ════════════════════════════════════════════════════
# 13. asyncio.Semaphore — limit concurrent tasks
#
#  Semaphore(N) = only N tasks can run at the same time
#  Others wait until a slot opens up
#  Useful for: rate limiting API calls, DB connection limits
# ════════════════════════════════════════════════════

semaphore = asyncio.Semaphore(3)  # max 3 concurrent tasks

async def rate_limited_fetch(client: httpx.AsyncClient, todo_id: int) -> dict:
    async with semaphore:  # acquire slot (waits if all 3 are taken)
        response = await client.get(
            f"https://jsonplaceholder.typicode.com/todos/{todo_id}"
        )
        return response.json()
    # slot is released automatically when "async with" exits

@app.get("/async/semaphore")
async def get_with_semaphore():
    async with httpx.AsyncClient() as client:
        # 10 tasks, but only 3 run at a time
        tasks = [rate_limited_fetch(client, i) for i in range(1, 11)]
        results = await asyncio.gather(*tasks)
    return {
        "count": len(results),
        "titles": [r["title"] for r in results],
        "note": "Only 3 ran at a time despite 10 tasks",
    }
# curl http://localhost:8000/async/semaphore


# ════════════════════════════════════════════════════
# 14. asyncio.Queue — producer/consumer pattern
#
#  Queue = async-safe way to pass data between tasks
#  Producer puts items in → Consumer takes items out
#  Useful for: job processing, batch operations
# ════════════════════════════════════════════════════

@app.post("/async/queue-demo")
async def queue_demo():
    queue = asyncio.Queue()
    results = []

    async def producer():
        """Puts shipment IDs into the queue"""
        for id in shipment_data.keys():
            await queue.put(id)
            await asyncio.sleep(0.1)  # simulate staggered production
        await queue.put(None)  # signal: no more items

    async def consumer():
        """Takes IDs from queue and processes them"""
        while True:
            id = await queue.get()
            if id is None:
                break
            await asyncio.sleep(0.2)  # simulate processing
            results.append({"id": id, "processed": True})
            queue.task_done()

    # Run producer and consumer in parallel
    await asyncio.gather(producer(), consumer())
    return {"processed": results}
# curl -X POST http://localhost:8000/async/queue-demo


# ════════════════════════════════════════════════════
# 15. asyncio.Event — coordinate between tasks
#
#  Event = a flag that tasks can wait on
#  event.set()    → flag is ON, all waiters proceed
#  event.wait()   → blocks until flag is ON
#  event.clear()  → reset flag to OFF
#
#  Useful for: "wait until X is ready before doing Y"
# ════════════════════════════════════════════════════

@app.get("/async/event-demo")
async def event_demo():
    ready_event = asyncio.Event()
    result = {"steps": []}

    async def setup_database():
        result["steps"].append("DB: starting setup...")
        await asyncio.sleep(1)
        result["steps"].append("DB: setup complete!")
        ready_event.set()  # signal: database is ready

    async def run_query():
        result["steps"].append("Query: waiting for DB to be ready...")
        await ready_event.wait()  # blocks until ready_event.set() is called
        result["steps"].append("Query: DB is ready, running query!")
        await asyncio.sleep(0.5)
        result["steps"].append("Query: done!")

    await asyncio.gather(setup_database(), run_query())
    return result
# curl http://localhost:8000/async/event-demo
# Query waits for DB setup to finish before running


# ════════════════════════════════════════════════════
# 16. asyncio.Lock — prevent race conditions
#
#  Lock = only ONE task can access the resource at a time
#  Without lock: two tasks modify the same data = corrupted
#  With lock: tasks take turns, data stays consistent
# ════════════════════════════════════════════════════

counter = {"value": 0}
lock = asyncio.Lock()

async def increment_safe():
    async with lock:  # only one task at a time
        current = counter["value"]
        await asyncio.sleep(0.01)  # simulate some work
        counter["value"] = current + 1

async def increment_unsafe():
    # NO lock — race condition possible
    current = counter["value"]
    await asyncio.sleep(0.01)
    counter["value"] = current + 1

@app.get("/async/lock-demo")
async def lock_demo():
    counter["value"] = 0

    # 10 parallel increments WITH lock → always 10
    tasks_safe = [increment_safe() for _ in range(10)]
    await asyncio.gather(*tasks_safe)
    safe_result = counter["value"]

    counter["value"] = 0

    # 10 parallel increments WITHOUT lock → might be < 10
    tasks_unsafe = [increment_unsafe() for _ in range(10)]
    await asyncio.gather(*tasks_unsafe)
    unsafe_result = counter["value"]

    return {
        "with_lock": safe_result,       # always 10
        "without_lock": unsafe_result,  # might be less than 10 (race condition)
    }
# curl http://localhost:8000/async/lock-demo


# ════════════════════════════════════════════════════
# 17. async for — async iteration (async generators)
#
#  "async for" = iterate over items that arrive over time
#  Each item might require an await (DB cursor, paginated API)
#
#  async def + yield = async generator
# ════════════════════════════════════════════════════

async def fetch_shipments_paginated(page_size: int = 2):
    """Simulates paginated DB query — yields one page at a time"""
    all_ids = list(shipment_data.keys())
    for i in range(0, len(all_ids), page_size):
        await asyncio.sleep(0.3)  # simulate DB call per page
        page_ids = all_ids[i:i + page_size]
        yield [shipment_data[sid] for sid in page_ids]

@app.get("/async/async-for")
async def get_with_async_for():
    all_shipments = []
    page_num = 0
    async for page in fetch_shipments_paginated(page_size=2):
        page_num += 1
        all_shipments.extend(page)
    return {
        "total_pages": page_num,
        "total_shipments": len(all_shipments),
        "shipments": all_shipments,
    }
# curl http://localhost:8000/async/async-for


# ════════════════════════════════════════════════════
# 18. async with — async context manager
#
#  "async with" = setup + cleanup that needs await
#  Example: open DB connection, do work, close connection
#
#  __aenter__ = setup (called on entry)
#  __aexit__  = cleanup (called on exit, even if error)
# ════════════════════════════════════════════════════

class AsyncDBConnection:
    """Simulates an async database connection"""

    async def __aenter__(self):
        await asyncio.sleep(0.2)  # simulate connection setup
        self.connected = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await asyncio.sleep(0.1)  # simulate connection cleanup
        self.connected = False
        return False  # don't suppress exceptions

    async def query(self, id: int) -> Optional[dict]:
        await asyncio.sleep(0.1)  # simulate query
        return shipment_data.get(id)

@app.get("/async/context-manager/{id}")
async def get_with_context_manager(id: int):
    async with AsyncDBConnection() as db:
        result = await db.query(id)
        if not result:
            raise HTTPException(status_code=404, detail="Not found")
        return {"shipment": result, "db_connected": db.connected}
    # db.__aexit__ runs automatically here — connection closed
# curl http://localhost:8000/async/context-manager/1


# ════════════════════════════════════════════════════
# 19. asyncio.shield() — protect task from cancellation
#
#  shield() = the inner task keeps running even if
#  the outer task is cancelled (e.g., by timeout)
#
#  Use for: critical operations that MUST complete
#  (payment processing, data commits)
# ════════════════════════════════════════════════════

async def critical_save(id: int) -> dict:
    """Must complete even if request times out"""
    await asyncio.sleep(1)
    shipment_data[id]["status"] = "Saved"
    return shipment_data[id]

@app.post("/async/shield/{id}")
async def save_with_shield(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        # Even if this endpoint times out, critical_save keeps running
        result = await asyncio.wait_for(
            asyncio.shield(critical_save(id)),
            timeout=0.5,
        )
        return {"result": result, "note": "Completed within timeout"}
    except asyncio.TimeoutError:
        return {"note": "Timed out, but save is still running in background"}
# curl -X POST http://localhost:8000/async/shield/1


# ════════════════════════════════════════════════════
# 20. Mixing async + sync — calling sync from async
#
#  asyncio.to_thread() = run a SYNC function in a thread
#  without blocking the event loop
#
#  Use when: you have a sync library (e.g., requests, PIL)
#  that you need to call from an async endpoint
# ════════════════════════════════════════════════════

def heavy_cpu_work(id: int) -> dict:
    """Sync function — CPU-intensive work (can't be async)"""
    total = 0
    for i in range(1_000_000):
        total += i
    return {"id": id, "computed_sum": total}

@app.get("/async/sync-in-async/{id}")
async def call_sync_from_async(id: int):
    # Run sync function in thread — doesn't block event loop
    result = await asyncio.to_thread(heavy_cpu_work, id)
    return result
# curl http://localhost:8000/async/sync-in-async/1


# ════════════════════════════════════════════════════
# 21. asyncio.as_completed() — process results as they arrive
#
#  gather()       = waits for ALL tasks, returns in input order
#  as_completed() = yields tasks as each one finishes (fastest first)
#
#  Useful when you want to process results immediately
#  instead of waiting for the slowest task
# ════════════════════════════════════════════════════

async def fetch_with_delay(id: int, delay: float) -> dict:
    await asyncio.sleep(delay)
    return {"id": id, "delay": delay}

@app.get("/async/as-completed")
async def process_as_completed():
    tasks = [
        asyncio.create_task(fetch_with_delay(1, 2.0)),  # slowest
        asyncio.create_task(fetch_with_delay(2, 0.5)),  # fastest
        asyncio.create_task(fetch_with_delay(3, 1.0)),  # medium
    ]
    results = []
    order = 1
    for completed_task in asyncio.as_completed(tasks):
        result = await completed_task
        result["finished_order"] = order
        results.append(result)
        order += 1
    return {
        "results": results,
        "note": "Results are in completion order: id=2 first, then id=3, then id=1",
    }
# curl http://localhost:8000/async/as-completed


# ════════════════════════════════════════════════════
# 22. Retry pattern — retry failed async operations
#
#  Common pattern for unreliable external services
#  Try N times with increasing delay between retries
# ════════════════════════════════════════════════════

attempt_counter = {"count": 0}

async def unreliable_service() -> dict:
    """Fails the first 2 times, succeeds on 3rd"""
    attempt_counter["count"] += 1
    if attempt_counter["count"] < 3:
        raise Exception(f"Service unavailable (attempt {attempt_counter['count']})")
    return {"data": "success!", "attempts": attempt_counter["count"]}

async def retry_async(func, max_retries: int = 3, base_delay: float = 0.5):
    """Generic retry wrapper for any async function"""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                delay = base_delay * attempt  # increasing delay: 0.5, 1.0, 1.5...
                await asyncio.sleep(delay)
    raise last_error

@app.get("/async/retry")
async def get_with_retry():
    attempt_counter["count"] = 0  # reset for demo
    try:
        result = await retry_async(unreliable_service, max_retries=5, base_delay=0.3)
        return {"result": result, "note": "Succeeded after retries"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
# curl http://localhost:8000/async/retry
# Fails twice, succeeds on 3rd attempt


# ════════════════════════════════════════════════════
# 23. Async list comprehension — await inside comprehension
# ════════════════════════════════════════════════════

async def process_shipment(id: int) -> dict:
    await asyncio.sleep(0.1)
    s = shipment_data.get(id)
    if s:
        return {**s, "processed": True}
    return {"id": id, "processed": False, "error": "not found"}

@app.get("/async/comprehension")
async def async_comprehension():
    ids = list(shipment_data.keys())

    # WRONG WAY — this is sequential (one at a time)!
    # results = [await process_shipment(id) for id in ids]

    # RIGHT WAY — use gather for parallel
    results = await asyncio.gather(*[process_shipment(id) for id in ids])

    return {"results": list(results)}
# curl http://localhost:8000/async/comprehension


# ════════════════════════════════════════════════════
# 24. Chaining async calls — one result feeds the next
#
#  Common pattern: fetch → transform → save
#  Each step awaits the previous step's result
# ════════════════════════════════════════════════════

async def step1_fetch(id: int) -> dict:
    await asyncio.sleep(0.2)
    return shipment_data.get(id, {})

async def step2_transform(data: dict) -> dict:
    await asyncio.sleep(0.2)
    data["weight_lbs"] = round(data.get("weight", 0) * 2.205, 2)
    return data

async def step3_validate(data: dict) -> dict:
    await asyncio.sleep(0.1)
    data["validated"] = data.get("weight_lbs", 0) > 0
    return data

@app.get("/async/chain/{id}")
async def chained_pipeline(id: int):
    if id not in shipment_data:
        raise HTTPException(status_code=404, detail="Not found")
    # Each step uses the result of the previous step
    raw = await step1_fetch(id)
    transformed = await step2_transform(raw.copy())
    validated = await step3_validate(transformed)
    return validated
# curl http://localhost:8000/async/chain/1
# Runs 3 steps sequentially: fetch → transform → validate


# ════════════════════════════════════════════════════
# 25. Fan-out / fan-in — split work, then combine
#
#  Fan-out:  one input → many parallel tasks
#  Fan-in:   many results → one combined output
#
#  Pattern: split → parallel process → merge results
# ════════════════════════════════════════════════════

async def check_warehouse(warehouse: str, id: int) -> dict:
    await asyncio.sleep(0.3)
    available = (id + hash(warehouse)) % 2 == 0  # fake availability
    return {"warehouse": warehouse, "shipment_id": id, "available": available}

@app.get("/async/fan-out/{id}")
async def fan_out_fan_in(id: int):
    warehouses = ["NYC", "LON", "TYO", "SYD", "BER"]

    # Fan-out: check all warehouses in parallel
    results = await asyncio.gather(
        *[check_warehouse(wh, id) for wh in warehouses]
    )

    # Fan-in: combine results
    available = [r for r in results if r["available"]]
    unavailable = [r for r in results if not r["available"]]

    return {
        "shipment_id": id,
        "available_in": [r["warehouse"] for r in available],
        "unavailable_in": [r["warehouse"] for r in unavailable],
        "checked_warehouses": len(results),
    }
# curl http://localhost:8000/async/fan-out/1
