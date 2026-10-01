"""Lesson 04 -- Resource (who's emitting this?) and IdGenerator (how are IDs made?)
======================================================================================

Two TracerProvider settings that lesson 01 glossed over.

1. RESOURCE -- identifies the thing producing the telemetry: a service
   name, version, environment, host, etc. Every span from a provider
   carries the SAME resource, attached under the span's "resource" field.
   Leave it unset and you get lesson 01's "service.name":
   "unknown_service:python.exe" -- not useful once you have more than one
   service shipping traces to the same place.

2. ID GENERATOR -- the thing that mints each span's trace_id and span_id.
   The default (RandomIdGenerator) picks random 128-bit / 64-bit numbers --
   fine for production, useless if you want a deterministic test or a
   reproducible example. Subclass IdGenerator to control that.

    TracerProvider(
        resource=Resource.create({SERVICE_NAME: "greeting-service"}),
        id_generator=SequentialIdGenerator(),
    )
         │
         ├─ resource       attached to EVERY span this provider creates
         │                  (replaces lesson 01's "unknown_service:python.exe")
         │
         └─ id_generator   called once per new trace_id / span_id
                            default: random bits  |  here: 1, 2, 3, ...

NESTING RULE, proven below: a span that starts while another is already
open REUSES the parent's trace_id and gets its OWN new span_id. A span
with no open parent starts a brand new trace_id.

Run:  uv run python 04_resource_and_id_generator.py
"""

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.id_generator import IdGenerator


# ------------------------------------------------------- 1. a custom IdGenerator
class SequentialIdGenerator(IdGenerator):
    """Counts 1, 2, 3, ... instead of picking random bits.

    Only the two abstract methods are required. Real-world use case: a
    test suite that snapshots span output and can't have the expected
    value change on every run just because the trace_id is random.
    """

    def __init__(self) -> None:
        self._next_trace_id = 1
        self._next_span_id = 1

    def generate_trace_id(self) -> int:
        value = self._next_trace_id
        self._next_trace_id += 1
        return value

    def generate_span_id(self) -> int:
        value = self._next_span_id
        self._next_span_id += 1
        return value


# ----------------------------------------------------------------- 2. a Resource
resource = Resource.create({
    SERVICE_NAME: "greeting-service",      # SERVICE_NAME is just the string "service.name"
    "service.version": "1.0.0",
    "deployment.environment": "dev",
})

provider = TracerProvider(resource=resource, id_generator=SequentialIdGenerator())
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("lesson-04")


def span_ids(span) -> str:
    ctx = span.get_span_context()
    return f"trace_id={ctx.trace_id} span_id={ctx.span_id}"


# ----------------------------------------------------------- 3. prove the nesting rule
with tracer.start_as_current_span("handle-request") as outer:
    print("outer  ->", span_ids(outer))
    with tracer.start_as_current_span("greet") as inner:
        print("inner  ->", span_ids(inner), "  (same trace_id as outer, new span_id)")

with tracer.start_as_current_span("second-request") as second_root:
    print("2nd root ->", span_ids(second_root), "  (new trace_id -- no parent was open)")

print("\nresource on every span above:")
print(" ", dict(resource.attributes))

# Expected output (ids are deterministic -- SequentialIdGenerator, not random):
#
#   outer  -> trace_id=1 span_id=1
#   inner  -> trace_id=1 span_id=2   (same trace_id as outer, new span_id)
#   2nd root -> trace_id=2 span_id=3   (new trace_id -- no parent was open)
#
#   resource on every span above:
#     {'telemetry.sdk.language': 'python', 'telemetry.sdk.name': 'opentelemetry',
#      'telemetry.sdk.version': '1.45.0', 'service.instance.id': '<a random uuid>',
#      'service.name': 'greeting-service', 'service.version': '1.0.0',
#      'deployment.environment': 'dev'}
#
# (plus three ConsoleSpanExporter JSON blocks, printed as each span ends --
#  same shape as lesson 01, now with "resource.attributes.service.name"
#  reading "greeting-service" instead of "unknown_service:python.exe",
#  and small integer trace_id/span_id values instead of random hex.)
