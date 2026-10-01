"""Lesson 10 -- Baggage: carrying your OWN data across a network call
=========================================================================

Lesson 05 used `inject()`/`extract()` to carry trace IDENTITY (trace_id,
span_id) across a network call. Baggage uses the EXACT SAME `inject()`/
`extract()` calls, but carries something different: arbitrary BUSINESS
data you choose -- a tenant id, a user id, an experiment flag -- in its
own header, separate from `traceparent`.

    span attribute              baggage
    ---------------------------  ---------------------------------------
    stays on the ONE span you   travels WITH the request to every
    set it on                   downstream service that extracts it
    read via span.attributes    read via baggage.get_baggage(key),
                                 with NO span involved at all

    baggage.set_baggage("tenant.id", "acme-corp")
         │   returns a NEW Context (same immutable pattern as lesson 06 --
         │   this call alone changes nothing yet)
         ▼
    context.attach(ctx)          makes it current
         │
         ▼
    inject(carrier)              writes a "baggage" header -- and a
                                   "traceparent" header too, if a span is
                                   also open right now (lesson 05's and
                                   this lesson's mechanisms compose; one
                                   inject() call writes BOTH at once)
         │
         │   ...sent over the network...
         ▼
    SERVICE B: extract(carrier) + context.attach(...)
         │
         ▼
    baggage.get_baggage("tenant.id")   -> "acme-corp", read from ambient
                                           Context, no parameter passed --
                                           the same mechanism as lesson 06's
                                           get_value()

Run:  uv run python 10_baggage.py
"""

from opentelemetry import baggage, context, trace
from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("lesson-10")


# ------------------------------------------------ 1. baggage alone, no span
print("=== part 1: baggage by itself ===")
ctx = baggage.set_baggage("tenant.id", "acme-corp")
token = context.attach(ctx)
try:
    carrier: dict[str, str] = {}
    inject(carrier)
    print("carrier:", carrier, "  (just a 'baggage' header -- no span was open)")
finally:
    context.detach(token)

print("read with nothing attached ->", baggage.get_baggage("tenant.id"))


# ------------------------------------- 2. baggage AND a span, at the same time
print("\n=== part 2: baggage riding alongside a real span ===")
with tracer.start_as_current_span("handle-request"):
    ctx = baggage.set_baggage("tenant.id", "acme-corp")
    token = context.attach(ctx)
    try:
        carrier = {}
        inject(carrier)
        print("carrier sent downstream:", carrier)
        print("(both 'traceparent' AND 'baggage' -- one inject() call, two concerns)")
    finally:
        context.detach(token)


# --------------------------------------------- 3. the receiving side (service B)
print("\n=== part 3: service B, a separate process, gets only `carrier` ===")
received_ctx = extract(carrier)
token = context.attach(received_ctx)
try:
    print("service B sees tenant.id ->", baggage.get_baggage("tenant.id"))
    print("all baggage entries      ->", dict(baggage.get_all()))
finally:
    context.detach(token)

# Expected output (trace_id/span_id vary -- the baggage VALUES never do,
# since nothing about them is random):
#
# === part 1: baggage by itself ===
# carrier: {'baggage': 'tenant.id=acme-corp'}   (just a 'baggage' header -- no span was open)
# read with nothing attached -> None
#
# === part 2: baggage riding alongside a real span ===
# carrier sent downstream: {'traceparent': '00-<trace_id>-<span_id>-03', 'baggage': 'tenant.id=acme-corp'}
# (both 'traceparent' AND 'baggage' -- one inject() call, two concerns)
# {
#     "name": "handle-request", ...
# }
#
# === part 3: service B, a separate process, gets only `carrier` ===
# service B sees tenant.id -> acme-corp
# all baggage entries      -> {'tenant.id': 'acme-corp'}
