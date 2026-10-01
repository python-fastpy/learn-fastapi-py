"""Lesson 12 -- Span events and links: the two fields that stayed empty
===========================================================================

Every span printed so far showed `"events": []` and `"links": []`. Both
are real fields with a real purpose -- they just never got used.

EVENTS -- a timestamped thing that happened INSIDE one span
    An attribute describes the whole span ("greet.name": "Ada"). An event
    is a moment within it, with its own timestamp:
        span.add_event("cache-miss")
        span.add_event("db-query-finished", {"rows": 1})
    (lesson 11's "exception" record is implemented as exactly this --
     record_exception() is just add_event("exception", {...}) under the hood)

LINKS -- relate a span to a DIFFERENT, UNRELATED trace
    Nesting (lesson 01) shares one trace_id: parent and child are the SAME
    story. A link instead says "this span is related to that completely
    separate trace" -- e.g. one "batch-summary" span that links to 50
    independent per-item traces it doesn't share a trace_id with at all:

        item-1 (trace A) ─┐
        item-2 (trace B) ─┼─ linked from ──  batch-summary (trace C, its OWN trace_id)
        item-3 (trace C) ─┘

    links=[Link(span_context), Link(other_context, {"note": "slow"})]
    passed to start_as_current_span() -- links are set at CREATION time,
    unlike events/attributes which can be added any time before the span ends.

Run:  uv run python 12_span_events_and_links.py
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Link

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("lesson-12")


# ------------------------------------------------------------------- 1. events
print("--- span 1: 'fetch-user', three events inside one span ---")
with tracer.start_as_current_span("fetch-user"):
    trace.get_current_span().add_event("cache-miss")
    trace.get_current_span().add_event("db-query-started", {"table": "users"})
    trace.get_current_span().add_event("db-query-finished", {"rows": 1})


# -------------------------------------------------------------------- 2. links
print("\n--- spans 2-3: two INDEPENDENT traces (no parent/child relationship) ---")
with tracer.start_as_current_span("item-1") as item1:
    ctx1 = item1.get_span_context()
with tracer.start_as_current_span("item-2") as item2:
    ctx2 = item2.get_span_context()

print("\n--- span 4: 'batch-summary', its OWN trace, LINKED to both items above ---")
with tracer.start_as_current_span(
    "batch-summary", links=[Link(ctx1), Link(ctx2, {"note": "slow"})]
) as summary:
    print("batch-summary trace_id:", summary.get_span_context().trace_id)
    print("item-1 trace_id:       ", ctx1.trace_id, " <- a DIFFERENT trace, only linked")

# Expected output (ids vary; the shapes and relationships don't):
#
# --- span 1: 'fetch-user', three events inside one span ---
# {
#     "name": "fetch-user",
#     "events": [
#         {"name": "cache-miss", "attributes": {}},
#         {"name": "db-query-started", "attributes": {"table": "users"}},
#         {"name": "db-query-finished", "attributes": {"rows": 1}}
#     ],
#     "links": [],
#     ...
# }
#
# --- spans 2-3: two INDEPENDENT traces (no parent/child relationship) ---
# { "name": "item-1", "context": {"trace_id": "0xAAA...", ...}, "links": [], ... }
# { "name": "item-2", "context": {"trace_id": "0xBBB...", ...}, "links": [], ... }
#
# --- span 4: 'batch-summary', its OWN trace, LINKED to both items above ---
# batch-summary trace_id: <some integer>
# item-1 trace_id:        <a DIFFERENT integer>  <- a DIFFERENT trace, only linked
# {
#     "name": "batch-summary",
#     "context": {"trace_id": "0xCCC...", ...},        <- its OWN trace_id, not A or B
#     "events": [],
#     "links": [
#         {"context": {"trace_id": "0xAAA...", ...}, "attributes": {}},
#         {"context": {"trace_id": "0xBBB...", ...}, "attributes": {"note": "slow"}}
#     ],
#     ...
# }
