"""Lesson 03 -- Sending real spans over the network: OTLPSpanExporter
========================================================================

Same three pieces as lesson 01 -- TracerProvider, Tracer, exporter -- but
swap ConsoleSpanExporter for OTLPSpanExporter, and the spans leave your
process for real, over HTTP, to whatever OTLP endpoint you point it at.

    ConsoleSpanExporter(...)                     lesson 01: prints locally
    OTLPSpanExporter(endpoint="http://host/v1/traces")   this lesson: POSTs protobuf

This also switches to BatchSpanProcessor instead of lesson 01's
SimpleSpanProcessor -- the processor that buffers spans and exports them
together, since a real network call is relatively expensive and you don't
want one per span. The cost: spans don't leave immediately, so this script
calls `provider.shutdown()` at the end to flush whatever's still buffered
before the process exits. Skip that and your last batch can simply vanish.

    your code
        │  4 spans end: "greet" x3, "handle-request" x1
        ▼
  BatchSpanProcessor    buffers them -- nothing sent yet
        │  provider.shutdown()  <-- forces the buffer out now
        ▼
  OTLPSpanExporter      serializes the batch to protobuf,
        │                POSTs it to the endpoint below
        ▼
  http://localhost:4318/v1/traces
        │
        ▼
  02_otlp_receiver.py   (a separate process -- must already be running)

REQUIRES lesson 02's receiver running first:
    uv run python 02_otlp_receiver.py      (leave it running, separate terminal)
    uv run python 03_otlp_http_exporter.py (this file)
"""

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

provider = TracerProvider()
exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
provider.add_span_processor(BatchSpanProcessor(exporter))
trace.set_tracer_provider(provider)

tracer = trace.get_tracer("lesson-03")


def greet(name: str) -> str:
    with tracer.start_as_current_span("greet"):
        return f"Hello, {name}!"


with tracer.start_as_current_span("handle-request"):
    for name in ("Ada", "Bob", "Cleo"):
        print(greet(name))

# force the batch out NOW instead of waiting for the background flush timer
# -- without this, a short-lived script can exit before anything is sent.
provider.shutdown()
print("\ndone -- check lesson 02's terminal for the received spans")

# Expected output, in THIS file's own terminal (fully deterministic --
# nothing random is printed here):
#
#   Hello, Ada!
#   Hello, Bob!
#   Hello, Cleo!
#
#   done -- check lesson 02's terminal for the received spans
#
# Expected output, in lesson 02's terminal (started first, still running):
#
#     received span: 'greet'  (trace fa69300d...)
#     received span: 'greet'  (trace fa69300d...)
#     received span: 'greet'  (trace fa69300d...)
#     received span: 'handle-request'  (trace fa69300d...)
#
# If lesson 02's terminal prints nothing, the most common cause isn't a
# code bug -- it's a stale process still bound to port 4318 from a
# previous run. Check with (PowerShell) Get-NetTCPConnection -LocalPort 4318.
