"""Lesson 13 -- Samplers: deciding which traces actually get recorded
=========================================================================

Every earlier lesson recorded 100% of its spans -- fine for a lesson,
expensive in production, where "trace everything" can mean paying to
store and ship data nobody will ever look at. A Sampler decides, per
trace, whether a span actually gets recorded and exported, or is thrown
away before it costs anything.

    TracerProvider(sampler=...)
         │
         ▼
    the sampler runs ONCE PER ROOT SPAN (a span with no open parent) and
    decides: record this span (and everything inside it), or don't

    ALWAYS_ON              record everything              (the default)
    ALWAYS_OFF              record nothing -- spans still exist in your
                             code (nothing crashes) but span.is_recording()
                             is False and nothing reaches the exporter
    TraceIdRatioBased(0.5)  deterministic ~50% -- SAME trace_id always
                             gets the SAME decision, so re-running a
                             request with a fixed trace_id is reproducible
    ParentBased(inner)       a ROOT span asks `inner`; a CHILD span instead
                             just INHERITS whatever the root already
                             decided -- so you never get a trace with some
                             spans recorded and others silently missing

Run:  uv run python 13_samplers.py
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_OFF, ParentBased, TraceIdRatioBased


# ---------------------------------------------------------------- 1. ALWAYS_OFF
print("=== part 1: ALWAYS_OFF -- spans exist, but are never recorded ===")
provider = TracerProvider(sampler=ALWAYS_OFF)
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
tracer = provider.get_tracer("lesson-13")

with tracer.start_as_current_span("dropped") as span:
    print("is_recording:", span.is_recording(), " (nothing will print below -- there's nothing to export)")


# --------------------------------------------------------- 2. TraceIdRatioBased
print("\n=== part 2: TraceIdRatioBased(0.5) -- roughly half, by trace_id ===")
provider2 = TracerProvider(sampler=TraceIdRatioBased(0.5))
provider2.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
tracer2 = provider2.get_tracer("lesson-13")

kept = 0
for i in range(10):
    with tracer2.start_as_current_span(f"call-{i}") as span:
        if span.is_recording():
            kept += 1
print(f"{kept}/10 recorded (varies run to run -- each call starts a fresh random trace_id)")


# -------------------------------------------------------------- 3. ParentBased
print("\n=== part 3: ParentBased -- children inherit the ROOT's decision ===")
provider3 = TracerProvider(sampler=ParentBased(ALWAYS_OFF))
provider3.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
tracer3 = provider3.get_tracer("lesson-13")

with tracer3.start_as_current_span("root") as root:
    print("root  is_recording:", root.is_recording())
    with tracer3.start_as_current_span("child") as child:
        print("child is_recording:", child.is_recording(), " (inherits root -- never asks its own sampler)")

# Expected output:
#
# === part 1: ALWAYS_OFF -- spans exist, but are never recorded ===
# is_recording: False  (nothing will print below -- there's nothing to export)
#
# === part 2: TraceIdRatioBased(0.5) -- roughly half, by trace_id ===
# (0-10 JSON span blocks print here, order and count vary run to run)
# <N>/10 recorded (varies run to run -- each call starts a fresh random trace_id)
#
# === part 3: ParentBased -- children inherit the ROOT's decision ===
# root  is_recording: False
# child is_recording: False  (inherits root -- never asks its own sampler)
#
# The important proof in part 3: `child` never even consults ALWAYS_OFF
# itself -- it just copies whatever `root` decided. Swap ALWAYS_OFF for
# ALWAYS_ON and both print True, for the same reason.
