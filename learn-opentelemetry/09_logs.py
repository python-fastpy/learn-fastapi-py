"""Lesson 09 -- Logs: the third OTel pillar, bridged onto Python's own logging
==================================================================================

OTel doesn't replace Python's `logging` module -- it BRIDGES it. You keep
writing ordinary `logger.info(...)` calls; a `LoggingHandler` attached to
your logger is what turns each record into an OTel log record and exports
it. The one thing that bridge buys you: every log record emitted while a
span is open gets stamped with that span's `trace_id`/`span_id`
AUTOMATICALLY -- the same "current span" Context from lesson 06, just read
by something other than a span this time.

    logging.getLogger(...).info("message")   an ORDINARY Python logging call,
         │                                     nothing OTel-specific about it
         ▼
    LoggingHandler         attached like any other logging.Handler. Reads
                            whatever span is CURRENT right now (lesson 06's
                            Context) and stamps its trace_id/span_id onto
                            the record -- or all-zeros if no span is open
         │
         ▼
    LogRecordProcessor      SimpleLogRecordProcessor (export immediately,
                             used here) or BatchLogRecordProcessor (buffer --
                             lesson 03's BatchSpanProcessor, same idea)
         │
         ▼
    LogExporter              ConsoleLogRecordExporter here; OTLPLogExporter
                             for a real backend

Run:  uv run python 09_logs.py
"""

import logging

from opentelemetry import trace
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import ConsoleLogRecordExporter, SimpleLogRecordProcessor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

# tracing, same as every earlier lesson -- so there's a span to correlate against
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
tracer = trace.get_tracer("lesson-09")

# logging's OTel half: a LoggerProvider, a processor, an exporter -- the
# exact same three-piece shape as tracing, just for log records instead
logger_provider = LoggerProvider()
set_logger_provider(logger_provider)
logger_provider.add_log_record_processor(SimpleLogRecordProcessor(ConsoleLogRecordExporter()))

# attach the bridge to a PLAIN Python logger -- this is the only OTel-aware line
handler = LoggingHandler(logger_provider=logger_provider)
py_logger = logging.getLogger("lesson-09")
py_logger.addHandler(handler)
py_logger.setLevel(logging.INFO)

print("--- log OUTSIDE any span ---")
py_logger.info("no active span here")

print("\n--- log INSIDE a span ---")
with tracer.start_as_current_span("do-work"):
    py_logger.info("inside the span")

# Expected output (trace_id/span_id/timestamps vary -- but the first log's
# ids are always all-zeros, and the second log's ids always match the span
# printed right after it):
#
# --- log OUTSIDE any span ---
# {
#     "body": "no active span here",
#     "severity_text": "INFO",
#     "trace_id": "0x00000000000000000000000000000000",   <- no span was open
#     "span_id": "0x0000000000000000",
#     ...
# }
#
# --- log INSIDE a span ---
# {
#     "body": "inside the span",
#     "severity_text": "INFO",
#     "trace_id": "0x3f394b85c950be90e3ed6257378b0bb5",   <- matches the span below
#     "span_id": "0xd505f18236520a58",                     <- matches the span below
#     ...
# }
# {
#     "name": "do-work",
#     "context": {
#         "trace_id": "0x3f394b85c950be90e3ed6257378b0bb5",
#         "span_id": "0xd505f18236520a58"
#     },
#     ...
# }
