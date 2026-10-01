# Learn OpenTelemetry — Tracing Basics

Six small files that build one real OTLP trace pipeline from scratch: a
span, a processor, two different exporters (console, then real network),
how a trace survives crossing a network call to another service, and the
low-level `Context` mechanism all of that is actually built on.

## What OpenTelemetry is, in short

OpenTelemetry (OTEL) is a vendor-neutral standard for recording what your
code did — as **traces** made of **spans** (named units of work, with a
start/end time and nested parent/child relationships), plus metrics and
logs. You instrument your code once, using OTEL's own API; *where the data
goes* is a separate, swappable choice called an **exporter** — so the same
instrumented code can ship data to a console, a file, or any OTLP-speaking
backend (Jaeger, Datadog, Honeycomb, Braintrust, ...) just by changing
which exporter you plug in.

## The flow

```
   your code
       │
       │  tracer.start_as_current_span("name")
       ▼
     Span                 one unit of work: name, start/end time,
                           attributes, and a parent (for nesting)
       │
       ▼
  SpanProcessor            WHEN does a finished span get handed off?
   ├─ SimpleSpanProcessor      export the instant it ends        (01)
   └─ BatchSpanProcessor       buffer, export in batches          (03)
       │
       ▼
  SpanExporter              WHERE does it go?
   ├─ ConsoleSpanExporter      print(span) to stdout               (01)
   └─ OTLPSpanExporter         POST protobuf to a URL              (03)
                                       │
                                       ▼
                             02_otlp_receiver.py
                         a ~15-line stand-in "collector" --
                         in production this would be the real
                         OpenTelemetry Collector, or a vendor's
                         own OTLP-compatible ingest endpoint
```

`01` only needs the left-hand path (no setup, nothing to run first). `03`
needs `02` running first, in a separate terminal, to actually receive what
it sends. `05` is a different axis entirely -- not where a span is
EXPORTED to, but how a trace survives crossing to another SERVICE:

```
   service A (has the span open)             service B (a separate process)
       │
       │  carrier = {}
       │  inject(carrier)     reads the current span, writes a
       │                      "traceparent" string into carrier
       ▼
   {"traceparent": "00-<trace_id>-<span_id>-<flags>"}
       │
       │  ...sent however carrier travels: HTTP headers, a queue message...
       ▼
                                      ctx = extract(carrier)
                                      start_as_current_span(..., context=ctx)
                                              │
                                              ▼
                                      new span, SAME trace_id,
                                      parented to service A's span
```

## Setup

```bash
cd learn-opentelemetry
uv sync
```

## Lessons

| # | File | Covers |
|---|------|--------|
| 01 | [01_console_exporter.py](01_console_exporter.py) | `TracerProvider`, `Tracer`, spans + attributes, nested (parent/child) spans, `SimpleSpanProcessor` + `ConsoleSpanExporter`, and two manual alternatives to `with start_as_current_span(...) as span:` -- rebuilding it from `start_span()` + `attach()`/`detach()`, and calling the same context manager's `__enter__()`/`__exit__()` directly |
| 02 | [02_otlp_receiver.py](02_otlp_receiver.py) | What an OTLP/HTTP request actually is on the wire: a protobuf `ExportTraceServiceRequest` POSTed to `/v1/traces` |
| 03 | [03_otlp_http_exporter.py](03_otlp_http_exporter.py) | `OTLPSpanExporter`, `BatchSpanProcessor`, and why `provider.shutdown()` matters for a short-lived script |
| 04 | [04_resource_and_id_generator.py](04_resource_and_id_generator.py) | `Resource` / `SERVICE_NAME` (who's emitting this?), a custom `IdGenerator` (how are trace/span IDs made?), and the trace_id/span_id nesting rule |
| 05 | [05_explicit_tracer_and_propagation.py](05_explicit_tracer_and_propagation.py) | Using a `TracerProvider` without a global (`provider.get_tracer(...)` passed explicitly), `span.is_recording()` / `get_span_context()`, and `inject()`/`extract()` -- carrying one trace across a network call |
| 06 | [06_context.py](06_context.py) | `opentelemetry.context` -- the primitive underneath `start_as_current_span` AND `inject`/`extract`: `set_value`, `attach`, `get_value`, `detach` |

## Running

```bash
# 01, 04, 05 and 06 are fully standalone:
uv run python 01_console_exporter.py
uv run python 04_resource_and_id_generator.py
uv run python 05_explicit_tracer_and_propagation.py
uv run python 06_context.py

# 02 and 03 are a pair -- start the receiver first and leave it running:
uv run python 02_otlp_receiver.py       # terminal 1
uv run python 03_otlp_http_exporter.py  # terminal 2
```

## How to check it's working

- **Lesson 01**: read the two JSON blocks it prints. Confirm the `greet`
  span's `parent_id` matches the `handle-request` span's `span_id` — that's
  the nesting, proven, not just asserted.
- **Lesson 04**: it prints an exact "Expected output" block in its own
  docstring — the three `trace_id`/`span_id` summary lines should match
  verbatim (the `service.instance.id` UUID is the one value that's
  supposed to differ every run).
- **Lessons 02 + 03**: lesson 02's terminal should print one line per span
  it received (`greet` × 3, `handle-request` × 1) right after lesson 03
  finishes. If nothing prints, check that port `4318` is free before
  starting lesson 02 (`Get-NetTCPConnection -LocalPort 4318` on Windows) --
  a stale process left listening on it is the most common reason a "running"
  receiver silently never sees the request.
- **Lesson 05**: compare the two printed `SpanContext`s -- `trace_id` must
  be IDENTICAL on both ("service A" and "service B"), while `span_id`
  differs and `handle-request`'s `parent_id` equals `say-hello`'s `span_id`.
  That's `inject()`/`extract()` proven, not just asserted.
- **Lesson 06**: `context.get_current()` must print `{}` both BEFORE the
  span starts and AFTER it ends, with exactly one key while it's open --
  proof that `start_as_current_span` is just an `attach`/`detach` pair
  around your code, not some separate span-only mechanism.
