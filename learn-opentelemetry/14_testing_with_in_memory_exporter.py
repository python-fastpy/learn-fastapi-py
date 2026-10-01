"""Lesson 14 -- Testing your own instrumentation: InMemorySpanExporter
==========================================================================

Every earlier lesson exported to a console or a real OTLP endpoint --
fine for learning, wrong for a test suite: you don't want "did my code
set the right span attribute?" to depend on parsing printed JSON or
standing up a network receiver. `InMemorySpanExporter` exists exactly for
this: it exports into a plain Python list you can assert on directly.

    your code under test
         │  tracer.start_as_current_span("greet") -- same code either way,
         │  it has no idea the exporter is a test double
         ▼
    SimpleSpanProcessor
         │
         ▼
    InMemorySpanExporter    .get_finished_spans()  -> tuple[ReadableSpan, ...]
                             .clear()                -> empty it between tests

No console output, no network, no server to start first -- just a list of
real `Span` objects with real `.name`/`.attributes`/`.status`, built by
actually running your instrumented function.

Run:  uv run python 14_testing_with_in_memory_exporter.py
"""

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

exporter = InMemorySpanExporter()
provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(exporter))
tracer = provider.get_tracer("lesson-14")


# ---------------------------------------------- the function you're "testing"
def greet(name: str) -> str:
    with tracer.start_as_current_span("greet") as span:
        span.set_attribute("greet.name", name)
        return f"Hello, {name}!"


# ------------------------------------------------- the shape of a real test
result = greet("Ada")

spans = exporter.get_finished_spans()
assert len(spans) == 1
assert spans[0].name == "greet"
assert spans[0].attributes["greet.name"] == "Ada"
assert result == "Hello, Ada!"
print("assertions passed -- no console output, no network, just a list of Span objects")
print("captured spans:", [(s.name, dict(s.attributes)) for s in spans])

# clear() between test cases -- otherwise the next test sees THIS span too
exporter.clear()
print("\nafter clear():", exporter.get_finished_spans())

# Expected output:
#
# assertions passed -- no console output, no network, just a list of Span objects
# captured spans: [('greet', {'greet.name': 'Ada'})]
#
# after clear(): ()
#
# A pytest version of the same test:
#
#   @pytest.fixture
#   def exporter():
#       exp = InMemorySpanExporter()
#       provider = TracerProvider()
#       provider.add_span_processor(SimpleSpanProcessor(exp))
#       trace.set_tracer_provider(provider)
#       yield exp
#       exp.clear()
#
#   def test_greet_sets_name_attribute(exporter):
#       greet("Ada")
#       spans = exporter.get_finished_spans()
#       assert spans[0].attributes["greet.name"] == "Ada"
