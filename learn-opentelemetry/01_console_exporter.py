"""Lesson 01 -- The simplest possible trace: ConsoleSpanExporter
===================================================================

Three pieces make tracing work, and you need all three every time:

    TracerProvider   the factory for tracers -- one per process, set once
    Tracer           what your code calls to create spans
    SpanExporter     WHERE a finished span goes (console, a file, a
                     collector over the network, ...)

A Span is one unit of work with a name, a start/end time, and optional
attributes (key-value data about what happened). Spans can nest: a span
started while another is already open becomes its CHILD, so you get a tree
that shows which call happened inside which.

`start_as_current_span()` (used below) does two things for you
automatically: it makes the span "current" (so nested code can find it),
and it ends the span when the `with` block exits. Sections 3 and 4 do both
steps BY HAND, two different ways, to show what that sugar is actually
sugar FOR:
    section 3   rebuilds it from scratch -- tracer.start_span() +
                 trace.set_span_in_context() + context.attach()/detach()
    section 4   calls `start_as_current_span()` itself WITHOUT `with` --
                 __enter__() does the exact same attach, by hand, and
                 __exit__() does the exact same detach + span.end()
Lesson 06 covers the underlying `context` primitives (`attach`/`detach`)
in full.

This lesson uses the exporter that needs no setup at all: ConsoleSpanExporter
just prints each finished span as JSON to your terminal. No server, no
network, nothing to run first -- which makes it the right tool for checking
your instrumentation actually produces the spans you expect, before you
worry about shipping them anywhere.

    your code
        │  tracer.start_as_current_span("greet")
        ▼
      Span            name="greet", attributes={"greet.name": "Ada"},
                       parent = the still-open "handle-request" span
        │  span ends (the `with` block exits)
        ▼
  SimpleSpanProcessor   hands it to the exporter IMMEDIATELY, one by one
        │
        ▼
  ConsoleSpanExporter   print(span)  -->  your terminal, as JSON

Run:  uv run python 01_console_exporter.py
"""

from opentelemetry import context, trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# 1. one TracerProvider per process. Do this once, near startup.
provider = TracerProvider()

# 2. SimpleSpanProcessor exports each span the instant it ends -- no
#    buffering. Good for this lesson (you want to see output immediately);
#    lesson 03 uses BatchSpanProcessor instead, which is what you actually
#    want in production (fewer, bigger network calls).
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

# 3. a Tracer is what your code actually calls.
tracer = trace.get_tracer("lesson-01")


def greet(name: str) -> str:
    # a CHILD span -- it starts while "handle-request" (below) is still open
    with tracer.start_as_current_span("greet") as span:
        span.set_attribute("greet.name", name)          # arbitrary key-value data
        return f"Hello, {name}!"


print("--- span 1: 'greet', printed the instant it ends ---")
with tracer.start_as_current_span("handle-request") as span:
    span.set_attribute("request.id", "demo-1")
    result = greet("Ada")
    print(f"\nresult: {result}\n")

print("--- span 2: 'handle-request', printed after greet() returns ---")
print("(its parent_id is null -- it's the root; 'greet' above has parent_id == this span_id)")


# -------------------------------------------------------- 4. the manual way
# start_span() just creates a Span -- nothing more. It is NOT "current"
# (nested code can't find it via trace.get_current_span()) and it does NOT
# auto-end. Both are YOUR job:
#   trace.set_span_in_context(span)  build a Context with this span in it
#   context.attach(ctx)              make that context current -- returns
#                                     a Token you MUST keep, to undo this later
#   context.detach(token)            restore whatever was current before
#   span.end()                       marks it finished -- THIS is what
#                                     triggers SimpleSpanProcessor's export,
#                                     not the attach/detach calls
print("\n--- span 3: 'say-hello-manual', nothing automatic this time ---")
span = tracer.start_span("say-hello-manual")
span.set_attribute("greeting.language", "en")       # attributes work the same as
span.set_attribute("greeting.recipient", "world")    # sections 1-2 -- set anytime before end()
ctx = trace.set_span_in_context(span)
token = context.attach(ctx)
try:
    print("Hello from a manually managed span!")
    print("is it the current span? ->", trace.get_current_span() is span)
finally:
    # always in a finally -- forgetting detach() leaks this span as
    # "current" forever, even after span.end() has already run
    context.detach(token)
    span.end()
print("after end(), is_recording ->", span.is_recording())


# --------------------------------------- 5. the manual way, reusing start_as_current_span
# `with tracer.start_as_current_span(name) as span:` relies on TWO Python
# mechanics most code never sees separately: calling the function builds a
# context-manager OBJECT (nothing has started yet -- no span exists), and
# the `with` statement is what then calls that object's __enter__() for
# you, binding its return value to `as span`, and calls __exit__() for you
# when the block ends.
#
# You can call __enter__()/__exit__() yourself instead of using `with`.
# This does the SAME attach-and-create work section 4 did by hand
# (start_as_current_span's own body calls trace.use_span(), which is where
# the attach() from section 4 actually happens) -- but you don't have to
# re-implement attach/detach yourself; you just have to remember __exit__.
def apply_attributes(span, attributes: dict) -> None:
    """Stands in for a reusable helper that batch-applies a dict of attributes."""
    for key, value in attributes.items():
        span.set_attribute(key, value)


print("\n--- span 4: 'say-hello-contextmanager', __enter__/__exit__ by hand ---")
manager = tracer.start_as_current_span("say-hello-contextmanager")   # nothing started yet
span = manager.__enter__()                                            # NOW the span exists
apply_attributes(span, {"greeting.language": "en", "greeting.recipient": "world"})
print("is it the current span? ->", trace.get_current_span() is span)
print("is_recording (still open) ->", span.is_recording())

manager.__exit__(None, None, None)   # <- easy to forget; nothing ends this for you
print("is_recording (after __exit__) ->", span.is_recording())
print("still current after __exit__? ->", trace.get_current_span() is span)

# Expected output (trace_id/span_id/timestamps are random -- yours will
# differ -- but the SHAPE, attribute values, and the parent/child link
# are always the same):
#
# --- span 1: 'greet', printed the instant it ends ---
# {
#     "name": "greet",
#     "context": {
#         "trace_id": "0x7d7a36400fd519b587643add24f23a68",
#         "span_id": "0x8b4a8b9aaf92e24a",
#         "trace_state": "[]"
#     },
#     "kind": "SpanKind.INTERNAL",
#     "parent_id": "0x6d9428bb3efb4774",             <- matches handle-request's span_id below
#     "start_time": "2026-10-01T09:26:12.848773Z",
#     "end_time": "2026-10-01T09:26:12.848784Z",
#     "status": {"status_code": "UNSET"},
#     "attributes": {"greet.name": "Ada"},
#     "events": [], "links": [],
#     "resource": {
#         "attributes": {
#             "telemetry.sdk.language": "python",
#             "telemetry.sdk.name": "opentelemetry",
#             "telemetry.sdk.version": "1.45.0",
#             "service.instance.id": "ab2596c4-7718-4dbd-9daf-200058c92d8c",
#             "service.name": "unknown_service:python.exe"    <- lesson 04 fixes this
#         },
#         "schema_url": ""
#     }
# }
#
# result: Hello, Ada!
#
# {
#     "name": "handle-request",
#     "context": {
#         "trace_id": "0x7d7a36400fd519b587643add24f23a68",  <- same trace_id as 'greet'
#         "span_id": "0x6d9428bb3efb4774"                     <- matches greet's parent_id above
#     },
#     "kind": "SpanKind.INTERNAL",
#     "parent_id": null,                                      <- null: this is the root span
#     "status": {"status_code": "UNSET"},
#     "attributes": {"request.id": "demo-1"},
#     ...
# }
# --- span 2: 'handle-request', printed after greet() returns ---
# (its parent_id is null -- it's the root; 'greet' above has parent_id == this span_id)
#
# --- span 3: 'say-hello-manual', nothing automatic this time ---
# Hello from a manually managed span!
# is it the current span? -> True
# {
#     "name": "say-hello-manual",
#     "parent_id": null,
#     "attributes": {
#         "greeting.language": "en",
#         "greeting.recipient": "world"
#     },
#     ...                                 <- printed by span.end(), same as the others
# }
# after end(), is_recording -> False      <- span.end() already ran; it's closed for good
#
# --- span 4: 'say-hello-contextmanager', __enter__/__exit__ by hand ---
# is it the current span? -> True
# is_recording (still open) -> True
# {
#     "name": "say-hello-contextmanager",     <- printed by __exit__(), which is what
#     "attributes": {                             calls span.end() for you this time
#         "greeting.language": "en",
#         "greeting.recipient": "world"
#     },
#     ...
# }
# is_recording (after __exit__) -> False
# still current after __exit__? -> False   <- __exit__ restored the PREVIOUS current span
