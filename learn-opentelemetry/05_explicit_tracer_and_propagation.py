"""Lesson 05 -- No global tracer, and carrying a trace across a network call
================================================================================

Two things every earlier lesson skipped past.

1. EXPLICIT TRACER, NO GLOBAL STATE
   Lessons 01-04 all called `trace.set_tracer_provider(provider)` once, then
   `trace.get_tracer(...)` anywhere, relying on that GLOBAL. Fine for a
   script; risky for a library or a test suite, where mutating global OTEL
   state can leak between tests or between two libraries that both want to
   own it. The alternative: keep the provider as a plain local object and
   hand its tracer to whoever needs it --
       tracer = provider.get_tracer(__name__)
       say_hello(tracer)              # passed in, not fetched from a global
   Nothing stops you from running two totally independent TracerProviders
   in one process this way.

2. PROPAGATION -- carrying a trace ACROSS a network call
   Every span so far lived inside one process. Real systems don't: service
   A calls service B over HTTP, and you want ONE trace covering both sides,
   not two unrelated ones. `inject()` / `extract()` are how:

       SERVICE A (has the span open)              SERVICE B (a separate process)
           │
           │  carrier = {}
           │  inject(carrier)      reads the CURRENT span, writes the
           │                       W3C "traceparent" header into carrier
           ▼
       carrier = {"traceparent": "00-<trace_id>-<span_id>-<flags>"}
           │
           │   ...sent over HTTP, a queue, anywhere a dict of strings can go...
           ▼
                                           ctx = extract(carrier)
                                           start_as_current_span(..., context=ctx)
                                                   │
                                                   ▼
                                           a NEW span, SAME trace_id,
                                           parented to service A's span

   `inject`/`extract` don't know or care that it was HTTP -- `carrier` is
   just a dict of strings. A real HTTP client would merge it into its
   request headers; a real HTTP server would read it out of the incoming
   headers before calling extract().

Also note: `Resource(attributes={...})` (used below) is the raw
constructor -- exactly what you pass, nothing more. Lesson 04's
`Resource.create({...})` instead MERGES in the SDK defaults
(telemetry.sdk.*, a random service.instance.id). Compare the two
"resource" blocks in the printed spans to see the difference.

Run:  uv run python 05_explicit_tracer_and_propagation.py
"""

from opentelemetry.propagate import extract, inject
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import Tracer, TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# No trace.set_tracer_provider() anywhere in this file -- the provider stays
# a local variable, and we hand its tracer to whoever needs it explicitly.
resource = Resource(attributes={SERVICE_NAME: "my-service"})
provider = TracerProvider(resource=resource)
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))


def say_hello(tracer: Tracer) -> dict[str, str]:
    """SERVICE A. Opens a span, then packs it into a carrier to send onward."""
    with tracer.start_as_current_span("say-hello") as span:
        print("Hello, OpenTelemetry!")
        print("is recording:", span.is_recording())        # False once the span has ended
        print("span context:", span.get_span_context())

        carrier: dict[str, str] = {}
        inject(carrier)                                     # <- writes "traceparent" into carrier
        print("propagated headers:", carrier)
        return carrier


def handle_request(tracer: Tracer, carrier: dict[str, str]) -> None:
    """SERVICE B. A separate 'process' -- all it gets is the carrier dict."""
    ctx = extract(carrier)                                  # <- reads "traceparent" back out
    with tracer.start_as_current_span("handle-request", context=ctx) as span:
        print("\nservice B span context:", span.get_span_context())
        print("(trace_id above matches service A's -- same trace, new span)")


tracer = provider.get_tracer(__name__)
sent_carrier = say_hello(tracer)
handle_request(tracer, sent_carrier)

# Expected output (trace_id/span_id are random -- yours will differ, but
# the trace_id in BOTH span contexts below will always match each other):
#
# Hello, OpenTelemetry!
# is recording: True
# span context: SpanContext(trace_id=0x2a3690fbd697cd36584e9192fb8282d0,
#     span_id=0x14122bcc7dec3de9, trace_flags=0x03, trace_state=[], is_remote=False)
# propagated headers: {'traceparent': '00-2a3690fbd697cd36584e9192fb8282d0-14122bcc7dec3de9-03'}
# {
#     "name": "say-hello", ...
#     "resource": {"attributes": {"service.name": "my-service"}}   <- plain Resource(): nothing extra
# }
#
# service B span context: SpanContext(trace_id=0x2a3690fbd697cd36584e9192fb8282d0, ...)
# (trace_id above matches service A's -- same trace, new span)
# {
#     "name": "handle-request",
#     "parent_id": "0x14122bcc7dec3de9",   <- service A's span_id
#     ...
# }
