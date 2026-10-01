"""Lesson 02 -- A tiny stand-in "collector" that receives real OTLP traffic
===============================================================================

Lesson 01's ConsoleSpanExporter just prints -- nothing leaves your process.
A real backend (Jaeger, Datadog, Honeycomb, Braintrust, ...) instead
receives spans over the network, in OpenTelemetry's own wire format: OTLP
(OpenTelemetry Protocol). Lesson 03 sends real OTLP traffic; THIS file is
what receives it, so you can see the wire format with nothing hidden.

A real OTLP/HTTP request is just:  POST /v1/traces, body = protobuf bytes,
where the bytes deserialize into an ExportTraceServiceRequest message.
That's it -- no magic, no special framework. This file is ~15 lines because
that's really all a minimal receiver needs to be.

(A real collector also validates, batches, retries, and forwards to several
backends at once -- which is why "run the OpenTelemetry Collector" is the
usual production answer instead of hand-rolling this. But seeing the raw
shape once is worth more than skipping straight to a black box.)

    lesson 03 (a separate process)
        │  POST /v1/traces
        │  body = protobuf bytes
        ▼
    do_POST()              this file
        │  request.ParseFromString(body)
        ▼
  ExportTraceServiceRequest   a tree: resource_spans -> scope_spans -> spans
        │  three nested for-loops, below
        ▼
    print(span.name)        your terminal

Run this FIRST, and leave it running:
    uv run python 02_otlp_receiver.py
Then, in another terminal, run lesson 03 to send it real spans.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer

from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
)

PORT = 4318


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        # this is the whole trick: the body IS a serialized protobuf message
        request = ExportTraceServiceRequest()
        request.ParseFromString(body)

        for resource_spans in request.resource_spans:
            for scope_spans in resource_spans.scope_spans:
                for span in scope_spans.spans:
                    print(
                        f"  received span: {span.name!r}  (trace {span.trace_id.hex()[:8]}...)",
                        flush=True,
                    )

        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # silence the default per-request access log line


if __name__ == "__main__":
    print(f"Listening for OTLP/HTTP trace exports on http://localhost:{PORT}/v1/traces ...")
    print("(Ctrl+C to stop)\n", flush=True)
    HTTPServer(("localhost", PORT), Handler).serve_forever()

# Expected output -- this file prints nothing on its own until lesson 03
# (running separately) sends it something. Once it does:
#
#   Listening for OTLP/HTTP trace exports on http://localhost:4318/v1/traces ...
#   (Ctrl+C to stop)
#
#     received span: 'greet'  (trace fa69300d...)
#     received span: 'greet'  (trace fa69300d...)
#     received span: 'greet'  (trace fa69300d...)
#     received span: 'handle-request'  (trace fa69300d...)
#
# Four lines because lesson 03 creates four spans (three "greet" calls
# inside one "handle-request"); the "fa69300d..." trace id prefix is
# random and will differ every run, but all four lines share the SAME
# prefix -- one request, one trace, four spans.
