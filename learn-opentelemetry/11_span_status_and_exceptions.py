"""Lesson 11 -- Span status and exceptions: how "failed" actually shows up
==============================================================================

Every span printed in lessons 01-10 showed `"status_code": "UNSET"` --
nobody ever told the span whether it succeeded or failed. A real backend
uses this field to decide what counts as an error for alerting/dashboards,
so leaving it UNSET means a failed operation can look identical to a
successful one.

THREE WAYS STATUS/EXCEPTIONS GET RECORDED, in increasing automation:

    1. MANUAL, no exception object
       span.set_status(Status(StatusCode.OK))             -- mark success explicitly
       span.set_status(Status(StatusCode.ERROR, "why"))   -- a business-logic failure,
                                                               no Python exception involved

    2. MANUAL, with a caught exception
       span.record_exception(e)             -- adds an "exception" EVENT (lesson 12
                                                 covers events) with type/message/stacktrace
       span.set_status(Status(StatusCode.ERROR, str(e)))   -- record_exception alone
                                                               does NOT set status; you still
                                                               need this line too

    3. AUTOMATIC -- the one lessons 01-10 never showed, because none of
       them let an exception escape the `with` block
       with tracer.start_as_current_span(...) as span:
           raise RuntimeError("boom")        -- UNCAUGHT
       Both the "exception" event AND the ERROR status get added FOR YOU.
       This is start_as_current_span's own default behavior
       (record_exception=True, set_status_on_exception=True) -- turn it
       off with start_as_current_span(..., record_exception=False,
       set_status_on_exception=False) if you don't want it.

Run:  uv run python 11_span_status_and_exceptions.py
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Status, StatusCode

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("lesson-11")


# -------------------------------------------------------- 1. explicit success
print("--- span 1: explicit OK ---")
with tracer.start_as_current_span("ok-call") as span:
    span.set_status(Status(StatusCode.OK))


# --------------------------------------------- 2. explicit failure, no exception
print("\n--- span 2: explicit ERROR, no Python exception involved ---")
with tracer.start_as_current_span("bad-call") as span:
    span.set_status(Status(StatusCode.ERROR, "bad input"))


# ------------------------------------------------- 3. caught exception, by hand
print("\n--- span 3: caught exception -- record_exception + set_status, BOTH by hand ---")
with tracer.start_as_current_span("raises-caught") as span:
    try:
        raise ValueError("boom")
    except ValueError as e:
        span.record_exception(e)                        # the event
        span.set_status(Status(StatusCode.ERROR, str(e)))  # the status -- a SEPARATE call


# --------------------------------------------- 4. uncaught exception, automatic
print("\n--- span 4: UNCAUGHT exception -- nothing called by hand ---")
try:
    with tracer.start_as_current_span("raises-uncaught") as span:
        raise RuntimeError("uncaught!")
except RuntimeError:
    pass   # caught out here just so the script keeps running; the span already closed

# Expected output (trace_id/span_id/timestamps vary; everything else doesn't):
#
# --- span 1: explicit OK ---
# { "name": "ok-call", "status": {"status_code": "OK"}, "events": [], ... }
#
# --- span 2: explicit ERROR, no Python exception involved ---
# { "name": "bad-call", "status": {"status_code": "ERROR", "description": "bad input"}, ... }
#
# --- span 3: caught exception -- record_exception + set_status, BOTH by hand ---
# {
#     "name": "raises-caught",
#     "status": {"status_code": "ERROR", "description": "boom"},
#     "events": [
#         {
#             "name": "exception",
#             "attributes": {
#                 "exception.type": "ValueError",
#                 "exception.message": "boom",
#                 "exception.stacktrace": "Traceback ...",
#                 "exception.escaped": "False"
#             }
#         }
#     ],
#     ...
# }
#
# --- span 4: UNCAUGHT exception -- nothing called by hand ---
# {
#     "name": "raises-uncaught",
#     "status": {"status_code": "ERROR", "description": "RuntimeError: uncaught!"},
#     "events": [{"name": "exception", "attributes": {"exception.type": "RuntimeError", ...}}],
#     ...
# }
# (span 4's status and event look almost identical to span 3's -- the
#  difference is nobody wrote record_exception()/set_status() for span 4;
#  start_as_current_span did it the moment the exception left the block)
